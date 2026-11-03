#!/usr/bin/env python3
"""Apply the AWS Korea V-team black/white template to a deck built with pptxgenjs.

pptxgenjs cannot open an existing .pptx, so build_<deck>.js renders every slide on an
empty "AWS_<TYPE>" slide master (13.333 x 7.5 in). This script opens the chosen template,
removes its sample slides, and re-homes each built slide onto the matching template layout.
Backgrounds, AWS logo, copyright footer, slide-number fields and embedded fonts therefore
come from the template itself - the build never draws them.

It also
  * copies pictures, native charts (with their embedded Excel workbook) and hyperlinks,
  * writes speaker notes one sentence per line (each line becomes its own paragraph),
  * gives every bullet the color and font of its own text (pptxgenjs writes neither),
  * embeds the vector SVG for pictures named "svg:<file.svg>" (PNG stays as the fallback). The
    embedded copy gets an opaque backdrop in the slide color, xlink:href and an intrinsic size,
    and the PNG fallback is flattened onto the same color, so dark-theme diagrams never vanish
    in viewers that draw transparency as white,
  * clones the template's slide-number placeholder where the template's own sample
    slides carry one (white theme), and drops the template's sample slides and sections.

Usage
  python3 apply_template.py <Deck>_raw.pptx --out <Deck>.pptx [--theme black|white] [--assets-dir DIR]

--theme defaults to the THEME the build recorded in the deck subject ("aws-ppt-skills theme=...");
passing a different value is refused so palette and template never mismatch.
"""
from __future__ import annotations

import argparse
import copy
import io
import re
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import PartFactory, XmlPart
from pptx.opc.packuri import PackURI

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"

# Slide type (pptxgenjs master "AWS_<TYPE>") -> template layout. Mirrors each template's own
# sample slides. "slide_number" lists the types whose sample slides carry a slide-number
# placeholder; the black master shows numbers through its own text box instead.
THEMES = {
    "black": {
        "file": "2026_aws_powerpoint_template_whchoi_black.pptx",
        "master": 0,
        "bg": "000000",  # content background; diagrams get an opaque backdrop in this color
        "layouts": {
            "COVER": "1_Title Slide 2B",
            "AGENDA": "Agenda Slide 3",
            "DIVIDER": "Section Header Option 2",
            "CONTENT": "Title Only",
            "CLOSING": "Thank You Option 1",
        },
        "slide_number": set(),
    },
    "white": {
        "file": "2026_aws_powerpoint_template_whchoi_white.pptx",
        "master": 0,
        "bg": "FFFFFF",
        "layouts": {
            "COVER": "Title Side 1A",
            "AGENDA": "Agenda Slide 1",
            "DIVIDER": "Section Header Option 2",
            "CONTENT": "Title Only",
            "CLOSING": "Thank You Option 1",
        },
        "slide_number": {"AGENDA", "DIVIDER", "CONTENT"},
    },
}

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SECTIONS_EXT_URI = "{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


class Copier:
    """Copies parts/relationships from the built deck into the template package."""

    def __init__(self, dst_prs):
        self.pkg = dst_prs.part.package
        self.memo: dict[int, object] = {}
        self.allocated: set[str] = set()

    def next_partname(self, src_partname: str) -> PackURI:
        tmpl = re.sub(r"\d*(\.\w+)$", r"%d\1", src_partname)
        taken = {str(p.partname) for p in self.pkg.iter_parts()} | self.allocated
        n = 1
        while (tmpl % n) in taken:
            n += 1
        name = tmpl % n
        self.allocated.add(name)
        return PackURI(name)

    def clone_part(self, src):
        key = id(src)
        if key in self.memo:
            return self.memo[key]
        new = PartFactory(self.next_partname(str(src.partname)), src.content_type, self.pkg, src.blob)
        self.memo[key] = new
        rid_map = {}
        for rId, rel in list(src.rels.items()):
            if rel.is_external:
                rid_map[rId] = new.relate_to(rel.target_ref, rel.reltype, is_external=True)
            else:
                rid_map[rId] = new.relate_to(self.clone_part(rel.target_part), rel.reltype)
        if rid_map and isinstance(new, XmlPart):
            remap_attrs(new._element, rid_map)
        return new

    def map_rel(self, src_part, dst_part, rId: str) -> str:
        rel = src_part.rels[rId]
        if rel.is_external:
            return dst_part.relate_to(rel.target_ref, rel.reltype, is_external=True)
        target = rel.target_part
        if rel.reltype == RT.IMAGE:
            try:
                _, new_rId = dst_part.get_or_add_image_part(io.BytesIO(target.blob))
                return new_rId
            except Exception:  # unusual raster formats: copy the part as-is
                pass
        return dst_part.relate_to(self.clone_part(target), rel.reltype)


def remap_attrs(root, rid_map: dict[str, str]) -> None:
    for node in root.iter():
        for attr, val in list(node.attrib.items()):
            if attr.startswith(f"{{{R_NS}}}") and val in rid_map:
                node.set(attr, rid_map[val])


def find_layout(prs, master_idx: int, name: str):
    for layout in prs.slide_masters[master_idx].slide_layouts:
        if layout.name == name:
            return layout
    raise SystemExit(f"layout {name!r} not found in master {master_idx}")


def clear_template_slides(prs) -> None:
    sld_id_lst = prs.slides._sldIdLst
    for sld_id in list(sld_id_lst):
        prs.part.drop_rel(sld_id.rId)
        sld_id_lst.remove(sld_id)
    # sections reference slide ids of the removed sample slides -> drop them
    pres_el = prs.part._element
    for ext in pres_el.iter(q(P_NS, "ext")):
        if ext.get("uri") == SECTIONS_EXT_URI:
            ext.getparent().remove(ext)


def max_shape_id(slide) -> int:
    ids = [int(el.get("id")) for el in slide.shapes._spTree.iter() if el.tag == q(P_NS, "cNvPr") and el.get("id", "").isdigit()]
    return max(ids or [1])


def strip_placeholders(slide) -> None:
    for ph in list(slide.placeholders):
        ph._element.getparent().remove(ph._element)


def add_slide_number(slide, layout) -> None:
    for sp in layout.placeholders:
        if sp.placeholder_format.type is not None and "SLIDE_NUMBER" in str(sp.placeholder_format.type):
            el = copy.deepcopy(sp._element)
            sp_pr = el.find(q(P_NS, "spPr"))
            if sp_pr is not None:  # inherit geometry from the layout
                for child in list(sp_pr):
                    sp_pr.remove(child)
            c_nv_pr = el.find(f"{q(P_NS, 'nvSpPr')}/{q(P_NS, 'cNvPr')}")
            c_nv_pr.set("id", str(max_shape_id(slide) + 1))
            slide.shapes._spTree.append(el)
            return


def normalize_bullets(root) -> None:
    """Give every bulleted paragraph the color and font of its own text.

    pptxgenjs writes <a:buChar> without <a:buClr>/<a:buFont>, so the bullet falls back to the
    template's list style (tx1, minor font) and can drift from the text color.
    """
    bu_after_clr = ("buSzTx", "buSzPct", "buSzPts", "buFontTx", "buFont", "buChar")
    for ppr in root.iter(q(A_NS, "pPr")):
        bu_char = ppr.find(q(A_NS, "buChar"))
        if bu_char is None:
            continue
        para = ppr.getparent()
        if ppr.find(q(A_NS, "buClr")) is None and ppr.find(q(A_NS, "buClrTx")) is None:
            clr = para.find(f"{q(A_NS, 'r')}/{q(A_NS, 'rPr')}/{q(A_NS, 'solidFill')}/{q(A_NS, 'srgbClr')}")
            if clr is not None:
                bu_clr = etree.Element(q(A_NS, "buClr"))
                etree.SubElement(bu_clr, q(A_NS, "srgbClr"), val=clr.get("val"))
                anchor = next(c for c in ppr if isinstance(c.tag, str) and etree.QName(c).localname in bu_after_clr)
                anchor.addprevious(bu_clr)
        if ppr.find(q(A_NS, "buFont")) is None and ppr.find(q(A_NS, "buFontTx")) is None:
            latin = para.find(f"{q(A_NS, 'r')}/{q(A_NS, 'rPr')}/{q(A_NS, 'latin')}")
            if latin is not None and latin.get("typeface"):
                bu_char.addprevious(etree.Element(q(A_NS, "buFont"), typeface=latin.get("typeface")))


def copy_shapes(src_slide, dst_slide, copier: Copier) -> None:
    next_id = max_shape_id(dst_slide) + 1
    skip = {q(P_NS, "nvGrpSpPr"), q(P_NS, "grpSpPr")}
    for child in src_slide.shapes._spTree.iterchildren():
        if child.tag in skip:
            continue
        el = copy.deepcopy(child)
        rid_map = {}
        for node in el.iter():
            for attr, val in list(node.attrib.items()):
                if attr.startswith(f"{{{R_NS}}}") and val in src_slide.part.rels and val not in rid_map:
                    rid_map[val] = copier.map_rel(src_slide.part, dst_slide.part, val)
        remap_attrs(el, rid_map)
        normalize_bullets(el)
        for c_nv_pr in el.iter(q(P_NS, "cNvPr")):
            c_nv_pr.set("id", str(next_id))
            next_id += 1
        dst_slide.shapes._spTree.append(el)


def _num(v: str | None) -> float | None:
    try:
        return float(re.sub(r"[a-z%]+$", "", v)) if v is not None else None
    except ValueError:
        return None


def normalize_svg(data: bytes, bg_hex: str) -> bytes:
    """Make a diagram SVG render the same in every viewer.

    * opaque backdrop in the slide color (viewers that flatten transparency onto white would
      otherwise hide light-on-dark diagrams of the black theme),
    * xlink:href next to href on <image>/<use> (older Office SVG renderers read only xlink:href),
    * width/height from the viewBox when missing (intrinsic size).
    """
    text = data.decode("utf-8")
    m = re.search(r"<svg\b[^>]*>", text)
    if m and "xmlns:xlink" not in m.group(0):
        text = text[: m.end() - 1].rstrip("/") + f' xmlns:xlink="{XLINK_NS}"' + text[m.end() - 1:]
    root = etree.fromstring(text.encode("utf-8"), etree.XMLParser(huge_tree=True))
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        if etree.QName(el).localname in ("image", "use") and el.get("href") and el.get(f"{{{XLINK_NS}}}href") is None:
            el.set(f"{{{XLINK_NS}}}href", el.get("href"))
    vb = [float(v) for v in re.split(r"[\s,]+", (root.get("viewBox") or "").strip()) if v]
    if len(vb) == 4:
        vx, vy, vw, vh = vb
    else:
        vx, vy, vw, vh = 0.0, 0.0, _num(root.get("width")) or 1600.0, _num(root.get("height")) or 900.0
    root.set("width", root.get("width") or f"{vw:g}")
    root.set("height", root.get("height") or f"{vh:g}")

    lead = {"title", "desc", "defs", "style", "metadata"}
    children = [c for c in root if isinstance(c.tag, str)]
    first_draw = next((c for c in children if etree.QName(c).localname not in lead), None)
    has_bg = False
    if first_draw is not None and etree.QName(first_draw).localname == "rect":
        w, h = first_draw.get("width", ""), first_draw.get("height", "")
        full_w = w == "100%" or (_num(w) or 0) >= vw * 0.98
        full_h = h == "100%" or (_num(h) or 0) >= vh * 0.98
        filled = (first_draw.get("fill") or "").lower() not in ("", "none", "transparent")
        has_bg = full_w and full_h and filled
    if not has_bg:
        rect = etree.Element(f"{{{SVG_NS}}}rect" if root.tag.startswith("{") else "rect",
                             x=f"{vx:g}", y=f"{vy:g}", width=f"{vw:g}", height=f"{vh:g}", fill=f"#{bg_hex}")
        idx = root.index(first_draw) if first_draw is not None else len(root)
        root.insert(idx, rect)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def flatten_png(image_part, bg_hex: str) -> None:
    """Composite a transparent PNG fallback onto the slide color so it never shows up blank."""
    from PIL import Image
    im = Image.open(io.BytesIO(image_part.blob))
    if im.mode not in ("RGBA", "LA") and not (im.mode == "P" and "transparency" in im.info):
        return
    im = im.convert("RGBA")
    base = Image.new("RGBA", im.size, f"#{bg_hex}")
    base.alpha_composite(im)
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG", optimize=True)
    image_part._blob = out.getvalue()


def embed_svgs(dst_slide, copier: Copier, assets_dir: Path, bg_hex: str) -> list[str]:
    missing = []
    for pic in dst_slide.shapes._spTree.iter(q(P_NS, "pic")):
        c_nv_pr = pic.find(f"{q(P_NS, 'nvPicPr')}/{q(P_NS, 'cNvPr')}")
        name = c_nv_pr.get("name", "")
        if not name.startswith("svg:"):
            continue
        svg_path = Path(name[4:])
        if not svg_path.is_absolute():
            svg_path = assets_dir / svg_path
        if not svg_path.exists():
            missing.append(str(svg_path))
            continue
        svg_bytes = normalize_svg(svg_path.read_bytes(), bg_hex)
        svg_part = PartFactory(copier.next_partname("/ppt/media/image1.svg"), "image/svg+xml", copier.pkg, svg_bytes)
        rId = dst_slide.part.relate_to(svg_part, RT.IMAGE)
        blip = pic.find(f"{q(P_NS, 'blipFill')}/{q(A_NS, 'blip')}")
        png_rid = blip.get(q(R_NS, "embed"))
        if png_rid in dst_slide.part.rels:
            flatten_png(dst_slide.part.rels[png_rid].target_part, bg_hex)
        ext_lst = blip.find(q(A_NS, "extLst"))
        if ext_lst is None:
            ext_lst = etree.SubElement(blip, q(A_NS, "extLst"))
        ext = etree.SubElement(ext_lst, q(A_NS, "ext"), uri=SVG_EXT_URI)
        svg_blip = etree.SubElement(ext, q(ASVG_NS, "svgBlip"), nsmap={"asvg": ASVG_NS})
        svg_blip.set(q(R_NS, "embed"), rId)
        c_nv_pr.set("name", f"Diagram {svg_path.stem}")
    return missing


def copy_notes(src_slide, dst_slide) -> None:
    if not src_slide.has_notes_slide:
        return
    text = src_slide.notes_slide.notes_text_frame.text
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\v", "\n")
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    if lines:
        dst_slide.notes_slide.notes_text_frame.text = "\n".join(lines)


def slide_type(src_slide) -> str:
    name = (src_slide.slide_layout.name or "").upper()
    return name[4:] if name.startswith("AWS_") else "CONTENT"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", help="deck built by pptxgenjs on AWS_* masters (13.333 x 7.5 in)")
    ap.add_argument("--theme", choices=sorted(THEMES), help="default: the THEME recorded by the build")
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets-dir", default=".", help="base dir for relative svg:<file> picture names")
    args = ap.parse_args()

    src = Presentation(args.raw)
    m = re.search(r"theme=(\w+)", src.core_properties.subject or "")
    built_theme = m.group(1) if m else None
    if args.theme and built_theme and args.theme != built_theme:
        print(f"ERROR: deck was built with THEME={built_theme!r} but --theme {args.theme!r} was given. "
              "Rebuild with the matching THEME or drop --theme.", file=sys.stderr)
        return 2
    args.theme = args.theme or built_theme
    if args.theme not in THEMES:
        print("ERROR: theme unknown - pass --theme black|white", file=sys.stderr)
        return 2
    cfg = THEMES[args.theme]
    dst = Presentation(str(TEMPLATE_DIR / cfg["file"]))
    if (src.slide_width, src.slide_height) != (dst.slide_width, dst.slide_height):
        print(f"ERROR: built deck is {src.slide_width}x{src.slide_height} EMU, template is "
              f"{dst.slide_width}x{dst.slide_height}. Use pres.layout = 'LAYOUT_WIDE'.", file=sys.stderr)
        return 2

    clear_template_slides(dst)
    copier = Copier(dst)
    layouts = {t: find_layout(dst, cfg["master"], n) for t, n in cfg["layouts"].items()}
    missing_svgs, unknown = [], []

    for i, s in enumerate(src.slides, 1):
        kind = slide_type(s)
        if kind not in layouts:
            unknown.append((i, kind))
            kind = "CONTENT"
        layout = layouts[kind]
        d = dst.slides.add_slide(layout)
        strip_placeholders(d)
        copy_shapes(s, d, copier)
        if kind in cfg["slide_number"]:
            add_slide_number(d, layout)
        missing_svgs += embed_svgs(d, copier, Path(args.assets_dir), cfg["bg"])
        copy_notes(s, d)

    dst.save(args.out)
    print(f"OK {args.out}: {len(src.slides)} slides on {args.theme} template "
          f"({', '.join(f'{k}->{v}' for k, v in cfg['layouts'].items())})")
    for i, kind in unknown:
        print(f"WARN slide {i}: unknown type {kind!r}, used CONTENT layout", file=sys.stderr)
    for path in missing_svgs:
        print(f"WARN svg not found, PNG kept without vector: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

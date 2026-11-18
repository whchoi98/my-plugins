#!/usr/bin/env python3
"""Check that a deck made from an infographic stays editable: text boxes, shapes, tables, charts and icon pictures only.

Checks (every slide of the .pptx)
  ERROR  an SVG file is linked to the slide (ppt/media/*.svg) or sits inside a picture (asvg:svgBlip)
  ERROR  a picture that is not an icon: its name does not start with "icon:" (addIcon() sets that name)
  ERROR  an icon picture wider or taller than --icon-max inches: a figure pasted as one picture

Prints one count line per slide (text and shapes, lines, tables, charts, icons) and the result line.

Usage
  python3 check_editable.py <Deck>.pptx [--icon-max 1.2]
Exit 0 when clean, 1 on errors, 2 when the file cannot be read as a deck (no slides, broken XML, or XML with
a DTD, which a deck never has). Standard library only.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
EMU_PER_IN = 914400
ICON_MAX_IN = 1.2   # same limit as ../../aws-ppt-skills/scripts/check_deck.py


def parse_part(data):
    """Parse one slide part. OOXML parts carry no DTD, so one is refused before it reaches the parser
    (no entity expansion from a crafted file)."""
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise ValueError("DTD가 있는 XML")
    return ET.fromstring(data)


def inches(el):
    ext = el.find(f"{P}spPr/{A}xfrm/{A}ext")
    if ext is None:
        return 0.0, 0.0
    return int(ext.get("cx", "0")) / EMU_PER_IN, int(ext.get("cy", "0")) / EMU_PER_IN


def check_slide(no, root, rels, icon_max):
    errors = []
    for target in re.findall(r'Target="([^"]+)"', rels):
        if target.lower().endswith(".svg"):
            errors.append(f"slide {no}: SVG 파일이 연결되어 있음 ({target}) - 그림 대신 도형, 표, 차트로 만든다")
    icons = 0
    for pic in root.iter(f"{P}pic"):
        c_nv_pr = pic.find(f"{P}nvPicPr/{P}cNvPr")
        name = c_nv_pr.get("name", "") if c_nv_pr is not None else ""
        w, h = inches(pic)
        if any(el.tag.endswith("}svgBlip") for el in pic.iter()):
            errors.append(f"slide {no}: 그림 '{name}'에 SVG가 들어 있음 - 아이콘은 icon_png.py의 PNG를 addIcon()으로 넣는다")
        if not name.startswith("icon:"):
            errors.append(f"slide {no}: 아이콘이 아닌 그림 '{name}' ({w:.2f} x {h:.2f} in) - 도형, 표, 차트로 다시 만든다")
        elif max(w, h) > icon_max:
            errors.append(f"slide {no}: 아이콘 '{name}'이 한도보다 큼 ({w:.2f} x {h:.2f} in, 한도 {icon_max:.2f} in) "
                          "- 그림 한 장으로 붙인 도식은 도형으로 다시 만든다")
        else:
            icons += 1
    tables = sum(1 for _ in root.iter(f"{A}tbl"))
    charts = sum(1 for gd in root.iter(f"{A}graphicData") if gd.get("uri", "").endswith("/chart"))
    # pptxgenjs writes a line as a p:sp with the preset geometry "line"; PowerPoint's own connectors are p:cxnSp
    geom = [(sp.find(f"{P}spPr/{A}prstGeom"), sp) for sp in root.iter(f"{P}sp")]
    lines = sum(1 for g, _ in geom if g is not None and g.get("prst") == "line") + sum(1 for _ in root.iter(f"{P}cxnSp"))
    counts = (len(geom) + sum(1 for _ in root.iter(f"{P}cxnSp")) - lines, lines, tables, charts, icons)
    return errors, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--icon-max", type=float, default=ICON_MAX_IN, help="largest icon side in inches (default %(default)s)")
    args = ap.parse_args()
    try:
        z = zipfile.ZipFile(args.deck)
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"덱을 열지 못했습니다: {args.deck} ({exc})", file=sys.stderr)
        return 2
    with z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                       key=lambda n: int(re.search(r"\d+", n.rsplit("/", 1)[1]).group()))
        if not names:
            print(f"슬라이드가 없습니다: {args.deck}", file=sys.stderr)
            return 2
        errors, total = [], 0
        for name in names:
            no = int(re.search(r"\d+", name.rsplit("/", 1)[1]).group())
            rel_name = f"ppt/slides/_rels/slide{no}.xml.rels"
            rels = z.read(rel_name).decode("utf-8", "replace") if rel_name in z.namelist() else ""
            try:
                root = parse_part(z.read(name))
            except (ValueError, ET.ParseError) as exc:
                print(f"슬라이드 XML을 읽지 못했습니다: {name} ({exc})", file=sys.stderr)
                return 2
            errs, counts = check_slide(no, root, rels, args.icon_max)
            errors += errs
            total += sum(counts)
            print("slide %d: 텍스트와 도형 %d, 선 %d, 표 %d, 차트 %d, 아이콘 %d" % ((no,) + counts))
    for msg in errors:
        print("ERROR", msg)
    print(f"결과: ERROR {len(errors)} / 슬라이드 {len(names)}장, 편집 가능한 개체 {total}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

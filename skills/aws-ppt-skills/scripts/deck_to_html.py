#!/usr/bin/env python3
"""Turn a finished aws-ppt-skills deck into one HTML file that is presented in a browser.

The input is the final .pptx, the one apply_template.py wrote. Every slide keeps its content as real HTML:
text boxes, shapes, tables, pictures (the vector SVG when the deck embeds one) and charts drawn as SVG from
the chart data. The template's chrome (background, AWS logo, copyright, page number, "Thank you!") is
rendered with LibreOffice once per layout and placed behind the content as an image, so the page shows the
same template as the deck. Speaker notes go to the presenter view (key N).

The file is self-contained: fonts (subset to the characters the deck uses), pictures, styles and the
script are inside it. It opens from a disk, a mail attachment or any static host without other files.

Usage
  python3 deck_to_html.py <Deck>.pptx [--out <Deck>.html] [--title TEXT] [--lang ko|en]
                          [--no-notes] [--chrome-width 1920]

  --no-notes       leave the speaker notes out (a page that is published can be read by anyone who opens it)
  --chrome-width   pixel width of the template chrome images (1920; 2560 or 3840 for a 4K room)

Needs python-pptx, lxml and Pillow, plus LibreOffice (soffice) and Poppler (pdftoppm) for the chrome.
fontTools is optional: without it the whole font files are embedded and diagrams fall back to their PNG.
Exit code 1 on an error (a raw deck without the template, a missing tool, no slides), 0 otherwise. WARN
lines name what the page shows differently from the deck.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import logging
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from lxml import etree
from pptx import Presentation

SKILL_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = SKILL_DIR / "assets" / "html"
FONT_DIR = SKILL_DIR / "assets" / "fonts"
EMBER_DIR = SKILL_DIR.parent / "aws-diagram-design" / "assets" / "fonts" / "ttf"

# typeface name in the deck or in a diagram SVG -> font file. The templates call the body font
# "NanumSquareOTF Bold"; the other names are the aliases install_fonts.sh registers.
FONT_FILES = {
    "NanumSquareOTF Bold": FONT_DIR / "NanumSquareOTF_acB.otf",
    "나눔스퀘어OTF Bold": FONT_DIR / "NanumSquareOTF_acB.otf",
    "NanumSquareOTF_ac Bold": FONT_DIR / "NanumSquareOTF_acB.otf",
    "NanumSquareOTF_ac": FONT_DIR / "NanumSquareOTF_acB.otf",
    "D2Coding": FONT_DIR / "D2Coding-Ver1.3.2-20180524.ttf",
    "Amazon Ember": EMBER_DIR / "AmazonEmber_Rg.ttf",
    "Amazon Ember Mono": EMBER_DIR / "AmazonEmberMono_Rg.ttf",
}
MONO = {"D2Coding", "Amazon Ember Mono"}
SANS_FALLBACK = '"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif'
MONO_FALLBACK = "ui-monospace,Menlo,Consolas,monospace"

# Line geometry, measured on LibreOffice renders of decks built by this skill (the renderer of the QA step):
# one line is 1.2 x the font size whatever the font, proportional spacing multiplies that, and the extra
# leading goes above the line. LO_DESCENT is the distance from the baseline to the line bottom, in em.
LINE_EM = 1.2
LO_DESCENT = {"D2Coding": 0.242}
LO_DESCENT_DEFAULT = 0.2      # NanumSquareOTF Bold

EMU_PX = 9525.0            # EMU per CSS px at 96 dpi: a 13.333 in slide is 1280 px wide
PT_PX = 96.0 / 72.0
STAGE_W, STAGE_H = 1280, 720

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "asvg": "http://schemas.microsoft.com/office/drawing/2016/SVG/main",
}
TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def q(prefix: str, tag: str) -> str:
    return "{%s}%s" % (NS[prefix], tag)


def local(el) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def n(v: float) -> str:
    """A number for CSS or SVG: two decimals at most, no trailing zeros."""
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def px(emu) -> float:
    return int(emu or 0) / EMU_PX


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def data_uri(mime: str, blob: bytes) -> str:
    return "data:%s;base64,%s" % (mime, base64.b64encode(blob).decode("ascii"))


# --------------------------------------------------------------------------------------- fonts

def font_metrics(path: Path | None) -> tuple[float, float]:
    """(ascent, descent) of a font file in em, from its hhea table: where a browser puts the baseline."""
    try:
        data = path.read_bytes()
        num = struct.unpack(">H", data[4:6])[0]
        tables = {}
        for i in range(num):
            tag, _, off, _ = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
            tables[tag] = off
        upm = float(struct.unpack(">H", data[tables[b"head"] + 18: tables[b"head"] + 20])[0])
        asc, desc = struct.unpack(">hh", data[tables[b"hhea"] + 4: tables[b"hhea"] + 8])
        return asc / upm, -desc / upm
    except Exception:
        return 0.85, 0.25


def subset_font(path: Path, chars: set[str]) -> tuple[bytes, str, bool]:
    """(font bytes, CSS format, subset?) - the glyphs of `chars` as WOFF, or the whole file without fontTools."""
    fmt = "opentype" if path.suffix.lower() == ".otf" else "truetype"
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return path.read_bytes(), fmt, False
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = [1, 2]
    opts.notdef_outline = True
    font = TTFont(str(path))
    sub = subset.Subsetter(options=opts)
    sub.populate(text="".join(sorted(chars | set(" "))))
    sub.subset(font)
    font.flavor = "woff"
    out = io.BytesIO()
    font.save(out)
    return out.getvalue(), "woff", True


def font_face(family: str, blob: bytes, fmt: str) -> str:
    mime = {"woff": "font/woff", "opentype": "font/otf", "truetype": "font/ttf"}[fmt]
    return '@font-face{font-family:"%s";src:url(%s) format("%s");font-display:block}' % (
        re.sub(r"[^\w .\-]", "", family), data_uri(mime, blob), fmt)


def css_family(face: str) -> str:
    """font-family value for a typeface name. The name comes from the deck, so only name characters pass."""
    name = re.sub(r"[^\w .\-]", "", face)
    return '"%s",%s' % (name, MONO_FALLBACK if face in MONO else SANS_FALLBACK)


# --------------------------------------------------------------------------------------- drawing

def color(parent, warn=None) -> str | None:
    """CSS color of the <a:solidFill> under `parent`, None when there is none."""
    if parent is None:
        return None
    fill = parent.find(q("a", "solidFill"))
    if fill is None:
        return None
    clr = fill.find(q("a", "srgbClr"))
    if clr is None:
        if warn:
            warn("테마 색(schemeClr)을 쓴 요소는 색을 옮기지 못했습니다")
        return None
    hexv = clr.get("val", "000000")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", hexv):          # the value goes into CSS as is
        return None
    alpha = clr.find(q("a", "alpha"))
    if alpha is not None and int(alpha.get("val", "100000")) < 100000:
        r, g, b = (int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        return "rgba(%d,%d,%d,%s)" % (r, g, b, n(int(alpha.get("val")) / 100000.0))
    return "#" + hexv


def line_of(sp_pr, tag="ln"):
    """(width px, color, dash list or None, head end, tail end) of an outline, or None when it has none."""
    ln = sp_pr.find(q("a", tag)) if sp_pr is not None else None
    if ln is None or ln.find(q("a", "noFill")) is not None:
        return None
    clr = color(ln)
    if clr is None:
        return None
    w = px(ln.get("w", "9525"))
    if w <= 0:
        return None
    dash = ln.find(q("a", "prstDash"))
    pattern = {"dash": (4, 3), "sysDash": (3, 1), "lgDash": (8, 3), "dot": (1, 3), "sysDot": (1, 1),
               "dashDot": (4, 3, 1, 3), "lgDashDot": (8, 3, 1, 3)}.get(dash.get("val") if dash is not None else "solid")
    ends = []
    for name in ("headEnd", "tailEnd"):
        end = ln.find(q("a", name))
        ends.append(end.get("type") if end is not None and end.get("type", "none") != "none" else None)
    return w, clr, pattern, ends[0], ends[1]


def border_css(line) -> str:
    if not line:
        return ""
    w, clr, pattern, _, _ = line
    return "border:%spx %s %s;" % (n(w), "dashed" if pattern and pattern[0] > 1 else ("dotted" if pattern else "solid"), clr)


# preset shapes beyond rect, roundRect and ellipse, as polygons in a 0..1 box (default adjust values)
POLYGONS = {
    "triangle": [(0.5, 0), (1, 1), (0, 1)],
    "rtTriangle": [(0, 0), (1, 1), (0, 1)],
    "diamond": [(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)],
    "parallelogram": [(0.25, 0), (1, 0), (0.75, 1), (0, 1)],
    "trapezoid": [(0.25, 0), (0.75, 0), (1, 1), (0, 1)],
    "pentagon": [(0.5, 0), (1, 0.38), (0.81, 1), (0.19, 1), (0, 0.38)],
    "hexagon": [(0.25, 0), (0.75, 0), (1, 0.5), (0.75, 1), (0.25, 1), (0, 0.5)],
    "octagon": [(0.29, 0), (0.71, 0), (1, 0.29), (1, 0.71), (0.71, 1), (0.29, 1), (0, 0.71), (0, 0.29)],
    "plus": [(0.25, 0), (0.75, 0), (0.75, 0.25), (1, 0.25), (1, 0.75), (0.75, 0.75), (0.75, 1), (0.25, 1),
             (0.25, 0.75), (0, 0.75), (0, 0.25), (0.25, 0.25)],
}


def polygon_points(prst: str, w: float, h: float):
    """Corner points of a preset shape in px, None for a preset this script does not draw."""
    if prst in POLYGONS:
        return [(x * w, y * h) for x, y in POLYGONS[prst]]
    a = min(w, h) * 0.5                               # arrows and chevrons keep their head at half the short side
    if prst == "chevron":
        return [(0, 0), (w - a, 0), (w, h / 2), (w - a, h), (0, h), (a, h / 2)]
    if prst == "homePlate":
        return [(0, 0), (w - a, 0), (w, h / 2), (w - a, h), (0, h)]
    if prst == "rightArrow":
        return [(0, h * 0.25), (w - a, h * 0.25), (w - a, 0), (w, h / 2), (w - a, h), (w - a, h * 0.75), (0, h * 0.75)]
    if prst == "leftArrow":
        return [(w, h * 0.25), (a, h * 0.25), (a, 0), (0, h / 2), (a, h), (a, h * 0.75), (w, h * 0.75)]
    if prst == "downArrow":
        return [(w * 0.25, 0), (w * 0.75, 0), (w * 0.75, h - a), (w, h - a), (w / 2, h), (0, h - a), (w * 0.25, h - a)]
    if prst == "upArrow":
        return [(w * 0.25, h), (w * 0.75, h), (w * 0.75, a), (w, a), (w / 2, 0), (0, a), (w * 0.25, a)]
    return None


# --------------------------------------------------------------------------------------- number formats

def general(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return "{:,}".format(int(round(v))) if abs(v) >= 10000 else str(int(round(v)))
    return ("%.2f" % v).rstrip("0").rstrip(".")


def format_number(v, code: str | None) -> str:
    """A value under an Excel number format: literals in quotes, %, thousands separators, decimals."""
    if v is None:
        return ""
    sec = (code or "General").split(";")[0]
    bare = re.sub(r'"[^"]*"', "", sec)
    m = re.search(r"[#0][#0,]*(\.[#0]+)?", bare)
    if "general" in bare.lower() or not m:
        return general(v)
    val = v * 100 if "%" in bare else v
    dec = len(m.group(1)) - 1 if m.group(1) else 0
    num = ("{:,.%df}" if "," in m.group(0) else "{:.%df}") % dec
    num = num.format(val)
    # put the number where the placeholder was, then drop the quotes around the literals
    start = sec.find(m.group(0))
    out = sec[:start] + num + sec[start + len(m.group(0)):]
    return out.replace('"', "").replace("\\", "")


def nice_scale(lo: float, hi: float, target: int = 5):
    """(lo, hi, step) with round tick values that cover lo..hi."""
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / max(1, target)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw - 1e-12)
    return math.floor(lo / step + 1e-9) * step, math.ceil(hi / step - 1e-9) * step, step


def text_width(text: str, size: float) -> float:
    """Rough width of a label in px: CJK glyphs are one em wide, the rest a little over half."""
    return sum(1.0 if ord(ch) > 0x2E7F else 0.56 for ch in text) * size


# --------------------------------------------------------------------------------------- converter

class Deck:
    def __init__(self, path: Path, args):
        self.path = path
        self.args = args
        self.prs = Presentation(str(path))
        self.warnings: list[str] = []
        self.chars: dict[str, set[str]] = {}       # typeface -> characters, for the font subset
        self.classes: dict[str, str] = {}          # style text -> class name
        self.images: dict[str, str] = {}           # sha1 -> class name
        self.image_css: list[str] = []
        self.stats = {"charts": 0, "tables": 0, "pictures": 0, "svg": 0, "notes": 0}
        self.marker_id = 0
        self.slide_no = 0
        self.metrics: dict[str, tuple[float, float]] = {}
        self.have_fonttools = True
        try:
            import fontTools  # noqa: F401
        except ImportError:
            self.have_fonttools = False

    # ---- small helpers ----
    def warn(self, msg: str) -> None:
        line = "slide %d: %s" % (self.slide_no, msg) if self.slide_no else msg
        if line not in self.warnings:
            self.warnings.append(line)

    def cls(self, style: str) -> str:
        """Class name for a style text; the same text gets the same class, so the page stays small."""
        if style not in self.classes:
            self.classes[style] = "k%d" % len(self.classes)
        return self.classes[style]

    def use(self, face: str, text: str) -> None:
        self.chars.setdefault(face, set()).update(text)

    def baseline_shift(self, face: str, line_em: float) -> float:
        """How far (em) a line must move down so its baseline sits where the deck's renderer puts it.

        CSS centers the glyphs in the line box; the deck puts the baseline LO_DESCENT above the line bottom.
        """
        if face not in self.metrics:
            self.metrics[face] = font_metrics(FONT_FILES.get(face))
        asc, desc = self.metrics[face]
        return line_em / 2.0 - (asc - desc) / 2.0 - LO_DESCENT.get(face, LO_DESCENT_DEFAULT)

    def image_class(self, mime: str, blob: bytes) -> str:
        key = hashlib.sha1(blob).hexdigest()
        if key not in self.images:
            self.images[key] = "im%d" % len(self.images)
            self.image_css.append(".%s{background-image:url(%s)}" % (self.images[key], data_uri(mime, blob)))
        return self.images[key]

    # ---- text ----
    def run_style(self, r_pr, scale: float = 1.0):
        """(css, typeface, size px) of a run."""
        size = int(r_pr.get("sz", "1800")) / 100.0 * PT_PX * scale if r_pr is not None else 18 * PT_PX
        css = ["font-size:%spx" % n(size)]
        face = "NanumSquareOTF Bold"
        if r_pr is not None:
            latin = r_pr.find(q("a", "latin"))
            ea = r_pr.find(q("a", "ea"))
            face = (latin if latin is not None else ea).get("typeface", face) if (latin is not None or ea is not None) else face
            clr = color(r_pr, self.warn)
            if clr:
                css.append("color:" + clr)
            if r_pr.get("b") == "1":
                css.append("font-weight:700")
            if r_pr.get("i") == "1":
                css.append("font-style:italic")
            deco = [d for d, on in (("underline", r_pr.get("u", "none") != "none"),
                                    ("line-through", r_pr.get("strike", "noStrike") != "noStrike")) if on]
            if deco:
                css.append("text-decoration:" + " ".join(deco))
            if r_pr.get("spc"):
                css.append("letter-spacing:%spx" % n(int(r_pr.get("spc")) / 100.0 * PT_PX))
            if r_pr.get("baseline") and int(r_pr.get("baseline")) != 0:
                css.append("vertical-align:%s;font-size:%spx" % ("super" if int(r_pr.get("baseline")) > 0 else "sub", n(size * 0.65)))
        css.append("font-family:" + css_family(face))
        return ";".join(css), face, size

    def paragraphs(self, tx_body, rels) -> str:
        """The paragraphs of a text body as <p> elements."""
        body_pr = tx_body.find(q("a", "bodyPr"))
        fit = body_pr.find(q("a", "normAutofit")) if body_pr is not None else None
        scale = int(fit.get("fontScale", "100000")) / 100000.0 if fit is not None else 1.0
        out = []
        for para in tx_body.findall(q("a", "p")):
            p_pr = para.find(q("a", "pPr"))      # pptxgenjs repeats <a:pPr> before every run; the first one counts
            runs, first = [], None
            for child in para:
                kind = local(child)
                if kind == "br":
                    runs.append("<br>")
                elif kind in ("r", "fld"):
                    r_pr = child.find(q("a", "rPr"))
                    text = "".join(t.text or "" for t in child.findall(q("a", "t")))
                    if kind == "fld" and child.get("type") == "slidenum":
                        text = str(self.slide_no)
                    css, face, size = self.run_style(r_pr, scale)
                    self.use(face, text)
                    first = first or (css, face, size)
                    piece = esc(text)
                    link = r_pr.find(q("a", "hlinkClick")) if r_pr is not None else None
                    if link is not None:
                        rid = link.get(q("r", "id"))
                        url = rels[rid].target_ref if rid in rels and rels[rid].is_external else ""
                        if re.match(r"(?i)^(https?://|mailto:)", url):
                            piece = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), piece)
                    runs.append((css, piece))
            if first is None:                    # an empty paragraph still takes a line of its size
                end = para.find(q("a", "endParaRPr"))
                first = self.run_style(end, scale)
                runs.append((first[0], "&#8203;"))
            css, face, size = first
            style = [css]
            line_em = LINE_EM
            if p_pr is not None:
                algn = {"ctr": "center", "r": "right", "just": "justify"}.get(p_pr.get("algn", "l"))
                if algn:
                    style.append("text-align:" + algn)
                spc_pct = p_pr.find("%s/%s" % (q("a", "lnSpc"), q("a", "spcPct")))
                spc_pts = p_pr.find("%s/%s" % (q("a", "lnSpc"), q("a", "spcPts")))
                if spc_pts is not None:
                    line_em = int(spc_pts.get("val")) / 100.0 * PT_PX / size
                elif spc_pct is not None:
                    line_em = LINE_EM * int(spc_pct.get("val")) / 100000.0
                for tag, prop in (("spcBef", "margin-top"), ("spcAft", "margin-bottom")):
                    pts = p_pr.find("%s/%s" % (q("a", tag), q("a", "spcPts")))
                    if pts is not None and int(pts.get("val")) > 0:
                        style.append("%s:%spx" % (prop, n(int(pts.get("val")) / 100.0 * PT_PX)))
                mar, ind = px(p_pr.get("marL", "0")), px(p_pr.get("indent", "0"))
                if mar:
                    style.append("padding-left:%spx" % n(mar))
                if ind:
                    style.append("text-indent:%spx" % n(ind))
            style.append("line-height:%s" % n(line_em))
            shift = self.baseline_shift(face, line_em) * size
            if abs(shift) >= 0.5:
                style.append("position:relative;top:%spx" % n(shift))
            inner = []
            bu = p_pr.find(q("a", "buChar")) if p_pr is not None else None
            if bu is not None:
                bu_css = ["width:%spx" % n(abs(px(p_pr.get("indent", "0"))) or size)]
                bu_clr = color(p_pr.find(q("a", "buClr")))
                if bu_clr:
                    bu_css.append("color:" + bu_clr)
                bu_font = p_pr.find(q("a", "buFont"))
                bu_face = bu_font.get("typeface") if bu_font is not None else face
                bu_css.append("font-family:" + css_family(bu_face))
                self.use(bu_face, bu.get("char", "•"))
                inner.append('<span class="bu %s">%s</span>' % (self.cls(";".join(bu_css)), esc(bu.get("char", "•"))))
            for run in runs:
                if run == "<br>":
                    inner.append(run)
                elif run[0] == css:
                    inner.append(run[1])
                else:
                    inner.append('<span class="%s">%s</span>' % (self.cls(run[0]), run[1]))
            out.append('<p class="%s">%s</p>' % (self.cls(";".join(style)), "".join(inner)))
        return "".join(out)

    # ---- shapes ----
    def box(self, xfrm) -> tuple[float, float, float, float, str]:
        off, ext = xfrm.find(q("a", "off")), xfrm.find(q("a", "ext"))
        x, y, w, h = px(off.get("x")), px(off.get("y")), px(ext.get("cx")), px(ext.get("cy"))
        tf = []
        if xfrm.get("rot") and int(xfrm.get("rot")):
            tf.append("rotate(%sdeg)" % n(int(xfrm.get("rot")) / 60000.0))
        return x, y, w, h, ("transform:%s;" % " ".join(tf)) if tf else ""

    def shape(self, sp, rels) -> str:
        sp_pr = sp.find(q("p", "spPr"))
        xfrm = sp_pr.find(q("a", "xfrm")) if sp_pr is not None else None
        if xfrm is None:
            self.warn("위치 정보가 없는 도형은 옮기지 않았습니다")
            return ""
        x, y, w, h, tf = self.box(xfrm)
        geom = sp_pr.find(q("a", "prstGeom"))
        prst = geom.get("prst", "rect") if geom is not None else "rect"
        fill = color(sp_pr, self.warn)
        line = line_of(sp_pr)
        pos = "left:%spx;top:%spx;width:%spx;height:%spx;" % (n(x), n(y), n(w), n(h))
        tx_body = sp.find(q("p", "txBody"))
        has_text = tx_body is not None and any((t.text or "").strip() for t in tx_body.iter(q("a", "t")))
        out = []

        if prst in ("line", "straightConnector1"):
            return self.line(xfrm, x, y, w, h, line)

        deco = ""
        if prst in ("rect", "roundRect", "ellipse"):
            if fill:
                deco += "background:%s;" % fill
            deco += border_css(line)
            if prst == "roundRect":
                adj = 16667
                gd = geom.find("%s/%s" % (q("a", "avLst"), q("a", "gd")))
                if gd is not None and gd.get("fmla", "").startswith("val "):
                    adj = int(gd.get("fmla")[4:])
                deco += "border-radius:%spx;" % n(min(w, h) * min(adj, 50000) / 100000.0)
            elif prst == "ellipse":
                deco += "border-radius:50%;"
            shadow = sp_pr.find("%s/%s" % (q("a", "effectLst"), q("a", "outerShdw")))
            if shadow is not None:
                dist, ang = px(shadow.get("dist", "0")), int(shadow.get("dir", "0")) / 60000.0
                deco += "box-shadow:%spx %spx %spx %s;" % (n(dist * math.cos(math.radians(ang))), n(dist * math.sin(math.radians(ang))),
                                                         n(px(shadow.get("blurRad", "0"))), color(shadow) or "rgba(0,0,0,.35)")
        else:
            pts = polygon_points(prst, w, h)
            if pts is None:
                self.warn("도형 '%s'은(는) 사각형으로 표시했습니다" % prst)
                pts = [(0, 0), (w, 0), (w, h), (0, h)]
            stroke = ' stroke="%s" stroke-width="%s"' % (line[1], n(line[0])) if line else ""
            out.append('<svg class="geo" style="%s%s" viewBox="0 0 %s %s"><polygon points="%s" fill="%s"%s/></svg>'
                       % (pos, tf, n(w), n(h), " ".join("%s,%s" % (n(a), n(b)) for a, b in pts), fill or "none", stroke))

        if has_text:
            body_pr = tx_body.find(q("a", "bodyPr"))
            get = (lambda k, d: px(body_pr.get(k, d))) if body_pr is not None else (lambda k, d: px(d))
            pad = "padding:%spx %spx %spx %spx;" % (n(get("tIns", "45720")), n(get("rIns", "91440")), n(get("bIns", "45720")), n(get("lIns", "91440")))
            anchor = body_pr.get("anchor", "t") if body_pr is not None else "t"
            wrap = "white-space:nowrap;" if body_pr is not None and body_pr.get("wrap") == "none" else ""
            klass = "tx" + {"t": " at", "b": " ab"}.get(anchor, "")
            out.append('<div class="%s" style="%s%s%s%s%s">%s</div>' % (klass, pos, pad, deco, wrap, tf, self.paragraphs(tx_body, rels)))
        elif deco:
            out.append('<div style="%s%s%s"></div>' % (pos, deco, tf))
        return "".join(out)

    def line(self, xfrm, x, y, w, h, line) -> str:
        if not line:
            return ""
        width, clr, pattern, head, tail = line
        x1, y1, x2, y2 = 0.0, 0.0, w, h
        if xfrm.get("flipH") == "1":
            x1, x2 = x2, x1
        if xfrm.get("flipV") == "1":
            y1, y2 = y2, y1
        defs, attrs = "", ""
        for end, where in ((head, "start"), (tail, "end")):
            if not end:
                continue
            self.marker_id += 1
            mid = "m%d" % self.marker_id
            shape = {"oval": '<circle cx="5" cy="5" r="4"/>', "diamond": '<path d="M0 5 5 0 10 5 5 10z"/>'}.get(end, '<path d="M0 0 10 5 0 10z"/>')
            defs += ('<marker id="%s" viewBox="0 0 10 10" refX="%s" refY="5" markerWidth="4" markerHeight="4" '
                     'orient="auto-start-reverse" fill="%s">%s</marker>') % (mid, "9" if end not in ("oval", "diamond") else "5", clr, shape)
            attrs += ' marker-%s="url(#%s)"' % (where, mid)
        dash = ' stroke-dasharray="%s"' % " ".join(n(v * width) for v in pattern) if pattern else ""
        return ('<svg class="ln" style="left:%spx;top:%spx;width:%spx;height:%spx">%s<line x1="%s" y1="%s" x2="%s" y2="%s" '
                'stroke="%s" stroke-width="%s"%s%s/></svg>') % (n(x), n(y), n(max(w, 1)), n(max(h, 1)), "<defs>%s</defs>" % defs if defs else "",
                                                               n(x1), n(y1), n(x2), n(y2), clr, n(width), dash, attrs)

    # ---- pictures ----
    def svg_with_fonts(self, blob: bytes) -> bytes | None:
        """The diagram SVG with the fonts it names embedded, None when that cannot be done here.

        A picture shown through CSS cannot use the page's fonts, so the SVG carries its own subset.
        """
        text = blob.decode("utf-8", "replace")
        if re.search(r'(?i)(href|src)\s*=\s*["\']\s*https?://', text):
            self.warn("다이어그램 SVG가 외부 주소를 참조합니다. 오프라인에서는 그 부분이 비어 보입니다")
        faces = [f for f in FONT_FILES if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(f), text) and FONT_FILES[f].is_file()]
        if not faces:
            return blob
        if not self.have_fonttools:
            return None
        try:
            root = etree.fromstring(blob, etree.XMLParser(huge_tree=True))
        except etree.XMLSyntaxError:
            return None
        chars = set("".join(root.itertext()))
        css = []
        for face in faces:
            data, fmt, _ = subset_font(FONT_FILES[face], chars)
            css.append(font_face(face, data, fmt))
        style = etree.Element("{http://www.w3.org/2000/svg}style" if root.tag.startswith("{") else "style")
        style.text = "".join(css)
        root.insert(0, style)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    def picture(self, pic, part) -> str:
        sp_pr = pic.find(q("p", "spPr"))
        xfrm = sp_pr.find(q("a", "xfrm")) if sp_pr is not None else None
        blip = pic.find("%s/%s" % (q("p", "blipFill"), q("a", "blip")))
        if xfrm is None or blip is None or blip.get(q("r", "embed")) not in part.rels:
            self.warn("그림 하나를 옮기지 못했습니다")
            return ""
        x, y, w, h, tf = self.box(xfrm)
        target = part.rels[blip.get(q("r", "embed"))].target_part
        mime, blob = target.content_type, target.blob
        svg = blip.find(".//" + q("asvg", "svgBlip"))
        if svg is not None and svg.get(q("r", "embed")) in part.rels:
            vector = self.svg_with_fonts(part.rels[svg.get(q("r", "embed"))].target_part.blob)
            if vector is not None:
                mime, blob = "image/svg+xml", vector
                self.stats["svg"] += 1
            else:
                self.warn("fontTools가 없어 다이어그램을 SVG 대신 PNG로 넣었습니다(my-plugins:setup)")
        self.stats["pictures"] += 1
        c_nv = pic.find("%s/%s" % (q("p", "nvPicPr"), q("p", "cNvPr")))
        alt = (c_nv.get("descr") or "").strip() if c_nv is not None else ""
        geom = sp_pr.find(q("a", "prstGeom"))
        style = "left:%spx;top:%spx;width:%spx;height:%spx;%s" % (n(x), n(y), n(w), n(h), tf)
        if geom is not None and geom.get("prst") == "ellipse":
            style += "border-radius:50%;"
        crop = pic.find("%s/%s" % (q("p", "blipFill"), q("a", "srcRect")))
        if crop is not None:
            l, t, r, b = (int(crop.get(k, "0")) / 100000.0 for k in ("l", "t", "r", "b"))
            fw, fh = w / max(0.01, 1 - l - r), h / max(0.01, 1 - t - b)
            style += "background-size:%spx %spx;background-position:%spx %spx;" % (n(fw), n(fh), n(-l * fw), n(-t * fh))
        label = ' role="img" aria-label="%s"' % esc(alt) if alt else ' aria-hidden="true"'
        return '<div class="pic %s" style="%s"%s></div>' % (self.image_class(mime, blob), style, label)

    # ---- tables ----
    def table(self, frame, tbl, rels) -> str:
        xfrm = frame.find(q("p", "xfrm"))
        x, y, _, _, _ = self.box(xfrm)
        cols = [px(c.get("w")) for c in tbl.find(q("a", "tblGrid")).findall(q("a", "gridCol"))]
        out = ['<table style="left:%spx;top:%spx;width:%spx"><colgroup>%s</colgroup>'
               % (n(x), n(y), n(sum(cols)), "".join('<col style="width:%spx">' % n(c) for c in cols))]
        for tr in tbl.findall(q("a", "tr")):
            out.append('<tr style="height:%spx">' % n(px(tr.get("h"))))
            for tc in tr.findall(q("a", "tc")):
                if tc.get("hMerge") == "1" or tc.get("vMerge") == "1":
                    continue
                tc_pr = tc.find(q("a", "tcPr"))
                get = (lambda k, d: px(tc_pr.get(k, d))) if tc_pr is not None else (lambda k, d: px(d))
                css = ["padding:%spx %spx %spx %spx" % (n(get("marT", "45720")), n(get("marR", "91440")), n(get("marB", "45720")), n(get("marL", "91440")))]
                css.append("vertical-align:" + {"ctr": "middle", "b": "bottom"}.get(tc_pr.get("anchor", "t") if tc_pr is not None else "t", "top"))
                fill = color(tc_pr, self.warn)
                if fill:
                    css.append("background:" + fill)
                for tag, side in (("lnL", "left"), ("lnR", "right"), ("lnT", "top"), ("lnB", "bottom")):
                    line = line_of(tc_pr, tag)
                    if line:
                        css.append("border-%s:%spx solid %s" % (side, n(line[0]), line[1]))
                span = ""
                if tc.get("gridSpan"):
                    span += ' colspan="%s"' % int(tc.get("gridSpan"))
                if tc.get("rowSpan"):
                    span += ' rowspan="%s"' % int(tc.get("rowSpan"))
                tx_body = tc.find(q("a", "txBody"))
                out.append('<td class="%s"%s>%s</td>' % (self.cls(";".join(css)), span, self.paragraphs(tx_body, rels) if tx_body is not None else ""))
            out.append("</tr>")
        out.append("</table>")
        self.stats["tables"] += 1
        return "".join(out)

    # ---- charts ----
    def chart(self, frame, chart_part) -> str:
        xfrm = frame.find(q("p", "xfrm"))
        x, y, w, h, _ = self.box(xfrm)
        root = etree.fromstring(chart_part.blob)
        try:
            chart = Chart(self, root, w, h)
            body = chart.render()
        except Unsupported as e:
            self.warn("차트(%s)는 HTML에서 그리지 못해 비워 두었습니다" % e)
            return ""
        self.stats["charts"] += 1
        return '<svg class="chart %s" style="left:%spx;top:%spx;width:%spx;height:%spx" viewBox="0 0 %s %s" role="img" aria-label="%s">%s</svg>' % (
            self.cls("font-family:" + css_family(chart.face)), n(x), n(y), n(w), n(h), n(w), n(h), esc(chart.label), body)

    # ---- slides ----
    def slide_html(self, slide, index: int, chrome: str) -> str:
        self.slide_no = index
        part = slide.part
        items = []
        texts = []                                  # (size, text) of the text boxes, for the slide title
        for el in slide.shapes._spTree.iterchildren():
            kind = local(el)
            if kind == "sp":
                if el.find("%s/%s/%s" % (q("p", "nvSpPr"), q("p", "nvPr"), q("p", "ph"))) is not None:
                    continue                        # placeholders (the page number) belong to the chrome
                items.append(self.shape(el, part.rels))
                for para in el.iter(q("a", "p")):
                    text = "".join(t.text or "" for t in para.iter(q("a", "t"))).strip()
                    r_pr = para.find("%s/%s" % (q("a", "r"), q("a", "rPr")))
                    if text and r_pr is not None:
                        texts.append((int(r_pr.get("sz", "0")), text))
            elif kind == "cxnSp":
                sp_pr = el.find(q("p", "spPr"))
                xfrm = sp_pr.find(q("a", "xfrm")) if sp_pr is not None else None
                if xfrm is not None:
                    bx = self.box(xfrm)
                    items.append(self.line(xfrm, bx[0], bx[1], bx[2], bx[3], line_of(sp_pr)))
            elif kind == "pic":
                items.append(self.picture(el, part))
            elif kind == "graphicFrame":
                data = el.find("%s/%s" % (q("a", "graphic"), q("a", "graphicData")))
                uri = data.get("uri") if data is not None else ""
                if uri == TABLE_URI:
                    items.append(self.table(el, data.find(q("a", "tbl")), part.rels))
                elif uri == CHART_URI:
                    rid = data.find(q("c", "chart")).get(q("r", "id"))
                    items.append(self.chart(el, part.rels[rid].target_part))
                else:
                    self.warn("지원하지 않는 개체(graphicFrame)를 건너뛰었습니다")
            elif kind == "grpSp":
                self.warn("그룹 도형은 옮기지 않았습니다. 그룹을 풀어 다시 빌드하세요")
        title = max(texts, key=lambda t: t[0])[1] if texts else ""
        notes = ""
        if not self.args.no_notes and slide.has_notes_slide:
            lines = [ln.strip() for ln in re.split(r"[\r\n\v]+", slide.notes_slide.notes_text_frame.text) if ln.strip()]
            if lines:
                self.stats["notes"] += 1
                notes = '<aside class="notes">%s</aside>' % "".join("<p>%s</p>" % esc(ln) for ln in lines)
        self.slide_no = 0
        return ('<section class="slide" id="s%d" data-layout="%s" data-title="%s" aria-label="%s">%s%s%s</section>'
                % (index, esc(slide.slide_layout.name or ""), esc(title), esc("%d. %s" % (index, title)), chrome, "".join(items), notes)), title


# --------------------------------------------------------------------------------------- charts as SVG

class Unsupported(Exception):
    pass


class Chart:
    """One chart drawn as SVG from the cached data of the chart part. Sizes are stage px."""

    def __init__(self, deck: Deck, root, w: float, h: float):
        self.deck, self.w, self.h = deck, w, h
        plot = root.find(".//" + q("c", "plotArea"))
        kinds = [el for el in plot if local(el).endswith("Chart")] if plot is not None else []
        if not kinds:
            raise Unsupported("종류를 알 수 없음")
        self.el = kinds[0]
        self.kind = local(self.el)[:-5]
        if self.kind not in ("bar", "line", "area", "pie", "doughnut", "scatter", "radar"):
            raise Unsupported(self.kind)
        if len(kinds) > 1:
            deck.warn("여러 종류를 겹친 차트는 첫 종류(%s)만 그렸습니다" % self.kind)
        self.plot = plot
        self.face = "NanumSquareOTF Bold"
        self.series = [self.read_series(s) for s in self.el.findall(q("c", "ser"))]
        if not self.series:
            raise Unsupported("데이터 없음")
        legend = root.find(".//" + q("c", "legend"))
        self.legend = None
        if legend is not None:
            pos = legend.find(q("c", "legendPos"))
            self.legend = (pos.get("val") if pos is not None else "r",) + self.text_style(legend)
        title = root.find("%s/%s" % (q("c", "chart"), q("c", "title")))
        self.title = None
        if title is not None:
            text = "".join(t.text or "" for t in title.iter(q("a", "t")))
            r_pr = title.find(".//" + q("a", "rPr"))
            size = int(r_pr.get("sz", "1600")) / 100.0 * PT_PX if r_pr is not None else 16 * PT_PX
            self.title = (text, size, color(r_pr) or "#888888")
        self.label = (self.title[0] if self.title else "") or ", ".join(s["name"] for s in self.series if s["name"]) or "chart"
        self.out: list[str] = []

    # ---- reading ----
    def val(self, el, tag, default=None):
        node = el.find(q("c", tag)) if el is not None else None
        return node.get("val", default) if node is not None else default

    def text_style(self, el):
        """(size px, color, bold) from the <c:txPr> of an axis, a legend or the data labels."""
        r_pr = el.find("%s//%s" % (q("c", "txPr"), q("a", "defRPr"))) if el is not None else None
        if r_pr is None:
            return 12 * PT_PX, "#888888", False
        latin = r_pr.find(q("a", "latin"))
        if latin is not None and latin.get("typeface"):
            self.face = latin.get("typeface")
        return int(r_pr.get("sz", "1200")) / 100.0 * PT_PX, color(r_pr) or "#888888", r_pr.get("b") == "1"

    def points(self, el, numeric: bool):
        if el is None:
            return []
        cache = next((c for c in el.iter() if local(c) in ("numCache", "strCache", "lvl", "numLit", "strLit")), None)
        if cache is None:
            return []
        pts = {}
        for pt in cache.findall(q("c", "pt")):
            v = pt.find(q("c", "v"))
            pts[int(pt.get("idx", "0"))] = v.text if v is not None else None
        count = max(pts) + 1 if pts else 0
        out = []
        for i in range(count):
            raw = pts.get(i)
            if numeric:
                try:
                    out.append(float(raw))
                except (TypeError, ValueError):
                    out.append(None)
            else:
                out.append(raw or "")
        return out

    def read_series(self, ser):
        sp_pr = ser.find(q("c", "spPr"))
        line = line_of(sp_pr)
        marker = ser.find(q("c", "marker"))
        d_lbls = ser.find(q("c", "dLbls"))
        if d_lbls is None:
            d_lbls = self.el.find(q("c", "dLbls"))
        first = d_lbls.find(q("c", "dLbl")) if d_lbls is not None else None     # pie charts set the labels per point
        src = first if first is not None else d_lbls
        fmt = src.find(q("c", "numFmt")) if src is not None else None
        return {
            "name": "".join(v.text or "" for v in ser.findall("%s//%s" % (q("c", "tx"), q("c", "v")))),
            "fill": color(sp_pr) or "#888888",
            "line": line,
            "points": {int(self.val(d, "idx", "0")): color(d.find(q("c", "spPr"))) for d in ser.findall(q("c", "dPt"))},
            "cats": self.points(ser.find(q("c", "cat")), False),
            "vals": self.points(ser.find(q("c", "val")), True),
            "x": self.points(ser.find(q("c", "xVal")), True),
            "y": self.points(ser.find(q("c", "yVal")), True),
            "marker": None if marker is None or self.val(marker, "symbol", "none") == "none" else int(self.val(marker, "size", "5")) * PT_PX / 2.0,
            "show": self.val(src, "showVal") == "1", "percent": self.val(src, "showPercent") == "1",
            "fmt": fmt.get("formatCode") if fmt is not None else None,
            "pos": self.val(src, "dLblPos"), "label": self.text_style(src),
        }

    def axis(self, tag: str, pos: tuple[str, ...]):
        for ax in self.plot.findall(q("c", tag)):
            if self.val(ax, "axPos") in pos:
                fmt = ax.find(q("c", "numFmt"))
                scaling = ax.find(q("c", "scaling"))
                grid = ax.find(q("c", "majorGridlines"))
                num = lambda t: float(self.val(scaling, t)) if self.val(scaling, t) is not None else None  # noqa: E731
                line = line_of(ax.find(q("c", "spPr")))
                return {"hidden": self.val(ax, "delete") == "1", "fmt": fmt.get("formatCode") if fmt is not None else None,
                        "text": self.text_style(ax), "min": num("min"), "max": num("max"), "line": line[1] if line else None,
                        "grid": (line_of(grid.find(q("c", "spPr"))) or (0.75, "#888888"))[:2] if grid is not None else None,
                        "between": self.val(ax, "crossBetween", "between")}
        return {"hidden": True, "fmt": None, "text": (12 * PT_PX, "#888888", False), "min": None, "max": None, "line": None, "grid": None, "between": "between"}

    # ---- drawing ----
    def text(self, x, y, s, size, fill, anchor="middle", bold=False, baseline="central"):
        if s == "":
            return
        self.deck.use(self.face, s)
        self.out.append('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" dominant-baseline="%s"%s>%s</text>'
                        % (n(x), n(y), n(size), fill, anchor, baseline, ' font-weight="700"' if bold else "", esc(s)))

    def render(self) -> str:
        left, top, right, bottom = 4.0, 4.0, self.w - 4.0, self.h - 4.0
        if self.title:
            text, size, fill = self.title
            self.text(self.w / 2, top + size * 0.7, text, size, fill)
            top += size * 1.6
        if self.legend:
            pos, size, fill, _ = self.legend
            if self.kind in ("pie", "doughnut"):
                s = self.series[0]
                items = [(c, s["points"].get(i) or s["fill"]) for i, c in enumerate(s["cats"])]
            else:
                items = [(s["name"], (s["line"][1] if self.kind in ("line", "scatter", "radar") and s["line"] else s["fill"])) for s in self.series]
            sw = size * 0.62
            widths = [sw + size * 0.35 + text_width(t, size) for t, _ in items]
            if pos in ("b", "t"):
                gap = size * 1.1
                x = (self.w - sum(widths) - gap * (len(items) - 1)) / 2
                y = bottom - size * 0.75 if pos == "b" else top + size * 0.75
                for (label, clr), width in zip(items, widths):
                    self.out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (n(x), n(y - sw / 2), n(sw), n(sw), clr))
                    self.text(x + sw + size * 0.35, y, label, size, fill, "start")
                    x += width + gap
                if pos == "b":
                    bottom -= size * 1.9
                else:
                    top += size * 1.9
            else:
                col = max(widths) + size * 0.4
                x = right - col if pos != "l" else left
                y = (top + bottom) / 2 - (len(items) - 1) * size * 0.8
                for label, clr in items:
                    self.out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (n(x), n(y - sw / 2), n(sw), n(sw), clr))
                    self.text(x + sw + size * 0.35, y, label, size, fill, "start")
                    y += size * 1.6
                if pos == "l":
                    left += col
                else:
                    right -= col
        box = (left, top, right, bottom)
        if self.kind in ("pie", "doughnut"):
            self.pie(box)
        elif self.kind == "radar":
            self.radar(box)
        elif self.kind == "scatter":
            self.scatter(box)
        else:
            self.cartesian(box)
        return "".join(self.out)

    def value_axis(self, ax, lo, hi, length):
        """Tick values of a value axis: (lo, hi, ticks)."""
        if ax["min"] is not None:
            lo = ax["min"]
        if ax["max"] is not None:
            hi = ax["max"]
        a, b, step = nice_scale(lo, hi, max(3, min(8, int(length / 30))))
        if ax["min"] is not None:
            a = ax["min"]
        if ax["max"] is not None:
            b = ax["max"]
        ticks, v = [], a
        while v <= b + step * 1e-6:
            ticks.append(round(v, 10))
            v += step
        return a, b, ticks

    def cartesian(self, box):
        left, top, right, bottom = box
        horizontal = self.kind == "bar" and self.val(self.el, "barDir", "col") == "bar"
        grouping = self.val(self.el, "grouping", "clustered" if self.kind == "bar" else "standard")
        stacked, percent = grouping in ("stacked", "percentStacked"), grouping == "percentStacked"
        cats = max((s["cats"] for s in self.series), key=len)
        count = max(len(cats), max(len(s["vals"]) for s in self.series))
        cats = cats + [""] * (count - len(cats))
        cat_ax = self.axis("catAx", ("l",) if horizontal else ("b",))
        val_ax = self.axis("valAx", ("b",) if horizontal else ("l",))

        def value(s, i):
            return s["vals"][i] if i < len(s["vals"]) and s["vals"][i] is not None else 0.0

        totals = [sum(abs(value(s, i)) for s in self.series) or 1.0 for i in range(count)]
        if percent:
            lo, hi = 0.0, 1.0
        elif stacked:
            hi = max(sum(max(0.0, value(s, i)) for s in self.series) for i in range(count))
            lo = min(0.0, min(sum(min(0.0, value(s, i)) for s in self.series) for i in range(count)))
        else:
            every = [value(s, i) for s in self.series for i in range(count)]
            lo, hi = min(0.0, min(every)), max(0.0, max(every))
        fmt = "0%" if percent else val_ax["fmt"]
        v_size, v_fill, _ = val_ax["text"]
        c_size, c_fill, _ = cat_ax["text"]

        # room for the axis labels, then the scale
        any_labels = any(s["show"] for s in self.series)
        if horizontal:
            if not cat_ax["hidden"]:
                left += max(text_width(c, c_size) for c in cats) + c_size * 0.6
            if not val_ax["hidden"]:
                bottom -= v_size * 1.7
            if any_labels and not stacked:
                right -= v_size * 3.0
            lo, hi, ticks = self.value_axis(val_ax, lo, hi, right - left)
            if not val_ax["hidden"]:
                right -= text_width(format_number(ticks[-1], fmt), v_size) / 2
        else:
            if not cat_ax["hidden"]:
                bottom -= c_size * 1.7
            top += v_size * 1.5 if any_labels and not stacked else v_size * 0.6
            lo, hi, ticks = self.value_axis(val_ax, lo, hi, bottom - top)
            if not val_ax["hidden"]:
                left += max(text_width(format_number(t, fmt), v_size) for t in ticks) + v_size * 0.6
        span = (hi - lo) or 1.0

        def pos(v):                                  # value -> px along the value axis
            f = (v - lo) / span
            return left + f * (right - left) if horizontal else bottom - f * (bottom - top)

        for t in ticks:                              # grid lines and value labels
            p = pos(t)
            if val_ax["grid"]:
                gw, gc = val_ax["grid"]
                if horizontal:
                    self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (n(p), n(top), n(p), n(bottom), gc, n(gw)))
                else:
                    self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (n(left), n(p), n(right), n(p), gc, n(gw)))
            if not val_ax["hidden"]:
                if horizontal:
                    self.text(p, bottom + v_size * 0.95, format_number(t, fmt), v_size, v_fill)
                else:
                    self.text(left - v_size * 0.45, p, format_number(t, fmt), v_size, v_fill, "end")

        band = ((bottom - top) if horizontal else (right - left)) / max(1, count)

        def center(i):                               # middle of category i along the category axis
            if horizontal:
                return bottom - band * (i + 0.5)     # the first category sits at the bottom, as in PowerPoint
            if self.kind == "area" and val_ax["between"] == "midCat" and count > 1:
                return left + (right - left) * i / (count - 1)
            return left + band * (i + 0.5)

        if not cat_ax["hidden"]:
            for i, c in enumerate(cats):
                if horizontal:
                    self.text(left - c_size * 0.45, center(i), c, c_size, c_fill, "end")
                else:
                    self.text(center(i), bottom + c_size * 0.95, c, c_size, c_fill)
        base = pos(max(lo, min(hi, 0.0)))
        if cat_ax["line"]:
            if horizontal:
                self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>' % (n(base), n(top), n(base), n(bottom), cat_ax["line"]))
            else:
                self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>' % (n(left), n(base), n(right), n(base), cat_ax["line"]))

        labels = []                                  # drawn last, above every mark
        if self.kind == "bar":
            gap = int(self.val(self.el, "gapWidth", "150")) / 100.0
            slots = 1 if stacked else len(self.series)
            bw = band / (slots + gap)
            for i in range(count):
                acc_pos, acc_neg = 0.0, 0.0
                for k, s in enumerate(self.series):
                    v = value(s, i)
                    shown = v / totals[i] if percent else v
                    if stacked:
                        start = acc_pos if shown >= 0 else acc_neg
                        end = start + shown
                        if shown >= 0:
                            acc_pos = end
                        else:
                            acc_neg = end
                        offset = -bw / 2
                    else:
                        start, end = 0.0, shown
                        offset = -bw * slots / 2 + bw * (k if not horizontal else slots - 1 - k)
                    a, b = pos(max(lo, min(hi, start))), pos(max(lo, min(hi, end)))
                    fill = s["points"].get(i) or s["fill"]
                    c = center(i) + offset
                    if horizontal:
                        self.out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (n(min(a, b)), n(c), n(abs(b - a)), n(bw), fill))
                        mid, tip = (c + bw / 2), b
                    else:
                        self.out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (n(c), n(min(a, b)), n(bw), n(abs(b - a)), fill))
                        mid, tip = (c + bw / 2), b
                    if s["show"] and i < len(s["vals"]) and s["vals"][i] is not None:
                        size, clr, bold = s["label"]
                        label = format_number(v, s["fmt"])
                        inside = stacked or s["pos"] in ("ctr", "inEnd", "inBase")
                        if horizontal:
                            labels.append(((a + b) / 2 if inside else tip + size * 0.3, mid, label, size, clr, "middle" if inside else "start", bold))
                        else:
                            labels.append((mid, (a + b) / 2 if inside else tip - size * 0.65, label, size, clr, "middle", bold))
        else:
            for s in self.series:
                pts = [(center(i), pos(max(lo, min(hi, v)))) for i, v in enumerate(s["vals"]) if v is not None]
                if not pts:
                    continue
                path = " ".join("%s,%s" % (n(x), n(y)) for x, y in pts)
                if self.kind == "area":
                    self.out.append('<polygon points="%s,%s %s %s,%s" fill="%s"/>' % (n(pts[0][0]), n(base), path, n(pts[-1][0]), n(base), s["fill"]))
                else:
                    width, clr = (s["line"][0], s["line"][1]) if s["line"] else (2.0, s["fill"])
                    self.out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % (path, clr, n(width)))
                    if s["marker"]:
                        for x, y in pts:
                            self.out.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (n(x), n(y), n(s["marker"]), clr))
                if s["show"]:
                    size, clr, bold = s["label"]
                    for (x, y), v in zip(pts, [v for v in s["vals"] if v is not None]):
                        labels.append((x, y - size * 0.85, format_number(v, s["fmt"]), size, clr, "middle", bold))
        for x, y, label, size, clr, anchor, bold in labels:
            self.text(x, y, label, size, clr, anchor, bold)

    def scatter(self, box):
        left, top, right, bottom = box
        x_ax, y_ax = self.axis("valAx", ("b",)), self.axis("valAx", ("l",))
        xs = [v for s in self.series for v in s["x"] if v is not None]
        ys = [v for s in self.series for v in s["y"] if v is not None]
        if not xs or not ys:
            raise Unsupported("분산형 데이터 없음")
        x_size, x_fill, _ = x_ax["text"]
        y_size, y_fill, _ = y_ax["text"]
        if not x_ax["hidden"]:
            bottom -= x_size * 1.7
        top += y_size * 0.6
        y_lo, y_hi, y_ticks = self.value_axis(y_ax, min(0.0, min(ys)), max(ys), bottom - top)
        if not y_ax["hidden"]:
            left += max(text_width(format_number(t, y_ax["fmt"]), y_size) for t in y_ticks) + y_size * 0.6
        x_lo, x_hi, x_ticks = self.value_axis(x_ax, min(0.0, min(xs)), max(xs), right - left)
        right -= text_width(format_number(x_ticks[-1], x_ax["fmt"]), x_size) / 2
        fx = lambda v: left + (v - x_lo) / ((x_hi - x_lo) or 1.0) * (right - left)       # noqa: E731
        fy = lambda v: bottom - (v - y_lo) / ((y_hi - y_lo) or 1.0) * (bottom - top)     # noqa: E731
        for t in y_ticks:
            if y_ax["grid"]:
                self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (n(left), n(fy(t)), n(right), n(fy(t)), y_ax["grid"][1], n(y_ax["grid"][0])))
            if not y_ax["hidden"]:
                self.text(left - y_size * 0.45, fy(t), format_number(t, y_ax["fmt"]), y_size, y_fill, "end")
        for t in x_ticks:
            if x_ax["grid"]:
                self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (n(fx(t)), n(top), n(fx(t)), n(bottom), x_ax["grid"][1], n(x_ax["grid"][0])))
            if not x_ax["hidden"]:
                self.text(fx(t), bottom + x_size * 0.95, format_number(t, x_ax["fmt"]), x_size, x_fill)
        if x_ax["line"]:
            self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>' % (n(left), n(bottom), n(right), n(bottom), x_ax["line"]))
        for s in self.series:
            pts = [(fx(a), fy(b)) for a, b in zip(s["x"], s["y"]) if a is not None and b is not None]
            clr = s["line"][1] if s["line"] else s["fill"]
            if s["line"] and len(pts) > 1:
                self.out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
                                % (" ".join("%s,%s" % (n(x), n(y)) for x, y in pts), clr, n(s["line"][0])))
            for x, y in pts:
                self.out.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (n(x), n(y), n(s["marker"] or 3.5), clr))
            if s["show"]:
                size, fill, bold = s["label"]
                for (x, y), v in zip(pts, [b for a, b in zip(s["x"], s["y"]) if a is not None and b is not None]):
                    self.text(x, y - size * 0.85, format_number(v, s["fmt"]), size, fill, "middle", bold)

    def pie(self, box):
        left, top, right, bottom = box
        s = self.series[0]
        vals = [max(0.0, v or 0.0) for v in s["vals"]]
        total = sum(vals)
        if total <= 0:
            raise Unsupported("원형 차트 값 없음")
        cx, cy = (left + right) / 2, (top + bottom) / 2
        r = max(4.0, min(right - left, bottom - top) / 2 - 2)
        hole = r * int(self.val(self.el, "holeSize", "50")) / 100.0 if self.kind == "doughnut" else 0.0
        angle = math.radians(float(self.val(self.el, "firstSliceAng", "0")))
        edge = ' stroke="%s" stroke-width="%s"' % (s["line"][1], n(s["line"][0])) if s["line"] else ""
        at = lambda a, rad: (cx + rad * math.sin(a), cy - rad * math.cos(a))             # noqa: E731  0 = up, clockwise
        labels = []
        for i, v in enumerate(vals):
            if v <= 0:
                continue
            sweep = v / total * 2 * math.pi
            a0, a1 = angle, angle + sweep
            angle = a1
            fill = s["points"].get(i) or s["fill"]
            big = 1 if sweep > math.pi else 0
            if sweep >= 2 * math.pi - 1e-9:                                              # one slice: two half circles
                d = "M%s %s A%s %s 0 1 1 %s %s A%s %s 0 1 1 %s %s Z" % (n(cx), n(cy - r), n(r), n(r), n(cx), n(cy + r), n(r), n(r), n(cx), n(cy - r))
                if hole:
                    d += " M%s %s A%s %s 0 1 0 %s %s A%s %s 0 1 0 %s %s Z" % (n(cx), n(cy - hole), n(hole), n(hole), n(cx), n(cy + hole), n(hole), n(hole), n(cx), n(cy - hole))
            else:
                (x0, y0), (x1, y1) = at(a0, r), at(a1, r)
                if hole:
                    (x2, y2), (x3, y3) = at(a1, hole), at(a0, hole)
                    d = "M%s %s A%s %s 0 %d 1 %s %s L%s %s A%s %s 0 %d 0 %s %s Z" % (n(x0), n(y0), n(r), n(r), big, n(x1), n(y1), n(x2), n(y2), n(hole), n(hole), big, n(x3), n(y3))
                else:
                    d = "M%s %s L%s %s A%s %s 0 %d 1 %s %s Z" % (n(cx), n(cy), n(x0), n(y0), n(r), n(r), big, n(x1), n(y1))
            self.out.append('<path d="%s" fill="%s" fill-rule="evenodd"%s/>' % (d, fill, edge))
            if s["show"] or s["percent"]:
                size, clr, bold = s["label"]
                label = format_number(v / total, s["fmt"] or "0%") if s["percent"] else format_number(v, s["fmt"])
                lx, ly = at((a0 + a1) / 2, (r + hole) / 2 if hole else r * 0.62)
                labels.append((lx, ly, label, size, clr, bold))
        for lx, ly, label, size, clr, bold in labels:
            self.text(lx, ly, label, size, clr, "middle", bold)

    def radar(self, box):
        left, top, right, bottom = box
        cats = max((s["cats"] for s in self.series), key=len)
        count = max(len(cats), max(len(s["vals"]) for s in self.series))
        if count < 3:
            raise Unsupported("방사형 차트는 항목이 3개 이상이어야 함")
        cats = cats + [""] * (count - len(cats))
        cat_ax, val_ax = self.axis("catAx", ("b", "l", "t", "r")), self.axis("valAx", ("l", "b", "t", "r"))
        c_size, c_fill, _ = cat_ax["text"]
        every = [v for s in self.series for v in s["vals"] if v is not None]
        cx, cy = (left + right) / 2, (top + bottom) / 2
        r = max(4.0, min((right - left) / 2 - max(text_width(c, c_size) for c in cats) - c_size * 0.5, (bottom - top) / 2 - c_size * 1.5))
        lo, hi, ticks = self.value_axis(val_ax, 0.0, max(every or [1.0]), r * 1.6)
        at = lambda i, v: (cx + r * (v - lo) / ((hi - lo) or 1.0) * math.sin(2 * math.pi * i / count),      # noqa: E731
                           cy - r * (v - lo) / ((hi - lo) or 1.0) * math.cos(2 * math.pi * i / count))
        grid = val_ax["grid"] or (0.75, "#888888")
        for t in ticks[1:]:
            self.out.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="%s"/>'
                            % (" ".join("%s,%s" % (n(x), n(y)) for x, y in (at(i, t) for i in range(count))), grid[1], n(grid[0])))
        for i, c in enumerate(cats):
            x, y = at(i, hi)
            self.out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (n(cx), n(cy), n(x), n(y), grid[1], n(grid[0])))
            dx, dy = x - cx, y - cy
            anchor = "middle" if abs(dx) < r * 0.2 else ("start" if dx > 0 else "end")
            self.text(x + (c_size * 0.4 if dx > r * 0.2 else (-c_size * 0.4 if dx < -r * 0.2 else 0)),
                      y + (c_size * 0.8 if dy > r * 0.5 else (-c_size * 0.8 if dy < -r * 0.5 else 0)), c, c_size, c_fill, anchor)
        filled = self.val(self.el, "radarStyle", "standard") == "filled"
        for s in self.series:
            pts = [at(i, max(lo, min(hi, v if v is not None else lo))) for i, v in enumerate(s["vals"])]
            width, clr = (s["line"][0], s["line"][1]) if s["line"] else (2.0, s["fill"])
            self.out.append('<polygon points="%s" fill="%s" fill-opacity="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
                            % (" ".join("%s,%s" % (n(x), n(y)) for x, y in pts), s["fill"] if filled else "none", "0.35" if filled else "0", clr, n(width)))
            if s["marker"]:
                for x, y in pts:
                    self.out.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (n(x), n(y), n(s["marker"]), clr))


# --------------------------------------------------------------------------------------- template chrome

def run(cmd: list[str], timeout: int) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError("%s failed: %s" % (cmd[0], proc.stdout.decode("utf-8", "replace").strip()[-400:]))


def render_chrome(deck_path: Path, width: int, work: Path):
    """PNG bytes of every slide's chrome: the deck with the slide content removed, drawn by LibreOffice.

    Page-number placeholders stay, so the number is part of the picture.
    """
    prs = Presentation(str(deck_path))
    for slide in prs.slides:
        tree = slide.shapes._spTree
        for child in list(tree):
            if local(child) in ("nvGrpSpPr", "grpSpPr"):
                continue
            ph = child.find(".//%s/%s" % (q("p", "nvPr"), q("p", "ph")))
            if ph is not None and ph.get("type") == "sldNum":
                continue
            tree.remove(child)
    bare = work / "chrome.pptx"
    prs.save(str(bare))
    profile = (work / "lo-profile").as_uri()      # a profile of its own: a running LibreOffice does not block this one
    run(["soffice", "-env:UserInstallation=" + profile, "--headless", "--convert-to", "pdf", "--outdir", str(work), str(bare)], 300)
    pdf = work / "chrome.pdf"
    if not pdf.is_file():
        raise RuntimeError("soffice wrote no PDF")
    height = round(width * 9 / 16)
    run(["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", str(height), str(pdf), str(work / "c")], 300)
    pages = sorted(work.glob("c-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    return [p.read_bytes() for p in pages]


def chrome_layers(deck: Deck, pages: list[bytes], width: int):
    """For every slide the chrome HTML: one shared picture per layout, plus a small patch where a slide differs.

    Slides on one layout differ only in the page number. The first slide of a layout gives the shared
    picture; the others add the differing rectangle on top, so a 40-slide deck carries five pictures.
    """
    from PIL import Image, ImageChops
    k = STAGE_W / float(width)
    base: dict[str, tuple[str, object]] = {}
    out = []
    for slide, png in zip(deck.prs.slides, pages):
        name = slide.slide_layout.name or ""
        im = Image.open(io.BytesIO(png)).convert("RGB")
        if name not in base:
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            base[name] = (deck.image_class("image/png", buf.getvalue()), im)
            out.append('<div class="chrome %s"></div>' % base[name][0])
            continue
        klass, ref = base[name]
        bbox = ImageChops.difference(im, ref).getbbox() if im.size == ref.size else (0, 0) + im.size
        html_ = '<div class="chrome %s"></div>' % klass
        if bbox:
            x0, y0, x1, y1 = max(0, bbox[0] - 3), max(0, bbox[1] - 3), min(im.size[0], bbox[2] + 3), min(im.size[1], bbox[3] + 3)
            if (x1 - x0) * (y1 - y0) > im.size[0] * im.size[1] * 0.25:      # not a page number: keep the whole picture
                buf = io.BytesIO()
                im.save(buf, "PNG", optimize=True)
                html_ = '<div class="chrome %s"></div>' % deck.image_class("image/png", buf.getvalue())
            else:
                buf = io.BytesIO()
                im.crop((x0, y0, x1, y1)).save(buf, "PNG", optimize=True)
                html_ += '<div class="patch" style="left:%spx;top:%spx;width:%spx;height:%spx;background-image:url(%s)"></div>' % (
                    n(x0 * k), n(y0 * k), n((x1 - x0) * k), n((y1 - y0) * k), data_uri("image/png", buf.getvalue()))
        out.append(html_)
    return out


# --------------------------------------------------------------------------------------- page

EXTERNAL = re.compile(r"""(?i)(?:\bsrc\s*=\s*["']?|url\(\s*["']?|@import\s+["']?)\s*(?:https?:)?//""")


def build(deck: Deck, chrome: list[str]) -> str:
    args = deck.args
    slides, titles = [], []
    for i, slide in enumerate(deck.prs.slides, 1):
        html_, title = deck.slide_html(slide, i, chrome[i - 1])
        slides.append(html_)
        titles.append(title)
    all_text = "".join("".join(v) for v in deck.chars.values())
    lang = args.lang or ("ko" if re.search(r"[가-힣]", all_text) else "en")
    title = args.title or (titles[0] if titles else "") or deck.path.stem

    faces, sizes = [], []
    for face, chars in sorted(deck.chars.items()):
        path = FONT_FILES.get(face)
        if not path or not path.is_file():
            if face:
                deck.warn("글꼴 '%s'은(는) 스킬에 없어 넣지 못했습니다. 보는 장비의 글꼴로 표시됩니다" % face)
            continue
        blob, fmt, sub = subset_font(path, chars)
        faces.append(font_face(face, blob, fmt))
        sizes.append("%s %d KB%s" % (face, round(len(blob) / 1024.0), "" if sub else " (전체)"))
    if faces and not deck.have_fonttools:
        deck.warn("fontTools가 없어 글꼴 파일을 통째로 넣었습니다. 파일이 커집니다(my-plugins:setup)")

    css = (RUNTIME_DIR / "deck.css").read_text(encoding="utf-8")
    js = (RUNTIME_DIR / "deck.js").read_text(encoding="utf-8")
    rules = "".join(".%s{%s}" % (name, style) for style, name in deck.classes.items())
    deck_id = hashlib.sha1(deck.path.read_bytes()).hexdigest()[:10]
    page = "\n".join([
        "<!doctype html>",
        '<html lang="%s">' % lang,
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="generator" content="aws-ppt-skills deck_to_html">',
        "<title>%s</title>" % esc(title),
        '<style id="deck-fonts">%s</style>' % "".join(faces),
        '<style id="deck-runtime">\n%s</style>' % css,
        '<style id="deck-images">%s</style>' % "".join(deck.image_css),
        '<style id="deck-styles">%s</style>' % rules,
        "</head>",
        "<body>",
        '<div id="deck" data-id="%s" data-count="%d">' % (deck_id, len(slides)),
        "\n".join(slides),
        "</div>",
        '<script id="deck-script">\n%s</script>' % js,
        "</body>",
        "</html>",
        "",
    ])
    deck.font_sizes = sizes
    return page


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", help="the final .pptx (after apply_template.py)")
    ap.add_argument("--out", help="default: the deck's name with .html")
    ap.add_argument("--title", help="page title (default: the largest text of the first slide)")
    ap.add_argument("--lang", choices=["ko", "en"], help="language of the controls (default: ko when the slides have Korean text)")
    ap.add_argument("--no-notes", action="store_true", help="leave the speaker notes out of the page")
    ap.add_argument("--chrome-width", type=int, default=1920, help="pixel width of the template chrome pictures")
    args = ap.parse_args()

    path = Path(args.deck)
    if not path.is_file():
        print("ERROR %s: 파일이 없습니다" % path, file=sys.stderr)
        return 1
    try:
        deck = Deck(path, args)
    except Exception as e:
        print("ERROR %s: PowerPoint 파일로 열 수 없습니다 (%s)" % (path, e), file=sys.stderr)
        return 1
    if len(deck.prs.slides) == 0:
        print("ERROR %s: 슬라이드가 없습니다" % path, file=sys.stderr)
        return 1
    raw = sorted({s.slide_layout.name for s in deck.prs.slides if (s.slide_layout.name or "").upper().startswith("AWS_")})
    if raw:
        print("ERROR %s: 템플릿을 적용하기 전 파일입니다(%s). apply_template.py가 만든 최종 .pptx를 넘기세요" % (path, ", ".join(raw)), file=sys.stderr)
        return 1
    if not 640 <= args.chrome_width <= 7680:
        print("ERROR --chrome-width는 640에서 7680 사이여야 합니다", file=sys.stderr)
        return 1
    missing = [t for t in ("soffice", "pdftoppm") if not shutil.which(t)]
    try:
        import PIL  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    if missing:
        print("ERROR 템플릿 배경을 그리는 데 필요한 도구가 없습니다: %s. my-plugins:setup skill로 설치하세요" % ", ".join(missing), file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="deck-html-") as tmp:
        try:
            pages = render_chrome(path, args.chrome_width, Path(tmp))
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
            print("ERROR 템플릿 배경을 그리지 못했습니다: %s" % e, file=sys.stderr)
            return 1
    if len(pages) != len(deck.prs.slides):
        print("ERROR 템플릿 배경 %d장, 슬라이드 %d장으로 수가 다릅니다" % (len(pages), len(deck.prs.slides)), file=sys.stderr)
        return 1
    page = build(deck, chrome_layers(deck, pages, args.chrome_width))

    count = page.count('<section class="slide"')
    if count != len(deck.prs.slides):
        print("ERROR HTML의 슬라이드 %d장이 덱의 %d장과 다릅니다" % (count, len(deck.prs.slides)), file=sys.stderr)
        return 1
    if EXTERNAL.search(page):
        deck.warn("페이지가 외부 주소의 파일을 불러옵니다. 오프라인에서는 그 부분이 비어 보입니다")
    out = Path(args.out) if args.out else path.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    st = deck.stats
    notes = "노트 없음(--no-notes)" if args.no_notes else "노트 %d장" % st["notes"]
    print("OK %s: 슬라이드 %d장, %s, 차트 %d, 표 %d, 그림 %d(SVG %d), %.1f MB" % (
        out, count, notes, st["charts"], st["tables"], st["pictures"], st["svg"], len(page.encode("utf-8")) / 1048576.0))
    if deck.font_sizes:
        print("글꼴: " + ", ".join(deck.font_sizes))
    if not args.no_notes and st["notes"] < count:
        deck.warn("노트가 없는 슬라이드가 %d장 있습니다" % (count - st["notes"]))
    for w in deck.warnings:
        print("WARN " + w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

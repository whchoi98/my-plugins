# -*- coding: utf-8 -*-
"""Minimal SVG builder following aws-diagram-design style-guide (AWS skin).

Tokens: paper #FFFFFF, ink #232F3E, muted #545B64, soft #7D8998,
rule rgba(35,47,62,0.12), accent #EC7211, accent-tint rgba(255,153,0,0.10), link #0972D3.
Type ramp for the blog profile (1280x720): node-name 20px/600, sublabel/eyebrow/arrow/legend 16px.
"""
import base64, glob, os, re, sys


ASSETS_POINTER = ".aws-diagram-assets"   # 작업 폴더 사본 옆에 두는 assets 경로 파일


def _version_key(path):
    """플러그인 캐시 경로 .../<plugin>/<version>/skills/... 에서 버전을 숫자 튜플로 바꾼다(1.10 > 1.9)."""
    parts = path.split(os.sep)
    try:
        ver = parts[parts.index("skills") - 1]
    except ValueError:
        return (0,)
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.+-]", ver))


def find_assets():
    """aws-diagram-design skill의 assets 폴더(aws-icons, fonts)를 찾는다.

    순서: AWS_DIAGRAM_ASSETS 환경 변수 → 이 파일 옆의 ASSETS_POINTER 파일(작업 폴더로 복사할 때 기록)
    → my-plugins 안의 옆 skill(../../aws-diagram-design/assets) → Claude Code 플러그인 캐시(my-plugins, 예전
    aws-diagrams 단독 플러그인. 버전 높은 순) → claude.ai 동기화 사본(사용자 홈과 /root, `~g2` 같은 접미사 포함,
    최근 수정 순) → claude.ai 컨테이너 경로.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")
    candidates = []
    env = os.environ.get("AWS_DIAGRAM_ASSETS")
    if env:
        candidates.append(env)
    pointer = os.path.join(here, ASSETS_POINTER)
    if os.path.isfile(pointer):
        with open(pointer, encoding="utf-8") as f:
            candidates.append(f.read().strip())
    candidates.append(os.path.normpath(os.path.join(here, "..", "..", "aws-diagram-design", "assets")))
    for plugin in ("my-plugins", "aws-diagrams"):
        cached = glob.glob(os.path.join(
            home, ".claude/plugins/cache/*", plugin, "*/skills/aws-diagram-design/assets"))
        candidates += sorted(cached, key=_version_key, reverse=True)
    synced = set()
    for h in {home, "/root"}:
        synced.update(glob.glob(os.path.join(
            h, ".claude/plugins/synced/*/*/skills/aws-diagram-design/assets")))
    candidates += sorted(synced, key=os.path.getmtime, reverse=True)
    candidates += [
        "/mnt/skills/plugin-files/my-plugins/skills/aws-diagram-design/assets",
        "/mnt/skills/plugin-files/aws-diagrams/skills/aws-diagram-design/assets",
    ]
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "aws-icons")):
            return c
    raise FileNotFoundError("aws-diagram-design skill의 assets 폴더를 찾지 못했습니다. my-plugins 플러그인을 "
                            "설치하거나 AWS_DIAGRAM_ASSETS에 skills/aws-diagram-design/assets 경로를 지정하십시오.")


ASSETS = find_assets()
ICON_ROOT = os.path.join(ASSETS, "aws-icons")
SANS = "'Amazon Ember', 'Noto Sans CJK KR', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Amazon Ember Mono', 'Noto Sans CJK KR', ui-monospace, monospace"

PAPER = "#FFFFFF"; INK = "#232F3E"; MUTED = "#545B64"; SOFT = "#7D8998"
RULE = "rgba(35,47,62,0.12)"; RULE_SOLID = "#D5DBDB"
ACCENT = "#EC7211"; ACCENT_TINT = "rgba(255,153,0,0.10)"; LINK = "#0972D3"
SERIES_TEAL = "#01A88D"; SERIES_PURPLE = "#8C4FFF"

ICONS = {
    "vpc": "service/Networking-Content-Delivery/Arch_Amazon-Virtual-Private-Cloud_48.svg",
    "dx": "service/Networking-Content-Delivery/Arch_AWS-Direct-Connect_48.svg",
    "dxgw": "resource/Networking-Content-Delivery/Res_AWS-Direct-Connect_Gateway_48.svg",
    "router": "resource/General-Icons/Res_Servers_48_Light.svg",
    "cgw": "resource/Networking-Content-Delivery/Res_Amazon-VPC_Customer-Gateway_48.svg",
    "vgw": "resource/Networking-Content-Delivery/Res_Amazon-VPC_VPN-Gateway_48.svg",
    "dc": "group/Corporate-data-center_32.svg",
}


def g4(*vals):
    for v in vals:
        assert v % 4 == 0, f"not on 4px grid: {v}"
    return vals


def icon_data_uri(key):
    p = os.path.join(ICON_ROOT, ICONS[key])
    with open(p, "rb") as f:
        b = f.read()
    return "data:image/svg+xml;base64," + base64.b64encode(b).decode()


class Canvas:
    def __init__(self, slug, title, desc, w=1280, h=720):
        self.slug, self.title, self.desc, self.w, self.h = slug, title, desc, w, h
        self.layers = {"zones": [], "arrows": [], "labels": [], "nodes": [], "top": []}
        self.node_boxes = []   # (x,y,w,h,name)
        self.label_boxes = []  # (x,y,w,h,text)
        self.accent_count = 0

    # ---------- primitives ----------
    def text(self, layer, x, y, s, size=16, weight=400, fill=INK, anchor="start", mono=False, italic=False, ls=None):
        g4(x, y)
        fam = MONO if mono else SANS
        extra = f' letter-spacing="{ls}"' if ls else ""
        sty = ' font-style="italic"' if italic else ""
        self.layers[layer].append(
            f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'font-family="{fam}" text-anchor="{anchor}"{extra}{sty}>{esc(s)}</text>')

    def zone(self, x, y, w, h, title=None, stroke=INK, stroke_op=0.30, fill=INK, fill_op=0.03,
             dashed=False, title_color=None, eyebrow=None, rx=8):
        g4(x, y, w, h)
        dash = ' stroke-dasharray="6,4"' if dashed else ""
        self.layers["zones"].append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" fill-opacity="{fill_op}" '
            f'stroke="{stroke}" stroke-opacity="{stroke_op}" stroke-width="1.2"{dash}/>')
        if title:
            self.text("zones", x + 16, y + 32, title, size=20, weight=600, fill=title_color or INK)
        if eyebrow:
            self.text("zones", x + 16, y + 56, eyebrow, size=16, fill=SOFT)

    def node(self, x, y, w, h, name, sub=None, icon=None, kind="backend", sub_fill=MUTED, name_size=20,
             sub2=None, sub2_fill=None):
        g4(x, y, w, h)
        for (bx, by, bw, bh, bn) in self.node_boxes:
            assert not overlap((x, y, w, h), (bx, by, bw, bh)), f"node overlap: {name} vs {bn}"
        self.node_boxes.append((x, y, w, h, name))
        fills = {
            "backend": (PAPER, INK, 1, 1),
            "store": (INK, MUTED, 0.05, 1),
            "external": (INK, INK, 0.03, 0.30),
            "input": (MUTED, SOFT, 0.10, 1),
            "optional": (INK, INK, 0.02, 0.20),
            "focal": ("#FF9900", ACCENT, 0.10, 1),
            "standby": (INK, MUTED, 0.05, 1),
        }
        f, s, fo, so = fills[kind]
        if kind == "focal":
            self.accent_count += 1
        dash = ' stroke-dasharray="4,3"' if kind in ("optional", "standby") else ""
        L = self.layers["nodes"]
        L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>')
        L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{f}" fill-opacity="{fo}" '
                 f'stroke="{s}" stroke-opacity="{so}" stroke-width="1"{dash}/>')
        tx = x + 16
        if icon:
            isz = 40
            L.append(f'<image href="{icon_data_uri(icon)}" x="{x+16}" y="{y + (h-isz)//2 // 4 * 4}" '
                     f'width="{isz}" height="{isz}"/>')
            tx = x + 16 + isz + 12
        lines = [(name, name_size, 600, INK, False)]
        if sub:
            lines.append((sub, 16, 400, sub_fill, True))
        if sub2:
            lines.append((sub2, 16, 400, sub2_fill or sub_fill, True))
        # vertical centering on 4px grid
        total = sum(l[1] for l in lines) + 8 * (len(lines) - 1)
        cy = y + h // 2
        base = cy - total // 2
        yy = base
        for (s_, size, wt, col, mono) in lines:
            yy += size
            yb = (yy // 4) * 4
            self.text("nodes", tx // 4 * 4, yb, s_, size=size, weight=wt, fill=col, mono=mono)
            yy += 8

    def arrow(self, pts, label=None, color=MUTED, dashed=False, marker=True, label_seg=0, side="above",
              label_fill=None, label_shift=0, width=1.2, plate_w=None):
        """Orthogonal polyline with r=8 rounded elbows. pts: list of (x,y) on 4px grid."""
        for p in pts:
            g4(*p)
        d = rounded_path(pts, r=8)
        mk = {MUTED: "arrow", ACCENT: "arrow-accent", LINK: "arrow-link", INK: "arrow-ink",
              SERIES_TEAL: "arrow-teal", SERIES_PURPLE: "arrow-purple"}.get(color, "arrow")
        m = f' marker-end="url(#{mk})"' if marker else ""
        dash = ' stroke-dasharray="6,4"' if dashed else ""
        self.layers["arrows"].append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{m}/>')
        if label:
            (x1, y1), (x2, y2) = pts[label_seg], pts[label_seg + 1]
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
            self.arrow_label(mx, my, label, horizontal=(y1 == y2), side=side,
                             fill=label_fill or (ACCENT if "$" in label else SOFT), shift=label_shift,
                             plate_w=plate_w)

    def arrow_label(self, mx, my, label, horizontal=True, side="above", fill=SOFT, shift=0, plate_w=None):
        lines = label if isinstance(label, list) else [label]
        pw = plate_w or max(text_w(l) for l in lines) + 16
        pw = ((pw + 7) // 8) * 8
        ph = 24 * len(lines)
        if horizontal:
            px = (mx - pw // 2 + shift) // 4 * 4
            py = (my - 8 - ph) if side == "above" else (my + 8)
        else:
            py = (my - ph // 2 + shift) // 4 * 4
            px = (mx - 8 - pw) if side == "left" else (mx + 8)
        px, py = (px // 4) * 4, (py // 4) * 4
        for (bx, by, bw, bh, bn) in self.node_boxes:
            assert not overlap((px, py, pw, ph), (bx, by, bw, bh)), f"label mask '{lines[0]}' overlaps node {bn}"
        self.label_boxes.append((px, py, pw, ph, lines[0]))
        self.layers["labels"].append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="2" fill="{PAPER}"/>')
        for i, l in enumerate(lines):
            self.text("labels", px + pw // 2, py + 20 + 24 * i, l, size=16, fill=fill, anchor="middle", mono=True)

    def legend(self, items, y=648):
        """items: list of (kind, label). kind in solid|dashed|accent|teal|purple|ink|fill-standby|fill-focal|price"""
        g4(y)
        self.layers["top"].append(f'<line x1="40" y1="{y-16}" x2="{self.w-40}" y2="{y-16}" stroke="{RULE}" stroke-width="0.8"/>')
        self.text("top", 40, y + 12, "범례", size=16, weight=600, fill=MUTED)
        x = 120
        for kind, label in items:
            yy = y + 2
            if kind in ("solid", "dashed", "accent", "teal", "purple", "ink"):
                col = {"solid": MUTED, "dashed": MUTED, "accent": ACCENT, "teal": SERIES_TEAL,
                       "purple": SERIES_PURPLE, "ink": INK}[kind]
                dash = ' stroke-dasharray="6,4"' if kind == "dashed" else ""
                self.layers["top"].append(f'<line x1="{x}" y1="{yy}" x2="{x+40}" y2="{yy}" stroke="{col}" stroke-width="2"{dash}/>')
            elif kind == "fill-standby":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{INK}" fill-opacity="0.05" stroke="{MUTED}" stroke-dasharray="4,3"/>')
            elif kind == "fill-backend":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{PAPER}" stroke="{INK}"/>')
            elif kind == "fill-teal":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{SERIES_TEAL}" fill-opacity="0.18" stroke="{SERIES_TEAL}"/>')
            elif kind == "fill-purple":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{SERIES_PURPLE}" fill-opacity="0.18" stroke="{SERIES_PURPLE}"/>')
            elif kind == "fill-ink":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{INK}" fill-opacity="0.15" stroke="{INK}"/>')
            elif kind == "group":
                self.layers["top"].append(f'<rect x="{x}" y="{yy-12}" width="40" height="24" rx="4" fill="{ACCENT}" fill-opacity="0.05" stroke="{ACCENT}" stroke-opacity="0.6" stroke-dasharray="4,4"/>')
            elif kind == "price":
                self.text("top", x, yy + 6, "$", size=20, weight=600, fill=ACCENT)
            elif kind == "dot-accent":
                self.layers["top"].append(f'<circle cx="{x+20}" cy="{yy}" r="7" fill="{ACCENT}"/>')
            elif kind == "dot-ink":
                self.layers["top"].append(f'<circle cx="{x+20}" cy="{yy}" r="7" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
            self.text("top", x + 52, yy + 6, label, size=16, fill=MUTED)
            x += 52 + ((text_w(label) + 40 + 3) // 4) * 4

    # ---------- output ----------
    def svg(self):
        defs = f'''<defs>
<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{ACCENT}"/></marker>
<marker id="arrow-link" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{LINK}"/></marker>
<marker id="arrow-ink" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{INK}"/></marker>
<marker id="arrow-teal" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{SERIES_TEAL}"/></marker>
<marker id="arrow-purple" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0 0, 10 4, 0 8" fill="{SERIES_PURPLE}"/></marker>
</defs>'''
        body = "\n".join(self.layers["zones"] + self.layers["arrows"] + self.layers["labels"] + self.layers["nodes"] + self.layers["top"])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
                f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc">\n'
                f'<title id="{self.slug}-title">{esc(self.title)}</title>\n<desc id="{self.slug}-desc">{esc(self.desc)}</desc>\n'
                f'{defs}\n<rect width="100%" height="100%" fill="{PAPER}"/>\n{body}\n</svg>')

    def check(self):
        assert self.accent_count <= 2, f"accent budget exceeded: {self.accent_count}"
        for i, a in enumerate(self.node_boxes):
            for b in self.node_boxes[i + 1:]:
                assert not overlap(a[:4], b[:4]), f"node overlap {a[4]} / {b[4]}"
        for l in self.label_boxes:
            for n in self.node_boxes:
                assert not overlap(l[:4], n[:4]), f"label {l[4]} overlaps node {n[4]}"
        # everything inside viewBox
        for (x, y, w, h, n) in self.node_boxes + self.label_boxes:
            assert 0 <= x and x + w <= self.w and 0 <= y and y + h <= self.h, f"out of canvas: {n}"
        return True

    def write(self, path_html, path_svg):
        svg = self.svg()
        with open(path_svg, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
        html = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{esc(self.title)}</title>
<style>
@font-face{{font-family:'Amazon Ember';font-weight:400;src:local('Amazon Ember'),local('AmazonEmber-Regular');}}
@font-face{{font-family:'Amazon Ember';font-weight:600;src:local('Amazon Ember Medium'),local('Amazon Ember SemiBold'),local('Amazon Ember Bold');}}
@font-face{{font-family:'Amazon Ember';font-weight:700;src:local('Amazon Ember Bold');}}
@font-face{{font-family:'Amazon Ember Mono';font-weight:400;src:local('Amazon Ember Mono'),local('AmazonEmberMono-Regular');}}
html,body{{margin:0;background:#fff;}} svg{{display:block;width:{self.w}px;height:{self.h}px;}}
</style></head><body>{svg}</body></html>'''
        with open(path_html, "w", encoding="utf-8") as f:
            f.write(html)


# ---------- helpers ----------
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def overlap(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def text_w(s, size=16):
    """Rough width estimate: CJK 1.0em, ASCII 0.6em, digits/punct 0.55em."""
    w = 0.0
    for ch in s:
        if re.match(r"[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF\u4E00-\u9FFF\u3000-\u303F\uFF00-\uFFEF]", ch):
            w += 1.0
        elif ch.isupper():
            w += 0.68
        elif ch in " ":
            w += 0.3
        else:
            w += 0.58
    return int(w * size)


def rounded_path(pts, r=8):
    """Build an SVG path through orthogonal points with quarter-arc corners."""
    if len(pts) == 2:
        return f"M{pts[0][0]} {pts[0][1]} L{pts[1][0]} {pts[1][1]}"
    d = f"M{pts[0][0]} {pts[0][1]}"
    for i in range(1, len(pts) - 1):
        (px, py), (cx, cy), (nx, ny) = pts[i - 1], pts[i], pts[i + 1]
        # direction in / out
        dx1, dy1 = sign(cx - px), sign(cy - py)
        dx2, dy2 = sign(nx - cx), sign(ny - cy)
        ax, ay = cx - dx1 * r, cy - dy1 * r
        bx, by = cx + dx2 * r, cy + dy2 * r
        d += f" L{ax} {ay} Q{cx} {cy} {bx} {by}"
    d += f" L{pts[-1][0]} {pts[-1][1]}"
    return d


def sign(v):
    return (v > 0) - (v < 0)


if __name__ == "__main__" and "--assets" in sys.argv:
    print(ASSETS)

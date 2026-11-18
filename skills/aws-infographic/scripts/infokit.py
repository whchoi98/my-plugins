"""infokit: SVG infographic builder (AWS palette, dark/light, NanumSquareOTF metrics, official AWS icons).

Copy this file and buildkit.py into the work folder and import it from the page modules.
  python3 infokit.py --icons   print the path of the aws-diagram icon bundle (kept in .aws-icon-bundle next to the copy)
  python3 infokit.py --fonts   print the font files the text metrics use

Icon bundle: AWS_ICON_BUNDLE, then the .aws-icon-bundle file next to this file, then the aws-diagram skill next to
this skill, then installed plugin copies. Fonts: INFOKIT_FONTS (any folder layout), then fontconfig, then the user
font folders. Without NanumSquare the widths come from Noto Sans CJK, without any font from a per-character estimate.
"""
import base64
import glob
import json
import os
import re
import subprocess
import sys

# ----------------------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
ICON_POINTER = ".aws-icon-bundle"   # written next to a copy of this file: the copy cannot see the sibling skill
ICON_REL = os.path.join("skills", "aws-diagram", "assets", "icons.json")
NO_BUNDLE = ("aws-diagram skill의 assets/icons.json을 찾지 못했습니다. my-plugins 플러그인을 설치하거나 "
             "AWS_ICON_BUNDLE에 skills/aws-diagram/assets/icons.json 경로를 지정하십시오.")


def _version_key(path):
    """Plugin cache path .../<plugin>/<version>/skills/... as a numeric tuple (1.10 > 1.9)."""
    parts = path.split(os.sep)
    try:
        ver = parts[parts.index("skills") - 1]
    except ValueError:
        return (0,)
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.+-]", ver))


def find_icon_bundle():
    """Path of the aws-diagram skill's assets/icons.json, or None."""
    home = os.path.expanduser("~")
    candidates = [os.environ.get("AWS_ICON_BUNDLE")]
    pointer = os.path.join(HERE, ICON_POINTER)
    if os.path.isfile(pointer):
        with open(pointer, encoding="utf-8") as f:
            candidates.append(f.read().strip())
    candidates.append(os.path.normpath(os.path.join(HERE, "..", "..", "aws-diagram", "assets", "icons.json")))
    for plugin in ("my-plugins", "aws-diagrams"):
        cached = glob.glob(os.path.join(home, ".claude/plugins/cache/*", plugin, "*", ICON_REL))
        candidates += sorted(cached, key=_version_key, reverse=True)
    synced = set()
    for h in {home, "/root"}:
        synced.update(glob.glob(os.path.join(h, ".claude/plugins/synced/*/*", ICON_REL)))
        synced.update(glob.glob(os.path.join(h, ".claude/skills/**/aws-diagram/assets/icons.json"), recursive=True))
    candidates += sorted(synced, key=os.path.getmtime, reverse=True)
    candidates += [os.path.join("/mnt/skills/plugin-files", plugin, ICON_REL) for plugin in ("my-plugins", "aws-diagrams")]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


_ICONS = find_icon_bundle()
BUNDLE = json.load(open(_ICONS, encoding="utf-8"))["sets"] if _ICONS else {}

FONT_DIR = os.environ.get("INFOKIT_FONTS", "")
_NANUM = {300: "L", 400: "R", 700: "B", 800: "EB"}   # drawn weight -> NanumSquare file suffix
_FONT_FILES = None


def _font_files():
    """{file name: path} of the installed fonts: INFOKIT_FONTS first, then fontconfig, then the user font folders."""
    global _FONT_FILES
    if _FONT_FILES is None:
        paths = []
        if FONT_DIR:
            paths += sorted(glob.glob(os.path.join(FONT_DIR, "**", "*.*"), recursive=True))
        try:
            out = subprocess.run(["fc-list", ":", "file"], capture_output=True, text=True).stdout
            paths += sorted(ln.strip().rstrip(":").strip() for ln in out.splitlines() if ln.strip())
        except OSError:
            pass
        home = os.path.expanduser("~")
        for d in (os.path.join(home, ".local/share/fonts"), os.path.join(home, "Library/Fonts"), "/Library/Fonts"):
            paths += sorted(glob.glob(os.path.join(d, "**", "*.*"), recursive=True))
        _FONT_FILES = {}
        for path in paths:
            if path.lower().endswith((".otf", ".ttf", ".ttc")):
                _FONT_FILES.setdefault(os.path.basename(path), path)
    return _FONT_FILES


def font_file(weight):
    """NanumSquare file for a drawn weight (300, 400, 700, 800), or None when it is not installed."""
    files, s = _font_files(), _NANUM[weight]
    for name in (f"NanumSquare{s}.otf", f"NanumSquareOTF{s}.otf", f"NanumSquareOTF_ac{s}.otf", f"NanumSquare{s}.ttf"):
        if name in files:
            return files[name]
    return None


def code_font(bold=False):
    """(file, face index) of D2Coding, or None. A .ttc holds regular and bold as faces 0 and 1; .ttf files hold one."""
    files = _font_files()
    names = [n for n in files if n.lower().startswith("d2coding")]   # lookup order: INFOKIT_FONTS first
    ttc = [n for n in names if n.lower().endswith(".ttc")]
    ttf = [n for n in names if not n.lower().endswith(".ttc")]
    if bold:
        hit = [n for n in ttf if "bold" in n.lower()]
        if hit:
            return files[hit[0]], 0
        if ttc:
            return files[ttc[0]], 1
    plain = [n for n in ttf if "bold" not in n.lower()]
    if plain:
        return files[plain[0]], 0
    return (files[ttc[0]], 0) if ttc else None

FONT_STACK = ("NanumSquareOTF, '나눔스퀘어OTF', NanumSquare, '나눔스퀘어', 'Apple SD Gothic Neo', "
              "'Malgun Gothic', 'Noto Sans KR', 'Noto Sans CJK KR', Arial, sans-serif")
CODE_FAMILY = "D2Coding, 'D2Coding ligature', Menlo, Consolas, monospace"

# Body is NanumSquareOTF Bold: logical 400 -> Bold(700), 700 -> ExtraBold(800).
WEIGHT_MAP = {300: 300, 400: 700, 500: 700, 600: 700, 700: 800, 800: 800}


def fw(w):
    return WEIGHT_MAP.get(int(w), int(w))


# ----------------------------------------------------------------------------- themes
# Every accent has an "F" (fill) twin. Text on saturated fills: badgetext (blue/purple), onwarm (orange/yellow/green).
THEMES = {
    "dark": dict(bg="#161D26", card="#1C2430", panel="#232D3A", cardline="#2E3947", line2="#3B4757",
                 text="#F3F3F7", text2="#E2E4EC", muted="#A6ABBE", faint="#7B8198", arrow="#A6ABBE",
                 badge="#E2E4EC", badgetext="#161D26", onwarm="#161D26", chipline="#5A667A",
                 blue="#41B3FF", blueF="#41B3FF", yellow="#FBD332", yellowF="#FBD332",
                 orange="#FF9900", orangeF="#FF9900", purple="#AD5CFF", purpleF="#AD5CFF",
                 pink="#FF5C85", pinkF="#FF5C85", green="#8CC63F", greenF="#8CC63F", icon="#E2E4EC"),
    "light": dict(bg="#FFFFFF", card="#F5F7F9", panel="#FFFFFF", cardline="#DFE4EA", line2="#CDD4DD",
                  text="#232F3E", text2="#2E3A4A", muted="#5F6B7A", faint="#8A94A2", arrow="#232F3E",
                  badge="#232F3E", badgetext="#FFFFFF", onwarm="#232F3E", chipline="#9AA5B3",
                  blue="#0972D3", blueF="#2E8CF0", yellow="#A87900", yellowF="#F5C518",
                  orange="#E8710A", orangeF="#FF9900", purple="#7D3FE0", purpleF="#8C4FFF",
                  pink="#D4245F", pinkF="#FF5C85", green="#4F8A10", greenF="#5FA82A", icon=None),
}


def icon_source(ref, theme="light"):
    """(mime type, bytes) of a bundle icon such as 'service/Amazon-Bedrock'. Dark themes lighten squid-ink glyphs."""
    setname, _, name = ref.partition("/")
    try:
        e = BUNDLE[setname][name]
    except KeyError:
        raise KeyError(f"아이콘 {ref!r}이 번들에 없습니다. aws-diagram skill의 scripts/find_icon.py로 이름을 확인하십시오"
                       if BUNDLE else NO_BUNDLE) from None
    if e["type"] == "svg":
        data = e["data"]
        tint = THEMES[theme].get("icon")
        if tint:
            data = re.sub(r"#2[34]2F3[DE]", tint, data)
        return "image/svg+xml", data.encode()
    return "image/png", base64.b64decode(e["data"])


# ----------------------------------------------------------------------------- text metrics
_FC = {}
_FALLBACK = {}


def _fallback_path(weight):
    """Noto Sans CJK file through fontconfig, or "" when there is none."""
    bold = weight >= 700
    if bold not in _FALLBACK:
        q = f"Noto Sans CJK KR:weight={'bold' if bold else 'regular'}"
        try:
            _FALLBACK[bold] = subprocess.run(["fc-match", "-f", "%{file}", q], capture_output=True, text=True).stdout.strip()
        except OSError:
            _FALLBACK[bold] = ""
    return _FALLBACK[bold]


def _font(weight, size):
    """Pillow font for a logical weight; None when the machine has neither NanumSquare nor a fontconfig fallback."""
    w = min(_NANUM, key=lambda k: abs(k - fw(weight)))
    key = (w, int(round(size)))
    if key not in _FC:
        from PIL import ImageFont   # Pillow is needed only where text is measured
        path = font_file(w) or _fallback_path(w)
        if not path and "warned" not in _FC:
            _FC["warned"] = True
            print("infokit: 나눔스퀘어OTF와 대체 폰트를 찾지 못해 글자 수로 폭을 추정합니다 (my-plugins:setup으로 폰트 설치)",
                  file=sys.stderr)
        _FC[key] = ImageFont.truetype(path, max(1, key[1])) if path else None
    return _FC[key]


def tw(s, size, weight=400):
    f = _font(weight, size)
    if f is None:   # no font file: Hangul and CJK one em, everything else 0.56 em
        return sum(size if ord(ch) > 0x2E7F else size * 0.56 for ch in s)
    return f.getlength(s) * (size / max(1, int(round(size))))


def cw(s, size, bold=False):
    """Width in D2Coding (code text only)."""
    hit = code_font(bold)
    if not hit:
        return tw(s, size) * 1.05
    key = ("d2", int(round(size)), bold)
    if key not in _FC:
        from PIL import ImageFont
        _FC[key] = ImageFont.truetype(hit[0], key[1], index=hit[1])
    return _FC[key].getlength(s)


# rich text: _{sub} ^{sup} **bold** [colorkey]{text}
_RICH = re.compile(r"(_\{[^}]*\}|\^\{[^}]*\}|\*\*[^*]+\*\*|\[[a-zA-Z0-9]+\]\{[^}]*\})")


def parse_rich(s):
    segs = []
    for part in _RICH.split(s):
        if not part:
            continue
        if part.startswith("_{"):
            segs.append((part[2:-1], "sub", None, None))
        elif part.startswith("^{"):
            segs.append((part[2:-1], "sup", None, None))
        elif part.startswith("**"):
            segs.append((part[2:-2], None, 700, None))
        elif part.startswith("["):
            m = re.match(r"\[([a-zA-Z0-9]+)\]\{(.*)\}$", part)
            segs.append((m.group(2), None, None, m.group(1)))
        else:
            segs.append((part, None, None, None))
    return segs


def rw(s, size, weight=400, ls=0.0):
    """Rendered width of (rich) text in px."""
    total, n = 0.0, 0
    for txt, kind, sw, _ in parse_rich(s):
        total += tw(txt, size * 0.7 if kind else size, sw or weight)
        n += len(txt)
    return total + ls * n


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def F(n, k):
    """Scale a size by the layout factor k (portrait pages use k = 1.1 ~ 1.25)."""
    return round(n * k)


# ----------------------------------------------------------------------------- document
class Doc:
    def __init__(self, W, H, theme):
        self.W, self.H, self.theme, self.t = W, H, theme, THEMES[theme]
        self.out, self.defs, self._markers = [], [], set()

    def c(self, key):
        return self.t.get(key, key) if key else key

    def add(self, s):
        self.out.append(s)

    def rect(self, x, y, w, h, rx=0, fill="none", stroke=None, sw=1.0, dash=None, fo=None, so=None, opacity=None):
        a = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
        if rx:
            a += f' rx="{rx:.1f}"'
        a += f' fill="{self.c(fill)}"'
        if fo is not None:
            a += f' fill-opacity="{fo:.3f}"'
        if stroke:
            a += f' stroke="{self.c(stroke)}" stroke-width="{sw}"'
            if so is not None:
                a += f' stroke-opacity="{so:.3f}"'
            if dash:
                a += f' stroke-dasharray="{dash}"'
        if opacity is not None:
            a += f' opacity="{opacity:.3f}"'
        self.add(a + "/>")

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1.0, fo=None):
        a = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{self.c(fill)}"'
        if fo is not None:
            a += f' fill-opacity="{fo:.3f}"'
        if stroke:
            a += f' stroke="{self.c(stroke)}" stroke-width="{sw}"'
        self.add(a + "/>")

    def line(self, x1, y1, x2, y2, stroke="arrow", sw=1.5, dash=None, so=None):
        a = (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{self.c(stroke)}" '
             f'stroke-width="{sw}" stroke-linecap="round"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if so is not None:
            a += f' stroke-opacity="{so}"'
        self.add(a + "/>")

    def path(self, d, stroke="arrow", sw=1.5, fill="none", dash=None, marker=None, fo=None, so=None):
        a = f'<path d="{d}" fill="{self.c(fill)}"'
        if fo is not None:
            a += f' fill-opacity="{fo}"'
        if stroke:
            a += f' stroke="{self.c(stroke)}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
            if so is not None:
                a += f' stroke-opacity="{so}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if marker:
            a += f' marker-end="url(#{marker})"'
        self.add(a + "/>")

    def marker(self, key):
        mid = f"ah-{key}"
        if mid not in self._markers:
            self.defs.append(f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="11" '
                             f'markerHeight="11" markerUnits="userSpaceOnUse" orient="auto">'
                             f'<path d="M0,0.6 L10,5 L0,9.4 z" fill="{self.c(key)}"/></marker>')
            self._markers.add(mid)
        return mid

    def arrow(self, pts, color="arrow", sw=1.8, dash=None, r=10, head=True):
        self.path(poly_d(pts, r), stroke=color, sw=sw, dash=dash, marker=self.marker(color) if head else None)

    def text(self, x, y, s, size=16, weight=400, color="text", anchor="start", ls=None, opacity=None, box=None,
             family=None):
        """Rich text. Pass box=(x, y, w, h) of the enclosing card so QA can detect overflow."""
        parts, shift = [], 0.0
        for txt, kind, sw, sc in parse_rich(s):
            target = size * 0.30 if kind == "sub" else (-size * 0.42 if kind == "sup" else 0.0)
            attrs = ""
            if abs(target - shift) > 1e-6:
                attrs += f' dy="{target - shift:.2f}"'
                shift = target
            if kind:
                attrs += f' font-size="{size * 0.7:.1f}"'
            if sw:
                attrs += f' font-weight="{fw(sw)}"'
            if sc:
                attrs += f' fill="{self.c(sc)}"'
            parts.append(f"<tspan{attrs}>{esc(txt)}</tspan>" if attrs else esc(txt))
        a = f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{fw(weight)}" fill="{self.c(color)}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if ls:
            a += f' letter-spacing="{ls}"'
        if opacity is not None:
            a += f' opacity="{opacity}"'
        if family:
            a += f' font-family="{family}"'
        if box:
            a += f' data-box="{box[0]:.0f},{box[1]:.0f},{box[2]:.0f},{box[3]:.0f}"'
        self.add(a + ">" + "".join(parts) + "</text>")

    def runs(self, x, y, runs, anchor="start", box=None):
        """One line of differently styled runs: (text, size, weight, color[, dx[, letter_spacing]])."""
        parts = []
        for r in runs:
            txt, size, weight, color = r[:4]
            a = f' font-size="{size}" font-weight="{fw(weight)}" fill="{self.c(color)}"'
            if len(r) > 4 and r[4]:
                a += f' dx="{r[4]}"'
            if len(r) > 5 and r[5]:
                a += f' letter-spacing="{r[5]}"'
            parts.append(f"<tspan{a}>{esc(txt)}</tspan>")
        a = f'<text x="{x:.1f}" y="{y:.1f}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if box:
            a += f' data-box="{box[0]:.0f},{box[1]:.0f},{box[2]:.0f},{box[3]:.0f}"'
        self.add(a + ">" + "".join(parts) + "</text>")

    def icon(self, ref, x, y, size):
        """Official AWS icon from the aws-diagram bundle, e.g. 'service/Amazon-Bedrock' (find_icon.py)."""
        mime, raw = icon_source(ref, self.theme)
        uri = f"data:{mime};base64," + base64.b64encode(raw).decode()
        self.add(f'<image href="{uri}" xlink:href="{uri}" x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" '
                 f'height="{size:.1f}"/>')

    def svg(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'viewBox="0 0 {self.W} {self.H}" width="{self.W}" height="{self.H}" font-family="{FONT_STACK}">')
        return head + "\n<defs>" + "".join(self.defs) + "</defs>\n" + "\n".join(self.out) + "\n</svg>\n"


def poly_d(pts, r=10):
    if len(pts) == 2 or r <= 0:
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1, l2 = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        rr = min(r, l1 / 2, l2 / 2)
        ax, ay = x1 - (x1 - x0) / l1 * rr, y1 - (y1 - y0) / l1 * rr
        bx, by = x1 + (x2 - x1) / l2 * rr, y1 + (y2 - y1) / l2 * rr
        d += f" L{ax:.1f},{ay:.1f} Q{x1:.1f},{y1:.1f} {bx:.1f},{by:.1f}"
    return d + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"


# ----------------------------------------------------------------------------- text layout
def wrap(s, size, weight, maxw):
    words, lines, cur = s.split(" "), [], ""
    for wd in words:
        cand = wd if not cur else cur + " " + wd
        if rw(cand, size, weight) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = wd
    return lines + ([cur] if cur else [])


def wrap_balanced(s, size, weight, maxw):
    """Greedy wrap; two-line results are rebalanced (prefer breaking after ',', never after ':' or '(')."""
    lines = wrap(s, size, weight, maxw)
    if len(lines) != 2:
        return lines
    words, best = s.split(" "), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa, wb = rw(a, size, weight), rw(b, size, weight)
        score = max(wa, wb) - (24 if a.endswith(",") else 0) + (60 if a.endswith((":", "(")) else 0)
        if wa <= maxw and wb <= maxw and (best is None or score < best[0]):
            best = (score, [a, b])
    return best[1] if best else lines


def nlines(text, size, w, weight=400):
    return len(wrap_balanced(text, size, weight, w)) if rw(text, size, weight) > w else 1


def para(d, x, y, w, text, size=16, lh=None, weight=400, color="text2", box=None, anchor="start", maxl=4):
    """Wrapped paragraph starting at baseline y. Returns the baseline of the last line."""
    lh = lh or round(size * 1.45)
    lines = (wrap_balanced(text, size, weight, w) if rw(text, size, weight) > w else [text])[:maxl]
    for i, ln in enumerate(lines):
        d.text(x, y + i * lh, ln, size, weight, color, anchor, box=box)
    return y + (len(lines) - 1) * lh


def cell(d, x, mid, w, text, size, lh, weight, color, box, k=1.0):
    """Table cell text vertically centered on mid (handles 1-2 wrapped lines)."""
    lines = wrap_balanced(text, size, weight, w) if rw(text, size, weight) > w else [text]
    y0 = mid + 5 * k - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        d.text(x, y0 + i * lh, ln, size, weight, color, box=box)


def dot_list(d, x, y, w, items, size=15, lh=None, gap=None, color="text2", dot="muted", box=None):
    """Bulleted list from baseline y. Returns the baseline of the last line."""
    lh = lh or round(size * 1.42)
    gap = gap if gap is not None else round(size * 0.55)
    yy = last = y
    for it in items:
        d.circle(x + 4, yy - size * 0.33, 2.8, fill=dot)
        last = para(d, x + 16, yy, w - 16, it, size, lh, 400, color, box=box)
        yy = last + lh + gap
    return last


def items_h(items, w, size, lh, gap):
    """Height of a dot_list block (for vertical centering)."""
    return sum(nlines(it, size, w - 16) for it in items) * lh + (len(items) - 1) * gap


# ----------------------------------------------------------------------------- components
def card(d, x, y, w, h, stroke="cardline", sw=1.2, fill="card", rx=14, dashed=False):
    d.rect(x, y, w, h, rx=rx, fill=fill, stroke=stroke, sw=sw, dash="8 6" if dashed else None)


def badge(d, cx, cy, num, r=15, size=16):
    d.circle(cx, cy, r, fill="badge")
    d.text(cx, cy + size * 0.35, str(num), size, 700, "badgetext", "middle")


def tag(d, x, y, text, color="green", size=13, h=24, pad=10, fill_op=0.14, box=None):
    """Rounded label chip. Returns its width."""
    w = rw(text, size, 700) + 2 * pad
    d.rect(x, y, w, h, rx=h / 2, fill=color + "F", fo=fill_op, stroke=color, sw=1.1)
    d.text(x + w / 2, y + h / 2 + size * 0.36, text, size, 700, color, "middle", box=box)
    return w


def pill(d, x, y, w, h, text, color="blue", size=15, weight=700, fo=0.14, txt="text", sw=1.3, dash=None):
    d.rect(x, y, w, h, rx=min(h / 2, 12), fill=color + "F", fo=fo, stroke=color, sw=sw, dash=dash)
    d.text(x + w / 2, y + h / 2 + size * 0.36, text, size, weight, txt, "middle")


def callout(d, x, y, w, title, body, k=1.0, color="orange", box=None):
    """Key-insight box (max one per section). Returns bottom y."""
    h = 58 * k
    d.rect(x, y, w, h, rx=10, fill=color + "F", fo=0.08, stroke=color, sw=1.2)
    d.text(x + 16, y + 25 * k, title, F(15, k), 700, "text", box=box)
    para(d, x + 16, y + 46 * k, w - 32, body, F(13, k), None, 400, "text2", box=box)
    return y + h


def check(d, x, y, s, color="green", sw=2.4):
    d.path(f"M{x:.1f},{y + s * 0.55:.1f} L{x + s * 0.38:.1f},{y + s * 0.9:.1f} L{x + s:.1f},{y + s * 0.12:.1f}",
           stroke=color, sw=sw)


def cross(d, x, y, s, color="pink", sw=2.4):
    d.path(f"M{x:.1f},{y:.1f} L{x + s:.1f},{y + s:.1f} M{x + s:.1f},{y:.1f} L{x:.1f},{y + s:.1f}", stroke=color, sw=sw)


def header(d, x, y, title, sub_en, sub_ko, tsize=42, ssize=21, kosize=18):
    d.text(x, y, title, tsize, 700, "text", ls=0.2)
    d.runs(x, y + round(tsize * 0.92), [(sub_en, ssize, 700, "orange"), (sub_ko, kosize, 400, "muted", 16)])


def series_nav(d, x, y, parts, current, size=13, anchor="end"):
    """Chips for a multi-part series. parts = [("0", "개요"), ("1", "..."), ...]."""
    items = [f"{n} {t}" for n, t in parts]
    widths = [rw(t, size, 700) + 24 for t in items]
    lab = rw("SERIES", 11, 700, 1.2)
    total = sum(widths) + 8 * (len(items) - 1) + lab + 12
    cx = x - total if anchor == "end" else x
    d.text(cx, y + 17, "SERIES", 11, 700, "faint", ls=1.2)
    cx += lab + 12
    for (n, _), t, wdt in zip(parts, items, widths):
        on = n == current
        d.rect(cx, y, wdt, 26, rx=13, fill="orangeF" if on else "card", fo=0.9 if on else None,
               stroke="orange" if on else "line2", sw=1.1)
        d.text(cx + wdt / 2, y + 17.5, t, size, 700, "badgetext" if on else "muted", "middle")
        cx += wdt + 8


def section(d, x, y, w, h, num, title, take=None, tsize=21, ksize=15, inline=True):
    """Numbered card with a title and a one-line takeaway. Returns the y where content starts."""
    box = (x, y, w, h)
    card(d, x, y, w, h)
    badge(d, x + 34, y + 33, num, r=15, size=16)
    if take and inline:
        d.runs(x + 58, y + 40, [(title, tsize, 700, "text", 0, 0.2), (take, ksize, 400, "muted", 14)], box=box)
        return y + 66
    d.text(x + 58, y + 40, title, tsize, 700, "text", ls=0.2, box=box)
    if take:
        d.text(x + 58, y + 66, take, ksize, 400, "muted", box=box)
        return y + 88
    return y + 66


def footer_note(d, x, y, text, size=13, anchor="end"):
    d.text(x, y, text, size, 400, "faint", anchor)


# ----------------------------------------------------------------------------- command line
def _cli(argv):
    if argv == ["--icons"]:
        if not _ICONS:
            print(NO_BUNDLE, file=sys.stderr)
            return 1
        print(_ICONS)
        return 0
    if argv == ["--fonts"]:
        for w in sorted(_NANUM):
            print(w, font_file(w) or f"(없음, 대체: {_fallback_path(w) or '글자 수로 추정'})")
        for label, bold in (("code", False), ("code-bold", True)):
            hit = code_font(bold)
            print(label, hit[0] if hit else "(없음, 본문 폰트 폭으로 추정)")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))

"""buildkit: render page modules to SVG + PNG (1x, 2x), run layout QA and text lint, make contact sheets.

usage: python buildkit.py <out_dir> [--sizes 16x9,4x5] <module>[:<slug>] ...
  uv run --no-project --with playwright==1.64.1 --with pillow python buildkit.py build part0:00-overview
Run it in the work folder, next to infokit.py and the page modules. Default output is 16x9 landscape in dark and
light. Each module exposes landscape(theme) (and portrait(theme) when 4x5 is requested) returning SVG strings.
Playwright is imported only by build(); lint() and contact_sheet() work without it.
"""
import html
import importlib
import json
import re
import sys
from pathlib import Path


SIZES = {"16x9": (1920, 1080, "landscape"), "4x5": (1536, 1920, "portrait")}
DEFAULT_SIZES = ("16x9",)  # 4x5 only on request
THEME_NAMES = ("dark", "light")

QA_JS = r"""
() => {
  const out = [];
  const texts = Array.from(document.querySelectorAll('text')).filter(t => !t.closest('g[transform]'));
  const items = texts.map(t => ({t, b: t.getBBox(), txt: t.textContent}));
  const vb = document.documentElement.viewBox.baseVal;
  for (const {t, b, txt} of items) {
    if (b.x < 0 || b.y < 0 || b.x + b.width > vb.width || b.y + b.height > vb.height) out.push({type: 'canvas', txt});
    const db = t.getAttribute('data-box');
    if (db) {
      const [x, y, w, h] = db.split(',').map(Number);
      const over = [];
      if (b.x < x + 6) over.push('L' + (x + 6 - b.x).toFixed(1));
      if (b.x + b.width > x + w - 6) over.push('R' + (b.x + b.width - (x + w - 6)).toFixed(1));
      if (b.y < y + 1) over.push('T' + (y + 1 - b.y).toFixed(1));
      if (b.y + b.height > y + h - 1) over.push('B' + (b.y + b.height - (y + h - 1)).toFixed(1));
      if (over.length) out.push({type: 'overflow', txt, over: over.join(' ')});
    }
  }
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const a = items[i].b, c = items[j].b;
    const ix = Math.min(a.x + a.width, c.x + c.width) - Math.max(a.x, c.x);
    const iy = Math.min(a.y + a.height, c.y + c.height) - Math.max(a.y, c.y);
    if (ix > 1 && iy > 4) out.push({type: 'overlap', a: items[i].txt, b: items[j].txt, ix: +ix.toFixed(1), iy: +iy.toFixed(1)});
  }
  return out;
}
"""

BANNED = "·—–"
POLITE = re.compile(r"(입니다|합니다|됩니다|습니다)")
PLAIN_END = re.compile(r"다[.!?]?$")
QUESTION = re.compile(r"(\?|[는은인린한된할을]가|[가-힣]나)$")  # titles must be condensed noun phrases


def lint(svg):
    """Slide-text rules: no middle dot or long dashes, noun-phrase endings, no question-style titles."""
    s = re.sub(r'href="data:[^"]+"', "", svg)
    issues = []
    for t in re.findall(r"<text[^>]*>(.*?)</text>", s, flags=re.S):
        t = html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
        if any(ch in t for ch in BANNED):
            issues.append(("banned-char", t))
        if POLITE.search(t) or PLAIN_END.search(t):
            issues.append(("ending", t))
        if QUESTION.search(t):
            issues.append(("question", t))
    if "bundle:" in svg:
        issues.append(("unresolved-icon", ""))
    return issues


def render(page, svg_path, png_path, w, h):
    page.set_viewport_size({"width": w, "height": h})
    page.goto(Path(svg_path).resolve().as_uri())
    page.wait_for_timeout(150)
    page.screenshot(path=str(png_path), full_page=False)  # full_page on SVG can time out
    return page.evaluate(QA_JS)


def build(out_dir, specs, sizes=DEFAULT_SIZES):
    from playwright.sync_api import sync_playwright   # only rendering needs the browser

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for mod_name, slug in specs:
            mod = importlib.import_module(mod_name)
            for size in sizes:
                w, h, fn = SIZES[size]
                if not hasattr(mod, fn):
                    continue
                for theme in THEME_NAMES:
                    stem = f"{slug}_{size}_{theme}"
                    svg = getattr(mod, fn)(theme)
                    path = out / f"{stem}.svg"
                    path.write_text(svg, encoding="utf-8")
                    issues = [{"type": a, "txt": t} for a, t in lint(svg)]
                    for scale, suffix in ((1, "@1x"), (2, "")):
                        page = b.new_page(device_scale_factor=scale)
                        res = render(page, path, out / f"{stem}{suffix}.png", w, h)
                        page.close()
                        if scale == 1:
                            issues += res
                    report[stem] = issues
        b.close()
    bad = 0
    for k, v in report.items():
        print(f"== {k}: {len(v)} issue(s)")
        for it in v[:30]:
            print("   ", json.dumps(it, ensure_ascii=False))
        bad += len(v)
    return bad


def contact_sheet(out_dir, pattern, dest, cols=2, cell_w=960):
    """Tile PNGs of one format (e.g. '*_16x9_*@1x.png') into one image for a quick visual review."""
    from PIL import Image
    files = sorted(Path(out_dir).glob(pattern))
    if not files:
        return None
    ims = [Image.open(f).convert("RGB") for f in files]
    ch_ = max(round(cell_w * im.height / im.width) for im in ims)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, ch_ * rows), "white")
    for i, im in enumerate(ims):
        im = im.resize((cell_w, round(cell_w * im.height / im.width)), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * cell_w, (i // cols) * ch_))
    sheet.save(dest)
    return dest


if __name__ == "__main__":
    sys.path.insert(0, str(Path.cwd()))
    args = sys.argv[1:]
    sizes = DEFAULT_SIZES
    if "--sizes" in args:
        i = args.index("--sizes")
        sizes = tuple(args[i + 1].split(","))
        del args[i:i + 2]
    out_dir, *mods = args
    specs = [(m.split(":")[0], m.split(":")[1] if ":" in m else m) for m in mods]
    sys.exit(1 if build(out_dir, specs, sizes) else 0)

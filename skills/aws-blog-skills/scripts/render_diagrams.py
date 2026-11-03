# Usage: python3 render_diagrams.py <images-dir>   (renders every *.html in the dir to *.png at 2x)
# Without Playwright installed: uv run --no-project --with playwright==1.64.1 python render_diagrams.py <images-dir>
# Keep the pin in step with SKILL.md, references/diagrams.md and skills/setup/scripts/setup.sh (PW_SPEC).
import glob, os, pathlib, subprocess, sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is not installed. Run with:\n"
             "  uv run --no-project --with playwright==1.64.1 python render_diagrams.py <images-dir>\n"
             "or install it: pip install playwright && python -m playwright install chromium")

# The images dir must be the blog work folder, never this skill folder (a plugin cache that updates replace).
IMG = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BLOG_IMAGES")
if not IMG:
    sys.exit("usage: render_diagrams.py <images-dir>  (or set BLOG_IMAGES)")
files = sorted(glob.glob(os.path.join(IMG, "*.html")))
if not files:
    sys.exit(f"no *.html in {IMG}")

def launch(p):
    """Start Chromium. When this Playwright build's browser revision is missing (a different Playwright
    version was resolved than the one setup installed), install it into the same environment once and retry."""
    try:
        return p.chromium.launch()
    except Exception as exc:  # playwright raises its own Error type
        if "Executable doesn't exist" not in str(exc):
            raise
        print("chromium for this Playwright version is missing; running: playwright install chromium", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return p.chromium.launch()


with sync_playwright() as p:
    b = launch(p)
    pg = b.new_page(device_scale_factor=2, viewport={"width": 1400, "height": 800})
    for f in files:
        pg.goto("file://" + str(pathlib.Path(f).resolve()))
        pg.wait_for_function("document.fonts.ready.then(()=>true)")
        ok = pg.evaluate("document.fonts.check('600 20px \"Amazon Ember\"') && document.fonts.check('16px \"Noto Sans CJK KR\"')")
        # text overflow gate: every <text> must stay inside the svg viewBox with 8px margin
        over = pg.evaluate("""() => {
          const svg = document.querySelector('svg'); const vb = svg.viewBox.baseVal;
          const out = [];
          document.querySelectorAll('svg text').forEach(t => { const bb = t.getBBox();
            if (bb.x < 8 || bb.y < 0 || bb.x + bb.width > vb.width - 8 || bb.y + bb.height > vb.height) out.push(t.textContent + ' @' + Math.round(bb.x+bb.width)); });
          return out; }""")
        out = f[:-5] + ".png"
        pg.locator("svg").first.screenshot(path=out, omit_background=False)
        print(os.path.basename(out), "fonts:", ok, "overflow:", over)
    b.close()

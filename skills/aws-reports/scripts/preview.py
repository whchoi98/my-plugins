#!/usr/bin/env python3
"""Screenshot the finished report so you can look at it before handing it over.

usage: uv run --no-project --with playwright python preview.py report.docx report.html --out-dir preview/

- .docx: rendered in Chromium with docx-preview (npm, global install by my-plugins:setup). It draws Word styles, tables, shading, borders,
  numbering, header and footer faithfully, but it does NOT paginate by content height: a "page" image is the content
  between explicit page breaks, cut into A4-height slices. Use LibreOffice (soffice --convert-to pdf) for real
  pagination when it is available.
- .html: full page at 900 px wide, cut into 1400 px slices.
Prints the PNG paths. Open them with the Read tool and look at them.
"""
import argparse
import base64
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent


def npm_dir(pkg):
    """Package folder: a node_modules next to this script, NODE_PATH entries, then `npm root -g` (where my-plugins:setup installs)."""
    roots = [HERE / "node_modules"] + [Path(p) for p in os.environ.get("NODE_PATH", "").split(os.pathsep) if p]
    try:
        roots.append(Path(subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True).stdout.strip()))
    except (OSError, subprocess.CalledProcessError):
        pass
    for r in roots:
        if (r / pkg / "package.json").exists():
            return r / pkg
    sys.exit(f"npm package {pkg} not found; install the report dependencies with the my-plugins setup skill")
A4_PX = 1123  # 297 mm at 96 dpi


def slices(page, el_box, out_prefix, slice_h):
    paths = []
    y, i = el_box["y"], 1
    end = el_box["y"] + el_box["height"]
    while y < end - 2:
        h = min(slice_h, end - y)
        p = f"{out_prefix}-{i:02d}.png"
        page.screenshot(path=p, clip={"x": el_box["x"], "y": y, "width": el_box["width"], "height": h}, full_page=True)
        paths.append(p)
        y += h
        i += 1
    return paths


def docx_preview(pw, docx, out_dir):
    jszip = (npm_dir("jszip") / "dist/jszip.min.js").read_text()
    dp = (npm_dir("docx-preview") / "dist/docx-preview.min.js").read_text()
    data = base64.b64encode(Path(docx).read_bytes()).decode()
    html = f"""<!doctype html><meta charset=utf-8><style>body{{margin:0;background:#e5e7eb}} .docx-wrapper{{padding:20px!important}}</style>
<div id=c></div><script>{jszip}</script><script>{dp}</script><script>
const b = Uint8Array.from(atob("{data}"), c => c.charCodeAt(0));
docx.renderAsync(b, document.getElementById('c'), null, {{breakPages: true, renderHeaders: true, renderFooters: true,
  ignoreLastRenderedPageBreak: false, experimental: true, useBase64URL: true}}).then(() => window.done = true, e => window.err = String(e));
</script>"""
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=1.5)
    pg.set_content(html)
    pg.wait_for_function("window.done || window.err", timeout=60000)
    err = pg.evaluate("window.err || null")
    if err:
        raise SystemExit(f"docx-preview failed: {err}")
    pg.wait_for_timeout(500)
    paths = []
    for k, sec in enumerate(pg.locator("section.docx").all(), 1):
        box = sec.bounding_box()
        paths += slices(pg, box, str(Path(out_dir) / f"docx-p{k:02d}"), A4_PX)
    b.close()
    return paths


def html_preview(pw, html_file, out_dir, width=900):
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": width, "height": 1200}, device_scale_factor=1.5)
    pg.goto(Path(html_file).resolve().as_uri())
    pg.wait_for_timeout(500)
    fonts = pg.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight)")
    h = pg.evaluate("document.documentElement.scrollHeight")
    paths = slices(pg, {"x": 0, "y": 0, "width": width, "height": h}, str(Path(out_dir) / "html"), 1400)
    over = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    pg.set_viewport_size({"width": 390, "height": 900})
    mobile_over = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    b.close()
    print(f"html fonts loaded: {sorted(set(fonts))}; horizontal scroll at 900px={over}, at 390px={mobile_over}")
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out-dir", default="preview")
    a = ap.parse_args()
    Path(a.out_dir).mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        for f in a.files:
            if f.endswith(".docx"):
                ps = docx_preview(pw, f, a.out_dir)
            elif f.endswith((".html", ".htm")):
                ps = html_preview(pw, f, a.out_dir)
            else:
                raise SystemExit(f"unsupported file: {f}")
            print("\n".join(ps))


if __name__ == "__main__":
    main()

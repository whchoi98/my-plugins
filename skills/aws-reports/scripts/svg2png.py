#!/usr/bin/env python3
"""Render an SVG (e.g. an AWS architecture diagram) to PNG for the Word report, with NanumSquareOTF text.
Word cannot take SVG alone, so the report uses the PNG in both the .docx and the HTML.

usage: uv run --no-project --with playwright python svg2png.py diagram.svg [out.png] [--scale 2]
"""
import argparse
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("svg")
ap.add_argument("out", nargs="?")
ap.add_argument("--scale", type=float, default=2)
a = ap.parse_args()
src = Path(a.svg)
out = Path(a.out) if a.out else src.with_suffix(".png")
svg = src.read_text(encoding="utf-8")
m = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', svg)
w, h = (float(m.group(1)), float(m.group(2))) if m else (1280, 720)
html = ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#fff}"
        f"svg{{display:block;width:{w}px;height:{h}px}} svg text{{font-family:'NanumSquareOTF',sans-serif!important}}</style>" + svg)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": int(w), "height": int(h)}, device_scale_factor=a.scale)
    pg.set_content(html)
    pg.wait_for_timeout(300)
    ok = pg.evaluate("document.fonts.check('12px NanumSquareOTF')")
    pg.locator("svg").first.screenshot(path=str(out))
    b.close()
print(f"{out} (NanumSquareOTF available: {ok})")
# Word shows figures about 16 cm wide (605 px at 96 dpi). Text smaller than ~7 pt there is hard to read.
sizes = [float(x) for x in re.findall(r'font-size\s*[:=]\s*"?([\d.]+)', svg)]
if sizes:
    pt = min(sizes) * (605 / w) * 0.75
    need = 7 / 0.75 * w / 605
    print(f"smallest text: {min(sizes):g}px in a {w:g}px-wide SVG = {pt:.1f}pt at 16 cm in Word" + (f" -> WARN: use font-size >= {need:.0f}px or a narrower viewBox" if pt < 7 else ""))

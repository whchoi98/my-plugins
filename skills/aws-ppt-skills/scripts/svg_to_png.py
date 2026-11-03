#!/usr/bin/env python3
"""Render an SVG diagram to a transparent PNG preview for the deck.

The PNG is what addDiagram() places on the slide; apply_template.py then embeds the
original SVG next to it, so PowerPoint shows the vector version and other viewers
(LibreOffice, previews) fall back to this PNG.

Usage
  python3 svg_to_png.py in.svg out.png [--width 2400] [--background 000000]

--background paints the slide color behind the diagram (black theme 000000, white FFFFFF);
without it the PNG keeps transparency (apply_template.py flattens it onto the theme color).

Renderers are tried in order: Playwright Chromium (best text and font fidelity),
cairosvg, rsvg-convert, ImageMagick.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def svg_size(svg: str) -> tuple[float, float]:
    m = re.search(r'viewBox\s*=\s*"\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', svg)
    if m:
        return float(m.group(1)), float(m.group(2))
    w = re.search(r'<svg[^>]*\swidth\s*=\s*"([\d.]+)', svg)
    h = re.search(r'<svg[^>]*\sheight\s*=\s*"([\d.]+)', svg)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    return 1600.0, 900.0


def with_playwright(src: Path, out: Path, width: int, bg: str | None) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    svg = src.read_text(encoding="utf-8")
    vw, vh = svg_size(svg)
    scale = width / vw
    # Size the root <svg> explicitly so the screenshot box matches the viewBox.
    svg_root = re.sub(r"<svg\b", f'<svg width="{vw}" height="{vh}"', re.sub(r'(<svg\b[^>]*?)\s(width|height)="[^"]*"', r"\1", svg, count=2), count=1)
    page_bg = f"#{bg}" if bg else "transparent"
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>html,body{{margin:0;background:{page_bg}}} svg{{display:block;background:{page_bg}}}</style></head><body>{svg_root}</body></html>"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": int(round(vw)), "height": int(round(vh))}, device_scale_factor=scale)
            page.set_content(html, wait_until="load")
            page.wait_for_timeout(150)
            page.locator("svg").first.screenshot(path=str(out), omit_background=bg is None)
            browser.close()
        return out.exists()
    except Exception as exc:  # browser missing etc.
        print(f"playwright failed: {exc}", file=sys.stderr)
        return False


def with_cairosvg(src: Path, out: Path, width: int, bg: str | None) -> bool:
    try:
        import cairosvg
    except ImportError:
        return False
    cairosvg.svg2png(url=str(src), write_to=str(out), output_width=width, background_color=f"#{bg}" if bg else None)
    return out.exists()


def with_cli(src: Path, out: Path, width: int, bg: str | None) -> bool:
    if shutil.which("rsvg-convert"):
        cmd = ["rsvg-convert", "-w", str(width), "-o", str(out)] + (["-b", f"#{bg}"] if bg else []) + [str(src)]
        subprocess.run(cmd, check=False)
        if out.exists():
            return True
    if shutil.which("convert"):
        cmd = ["convert", "-background", f"#{bg}" if bg else "none", "-density", "300", str(src), "-resize", f"{width}x"]
        cmd += (["-flatten"] if bg else []) + [str(out)]
        subprocess.run(cmd, check=False, capture_output=True)
        return out.exists()
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("png")
    ap.add_argument("--width", type=int, default=2400, help="output pixel width (default 2400)")
    ap.add_argument("--background", help="hex slide color painted behind the diagram, e.g. 000000")
    args = ap.parse_args()
    bg = args.background.lstrip("#").upper() if args.background else None
    src, out = Path(args.svg), Path(args.png)
    if out.exists():
        out.unlink()
    for fn in (with_playwright, with_cairosvg, with_cli):
        if fn(src, out, args.width, bg):
            print(f"OK {out} via {fn.__name__[5:]}")
            return 0
    print("ERROR: no SVG renderer available (playwright, cairosvg, rsvg-convert, ImageMagick)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

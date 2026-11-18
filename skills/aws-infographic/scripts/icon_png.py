#!/usr/bin/env python3
"""Export AWS icons from the aws-diagram bundle as PNG files for an editable deck (aws-ppt-skills addIcon()).

Usage
  python -B icon_png.py <out_dir> [--theme dark|light] [--size 256] <set/name> [<set/name> ...]
  uv run --no-project --with playwright==1.64.1 --with pillow python -B icon_png.py deck/icons --theme dark service/Amazon-Bedrock

--theme dark   for the black deck template: squid-ink glyphs are lightened, as in the dark infographic
--theme light  for the white deck template (default)
--size         pixel size of the square PNG (default 256; a 0.4 in icon stays sharp when enlarged)

Prints one line per icon: <set/name> TAB <png path>. The file is <set>-<name>.png. Icons the bundle holds as SVG
are drawn with Playwright Chromium on a transparent background; icons it holds as PNG are written as they are.
Exit 2 when a name is not in the bundle (nothing is written), 1 when an SVG icon cannot be drawn.
"""
import sys

sys.dont_write_bytecode = True   # this folder is the plugin cache: no __pycache__ next to infokit.py

import argparse
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infokit  # noqa: E402


def draw_svgs(jobs, size):
    """jobs = [(svg bytes, out path)]; one browser for all of them."""
    from playwright.sync_api import sync_playwright   # only SVG icons need the browser
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": size, "height": size})
        for svg, out in jobs:
            uri = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
            page.set_content("<!doctype html><html><body style='margin:0;background:transparent'>"
                             f"<img src='{uri}' width='{size}' height='{size}' style='display:block'></body></html>",
                             wait_until="load")
            page.wait_for_timeout(50)
            page.screenshot(path=str(out), omit_background=True, full_page=False)
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    ap.add_argument("refs", nargs="+", metavar="set/name")
    ap.add_argument("--theme", choices=("dark", "light"), default="light")
    ap.add_argument("--size", type=int, default=256)
    args = ap.parse_args()

    sources, missing = [], []
    for ref in args.refs:
        try:
            sources.append((ref,) + infokit.icon_source(ref, args.theme))
        except KeyError:
            missing.append(ref)
    if missing:
        print("아이콘을 찾지 못했습니다: " + ", ".join(missing), file=sys.stderr)
        print("이름은 aws-diagram skill의 scripts/find_icon.py로 확인합니다" if infokit.BUNDLE else infokit.NO_BUNDLE,
              file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    done, svgs = [], []
    for ref, mime, raw in sources:
        out = out_dir / (ref.replace("/", "-") + ".png")
        if mime == "image/png":
            out.write_bytes(raw)
        else:
            svgs.append((raw, out))
        done.append((ref, out))
    if svgs:
        try:
            draw_svgs(svgs, args.size)
        except ImportError:
            print("SVG 아이콘을 PNG로 그리려면 Playwright가 필요합니다: "
                  "uv run --no-project --with playwright==1.64.1 --with pillow python -B icon_png.py ...", file=sys.stderr)
            return 1
    for ref, out in done:
        print(f"{ref}\t{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

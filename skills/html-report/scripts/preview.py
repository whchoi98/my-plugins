#!/usr/bin/env python3
"""Screenshot an html-report page in the four views a reader can get, so you can look at it before handing it over.

usage: uv run --no-project --with playwright python preview.py report/out/page.html --out-dir report/out/preview

Views: 1440 px light Korean, 1440 px dark English, 390 px light Korean, 390 px dark English. The theme and
the language are switched by clicking the page's own buttons, so the toggle script runs too. Each view is
cut into slices of at most 1600 px (8 slices at most). Prints the PNG paths; open them with the Read tool.
Prints a WARN line when the buttons do not switch the page, when the page itself scrolls sideways (only
figure and table boxes may) or when the page script throws. Exit code 1 when there is a WARN.
When Playwright's bundled Node.js cannot start (for example libatomic.so.1 is missing on some Linux
hosts), it retries once with the system `node` through PLAYWRIGHT_NODEJS_PATH.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWS = [("desktop-light-ko", 1440, "light", "ko"), ("desktop-dark-en", 1440, "dark", "en"),
         ("mobile-light-ko", 390, "light", "ko"), ("mobile-dark-en", 390, "dark", "en")]
SLICE, MAX_SLICES = 1600, 8


def shoot(page, out):
    warns = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, width, theme, lang in VIEWS:
            ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme="light")
            tab = ctx.new_page()
            errors = []
            tab.on("pageerror", lambda e: errors.append(str(e)))
            tab.goto(page.resolve().as_uri())
            tab.wait_for_load_state("load")
            tab.click(f'[data-set-theme="{theme}"]')
            tab.click(f'[data-set-lang="{lang}"]')
            state = tab.evaluate("[document.documentElement.dataset.lang, document.documentElement.dataset.theme]")
            if state != [lang, theme]:
                print(f"WARN {name}: the buttons did not switch the page (lang, theme = {state})")
                warns += 1
            scroll_w = tab.evaluate("document.documentElement.scrollWidth")
            if scroll_w > width + 1:
                print(f"WARN {name}: the page is {scroll_w}px wide in a {width}px window; "
                      "only figure and table boxes may scroll sideways")
                warns += 1
            if errors:
                print(f"WARN {name}: page script error: {errors[0]}")
                warns += 1
            height = tab.evaluate("document.documentElement.scrollHeight")
            for i, y in enumerate(range(0, height, SLICE)):
                if i == MAX_SLICES:
                    print(f"note {name}: {height}px tall, only the first {MAX_SLICES} slices are saved")
                    break
                shot = out / f"{page.stem}-{name}-{i + 1}.png"
                tab.screenshot(path=str(shot), full_page=True,
                               clip={"x": 0, "y": y, "width": width, "height": min(SLICE, height - y)})
                print(shot)
            ctx.close()
        browser.close()
    return 1 if warns else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    page = Path(a.html)
    if not page.is_file():
        print(f"ERROR {page}: file not found")
        return 1
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        return shoot(page, out)
    except Exception as e:
        node = shutil.which("node")
        if "driver" not in str(e) or not node or os.environ.get("PLAYWRIGHT_NODEJS_PATH"):
            raise
        print(f"note: Playwright's bundled Node.js did not start; retrying with {node}")
        os.environ["PLAYWRIGHT_NODEJS_PATH"] = node
        return shoot(page, out)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Screenshot a techblogs report page in the views a reader can get.

usage: uv run --no-project --with playwright==1.64.1 python preview.py <url-or-file> --out-dir DIR [--embedded]

Without --embedded the target is the report page itself (<slug>-report.html): 1440 px light Korean, 1440 px dark
English, 390 px light Korean and 390 px dark English, switched with the page's own buttons so the script runs too.
With --embedded the target is the blog post page that embeds the report (light Korean, 1440 px and 390 px), as built
by Jekyll and served over HTTP. Serve the built site (python3 -m http.server in _site) so that /assets/fonts loads.
Each view is cut into slices of at most 1600 px (6 at most). Prints the PNG paths; open them with the Read tool.
Prints WARN when the buttons do not switch the page, the page scrolls sideways, or the page script throws.
The system `node` is used through PLAYWRIGHT_NODEJS_PATH when it is on PATH.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWS = [("desktop-light-ko", 1440, "light", "ko"), ("desktop-dark-en", 1440, "dark", "en"),
         ("mobile-light-ko", 390, "light", "ko"), ("mobile-dark-en", 390, "dark", "en")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--embedded", action="store_true")
    a = ap.parse_args()
    url = a.target if "://" in a.target else Path(a.target).resolve().as_uri()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    warn = 0
    # Playwright's bundled Node.js does not start on some Linux hosts (libatomic.so.1 missing); use the system node.
    if "PLAYWRIGHT_NODEJS_PATH" not in os.environ and shutil.which("node"):
        os.environ["PLAYWRIGHT_NODEJS_PATH"] = shutil.which("node")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        views = [v for v in VIEWS if v[2] == "light"] if a.embedded else VIEWS
        for name, width, theme, lang in views:
            tab = browser.new_page(viewport={"width": width, "height": 900})
            errors = []
            tab.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
            tab.goto(url, wait_until="networkidle")
            if not a.embedded:
                tab.click('#themeSeg button[data-v="%s"]' % theme)
                tab.click('#langSeg button[data-v="%s"]' % lang)
                state = tab.evaluate("[document.documentElement.dataset.lang, document.documentElement.dataset.theme]")
                if state != [lang, theme]:
                    print("WARN %s: the buttons did not switch the page (lang, theme = %s)" % (name, state))
                    warn += 1
            tab.wait_for_timeout(600)
            tab.evaluate("document.fonts.ready")
            sw, cw = tab.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            if sw > cw + 1:
                print("WARN %s: the page scrolls sideways (%d > %d)" % (name, sw, cw))
                warn += 1
            for e in errors:
                print("WARN %s: script error: %s" % (name, e))
                warn += 1
            height = tab.evaluate("document.documentElement.scrollHeight")
            fonts = tab.evaluate("Array.from(document.fonts).filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight)")
            print("%s: height %d, fonts loaded: %s" % (name, height, sorted(set(fonts))))
            for i in range(min(6, (height + 1599) // 1600)):
                shot = out / ("%s-%d.png" % (name, i + 1))
                tab.screenshot(path=str(shot), clip={"x": 0, "y": i * 1600, "width": width, "height": min(1600, height - i * 1600)}, full_page=True)
                print(str(shot))
            tab.close()
        browser.close()
    return 1 if warn else 0


if __name__ == "__main__":
    sys.exit(main())

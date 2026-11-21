#!/usr/bin/env python3
"""Screenshot every slide of an HTML deck made by deck_to_html.py, and try its controls, before handing it over.

usage: uv run --no-project --with playwright python preview_html_deck.py <Deck>.html --out-dir qa-html

Writes <stem>-NN.png for every slide (1280 x 720, the size of the stage), <stem>-list.png (the slide list,
key G) and <stem>-presenter.png (the presenter view, key N). Prints the PNG paths; open them with the Read
tool and compare them with the slide pictures of the .pptx.

Prints a WARN line and exits 1 when
  - the page script throws, or the page asks the network for a file (the deck must be self-contained),
  - a font the page declares did not load,
  - the keys do not move the deck (→, End, Home), a slide does not show, or the list and the presenter view
    do not open,
  - the presenter window does not follow the audience window, or shows no notes for a slide that has them,
  - the glyphs of a text box need over 4 px more height than the box has (the text wrapped onto one more
    line than in the deck and runs over the shape below it).
When Playwright's bundled Node.js cannot start (for example libatomic.so.1 is missing on some Linux
hosts), it retries once with the system `node` through PLAYWRIGHT_NODEJS_PATH.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

W, H = 1280, 720
# Height the glyphs need: the paragraphs' height without the leading that line spacing adds to one line.
# A one-line title with 1.5 spacing is taller than its box in PowerPoint too; text that wraps one line more is not.
OVERFLOW = """() => [...document.querySelectorAll('.slide.active .tx')].map(b => {
  let wrapped = false;
  const ink = [...b.children].reduce((h, p) => {
    const cs = getComputedStyle(p), lh = parseFloat(cs.lineHeight) || 0, fs = parseFloat(cs.fontSize) || 0;
    if (lh && p.offsetHeight > lh * 1.5) wrapped = true;
    return h + p.offsetHeight - Math.max(0, lh - fs * 1.15);
  }, 0);
  return { over: wrapped ? Math.round(ink - b.offsetHeight) : 0, text: b.textContent.trim().slice(0, 24) };
}).filter(r => r.over > 4)"""


def shoot(page_path, out):
    warns = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": W, "height": H})
        tab = ctx.new_page()
        tab.on("pageerror", lambda e: warns.append("page script error: %s" % e))
        tab.on("request", lambda r: warns.append("the page asked the network for %s" % r.url[:80])
               if r.url.startswith(("http://", "https://")) else None)
        tab.goto(page_path.resolve().as_uri())
        tab.wait_for_load_state("load")
        tab.evaluate("document.fonts.ready")
        total = tab.evaluate("document.querySelectorAll('#deck > .slide').length")
        if not total:
            print("WARN no slides in the page")
            return 1
        failed = tab.evaluate("[...document.fonts].filter(f => f.status !== 'loaded').map(f => f.family)")
        tab.add_style_tag(content="#bar, #progress { display: none !important }")   # no controls in the pictures
        current = "() => [...document.querySelectorAll('#deck > .slide')].findIndex(s => s.classList.contains('active')) + 1"

        # keys
        tab.keyboard.press("ArrowRight")
        if total > 1 and tab.evaluate(current) != 2:
            warns.append("the → key did not move to slide 2")
        tab.keyboard.press("End")
        if tab.evaluate(current) != total:
            warns.append("the End key did not move to the last slide")
        tab.keyboard.press("Home")
        if tab.evaluate(current) != 1:
            warns.append("the Home key did not move to slide 1")

        # every slide
        for i in range(1, total + 1):
            tab.evaluate("i => { location.hash = '#' + i }", i)
            try:
                tab.wait_for_function("i => document.querySelector('#s' + i).classList.contains('active')", arg=i, timeout=3000)
            except Exception:
                warns.append("slide %d did not show when the address asked for it" % i)
                continue
            shot = out / ("%s-%02d.png" % (page_path.stem, i))
            tab.screenshot(path=str(shot))
            print(shot)
            for r in tab.evaluate(OVERFLOW):
                warns.append("slide %d: the text '%s' is %d px taller than its box" % (i, r["text"], r["over"]))
        for face in tab.evaluate("[...document.fonts].filter(f => f.status !== 'loaded').map(f => f.family)") if failed else []:
            warns.append("the font %s did not load" % face)

        # slide list
        tab.keyboard.press("g")
        if tab.evaluate("document.body.classList.contains('grid') ? document.querySelectorAll('#grid .thumb').length : 0") != total:
            warns.append("the slide list (G) did not open with every slide")
        else:
            shot = out / ("%s-list.png" % page_path.stem)
            tab.screenshot(path=str(shot))
            print(shot)
        tab.keyboard.press("Escape")

        # presenter view: N opens the second window; it must follow the audience window and show the notes
        tab.evaluate("location.hash = '#1'")
        try:
            with ctx.expect_page(timeout=8000) as popup:
                tab.keyboard.press("n")
            pv = popup.value
            pv.on("pageerror", lambda e: warns.append("presenter view script error: %s" % e))
            pv.wait_for_selector("#pv .cur .slide")
            pv.set_viewport_size({"width": W, "height": 800})
            step = min(2, total)
            tab.bring_to_front()
            if step == 2:
                tab.keyboard.press("ArrowRight")
            pv.wait_for_function("t => document.querySelector('#pv .count').textContent.trim() === t",
                                 arg="%d / %d" % (step, total), timeout=5000)
            has_notes = tab.evaluate("i => !!document.querySelector('#s' + i + ' .notes p')", step)
            if has_notes and pv.evaluate("document.querySelectorAll('#pv .text p:not(.none)').length") == 0:
                warns.append("the presenter view shows no notes for slide %d" % step)
            shot = out / ("%s-presenter.png" % page_path.stem)
            pv.screenshot(path=str(shot))
            print(shot)
            pv.keyboard.press("ArrowRight")          # and the other way round
            if total > step:
                tab.wait_for_function("i => document.querySelector('#s' + i).classList.contains('active')", arg=step + 1, timeout=5000)
        except Exception as e:                        # a timeout here means the two windows do not talk
            warns.append("the presenter view (N) did not open or did not follow the deck: %s" % str(e).splitlines()[0][:120])
        browser.close()
    for w in dict.fromkeys(warns):
        print("WARN " + w)
    return 1 if warns else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    page = Path(a.html)
    if not page.is_file():
        print("ERROR %s: file not found" % page)
        return 1
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        return shoot(page, out)
    except Exception as e:
        node = shutil.which("node")
        if "driver" not in str(e) or not node or os.environ.get("PLAYWRIGHT_NODEJS_PATH"):
            raise
        print("note: Playwright's bundled Node.js did not start; retrying with %s" % node)
        os.environ["PLAYWRIGHT_NODEJS_PATH"] = node
        return shoot(page, out)


if __name__ == "__main__":
    sys.exit(main())

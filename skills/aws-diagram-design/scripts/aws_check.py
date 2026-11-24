#!/usr/bin/env python3
"""Check a generated diagram HTML or SVG file against the rules of the AWS edition.

    python3 <skill-dir>/scripts/aws_check.py my-diagram.html [more files]

Run it after self_check.py and verify_geometry.py. It reads the file as text and checks three things
those two do not:

  separators  no middle dot in the text of an SVG <text> element (style-guide.md, Separators)
  fonts       nothing loads a font from outside the file: no font <link>, no @import, no CSS url()
              (style-guide.md, Font source: system)
  fallback    a font-family that names Amazon Ember ends in a generic family, so a machine
              without the font still renders the diagram

Standard library only. Exit codes: 0 every file passes, 1 a rule is broken, 2 a file cannot be read.
"""
import re
import sys

COMMENT = re.compile(r"<!--.*?-->", re.S)
SVG = re.compile(r"<svg\b.*?</svg>", re.S | re.I)
SVG_TEXT = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
STYLE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
LINK = re.compile(r"<link\b[^>]*>", re.I)
FONT_FACE = re.compile(r"@font-face\s*\{[^}]*\}", re.I | re.S)
CSS_URL = re.compile(r"url\(\s*[\"']?(?!\s*#)", re.I)
STYLE_ATTR = re.compile(r"""\bstyle\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
FAMILY_ATTR = re.compile(r"""font-family\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
FAMILY_CSS = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
FONT_VAR = re.compile(r"--font-[\w-]+\s*:\s*([^;}\n]+)", re.I)
FONT_SHORTHAND = re.compile(r"(?<![\w-])font\s*:\s*([^;}\n]+)", re.I)
GENERIC = ("sans-serif", "serif", "monospace", "system-ui", "ui-monospace", "ui-sans-serif", "ui-serif", "inherit")
MIDDLE_DOTS = ("·", "&middot;", "&#183;", "&#xb7;", "&centerdot;")


def separators(source):
    for svg in SVG.findall(source):
        for raw in SVG_TEXT.findall(svg):
            if any(dot in raw.lower() for dot in MIDDLE_DOTS):
                text = " ".join(TAG.sub("", raw).split())
                yield "middle dot in SVG text %r: write '/' for a pair and commas for a list" % text[:60]


def fonts(source):
    for link in LINK.findall(source):
        if re.search(r"rel\s*=\s*[\"']?[^\"'>]*stylesheet", link, re.I) or "fonts." in link.lower():
            yield "a <link> loads a stylesheet or a font: the AWS skin uses installed fonts only (%s)" % link[:80]
    css = "\n".join(STYLE.findall(source))
    if re.search(r"@import\b", css, re.I):
        yield "CSS @import: the AWS skin loads nothing from outside the file"
    if re.search(r"@font-face\b[^}]*url\(", css, re.I | re.S):
        yield "@font-face with url(): name installed fonts with local() or leave @font-face out"
    elif CSS_URL.search(css) or any(CSS_URL.search(a or b) for a, b in STYLE_ATTR.findall(source)):
        yield "CSS url() that is not a fragment: a diagram is one file and loads nothing"


def fallback(source):
    # An @font-face rule names the family it defines: that is not a use of the family
    css = FONT_FACE.sub("", "\n".join(STYLE.findall(source)))
    values = [a or b for a, b in FAMILY_ATTR.findall(source)]
    values += FAMILY_CSS.findall(css) + FONT_VAR.findall(css) + FONT_SHORTHAND.findall(css)
    seen = set()
    for value in values:
        value = " ".join(value.split())
        if "amazon ember" not in value.lower() or "var(" in value or value in seen:
            continue
        seen.add(value)
        last = value.rstrip(" ;").split(",")[-1].strip().strip("'\"").lower()
        if last.endswith("!important"):
            last = last[:-len("!important")].strip()
        if last not in GENERIC:
            yield "font-family %r names Amazon Ember without a generic fallback at the end" % value[:70]


def check(path):
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError) as err:
        print("ERROR %s: %s" % (path, err))
        return 2
    source = COMMENT.sub("", source)
    problems = list(separators(source)) + list(fonts(source)) + list(fallback(source))
    for problem in problems:
        print("FAIL %s: %s" % (path, problem))
    if not problems:
        print("OK %s" % path)
    return 1 if problems else 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv else 2
    return max(check(path) for path in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

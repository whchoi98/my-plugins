#!/usr/bin/env python3
"""Put every <img src="relative/path"> of an html-report page into the file as a data URI, so the page is one file.

usage: python3 embed_images.py report/page.html -o report/out/page.html

Only image files (png, jpg, jpeg, gif, webp, svg) inside the page's own folder are read. A path that leaves
that folder (../, an absolute path, a symlink pointing out) is refused, so nothing outside the report is
copied into a file that will be shared. data:, http(s): and # sources are left as they are.
Exit code 1 when an image is missing or refused; the output is not written then. Standard library only.
"""
import argparse
import base64
import re
import sys
from pathlib import Path
from urllib.parse import unquote

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".webp": "image/webp", ".svg": "image/svg+xml"}
IMG_SRC = re.compile(r"""(<img\b[^>]*?\bsrc\s*=\s*)(["'])(.*?)\2""", re.I | re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="page with relative image paths")
    ap.add_argument("-o", "--output", required=True, help="single-file page to write")
    a = ap.parse_args()
    src = Path(a.html)
    if not src.is_file():
        print(f"ERROR {src}: file not found")
        return 1
    base = src.resolve().parent
    problems, count = [], 0

    def embed(m):
        nonlocal count
        url = m.group(3).strip()
        if not url or url.startswith(("data:", "http://", "https://", "#")):
            return m.group(0)
        path = (base / unquote(url.split("#")[0].split("?")[0])).resolve()
        if not path.is_relative_to(base):
            problems.append(f"{url}: outside the page folder {base}, not embedded")
        elif path.suffix.lower() not in MIME:
            problems.append(f"{url}: not an image file ({path.suffix or 'no extension'})")
        elif not path.is_file():
            problems.append(f"{url}: file not found")
        else:
            count += 1
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"{m.group(1)}{m.group(2)}data:{MIME[path.suffix.lower()]};base64,{data}{m.group(2)}"
        return m.group(0)

    html = IMG_SRC.sub(embed, src.read_text(encoding="utf-8"))
    if problems:
        for p in problems:
            print(f"ERROR {p}")
        print("nothing written")
        return 1
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"embedded {count} image(s) -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

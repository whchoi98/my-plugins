#!/usr/bin/env python3
"""Inline bundled icons into an SVG, producing a portable standalone file.

In your draft SVG, reference icons from the bundle with the `bundle:` scheme:

    <image href="bundle:service/AWS-Lambda"  x="200" y="200" width="56" height="56"/>
    <image href="bundle:group/AWS-Cloud_32"  x="30"  y="30"  width="26" height="26"/>
    <image href="bundle:agentcore-dark/Runtime" x="80" y="80" width="52" height="52"/>

Then:  python scripts/embed.py draft.svg final.svg

Each bundle: ref is replaced with a data: URI pulled from assets/icons.json,
so the final SVG renders anywhere with no external files. Refs that don't
resolve are reported and left as-is.
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = json.loads((ROOT / "assets" / "icons.json").read_text(encoding="utf-8"))
SETS = BUNDLE["sets"]

REF_RE = re.compile(r'(?:xlink:)?href\s*=\s*"bundle:([^"]+)"')


def data_uri(setname: str, name: str):
    entry = SETS.get(setname, {}).get(name)
    if entry is None:
        return None
    if entry["type"] == "svg":
        b64 = base64.b64encode(entry["data"].encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    return f"data:image/png;base64,{entry['data']}"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    svg = src.read_text(encoding="utf-8")
    missing, embedded = [], 0

    def repl(m):
        nonlocal embedded
        ref = m.group(1)
        setname, _, name = ref.partition("/")
        uri = data_uri(setname, name)
        if uri is None:
            missing.append(ref)
            return m.group(0)
        embedded += 1
        return m.group(0).replace(f"bundle:{ref}", uri)

    out = REF_RE.sub(repl, svg)
    dst.write_text(out, encoding="utf-8")
    print(f"Embedded {embedded} icon(s) -> {dst}")
    if missing:
        print("MISSING (fix these refs — check names with find_icon.py):")
        for r in missing:
            print(f"  bundle:{r}")


if __name__ == "__main__":
    main()

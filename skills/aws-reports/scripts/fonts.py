#!/usr/bin/env python3
"""Make per-report font subsets.

usage: uv run --no-project --with fonttools --with brotli python fonts.py --text-file T --code-file C --out-dir D

- D/D2Coding-docx.ttf : printable ASCII + Latin-1 subset of D2Coding, embedded in the .docx so inline code
  renders in D2Coding even where the font is not installed (D2Coding is TrueType with fsType 8, OFL-1.1).
- D/<family>-<weight>.woff2 : only the characters this report uses, inlined into the HTML via @font-face.
  NanumSquareOTF is CFF-based, so Word cannot embed it; the HTML can.
Prints one JSON line: {"docx_mono": path|null, "html": [{family, weight, local, file}], "missing": [...]}.
"""
import argparse
import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

SEARCH = [Path.home() / ".local/share/fonts", Path.home() / ".fonts", Path.home() / "Library/Fonts", Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
          Path("/Library/Fonts"), Path("C:/Windows/Fonts")]
FACES = [  # (family, weight, file names to look for, local() name)
    ("NanumSquareOTF", 400, ["NanumSquareR.otf", "NanumSquareOTFR.otf", "NanumSquareOTF_acR.otf"], "NanumSquareOTF"),
    ("NanumSquareOTF", 700, ["NanumSquareB.otf", "NanumSquareOTFB.otf", "NanumSquareOTF_acB.otf"], "NanumSquareOTF Bold"),
    ("D2Coding", 400, ["D2Coding.ttf", "D2Coding-Ver1.3.2-20180524.ttf"], "D2Coding"),
]
ASCII = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | set(range(0x2010, 0x2028))


def find(names):
    for root in SEARCH:
        if not root.exists():
            continue
        for n in names:
            hit = next(root.rglob(n), None)
            if hit:
                return hit
    return None


def make(src, out, chars, flavor=None):
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.drop_tables += ["FFTM"]
    opts.flavor = flavor
    font = TTFont(str(src))
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=sorted(chars))
    sub.subset(font)
    font.flavor = flavor
    font.save(str(out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--code-file", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    text = Path(a.text_file).read_text(encoding="utf-8")
    code = Path(a.code_file).read_text(encoding="utf-8")
    used = {ord(c) for c in text if not c.isspace()} | ASCII
    used_code = {ord(c) for c in code if not c.isspace()} | ASCII
    res = {"docx_mono": None, "html": [], "missing": []}
    for family, weight, names, local in FACES:
        src = find(names)
        if not src:
            res["missing"].append(f"{family} {weight}")
            continue
        chars = used_code if family == "D2Coding" else used
        f = make(src, out / f"{family}-{weight}.woff2", chars, flavor="woff2")
        res["html"].append({"family": family, "weight": weight, "local": local, "file": str(f)})
        if family == "D2Coding":
            res["docx_mono"] = str(make(src, out / "D2Coding-docx.ttf", ASCII))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

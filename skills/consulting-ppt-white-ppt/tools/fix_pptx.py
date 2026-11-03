#!/usr/bin/env python3
"""
fix_pptx.py - PowerPoint-compatibility fixes for pptxgenjs output.

LibreOffice renders these fine WITHOUT the fixes, so QA renders can hide the bugs;
PowerPoint needs them. Run on the .pptx right after pptxgenjs writeFile().

Fix 1 - round2SameRect geometry (top-rounded cards):
  pptxgenjs writes <a:gd name="adj">, but this preset needs adj1 (top) + adj2 (bottom).
  Wrong guide name -> PowerPoint cannot resolve the geometry and HIDES the shape.
  Rewrite to adj1 = <radius>, adj2 = 0  (top corners rounded, bottom square).

Fix 2 - character bullets:
  pptxgenjs emits <a:buChar> with NO <a:buFont>, so PowerPoint cannot resolve the
  bullet glyph and shows NO bullet (the bullets "disappear").
  Insert <a:buFont typeface="Arial"/> before every <a:buChar>. Idempotent.

Usage:  python fix_pptx.py deck.pptx
"""
import sys, re, zipfile, shutil

_BUFONT = '<a:buFont typeface="Arial" pitchFamily="34" charset="0"/>'


def fix(path):
    tmp = path + ".tmp"
    rounds = bullets = 0
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/slides/") and item.filename.endswith(".xml"):
                txt = data.decode("utf-8")
                # Fix 1: round2SameRect single "adj" -> adj1 (radius) + adj2 (0)
                txt, n1 = re.subn(
                    r'(<a:prstGeom prst="round2SameRect"><a:avLst>)<a:gd name="adj" fmla="val (\d+)"/>(</a:avLst>)',
                    r'\1<a:gd name="adj1" fmla="val \2"/><a:gd name="adj2" fmla="val 0"/>\3',
                    txt,
                )
                rounds += n1
                # Fix 2: ensure every <a:buChar> is preceded by a <a:buFont> (idempotent)
                txt = re.sub(r'<a:buFont[^>]*/>(<a:buChar )', r'\1', txt)   # strip any existing
                txt, n2 = re.subn(r'(<a:buChar )', _BUFONT + r'\1', txt)    # add fresh, correct order
                bullets += n2
                data = txt.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)
    return rounds, bullets


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python fix_pptx.py deck.pptx"); sys.exit(1)
    r, b = fix(sys.argv[1])
    print(f"fixed round2SameRect guides: {r}, bullet fonts added: {b}")

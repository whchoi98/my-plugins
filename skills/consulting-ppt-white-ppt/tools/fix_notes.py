#!/usr/bin/env python3
# Split speaker notes into one sentence per line by converting the sentence
# boundary ". " (period + space) inside note text runs into an OOXML <a:br/>.
# Only touches ppt/notesSlides/notesSlideN.xml. Sentence boundary = a period
# followed by a space and a non-space, non-tag char (so version numbers like
# "2.17" and trailing ". </a:t>" are left untouched).
import sys, zipfile, re

path = sys.argv[1]
zin = zipfile.ZipFile(path, "r")
items = [(n, zin.read(n)) for n in zin.namelist()]
zin.close()

# ". " -> end this run, insert <a:br/>, start a new run (new runs inherit notes default fmt)
pat = re.compile(rb"\. (?=[^<\s])")
repl = rb".</a:t></a:r><a:br/><a:r><a:t>"

out = []
n_breaks = 0
for name, data in items:
    if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml"):
        data, k = pat.subn(repl, data)
        n_breaks += k
    out.append((name, data))

zout = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
for name, data in out:
    zout.writestr(name, data)
zout.close()
print("notes line-breaks inserted:", n_breaks)

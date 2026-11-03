#!/usr/bin/env python3
"""Lint a finished deck against the skill rules (run after apply_template.py, before visual QA).

Checks
  ERROR  slide size differs from the 13.333 x 7.5 in template, or template not applied (AWS_* layout)
  ERROR  footer text drawn on a slide (copyright belongs to the template)
  ERROR  middle dot (U+00B7) or em-dash (U+2014) in slide text or notes
  ERROR  native chart without an embedded Excel workbook (chart would not be editable)
  WARN   presentation time on the Agenda or in speaker notes (10분, 30분 동안, 시간 관계상),
         slide text ending in a predicate (~합니다, ~입니다 ...) instead of a noun phrase,
         fonts other than NanumSquareOTF Bold / D2Coding, top-anchored text outside code boxes,
         speaker notes shorter than 4 lines, pictures without a vector SVG (charts must be native)

Usage
  python3 check_deck.py <Deck>.pptx
"""
from __future__ import annotations

import re
import sys
from pptx import Presentation
from pptx.util import Emu

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
ALLOWED_FONTS = {"NanumSquareOTF Bold", "D2Coding"}
BAD_CHARS = {"·": "middle dot", "—": "em-dash"}
# Slide copy must end in a noun phrase ("컨테이너 이미지로 배포"), not a predicate ("배포합니다.").
PREDICATE_END = re.compile(r"(습니다|합니다|입니다|됩니다|있습니다|없습니다|십시오|하세요|해요|이다|한다|된다)[.!?]?\s*$")
# No presentation time on the Agenda or in scripts. "1분기", "3분의 1" etc. are content, not time.
MINUTES = r"\d+\s*분(?![기의할산석류야포리배])|\d+\s*(?:min|mins|minutes)\b"
TIME_TALK = re.compile(MINUTES + r"|시간\s*배분|시간\s*관계상|남은\s*시간", re.I)
AGENDA_TIME = re.compile(MINUTES, re.I)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    prs = Presentation(sys.argv[1])
    errors, warns = [], []
    w, h = Emu(prs.slide_width).inches, Emu(prs.slide_height).inches
    if abs(w - 13.333) > 0.01 or abs(h - 7.5) > 0.01:
        errors.append(f"slide size {w:.3f}x{h:.3f} in, expected 13.333x7.5 (template)")

    for i, slide in enumerate(prs.slides, 1):
        tag = f"slide {i}"
        if slide.slide_layout.name.upper().startswith("AWS_"):
            errors.append(f"{tag}: template not applied (layout {slide.slide_layout.name}) - run apply_template.py")
        sp_tree = slide.shapes._spTree
        texts = []
        for t in sp_tree.iter(f"{A}t"):
            texts.append(t.text or "")
        joined = "".join(texts)
        if "agenda" in slide.slide_layout.name.lower() and AGENDA_TIME.search(joined):
            warns.append(f"{tag}: time on the Agenda ('{AGENDA_TIME.search(joined).group(0)}') - rows carry number, title, meta only")
        if "Amazon Web Services, Inc." in joined or "© 20" in joined:
            errors.append(f"{tag}: copyright/footer text drawn on the slide - the template provides it")
        for ch, name in BAD_CHARS.items():
            if ch in joined:
                errors.append(f"{tag}: {name} in slide text")
        fonts = set()
        for shape in sp_tree.iterchildren():
            if shape.find(f"{P}nvSpPr/{P}nvPr/{P}ph") is not None:
                continue  # template-owned placeholder (slide number) keeps the template's own font
            for tag_name in ("latin", "ea"):
                for el in shape.iter(f"{A}{tag_name}"):
                    face = el.get("typeface", "")
                    if face and not face.startswith("+"):
                        fonts.add(face)
        odd = sorted(fonts - ALLOWED_FONTS)
        if odd:
            warns.append(f"{tag}: fonts outside the standard set: {', '.join(odd)}")
        for sp in sp_tree.iter(f"{P}sp"):
            if sp.find(f"{P}nvSpPr/{P}nvPr/{P}ph") is not None:
                continue
            faces = {el.get("typeface") for el in sp.iter(f"{A}latin")}
            if "D2Coding" not in faces:
                for para in sp.iter(f"{A}p"):
                    line = "".join(t.text or "" for t in para.iter(f"{A}t")).strip()
                    if line and PREDICATE_END.search(line):
                        warns.append(f"{tag}: predicate ending, use a noun phrase: '{line[-24:]}'")
        for sp in sp_tree.iter(f"{P}sp"):
            body = sp.find(f"{P}txBody/{A}bodyPr")
            if body is None or body.get("anchor") != "t":
                continue
            faces = {el.get("typeface") for el in sp.iter(f"{A}latin")}
            if "D2Coding" not in faces and "".join(x.text or "" for x in sp.iter(f"{A}t")).strip():
                warns.append(f"{tag}: top-anchored text box (use valign middle; code boxes excepted)")
        for pic in sp_tree.iter(f"{P}pic"):
            name = pic.find(f"{P}nvPicPr/{P}cNvPr").get("name", "")
            if not any(e.tag.endswith("}svgBlip") for e in pic.iter()):
                warns.append(f"{tag}: picture '{name}' has no vector SVG - charts must use addNativeChart, diagrams addDiagram")
        for gf in slide.shapes:
            if getattr(gf, "has_chart", False) and gf.has_chart:
                part = gf.chart.part
                if part.chart_workbook.xlsx_part is None:
                    errors.append(f"{tag}: chart '{gf.name}' has no embedded workbook (not editable)")
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        lines = [ln for ln in notes.splitlines() if ln.strip()]
        for ch, name in BAD_CHARS.items():
            if ch in notes:
                errors.append(f"{tag}: {name} in speaker notes")
        hit = TIME_TALK.search(notes)
        if hit:
            warns.append(f"{tag}: presentation time in speaker notes ('{hit.group(0)}')")
        if len(lines) < 4:
            warns.append(f"{tag}: speaker notes have {len(lines)} line(s), expected 4+ (one sentence per line)")

    for msg in errors:
        print("ERROR", msg)
    for msg in warns:
        print("WARN ", msg)
    print(f"{len(prs.slides)} slides, {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿-필 결과 QA.

템플릿-필의 실패는 대부분 눈에 잘 안 띄는 형태로 나타난다.
 - 어느 카드 하나에 'Text 15', '20XX' 같은 템플릿 잔존물이 남음
 - 새 문구가 길어져 표 셀이나 도형 밖으로 밀림
 - 폰트가 섞여 한 슬라이드에 두세 종류가 공존
 - 노트가 한 문단으로 뭉쳐 발표 중 읽기 어려움
이 스크립트는 그 네 가지를 기계적으로 잡아낸다.

사용법
  python qa_check.py out.pptx
  python qa_check.py out.pptx --tokens "20XX,DATA,Lorem,TBD,Text 15"
  python qa_check.py out.pptx --font "나눔스퀘어OTF Bold" --forbid-punct "·,—"
  python qa_check.py out.pptx --render                 # PDF 렌더 후 화면 밖 텍스트 검사
  python qa_check.py out.pptx --render --ref before.pptx   # 원본 대비 문자 손실 검사

--render 는 soffice(LibreOffice)와 pdftotext(poppler)가 필요하다.
대상 폰트가 설치돼 있지 않으면 렌더는 대체 폰트로 근사되므로, 오버플로 결과는
'경향' 으로만 읽고 최종 확인은 PowerPoint 에서 하도록 사용자에게 안내할 것.
근사 정확도를 높이려면 fontconfig 별칭을 걸어 유사 폰트로 매핑한다
(references/recipes.md 의 '폰트 미설치 환경 렌더 QA' 참고).
"""
import argparse
import collections
import os
import re
import shutil
import subprocess
import sys
import zipfile

from pptx import Presentation

FAIL = []
WARN = []


def ok(msg):
    print(f"  OK   {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"  FAIL {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"  WARN {msg}")


def iter_runs(prs):
    """(슬라이드번호, 텍스트, run객체) 를 표/그룹까지 포함해 순회."""
    def shapes_of(shapes):
        for sh in shapes:
            yield sh
            if sh.shape_type == 6:
                yield from shapes_of(sh.shapes)

    for i, sl in enumerate(prs.slides, 1):
        for sh in shapes_of(sl.shapes):
            if sh.has_text_frame:
                for pa in sh.text_frame.paragraphs:
                    for r in pa.runs:
                        yield i, r.text, r
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        for pa in c.text_frame.paragraphs:
                            for r in pa.runs:
                                yield i, r.text, r


def check_structure(path):
    print("\n[1] 구조/무결성")
    prs = Presentation(path)
    n = len(prs.slides)
    ok(f"열기 성공, 슬라이드 {n}장")
    from lxml import etree
    bad = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith((".xml", ".rels")):
                try:
                    etree.fromstring(z.read(name))
                except Exception as e:
                    bad.append(f"{name}: {str(e)[:50]}")
    if bad:
        fail(f"XML 파싱 오류 {len(bad)}건: {bad[:3]}")
    else:
        ok("전 파트 XML 유효")
    return prs


def check_tokens(prs, tokens):
    print("\n[2] 템플릿 잔존물")
    if not tokens:
        ok("검사 토큰 미지정 (--tokens 로 지정 권장)")
        return
    hits = collections.defaultdict(list)
    for sidx, text, _ in iter_runs(prs):
        for t in tokens:
            if t and t in text:
                hits[t].append(sidx)
    if hits:
        for t, pages in hits.items():
            fail(f"'{t}' 잔존 - 슬라이드 {sorted(set(pages))}")
    else:
        ok(f"잔존물 없음 ({len(tokens)}개 토큰 검사)")


def check_punct(prs, forbidden):
    print("\n[3] 금지 구두점")
    if not forbidden:
        ok("검사 문자 미지정")
        return
    hits = collections.defaultdict(list)
    for sidx, text, _ in iter_runs(prs):
        for ch in forbidden:
            if ch and ch in text:
                hits[ch].append(sidx)
    # 노트도 검사 (발표 노트에도 같은 규칙을 적용하는 경우가 많다)
    for i, sl in enumerate(prs.slides, 1):
        if sl.has_notes_slide and sl.notes_slide.notes_text_frame:
            t = sl.notes_slide.notes_text_frame.text
            for ch in forbidden:
                if ch and ch in t:
                    hits[ch].append(f"S{i}노트")
    if hits:
        for ch, pages in hits.items():
            fail(f"'{ch}' 발견 - {sorted(set(map(str, pages)))}")
    else:
        ok(f"금지 문자 없음 ({''.join(forbidden)})")


def check_fonts(path, expected):
    print("\n[4] 폰트 일관성")
    counter = collections.Counter()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".xml"):
                continue
            if not name.startswith(("ppt/slides/", "ppt/notesSlides/", "ppt/charts/",
                                    "ppt/slideLayouts/", "ppt/slideMasters/", "ppt/theme/")):
                continue
            x = z.read(name).decode("utf-8", "ignore")
            for m in re.finditer(r'<a:(latin|ea|cs)\b[^>]*typeface="([^"]*)"', x):
                counter[m.group(2)] += 1
    if not counter:
        warn("텍스트 폰트 지정을 찾지 못함")
        return
    top = counter.most_common()
    print(f"       사용 폰트: {dict(top[:6])}")
    if expected:
        others = {k: v for k, v in counter.items() if k != expected}
        if others:
            fail(f"'{expected}' 외 폰트 잔존: {others}")
        else:
            ok(f"전량 '{expected}' ({counter[expected]}곳)")
    elif len(top) > 3:
        warn(f"폰트 종류 {len(top)}종 - 의도한 조합인지 확인")
    else:
        ok(f"폰트 {len(top)}종")


def check_notes(prs, path):
    print("\n[5] 발표 노트")
    from lxml import etree
    written, multi, single = 0, 0, []
    for i, sl in enumerate(prs.slides, 1):
        if not sl.has_notes_slide:
            continue
        tf = sl.notes_slide.notes_text_frame
        if tf is None or not tf.text.strip():
            continue
        written += 1
        # 문단이 2개 이상이면 python-pptx 로 넣은 줄바꿈,
        # <a:br/> 이 있으면 pptxgenjs 계열에서 변환한 줄바꿈이다.
        xml = etree.tostring(sl.notes_slide.part._element, encoding="unicode")
        if len(tf.paragraphs) >= 2 or "<a:br/>" in xml:
            multi += 1
        else:
            single.append(i)
    if written == 0:
        warn("노트가 비어 있음")
        return
    ok(f"노트 작성 {written}/{len(prs.slides)}장, 줄바꿈 적용 {multi}장")
    if single:
        warn(f"한 문단으로 뭉친 노트: 슬라이드 {single[:10]} - 문장별 줄바꿈 권장")


def render(path, tag):
    if not shutil.which("soffice"):
        warn("soffice 없음 - 렌더 검사 생략")
        return None
    out = f"_qa_{tag}"
    os.makedirs(out, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out, path],
                   capture_output=True, timeout=900)
    pdf = os.path.join(out, os.path.splitext(os.path.basename(path))[0] + ".pdf")
    return pdf if os.path.exists(pdf) else None


def page_words(pdf):
    """pdftotext -bbox-layout 으로 단어별 좌표를 얻는다."""
    from lxml import etree
    xml = pdf + ".bbox.xml"
    subprocess.run(["pdftotext", "-bbox-layout", pdf, xml], capture_output=True)
    if not os.path.exists(xml):
        return []
    H = "{http://www.w3.org/1999/xhtml}"
    pages = []
    for pg in etree.parse(xml).getroot().iter(H + "page"):
        W, Hh = float(pg.get("width")), float(pg.get("height"))
        words = [(float(w.get("xMin")), float(w.get("yMin")),
                  float(w.get("xMax")), float(w.get("yMax")), w.text or "")
                 for w in pg.iter(H + "word")]
        pages.append((W, Hh, words))
    return pages


def page_text(pdf):
    out = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
    return [re.sub(r"\s+", "", p) for p in out.split("\f")]


def check_render(path, ref):
    print("\n[6] 렌더 검사 (화면 밖 텍스트 / 문자 손실)")
    if not shutil.which("pdftotext"):
        warn("pdftotext 없음 - 렌더 검사 생략")
        return
    pdf = render(path, "new")
    if not pdf:
        warn("PDF 변환 실패")
        return
    pages = page_words(pdf)
    off = 0
    for i, (W, H, words) in enumerate(pages, 1):
        bad = [w for w in words if w[2] > W - 2 or w[3] > H - 2 or w[0] < 2]
        if bad:
            off += 1
            fail(f"S{i} 화면 밖 텍스트 {len(bad)}개: {[w[4] for w in bad[:4]]}")
    if not off:
        ok(f"{len(pages)}장 모두 텍스트가 슬라이드 안에 있음")

    if not ref:
        return
    rpdf = render(ref, "ref")
    if not rpdf:
        warn("기준 파일 PDF 변환 실패")
        return
    a, b = page_text(rpdf), page_text(pdf)
    issues = []
    for i, (x, y) in enumerate(zip(a, b), 1):
        ca, cb = collections.Counter(x), collections.Counter(y)
        lost, gained = ca - cb, cb - ca
        if lost or gained:  # 문자 집합이 같고 순서만 다르면 정상(추출 순서 차이)
            issues.append((i, "".join(sorted(lost.elements()))[:40],
                           "".join(sorted(gained.elements()))[:40]))
    if issues:
        for i, lost, gained in issues[:8]:
            warn(f"S{i} 문자 차이 손실='{lost}' 추가='{gained}' "
                 f"(차트 축 눈금 자동 간격 변화일 수 있음)")
    else:
        ok("기준 대비 문자 손실 없음")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--tokens", default="")
    ap.add_argument("--font", default="")
    ap.add_argument("--forbid-punct", default="")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--ref", default="")
    args = ap.parse_args()

    print(f"QA: {args.pptx}")
    prs = check_structure(args.pptx)
    check_tokens(prs, [t.strip() for t in args.tokens.split(",") if t.strip()])
    check_punct(prs, [c.strip() for c in args.forbid_punct.split(",") if c.strip()])
    check_fonts(args.pptx, args.font)
    check_notes(prs, args.pptx)
    if args.render:
        check_render(args.pptx, args.ref)

    print("\n" + "=" * 46)
    if FAIL:
        print(f"실패 {len(FAIL)}건 / 경고 {len(WARN)}건")
        for m in FAIL:
            print(f"  - {m}")
        return 1
    print(f"통과 (경고 {len(WARN)}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

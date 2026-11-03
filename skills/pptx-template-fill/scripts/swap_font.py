#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
덱 전체 폰트 통일 (OOXML 후처리).

python-pptx 의 run.font.name 만 건드리면 표 기본 스타일, 차트 텍스트,
레이아웃/마스터/테마, 발표 노트에 남은 폰트가 그대로 살아 혼용이 생긴다.
그래서 패키지를 풀어 모든 파트의 typeface 를 직접 통일한다.

사용법
  python swap_font.py in.pptx out.pptx "나눔스퀘어OTF Bold"
  python swap_font.py in.pptx out.pptx "Noto Sans KR" --keep-embedded
  python swap_font.py in.pptx out.pptx "Arial" --latin-only   # 영문 슬롯만 교체

무엇을 바꾸고 무엇을 남기는가
  바꿈 : rPr/defRPr/endParaRPr 의 a:latin, a:ea, a:cs  (누락 시 스키마 순서대로 삽입)
         theme 의 majorFont/minorFont, '+mn-lt' 같은 테마 참조 토큰
  남김 : a:buFont (글머리표 기호 폰트) - 바꾸면 Wingdings 계열 기호가 깨진다
         a:sym, theme 의 <a:font script="..."> 스크립트별 폴백 목록
         b="1" 굵기 플래그 - 폰트명에 Bold 가 포함된 경우 이중 굵게를 피하려면
                             기존 상태를 그대로 두는 것이 안전하다

한글 텍스트는 a:ea, 영문/숫자는 a:latin 경로로 렌더링되므로 세 슬롯(latin/ea/cs)을
함께 지정해야 한 문장 안에서 폰트가 섞이지 않는다.
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

from lxml import etree

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

RPR_TAGS = {f"{{{A}}}rPr", f"{{{A}}}defRPr", f"{{{A}}}endParaRPr"}
# CT_TextCharacterProperties 에서 latin/ea/cs 뒤에 오는 요소들 (삽입 위치 계산용)
AFTER = [f"{{{A}}}sym", f"{{{A}}}hlinkClick", f"{{{A}}}hlinkMouseOver",
         f"{{{A}}}rtl", f"{{{A}}}extLst"]

TARGET_PREFIX = ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/",
                 "ppt/notesSlides/", "ppt/notesMasters/", "ppt/charts/",
                 "ppt/theme/", "ppt/drawings/", "ppt/diagrams/",
                 "ppt/handoutMasters/")
TARGET_EXACT = ("ppt/presProps.xml", "ppt/tableStyles.xml")


def fix_charprops(root, font, slots):
    stats = {"set": 0, "inserted": 0}
    for el in root.iter():
        if el.tag not in RPR_TAGS:
            continue
        insert_at = len(el)
        for i, child in enumerate(el):
            if child.tag in AFTER:
                insert_at = i
                break
        for slot in slots:
            node = el.find(f"{{{A}}}{slot}")
            if node is None:
                node = etree.SubElement(el, f"{{{A}}}{slot}")
                el.remove(node)
                el.insert(insert_at, node)
                insert_at += 1
                stats["inserted"] += 1
            else:
                stats["set"] += 1
            node.set("typeface", font)
            # 이전 폰트의 메트릭 힌트가 남으면 대체 동작이 어긋날 수 있다
            for attr in ("pitchFamily", "charset", "panose"):
                node.attrib.pop(attr, None)
    return stats


def fix_theme(root, font, slots):
    n = 0
    for scheme in ("majorFont", "minorFont"):
        for fs in root.iter(f"{{{A}}}{scheme}"):
            for i, slot in enumerate(slots):
                node = fs.find(f"{{{A}}}{slot}")
                if node is None:
                    node = etree.Element(f"{{{A}}}{slot}")
                    fs.insert(i, node)
                node.set("typeface", font)
                for attr in ("pitchFamily", "charset", "panose"):
                    node.attrib.pop(attr, None)
                n += 1
    return n


def strip_embedded_fonts(work):
    """교체 후 쓰이지 않는 임베딩 폰트 제거. 파일 크기를 크게 줄인다."""
    removed = []
    fonts_dir = os.path.join(work, "ppt", "fonts")
    if os.path.isdir(fonts_dir):
        removed = sorted(os.listdir(fonts_dir))
        shutil.rmtree(fonts_dir)

    pres = os.path.join(work, "ppt", "presentation.xml")
    tree = etree.parse(pres)
    root = tree.getroot()
    for lst in root.findall(f"{{{P}}}embeddedFontLst"):
        root.remove(lst)
    root.attrib.pop("embedTrueTypeFonts", None)
    tree.write(pres, xml_declaration=True, encoding="UTF-8", standalone=True)

    rels = os.path.join(work, "ppt", "_rels", "presentation.xml.rels")
    tree = etree.parse(rels)
    root = tree.getroot()
    dropped = 0
    for rel in list(root):
        if rel.get("Type", "").endswith("/font"):
            root.remove(rel)
            dropped += 1
    tree.write(rels, xml_declaration=True, encoding="UTF-8", standalone=True)

    ctp = os.path.join(work, "[Content_Types].xml")
    tree = etree.parse(ctp)
    root = tree.getroot()
    for el in list(root):
        if el.tag == f"{{{CT}}}Default" and (el.get("Extension") or "").lower() == "fntdata":
            root.remove(el)
        elif el.tag == f"{{{CT}}}Override" and "/ppt/fonts/" in (el.get("PartName") or ""):
            root.remove(el)
    tree.write(ctp, xml_declaration=True, encoding="UTF-8", standalone=True)
    return removed, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("font")
    ap.add_argument("--keep-embedded", action="store_true",
                    help="임베딩 폰트를 남긴다(원본 폰트를 계속 쓸 계획일 때)")
    ap.add_argument("--latin-only", action="store_true",
                    help="a:latin 만 교체(한글은 기존 폰트 유지)")
    ap.add_argument("--work", default="_swapfont_work")
    args = ap.parse_args()

    slots = ["latin"] if args.latin_only else ["latin", "ea", "cs"]
    work = args.work
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    with zipfile.ZipFile(args.src) as z:
        order = z.namelist()
        z.extractall(work)

    total = {"parts": 0, "set": 0, "inserted": 0, "theme": 0, "tokens": 0, "runs": 0}

    for dirpath, _, files in os.walk(work):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, work).replace(os.sep, "/")
            if not rel.endswith(".xml"):
                continue
            if not (rel.startswith(TARGET_PREFIX) or rel in TARGET_EXACT):
                continue
            tree = etree.parse(full)
            root = tree.getroot()
            st = fix_charprops(root, args.font, slots)
            total["set"] += st["set"]
            total["inserted"] += st["inserted"]
            if rel.startswith("ppt/theme/"):
                total["theme"] += fix_theme(root, args.font, slots)
            # rPr 자체가 없는 run 에 폰트를 명시 (상속 의존 제거)
            if rel.startswith(("ppt/slides/", "ppt/notesSlides/", "ppt/charts/")):
                for r in root.iter(f"{{{A}}}r"):
                    if r.find(f"{{{A}}}rPr") is None:
                        rpr = etree.Element(f"{{{A}}}rPr")
                        rpr.set("lang", "ko-KR")
                        rpr.set("dirty", "0")
                        for slot in slots:
                            etree.SubElement(rpr, f"{{{A}}}{slot}").set("typeface", args.font)
                        r.insert(0, rpr)
                        total["runs"] += 1
            tree.write(full, xml_declaration=True, encoding="UTF-8", standalone=True)
            total["parts"] += 1

    # 차트 스타일 파트는 cs: 네임스페이스 defRPr 을 쓰므로 위 패스에서 빠진다.
    slot_alt = "|".join(slots)
    tok = re.compile(rf'(<a:(?:{slot_alt})\b[^>]*typeface=")\+m[jn]-(?:lt|ea|cs)(")')
    for dirpath, _, files in os.walk(work):
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            full = os.path.join(dirpath, fn)
            with open(full, encoding="utf-8") as fh:
                txt = fh.read()
            new_txt, cnt = tok.subn(rf"\g<1>{args.font}\g<2>", txt)
            if cnt:
                with open(full, "w", encoding="utf-8") as fh:
                    fh.write(new_txt)
                total["tokens"] += cnt

    removed, dropped = ([], 0)
    if not args.keep_embedded:
        removed, dropped = strip_embedded_fonts(work)
        order = [n for n in order if not n.startswith("ppt/fonts/")]

    if os.path.exists(args.dst):
        os.remove(args.dst)
    with zipfile.ZipFile(args.dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zo:
        for name in order:  # 원본 순서 유지 ([Content_Types].xml 선두)
            path = os.path.join(work, name.replace("/", os.sep))
            if os.path.isfile(path):
                zo.write(path, name)
    shutil.rmtree(work, ignore_errors=True)

    print(f"폰트: '{args.font}' / 슬롯: {', '.join(slots)}")
    print(f"파트 {total['parts']}개 | typeface 설정 {total['set']} / 삽입 {total['inserted']} "
          f"| theme {total['theme']} | 참조토큰 {total['tokens']} | rPr 보강 {total['runs']}")
    if removed:
        print(f"임베딩 폰트 제거: {len(removed)}개, 관계 {dropped}건")
    print(f"출력: {args.dst} ({os.path.getsize(args.dst)/1024/1024:.2f} MB, "
          f"원본 {os.path.getsize(args.src)/1024/1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

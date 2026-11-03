#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check an AWS Korea Tech Blog Markdown draft against references/structure.md.

Usage: python3 check_structure.py <draft.md>
Checks: frontmatter fields, H1 then byline, byline format and category count/order,
lead without heading, numbered H2/H3 depth, table/figure caption placement (below) and numbering,
image files exist relative to the md, 참고 자료 and 저자 소개 present, author bio verbatim.
"""
import io, os, re, sys

BIO_HEAD = "**최우형 (Woohyung Choi)** 님은 AWS Korea의 Principal Solutions Architect로"


def main(path):
    md = io.open(path, encoding="utf-8").read()
    lines = md.splitlines()
    issues = []

    fm = re.match(r"^---\n(.*?)\n---\n", md, flags=re.S)
    if not fm:
        issues.append("frontmatter 없음")
    else:
        for f in ("title:", "date:", "author:", "status: draft"):
            if f not in fm.group(1):
                issues.append(f"frontmatter에 {f} 없음")
    body = md[fm.end():] if fm else md
    blines = body.strip().splitlines()
    if not blines or not blines[0].startswith("# "):
        issues.append("H1이 프론트매터 바로 아래에 없음")
    by = next((l for l in blines if l.startswith("by WOO HYUNG CHOI on ")), None)
    if not by:
        issues.append("바이라인 없음 (by WOO HYUNG CHOI on ...)")
    else:
        if blines.index(by) != 2:
            issues.append("바이라인이 H1 바로 아래(빈 줄 하나)에 있지 않음")
        if not re.search(r"on \d{1,2} \d{1,2}월 \d{4} in ", by):
            issues.append("바이라인 날짜 형식 오류 (예: on 18 9월 2026 in)")
        cats = re.findall(r"\[([^\]]+)\]\((https://aws\.amazon\.com/ko/blogs/tech/category/[^)]+)\)", by)
        if not (2 <= len(cats) <= 4):
            issues.append(f"카테고리 수 {len(cats)} (2~4개 필요)")
        names = [c[0] for c in cats]
        if names != sorted(names, key=str.lower):
            issues.append(f"카테고리 알파벳순 아님: {names}")
        bad = [c[1] for c in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", by) if "/ko/blogs/tech/category/" not in c[1]]
        if bad:
            issues.append(f"tech 카테고리 경로가 아님: {bad}")
    # lead: first non-empty line after byline must not be a heading
    if by:
        i = blines.index(by) + 1
        while i < len(blines) and not blines[i].strip():
            i += 1
        if i < len(blines) and blines[i].startswith("#"):
            issues.append("리드 문단이 없음 (바이라인 뒤 바로 헤딩)")
    # headings
    h2 = [l for l in lines if l.startswith("## ")]
    nums = [l for l in h2 if re.match(r"## \d+\. ", l)]
    if not nums:
        issues.append("번호 매긴 H2(## 1. ...) 없음")
    for l in lines:
        if l.startswith("#### "):
            issues.append(f"H4 사용 금지: {l[:40]}")
        if l.startswith("### ") and not re.match(r"### \d+\.\d+ ", l):
            issues.append(f"H3 형식(### 1.1 ...) 아님: {l[:40]}")
    for h in ("## 마치며", "## 참고 자료", "## 저자 소개"):
        if not any(l.strip().endswith(h.replace("## ", "")) and l.startswith("## ") for l in lines):
            issues.append(f"{h} 섹션 없음")
    # captions
    tbl_caps, fig_caps = [], []
    for i, l in enumerate(lines):
        m = re.match(r"\*표 (\d+)\.", l)
        if m:
            tbl_caps.append(int(m.group(1)))
            prev = next((lines[j] for j in range(i - 1, -1, -1) if lines[j].strip()), "")
            if not prev.startswith("|"):
                issues.append(f"표 {m.group(1)} 캡션이 표 바로 아래에 없음")
        m = re.match(r"\*그림 (\d+)\.", l)
        if m:
            fig_caps.append(int(m.group(1)))
            prev = next((lines[j] for j in range(i - 1, -1, -1) if lines[j].strip()), "")
            if not prev.startswith("!["):
                issues.append(f"그림 {m.group(1)} 캡션이 이미지 바로 아래에 없음")
    for name, caps in (("표", tbl_caps), ("그림", fig_caps)):
        if caps != list(range(1, len(caps) + 1)):
            issues.append(f"{name} 번호 불연속: {caps}")
    # tables without caption
    n_tables = sum(1 for i, l in enumerate(lines) if l.startswith("|") and (i == 0 or not lines[i - 1].startswith("|")))
    if n_tables != len(tbl_caps):
        issues.append(f"표 {n_tables}개 vs 캡션 {len(tbl_caps)}개")
    # images
    base = os.path.dirname(os.path.abspath(path))
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
    if len(imgs) != len(fig_caps):
        issues.append(f"이미지 {len(imgs)}개 vs 그림 캡션 {len(fig_caps)}개")
    for p in imgs:
        if not p.startswith("images/"):
            issues.append(f"이미지 경로가 images/ 상대 경로가 아님: {p}")
        if not os.path.exists(os.path.join(base, p)):
            issues.append(f"이미지 파일 없음: {p}")
        for alt in re.findall(r"!\[([^\]]*)\]\(" + re.escape(p) + r"\)", md):
            if len(alt) < 20:
                issues.append(f"alt 텍스트가 짧음: {p}")
    if BIO_HEAD not in md:
        issues.append("저자 소개 원문 첫 문장 불일치")
    # references section: every link https
    ref = md.split("## 참고 자료")[-1].split("## 저자 소개")[0] if "## 참고 자료" in md else ""
    for u in re.findall(r"\]\(([^)]+)\)", ref):
        if not u.startswith("https://"):
            issues.append(f"참고 자료 URL 형식: {u}")
    print(f"== {path}")
    if issues:
        for i in issues:
            print("  [!]", i)
        return 1
    print("  OK: structure checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sweep an AWS Korea Tech Blog Markdown draft for prohibited words and AI-tell patterns.

Usage: python3 lint_prose.py <draft.md>
Exit code 1 when a hard-prohibited term or a sentence over 140 characters is found (so it can gate packaging).
The term lists mirror references/style.md and humanize-checklist.md; when a rule is added there, add it here too.
Tables, code blocks, image lines, frontmatter and the author bio are excluded from the sweep;
the title (H1/frontmatter) is excluded from the dash check only.
"""
import io, re, sys

HARD = [  # term, replacement hint
    ("레버", "해법"),
    ("돌린다", "실행한다"), ("돌립니다", "실행합니다"), ("돌아가", "실행되"),
    ("·", "쉼표나 와, 과, 및 (다이어그램 텍스트만 슬래시)"),
    ("—", "하이픈/쉼표/문장 분리"), ("–", "하이픈/쉼표/문장 분리 (제목 제외)"),
    ("낭비 절감", "비용 절감"),
    ("붙는다", "과금됩니다/부과됩니다"), ("붙습니다", "과금됩니다/부과됩니다"),
    ("암시적 캐싱", "묵시적 캐싱(Implicit Prompt Caching)"),
    ("미국 본토", "미국 리전"),
    ("문서가 짚는", "직접 서술"), ("문서가 안내합니다", "직접 서술"),
    ("다음과 같습니다", "도입구 삭제"), ("크게 세 가지", "도입구 삭제"),
    ("하세요", "~하는 것을 권고합니다"),
    ("쓸 수 있", "사용할 수 있"), ("씁니다", "사용합니다"), ("쓰면", "사용하면"),
    ("4쪽", "내용 지칭"), ("앞서 ", "내용 지칭 (섹션 번호 참조 여부 확인)"),
]

# 예외가 있어 정규식으로 잡는 HARD 규칙
HARD_RE = [
    (r"계약", "요구 사항, 조건, 기준 (contract 직역, 2026-10-24 확정)"),
    (r"(?<![압구단])축(?![소적])", "방식, 기준 (axis 직역, 2026-10-24 확정). 축소, 압축, 구축, 단축, 축적은 제외"),
    # 절은 항상 위치 참조, 장은 조사가 붙어 위치를 가리킬 때만 참조로 본다("슬라이드 12장을 만들었습니다"는 개수)
    (r"\d+(?:\.\d+)*절|\d+장(?=의|에서|에 )", "섹션 번호 참조 금지, 내용으로 지칭 (2026-10-28 확정)"),
]

SENT_WARN, SENT_HARD = 120, 140  # 2026-11-01 확정: 120자 초과는 분리 검토, 140자 초과는 반드시 분리

COUNT = [  # pattern, threshold, note
    (r"를 통해|을 통해", 3, "번역투 A-2"),
    (r"에 대해", 2, "번역투 A-1"),
    (r"할 수 있습니다", 4, "A-10 단언으로"),
    (r"^(또한|따라서|즉|나아가|아울러|게다가|더욱이)[ ,]", 5, "문두 접속사 H-1"),
    (r"결론적으로|요약하면|정리하자면|이를 통해", 3, "결산 lexicon D-1"),
    (r"시사하는 바|주목할 만|매우 중요", 1, "의의 과장 D-2"),
    (r"혁신적|획기적|압도적|파격적|폭발적|전례 없는", 1, "hype D-4"),
    (r"가 아니라 ", 2, "대구 C-8"),
    (r"\*\*[^*]+\*\*", 3, "본문 볼드 J-1 (저자 소개 제외)"),
    (r"가지고 있", 1, "A-7"),
    (r"되어진|지게 된", 1, "이중 피동 A-8"),
    (r"에 의해", 1, "A-9"),
    (r"것입니다", 3, "형식명사 I-3"),
    # 2026-11-01 추가 (kor-deslop 기준)
    (r"에 있어(서)?", 0, "번역투 A-3"),
    (r"라는 점에서|와 관련하여|과 관련하여|에 기반하여|을 바탕으로|를 바탕으로", 2, "번역투 A-4~A-6"),
    (r"을 위해|를 위해", 3, "목적절 A-11"),
    (r"이루어[지집졌]|만들어[지집졌]", 2, "자동 피동 A-12"),
    (r"^그리고[ ,]", 1, "문두 그리고 A-14"),
    (r"에서의|에로의|으로의|으로부터의|로부터의", 1, "이중 조사 A-19"),
    (r"(?i)\b(seamless|robust|leverage)\b", 0, "광고성 영어 B-2"),
    (r"라고 알려진|로 일컬어지는", 0, "B-4"),
    (r"이 (섹션|절|장)에서는", 0, "헤딩 아래 안내문 C-6"),
    (r"^\d\) ", 0, "괄호 번호 C-9"),
    (r"을 넘어 |를 넘어 ", 1, "변환 공식 D-7"),
    (r"매우 |정말 |대단히 |극히 ", 3, "정도부사 F-1"),
    (r"작업을 진행|을 진행했|를 진행했|을 진행합|를 진행합", 1, "명사화 F-4"),
    (r"양쪽 모두|장점도 있지만|신중하게|균형", 4, "균형 어휘 G-3"),
    (r"^(하지만|그러나)[ ,]", 3, "역접 H-2"),
    (r"^이는 |^이 점에서", 3, "지시 반복 H-3"),
    (r"이 필요합니다|가 필요합니다", 2, "I-5 주어와 동사로"),
    (r"능력", 2, "I-6"),
]


def body_text(md):
    md = re.sub(r"^---.*?---\n", "", md, flags=re.S)
    md = md.split("## 저자 소개")[0]
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    lines = [l for l in md.splitlines() if not l.startswith("|") and not l.startswith("![")]
    return "\n".join(lines)


def prose_only(body):
    """Drop headings, captions, byline and reference-list links for sentence-level checks."""
    keep = []
    for l in body.splitlines():
        if l.startswith("#") or l.startswith("*표 ") or l.startswith("*그림 ") or l.startswith("by WOO") or l.startswith("- ["):
            continue
        keep.append(l)
    return "\n".join(keep)


def main(path):
    md = io.open(path, encoding="utf-8").read()
    body = body_text(md)
    body_no_title = prose_only(body)
    bad = 0
    print(f"== {path}")
    for term, hint in HARD:
        src = body_no_title if term in ("—", "–") else body
        n = src.count(term)
        if n:
            bad += 1
            print(f"  [HARD] {term!r} ×{n} → {hint}")
            for m in re.finditer(re.escape(term), src):
                ctx = src[max(0, m.start()-30): m.end()+30].replace("\n", " ")
                print(f"         …{ctx}…")
    for pat, hint in HARD_RE:
        ms = list(re.finditer(pat, body_no_title))
        if ms:
            bad += 1
            print(f"  [HARD] /{pat}/ ×{len(ms)} → {hint}")
            for m in ms:
                ctx = body_no_title[max(0, m.start()-30): m.end()+30].replace("\n", " ")
                print(f"         …{ctx}…")
    for pat, th, note in COUNT:
        n = len(re.findall(pat, body, flags=re.M))
        flag = "!" if n > th else " "
        if n:
            print(f"  [{flag}] {pat} ×{n} (임계 {th}) {note}")
    # long sentences: 줄(문단, 불릿) 단위로 나눈 뒤 문장 부호로 자른다. 링크는 표시 텍스트, 인라인 코드는 내용만 센다
    sents = []
    for line in prose_only(body).splitlines():
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).replace("`", "").strip()
        sents += [x.strip() for x in re.split(r"(?<=[.?!])\s+", line) if x.strip()]
    hard_long = [x for x in sents if len(x) > SENT_HARD]
    warn_long = [x for x in sents if SENT_WARN < len(x) <= SENT_HARD]
    if hard_long:
        bad += 1
        print(f"  [HARD] {SENT_HARD}자 초과 문장 {len(hard_long)}개 → 반드시 분리 (style.md 문장 원칙)")
        for x in hard_long:
            print(f"      ({len(x)}자) {x[:90]}…")
    if warn_long:
        print(f"  [!] {SENT_WARN}자 초과 문장 {len(warn_long)}개 → 분리 검토")
        for x in warn_long:
            print(f"      ({len(x)}자) {x[:90]}…")
    print(f"  chars={len(md)}  hard_findings={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

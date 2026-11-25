#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure repetition and filler in an AWS Korea Tech Blog Markdown draft (criterion 4 of the pre-check).

Usage: python3 redundancy_metrics.py <draft.md> [--restated N]
Prints a Markdown score table to stdout; paste it into gate-report.md. The score is 0 to 100 and a higher score
means fewer things that get in the reader's way. It does not judge whether the text was written by AI.
--restated N subtracts 5 points for each restatement counted by hand (the same point made again in other words),
which the script cannot see, and prints the score of criterion 4. Exit code 0 when measured, 2 on a usage error.

The six measures, their limits and their weights follow redundancy_metrics.py of
github.com/comeddy/blog-precheck-plugin (MIT, Copyright (c) 2026 Youngjin Kim; the license text is
third_party/LICENSE-blog-precheck in the my-plugins repository). This version reads the draft the way
lint_prose.py does: frontmatter, code blocks, tables, image lines, captions, the byline, the reference list and
the author bio are not prose. It reads Markdown only and takes the hand-counted restatements as an argument.
A sentence that resembles several earlier ones counts once, like a sentence that is repeated word for word.
"""
import argparse, collections, io, os, re, sys

META = r"핵심|중요한 점은|주목할|요컨대|결론적으로|바로 이것|이 한 문장"
# not inside another word: 아쉽게도, 부적절한 and 비효율적으로 are other words
FILLER = r"(?<![가-힣])(?:다양한|효과적으로|효율적으로|원활하게|적절한|적절히|성공적으로|쉽게|간단히|보다 나은|더욱|매우|상당히)"
MINIMUM = 60          # references/precheck.md, criterion 4
RESTATED_POINTS = 5   # per restatement counted by hand
GRAM, GRAM_HANGUL = 20, 12  # two sentences are alike when they share 20 characters of which 12 are Hangul


def plain(text):
    """Markdown inline markup removed: link text only, no code ticks, no emphasis marks, no HTML tags."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"</?[A-Za-z][^<>]*>", "", text)  # tags only: "< 100 ms" and "> 1,000" are prose
    text = text.replace("`", "")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def blocks(md):
    """(kind, text) pairs of the prose: kind is "h" (heading), "li" (list item) or "p" (paragraph)."""
    md = md.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    md = md.split("\n## 저자 소개")[0]
    md = re.sub(r"\n## 참고 자료\n.*?(?=\n## |\Z)", "\n", md, flags=re.S)
    out, para, fence = [], [], None

    def flush():
        if para:
            text = plain(" ".join(para))
            if text:
                out.append(("p", text))
            del para[:]

    for line in md.split("\n"):
        s = line.strip()
        if fence:  # closed by a line of the same marks only, at least as long
            if len(s) >= len(fence) and set(s) == set(fence[0]):
                fence = None
            continue
        m = re.match(r"(`{3,}|~{3,})(.*)", s)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            flush()
            fence = m.group(1)
            continue
        if not s:
            flush()
            continue
        if s.startswith("|") or s.startswith("![") or re.match(r"\*(표|그림) \d+\.", s) or re.match(r"by .+ on \d", s):
            flush()
            continue
        if re.match(r"([-*_])(\s*\1){2,}$", s):
            flush()
            continue
        m = re.match(r"#{1,6}\s+(.*)", s)
        if m:
            flush()
            out.append(("h", plain(m.group(1))))
            continue
        m = re.match(r"(?:[-*+]|\d+[.)])\s+(.*)", s)
        if m:
            flush()
            out.append(("li", plain(m.group(1))))
            continue
        if s.startswith(">"):
            s = s.lstrip("> ")
        para.append(s)
    flush()
    return out


def sentences(text):
    # a sentence may end inside a bracket or a quotation: "(셋째 문장입니다.) 넷째 ..."
    return [s.strip() for s in re.split(r"(?<=[.?!])[)\]\"”’']*\s+", text) if len(s.strip()) > 3]


def measure(md):
    """(rows, samples, score): rows are (name, value, limit, penalty), samples are (kind, text)."""
    prose = [(k, t) for k, t in blocks(md) if k != "h"]
    text = "\n".join(t for _, t in prose)
    chars = max(len(text), 1)
    rows, samples = [], []

    # 1. the same paragraph in more than one place (a notice repeated in every chapter)
    paras = collections.Counter(t for k, t in prose if k == "p" and len(t) >= 10)
    boiler = [t for t, c in paras.items() if c > 1]
    repeated = sum(c - 1 for c in paras.values() if c > 1)
    rows.append(("보일러플레이트 문단 반복", "%d회" % repeated, "0", min(20, repeated * 6)))
    samples += [("보일러플레이트", t) for t in boiler]

    # 2. the same sentence again, or two sentences that share a long Korean phrase
    counted = set(s for t in boiler for s in sentences(t))  # already counted under 1
    cand = [s for _, t in prose for s in sentences(t) if len(s) >= 15 and s not in counted]
    sents = collections.Counter(cand)
    exact = sum(c - 1 for c in sents.values() if c > 1)
    uniq = list(sents)

    def grams(s):
        return set(s[i:i + GRAM] for i in range(len(s) - GRAM + 1)
                   if len(re.findall(r"[가-힣]", s[i:i + GRAM])) >= GRAM_HANGUL)

    seen = [grams(s) for s in uniq]
    near = []
    for j in range(1, len(uniq)):  # each sentence once, however many earlier ones it resembles
        for i in range(j):
            shared = seen[i] & seen[j]
            if shared:
                near.append((uniq[i], uniq[j], sorted(shared)[0]))
                break
    rows.append(("문장 반복 (동일 또는 한글 공통 구절 %d자)" % GRAM, "동일 %d, 유사 %d" % (exact, len(near)), "0",
                 min(25, (exact + len(near)) * 8)))
    samples += [("반복 문장", s) for s, c in sents.items() if c > 1]
    samples += [("유사 문장", "'%s' ← %s… / %s…" % (g, a[:25], b[:25])) for a, b, g in near]

    # 3. sentences that say something matters instead of showing it
    all_sents = [s for _, t in prose for s in sentences(t)]
    meta = [s for s in all_sents if re.search(META, s)]
    rows.append(("메타 강조 문장", "%d회" % len(meta), "≤ 1", min(15, max(0, len(meta) - 1) * 5)))
    samples += [("메타 문장", s) for s in meta]

    # 4. a plain noun phrase in quotation marks, used as if it were a term
    # pair the marks in order first, so the text between two quotations is not read as a third one
    quotes = re.findall(r"[\"“]([^\"”\n]*)[\"”]", text)
    coined = [q for q in quotes if 2 <= len(q) <= 40 and not re.search(r"[A-Za-z_]{3,}|\d", q)]
    density = len(coined) / chars * 1000
    rows.append(("따옴표 조어 밀도 (1000자당)", "%.1f (%d회)" % (density, len(coined)), "≤ 1.0",
                 min(12, int(max(0, density - 1.0) * 5))))
    samples += [("따옴표 조어", q) for q in coined]

    # 5. paragraphs of six sentences or more
    long_paras = [t for k, t in prose if k == "p" and len(sentences(t)) >= 6]
    rows.append(("6문장 이상 문단", "%d개" % len(long_paras), "0", min(15, len(long_paras) * 5)))
    samples += [("긴 문단", t[:50] + "…") for t in long_paras]

    # 6. stock words that add no meaning
    fillers = re.findall(FILLER, text)
    density = len(fillers) / chars * 1000
    rows.append(("상투어 밀도 (1000자당)", "%.1f (%d회)" % (density, len(fillers)), "≤ 1.5",
                 min(13, int(max(0, density - 1.5) * 4))))
    if fillers:
        top = collections.Counter(fillers).most_common(6)
        samples.append(("상투어", ", ".join("%s×%d" % (w, c) for w, c in top)))

    return rows, samples, max(0, 100 - sum(r[3] for r in rows))


def main(argv):
    ap = argparse.ArgumentParser(description="Repetition and filler metrics of a Markdown blog draft.")
    ap.add_argument("draft")
    ap.add_argument("--restated", type=int, metavar="N",
                    help="restatements counted by hand; 5 points each are subtracted")
    args = ap.parse_args(argv)
    if not args.draft.lower().endswith(".md") or not os.path.isfile(args.draft):
        ap.error("a Markdown draft (.md) is needed: %s" % args.draft)
    if args.restated is not None and args.restated < 0:
        ap.error("--restated takes 0 or more")
    rows, samples, score = measure(io.open(args.draft, encoding="utf-8-sig", newline="").read())

    print("## 중복과 군더더기 지표: %s\n" % os.path.basename(args.draft))
    print("**점수: %d/100** (높을수록 읽기에 방해되는 요소가 적음, 최저선 %d)\n" % (score, MINIMUM))
    print("| 지표 | 측정값 | 기준 | 감점 |\n|---|---|---|---|")
    for name, value, limit, penalty in rows:
        print("| %s | %s | %s | -%d |" % (name, value, limit, penalty))
    print("\n### 근거 샘플")
    by_kind = collections.OrderedDict()
    for kind, text in samples:
        by_kind.setdefault(kind, []).append(text)
    if not by_kind:
        print("- 없음")
    for kind, texts in by_kind.items():
        print("- %s: %s" % (kind, "; ".join(t[:90] for t in texts[:8])))
    print()
    if args.restated is None:
        print("재진술 미집계: 같은 뜻을 다른 문장으로 되풀이한 곳은 스크립트가 잡지 못한다. 섹션마다 핵심 메시지를 한 줄씩 "
              "적어 겹치는 것을 센 뒤 `--restated <건수>`로 다시 실행한다(재진술 1건당 -%d)." % RESTATED_POINTS)
    else:
        final = max(0, score - RESTATED_POINTS * args.restated)
        print("재진술 %d건: -%d" % (args.restated, RESTATED_POINTS * args.restated))
        print("\n**기준 4 점수: %d/100**" % final)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

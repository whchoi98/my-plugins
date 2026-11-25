#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that gate-report.md (the pre-check report) is complete and that its verdict follows from its scores.

Usage: python3 check_gate.py <gate-report.md> [--draft <draft.md>]
Recomputes the total and the verdict from the six scores and compares them with what the report states. A score
has to be one the scoring rules can give, a judged score needs a quoted sentence, a lost point needs the original
and the corrected text, and the score of criterion 4 has to follow from the pasted output of
redundancy_metrics.py. With --draft the metrics are measured again on that draft, so a report that was written
for another draft, or before the draft changed, is refused. A consistent report is printed back as its score
table, which package_blog.sh repeats for the last response of the session.
Exit code 0: the report is consistent and the draft may be handed over (통과, or 2회 초과 전달 after round 2).
Exit code 3: the report is consistent and the verdict is 반려 (correct the criteria below their minimum, score again).
Exit code 1: the report is incomplete or states something its scores do not support. Exit code 2: usage.

The criteria, minimums and report layout are in references/precheck.md; keep CRITERIA and PASS_TOTAL the same
there. The layout is the one gate.md of github.com/comeddy/blog-precheck-plugin (MIT) defines, so a reviewer's
tool that reads that file reads this one too.
"""
import importlib.util, io, os, re, sys

CRITERIA = [  # name, minimum
    ("정합성", 80),
    ("구조 완결성", 70),
    ("표기 규범", 70),
    ("중복과 군더더기", 60),
    ("차별성과 근거", 60),
    ("가독성", 60),
]
PASS_TOTAL = 70
MAX_ROUND = 2
JUDGED = ("구조 완결성", "차별성과 근거", "가독성")  # scored by judgement: a quoted sentence is required
COMPARED_POSTS = 3  # criterion 5 is scored after this many posts on the same topic were looked at
RESTATED_POINTS = 5
PASS, REJECT, HANDOVER = "통과", "반려", "2회 초과 전달"
ALLOWED = {  # the scores the rules of references/precheck.md can give
    "정합성": set(range(0, 101, 10)),                                                 # 10 off per finding
    "구조 완결성": set(k * 100 // n for n in (6, 7) for k in range(n + 1)),             # items met of 7, or of 6
    "표기 규범": set(range(0, 101, 10)),                                              # 10 off per finding
    "차별성과 근거": set(a + b + c for a in (0, 40) for b in (0, 40) for c in (0, 20)),  # 40 + 40 + 20
    "가독성": set(a + b + c for a in (0, 40) for b in (0, 30) for c in (0, 30)),        # 40 + 30 + 30
}


def section(md, heading):
    """Text of a "## heading" section (the heading may carry a suffix), or None."""
    m = re.search(r"^## %s[^\n]*\n(.*?)(?=^## |\Z)" % re.escape(heading), md, flags=re.M | re.S)
    return m.group(1) if m else None


def subsections(text):
    """{"### title": body} of a section."""
    out = {}
    for m in re.finditer(r"^### ([^\n]+)\n(.*?)(?=^### |\Z)", text or "", flags=re.M | re.S):
        out[m.group(1).strip()] = m.group(2)
    return out


def measured(draft):
    """(score, file name) from redundancy_metrics.py, which sits next to this file."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redundancy_metrics.py")
    sys.dont_write_bytecode = True  # the skill folder is the plugin cache: no __pycache__ there
    spec = importlib.util.spec_from_file_location("redundancy_metrics", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text = io.open(draft, encoding="utf-8-sig", newline="").read()
    return module.measure(text)[2], os.path.basename(draft)


def score_table(scores, total, verdict, below):
    """The six scores and the total as the table the session shows to the user."""
    lines = ["| 기준 | 점수 | 최저선 | 판정 |", "|---|---|---|---|"]
    for name, minimum in CRITERIA:
        lines.append("| %s | %d | %d | %s |" % (name, scores[name], minimum, PASS if scores[name] >= minimum else "미달"))
    note = " (%s 미달)" % ", ".join(below) if below else ""
    lines.append("| **총점** | %d | %d | **%s%s** |" % (total, PASS_TOTAL, verdict, note))
    return lines


def check(md, draft=None):
    """(issues, verdict, table): verdict and table are None when the scores could not be read."""
    md = md.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    issues = []
    if not re.search(r"^# Gate Report: \S", md, flags=re.M):
        issues.append("첫 줄 '# Gate Report: <블로그 제목>' 없음")
    m = re.search(r"^회차: (\d+) / %d \| 판정: (.+?)\s*$" % MAX_ROUND, md, flags=re.M)
    rnd, stated = (int(m.group(1)), m.group(2)) if m else (None, None)
    if not m:
        issues.append("'회차: N / %d | 판정: …' 줄 없음" % MAX_ROUND)
    elif not 1 <= rnd <= MAX_ROUND:
        issues.append("회차 %d: 1 또는 %d만 가능 (재채점은 한 번)" % (rnd, MAX_ROUND))
    if rnd == MAX_ROUND and not re.search(r"^이전 회차", md, flags=re.M):
        issues.append("%d회차 리포트에 '이전 회차: …' 줄(앞 회차 점수) 없음" % MAX_ROUND)

    scores = {}
    for name, minimum in CRITERIA:
        row = re.search(r"^\| *%s *\| *(\d+) *\| *(\d+) *\| *([^|]+?) *\|" % re.escape(name), md, flags=re.M)
        if not row:
            issues.append("점수표에 '%s' 행 없음" % name)
            continue
        score, stated_min, mark = int(row.group(1)), int(row.group(2)), row.group(3).strip("* ")
        if score > 100:
            issues.append("%s 점수 %d: 0~100" % (name, score))
        elif name in ALLOWED and score not in ALLOWED[name]:
            issues.append("%s 점수 %d: 채점 규칙으로 나올 수 없는 값 (나올 수 있는 값: %s)"
                          % (name, score, ", ".join(str(v) for v in sorted(ALLOWED[name]))))
        if stated_min != minimum:
            issues.append("%s 최저선 %d: %d이어야 함" % (name, stated_min, minimum))
        want = PASS if score >= minimum else "미달"
        if mark != want:
            issues.append("%s 판정 '%s': 점수 %d, 최저선 %d이면 '%s'" % (name, mark, score, minimum, want))
        scores[name] = score
    if len(scores) != len(CRITERIA):
        return issues, None, None

    total = sum(scores.values()) // len(CRITERIA)
    below = [n for n, minimum in CRITERIA if scores[n] < minimum]
    if total >= PASS_TOTAL and not below:
        verdict = PASS
    else:
        verdict = HANDOVER if rnd == MAX_ROUND else REJECT
    table = ["%s회차, 총점 %d" % (rnd, total)] + score_table(scores, total, verdict, below)
    row = re.search(r"^\| *\**총점\** *\| *(\d+) *\| *(\d+) *\| *([^|]+?) *\|", md, flags=re.M)
    if not row:
        issues.append("점수표에 '**총점**' 행 없음")
    else:
        cell = row.group(3).strip("* ")
        if int(row.group(1)) != total:
            issues.append("총점 %s: 여섯 점수의 평균(소수점 아래 버림)은 %d" % (row.group(1), total))
        if int(row.group(2)) != PASS_TOTAL:
            issues.append("총점 최저선 %s: %d이어야 함" % (row.group(2), PASS_TOTAL))
        if not cell.startswith(verdict):
            issues.append("총점 행 판정 '%s': 점수로는 '%s'" % (cell, verdict))
        named = [n for n, _ in CRITERIA if n in cell and n not in below]
        if named:
            issues.append("총점 행에 적은 '%s': 최저선에 못 미친 기준이 아님" % ", ".join(named))
    if stated is not None and stated != verdict:
        why = "미달: %s" % ", ".join(below) if below else "총점 %d" % total
        issues.append("판정 '%s': 점수로는 '%s' (%s)" % (stated, verdict, why))

    # scores given by judgement need a quoted sentence
    basis = subsections(section(md, "채점 근거"))
    for name in JUDGED:
        if not re.search(r"^> *\S", basis.get(name, ""), flags=re.M):
            issues.append("'## 채점 근거'의 '### %s'에 근거 문장 인용(> …) 없음: 근거 없는 점수는 무효" % name)
    compared = set(re.findall(r"https?://[^\s<>()]+", basis.get("차별성과 근거", "")))
    if len(compared) < COMPARED_POSTS:
        issues.append("'### 차별성과 근거'에 비교한 글의 URL %d개: 같은 주제의 글 %d개 이상을 확인하고 URL을 적는다"
                      % (len(compared), COMPARED_POSTS))

    # every lost point is a pair: the quoted original and the corrected text
    reasons = subsections(section(md, "감점 사유"))
    for name, _ in CRITERIA:
        if scores[name] == 100:
            continue
        title = "%s (%d)" % (name, scores[name])
        body = reasons.get(title)
        if body is None:
            issues.append("'## 감점 사유'에 '### %s' 없음 (제목의 점수는 점수표와 같아야 함)" % title)
        elif not re.search(r"^> *\S", body, flags=re.M) or not re.search(r"^→ *\S", body, flags=re.M):
            issues.append("'### %s': 원문 인용(> …)과 수정안(→ …) 쌍 없음" % title)

    # criterion 4 is the script's number, not an estimate. The pasted output has a "## " heading of its own,
    # so this section runs to the end of the report
    parts = re.split(r"^## 중복과 군더더기 지표 원본[^\n]*\n", md, maxsplit=1, flags=re.M)
    raw = parts[1] if len(parts) == 2 else None
    if raw is None or "| 지표 | 측정값 | 기준 | 감점 |" not in raw:
        issues.append("'## 중복과 군더더기 지표 원본'에 redundancy_metrics.py 출력 없음")
        return issues, verdict, table
    script = re.search(r"\*\*점수: (\d+)/100\*\*", raw)
    final = re.search(r"기준 4 점수: (\d+)/100", raw)
    restated = re.search(r"^재진술 (\d+)건", raw, flags=re.M)
    penalties = [int(v) for v in re.findall(r"^\|[^\n]*\| *-(\d+) *\|$", raw, flags=re.M)]
    if not script or not penalties:
        issues.append("지표 원본에 '**점수: N/100**'과 감점 표가 없음: 스크립트 출력을 줄이지 않고 붙인다")
    elif int(script.group(1)) != max(0, 100 - sum(penalties)):
        issues.append("지표 원본의 점수 %s: 표의 감점을 100에서 빼면 %d" % (script.group(1), max(0, 100 - sum(penalties))))
    if not final or not restated:
        issues.append("지표 원본에 '기준 4 점수'가 없음: redundancy_metrics.py를 --restated <건수>로 실행한 출력을 붙인다")
    else:
        if script and int(final.group(1)) != max(0, int(script.group(1)) - RESTATED_POINTS * int(restated.group(1))):
            issues.append("기준 4 점수 %s: 점수 %s에서 재진술 %s건(1건 %d점)을 빼면 %d" % (
                final.group(1), script.group(1), restated.group(1), RESTATED_POINTS,
                max(0, int(script.group(1)) - RESTATED_POINTS * int(restated.group(1)))))
        if int(final.group(1)) != scores["중복과 군더더기"]:
            issues.append("중복과 군더더기 %d: 스크립트의 기준 4 점수는 %s" % (scores["중복과 군더더기"], final.group(1)))

    # the report belongs to this draft: same file name, same measured score
    if draft and script:
        now, name = measured(draft)
        header = re.search(r"^## 중복과 군더더기 지표: (.+?)\s*$", raw, flags=re.M)
        if not header or header.group(1) != name:
            issues.append("지표 원본은 '%s'의 것: 이 원고는 '%s'" % (header.group(1) if header else "?", name))
        elif now != int(script.group(1)):
            issues.append("지표 원본의 점수 %s: 지금 원고를 재면 %d. 원고를 수정했으면 redundancy_metrics.py를 다시 실행해 "
                          "리포트를 갱신한다" % (script.group(1), now))
    return issues, verdict, table


def main(argv):
    draft = None
    if "--draft" in argv:
        k = argv.index("--draft")
        draft = argv[k + 1] if k + 1 < len(argv) else ""
        argv = argv[:k] + argv[k + 2:]
    if len(argv) != 1 or draft == "":
        print(__doc__.strip().splitlines()[2])
        return 2
    try:
        md = io.open(argv[0], encoding="utf-8-sig", newline="").read()
    except (IOError, OSError) as exc:
        print("gate report not readable: %s" % exc)
        return 2
    if draft and not os.path.isfile(draft):
        print("draft not found: %s" % draft)
        return 2
    issues, verdict, table = check(md, draft)
    print("== %s" % argv[0])
    if issues:
        for issue in issues:
            print("  [!] %s" % issue)
        print("  gate report: %d problem(s)" % len(issues))
        return 1
    print("  OK: 판정 %s (%s)" % (verdict, table[0]))
    for line in table[1:]:
        print("  %s" % line)
    if verdict == REJECT:
        print("  반려: 최저선에 못 미친 기준(없으면 점수가 가장 낮은 기준)의 감점 사유만 수정한 뒤 다시 채점한다 "
              "(references/precheck.md)")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/bin/bash
# Behavior of the scripts aws-blog-skills ships (sourced by tests/run-all.sh; filter: scripts).
# Everything runs on fixtures in $TEST_TMP; nothing is written under skills/.
# Pre-check: redundancy_metrics.py (criterion 4), check_gate.py (the report's arithmetic and evidence),
# md_to_wordpress.py (HTML for the WordPress code editor) and package_blog.sh, which runs the last two.

SCR=skills/aws-blog-skills/scripts
SCR_SLUG=2026-01-01-fixture
SCR_W="$TEST_TMP/$SCR_SLUG"
mkdir -p "$SCR_W"/{drafts,images,out}
ln -sfn ../images "$SCR_W/drafts/images"

# A minimal draft that satisfies references/structure.md and style.md
scr_write_draft() {
    cat > "$1" <<'EOF'
---
title: "샘플 원고 – Amazon VPC 구성 점검"
date: 2026-01-01
author: "Woohyung Choi"
status: draft
---

# 샘플 원고 – Amazon VPC 구성 점검

by WOO HYUNG CHOI on 1 1월 2026 in [Best Practices](https://aws.amazon.com/ko/blogs/tech/category/post-types/best-practices/), [Intermediate (200)](https://aws.amazon.com/ko/blogs/tech/category/learning-levels/intermediate-200/)

이 원고는 하네스 테스트용 샘플입니다. 이 글은 VPC를 운영하는 엔지니어를 대상으로 하며, 서브넷의 기본 개념을 알고 있다면 무리 없이 읽을 수 있습니다.

## 1. 구성 개요

샘플 구성은 서브넷 두 개로 시작합니다.

| 항목 | 값 |
|---|---|
| 서브넷 수 | 2개 |

*표 1. 샘플 구성 항목(단위: 개)*

![서울 리전 VPC가 Direct Connect Gateway를 거쳐 온프레미스 라우터로 연결되는 기존 구성](images/fixture-fig01-arch.png)

*그림 1. 샘플 아키텍처*

## 2. 마치며

이 글의 표가 여러분의 VPC 검토에 실질적인 참고가 되기를 바랍니다.

## 참고 자료

- [What is Amazon VPC? – User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)

## 저자 소개

**최우형 (Woohyung Choi)** 님은 AWS Korea의 Principal Solutions Architect로, 국내 주요 엔터프라이즈 및 디지털 기업의 클라우드 전환과 아키텍처 현대화를 지원하고 있습니다.
EOF
}
SCR_MD="$SCR_W/drafts/$SCR_SLUG.md"
scr_write_draft "$SCR_MD"
# A gate report whose six scores are $2..$7 (default 100 each), round $8 (default 1). The total, the row marks and
# the verdict are worked out here the way references/precheck.md says, so check_gate.py is tested against the
# rule and not against itself. The raw metrics are the script's own output for the draft.
scr_write_gate() {
    local out="$1" names=("정합성" "구조 완결성" "표기 규범" "중복과 군더더기" "차별성과 근거" "가독성") mins=(80 70 70 60 60 60)
    local scores=("${2:-100}" "${3:-100}" "${4:-100}" "${5:-100}" "${6:-100}" "${7:-100}") round="${8:-1}"
    local sum=0 below=0 k verdict
    for k in 0 1 2 3 4 5; do sum=$((sum + scores[k])); [ "${scores[k]}" -lt "${mins[k]}" ] && below=1; done
    local total=$((sum / 6))
    if [ "$below" = 0 ] && [ "$total" -ge 70 ]; then verdict="통과"; elif [ "$round" = 2 ]; then verdict="2회 초과 전달"; else verdict="반려"; fi
    {
        echo "# Gate Report: 샘플 원고"
        echo "회차: $round / 2 | 판정: $verdict"
        [ "$round" = 2 ] && echo "이전 회차: 1회차 총점 60, 가독성 30 미달"
        echo; echo "| 기준 | 점수 | 최저선 | 판정 |"; echo "|---|---|---|---|"
        for k in 0 1 2 3 4 5; do
            [ "${scores[k]}" -ge "${mins[k]}" ] && mark="통과" || mark="미달"
            echo "| ${names[k]} | ${scores[k]} | ${mins[k]} | $mark |"
        done
        echo "| **총점** | $total | 70 | **$verdict** |"
        echo; echo "## 채점 근거"
        for k in 1 4 5; do
            echo "### ${names[k]}"; echo "> 샘플 구성은 서브넷 두 개로 시작합니다."; echo; echo "근거 한 줄."
            [ "$k" = 4 ] && printf -- '- https://example.com/post-%s 다른 점 한 줄\n' 1 2 3
        done
        echo; echo "## 감점 사유 (원문 인용 → 수정안)"
        for k in 0 1 2 3 4 5; do
            [ "${scores[k]}" = 100 ] && continue
            echo "### ${names[k]} (${scores[k]})"; echo "> 샘플 구성은 서브넷 두 개로 시작합니다."; echo
            echo "→ 샘플 구성은 서브넷 두 개입니다. 이유: 시험용"
        done
        echo; echo "## 중복과 군더더기 지표 원본"
        python3 -I "$SCR/redundancy_metrics.py" "$SCR_MD" --restated $(( (100 - scores[3]) / 5 ))
    } > "$out"
}
printf 'png' > "$SCR_W/images/fixture-fig01-arch.png"
printf '<svg xmlns="http://www.w3.org/2000/svg"/>' > "$SCR_W/images/fixture-fig01-arch.svg"

# --- lint_prose.py ---
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "lint_prose: clean draft exits 0" "0" "$SCR_RC"
assert_contains "lint_prose: reports zero hard findings" "$SCR_OUT" "hard_findings=0"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./샘플 구성은 비용 레버를 다룹니다./' "$SCR_MD" > "$TEST_TMP/lint-bad.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-bad.md" 2>&1); SCR_RC=$?
assert_eq "lint_prose: banned word exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: names the banned word" "$SCR_OUT" "[HARD] '레버'"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./실측 결과는 두 축으로 나눠 봅니다./' "$SCR_MD" > "$TEST_TMP/lint-axis.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-axis.md" 2>&1)
assert_contains "lint_prose: flags 실측" "$SCR_OUT" "[HARD] '실측'"
assert_contains "lint_prose: flags 축 used as axis metaphor" "$SCR_OUT" "기준, 방식, 관점, 측면"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./그래프의 x축과 가로축은 시간이고, 로그를 압축해 구축한 축약본을 축소합니다./' "$SCR_MD" > "$TEST_TMP/lint-axis-ok.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-axis-ok.md" 2>&1)
assert_contains "lint_prose: chart axes and compounds with 축 are not flagged" "$SCR_OUT" "hard_findings=0"
# "Changelog" is written in English; its translation "변경 기록" (with or without the space) is a HARD finding
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./새 버전의 변경 기록을 먼저 확인합니다./' "$SCR_MD" > "$TEST_TMP/lint-changelog.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-changelog.md" 2>&1); SCR_RC=$?
assert_eq "lint_prose: 변경 기록 exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: flags 변경 기록 and names Changelog" "$SCR_OUT" "[HARD] '변경 기록' ×1 → Changelog"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./새 버전의 변경기록을 먼저 확인합니다./' "$SCR_MD" > "$TEST_TMP/lint-changelog-nospace.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-changelog-nospace.md" 2>&1)
assert_contains "lint_prose: flags 변경기록 written without the space" "$SCR_OUT" "[HARD] '변경기록' ×1 → Changelog"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./새 버전의 Changelog를 먼저 확인합니다./' "$SCR_MD" > "$TEST_TMP/lint-changelog-ok.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-changelog-ok.md" 2>&1)
assert_contains "lint_prose: Changelog in English is not flagged" "$SCR_OUT" "hard_findings=0"
# Word rule of 2026-11-18. "절" for a part of the text is written 챕터 or 장; "견주다" is written 비교하다
scr_lint_line() { sed "s/샘플 구성은 서브넷 두 개로 시작합니다./$1/" "$SCR_MD" > "$TEST_TMP/lint-word.md"
    SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-word.md" 2>&1); SCR_RC=$?; }
scr_lint_line '이 절은 짧습니다. 절 제목과 절마다 붙는 표는 다음 절로 넘깁니다.'
assert_eq "lint_prose: 절 for a part of the text exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: flags every 절 (four forms) and names 챕터, 장" "$SCR_OUT" "×4 → 챕터, 장 (2026-11-18 확정)"
scr_lint_line '절차의 절반을 조절하고 WHERE 절과 `GROUP BY` 절, 관형절을 적절히 다룹니다. 비용 절감도 됩니다.'
assert_contains "lint_prose: 절차, 절반, 조절, SQL clauses and 관형절 are not flagged" "$SCR_OUT" "hard_findings=0"
scr_lint_line '3.1절의 설정을 다시 봅니다.'
assert_contains "lint_prose: a numbered 절 is a section-number reference" "$SCR_OUT" "섹션 번호 참조 금지"
assert_not_contains "lint_prose: a numbered 절 is reported once, not as the word rule too" "$SCR_OUT" "챕터, 장 (2026-11-18 확정)"
scr_lint_line '두 방식을 견주어 봅니다. 견줘 보면 다릅니다. 견준 결과와 견줄 대상을 견줍니다.'
assert_eq "lint_prose: 견주다 exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: flags every form of 견주다 and names 비교하다" "$SCR_OUT" "×5 → 비교하다 (2026-11-18 확정)"
scr_lint_line '두 방식을 비교해 봅니다. 의견 주시면 반영하고, 의견주신 내용도 봅니다.'
assert_contains "lint_prose: 비교하다 and 의견 주시면 are not flagged" "$SCR_OUT" "hard_findings=0"
# Word rule of 2026-11-22. "대가가 있다" (something gained comes with something lost) is written 트레이드 오프가 있다
scr_lint_line '이 방식에는 대가가 있습니다. 대가가 있고 대가가있는 구성입니다.'
assert_eq "lint_prose: 대가가 있다 exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: flags every form of 대가가 있다 and names 트레이드 오프가 있다" "$SCR_OUT" "×3 → 트레이드 오프가 있다 (2026-11-22 확정)"
scr_lint_line '이 방식에는 트레이드 오프가 있습니다. 멈춰도 되는 시간대가 있고 기대가 있습니다.'
assert_contains "lint_prose: 트레이드 오프가 있다, 시간대가 있고 and 기대가 있습니다 are not flagged" "$SCR_OUT" "hard_findings=0"
# The rules that named 절 follow the new word: a heading guide sentence and a numbered reference with 챕터
scr_lint_line '이 챕터에서는 설정을 다룹니다.'
assert_contains "lint_prose: '이 챕터에서는' counts as a heading guide sentence (C-6)" "$SCR_OUT" "[!] 이 (섹션|절|장|챕터)에서는 ×1"
scr_lint_line '챕터 3에서 본 설정과 2챕터의 표를 다시 봅니다.'
assert_eq "lint_prose: a numbered 챕터 reference exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: a numbered 챕터 is a section-number reference (two forms)" "$SCR_OUT" "×2 → 섹션 번호 참조 금지"
scr_lint_line '글을 챕터 3개로 나눴습니다.'
assert_contains "lint_prose: a count of 챕터 is not a reference" "$SCR_OUT" "hard_findings=0"
SCR_LONG=$(printf '가%.0s' $(seq 1 150))
sed "s/샘플 구성은 서브넷 두 개로 시작합니다./${SCR_LONG}입니다./" "$SCR_MD" > "$TEST_TMP/lint-long.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-long.md" 2>&1); SCR_RC=$?
assert_eq "lint_prose: sentence over 140 chars exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: reports the long sentence" "$SCR_OUT" "140자 초과 문장 1개"

# --- check_structure.py ---
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "check_structure: valid draft exits 0 (drafts/images link resolves)" "0" "$SCR_RC"
assert_contains "check_structure: reports OK" "$SCR_OUT" "OK: structure checks passed"
awk '/^\*표 1\./{next} /^\| 항목 \| 값 \|/{print "*표 1. 샘플 구성 항목(단위: 개)*"; print ""} {print}' "$SCR_MD" > "$SCR_W/drafts/caption-above.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/caption-above.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: caption above table exits 1" "1" "$SCR_RC"
assert_contains "check_structure: names the misplaced caption" "$SCR_OUT" "표 1 캡션이 표 바로 아래에 없음"
sed 's#images/fixture-fig01-arch.png#images/missing.png#' "$SCR_MD" > "$SCR_W/drafts/missing-img.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/missing-img.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: missing image exits 1" "1" "$SCR_RC"
assert_contains "check_structure: names the missing image" "$SCR_OUT" "이미지 파일 없음: images/missing.png"
rm -f "$SCR_W/drafts/caption-above.md" "$SCR_W/drafts/missing-img.md"

# --- package_blog.sh ---
echo keep > "$SCR_W/out/keep.txt"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: no gate report exits 1" "1" "$SCR_RC"
assert_contains "package_blog: names the missing gate report and the pre-check" "$SCR_OUT" "gate report not found: $SCR_W/gate-report.md (run the pre-check first"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && pass "package_blog: no zip without a gate report" \
    || fail "package_blog: no zip without a gate report" "zip written"
scr_write_gate "$SCR_W/gate-report.md"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: valid draft with a passing gate report exits 0" "0" "$SCR_RC"
assert_file_exists "package_blog: zip in <workdir>/out by default" "$SCR_W/out/$SCR_SLUG.zip"
SCR_ZIP=$(unzip -Z1 "$SCR_W/out/$SCR_SLUG.zip" 2>/dev/null | tr '\n' ' ')
for entry in "$SCR_SLUG/$SCR_SLUG.md" "$SCR_SLUG/wordpress.md" "$SCR_SLUG/gate-report.md" \
             "$SCR_SLUG/images/fixture-fig01-arch.png" "$SCR_SLUG/images/fixture-fig01-arch.svg"; do
    assert_contains "package_blog: zip has $entry" "$SCR_ZIP" "$entry"
done
assert_contains "package_blog: prints deliverables" "$SCR_OUT" "deliverables:"
assert_contains "package_blog: deliverables name wordpress.md" "$SCR_OUT" "  $SCR_W/out/$SCR_SLUG/wordpress.md"
assert_contains "package_blog: deliverables name gate-report.md" "$SCR_OUT" "  $SCR_W/out/$SCR_SLUG/gate-report.md"
# The score table is the end of the output, ready for the last response of the session
assert_eq "package_blog: ends with the score table of the pre-check" "scores (show this table in the last response):
  OK: 판정 통과 (1회차, 총점 100)
  | 기준 | 점수 | 최저선 | 판정 |
  |---|---|---|---|
  | 정합성 | 100 | 80 | 통과 |
  | 구조 완결성 | 100 | 70 | 통과 |
  | 표기 규범 | 100 | 70 | 통과 |
  | 중복과 군더더기 | 100 | 60 | 통과 |
  | 차별성과 근거 | 100 | 60 | 통과 |
  | 가독성 | 100 | 60 | 통과 |
  | **총점** | 100 | 70 | **통과** |" "$(printf '%s\n' "$SCR_OUT" | sed -n '/^scores/,$p')"
assert_contains "package_blog: wordpress.md starts with the comment that carries the title" \
    "$(head -2 "$SCR_W/out/$SCR_SLUG/wordpress.md" | tr '\n' ' ')" "<!-- 제목: 샘플 원고 – Amazon VPC 구성 점검"
assert_contains "package_blog: deliverables are absolute paths" "$SCR_OUT" "  $SCR_W/out/$SCR_SLUG.zip"
assert_file_exists "package_blog: leaves other files in out/ alone" "$SCR_W/out/keep.txt"
rm -f "$SCR_W/drafts/images"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" "$TEST_TMP/custom-out" 2>&1); SCR_RC=$?
assert_eq "package_blog: works without the drafts/images link (checks the assembled copy)" "0" "$SCR_RC"
assert_file_exists "package_blog: third argument sets the out dir" "$TEST_TMP/custom-out/$SCR_SLUG.zip"
sed -i 's#images/fixture-fig01-arch.png#images/missing.png#' "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: broken image exits 1" "1" "$SCR_RC"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && pass "package_blog: no zip after a failed check" \
    || fail "package_blog: no zip after a failed check" "stale zip left in out/"
scr_write_draft "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" 2>&1); SCR_RC=$?
assert_eq "package_blog: missing arguments exits 2" "2" "$SCR_RC"
assert_contains "package_blog: prints usage" "$SCR_OUT" "Usage: package_blog.sh [--no-gate] <workdir> <slug> [outdir]"
# A report whose verdict is 반려 (round 1, one criterion below its minimum) is consistent but not a hand-over
scr_write_gate "$SCR_W/gate-report.md" 100 100 100 100 100 30
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a 반려 report exits 1" "1" "$SCR_RC"
assert_contains "package_blog: says the gate report check failed" "$SCR_OUT" "gate report check failed"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && pass "package_blog: no zip while the verdict is 반려" \
    || fail "package_blog: no zip while the verdict is 반려" "zip written"
# Round 2 with the same score is handed over with the failing criterion named
scr_write_gate "$SCR_W/gate-report.md" 100 100 100 100 100 30 2
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a round 2 report (2회 초과 전달) is packaged" "0" "$SCR_RC"
assert_contains "package_blog: the score table of a round 2 hand-over names the round, the total and the criterion below its minimum" \
    "$(printf '%s\n' "$SCR_OUT" | sed -n '/^scores/,$p')" "  OK: 판정 2회 초과 전달 (2회차, 총점 88)"
assert_contains "package_blog: the total row of that table" "$(printf '%s\n' "$SCR_OUT" | sed -n '/^scores/,$p')" \
    "  | **총점** | 88 | 70 | **2회 초과 전달 (가독성 미달)** |"
# A report that states a verdict its scores do not support
scr_write_gate "$SCR_W/gate-report.md" 100 100 100 100 100 30
sed -i 's/판정: 반려/판정: 통과/' "$SCR_W/gate-report.md"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a report with a verdict its scores do not support exits 1" "1" "$SCR_RC"
# --no-gate: the user asked to leave the pre-check out
rm -f "$SCR_W/gate-report.md"
SCR_OUT=$(bash "$SCR/package_blog.sh" --no-gate "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog --no-gate: packages without a gate report" "0" "$SCR_RC"
SCR_ZIP=$(unzip -Z1 "$SCR_W/out/$SCR_SLUG.zip" 2>/dev/null | tr '\n' ' ')
assert_contains "package_blog --no-gate: zip still has wordpress.md" "$SCR_ZIP" "$SCR_SLUG/wordpress.md"
assert_not_contains "package_blog --no-gate: zip has no gate-report.md" "$SCR_ZIP" "gate-report.md"
assert_not_contains "package_blog --no-gate: deliverables do not name a gate report" "$SCR_OUT" "gate-report.md"
assert_contains "package_blog --no-gate: says there are no scores" "$SCR_OUT" "scores: none (--no-gate: the pre-check was left out)"
# The optional slug of the frontmatter is checked by the structure check
scr_write_gate "$SCR_W/gate-report.md"
sed -i 's#^status: draft#status: draft\nslug: 한글-슬러그#' "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a slug that is not English exits 1 (structure check)" "1" "$SCR_RC"
assert_contains "package_blog: names the slug rule" "$SCR_OUT" "frontmatter slug 형식 오류"
scr_write_draft "$SCR_MD"
# The conversion is part of packaging: an image file name the converter refuses stops the zip, although the
# structure check accepts it (the file exists under images/)
printf 'png' > "$SCR_W/images/screen shot.png"
sed -i 's#images/fixture-fig01-arch.png#images/screen shot.png#' "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: an image file name with a space exits 1" "1" "$SCR_RC"
assert_contains "package_blog: the converter names the file" "$SCR_OUT" "[FAIL] 이미지 파일 이름에 공백이나 특수문자가 있음: 'images/screen shot.png'"
assert_contains "package_blog: says the conversion failed" "$SCR_OUT" "WordPress conversion failed"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && pass "package_blog: no zip after a failed conversion" \
    || fail "package_blog: no zip after a failed conversion" "zip written"
rm -f "$SCR_W/images/screen shot.png" "$SCR_W/gate-report.md"
scr_write_draft "$SCR_MD"
assert_not_contains "package_blog: no claude.ai output path" "$(cat "$SCR/package_blog.sh")" "/mnt/user-data"

# --- check_urls.py against a local server (no external network) ---
cat > "$TEST_TMP/url-server.py" <<'EOF'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/moved":
            self.send_response(302); self.send_header("Location", "/landing/"); self.end_headers(); return
        if self.path == "/ok":  # like real servers: add the trailing slash
            self.send_response(301); self.send_header("Location", "/ok/"); self.end_headers(); return
        code = 200 if self.path in ("/ok/", "/landing/") else 404
        self.send_response(code); self.send_header("Content-Type", "text/html"); self.end_headers()
        self.wfile.write(b"<title>t</title>")
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1], "w").write(str(srv.server_address[1]))
srv.serve_forever()
EOF
python3 -I "$TEST_TMP/url-server.py" "$TEST_TMP/url-port" &
SCR_SRV=$!
for _ in $(seq 1 50); do [ -s "$TEST_TMP/url-port" ] && break; sleep 0.1; done
SCR_PORT=$(cat "$TEST_TMP/url-port" 2>/dev/null)
if [ -n "$SCR_PORT" ]; then
    SCR_BASE="http://127.0.0.1:$SCR_PORT"
    cat > "$TEST_TMP/urls.md" <<EOF
- [ok]($SCR_BASE/ok/)
- [moved]($SCR_BASE/moved)
- [missing]($SCR_BASE/missing)
- example https://api.example.com/v1 and template \`https://aws.amazon.com/ko/blogs/tech/category/<path>/\`
EOF
    SCR_OUT=$(no_proxy=127.0.0.1 NO_PROXY=127.0.0.1 python3 -I "$SCR/check_urls.py" "$TEST_TMP/urls.md" 2>&1); SCR_RC=$?
    assert_eq "check_urls: failures exit 1" "1" "$SCR_RC"
    assert_contains "check_urls: 200 is OK" "$SCR_OUT" "[OK] $SCR_BASE/ok/"
    assert_contains "check_urls: redirect to another page is REDIRECT" "$SCR_OUT" "[REDIRECT] $SCR_BASE/moved  -> $SCR_BASE/landing/"
    assert_contains "check_urls: 404 is FAIL" "$SCR_OUT" "[FAIL] $SCR_BASE/missing  -> HTTP 404"
    assert_contains "check_urls: example host and template are skipped" "$SCR_OUT" "checked=3 skipped=2 failed=2"
    printf -- '- [ok](%s/ok)\n' "$SCR_BASE" > "$TEST_TMP/urls-ok.md"
    SCR_OUT=$(no_proxy=127.0.0.1 NO_PROXY=127.0.0.1 python3 -I "$SCR/check_urls.py" "$TEST_TMP/urls-ok.md" 2>&1); SCR_RC=$?
    assert_eq "check_urls: trailing-slash difference alone is OK (exit 0)" "0" "$SCR_RC"
else
    skip "check_urls: local server tests" "test HTTP server did not start"
fi
kill "$SCR_SRV" 2>/dev/null; wait "$SCR_SRV" 2>/dev/null

# --- render_diagrams.py refuses to guess an output folder ---
SCR_OUT=$(python3 -I "$SCR/render_diagrams.py" 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && pass "render_diagrams: no images dir exits non-zero" \
    || fail "render_diagrams: no images dir exits non-zero" "exit 0"
if printf '%s' "$SCR_OUT" | grep -qE 'usage: render_diagrams.py|playwright is not installed'; then
    pass "render_diagrams: explains usage or how to get Playwright"
else
    fail "render_diagrams: explains usage or how to get Playwright" "$SCR_OUT"
fi
assert_not_contains "render_diagrams: no default inside the skill folder" "$(cat "$SCR/render_diagrams.py")" \
    'os.path.dirname(__file__), "..", "images"'

# --- diagram_lib.py and the example generator, set up the way SKILL.md step 4 does it ---
# The cp and pointer lines of the step 4 block run as written, with CLAUDE_SKILL_DIR and W set and HOME pointed
# at an empty folder, so the copy can only find the assets through the .aws-diagram-assets pointer.
SCR_HOME="$TEST_TMP/scr-home"
SCR_DW="$TEST_TMP/scr-work"
mkdir -p "$SCR_HOME" "$SCR_DW"/{diagrams,images}
SCR_STEPS=$(awk '/^## 4\. /{s=1} s && /^```bash/{b=1; next} b && /^```/{exit} b' "$SCR/../SKILL.md" \
    | grep -E '^(cp|python3) "\$\{CLAUDE_SKILL_DIR\}/scripts/(diagram_lib|example_diagrams)\.py"' || true)
assert_eq "SKILL.md step 4: three setup lines (copy lib, write pointer, copy example)" "3" \
    "$(printf '%s\n' "$SCR_STEPS" | grep -c . || true)"
SCR_OUT=$(cd "$SCR_DW" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" CLAUDE_SKILL_DIR="$PROJECT_ROOT/skills/aws-blog-skills" \
    W="$SCR_DW" bash -c "$SCR_STEPS" 2>&1); SCR_RC=$?
assert_eq "SKILL.md step 4 setup lines run (exit 0)" "0" "$SCR_RC"
for scr_f in diagram_lib.py .aws-diagram-assets diagrams.py; do
    assert_file_exists "step 4 setup: $scr_f in the work folder" "$SCR_DW/diagrams/$scr_f"
done
SCR_ASSETS=$(cat "$SCR_DW/diagrams/.aws-diagram-assets" 2>/dev/null)
[ -d "$SCR_ASSETS/aws-icons" ] && pass "step 4 setup: pointer names an assets folder with aws-icons ($SCR_ASSETS)" \
    || fail "step 4 setup: pointer names an assets folder with aws-icons" "'$SCR_ASSETS'"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" BLOG_IMAGES="$SCR_DW/images" python3 diagrams.py 2>&1); SCR_RC=$?
assert_eq "example generator: exits 0 in the work folder" "0" "$SCR_RC"
assert_eq "example generator: 4 SVG figures" "4" "$(find "$SCR_DW/images" -name '*.svg' | wc -l | tr -d ' ')"
assert_eq "example generator: 4 HTML render pages" "4" "$(find "$SCR_DW/images" -name '*.html' | wc -l | tr -d ' ')"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" python3 -c 'from diagram_lib import Canvas
c = Canvas("t", "t", "t")
c.node(40, 40, 200, 96, "A")
c.node(120, 80, 200, 96, "B")' 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && printf '%s' "$SCR_OUT" | grep -qF "node overlap" \
    && pass "diagram_lib: overlapping nodes fail the geometry assert" \
    || fail "diagram_lib: overlapping nodes fail the geometry assert" "rc=$SCR_RC"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" python3 -c 'from diagram_lib import Canvas
Canvas("t", "t", "t").node(42, 40, 200, 96, "A")' 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && printf '%s' "$SCR_OUT" | grep -qF "not on 4px grid" \
    && pass "diagram_lib: off-grid coordinates fail the 4px assert" \
    || fail "diagram_lib: off-grid coordinates fail the 4px assert" "rc=$SCR_RC"
rm -rf "$SCR_DW/diagrams/__pycache__"

# --- check_structure.py: the optional slug ---
ln -sfn ../images "$SCR_W/drafts/images"   # the packaging tests above removed the link
sed 's#^status: draft#status: draft\nslug: vpc-check#' "$SCR_MD" > "$SCR_W/drafts/slug-ok.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/slug-ok.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: an English slug in the frontmatter passes" "0" "$SCR_RC"
sed 's#^status: draft#status: draft\nslug: VPC_Check#' "$SCR_MD" > "$SCR_W/drafts/slug-bad.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/slug-bad.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: a slug with capitals or an underscore exits 1" "1" "$SCR_RC"
assert_contains "check_structure: names the slug" "$SCR_OUT" "frontmatter slug 형식 오류 (영어 소문자, 숫자, 하이픈): VPC_Check"
rm -f "$SCR_W/drafts/slug-ok.md" "$SCR_W/drafts/slug-bad.md" "$SCR_W/drafts/images"

# --- redundancy_metrics.py (criterion 4 of the pre-check) ---
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "redundancy_metrics: a clean draft exits 0" "0" "$SCR_RC"
assert_contains "redundancy_metrics: a clean draft scores 100" "$SCR_OUT" "**점수: 100/100**"
assert_contains "redundancy_metrics: prints the table the gate report carries" "$SCR_OUT" "| 지표 | 측정값 | 기준 | 감점 |"
assert_not_contains "redundancy_metrics: no criterion score until restatements are counted" "$SCR_OUT" "기준 4 점수"
assert_contains "redundancy_metrics: asks for --restated" "$SCR_OUT" "재진술 미집계"
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$SCR_MD" --restated 3 2>&1)
assert_contains "redundancy_metrics --restated 3: 5 points each" "$SCR_OUT" "재진술 3건: -15"
assert_contains "redundancy_metrics --restated 3: prints the score of criterion 4" "$SCR_OUT" "**기준 4 점수: 85/100**"
# One draft that trips each measure once. The numbers below are worked out by hand from the rules:
# a repeated paragraph (-6), two sentences that share 20 characters (-8), four meta sentences (three over the
# one allowed, -15), three quoted coinages in a short text (density over the limit, capped at -12), one
# paragraph of six sentences (-5), seven stock words (capped at -13): 100 - 59 = 41
cat > "$TEST_TMP/redundant.md" <<'EOF'
---
title: "t"
date: 2026-01-01
author: "x"
status: draft
---

# 제목

by WOO HYUNG CHOI on 1 1월 2026 in [A](https://aws.amazon.com/ko/blogs/tech/category/a/), [B](https://aws.amazon.com/ko/blogs/tech/category/b/)

이 구성의 핵심은 엔드포인트입니다. 중요한 점은 라우팅입니다. 주목할 부분은 비용입니다. 결론적으로 비용이 줄어듭니다.

## 1. 가

아래 명령은 서울 리전을 기준으로 실행합니다.

| 항목 | 값 |
|---|---|
| a | 1 |

*표 1. 가*

게이트웨이 엔드포인트를 만들면 프라이빗 서브넷의 라우팅 테이블에 접두사 목록이 추가됩니다.

## 2. 나

아래 명령은 서울 리전을 기준으로 실행합니다.

| 항목 | 값 |
|---|---|
| a | 1 |

*표 2. 나*

게이트웨이 엔드포인트를 만들면 프라이빗 서브넷의 라우팅 테이블에 접두사 목록이 생깁니다. 이 방식은 "깔끔한 경로"와 "조용한 비용"을 "한 번에 정리"합니다. 다양한 구성을 효과적으로 쉽게 매우 간단히 더욱 적절히 다룹니다.

첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. 넷째 문장입니다. 다섯째 문장입니다. 여섯째 문장입니다.

```
이 구성의 핵심은 코드 블록 안에 있어도 세지 않습니다. 매우 매우 매우 매우.
```

## 참고 자료

- [매우 다양한 구성을 효과적으로 다루는 문서 – User Guide](https://example.com)

*본문의 금액은 매우 다양한 전제를 바탕으로 한 추정치입니다.*

## 저자 소개

효율적으로 효율적으로 효율적으로 핵심 핵심 핵심 핵심.
EOF
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$TEST_TMP/redundant.md" --restated 2 2>&1)
assert_contains "redundancy_metrics: a repeated paragraph" "$SCR_OUT" "| 보일러플레이트 문단 반복 | 1회 | 0 | -6 |"
assert_contains "redundancy_metrics: two sentences that share a long Korean phrase" "$SCR_OUT" "| 문장 반복 (동일 또는 한글 공통 구절 20자) | 동일 0, 유사 1 | 0 | -8 |"
assert_contains "redundancy_metrics: meta sentences over the one allowed" "$SCR_OUT" "| 메타 강조 문장 | 4회 | ≤ 1 | -15 |"
assert_contains "redundancy_metrics: quoted coinages" "$SCR_OUT" "(3회) | ≤ 1.0 | -12 |"
assert_contains "redundancy_metrics: a paragraph of six sentences" "$SCR_OUT" "| 6문장 이상 문단 | 1개 | 0 | -5 |"
assert_contains "redundancy_metrics: stock words (code, the reference list and the bio are not counted)" "$SCR_OUT" "(7회) | ≤ 1.5 | -13 |"
assert_contains "redundancy_metrics: score is 100 minus the six penalties" "$SCR_OUT" "**점수: 41/100**"
assert_contains "redundancy_metrics: restatements come off that score" "$SCR_OUT" "**기준 4 점수: 31/100**"
assert_contains "redundancy_metrics: shows the repeated paragraph as evidence" "$SCR_OUT" "- 보일러플레이트: 아래 명령은 서울 리전을 기준으로 실행합니다."
# The fixture's two tables are the same, row for row. Read as prose they would be a second repeated paragraph
# (the source's script counts them); the count stays at the one repeated sentence paragraph
assert_not_contains "redundancy_metrics: table rows are not repeated paragraphs" "$SCR_OUT" "| 보일러플레이트 문단 반복 | 2회 |"
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$TEST_TMP/redundant.md" --restated 20 2>&1)
assert_contains "redundancy_metrics: the criterion score does not go below 0" "$SCR_OUT" "**기준 4 점수: 0/100**"
# One meta sentence is allowed; the second one costs 5. Captions, the byline and image lines are not prose
cat > "$TEST_TMP/meta-two.md" <<'EOF'
# 제목

by WOO HYUNG CHOI on 1 1월 2026 in [핵심 A](https://aws.amazon.com/ko/blogs/tech/category/a/), [B](https://aws.amazon.com/ko/blogs/tech/category/b/)

이 구성의 핵심은 엔드포인트입니다. 결론적으로 비용이 줄어듭니다. 나머지 문장은 평범합니다.

![핵심 구성을 보여 주는 그림입니다. 중요한 점은 경로입니다.](images/a.png)

*그림 1. 핵심 구성. 중요한 점은 경로입니다.*
EOF
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$TEST_TMP/meta-two.md" --restated 0 2>&1)
assert_contains "redundancy_metrics: two meta sentences cost 5 (one is allowed; captions, alt text and the byline are not prose)" \
    "$SCR_OUT" "| 메타 강조 문장 | 2회 | ≤ 1 | -5 |"
assert_contains "redundancy_metrics --restated 0: the criterion score is the script score" "$SCR_OUT" "**기준 4 점수: 95/100**"
cp "$TEST_TMP/redundant.md" "$TEST_TMP/redundant.docx"
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$TEST_TMP/redundant.docx" 2>&1); SCR_RC=$?
assert_eq "redundancy_metrics: a file that is not Markdown exits 2" "2" "$SCR_RC"
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$SCR_MD" --restated -1 2>&1); SCR_RC=$?
assert_eq "redundancy_metrics: a negative --restated exits 2" "2" "$SCR_RC"

# --- check_gate.py (the report's arithmetic, evidence and verdict) ---
SCR_G="$TEST_TMP/gate.md"
scr_gate() { SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" 2>&1); SCR_RC=$?; }
scr_write_gate "$SCR_G"; scr_gate
assert_eq "check_gate: six scores of 100 exit 0" "0" "$SCR_RC"
assert_contains "check_gate: prints the verdict with the round and the total" "$SCR_OUT" "OK: 판정 통과 (1회차, 총점 100)"
assert_contains "check_gate: prints the score table (a criterion row)" "$SCR_OUT" "  | 차별성과 근거 | 100 | 60 | 통과 |"
assert_contains "check_gate: prints the score table (the total row)" "$SCR_OUT" "  | **총점** | 100 | 70 | **통과** |"
# 80 + 71 + 70 + 60 + 80 + 60 = 421, total 70 (cut, not rounded): every criterion at its minimum or above passes
scr_write_gate "$SCR_G" 80 71 70 60 80 60; scr_gate
assert_eq "check_gate: total 70 with every criterion at or above its minimum passes" "0" "$SCR_RC"
# 80 + 71 + 70 + 60 + 60 + 60 = 401, total 66 (66.8 cut): no criterion is below its minimum, the total is
scr_write_gate "$SCR_G" 80 71 70 60 60 60; scr_gate
assert_eq "check_gate: every minimum met but total 66 is 반려 (exit 3)" "3" "$SCR_RC"
assert_contains "check_gate: says what to do with a 반려" "$SCR_OUT" "수정한 뒤 다시 채점한다"
# A high total does not save one criterion below its minimum (정합성 70 < 80)
scr_write_gate "$SCR_G" 70 100 100 100 100 100; scr_gate
assert_eq "check_gate: one criterion below its minimum is 반려 although the total is 95" "3" "$SCR_RC"
assert_contains "check_gate: the score table of a 반려 marks the row and names the criterion in the total row" "$SCR_OUT" \
    "  | 정합성 | 70 | 80 | 미달 |"
assert_contains "check_gate: the total row of a 반려" "$SCR_OUT" "  | **총점** | 95 | 70 | **반려 (정합성 미달)** |"
scr_write_gate "$SCR_G" 70 100 100 100 100 100 2; scr_gate
assert_eq "check_gate: the same scores in round 2 are handed over (exit 0)" "0" "$SCR_RC"
assert_contains "check_gate: round 2 verdict" "$SCR_OUT" "OK: 판정 2회 초과 전달"
scr_write_gate "$SCR_G" 70 100 100 100 100 100 2; sed -i '/^이전 회차/d' "$SCR_G"; scr_gate
assert_eq "check_gate: round 2 without the line of the earlier round exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the missing line" "$SCR_OUT" "이전 회차"
scr_write_gate "$SCR_G"; sed -i 's#^회차: 1 / 2#회차: 3 / 2#' "$SCR_G"; scr_gate
assert_eq "check_gate: a third round exits 1" "1" "$SCR_RC"
# Statements the scores do not support
scr_write_gate "$SCR_G" 70 100 100 100 100 100; sed -i 's/판정: 반려/판정: 통과/' "$SCR_G"; scr_gate
assert_eq "check_gate: 통과 stated over a criterion below its minimum exits 1" "1" "$SCR_RC"
assert_contains "check_gate: says what the scores give" "$SCR_OUT" "판정 '통과': 점수로는 '반려' (미달: 정합성)"
scr_write_gate "$SCR_G" 80 71 70 60 80 60; sed -i 's#^| \*\*총점\*\* | 70 |#| **총점** | 75 |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a total that is not the average exits 1" "1" "$SCR_RC"
assert_contains "check_gate: prints the average" "$SCR_OUT" "총점 75: 여섯 점수의 평균(소수점 아래 버림)은 70"
scr_write_gate "$SCR_G" 70 100 100 100 100 100; sed -i 's#^| 정합성 | 70 | 80 | 미달 |#| 정합성 | 70 | 60 | 통과 |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a lowered minimum exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the minimum" "$SCR_OUT" "정합성 최저선 60: 80이어야 함"
scr_write_gate "$SCR_G" 100 100 100 100 100 30; sed -i 's#^| 가독성 | 30 | 60 | 미달 |#| 가독성 | 30 | 60 | 통과 |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a row marked 통과 below its minimum exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the row mark" "$SCR_OUT" "가독성 판정 '통과': 점수 30, 최저선 60이면 '미달'"
scr_write_gate "$SCR_G" 100 100 100 100 100 30; sed -i 's#^\(| \*\*총점\*\* | [0-9]* | 70 | \)\*\*반려\*\* |#\1**통과** |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a total row that says 통과 over a 반려 exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the total row" "$SCR_OUT" "총점 행 판정 '통과': 점수로는 '반려'"
scr_write_gate "$SCR_G"; sed -i 's#^| 정합성 | 100 | 80 |#| 정합성 | 160 | 80 |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a score over 100 exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the score" "$SCR_OUT" "정합성 점수 160: 0~100"
scr_write_gate "$SCR_G"; sed -i '/^| 가독성 |/d' "$SCR_G"; scr_gate
assert_eq "check_gate: a missing criterion row exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the missing row" "$SCR_OUT" "점수표에 '가독성' 행 없음"
# Evidence: a judged criterion needs a quoted sentence, every lost point a quote and a corrected text
scr_write_gate "$SCR_G"
awk '/^### 차별성과 근거$/{print; getline; next} {print}' "$SCR_G" > "$SCR_G.tmp" && mv "$SCR_G.tmp" "$SCR_G"; scr_gate
assert_eq "check_gate: a judged criterion without a quoted sentence exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the criterion without evidence" "$SCR_OUT" "'### 차별성과 근거'에 근거 문장 인용(> …) 없음"
scr_write_gate "$SCR_G" 100 100 90 100 100 100; sed -i '/^→ /d' "$SCR_G"; scr_gate
assert_eq "check_gate: a lost point without a corrected text exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the pair" "$SCR_OUT" "'### 표기 규범 (90)': 원문 인용(> …)과 수정안(→ …) 쌍 없음"
scr_write_gate "$SCR_G" 100 100 90 100 100 100; sed -i 's/^### 표기 규범 (90)/### 표기 규범 (95)/' "$SCR_G"; scr_gate
assert_eq "check_gate: a reason heading with another score exits 1" "1" "$SCR_RC"
# Criterion 4 is the script's number
scr_write_gate "$SCR_G" 100 100 100 90 100 100; scr_gate
assert_eq "check_gate: criterion 4 equal to the pasted script score passes" "0" "$SCR_RC"
sed -i 's#^| 중복과 군더더기 | 90 |#| 중복과 군더더기 | 95 |#; s/^### 중복과 군더더기 (90)/### 중복과 군더더기 (95)/' "$SCR_G"; scr_gate
assert_eq "check_gate: criterion 4 that differs from the script score exits 1" "1" "$SCR_RC"
assert_contains "check_gate: prints the script's number" "$SCR_OUT" "중복과 군더더기 95: 스크립트의 기준 4 점수는 90"
scr_write_gate "$SCR_G"; sed -i '/기준 4 점수/d' "$SCR_G"; scr_gate
assert_eq "check_gate: raw metrics without the criterion score (no --restated) exit 1" "1" "$SCR_RC"
assert_contains "check_gate: asks for the --restated output" "$SCR_OUT" "--restated"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" 2>&1); SCR_RC=$?
assert_eq "check_gate: no argument exits 2" "2" "$SCR_RC"
assert_contains "check_gate: prints usage" "$SCR_OUT" "Usage: python3 check_gate.py <gate-report.md>"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$TEST_TMP/no-such-report.md" 2>&1); SCR_RC=$?
assert_eq "check_gate: an unreadable report exits 2" "2" "$SCR_RC"

# --- md_to_wordpress.py (HTML for the WordPress code editor) ---
SCR_WP="$TEST_TMP/wp-work"
mkdir -p "$SCR_WP/images"
printf 'png' > "$SCR_WP/images/wp-fig01-arch.png"
cat > "$SCR_WP/2026-02-03-vpc-endpoint.md" <<'EOF'
---
title: "엔드포인트 비용 -- 점검"
date: 2026-02-03
author: "Woohyung Choi"
status: draft
---

# 엔드포인트 비용 -- 점검

by WOO HYUNG CHOI on 3 2월 2026 in [Best Practices](https://aws.amazon.com/ko/blogs/tech/category/post-types/best-practices/), [Intermediate (200)](https://aws.amazon.com/ko/blogs/tech/category/learning-levels/intermediate-200/)

리드 문단은 `com.amazonaws.s3` 이름과 [문서](https://docs.aws.amazon.com/vpc/?a=1&b=2)를 가리키고 A & B < C 를 적습니다.
둘째 줄은 같은 문단입니다.

## 1. 구성

| 항목 | 값 | 비고 |
|:---|---:|:---:|
| 전송량 | 1,024 GB | `a\|b` |

*표 1. 예시 구성*

![게이트웨이 엔드포인트를 거쳐 Amazon S3에 연결되는 구성 "따옴표"](images/wp-fig01-arch.png)

*그림 1. 구성*

---

### 1.1 절차

1. 엔드포인트를 만듭니다.

   ```bash
   aws ec2 describe-vpc-endpoints --query 'a<b'
   ```

2. 라우팅 테이블을 확인합니다.
   - 하위 항목 **굵게** 그리고 *기울임*
3. 끝입니다.

```
손익분기 = 고정 비용 ÷ 단가
```

> 인용 문장입니다.

자세한 내용은 <https://docs.aws.amazon.com/vpc/> 와 <video src="x.mov"></video> 를 봅니다.

## 2. 마치며

끝 문단입니다. 타입은 `Map<String, List<T>>` 입니다.
EOF
scr_wp() { SCR_OUT=$(python3 -I "$SCR/md_to_wordpress.py" "$@" 2>&1); SCR_RC=$?; }
scr_wp "$SCR_WP/2026-02-03-vpc-endpoint.md" --out "$SCR_WP/wordpress.md"
assert_eq "md_to_wordpress: converts the draft (exit 0)" "0" "$SCR_RC"
SCR_HTML=$(cat "$SCR_WP/wordpress.md" 2>/dev/null)
assert_contains "md_to_wordpress: the comment carries the title (no '--' inside a comment)" "$SCR_HTML" "제목: 엔드포인트 비용 - - 점검"
assert_contains "md_to_wordpress: the slug comes from the file name without its date" "$SCR_HTML" "추천 URL slug: vpc-endpoint (파일 이름에서 날짜를 뺀 값)"
assert_contains "md_to_wordpress: expected URL on the tech channel" "$SCR_HTML" "예상 URL: https://aws.amazon.com/ko/blogs/tech/vpc-endpoint/"
assert_contains "md_to_wordpress: byline categories go into the comment" "$SCR_HTML" "카테고리: Best Practices, Intermediate (200)"
assert_eq "md_to_wordpress: the file starts with the comment" "<!--" "$(head -1 "$SCR_WP/wordpress.md")"
assert_not_contains "md_to_wordpress: no h1 in the body" "$SCR_HTML" "<h1"
assert_not_contains "md_to_wordpress: the byline is not in the body" "$SCR_HTML" "by WOO HYUNG CHOI"
assert_not_contains "md_to_wordpress: frontmatter is not in the body" "$SCR_HTML" "status: draft"
assert_not_contains "md_to_wordpress: no hr" "$SCR_HTML" "<hr"
assert_contains "md_to_wordpress: two source lines are one paragraph; code, link and escapes inside" "$SCR_HTML" \
    '<p>리드 문단은 <code>com.amazonaws.s3</code> 이름과 <a href="https://docs.aws.amazon.com/vpc/?a=1&amp;b=2">문서</a>를 가리키고 A &amp; B &lt; C 를 적습니다. 둘째 줄은 같은 문단입니다.</p>'
assert_contains "md_to_wordpress: angle brackets inside inline code are escaped" "$SCR_HTML" \
    "<p>끝 문단입니다. 타입은 <code>Map&lt;String, List&lt;T&gt;&gt;</code> 입니다.</p>"
assert_contains "md_to_wordpress: h2 and h3" "$SCR_HTML" "<h2>1. 구성</h2>"
assert_contains "md_to_wordpress: h3" "$SCR_HTML" "<h3>1.1 절차</h3>"
assert_contains "md_to_wordpress: table with inline border, centered, 8px below" "$SCR_HTML" \
    '<table style="border-collapse: collapse; border: 1px solid #000; margin: 0 auto 8px auto;">'
assert_contains "md_to_wordpress: header cell in thead with the grey background and its alignment" "$SCR_HTML" \
    '<th style="border: 1px solid #000; padding: 8px; background-color: #f2f3f3; text-align: right;">값</th>'
assert_contains "md_to_wordpress: body cell; an escaped pipe inside code stays one cell" "$SCR_HTML" \
    '<td style="border: 1px solid #000; padding: 8px; text-align: center;"><code>a|b</code></td>'
assert_contains "md_to_wordpress: caption centered right below" "$SCR_HTML" \
    '<p style="text-align: center; margin-top: 0;"><em>표 1. 예시 구성</em></p>'
assert_contains "md_to_wordpress: image keeps its local path, alt is escaped" "$SCR_HTML" \
    '<p style="text-align: center;"><img src="images/wp-fig01-arch.png" alt="게이트웨이 엔드포인트를 거쳐 Amazon S3에 연결되는 구성 &quot;따옴표&quot;" /></p>'
assert_contains "md_to_wordpress: a code block inside a list item stays in the item, dedented and escaped" "$SCR_HTML" \
    "<li>엔드포인트를 만듭니다.
<pre><code class=\"lang-bash\">aws ec2 describe-vpc-endpoints --query 'a&lt;b'</code></pre>
</li>"
assert_contains "md_to_wordpress: a nested list with bold and italic" "$SCR_HTML" \
    "<li>하위 항목 <strong>굵게</strong> 그리고 <em>기울임</em></li>"
assert_eq "md_to_wordpress: one ordered list (the numbering does not restart after the code block)" "1" \
    "$(printf '%s\n' "$SCR_HTML" | grep -c '^<ol')"
assert_contains "md_to_wordpress: a fence without a label becomes lang-text" "$SCR_HTML" '<pre><code class="lang-text">손익분기 = 고정 비용 ÷ 단가</code></pre>'
assert_contains "md_to_wordpress: reports the unlabeled block" "$SCR_OUT" "[!] 언어 라벨 없는 코드 블록 → lang-text"
assert_contains "md_to_wordpress: blockquote" "$SCR_HTML" "<blockquote>
<p>인용 문장입니다.</p>
</blockquote>"
assert_contains "md_to_wordpress: an angle-bracket URL becomes a link" "$SCR_HTML" '<a href="https://docs.aws.amazon.com/vpc/">https://docs.aws.amazon.com/vpc/</a>'
assert_contains "md_to_wordpress: reports the angle-bracket URL" "$SCR_OUT" "[!] 꺾쇠로 감싼 URL 1개를 링크로 바꿈"
assert_contains "md_to_wordpress: raw HTML is written as text, not passed through" "$SCR_HTML" "&lt;video src=\"x.mov\"&gt;&lt;/video&gt;"
assert_contains "md_to_wordpress: reports the raw HTML" "$SCR_OUT" "[!] HTML 태그가 든 줄 1개"
assert_contains "md_to_wordpress: reports what it changed" "$SCR_OUT" "[변환] 구분선(hr) 1개 제거"
assert_contains "md_to_wordpress: summary counts" "$SCR_OUT" "h2 2, h3 1, 문단 3, 목록 1, 표 1, 이미지 1, 캡션 2, 코드 블록 2 (lang-bash, lang-text)"
# Slug: --slug wins over the frontmatter, the frontmatter over the file name
sed 's#^status: draft#status: draft\nslug: from-frontmatter#' "$SCR_WP/2026-02-03-vpc-endpoint.md" > "$SCR_WP/2026-02-03-with-slug.md"
scr_wp "$SCR_WP/2026-02-03-with-slug.md" --out "$SCR_WP/wp-slug.md"
assert_contains "md_to_wordpress: slug from the frontmatter" "$(cat "$SCR_WP/wp-slug.md")" "추천 URL slug: from-frontmatter (프론트매터 slug)"
scr_wp "$SCR_WP/2026-02-03-with-slug.md" --out "$SCR_WP/wp-slug.md" --slug from-option --channel korea
assert_contains "md_to_wordpress: --slug wins and --channel sets the URL" "$(cat "$SCR_WP/wp-slug.md")" \
    "예상 URL: https://aws.amazon.com/ko/blogs/korea/from-option/"
cp "$SCR_WP/2026-02-03-vpc-endpoint.md" "$SCR_WP/2026-02-03-한글-제목.md"
rm -f "$SCR_WP/wp-fail.md"
scr_wp "$SCR_WP/2026-02-03-한글-제목.md" --out "$SCR_WP/wp-fail.md"
assert_eq "md_to_wordpress: no English slug to be had exits 1" "1" "$SCR_RC"
assert_contains "md_to_wordpress: asks for slug: in the frontmatter" "$SCR_OUT" "[FAIL] 영어 URL slug를 정할 수 없음"
[ ! -e "$SCR_WP/wp-fail.md" ] && pass "md_to_wordpress: nothing is written on a failure" \
    || fail "md_to_wordpress: nothing is written on a failure" "file written"
# Images the converter refuses
scr_wp_image() { sed "s#images/wp-fig01-arch.png#$1#" "$SCR_WP/2026-02-03-vpc-endpoint.md" > "$SCR_WP/2026-02-03-img.md"
    rm -f "$SCR_WP/wp-fail.md"; scr_wp "$SCR_WP/2026-02-03-img.md" --out "$SCR_WP/wp-fail.md"; }
scr_wp_image 'data:image/png;base64,AAAA'
assert_eq "md_to_wordpress: a base64 image exits 1" "1" "$SCR_RC"
assert_contains "md_to_wordpress: names the base64 image" "$SCR_OUT" "[FAIL] base64 데이터 URI 이미지"
scr_wp_image 'images/missing.png'
assert_contains "md_to_wordpress: a missing image file fails" "$SCR_OUT" "[FAIL] 이미지 파일 없음: images/missing.png"
scr_wp_image 'figures/wp-fig01-arch.png'
assert_contains "md_to_wordpress: an image outside images/ fails" "$SCR_OUT" "[FAIL] 이미지 경로가 images/ 상대 경로가 아님"
# macOS screenshot names carry U+202F, which looks like a space
printf 'png' > "$SCR_WP/images/$(printf 'shot\xe2\x80\xafPM.png')"
scr_wp_image "images/$(printf 'shot\xe2\x80\xafPM.png')"
assert_eq "md_to_wordpress: a file name with U+202F exits 1" "1" "$SCR_RC"
assert_contains "md_to_wordpress: shows the invisible character" "$SCR_OUT" "\\u202fPM.png"
[ ! -e "$SCR_WP/wp-fail.md" ] && pass "md_to_wordpress: nothing is written when an image is refused" \
    || fail "md_to_wordpress: nothing is written when an image is refused" "file written"
scr_wp_image 'https://media.example.com/x/arch-300x169.png'
assert_eq "md_to_wordpress: a remote image is accepted (exit 0)" "0" "$SCR_RC"
assert_contains "md_to_wordpress: warns about a reduced copy (-300x169)" "$SCR_OUT" "[!] 축소본 이미지 URL"
# The second count: a caption the list parser swallows is noticed, not dropped silently
sed 's#^3\. 끝입니다\.#3. 끝입니다.\n   *그림 2. 목록 안의 캡션*#' "$SCR_WP/2026-02-03-vpc-endpoint.md" > "$SCR_WP/2026-02-03-count.md"
scr_wp "$SCR_WP/2026-02-03-count.md" --out "$SCR_WP/wp-fail.md"
assert_eq "md_to_wordpress: a block count that differs from the draft exits 1" "1" "$SCR_RC"
assert_contains "md_to_wordpress: names the block" "$SCR_OUT" "[FAIL] 변환 검산 불일치: 캡션 원고 3개, 변환본 2개"
scr_wp "$SCR_WP/2026-02-03-vpc-endpoint.md" --out "$SCR_WP/2026-02-03-vpc-endpoint.md"
assert_eq "md_to_wordpress: --out that is the draft exits 2" "2" "$SCR_RC"
scr_wp "$SCR_WP/2026-02-03-vpc-endpoint.md"
assert_eq "md_to_wordpress: --out is required (exit 2)" "2" "$SCR_RC"
# The draft template converts once its placeholder image exists (the skeleton and the converter stay in step)
mkdir -p "$TEST_TMP/wp-template/images"
cp skills/aws-blog-skills/assets/templates/blog-template.md "$TEST_TMP/wp-template/2026-01-01-template.md"
printf 'png' > "$TEST_TMP/wp-template/images/slug-fig01-current-architecture.png"
sed -i 's#images/<slug>-fig01#images/slug-fig01#; s#^slug: .*#slug: template-check#' "$TEST_TMP/wp-template/2026-01-01-template.md"
scr_wp "$TEST_TMP/wp-template/2026-01-01-template.md" --out "$TEST_TMP/wp-template/wordpress.md"
assert_eq "md_to_wordpress: blog-template.md converts (exit 0)" "0" "$SCR_RC"
assert_not_contains "md_to_wordpress: the template's fences all carry a language" "$SCR_OUT" "언어 라벨 없는 코드 블록"

# --- Inputs that once gave a wrong result (review of the first version, 2026-11-25) ---
scr_wp_case() { printf '%s\n' "$1" > "$SCR_WP/2026-02-03-case.md"; rm -f "$SCR_WP/wp-case.md"
    scr_wp "$SCR_WP/2026-02-03-case.md" --out "$SCR_WP/wp-case.md"; SCR_HTML=$(cat "$SCR_WP/wp-case.md" 2>/dev/null); }
# The title cannot close the comment at the top: three hyphens once left "- --" behind
scr_wp_case $'---\ntitle: "A ---><script>alert(1)</script>"\n---\n\n본문입니다.'
assert_eq "md_to_wordpress: a title with '--->' converts" "0" "$SCR_RC"
assert_contains "md_to_wordpress: hyphen runs are broken up and angle brackets escaped in the comment" "$SCR_HTML" \
    "제목: A - - -&gt;&lt;script&gt;alert(1)&lt;/script&gt;"
assert_not_contains "md_to_wordpress: no tag from the title reaches the page" "$SCR_HTML" "<script>"
assert_eq "md_to_wordpress: the comment is closed once, by the converter" "1" "$(grep -c -- '-->' "$SCR_WP/wp-case.md")"
scr_wp_case $'# B --> <b>x</b>\n\n본문입니다.'
assert_contains "md_to_wordpress: the same for a title taken from the H1" "$SCR_HTML" "제목: B - -&gt; &lt;b&gt;x&lt;/b&gt;"
# A code span inside a URL or an alt text is text there, escaped as an attribute value
scr_wp_case $'# T\n\n[x](https://a.example/`" onmouseover="alert(1)`) 끝\n\n- ![`echo "hi"` 결과](images/wp-fig01-arch.png)'
assert_contains "md_to_wordpress: a code span in a URL cannot break out of href" "$SCR_HTML" \
    '<a href="https://a.example/&quot; onmouseover=&quot;alert(1)">x</a>'
assert_contains "md_to_wordpress: a code span in an alt text is plain text there" "$SCR_HTML" 'alt="echo &quot;hi&quot; 결과"'
assert_not_contains "md_to_wordpress: no markup inside an attribute value" "$SCR_HTML" '="<code>'
# Link schemes
scr_wp_case $'# T\n\n[x](javascript:alert(1)) [y](DATA:text/html;base64,AAAA) ![그림](vbscript:x)'
assert_eq "md_to_wordpress: javascript:, data: and vbscript: URLs exit 1" "1" "$SCR_RC"
for scr_scheme in javascript DATA vbscript; do
    assert_contains "md_to_wordpress: names the scheme $scr_scheme" "$SCR_OUT" "[FAIL] 링크나 이미지 URL에 넣을 수 없는 스킴($scr_scheme)"
done
[ ! -e "$SCR_WP/wp-case.md" ] && pass "md_to_wordpress: nothing is written for a refused scheme" \
    || fail "md_to_wordpress: nothing is written for a refused scheme" "file written"
scr_wp_case $'# T\n\n[z](mailto:a@example.com) [r](../doc.html#x) [h](#anchor)'
assert_eq "md_to_wordpress: mailto, a relative path and an anchor are accepted" "0" "$SCR_RC"
assert_contains "md_to_wordpress: relative link kept" "$SCR_HTML" '<a href="../doc.html#x">r</a>'
# A fence whose info string has a space after the language
scr_wp_case $'# T\n\n```bash title="x"\necho **a**\n```\n\n문단입니다.\n\n```json\n{"a": 1}\n```'
assert_contains "md_to_wordpress: the first word of the info string is the language; the code is not read as Markdown" \
    "$SCR_HTML" '<pre><code class="lang-bash">echo **a**</code></pre>'
assert_contains "md_to_wordpress: the paragraph after that block is a paragraph" "$SCR_HTML" "<p>문단입니다.</p>"
assert_contains "md_to_wordpress: the next block keeps its own language" "$SCR_HTML" '<pre><code class="lang-json">{"a": 1}</code></pre>'
# Lists: a change of marker kind starts another list, and no item is lost when the indent steps back
scr_wp_case $'# T\n\n1. a\n2. b\n\n- c\n- d'
assert_contains "md_to_wordpress: an ordered list followed by a bulleted one are two lists" "$SCR_HTML" "<ol>
<li>a</li>
<li>b</li>
</ol>

<ul>
<li>c</li>
<li>d</li>
</ul>"
scr_wp_case $'# T\n\n  - a\n- b\n- c'
for scr_item in a b c; do
    assert_contains "md_to_wordpress: item $scr_item survives a first item that is indented further" "$SCR_HTML" "<li>$scr_item</li>"
done
# A second paragraph of a list item takes its indented lines only
scr_wp_case $'# T\n\n## 1. 절차\n\n1. 첫 항목\n\n   둘째 문단\n### 1.1 제목\n\n2. 다음\n\n   문단 줄\n   ```bash\n   echo 1\n   ```'
assert_eq "md_to_wordpress: a heading or a fence right below an item's second paragraph converts" "0" "$SCR_RC"
assert_contains "md_to_wordpress: the second paragraph stays in its item" "$SCR_HTML" "<li>첫 항목
<p>둘째 문단</p>
</li>"
assert_contains "md_to_wordpress: the heading below it is a heading" "$SCR_HTML" "<h3>1.1 제목</h3>"
assert_contains "md_to_wordpress: the list that goes on keeps its number, with the paragraph and the code in the item" "$SCR_HTML" "<ol start=\"2\">
<li>다음
<p>문단 줄</p>
<pre><code class=\"lang-bash\">echo 1</code></pre>
</li>"
# Headings, emphasis and images
scr_wp_case $'# T\n\n## 2. 예제: C#\n\n## 3. 닫는 표시 ##\n\n*기울임*은 되고 a*b*c 는 그대로이며 [w](https://a.example/s3:*) 는 *주의*입니다.'
assert_contains "md_to_wordpress: a # at the end of a word stays in the heading" "$SCR_HTML" "<h2>2. 예제: C#</h2>"
assert_contains "md_to_wordpress: a closing ## after a space is dropped" "$SCR_HTML" "<h2>3. 닫는 표시</h2>"
assert_contains "md_to_wordpress: italic before a Korean particle; a*b*c and a * inside a URL are left alone" "$SCR_HTML" \
    '<p><em>기울임</em>은 되고 a*b*c 는 그대로이며 <a href="https://a.example/s3:*">w</a> 는 <em>주의</em>입니다.</p>'
scr_wp_case $'# T\n\n![요약](images/wp-fig01-arch.png) 출처: [문서](https://a.example/doc)\n\n![구성도 [1] 요약](images/wp-fig01-arch.png)'
assert_eq "md_to_wordpress: an image followed by text, and brackets in an alt text, convert" "0" "$SCR_RC"
assert_contains "md_to_wordpress: the image and the link after it are two things" "$SCR_HTML" \
    '<p><img src="images/wp-fig01-arch.png" alt="요약" /> 출처: <a href="https://a.example/doc">문서</a></p>'
assert_contains "md_to_wordpress: brackets inside an alt text" "$SCR_HTML" 'alt="구성도 [1] 요약"'
# Tables, the byte-order mark, line endings
scr_wp_case $'# T\n\n| a | b |\n|---|---|\n| 1 | 2 | 3 |'
assert_contains "md_to_wordpress: reports a row with more cells than the header" "$SCR_OUT" "[!] 머리 행보다 칸이 많은 표 행"
assert_eq "md_to_wordpress: the extra cell is left out" "2" "$(grep -c '<td ' "$SCR_WP/wp-case.md")"
printf '\xef\xbb\xbf---\ntitle: "T"\nslug: bom-slug\n---\n\n본문\n' > "$SCR_WP/2026-02-03-case.md"
scr_wp "$SCR_WP/2026-02-03-case.md" --out "$SCR_WP/wp-case.md"
assert_contains "md_to_wordpress: frontmatter after a byte-order mark is read" "$(cat "$SCR_WP/wp-case.md")" "추천 URL slug: bom-slug (프론트매터 slug)"
assert_not_contains "md_to_wordpress: frontmatter after a byte-order mark is not body text" "$(cat "$SCR_WP/wp-case.md")" "title:"
scr_wp "$SCR_WP/2026-02-03-vpc-endpoint.md" --out "$SCR_WP/wp-lf.md"
assert_contains "md_to_wordpress: says when the slug comes from the file name" "$SCR_OUT" "[!] 프론트매터에 slug: 가 없어 파일 이름에서 만든 값을 썼다 (vpc-endpoint)"
mkdir -p "$SCR_WP/crlf" && ln -sfn ../images "$SCR_WP/crlf/images"
sed 's/$/\r/' "$SCR_WP/2026-02-03-vpc-endpoint.md" > "$SCR_WP/crlf/2026-02-03-vpc-endpoint.md"
scr_wp "$SCR_WP/crlf/2026-02-03-vpc-endpoint.md" --out "$SCR_WP/wp-crlf.md"
assert_eq "md_to_wordpress: CRLF line endings give the same page as LF" "$(cat "$SCR_WP/wp-lf.md")" "$(cat "$SCR_WP/wp-crlf.md")"
printf '# T\n\n```text\na\fb\n```\n' > "$SCR_WP/2026-02-03-case.md"
scr_wp "$SCR_WP/2026-02-03-case.md" --out "$SCR_WP/wp-case.md"
assert_eq "md_to_wordpress: a form feed inside a code block is not a line break" "1" "$(grep -c "$(printf 'a\fb')" "$SCR_WP/wp-case.md")"

cat > "$TEST_TMP/review-metrics.md" <<'EOF'
# 제목

"이 문장은 마흔 글자를 넘기려고 일부러 길게 적은 인용문이며 조어가 아닙니다 정말입니다"라고 말했고, 담당자는 "S3"라고 답했습니다. 그리고 "가" 또는 "나"를 고릅니다. 아쉽게도 부적절한 값은 비효율적으로 처리됩니다.

응답은 < 100 ms 입니다. 요청은 > 1,000 건입니다. 셋째 문장입니다. (넷째 문장입니다.) 다섯째 문장입니다. 여섯째 문장입니다.

```text
```bash 는 코드 안의 글자입니다
```

- 게이트웨이 엔드포인트를 만들면 프라이빗 서브넷의 라우팅 테이블이 바뀝니다 하나.
- 게이트웨이 엔드포인트를 만들면 프라이빗 서브넷의 라우팅 테이블이 바뀝니다 둘.
- 게이트웨이 엔드포인트를 만들면 프라이빗 서브넷의 라우팅 테이블이 바뀝니다 셋.

마지막 문단은 매우 쉽게 읽힙니다.
EOF
SCR_OUT=$(python3 -I "$SCR/redundancy_metrics.py" "$TEST_TMP/review-metrics.md" --restated 0 2>&1)
assert_contains "redundancy_metrics: the text between two quotations is not a quotation (a long one, 'S3', one-letter ones)" \
    "$SCR_OUT" "| 따옴표 조어 밀도 (1000자당) | 0.0 (0회) | ≤ 1.0 | -0 |"
assert_contains "redundancy_metrics: three sentences that share a phrase count twice, like a sentence repeated twice" \
    "$SCR_OUT" "| 문장 반복 (동일 또는 한글 공통 구절 20자) | 동일 0, 유사 2 | 0 | -16 |"
# Exactly six sentences: reading "< 100 ms 입니다. 요청은 >" as a tag, or not ending a sentence at ".)", leaves five
assert_contains "redundancy_metrics: a sentence that ends inside a bracket is a sentence; '< 100 ms ... > 1,000' is not a tag" \
    "$SCR_OUT" "| 6문장 이상 문단 | 1개 | 0 | -5 |"
assert_contains "redundancy_metrics: 아쉽게도, 부적절한 and 비효율적으로 are not stock words; a fence-like line inside a code block does not close it" \
    "$SCR_OUT" "- 상투어: 매우×1, 쉽게×1"

# check_gate.py: scores the rules cannot give, the compared posts, the total row, the pasted metrics, the draft
scr_write_gate "$SCR_G" 90 100 100 100 100 100
sed -i 's#^| 정합성 | 90 | 80 |#| 정합성 | 95 | 80 |#; s/^### 정합성 (90)/### 정합성 (95)/' "$SCR_G"; scr_gate
assert_eq "check_gate: a score the rules cannot give exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names the score and the values that are possible" "$SCR_OUT" "정합성 점수 95: 채점 규칙으로 나올 수 없는 값 (나올 수 있는 값: 0, 10, 20"
scr_write_gate "$SCR_G" 100 83 100 100 100 100; scr_gate
assert_eq "check_gate: 구조 완결성 83 (five of six items, one not applicable) is a score the rules give" "0" "$SCR_RC"
scr_write_gate "$SCR_G"; sed -i '/example\.com\/post-3/d' "$SCR_G"; scr_gate
assert_eq "check_gate: fewer than three compared posts exit 1" "1" "$SCR_RC"
assert_contains "check_gate: counts the URLs" "$SCR_OUT" "'### 차별성과 근거'에 비교한 글의 URL 2개"
scr_write_gate "$SCR_G" 100 100 100 100 100 30; sed -i 's#\*\*반려\*\* |$#**반려 (가독성 미달)** |#' "$SCR_G"; scr_gate
assert_eq "check_gate: the total row may name the criterion that is below its minimum (exit 3)" "3" "$SCR_RC"
scr_write_gate "$SCR_G" 100 100 100 100 100 30; sed -i 's#\*\*반려\*\* |$#**반려 (정합성 미달)** |#' "$SCR_G"; scr_gate
assert_eq "check_gate: a total row that names a criterion that passed exits 1" "1" "$SCR_RC"
assert_contains "check_gate: names that criterion" "$SCR_OUT" "총점 행에 적은 '정합성': 최저선에 못 미친 기준이 아님"
scr_write_gate "$SCR_G" 100 100 100 90 100 100; sed -i 's/^재진술 2건: -10$/재진술 1건: -5/' "$SCR_G"; scr_gate
assert_eq "check_gate: a criterion 4 score that is not the script score minus the restatements exits 1" "1" "$SCR_RC"
assert_contains "check_gate: shows the subtraction" "$SCR_OUT" "기준 4 점수 90: 점수 100에서 재진술 1건(1건 5점)을 빼면 95"
scr_write_gate "$SCR_G"; sed -i 's/^| 보일러플레이트 문단 반복 | 0회 | 0 | -0 |$/| 보일러플레이트 문단 반복 | 3회 | 0 | -18 |/' "$SCR_G"; scr_gate
assert_eq "check_gate: a script score that is not 100 minus the penalties of its table exits 1" "1" "$SCR_RC"
assert_contains "check_gate: shows the sum" "$SCR_OUT" "지표 원본의 점수 100: 표의 감점을 100에서 빼면 82"
scr_write_gate "$SCR_G"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" --draft "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "check_gate --draft: the report of this draft passes" "0" "$SCR_RC"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" --draft "$TEST_TMP/redundant.md" 2>&1); SCR_RC=$?
assert_eq "check_gate --draft: the report of another draft exits 1" "1" "$SCR_RC"
assert_contains "check_gate --draft: names both drafts" "$SCR_OUT" "지표 원본은 '$SCR_SLUG.md'의 것: 이 원고는 'redundant.md'"
mkdir -p "$TEST_TMP/stale"
{ cat "$SCR_MD"; printf '\n샘플 구성은 서브넷 두 개로 시작합니다. 이 문단은 채점한 뒤에 더한 문단입니다.\n\n샘플 구성은 서브넷 두 개로 시작합니다. 이 문단은 채점한 뒤에 더한 문단입니다.\n'; } \
    | awk '/^## 저자 소개/{hold=1} hold{buf=buf $0 "\n"; next} {print} END{printf "%s", buf}' > "$TEST_TMP/stale/$SCR_SLUG.md"
sed -i '/^## 참고 자료/,$d' "$TEST_TMP/stale/$SCR_SLUG.md"
printf '\n샘플 구성은 서브넷 두 개로 시작합니다. 이 문단은 채점한 뒤에 더한 문단입니다.\n\n샘플 구성은 서브넷 두 개로 시작합니다. 이 문단은 채점한 뒤에 더한 문단입니다.\n' >> "$TEST_TMP/stale/$SCR_SLUG.md"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" --draft "$TEST_TMP/stale/$SCR_SLUG.md" 2>&1); SCR_RC=$?
assert_eq "check_gate --draft: a draft that changed after the scoring exits 1" "1" "$SCR_RC"
assert_contains "check_gate --draft: shows the score measured now" "$SCR_OUT" "지표 원본의 점수 100: 지금 원고를 재면 94"
{ printf '\xef\xbb\xbf'; cat "$SCR_G"; } > "$TEST_TMP/gate-bom.md"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$TEST_TMP/gate-bom.md" 2>&1); SCR_RC=$?
assert_eq "check_gate: a report that starts with a byte-order mark is read" "0" "$SCR_RC"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" --draft 2>&1); SCR_RC=$?
assert_eq "check_gate: --draft without a file exits 2" "2" "$SCR_RC"
SCR_OUT=$(python3 -I "$SCR/check_gate.py" "$SCR_G" --draft "$TEST_TMP/no-such-draft.md" 2>&1); SCR_RC=$?
assert_eq "check_gate: --draft with a missing file exits 2" "2" "$SCR_RC"

# package_blog.sh: the slug is a file name, other image types travel, a failed run leaves nothing, a stale report stops
SCR_PK="$TEST_TMP/pk"
mkdir -p "$SCR_PK/w/drafts" "$SCR_PK/w/images" "$SCR_PK/w/notes"
scr_write_draft "$SCR_PK/w/notes.md"; echo keep > "$SCR_PK/w/notes/important.txt"
SCR_OUT=$(bash "$SCR/package_blog.sh" --no-gate "$SCR_PK/w" ../notes 2>&1); SCR_RC=$?
assert_eq "package_blog: a slug with a path in it exits 2" "2" "$SCR_RC"
assert_contains "package_blog: says the slug is not a file name" "$SCR_OUT" "slug is not a plain file name"
assert_file_exists "package_blog: a path in the slug deletes nothing outside the out folder" "$SCR_PK/w/notes/important.txt"
[ ! -e "$SCR_PK/w/notes.zip" ] && [ ! -d "$SCR_PK/w/out" ] && pass "package_blog: a path in the slug writes nothing" \
    || fail "package_blog: a path in the slug writes nothing" "$(ls "$SCR_PK/w")"
ln -sfn ../images "$SCR_W/drafts/images"
printf 'jpg' > "$SCR_W/images/fixture-fig01-arch.jpg"
sed -i 's#images/fixture-fig01-arch.png#images/fixture-fig01-arch.jpg#' "$SCR_MD"
scr_write_gate "$SCR_W/gate-report.md"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a draft with a jpg image is packaged" "0" "$SCR_RC"
assert_contains "package_blog: the jpg is in the zip" "$(unzip -Z1 "$SCR_W/out/$SCR_SLUG.zip" 2>/dev/null | tr '\n' ' ')" "$SCR_SLUG/images/fixture-fig01-arch.jpg"
assert_contains "package_blog: the jpg is among the deliverables" "$SCR_OUT" "  $SCR_W/out/$SCR_SLUG/images/fixture-fig01-arch.jpg"
# The report was written before the draft changed: the metrics measured on the bundle differ from the pasted ones
printf '\n샘플 구성은 서브넷 두 개로 시작합니다. 채점한 뒤에 더한 문단입니다.\n\n샘플 구성은 서브넷 두 개로 시작합니다. 채점한 뒤에 더한 문단입니다.\n' > "$TEST_TMP/added.txt"
awk -v add="$TEST_TMP/added.txt" '/^## 2\. 마치며/{while ((getline l < add) > 0) print l; print ""} {print}' "$SCR_MD" > "$SCR_MD.tmp" && mv "$SCR_MD.tmp" "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: a report written before the draft changed exits 1" "1" "$SCR_RC"
assert_contains "package_blog: says to measure again" "$SCR_OUT" "지금 원고를 재면"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && [ ! -d "$SCR_W/out/$SCR_SLUG" ] && pass "package_blog: a failed run leaves no zip and no assembled folder" \
    || fail "package_blog: a failed run leaves no zip and no assembled folder" "$(ls "$SCR_W/out")"
assert_file_exists "package_blog: a failed run still leaves other files in out/ alone" "$SCR_W/out/keep.txt"
rm -f "$SCR_W/images/fixture-fig01-arch.jpg" "$SCR_W/gate-report.md" "$SCR_W/drafts/images"
scr_write_draft "$SCR_MD"

# --- None of the above wrote into the shipped skill folder ---
assert_eq "scripts left no generated files in skills/ (caches, images, out, zips)" "" \
    "$(find skills \( -name __pycache__ -o -name '*.pyc' -o -name '*.zip' -o -type d -name images -o -type d -name out \) -print | tr '\n' ' ')"

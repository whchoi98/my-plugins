#!/bin/bash
# kor-deslop skill invariants (sourced by tests/run-all.sh), ported from the kor-writing repo:
# pattern table integrity, one pattern count everywhere it is quoted, description triggers, sections,
# the change-rate snippet, and the humanize-korean license notice.

KD_SKILL=skills/kor-deslop/SKILL.md
KD_PATTERNS=skills/kor-deslop/references/patterns.md
KD_NOTICE=third_party/NOTICE-kor-deslop.md
KD_BODY=$(cat "$KD_SKILL" 2>/dev/null)

# --- Pattern table integrity ---
# A-J rows carry a severity (S1-S3); K rows are writer principles without one. The total is A-J + K.
KD_AJ=$(grep -cE '^\| [A-J]-[0-9]+ \|' "$KD_PATTERNS" || true)
KD_AJ_SEV=$(grep -cE '^\| [A-J]-[0-9]+ \| S[123] \|' "$KD_PATTERNS" || true)
KD_K=$(grep -cE '^\| K-[0-9]+ \|' "$KD_PATTERNS" || true)
KD_TOTAL=$((KD_AJ + KD_K))
[ "$KD_TOTAL" -gt 0 ] && pass "patterns.md: $KD_TOTAL patterns ($KD_AJ in A-J, $KD_K in K)" \
    || fail "patterns.md: pattern rows found" "no '| X-N |' rows in $KD_PATTERNS"
assert_eq "every A-J pattern has severity S1-S3" "$KD_AJ" "$KD_AJ_SEV"
assert_eq "K principles carry no severity" "0" "$(grep -cE '^\| K-[0-9]+ \| S[123] \|' "$KD_PATTERNS" || true)"
assert_eq "pattern IDs are unique" "" \
    "$(grep -oE '^\| [A-K]-[0-9]+ ' "$KD_PATTERNS" | tr -d '| ' | sort | uniq -d | tr '\n' ' ')"
assert_eq "A-17 stays reserved (no row)" "0" "$(grep -cE '^\| A-17 \|' "$KD_PATTERNS" || true)"
for kd_cat in A B C D E F G H I J K; do
    grep -qE "^## ${kd_cat}\. " "$KD_PATTERNS" && pass "patterns.md: category $kd_cat present" \
        || fail "patterns.md: category $kd_cat present" "heading '## $kd_cat. ' not found"
done
KD_MISPLACED=$(awk '/^## [A-K]\. /{cat=substr($2,1,1)} /^\| [A-K]-[0-9]+ \|/{split($2,id,"-"); if (id[1]!=cat) printf "%s ", $2}' "$KD_PATTERNS")
assert_eq "every pattern sits under its own category" "" "$KD_MISPLACED"
grep -qF "## 장르별 허용과 금기" "$KD_PATTERNS" && pass "patterns.md: genre table present" \
    || fail "patterns.md: genre table present" "missing"
# Pattern IDs cited in prose (SKILL.md procedure, cross-references inside patterns.md) must exist as rows
KD_IDS=$(grep -oE '^\| [A-K]-[0-9]+ ' "$KD_PATTERNS" | tr -d '| ' | sort -u)
KD_DANGLING=""
for kd_id in $(grep -ohE '\b[A-K]-[0-9]+\b' "$KD_SKILL" <(grep -vE '^\| [A-K]-[0-9]+ \|' "$KD_PATTERNS") | sort -u); do
    [ "$kd_id" = "A-17" ] && continue
    printf '%s\n' "$KD_IDS" | grep -qx -- "$kd_id" || KD_DANGLING+=" $kd_id"
done
assert_eq "pattern IDs cited in SKILL.md and patterns.md prose exist" "" "${KD_DANGLING# }"

# --- The pattern count is the same everywhere it is quoted ---
KD_README=$(cat README.md)
KD_README_EN=$(sed -n '/<a id="english"><\/a>/,/<a id="korean"><\/a>/p' README.md)
KD_README_KO=$(sed -n '/<a id="korean"><\/a>/,$p' README.md)
assert_contains "count: README English says '${KD_TOTAL} patterns'" "$KD_README_EN" "${KD_TOTAL} patterns"
assert_contains "count: README Korean says '패턴 ${KD_TOTAL}개'" "$KD_README_KO" "패턴 ${KD_TOTAL}개"
assert_contains "count: skills/CLAUDE.md says '${KD_TOTAL} patterns'" "$(cat skills/CLAUDE.md)" "${KD_TOTAL} patterns"
assert_contains "count: CLAUDE.md convention says '(${KD_TOTAL})'" "$(cat CLAUDE.md)" "pattern count (${KD_TOTAL})"
# No other count may be quoted anywhere these files talk about kor-deslop patterns
KD_STALE=$(grep -noE '[0-9]+ patterns|패턴 [0-9]+개|[0-9]+개 패턴' README.md skills/CLAUDE.md "$KD_SKILL" "$KD_PATTERNS" 2>/dev/null \
    | grep -vE "(^|[^0-9])${KD_TOTAL} patterns|패턴 ${KD_TOTAL}개|(^|[^0-9])${KD_TOTAL}개 패턴" | tr '\n' ' ')
assert_eq "count: no conflicting pattern count in README, skills/CLAUDE.md, SKILL.md, patterns.md" "" "$KD_STALE"
if printf '%s\n' "$KD_BODY" | grep -qE '[0-9]+ patterns|패턴 [0-9]+개|[0-9]+개 패턴'; then
    pass "count: SKILL.md quotes the pattern count"
else
    skip "count: SKILL.md quotes the pattern count ($KD_TOTAL)" "SKILL.md states no count, only the conflict check applies"
fi

# --- Skill text ---
KD_DESC=$(sed -n '2,/^---$/s/^description: //p' "$KD_SKILL" | head -1)
assert_contains "kor-deslop: description keeps trigger phrase" "$KD_DESC" "윤문해줘"
assert_contains "kor-deslop: description keeps check-only trigger" "$KD_DESC" "점검만 해줘"
assert_contains "kor-deslop: description keeps exclusions" "$KD_DESC" "맞춤법만"
for kd_section in "우선순위" "의미 보존 규칙" "절차" "자체 점검" "결과 전달" "출처"; do
    assert_contains "kor-deslop: section '$kd_section'" "$KD_BODY" "## $kd_section"
done
assert_contains "kor-deslop: points to references/patterns.md" "$KD_BODY" "references/patterns.md"
assert_contains "kor-deslop: points to its notice under third_party/" "$KD_BODY" "$KD_NOTICE"

# The change-rate one-liner in SKILL.md must actually run
KD_SNIPPET=$(grep -m1 -oP '^\s*\Kpython3 -c ".*difflib.*" before\.txt after\.txt' "$KD_SKILL" || true)
if [ -z "$KD_SNIPPET" ]; then
    fail "kor-deslop: change-rate snippet found" "python3 difflib one-liner missing from SKILL.md"
else
    mkdir -p "$TEST_TMP/kd"
    printf '데이터를 논의했다.\n' > "$TEST_TMP/kd/before.txt"
    cp "$TEST_TMP/kd/before.txt" "$TEST_TMP/kd/after.txt"
    assert_eq "kor-deslop: change-rate snippet reports 0.0% for identical text" "0.0%" \
        "$(cd "$TEST_TMP/kd" && bash -c "$KD_SNIPPET" 2>&1)"
    printf '완전히 다른 문장으로 바꿨다.\n' > "$TEST_TMP/kd/after.txt"
    KD_RATE=$(cd "$TEST_TMP/kd" && bash -c "$KD_SNIPPET" 2>&1)
    [[ "$KD_RATE" =~ ^[0-9]+\.[0-9]%$ && "$KD_RATE" != "0.0%" ]] && pass "kor-deslop: change-rate snippet reports a change ($KD_RATE)" \
        || fail "kor-deslop: change-rate snippet reports a change" "got '$KD_RATE'"
fi

# --- License notice for the derived pattern set ---
KD_NOTICE_TEXT=$(cat "$KD_NOTICE" 2>/dev/null)
assert_contains "notice: names humanize-korean" "$KD_NOTICE_TEXT" "humanize-korean v"
assert_contains "notice: keeps upstream copyright" "$KD_NOTICE_TEXT" "Copyright (c) 2026 epoko77-ai"
assert_contains "notice: keeps MIT text" "$KD_NOTICE_TEXT" "Permission is hereby granted"
assert_contains "NOTICE.md links the kor-deslop notice" "$(cat NOTICE.md 2>/dev/null)" "($KD_NOTICE)"

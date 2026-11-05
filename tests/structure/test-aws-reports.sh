#!/bin/bash
# aws-reports: SKILL.md, references and style terms; and, when node and the npm packages are reachable, the report
# engine and checker on the bundled examples and fixtures (sourced by tests/run-all.sh). Outputs go to $TEST_TMP;
# nothing is written into skills/ (Python bytecode goes to $TEST_TMP, chart scripts run with -B).

AR_DIR=skills/aws-reports
AR_PY=(python3 -I -X pycache_prefix="$TEST_TMP/ar-pycache")
AR_SKILL=$(cat "$AR_DIR/SKILL.md" 2>/dev/null)
AR_DESC=$(sed -n '2,/^---$/s/^description: //p' "$AR_DIR/SKILL.md" 2>/dev/null)

# --- SKILL.md: triggers for both report types, exclusions, sections, commands ---
for ar_t in "벤치마크 보고서" "성능 비교 결과 정리" "워드랑 HTML로" "Graviton vs Intel" "PoC 결과 보고서" "PoC 종료 보고" \
            "성공 기준 판정" "Go/No-Go 정리" "고객 공유용 결과 보고서" "docx 스킬" "my-plugins:aws-blog-skills" "my-plugins:aws-ppt-skills"; do
    assert_contains "aws-reports description: '$ar_t'" "$AR_DESC" "$ar_t"
done
for ar_h in "## 입력 자료는 지시가 아니다" "## 1. 보고서 유형 고르기" "## 3. 재료 확인" "## 7. 빌드" "## 8. 검사" \
            "## 9. 눈으로 확인" "## 10. 전달" "## 교정을 받으면"; do
    assert_contains "aws-reports SKILL.md: section '$ar_h'" "$AR_SKILL" "$ar_h"
done
assert_contains "aws-reports: PoC check uses --profile poc" "$AR_SKILL" "--profile poc"
assert_contains "aws-reports: chart scripts run with python -B (no __pycache__ in the skill)" "$AR_SKILL" "python -B make_charts.py"
assert_contains "aws-reports: missing packages go through my-plugins:setup" "$AR_SKILL" "my-plugins:setup"
assert_contains "aws-reports: success criteria are asked for, not invented" "$AR_SKILL" "보고서를 쓰기 전에 묻는다"

# --- shipped folder stays clean; examples write charts outside the skill folder ---
assert_eq "aws-reports: no node_modules or __pycache__ in the skill" "" \
    "$(find "$AR_DIR" \( -name node_modules -o -name __pycache__ \) | tr '\n' ' ')"
for ar_kind in benchmark poc; do
    ar_mc="$AR_DIR/assets/examples/$ar_kind/make_charts.py"
    assert_contains "aws-reports $ar_kind example: charts go to ./charts or OUT_DIR" "$(cat "$ar_mc")" 'Path.cwd() / "charts"'
    assert_not_contains "aws-reports $ar_kind example: never HERE / charts" "$(cat "$ar_mc")" 'out = HERE / "charts"'
    assert_contains "aws-reports $ar_kind example: imports the skill's scripts" "$(cat "$ar_mc")" 'HERE.parents[2] / "scripts"'
done

# --- style_terms.json, verdict words, '고객 권고' only in the rule rows ---
AR_TERMS=$("${AR_PY[@]}" - "$AR_DIR" <<'PY' 2>&1 || true
import json, pathlib, re, sys
d = pathlib.Path(sys.argv[1])
terms = json.loads((d / "scripts/style_terms.json").read_text(encoding="utf-8"))["terms"]
bad = []
for t in terms:
    try:
        re.compile(t["pattern"])
    except re.error as e:
        bad.append("bad regex %r: %s" % (t["pattern"], e))
    if not set(t.get("profiles", ["benchmark"])) <= {"benchmark", "poc"}:
        bad.append("unknown profile in %r" % t["pattern"])
    if not t.get("use"):
        bad.append("no 'use' for %r" % t["pattern"])
if not any(re.search(t["pattern"], "> **고객 권고**") for t in terms):
    bad.append("no term flags '고객 권고'")
words = ["충족", "부분 충족", "미충족", "측정하지 않음"]
check = (d / "scripts/check_report.py").read_text(encoding="utf-8")
chart = (d / "scripts/chart_style.py").read_text(encoding="utf-8")
rules = (d / "references/poc-verdict-rules.md").read_text(encoding="utf-8")
for w in words:
    if w not in re.search(r"VERDICT_WORD = re\.compile\((.*)\)", check).group(1):
        bad.append("check_report VERDICT_WORD lacks %s" % w)
    if '"%s"' % w not in chart:
        bad.append("chart_style VERDICT_COLOR lacks %s" % w)
    if "| %s |" % w not in rules:
        bad.append("poc-verdict-rules table lacks %s" % w)
for f in sorted(d.rglob("*.md")):
    for no, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
        if "고객 권고" in line and not re.search(r'"고객 권고"', line):
            bad.append("%s:%d still uses 고객 권고" % (f, no))
print("\n".join(bad))
PY
)
assert_eq "aws-reports: style terms compile, profiles known, verdict words agree, no stale '고객 권고'" "" "$AR_TERMS"

# --- setup checks the report dependencies (check mode only, scratch HOME, offline) ---
AR_SETUP_HOME="$TEST_TMP/ar-setup-home"; mkdir -p "$AR_SETUP_HOME"
AR_SETUP=$(cd "$TEST_TMP" && env HOME="$AR_SETUP_HOME" UV_OFFLINE=1 bash "$PROJECT_ROOT/skills/setup/scripts/setup.sh" 2>&1 || true)
assert_contains "setup.sh check: has the aws-reports group" "$AR_SETUP" "== 보고서 (aws-reports)"
for ar_item in "NanumSquareOTF Regular" docx marked docx-preview jszip; do
    printf '%s\n' "$AR_SETUP" | grep -qE "^  \[(ok|miss)\] +${ar_item} " && pass "setup.sh check: reports '$ar_item'" \
        || fail "setup.sh check: reports '$ar_item'" "no [ok]/[miss] line for $ar_item"
done
AR_PINS=$(sed -n 's/^REPORT_NPM=(\(.*\))$/\1/p' skills/setup/scripts/setup.sh)
assert_eq "setup.sh REPORT_NPM pins the four report packages" "docx@9.15.1 marked@18.1.1 docx-preview@0.4.1 jszip@3.10.1" "$AR_PINS"
for ar_pin in $AR_PINS; do
    assert_contains "setup SKILL.md names the pinned ${ar_pin%@*} version" "$(cat skills/setup/SKILL.md)" "${ar_pin%@*} ${ar_pin#*@}"
done

# --- engine: only when node and the npm packages are reachable ---
AR_ROOT=""
if command -v node >/dev/null 2>&1; then
    for ar_r in $(printf '%s' "${NODE_PATH:-}" | tr ':' ' ') $(npm root -g 2>/dev/null); do
        if [ -f "$ar_r/docx/package.json" ] && [ -f "$ar_r/marked/package.json" ]; then AR_ROOT="$ar_r"; break; fi
    done
fi
if [ -z "$AR_ROOT" ]; then
    skip "aws-reports engine tests" "node, docx or marked not reachable (NODE_PATH, npm root -g); run my-plugins:setup install"
else
    AR_NODE=(env NODE_PATH="$AR_ROOT" node "$AR_DIR/scripts/report.mjs")
    for ar_kind in benchmark poc; do
        AR_LOG=$("${AR_NODE[@]}" "$AR_DIR/assets/examples/$ar_kind/example.md" --out-dir "$TEST_TMP/ar-$ar_kind" 2>&1); AR_RC=$?
        assert_eq "aws-reports $ar_kind example: report.mjs exits 0" "0" "$AR_RC"
        assert_contains "aws-reports $ar_kind example: no converter warnings" "$AR_LOG" "warnings=0"
        AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-$ar_kind/example.docx" "$TEST_TMP/ar-$ar_kind/example.html" \
                 --profile "$ar_kind" 2>&1); AR_RC=$?
        assert_eq "aws-reports $ar_kind example: check_report --profile $ar_kind exits 0" "0" "$AR_RC"
        assert_eq "aws-reports $ar_kind example: both files OK (no ERROR, no WARN)" "2" "$(printf '%s\n' "$AR_OUT" | grep -c '^   OK$')"
    done
    AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-poc/example.docx" --profile benchmark 2>&1)
    assert_contains "aws-reports: profiles differ (PoC example warns under benchmark)" "$AR_OUT" "첫 번째 섹션이 측정 환경"

    # Layout rules from the user's 2026-11-04 Word edits, on a fixture with 11-, 7-, 3-column and <br> tables
    "${AR_NODE[@]}" tests/fixtures/aws-reports-layout.md --out-dir "$TEST_TMP/ar-layout" >/dev/null 2>&1
    AR_LAYOUT=$("${AR_PY[@]}" - "$TEST_TMP/ar-layout/aws-reports-layout.docx" "$TEST_TMP/ar-layout/aws-reports-layout.html" <<'PY' 2>&1 || true
import re, sys, zipfile
doc = zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode()
html = open(sys.argv[2], encoding="utf-8").read()
tbls = re.findall(r"<w:tbl>.*?</w:tbl>", doc, re.S)
def head(t): return re.findall(r"<w:tc>.*?</w:tc>", re.findall(r"<w:tr[ >].*?</w:tr>", t, re.S)[0], re.S)
def centered(cells): return all('<w:jc w:val="center"/>' in c for c in cells)
h11, h7, h3, hbr = (head(t) for t in tbls[:4])
checks = [
    ("11-column table text 6.5 pt", set(re.findall(r'<w:sz w:val="(\d+)"/>', tbls[0])) <= {"13", "12"}),
    ("11-column headers centered", centered(h11)),
    ("7-column: unit on the second line", "<w:br/>" in h7[2] and ">On-Demand<" in h7[2]),
    ("7-column headers centered", centered(h7)),
    ("3-column headers keep column alignment", '<w:jc w:val="center"/>' not in "".join(h3) and '<w:jc w:val="right"/>' in h3[1]),
    ("<br> header splits and centers", "<w:br/>" in hbr[1] and centered(hbr)),
    ("html: same header splits", "On-Demand<br>(USD/시간)" in html and "JVM 사용<br>코어" in html),
    ("html: short note centered, long note not", '<p class="br-capnote one">짧은' in html and '<p class="br-capnote">아주 긴' in html),
]
print("\n".join(name for name, ok in checks if not ok))
PY
)
    assert_eq "aws-reports layout: header split and centering, wide-table size, caption-note alignment (Word, HTML)" "" "$AR_LAYOUT"

    # Negative checks: the checker catches an uncentered two-line header and a flipped caption note
    mkdir -p "$TEST_TMP/ar-neg/x" && cp "$TEST_TMP/ar-layout/aws-reports-layout.docx" "$TEST_TMP/ar-neg/n.docx"
    (cd "$TEST_TMP/ar-neg/x" && unzip -q ../n.docx word/document.xml 2>/dev/null) || true
    "${AR_PY[@]}" - "$TEST_TMP/ar-neg/x/word/document.xml" <<'PY' >/dev/null 2>&1 || true
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
i = s.index("<w:tbl>"); j = s.index("</w:tr>", i)
s = s[:i] + s[i:j].replace('<w:jc w:val="center"/>', '<w:jc w:val="left"/>') + s[j:]
k = s.index("짧은 주석"); a = max(s.rfind("<w:p>", 0, k), s.rfind("<w:p ", 0, k))
s = s[:a] + s[a:k].replace('<w:jc w:val="center"/>', "") + s[k:]
open(p, "w", encoding="utf-8").write(s)
PY
    (cd "$TEST_TMP/ar-neg/x" && zip -q ../n.docx word/document.xml 2>/dev/null) || true
    AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-neg/n.docx" 2>&1); AR_RC=$?
    assert_eq "aws-reports checker: broken Word layout exits 1" "1" "$AR_RC"
    assert_contains "aws-reports checker: reports the uncentered two-line header" "$AR_OUT" "two-line table header is not centered"
    assert_contains "aws-reports checker: reports the caption note alignment" "$AR_OUT" "caption note alignment"
    sed -e 's/<th class="ctr">인스턴스<\/th>/<th>인스턴스<\/th>/' -e 's/br-capnote one/br-capnote/' \
        "$TEST_TMP/ar-layout/aws-reports-layout.html" > "$TEST_TMP/ar-neg/n.html"
    AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-neg/n.html" 2>&1)
    assert_contains "aws-reports checker: html header rule" "$AR_OUT" "two-line table header is not centered"
    assert_contains "aws-reports checker: html caption note rule" "$AR_OUT" "caption note alignment class"

    # PoC wording and structure warnings on a deliberately bad draft
    "${AR_NODE[@]}" tests/fixtures/aws-reports-poc-bad.md --out-dir "$TEST_TMP/ar-bad" >/dev/null 2>&1
    AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-bad/aws-reports-poc-bad.docx" \
             "$TEST_TMP/ar-bad/aws-reports-poc-bad.html" --profile poc 2>&1)
    for ar_w in '판정 "PASS"' '판정 "거의 충족"' '용어 "PASS"' '용어 "성공적으로"' '용어 "고객 권고"' \
                '첫 번째 섹션이 PoC 개요가 아님' '성공 기준 섹션이 없음' '마지막 섹션이 종합 평가와 다음 단계가 아님' '전체 판정'; do
        assert_contains "aws-reports poc profile warns: $ar_w" "$AR_OUT" "$ar_w"
    done
    AR_OUT=$("${AR_PY[@]}" "$AR_DIR/scripts/check_report.py" "$TEST_TMP/ar-bad/aws-reports-poc-bad.docx" --profile benchmark 2>&1)
    assert_not_contains "aws-reports benchmark profile skips PoC-only terms" "$AR_OUT" '용어 "PASS"'
    assert_contains "aws-reports benchmark profile still warns 고객 권고" "$AR_OUT" '용어 "고객 권고"'

    # Package lookup: npm root -g of a scratch prefix (symlinks to the found packages), and the setup hint when nothing is found
    mkdir -p "$TEST_TMP/ar-npmg/lib/node_modules" "$TEST_TMP/ar-npm-empty"
    ln -s "$AR_ROOT/docx" "$TEST_TMP/ar-npmg/lib/node_modules/docx"
    ln -s "$AR_ROOT/marked" "$TEST_TMP/ar-npmg/lib/node_modules/marked"
    if [ -d "$(env npm_config_prefix="$TEST_TMP/ar-npmg" npm root -g 2>/dev/null)" ]; then
        AR_LOG=$(env -u NODE_PATH npm_config_prefix="$TEST_TMP/ar-npmg" node "$AR_DIR/scripts/report.mjs" \
                 "$AR_DIR/assets/examples/poc/example.md" --out-dir "$TEST_TMP/ar-npmg-out" --only html 2>&1); AR_RC=$?
        assert_eq "aws-reports: report.mjs finds packages through npm root -g (no NODE_PATH)" "0" "$AR_RC"
    else
        skip "aws-reports: npm root -g lookup" "npm masked the scratch prefix path (UUID-like name in TMPDIR)"
    fi
    AR_LOG=$(cd "$TEST_TMP" && env -u NODE_PATH npm_config_prefix="$TEST_TMP/ar-npm-empty" node "$PROJECT_ROOT/$AR_DIR/scripts/report.mjs" \
             "$PROJECT_ROOT/$AR_DIR/assets/examples/poc/example.md" --out-dir "$TEST_TMP/ar-none" 2>&1); AR_RC=$?
    assert_eq "aws-reports: missing packages exit 1" "1" "$AR_RC"
    assert_contains "aws-reports: missing packages point to the setup skill" "$AR_LOG" "my-plugins setup skill"
fi

# --- example charts: verdicts computed from data.json (uv with a cached matplotlib; never the network) ---
if command -v uv >/dev/null 2>&1 && (cd "$TEST_TMP" && UV_OFFLINE=1 uv run --quiet --no-project --with matplotlib python -c 'import matplotlib') >/dev/null 2>&1; then
    touch "$TEST_TMP/ar-before-charts"
    AR_LOG=$(cd "$TEST_TMP" && UV_OFFLINE=1 uv run --quiet --no-project --with matplotlib python -B \
             "$PROJECT_ROOT/$AR_DIR/assets/examples/poc/make_charts.py" "$TEST_TMP/ar-charts" 2>&1)
    assert_contains "aws-reports poc example: verdicts computed from data.json" "$AR_LOG" "필수 5개 중 충족 4개"
    assert_file_exists "aws-reports poc example: criteria chart written to OUT_DIR" "$TEST_TMP/ar-charts/chart-criteria.png"
    assert_eq "aws-reports poc example: nothing written into the skill folder" "" \
        "$(find "$AR_DIR" \( -name __pycache__ -o -newer "$TEST_TMP/ar-before-charts" \) -print | tr '\n' ' ')"
else
    skip "aws-reports example charts" "uv or a cached matplotlib is not available (tests stay offline)"
fi

#!/bin/bash
# html-report: SKILL.md, design-spec.md and the template agree; check_html.py and embed_images.py on the template
# and on copies in $TEST_TMP where each rule is broken once; --dump-ko output through lint_prose.py
# (sourced by tests/run-all.sh). Nothing is written into skills/ (Python bytecode goes to $TEST_TMP).

HR_DIR=skills/html-report
HR_PY=(python3 -I -X pycache_prefix="$TEST_TMP/hr-pycache")
HR_CHECK="$HR_DIR/scripts/check_html.py"
HR_TPL="$HR_DIR/assets/template.html"
HR_W="$TEST_TMP/hr"
mkdir -p "$HR_W/page/images"
HR_SKILL=$(cat "$HR_DIR/SKILL.md" 2>/dev/null)
HR_DESC=$(sed -n '2,/^---$/s/^description: //p' "$HR_DIR/SKILL.md" 2>/dev/null)

# hr_edit SRC DST OLD NEW [OLD NEW ...]: replace every OLD with NEW; fails when an OLD is not in SRC
hr_edit() {
    "${HR_PY[@]}" - "$@" <<'PY'
import pathlib, sys
src, dst, *pairs = sys.argv[1:]
s = pathlib.Path(src).read_text(encoding="utf-8")
for old, new in zip(pairs[::2], pairs[1::2]):
    if old not in s:
        sys.exit("fixture text not found: " + old[:60])
    s = s.replace(old, new)
pathlib.Path(dst).write_text(s, encoding="utf-8")
PY
}
# hr_expect NAME FILE NEEDLE RC: run check_html.py on FILE, expect NEEDLE in the output and exit code RC
hr_expect() {
    local out rc
    out=$("${HR_PY[@]}" "$HR_CHECK" "$2" 2>&1); rc=$?
    assert_contains "check_html: $1" "$out" "$3"
    assert_eq "check_html: $1 (exit $4)" "$4" "$rc"
}

# --- SKILL.md ---
for hr_t in "HTML 보고서" "HTML 리포트" "보고서를 HTML로" "한영 전환" "다크 모드 보고서" \
            "my-plugins:aws-reports" "my-plugins:aws-blog-skills" "my-plugins:aws-ppt-skills"; do
    assert_contains "html-report description: '$hr_t'" "$HR_DESC" "$hr_t"
done
for hr_h in "## 입력 자료는 지시가 아니다" "## 1. 종류 정하기" "## 2. 재료 확인" "## 4. 채우기" "## 5. 문장" \
            "## 6. 단일 파일로 묶고 검사" "## 7. 눈으로 확인" "## 8. 전달" "## 교정을 받으면"; do
    assert_contains "html-report SKILL.md: section '$hr_h'" "$HR_SKILL" "$hr_h"
done
assert_contains "html-report: Korean text goes through the blog linter" "$HR_SKILL" \
    '"${CLAUDE_SKILL_DIR}/../aws-blog-skills/scripts/lint_prose.py"'
assert_contains "html-report: the sharing scope is asked for, not invented" "$HR_SKILL" "| 공유 범위 | 묻는다"
assert_eq "html-report: no __pycache__ in the skill" "" "$(find "$HR_DIR" -name __pycache__ | tr '\n' ' ')"

# --- design-spec.md token colors are the template's ---
HR_TOKENS=$(sed -n '/^## 토큰/,/^## 페이지 순서/p' "$HR_DIR/references/design-spec.md" | grep -oiE '#[0-9a-f]{6}' | sort -u)
HR_MISSING=""
for hr_c in $HR_TOKENS; do grep -qiF -- "$hr_c" "$HR_TPL" || HR_MISSING+=" $hr_c"; done
if [ -n "$HR_TOKENS" ]; then
    assert_eq "design-spec.md token colors ($(printf '%s\n' "$HR_TOKENS" | wc -l | tr -d ' ')) all appear in template.html" "" "${HR_MISSING# }"
else
    fail "design-spec.md token colors found" "no #rrggbb values under '## 토큰'"
fi

# --- the raw template fails only on its placeholders ---
HR_OUT=$("${HR_PY[@]}" "$HR_CHECK" "$HR_TPL" 2>&1); HR_RC=$?
assert_contains "check_html: raw template reports its placeholders" "$HR_OUT" "템플릿 자리 표시가 남았다"
assert_eq "check_html: raw template has no finding besides placeholders" "" \
    "$(printf '%s\n' "$HR_OUT" | grep -E '^   (ERROR|WARN)' | grep -v '템플릿 자리 표시' || true)"
assert_eq "check_html: placeholders exit 1" "1" "$HR_RC"

# --- a filled copy passes; its Korean text passes lint_prose.py ---
# Fixed fills for the text the mutations below point at, then every other template sample sentence is broken
# (a "Q" after its second character) through the checker's own template_samples() list.
HR_FILL=("보고서 제목을 한 줄로 작성합니다" "S3 스토리지 클래스 비용 비교" "Write the report title on one line" "Comparing S3 storage class costs"
         "첫 번째 챕터 제목" "요금 구성" "두 번째 챕터 제목" "클래스별 비교" "First section title" "How pricing works"
         "Second section title" "Class by class"
         "요약 문단입니다. 이 보고서가 답하는 질문과 결론을 두세 문장으로 적습니다. 결론을 받치는 숫자가 있으면 결론 문장에 함께 적습니다."
         "S3 스토리지 클래스별 요금을 비교했습니다. 자주 읽지 않는 데이터는 Glacier 계열의 저장 비용이 가장 낮습니다."
         "This is the summary paragraph. State the question the report answers and its conclusion in two or three sentences. Put the number behind the conclusion in the same sentence."
         "This report compares S3 storage class prices. Data read rarely costs the least to store in the Glacier classes."
         "Source title as published" "Amazon S3 pricing" "example.com/source-" "aws.amazon.com/s3/pricing/#"
         "Placeholder figure" "Data flow" 'data-ko="보고서 제목"' 'data-ko="S3 비용 비교"'
         'data-en="Report title"' 'data-en="S3 cost comparison"' ">보고서 제목</title>" ">S3 비용 비교</title>")
HR_F="$HR_W/page/filled.html"
if hr_edit "$HR_TPL" "$HR_F" "${HR_FILL[@]}" && "${HR_PY[@]}" - "$HR_F" "$HR_DIR/scripts" <<'PY'
import pathlib, sys
sys.path.insert(0, sys.argv[2])
import check_html
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
sentences, short = check_html.template_samples()
for old in sorted(set(sentences) | short, key=len, reverse=True):
    s = s.replace(old, old[:2] + "Q" + old[2:])
p.write_text(s, encoding="utf-8")
PY
then
    HR_OUT=$("${HR_PY[@]}" "$HR_CHECK" "$HR_F" --dump-ko "$HR_W/filled.ko.md" 2>&1); HR_RC=$?
    assert_contains "check_html: filled template is OK" "$HR_OUT" "   OK"
    assert_eq "check_html: filled template exits 0" "0" "$HR_RC"
    HR_LINT=$(python3 -I skills/aws-blog-skills/scripts/lint_prose.py "$HR_W/filled.ko.md" 2>&1 || true)
    assert_contains "check_html --dump-ko: template Korean text has lint_prose HARD 0" "$HR_LINT" "hard_findings=0"
    HR_KO=$(cat "$HR_W/filled.ko.md")
    assert_contains "check_html --dump-ko: headings keep their level" "$HR_KO" "## 1. 요금 구성"
    assert_contains "check_html --dump-ko: includes the tab title" "$HR_KO" "S3 비용 비교"
    assert_not_contains "check_html --dump-ko: English text is left out" "$HR_KO" "How pricing works"

    # --- each rule fails once (mutation of the filled copy) ---
    hr_edit "$HR_F" "$HR_W/m-pair.html" '<span lang="en">Comparing S3 storage class costs</span>' '' \
        && hr_expect "missing English pair" "$HR_W/m-pair.html" '짝이 없다' 1
    hr_edit "$HR_F" "$HR_W/m-dot.html" '1. 요금 구성' '1. 요금·구성' \
        && hr_expect "middle dot in prose" "$HR_W/m-dot.html" '가운뎃점(·)를 쓰지 않는다' 1
    hr_edit "$HR_F" "$HR_W/m-arrow.html" 'Class by class' 'Class → class' \
        && hr_expect "arrow in English prose" "$HR_W/m-arrow.html" '화살표(→)를 쓰지 않는다' 1
    hr_edit "$HR_F" "$HR_W/m-attr.html" 'data-en="S3 cost comparison"' 'data-en="S3 cost — comparison"' \
        && hr_expect "dash in the English tab title" "$HR_W/m-attr.html" '엠 대시(—)를 쓰지 않는다' 1
    hr_edit "$HR_F" "$HR_W/m-sample.html" 'S3 스토리지 클래스별 요금을 비교했습니다.' '요약 문단입니다.' \
        && hr_expect "template sample sentence left in the summary" "$HR_W/m-sample.html" '(예시 문장): 요약 문단입니다.' 1
    hr_edit "$HR_F" "$HR_W/m-sample-li.html" '검색Q한 기간과 검색어를 적습니다.' '검색한 기간과 검색어를 적습니다.' \
        && hr_expect "template sample sentence left in a method item" "$HR_W/m-sample-li.html" '(예시 문장): 검색한 기간과 검색어를 적습니다.' 1
    hr_edit "$HR_F" "$HR_W/m-bar.html" '.callout>*{margin:0}' '.callout>*{margin:0}.callout{border-left:4px solid #1d5bb8}' \
        && hr_expect "left bar on the callout" "$HR_W/m-bar.html" 'border-left' 1
    hr_edit "$HR_F" "$HR_W/m-css.html" '</style>' '.wrap{max-width:900px}</style>' \
        && hr_expect "CSS appended to the template's style" "$HR_W/m-css.html" '<style>이 템플릿과 다르다' 1
    hr_edit "$HR_F" "$HR_W/m-inline.html" '<div class="callout">' '<div class="callout" style="border-left:4px solid red">' \
        && hr_expect "inline style attribute" "$HR_W/m-inline.html" '인라인 style을 쓰지 않는다' 1
    "${HR_PY[@]}" - "$HR_F" "$HR_W/m-script.html" <<'PY'
import pathlib, re, sys
s = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
pathlib.Path(sys.argv[2]).write_text(re.sub(r"<script>\s*\(function\(\)\{\s*var r=document\.documentElement,mq.*?</script>", "", s, flags=re.S), encoding="utf-8")
PY
    hr_expect "toggle script removed" "$HR_W/m-script.html" '<script>가 템플릿과 다르다' 1
    hr_edit "$HR_F" "$HR_W/m-token.html" '--accent:#1d5bb8' '--accent:#2255cc' \
        && hr_expect "changed light accent token" "$HR_W/m-token.html" '라이트 강조 #1d5bb8' 1
    hr_edit "$HR_F" "$HR_W/m-cap.html" '그림 1. ' '그림 3. ' \
        && hr_expect "figure caption out of sequence" "$HR_W/m-cap.html" '캡션은 "그림 1. "으로 시작한다' 1
    hr_edit "$HR_F" "$HR_W/m-cite.html" '<a href="#src-3">3</a>' '<a href="#src-9">9</a>' \
        && hr_expect "citation to a missing source" "$HR_W/m-cite.html" '출처 표에 없는 곳' 1
    hr_expect "uncited source warns" "$HR_W/m-cite.html" 'src-3: 본문에서 인용하지 않은 출처다' 1
    hr_edit "$HR_F" "$HR_W/m-mix.html" 'data-count="1"' 'data-count="2"' '블로그 1건' '블로그 2건' 'Blog posts: 1' 'Blog posts: 2' \
        && hr_expect "source mix count differs from the source table" "$HR_W/m-mix.html" '출처 구성 목록' 1
    hr_edit "$HR_F" "$HR_W/m-leak.html" '<td>128</td>' '<td>128개</td>' \
        && hr_expect "Korean text outside a language pair" "$HR_W/m-leak.html" '짝 밖에 있어 영어 화면에도 보인다' 1
    hr_edit "$HR_F" "$HR_W/m-order.html" '<section class="method" id="method">' '<section class="extra" id="method">' \
        && hr_expect "page order" "$HR_W/m-order.html" '순서가 규격과 다르다' 1
    hr_edit "$HR_F" "$HR_W/m-plain.html" '요금을 비교했습니다.' '요금을 비교했다.' \
        && hr_expect "한다체 sentence warns" "$HR_W/m-plain.html" '합쇼체가 아닌 문장' 0
    hr_edit "$HR_F" "$HR_W/m-yo.html" '요금을 비교했습니다.' '요금을 비교했어요.' \
        && hr_expect "해요체 sentence warns" "$HR_W/m-yo.html" '합쇼체가 아닌 문장' 0
    hr_edit "$HR_F" "$HR_W/m-li.html" '포함Q한 출처와 제외한 출처의 기준을 적습니다.' '포함한 출처와 제외한 출처의 기준을 적는다' \
        && hr_expect "한다체 list item without a period warns" "$HR_W/m-li.html" '합쇼체가 아닌 문장' 0
    hr_edit "$HR_F" "$HR_W/m-general.html" 'data-report="research"' 'data-report="general"' \
        && hr_expect "general report with every optional part is OK" "$HR_W/m-general.html" '   OK' 0
    "${HR_PY[@]}" - "$HR_W/m-general.html" "$HR_W/m-nosrc.html" <<'PY'
import pathlib, re, sys
s = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
s = re.sub(r'<section class="sources".*?</section>\s*', "", s, flags=re.S)
pathlib.Path(sys.argv[2]).write_text(s, encoding="utf-8")
PY
    hr_expect "general report with citations needs the source table" "$HR_W/m-nosrc.html" '인용 번호가 있는데 출처 표' 1

    # --- embed_images.py: relative image fails the check, embedding fixes it, paths outside are refused ---
    printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82' > "$HR_W/page/images/dot.png"
    HR_FIG='<figure class="fig fit"><div class="box"><img src="images/dot.png" alt="점" data-alt-en="Dot"></div><figcaption><span lang="ko">그림 2. 점</span><span lang="en">Figure 2. Dot</span></figcaption></figure><pre class="box">'
    if hr_edit "$HR_F" "$HR_W/page/img.html" '<pre class="box">' "$HR_FIG"; then
        hr_expect "relative image path" "$HR_W/page/img.html" '상대 경로 그림(images/dot.png)' 1
        HR_OUT=$("${HR_PY[@]}" "$HR_DIR/scripts/embed_images.py" "$HR_W/page/img.html" -o "$HR_W/out/img.html" 2>&1); HR_RC=$?
        assert_eq "embed_images: exits 0" "0" "$HR_RC"
        assert_contains "embed_images: reports one image" "$HR_OUT" "embedded 1 image(s)"
        assert_contains "embed_images: writes a data URI" "$(cat "$HR_W/out/img.html" 2>/dev/null)" 'src="data:image/png;base64,'
        hr_expect "embedded page is OK" "$HR_W/out/img.html" '   OK' 0
        printf 'secret' > "$HR_W/outside.png"
        hr_edit "$HR_W/page/img.html" "$HR_W/page/evil.html" 'images/dot.png' '../outside.png'
        HR_OUT=$("${HR_PY[@]}" "$HR_DIR/scripts/embed_images.py" "$HR_W/page/evil.html" -o "$HR_W/out/evil.html" 2>&1); HR_RC=$?
        assert_eq "embed_images: a path outside the page folder exits 1" "1" "$HR_RC"
        assert_contains "embed_images: says why it refused" "$HR_OUT" "outside the page folder"
        [ ! -e "$HR_W/out/evil.html" ] && pass "embed_images: nothing written when an image is refused" \
            || fail "embed_images: nothing written when an image is refused" "$HR_W/out/evil.html exists"
    else
        fail "html-report fixture with an image" "template text '<pre class=\"box\">' not found"
    fi
else
    fail "html-report: filled template fixture" "a text in HR_FILL is no longer in template.html, or template_samples() failed"
fi

HR_OUT=$("${HR_PY[@]}" "$HR_CHECK" "$HR_TPL" "$HR_TPL" --dump-ko "$HR_W/x.md" 2>&1); HR_RC=$?
assert_eq "check_html: --dump-ko with two files is a usage error (exit 2)" "2" "$HR_RC"

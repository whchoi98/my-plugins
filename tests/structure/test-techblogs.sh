#!/bin/bash
# techblogs: SKILL.md, design-spec.md, the template and the scripts agree; build_post.py, check_post.py,
# import_aws_post.py and place_post.py on the fixture in tests/fixtures/techblogs/, on copies in $TEST_TMP where
# each rule is broken once, and on a fake blog repository (sourced by tests/run-all.sh). No network and no
# Playwright: preview.py and place_post.py --build are not run. Nothing is written into skills/ (Python
# bytecode goes to $TEST_TMP, and the --out guard is tried on a copy of the skill).

TB_DIR=skills/techblogs
TB_PY=(python3 -I -X pycache_prefix="$TEST_TMP/tb-pycache")
TB_BUILD="$TB_DIR/scripts/build_post.py"
TB_CHECK="$TB_DIR/scripts/check_post.py"
TB_IMPORT="$TB_DIR/scripts/import_aws_post.py"
TB_PLACE="$TB_DIR/scripts/place_post.py"
TB_TPL="$TB_DIR/assets/template.html"
TB_SPEC="$TB_DIR/references/design-spec.md"
TB_FIX=tests/fixtures/techblogs
TB_SLUG=sample-batch-window
TB_W="$TEST_TMP/tb"
mkdir -p "$TB_W/bin"
TB_SKILL=$(cat "$TB_DIR/SKILL.md" 2>/dev/null)
TB_DESC=$(sed -n '2,/^---$/s/^description: //p' "$TB_DIR/SKILL.md" 2>/dev/null)
TB_FILES_BEFORE=$(find "$TB_DIR" | sort)

# tb_edit FILE OLD NEW [OLD NEW ...]: replace every OLD with NEW in FILE; an OLD that is not there is a failure
tb_edit() {
    local msg
    msg=$("${TB_PY[@]}" - "$@" 2>&1 <<'PY'
import pathlib, sys
path, *pairs = sys.argv[1:]
p = pathlib.Path(path)
s = p.read_text(encoding="utf-8")
for old, new in zip(pairs[::2], pairs[1::2]):
    if old not in s:
        sys.exit("text not found: " + old[:60])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
PY
    ) && return 0
    fail "techblogs fixture edit in $(basename "$1")" "$msg"
    return 1
}
# tb_resub FILE REGEX REPL: replace the first match (dot matches newlines); no match is a failure
tb_resub() {
    local msg
    msg=$("${TB_PY[@]}" - "$@" 2>&1 <<'PY'
import pathlib, re, sys
path, pattern, repl = sys.argv[1:]
p = pathlib.Path(path)
s, n = re.subn(pattern, repl, p.read_text(encoding="utf-8"), count=1, flags=re.S)
if not n:
    sys.exit("pattern not found: " + pattern[:60])
p.write_text(s, encoding="utf-8")
PY
    ) && return 0
    fail "techblogs fixture edit in $(basename "$1")" "$msg"
    return 1
}
# tb_work NAME: a fresh copy of the fixture work folder; sets TB_WK
tb_work() {
    TB_WK="$TB_W/w-$1"
    rm -rf "$TB_WK"; cp -a "$TB_FIX/work" "$TB_WK"
}
# tb_meta FILTER: rewrite meta.json of TB_WK with a jq filter
tb_meta() {
    jq "$1" "$TB_WK/meta.json" > "$TB_WK/meta.tmp" && mv "$TB_WK/meta.tmp" "$TB_WK/meta.json"
}
# tb_build_fails DESC NEEDLE [build args ...]: build TB_WK, expect NEEDLE in the output and exit 1
tb_build_fails() {
    local desc="$1" needle="$2" out rc; shift 2
    out=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" "$@" 2>&1); rc=$?
    assert_contains "build_post: $desc" "$out" "$needle"
    assert_eq "build_post: $desc (exit 1)" "1" "$rc"
}
# tb_case NAME: a fresh copy of the built output; sets TB_C (folder), TB_R (report) and TB_F (front matter file)
tb_case() {
    TB_C="$TB_W/c-$1"
    rm -rf "$TB_C"; cp -a "$TB_OUT" "$TB_C"
    TB_R="$TB_C/$TB_SLUG-report.html"; TB_F="$TB_C/$TB_SLUG.md"
}
# tb_check DESC NEEDLE RC [check args ...]: run check_post.py on TB_R, expect NEEDLE in the output and exit code RC
tb_check() {
    local desc="$1" needle="$2" want="$3" out rc; shift 3
    out=$("${TB_PY[@]}" "$TB_CHECK" "$TB_R" "$@" 2>&1); rc=$?
    assert_contains "check_post: $desc" "$out" "$needle"
    assert_eq "check_post: $desc (exit $want)" "$want" "$rc"
}
# tb_blog NAME: a fake blog repository (the parts the scripts read); sets TB_BLOG
tb_blog() {
    TB_BLOG="$TB_W/blog-$1"
    rm -rf "$TB_BLOG"; mkdir -p "$TB_BLOG/docs/techblog/sample" "$TB_BLOG/assets/icons"
    printf '%s\n' 'title: Sample blog' '' 'blog_categories:' \
        '  - name: Sample' '    icon: sample' '    desc: Example posts' '    url: /docs/techblog/sample/' \
        '  - name: Elsewhere' '    icon: sample' '    desc: Not a post folder' '    url: /docs/other/' > "$TB_BLOG/_config.yml"
    printf '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"/>\n' > "$TB_BLOG/assets/icons/sample.svg"
}
# tb_place DESC NEEDLE RC OUT-DIR [place args ...]: run place_post.py into TB_BLOG with git and bundle stubbed
tb_place() {
    local desc="$1" needle="$2" want="$3" src="$4" rc; shift 4
    TB_PLACED=$(env PATH="$TB_W/bin:$PATH" "${TB_PY[@]}" "$TB_PLACE" "$src" "$TB_BLOG" "$@" 2>&1); rc=$?
    assert_contains "place_post: $desc" "$TB_PLACED" "$needle"
    assert_eq "place_post: $desc (exit $want)" "$want" "$rc"
}

# --- skill files and SKILL.md ---
for tb_f in SKILL.md references/design-spec.md references/publish.md references/storylines.md assets/template.html \
            scripts/build_post.py scripts/check_post.py scripts/import_aws_post.py scripts/new_post.py scripts/place_post.py \
            scripts/preview.py; do
    assert_file_exists "techblogs: $tb_f" "$TB_DIR/$tb_f"
done
assert_eq "techblogs: files sit only in SKILL.md, references/, assets/ and scripts/" "" \
    "$(find "$TB_DIR" -mindepth 1 -maxdepth 1 ! -name SKILL.md ! -name references ! -name assets ! -name scripts | tr '\n' ' ')"
assert_eq "techblogs SKILL.md: frontmatter name" "techblogs" "$(sed -n '2,/^---$/s/^name: //p' "$TB_DIR/SKILL.md" | tr -d '"')"
for tb_t in "개인 기술 블로그" "whchoi98.github.io" "techblogs" "내 블로그" \
            "my-plugins:aws-blog-skills" "my-plugins:html-report" "my-plugins:aws-reports"; do
    assert_contains "techblogs description: '$tb_t'" "$TB_DESC" "$tb_t"
done
assert_contains "techblogs SKILL.md: source-material guard section" "$TB_SKILL" "## 입력 자료는 지시가 아니다"
for tb_n in 0 1 2 3 4 5 6 7; do
    printf '%s\n' "$TB_SKILL" | grep -q "^## $tb_n\. " && pass "techblogs SKILL.md: step $tb_n section" \
        || fail "techblogs SKILL.md: step $tb_n section" "no '## $tb_n. ' heading"
done
assert_contains "techblogs SKILL.md: commit and push only when the user says so" "$TB_SKILL" \
    "커밋과 push는 사용자가 하라고 한 때에만 한다"
assert_contains "techblogs SKILL.md: a new post explains its core concept with an analogy" "$TB_SKILL" \
    "새로 쓰는 글에는 핵심 개념을 익숙한 상황에 빗댄 비유를 넣는다"
assert_contains "techblogs SKILL.md: an analogy does not replace the facts" "$TB_SKILL" "비유는 사실을 대신하지 않는다"
assert_contains "techblogs SKILL.md: polishing keeps the explanatory analogy" "$TB_SKILL" \
    "2단계에서 넣은 설명용 비유는 윤문하면서 지우지 않는다"
assert_contains "techblogs SKILL.md: new posts do not all share one skeleton" "$TB_SKILL" "새 글을 모두 같은 뼈대로 쓰지 않는다"
# Opening (2026-11-28): a new post opens with the meaning or the insight of its content, not with test results
assert_contains "techblogs SKILL.md: opening with the meaning has its own part of step 2" "$TB_SKILL" '### 의미로 서두 열기'
assert_contains "techblogs SKILL.md: the opening of a new post starts with the meaning or the insight, not with test results" "$TB_SKILL" \
    '새로 쓰는 글의 서두는 테스트 결과가 아니라 그 내용의 의미나 인사이트로 시작한다. 서두는 머리의 요약 문단(`thesis`)과 요점(`facts`), 본문의 첫 챕터다.'
assert_contains "techblogs SKILL.md: the reader stays in the opening and goes on to the body" "$TB_SKILL" \
    '독자가 서두에서 그 의미를 자기 상황에 비춰 보며 머물고, 근거가 궁금해져 본문으로 넘어가게 한다.'
assert_contains "techblogs SKILL.md: the summary paragraph states the meaning in its first sentence" "$TB_SKILL" \
    '요약 문단은 첫 문장에 의미를 쓴다. 그 다음에 무엇을 어디에서 직접 테스트했는지, 근거가 되는 수치, 한계나 조건을 쓴다.'
assert_contains "techblogs SKILL.md: a key point is one takeaway" "$TB_SKILL" '요점은 한 줄에 독자가 가져갈 판단 하나를 쓴다.'
assert_contains "techblogs SKILL.md: the order of the first section" "$TB_SKILL" \
    '첫 챕터는 배경 문단, 의미, 상황(스토리라인의 여는 방식), 본문이 답할 질문 하나의 순서로 쓴다.'
assert_contains "techblogs SKILL.md: result tables and charts go to the sections on the results" "$TB_SKILL" \
    '결과 표와 결과 차트는 결과를 다루는 챕터에 둔다.'
assert_contains "techblogs SKILL.md: two measured values at most in each place of the opening" "$TB_SKILL" \
    '측정값은 요약 문단, 요점 하나, 목록 카드의 요약, 첫 챕터에 각각 둘까지 쓴다.'
assert_contains "techblogs SKILL.md: no measured value in the title of the first section" "$TB_SKILL" '첫 챕터의 제목에는 측정값을 넣지 않는다.'
assert_contains "techblogs SKILL.md: the judgement is not held back" "$TB_SKILL" '판단을 숨기지 않는다. 의미는 서두에서 말하고 근거를 본문으로 미룬다.'
assert_contains "techblogs SKILL.md: the user is told the meaning the opening states" "$TB_SKILL" \
    '서두에 쓸 의미 한 문장도 함께 알린다. 사용자가 다른 의미를 말하면 그것으로 서두를 쓴다.'
assert_contains "techblogs SKILL.md: polishing does not turn the opening back into a summary of numbers" "$TB_SKILL" \
    '서두의 의미 문단도 지우거나 수치 요약으로 되돌리지 않는다.'
assert_contains "techblogs SKILL.md: a new post with the opening warning gets its opening rewritten" "$TB_SKILL" \
    '서두에 측정값이 많다는 `WARN`(요약 문단, 요점, 목록 카드의 요약, 첫 챕터와 그 제목)이 나오면 새 글에서는 서두를 의미로 다시 쓴다.'
assert_contains "techblogs SKILL.md: the last response names the meaning of the opening" "$TB_SKILL" \
    '- 새 글이면 고른 스토리라인과 이유, 서두에 쓴 의미 한 문장'
assert_contains "techblogs SKILL.md: a post from before the rule keeps its opening unless asked" "$TB_SKILL" \
    '**서두 규칙 전에 올린 글**: 다시 빌드하면 `check_post.py`가 서두의 측정값에 `WARN`을 낼 수 있다. 사용자가 요청하지 않았으면 서두를 다시 쓰지 않고 마지막 응답에 알린다.'
# Background paragraph (2026-11-22): a new post opens with one or two sentences on the background of the topic or why it is needed
assert_contains "techblogs SKILL.md: the first section of a new post opens with the background paragraph" "$TB_SKILL" \
    "새로 쓰는 글의 첫 챕터는 배경 문단으로 시작한다"
assert_contains "techblogs SKILL.md: the background paragraph is one or two sentences, before the storyline's opening" "$TB_SKILL" \
    "첫 챕터의 첫 문단에 한 문장이나 두 문장으로 쓴다"
assert_contains "techblogs SKILL.md: the meaning and the background or the need are settled with the scope" "$TB_SKILL" \
    "핵심 주장 하나, 그 주장이 독자에게 뜻하는 것(서두에 쓸 의미), 이 주제의 배경이나 필요, 대상 독자, 스토리라인, 그림 목록을 한 문장씩 확정한다"
assert_contains "techblogs SKILL.md: polishing keeps the background paragraph" "$TB_SKILL" \
    "배경 문단도 도입부 상투구로 보고 지우지 않는다"
assert_contains "techblogs SKILL.md: a post from before the rule gets no background paragraph unless asked" "$TB_SKILL" \
    "사용자가 요청하지 않았으면 배경 문단을 넣지 않고 마지막 응답에 알린다"
# Reading time (2026-11-22): a new post stays within 15 minutes, a longer one is cut or split into a series
assert_contains "techblogs SKILL.md: writing within 15 minutes has its own part of step 2" "$TB_SKILL" '### 읽는 시간 15분 이하로 쓰기'
assert_contains "techblogs SKILL.md: a post is easy to understand and to read" "$TB_SKILL" \
    '글은 주제를 처음 보는 독자가 이해하기 쉽고 읽기 편해야 한다. 새로 쓰는 글 하나의 읽는 시간은 15분을 넘기지 않는다.'
assert_contains "techblogs SKILL.md: the length is settled with the scope" "$TB_SKILL" \
    '| 분량 | 새 글은 읽는 시간 15분 이하. 소재가 그보다 많으면 이 단계에서 연재(시리즈)로 나누고'
assert_contains "techblogs SKILL.md: how the reading time is counted" "$TB_SKILL" \
    '한국어 본문의 글자 수(공백과 코드 상자 제외)를 700으로 나눈 값이다. 15분은 약 10,500자다.'
assert_contains "techblogs SKILL.md: the minutes are not set by hand" "$TB_SKILL" '`meta.json`의 `minutes`에 값을 직접 적어 맞추지 않는다.'
assert_contains "techblogs SKILL.md: overlap is cut first" "$TB_SKILL" '넘으면 먼저 겹치는 내용을 줄인다.'
assert_contains "techblogs SKILL.md: a post that is still too long becomes a series, each part within 15 minutes" "$TB_SKILL" \
    '줄여도 넘으면 연재로 나눈다. 편마다 15분 이하로 쓰고, 한 편만 읽어도 이해되도록 편마다 요약 문단과 배경 문단을 둔다.'
assert_contains "techblogs SKILL.md: a new post does not keep the reading-time warning" "$TB_SKILL" \
    '읽는 시간이 15분을 넘는다는 `WARN`은 새 글에서 남기지 않는다.'
assert_contains "techblogs SKILL.md: a post from before the rule is not cut or split unless asked" "$TB_SKILL" \
    '**읽는 시간 규칙 전에 올린 글**: 다시 빌드하면 `check_post.py`가 15분을 넘는다는 `WARN`을 낼 수 있다. 사용자가 요청하지 않았으면 줄이거나 나누지 않고'
assert_contains "techblogs SKILL.md: the section order follows the chosen storyline" "$TB_SKILL" \
    "챕터의 순서는 0단계에서 고른 스토리라인을 따른다"
assert_contains "techblogs SKILL.md: the first section does not repeat the conclusion list" "$TB_SKILL" \
    "본문 첫 챕터에서 같은 내용을 목록으로 되풀이하지 않는다"
assert_contains "techblogs SKILL.md: the first and last section titles are not fixed" "$TB_SKILL" \
    '첫 챕터와 끝 챕터의 제목을 "들어가며", "마치며"로 고정하지 않는다'
assert_contains "techblogs SKILL.md: the user is told which storyline was chosen" "$TB_SKILL" \
    "고른 스토리라인과 이유를 사용자에게 한 줄로 알린다"
assert_contains "techblogs SKILL.md: the template is chosen from the topic and the material" "$TB_SKILL" \
    "글의 주제와 소재의 내용을 읽고 그에 맞는 스토리라인 템플릿을 고른다"
for tb_s in build_post check_post import_aws_post new_post place_post preview; do
    assert_contains "techblogs SKILL.md: calls scripts/$tb_s.py through the skill dir" "$TB_SKILL" \
        "\"\${CLAUDE_SKILL_DIR}/scripts/$tb_s.py\""
done
for tb_s in lint_prose check_urls; do
    assert_contains "techblogs SKILL.md: reuses aws-blog-skills $tb_s.py by a sibling path" "$TB_SKILL" \
        "\"\${CLAUDE_SKILL_DIR}/../aws-blog-skills/scripts/$tb_s.py\""
done
# Every path the skill text names exists: Markdown links, ${CLAUDE_SKILL_DIR} paths, ../<skill>/ paths, its own
# scripts/, references/ and assets/ files, script names, and my-plugins:<skill> calls. One line per problem.
TB_REFS=$("${TB_PY[@]}" - "$TB_DIR" 2>&1 <<'PY' || true
import glob, os, re, sys
d = sys.argv[1]
docs = [os.path.join(d, "SKILL.md")] + sorted(glob.glob(os.path.join(d, "references", "*.md")))
seen = dict.fromkeys(("link", "skill-dir path", "sibling path", "own file", "script name", "skill call"), 0)

def need(kind, doc, ref, ok):
    seen[kind] += 1
    if not ok:
        print("%s: %s -> %s" % (kind, doc, ref))

skill = ""
for doc in docs:
    if not os.path.isfile(doc):
        print("missing: %s" % doc)
        continue
    s = open(doc, encoding="utf-8").read()
    if doc.endswith("SKILL.md"):
        skill = s
    for t in re.findall(r"\]\(([^)#\s]+)\)", s):
        if not re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I):
            need("link", doc, t, os.path.exists(os.path.join(os.path.dirname(doc), t)))
    for t in sorted(set(re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w.\-/]+)", s))):
        need("skill-dir path", doc, t, os.path.exists(os.path.join(d, t.rstrip("./"))))
    for t in sorted(set(re.findall(r"(?<![\w/}])(\.\./[a-z0-9-]+/[\w.\-/]+)", s))):
        need("sibling path", doc, t, os.path.exists(os.path.join(d, t.rstrip("./"))))
    for t in sorted(set(re.findall(r"(?<![\w/.-])((?:scripts|references|assets)/[\w.-]+\.(?:py|md|html))", s))):
        need("own file", doc, t, os.path.isfile(os.path.join(d, t)))
    for t in sorted(set(re.findall(r"(?<![\w/-])([a-z_]+\.py)\b", s))):
        need("script name", doc, t, os.path.isfile(os.path.join(d, "scripts", t))
             or os.path.isfile(os.path.join(d, "..", "aws-blog-skills", "scripts", t)))
    for t in sorted(set(re.findall(r"my-plugins:([a-z0-9][a-z0-9-]*)", s))):
        need("skill call", doc, t, os.path.isfile(os.path.join(d, "..", t, "SKILL.md")))
for kind, n in seen.items():
    if not n:
        print("nothing checked: %s" % kind)
for p in sorted(glob.glob(os.path.join(d, "scripts", "*.py"))):
    if os.path.basename(p) not in skill:
        print("script not named in SKILL.md: %s" % p)
PY
)
assert_eq "techblogs: every path, script and skill named in SKILL.md and references exists" "" "$(printf '%s' "$TB_REFS" | tr '\n' ' ')"

# --- template: the names the blog layout and preview.py depend on, and the tokens build_post.py fills ---
TB_TPL_TEXT=$(cat "$TB_TPL" 2>/dev/null)
for tb_t in '<div class="wrap page">' '<nav class="top theme-bar">' \
            "getItem('techblogs-lang')" "getItem('techblogs-theme')" "put('techblogs-lang'," "put('techblogs-theme'," \
            "addEventListener('langchange'" "addEventListener('themechange'" \
            'id="langSeg"' 'id="themeSeg"' 'data-v="ko"' 'data-v="en"' 'data-v="light"' 'data-v="dark"'; do
    assert_contains "techblogs template: $tb_t" "$TB_TPL_TEXT" "$tb_t"
done
# The title fit: the template shrinks the title to one line, and design-spec.md names the same function
assert_contains "techblogs template: fits the title on one line (fitTitle)" "$TB_TPL_TEXT" "function fitTitle()"
assert_contains "techblogs template: a fitted title does not wrap (h1.one)" "$TB_TPL_TEXT" "h1.one{white-space:nowrap}"
assert_contains "techblogs design-spec.md: describes the title fit" "$(cat "$TB_SPEC" 2>/dev/null)" "fitTitle"
# "Changelog" is written in English: SKILL.md step 3 and the text rules of design-spec.md both say so
TB_STEP3=$(sed -n '/^## 3\. 문장 규칙/,/^## 4\. /p' "$TB_DIR/SKILL.md" 2>/dev/null)
assert_contains "techblogs SKILL.md step 3: Changelog stays in English" "$TB_STEP3" '"변경 기록"으로 옮기지 않고 "Changelog"'
TB_SPEC_TEXT=$(sed -n '/^## 글자 규칙/,/^## 템플릿에 있지만/p' "$TB_SPEC" 2>/dev/null)
assert_contains "techblogs design-spec.md: the text rules name the Changelog check" "$TB_SPEC_TEXT" '"Changelog"로 쓴다(WARN)'
# Word rule of 2026-11-18: 챕터 or 장 for a part of the text, 비교하다 for 견주다
assert_contains "techblogs SKILL.md step 3: 절 is written 챕터 or 장" "$TB_STEP3" '"절"은 "챕터"나 "장"으로'
assert_contains "techblogs SKILL.md step 3: 견주다 is written 비교하다" "$TB_STEP3" '"견주다"는 "비교하다"로'
assert_contains "techblogs design-spec.md: the text rules name the 절 check" "$TB_SPEC_TEXT" '"절"은 "챕터"나 "장"으로 쓴다(WARN)'
assert_contains "techblogs design-spec.md: the text rules name the 견주다 check" "$TB_SPEC_TEXT" '"견주다"는 "비교하다"로 쓴다(WARN)'
# Word rule of 2026-11-22: 트레이드 오프가 있다 for 대가가 있다
assert_contains "techblogs SKILL.md step 3: 대가가 있다 is written 트레이드 오프가 있다" "$TB_STEP3" '"대가가 있다"는 "트레이드 오프가 있다"로'
assert_contains "techblogs design-spec.md: the text rules name the 대가가 있다 check" "$TB_SPEC_TEXT" '"대가가 있다"는 "트레이드 오프가 있다"로 쓴다(WARN)'
TB_SPEC_HOOKS=$(sed -n '/^## 블로그 레이아웃과 맞물리는 부분/,/^## meta.json/p' "$TB_SPEC" 2>/dev/null)
for tb_t in 'div.wrap.page' 'nav.top.theme-bar' 'techblogs-theme' 'techblogs-lang'; do
    assert_contains "techblogs design-spec.md: blog layout hook $tb_t" "$TB_SPEC_HOOKS" "$tb_t"
done
TB_TOKENS=$("${TB_PY[@]}" - "$TB_TPL" "$TB_BUILD" 2>&1 <<'PY' || true
import ast, re, sys
tokens = set(re.findall(r"\[\[([a-z_]+)\]\]", open(sys.argv[1], encoding="utf-8").read()))
keys = set()
for node in ast.walk(ast.parse(open(sys.argv[2], encoding="utf-8").read())):
    if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
            and any(isinstance(t, ast.Name) and t.id == "fill" for t in node.targets)):
        keys |= {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
if not tokens or not keys:
    print("found %d template tokens and %d fill keys" % (len(tokens), len(keys)))
for t in sorted(tokens - keys):
    print("template token without a fill key: " + t)
for k in sorted(keys - tokens):
    print("fill key without a template token: " + k)
PY
)
assert_eq "techblogs: template [[tokens]] are the keys build_post.py fills" "" "$(printf '%s' "$TB_TOKENS" | tr '\n' ' ')"
# The meta.json example in design-spec.md is valid JSON with the keys build_post.py requires
TB_EXAMPLE=$("${TB_PY[@]}" - "$TB_SPEC" 2>&1 <<'PY' || true
import json, re, sys
m = re.search(r"```json\n(.*?)\n```", open(sys.argv[1], encoding="utf-8").read(), re.S)
if not m:
    sys.exit("no json block")
try:
    meta = json.loads(m.group(1))
except ValueError as e:
    sys.exit("invalid JSON: %s" % e)
missing = [k for k in ("slug", "category", "category_dir", "icon", "date", "title", "excerpt", "thesis") if k not in meta]
missing += ["%s.%s" % (k, l) for k in ("title", "excerpt", "thesis") for l in ("ko", "en") if l not in (meta.get(k) or {})]
print(" ".join(missing))
PY
)
assert_eq "techblogs design-spec.md: the meta.json example parses and has the required keys" "" "$TB_EXAMPLE"
# The storyline keys: build_post.py is the list; storylines.md has one table row and one section per key, in the
# same order, each section with its eight lines; SKILL.md and design-spec.md name every key
TB_STORY=$("${TB_PY[@]}" - "$TB_BUILD" "$TB_DIR/references/storylines.md" "$TB_SPEC" "$TB_DIR/SKILL.md" 2>&1 <<'PY' || true
import re, sys
build, story, spec, skill = (open(p, encoding="utf-8").read() for p in sys.argv[1:5])
m = re.search(r"^STORYLINES = \((.*?)\)$", build, re.M)
keys = re.findall(r'"([a-z]+)"', m.group(1)) if m else []
if len(keys) < 2:
    sys.exit("no STORYLINES tuple in build_post.py")
heads = re.findall(r"^## ([a-z]+): ", story, re.M)
rows = re.findall(r"^\| `([a-z]+)` \|", story, re.M)
if heads != keys:
    print("storylines.md sections %s differ from build_post.py %s" % (heads, keys))
if rows != keys:
    print("storylines.md table %s differs from build_post.py %s" % (rows, keys))
for k in keys:
    for name, text in (("design-spec.md", spec), ("SKILL.md", skill)):
        if "`%s`" % k not in text:
            print("%s does not name `%s`" % (name, k))
for sec in re.split(r"^## ", story, flags=re.M)[1:]:
    name = sec.split("\n", 1)[0]
    if not re.match(r"[a-z]+: ", name):
        continue
    for label in ("챕터 흐름", "배경 문단", "서두의 의미", "여는 방식", "닫는 방식", "비유의 자리", "그림", "피할 것"):
        if "- **%s**:" % label not in sec:
            print("storylines.md '%s': no '%s' line" % (name, label))
    if "- **배경 문단**:" in sec and sec.index("- **배경 문단**:") > sec.index("- **여는 방식**:"):
        print("storylines.md '%s': the background paragraph line comes after the opening line" % name)
    # Opening (2026-11-28): the meaning comes after the background paragraph and before the scene, and no storyline opens with a number
    if "- **서두의 의미**:" in sec and not sec.index("- **배경 문단**:") < sec.index("- **서두의 의미**:") < sec.index("- **여는 방식**:"):
        print("storylines.md '%s': the meaning line is not between the background paragraph line and the opening line" % name)
    how = re.search(r"^- \*\*여는 방식\*\*: (.*)$", sec, re.M)
    if how and not how.group(1).startswith("의미를 말한 뒤 "):
        print("storylines.md '%s': the opening line does not start with the meaning" % name)
ex = re.search(r'"storyline": "([a-z]+)"', spec)
if not ex or ex.group(1) not in keys:
    print("design-spec.md: the meta.json example has no known storyline")
PY
)
assert_eq "techblogs: the storyline keys agree in build_post.py, storylines.md, design-spec.md and SKILL.md" "" \
    "$(printf '%s' "$TB_STORY" | tr '\n' ' ')"
assert_contains "techblogs storylines.md: a republished post keeps the structure of the original" \
    "$(cat "$TB_DIR/references/storylines.md" 2>/dev/null)" '옮겨 싣는 글(`origin`이 있는 글)에는 적용하지 않는다'
TB_STORYDOC=$(cat "$TB_DIR/references/storylines.md" 2>/dev/null)
printf '%s\n' "$TB_STORYDOC" | grep -qxF '## 배경 문단' && pass "techblogs storylines.md: the background paragraph has its own section" \
    || fail "techblogs storylines.md: the background paragraph has its own section" "no '## 배경 문단' heading"
assert_contains "techblogs storylines.md: the background paragraph is one or two sentences" "$TB_STORYDOC" \
    "한 문장이나 두 문장, 문단 하나다"
assert_contains "techblogs storylines.md: the storyline's opening comes after the background paragraph" "$TB_STORYDOC" \
    "스토리라인의 여는 방식은 그 다음에 쓴다"
assert_contains "techblogs storylines.md: the background paragraph does not announce the order of the post" "$TB_STORYDOC" \
    '글의 순서 안내("이 글에서는 ~를 살펴봅니다")'
# Opening (2026-11-28): the meaning or the insight first, results in the sections after the first one
printf '%s\n' "$TB_STORYDOC" | grep -qxF '## 서두' && pass "techblogs storylines.md: the opening has its own section" \
    || fail "techblogs storylines.md: the opening has its own section" "no '## 서두' heading"
assert_contains "techblogs storylines.md: the opening is the summary paragraph, the key points and the first section" "$TB_STORYDOC" \
    '머리의 요약 문단(`thesis`)과 요점(`facts`), 본문의 첫 챕터를 가리키고, 목록 카드에 보이는 요약(`excerpt`)도 같은 원칙을 따른다.'
assert_contains "techblogs storylines.md: the opening starts with the meaning, results follow as evidence" "$TB_STORYDOC" \
    '새로 쓰는 글의 서두는 그 내용의 의미나 인사이트로 시작하고, 테스트 결과는 그 뒤에 근거로 둔다.'
assert_contains "techblogs storylines.md: every storyline opens with the meaning" "$TB_STORYDOC" \
    '- 서두는 테스트 결과가 아니라 그 내용의 의미나 인사이트로 연다.'
assert_contains "techblogs storylines.md: what a meaning is" "$TB_STORYDOC" \
    '결과는 측정하거나 확인한 사실이고, 의미는 그 사실 때문에 독자의 판단이 어떻게 달라지는지다.'
assert_contains "techblogs storylines.md: the summary paragraph states the meaning first and holds two measured values at most" "$TB_STORYDOC" \
    '- **요약 문단(`thesis`)**: 첫 문장에 의미를 쓴다.'
assert_contains "techblogs storylines.md: the first section ends on the question the body answers" "$TB_STORYDOC" \
    '4. **남는 질문**: 본문이 답할 질문 하나로 맺는다. 그 자리에서 바로 답하지 않는다.'
assert_contains "techblogs storylines.md: the first section title carries no measured value" "$TB_STORYDOC" \
    '- 첫 챕터의 제목은 의미나 독자의 상황으로 짓고 측정값을 넣지 않는다.'
assert_contains "techblogs storylines.md: result charts and tables stay out of the first section" "$TB_STORYDOC" \
    '결과 차트와 결과 표는 결과를 다루는 챕터에 둔다.'
assert_contains "techblogs storylines.md: how the opening holds the reader" "$TB_STORYDOC" '### 독자가 머무는 서두'
assert_contains "techblogs storylines.md: the judgement is stated, the evidence is what waits" "$TB_STORYDOC" \
    '- 판단을 숨기지 않는다. 의미는 서두에서 말하고 근거(수치, 로그, 명령)를 본문으로 미룬다.'
assert_contains "techblogs storylines.md: no teaser that does not say what differed" "$TB_STORYDOC" \
    '무엇이 달랐는지 말하지 않는 문장'
assert_contains "techblogs storylines.md: the background paragraph is the first paragraph of the opening" "$TB_STORYDOC" \
    '배경 문단은 서두의 첫 문단이다.'
# The two example summary paragraphs of the section are what the checker says they are: the first one passes, the second one
# warns, and the number of measured values the text names is the number the checker counts
TB_OPENEX=$("${TB_PY[@]}" - "$TB_CHECK" "$TB_DIR/references/storylines.md" 2>&1 <<'PY' || true
import importlib.util, re, sys
spec = importlib.util.spec_from_file_location("check_post", sys.argv[1])
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
doc = open(sys.argv[2], encoding="utf-8").read()
sec = doc.split("\n## 서두\n", 1)[-1].split("\n## ", 1)[0]
quotes = re.findall(r"^> (.+)$", sec, re.M)
if len(quotes) != 2:
    sys.exit("expected two example paragraphs in the section, found %d" % len(quotes))
good, bad = (cp.measures(q) for q in quotes)
if len(good) > cp.OPEN_MAX:
    print("the example to follow has %d measured values: %s" % (len(good), good))
if len(bad) <= cp.OPEN_MAX:
    print("the example to avoid has only %d measured values" % len(bad))
words = "한 두 세 네 다섯 여섯 일곱 여덟 아홉 열".split()
if not 1 <= len(bad) <= 10 or "측정값 %s 개를" % words[len(bad) - 1] not in sec:
    print("the text does not name the %d measured values of the example to avoid" % len(bad))
if "셋 이상" not in sec or cp.OPEN_MAX != 2:
    print("OPEN_MAX is %d but the section says a warning starts at three" % cp.OPEN_MAX)
PY
)
assert_eq "techblogs storylines.md: the example summary paragraphs agree with check_post.py" "" "$(printf '%s' "$TB_OPENEX" | tr '\n' ' ')"
assert_contains "techblogs design-spec.md: the first section of a new post is the body of the opening" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '새 글의 첫 챕터는 서두의 본문이다. 배경 문단, 의미, 상황, 본문이 답할 질문 하나의 순서로 쓰고 제목(`h2`)에는 측정값을 넣지 않는다.'
assert_contains "techblogs design-spec.md: the summary paragraph of a new post states the meaning first" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '새 글은 첫 문장에 의미를 쓰고 직접 테스트한 사실, 근거, 한계를 붙이며 측정값은 둘까지 쓴다'
assert_contains "techblogs design-spec.md: a key point of a new post is one takeaway" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '새 글은 한 줄에 독자가 가져갈 판단 하나를 쓰고 측정값은 요점 하나에 둘까지 붙인다'
assert_contains "techblogs design-spec.md: the checker warns about measured values in the opening" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '- 새 글의 서두에 측정값이 셋 이상이면 WARN이다(서두). 요약 문단(`thesis`), 요점(`facts`) 하나, 목록 카드의 요약(`excerpt`), 한국어 첫 챕터를 각각 세고, 한국어 첫 챕터의 제목은 측정값이 하나만 있어도 WARN이다.'
assert_contains "techblogs design-spec.md: what counts as a measured value" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '"5분 28초"는 하나로 세고 날짜, 버전, 물건의 개수(개, 대), 코드 안의 숫자는 세지 않는다. 한국어 쪽만 본다.'
assert_contains "techblogs design-spec.md: whether the opening states a meaning is left to the writer" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '- 서두의 내용(요약 문단의 첫 문장과 첫 챕터가 의미를 말하는가'
assert_contains "techblogs design-spec.md: the first section of a new post opens with the background paragraph" \
    "$(cat "$TB_SPEC" 2>/dev/null)" '새 글의 첫 챕터는 `div.prose`의 첫 요소가 배경 문단이다'
assert_contains "techblogs design-spec.md: the checker warns about the background paragraph" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '새 글의 첫 챕터가 문단(`<p>`)으로 시작하지 않거나 한국어 첫 문단이 세 문장 이상이면 WARN이다(배경 문단)'
assert_contains "techblogs storylines.md: one post stays within 15 minutes, more material becomes a series" "$TB_STORYDOC" \
    '- 글 하나의 읽는 시간은 15분을 넘기지 않는다. 소재가 그보다 많으면 연재로 나누고 편마다 스토리라인을 따로 고른다'
assert_contains "techblogs design-spec.md: the checker warns about a reading time over 15 minutes" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '- 새 글의 읽는 시간이 15분을 넘으면 WARN이다. 한국어 본문의 글자 수(공백과 코드 상자 제외)를 700으로 나눈 값으로'
assert_contains "techblogs design-spec.md: minutes in meta.json is not used to fit the limit" "$(cat "$TB_SPEC" 2>/dev/null)" \
    '새 글은 15분 이하여야 하며 값을 직접 적어 맞추지 않는다'

# --- build_post.py: the fixture builds; the result passes check_post.py and lint_prose.py ---
tb_work work
TB_OUT="$TB_WK/out"
TB_MSG=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" 2>&1); TB_RC=$?
assert_eq "build_post: the fixture builds (exit 0)" "0" "$TB_RC"
assert_contains "build_post: lists the deliverables" "$TB_MSG" "deliverables:"
assert_contains "build_post: names the storyline of the post" "$TB_MSG" "storyline: measure"
assert_not_contains "build_post: no warning when the storyline is set" "$TB_MSG" "WARN"
if [ "$TB_RC" -eq 0 ] && [ -f "$TB_OUT/$TB_SLUG-report.html" ]; then
    assert_file_exists "build_post: front matter file" "$TB_OUT/$TB_SLUG.md"
    assert_file_exists "build_post: image copied to the assets folder" "$TB_OUT/$TB_SLUG-assets/fig01-flow.png"
    : > "$TB_OUT/$TB_SLUG-assets/old-name.png"
    "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1
    [ ! -e "$TB_OUT/$TB_SLUG-assets/old-name.png" ] && pass "build_post: a rebuild leaves no stale file in the assets folder" \
        || fail "build_post: a rebuild leaves no stale file in the assets folder" "old-name.png is still there"
    TB_PAGE=$(cat "$TB_OUT/$TB_SLUG-report.html")
    assert_contains "build_post: images point at the assets folder" "$TB_PAGE" "src=\"$TB_SLUG-assets/fig01-flow.png\""
    assert_not_contains "build_post: no images/ path left in the page" "$TB_PAGE" 'src="images/'
    assert_contains "build_post: canonical is the post address when there is no origin" "$TB_PAGE" \
        "<link rel=\"canonical\" href=\"https://whchoi98.github.io/docs/techblog/sample/$TB_SLUG/\">"
    assert_contains "build_post: Korean menu links every section and the references" "$TB_PAGE" \
        '<a href="#ko-s1">문제와 측정</a><a href="#ko-s2">읽기 단계 나누기</a><a href="#sources">참고 자료</a>'
    assert_contains "build_post: source table row" "$TB_PAGE" '<tr id="src-1">'
    TB_FRONT=$(cat "$TB_OUT/$TB_SLUG.md")
    for tb_t in 'layout: report' "report_src: /docs/techblog/sample/$TB_SLUG-report.html" 'date: 2026-01-15' \
                'category: Sample' 'icon: sample' 'minutes: 3' 'title_en: "Shortening an example batch job"'; do
        # whole lines, so that "icon: sample-batch-window" is not taken for "icon: sample"
        printf '%s\n' "$TB_FRONT" | grep -qxF -- "$tb_t" && pass "build_post front matter: $tb_t" \
            || fail "build_post front matter: $tb_t" "no such line in $TB_SLUG.md"
    done

    # SKILL.md step 5: check with --blog, and write the Korean text and the links into out/
    tb_blog main
    TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_OUT/$TB_SLUG-report.html" --blog "$TB_BLOG" \
        --dump-ko "$TB_OUT/ko.md" --urls "$TB_OUT/urls.md" 2>&1); TB_RC=$?
    assert_contains "check_post: the built fixture has no ERROR and no WARN" "$TB_MSG" "결과: ERROR 0 / WARN 0"
    assert_eq "check_post: the built fixture exits 0" "0" "$TB_RC"
    TB_KO=$(cat "$TB_OUT/ko.md" 2>/dev/null)
    assert_contains "check_post --dump-ko: title" "$TB_KO" "# 예시 배치 작업의 실행 시간 줄이기"
    assert_contains "check_post --dump-ko: section heading keeps its level" "$TB_KO" "## 문제와 측정"
    assert_not_contains "check_post --dump-ko: English text is left out" "$TB_KO" "Splitting the read stage"
    assert_contains "check_post --dump-ko: the excerpt (meta description) is linted too" "$TB_KO" "가상의 집계 배치를 단계별로 재고 읽기 단계를 나누어 실행 시간을 줄인 예시입니다."
    assert_contains "check_post --dump-ko: the masthead facts are linted too" "$TB_KO" "결과 전체 실행 시간 40분에서 26분"
    assert_contains "check_post --dump-ko: the closing note is linted too" "$TB_KO" "이 글의 수치는 검사용으로 지어낸 값입니다."
    TB_LINT=$(python3 -I skills/aws-blog-skills/scripts/lint_prose.py "$TB_OUT/ko.md" 2>&1 || true)
    assert_contains "check_post --dump-ko: the fixture's Korean text has lint_prose HARD 0" "$TB_LINT" "hard_findings=0"
    assert_eq "check_post --urls: outside links, one per line, without the canonical link" \
        "- https://example.com/guide - https://example.com/docs/batch " "$(tr '\n' ' ' < "$TB_OUT/urls.md" 2>/dev/null)"
    TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/ko.body.html" --dump-ko "$TB_W/fragment.ko.md" 2>&1); TB_RC=$?
    assert_contains "check_post: a body fragment is only dumped" "$TB_MSG" "fragment:"
    assert_eq "check_post: a body fragment exits 0" "0" "$TB_RC"
    assert_contains "check_post --dump-ko: fragment text" "$(cat "$TB_W/fragment.ko.md" 2>/dev/null)" "### 단계별 시간"

    # --- check_post.py: each rule fails once on a copy of the built output ---
    tb_case style && tb_edit "$TB_R" '</style>' ';</style>' \
        && tb_check "one character added to <style>" '<style>이 템플릿과 다릅니다' 1
    tb_case script && tb_edit "$TB_R" '</script>' ';</script>' \
        && tb_check "<script> changed" '<script>가 템플릿과 다릅니다' 1
    tb_case token && tb_edit "$TB_R" '<h3>Time per stage</h3>' '<h3>[[title_en]]</h3>' \
        && tb_check "template token left in the page" '채우지 않은 템플릿 토큰이 남아 있습니다: [[title_en]]' 1
    tb_case todo && tb_edit "$TB_R" '<h3>단계별 시간</h3>' '<h3>TODO 단계별 시간</h3>' \
        && tb_check "TODO left in the text" 'TODO 표시가 남아 있습니다' 1
    tb_case inline && tb_edit "$TB_R" '<blockquote>' '<blockquote style="color:red">' \
        && tb_check "inline style attribute" '인라인 style 속성은 쓰지 않습니다' 1
    tb_case wrap && tb_edit "$TB_R" '<div class="wrap page">' '<div class="wrap">' \
        && tb_check "div.wrap.page renamed" 'div.wrap.page (블로그 레이아웃이 찾는 요소): 0개' 1
    tb_case bar && tb_edit "$TB_R" '<nav class="top theme-bar">' '<nav class="top">' \
        && tb_check "nav.top.theme-bar renamed" 'nav.top.theme-bar (블로그 레이아웃이 숨기는 상단 막대): 0개' 1
    tb_case secid && tb_edit "$TB_R" 'id="en-s2"' 'id="en-s9"' \
        && tb_check "section id out of sequence" 'en 2번째 챕터의 id가 en-s2 가 아닙니다' 1
    tb_case toc && tb_edit "$TB_R" '<a href="#ko-s2">' '<a href="#ko-s7">' \
        && tb_check "menu link to a missing section" 'ko 목차 링크가 가리키는 곳이 없습니다: #ko-s7' 1
    tb_case entable && tb_resub "$TB_R" '(id="en-s1".*?)<table>.*?</table>' '\1' \
        && tb_check "English table removed (component counts differ)" '챕터 1의 표 수가 다릅니다: ko 1, en 0' 1
    tb_case ensec && tb_resub "$TB_R" '<section class="sec" id="en-s2">.*?</section>\n' '' \
        && tb_check "English section removed" '챕터 수가 다릅니다: ko 2, en 1' 1
    tb_case enfig && cp "$TB_C/$TB_SLUG-assets/fig01-flow.png" "$TB_C/$TB_SLUG-assets/fig01-flow-en.png" \
        && tb_resub "$TB_R" '(id="en-s1".*?)fig01-flow\.png' '\1fig01-flow-en.png' \
        && tb_check "the English side may show the English version of a figure (<name>-en.<ext>)" '결과: ERROR 0 / WARN 0' 0
    tb_case figorder && cp "$TB_C/$TB_SLUG-assets/fig01-flow.png" "$TB_C/$TB_SLUG-assets/fig09-other.png" \
        && tb_resub "$TB_R" '(id="en-s1".*?)fig01-flow\.png' '\1fig09-other.png' \
        && tb_check "the English side shows a different figure" '두 언어의 그림 파일 순서가 다릅니다' 1
    tb_case figcap && tb_edit "$TB_R" '<b>그림 1.</b>' '<b>그림 2.</b>' \
        && tb_check "figure caption number skipped" 'ko 그림 캡션 번호가 순서대로가 아닙니다' 1
    tb_case tblcap && tb_edit "$TB_R" '<b>Table 1.</b>' '<b>Table 3.</b>' \
        && tb_check "table caption number skipped" 'en 표 캡션 번호가 순서대로가 아닙니다' 1
    tb_case nofile && rm -f "$TB_C/$TB_SLUG-assets/fig01-flow.png" \
        && tb_check "image file deleted" "그림 파일이 없습니다: $TB_SLUG-assets/fig01-flow.png" 1
    tb_case alt && tb_edit "$TB_R" 'alt="Three stages in a row: read, aggregate, write"' 'alt=""' \
        && tb_check "image without alt" '그림에 alt가 없습니다' 1
    tb_case remote && tb_edit "$TB_R" "src=\"$TB_SLUG-assets/fig01-flow.png\"" 'src="https://example.com/fig01-flow.png"' \
        && tb_check "remote image" '원격 주소와 data URI는 쓰지 않음' 1
    tb_case nofig && tb_edit "$TB_R" '<div class="canvas">' '<div class="frame">' \
        && tb_check "image outside div.canvas" '그림은 figure.fig 안의 div.canvas에 둡니다' 1
    tb_case scroll && tb_edit "$TB_R" '<div class="scroll"><table>' '<div class="box"><table>' \
        && tb_check "table outside div.scroll" '표는 div.scroll 안에 둡니다' 1
    tb_case snippet && tb_edit "$TB_R" '<button type="button" class="copy"><span class="i">Copy</span><span class="ok">Copied</span></button>' '' \
        && tb_check "code box without the copy button" '코드 상자는 .snippet-bar(span.lang, button.copy)와 pre > code를 갖춥니다' 1
    tb_case dot && tb_edit "$TB_R" '<h2>문제와 측정</h2>' '<h2>문제·측정</h2>' \
        && tb_check "middle dot in the text" '가운뎃점(·)은 쓰지 않습니다' 1
    tb_case dash && tb_edit "$TB_R" '<h3>Time per stage</h3>' '<h3>Time — per stage</h3>' \
        && tb_check "em dash in the English text" '엠 대시(—)은 쓰지 않습니다' 1
    tb_case codedot && tb_edit "$TB_R" '<p>Timing each stage shows' '<p>With <code>read·write</code>, timing each stage shows' \
        && tb_check "middle dot inside inline code is allowed" '결과: ERROR 0 / WARN 0' 0
    tb_case arrow && tb_edit "$TB_R" '<p>Timing each stage shows' '<p>Timing → each stage shows' \
        && tb_check "arrow in a sentence warns" '문장 안의 화살표(→)는 말로 풉니다' 0
    # "Changelog" stays in English. lint_prose.py does not read tables, so the page check looks at every text node
    tb_case term && tb_edit "$TB_R" '웹 문서' '변경 기록' \
        && tb_check "변경 기록 in a table cell warns and names Changelog" "'변경 기록'은 Changelog로 씁니다" 0
    tb_case termns && tb_edit "$TB_R" '<h3>단계별 시간</h3>' '<h3>단계별 변경기록</h3>' \
        && tb_check "변경기록 without the space warns" "'변경기록'은 Changelog로 씁니다" 0
    tb_case termok && tb_edit "$TB_R" '웹 문서' 'Changelog' \
        && tb_check "Changelog in English is not flagged" '결과: ERROR 0 / WARN 0' 0
    # Word rule of 2026-11-18, also in table cells and headings
    tb_case wordsec && tb_edit "$TB_R" '웹 문서' '다음 절' \
        && tb_check "절 for a part of the text warns and names 챕터, 장" "'절'은 챕터나 장으로 씁니다" 0
    tb_case wordsecok && tb_edit "$TB_R" '웹 문서' '절차의 절반과 WHERE 절' \
        && tb_check "절차, 절반 and an SQL clause are not flagged" '결과: ERROR 0 / WARN 0' 0
    tb_case wordcmp && tb_edit "$TB_R" '<h3>단계별 시간</h3>' '<h3>단계를 견주어 본 시간</h3>' \
        && tb_check "견주다 warns and names 비교하다" "'견주다'는 비교하다로 씁니다" 0
    # Word rule of 2026-11-22: 대가가 있다 is written 트레이드 오프가 있다; 대가 at the end of another word is left alone
    tb_case wordtrade && tb_edit "$TB_R" '웹 문서' '대가가 있습니다' \
        && tb_check "대가가 있다 warns and names 트레이드 오프가 있다" "'대가가 있다'는 트레이드 오프가 있다로 씁니다" 0
    tb_case wordtradeok && tb_edit "$TB_R" '웹 문서' '시간대가 있고 기대가 있습니다' \
        && tb_check "시간대가 있고 and 기대가 있습니다 are not flagged" '결과: ERROR 0 / WARN 0' 0
    # Background paragraph (2026-11-22): the first section opens with a paragraph of one or two sentences
    tb_case lead3 && tb_edit "$TB_R" '실행된다고 가정합니다.</p>' '실행된다고 가정합니다. 읽기 단계가 가장 깁니다.</p>' \
        && tb_check "a first paragraph of three sentences warns" 'ko 첫 챕터의 첫 문단이 3문장입니다. 배경 문단은 한두 문장으로 씁니다' 0
    tb_case leadcode && tb_edit "$TB_R" '<p>이 글은 검사용으로' '<p>이 글은 <code>가. 나. 다. 라</code> 검사용으로' \
        && tb_check "sentence ends inside inline code are not counted" '결과: ERROR 0 / WARN 0' 0
    tb_case leaddate && tb_edit "$TB_R" '<p>이 글은 검사용으로' '<p>2026. 1. 15. 기준으로 이 글은 검사용으로' \
        && tb_check "the dots of a date are not counted as sentence ends" '결과: ERROR 0 / WARN 0' 0
    tb_case leaden && tb_edit "$TB_R" 'for 40 minutes every night.</p>' 'for 40 minutes every night. The read stage is the longest.</p>' \
        && tb_check "the sentence count is taken on the Korean side only" '결과: ERROR 0 / WARN 0' 0
    tb_case leadenko && tb_edit "$TB_R" 'This post is a made-up example for testing. Assume an aggregation batch' '화면 one. 화면 two. 화면 three. Assume an aggregation batch' \
        && assert_not_contains "check_post: Korean words in the English first paragraph are not counted as its sentences" \
            "$("${TB_PY[@]}" "$TB_CHECK" "$TB_R" 2>&1)" "첫 문단이"
    tb_case leadko && tb_resub "$TB_R" '(id="ko-s1">.*?<div class="prose">\s*)<p>.*?</p>\s*' '\1' \
        && tb_check "a Korean first section that does not start with a paragraph warns" \
            'ko 첫 챕터가 문단으로 시작하지 않습니다. 새 글의 첫 챕터는 배경 문단(주제의 배경이나 필요, 한두 문장)으로 시작합니다' 0
    tb_case leadenp && tb_resub "$TB_R" '(id="en-s1">.*?<div class="prose">\s*)<p>.*?</p>\s*' '\1' \
        && tb_check "an English first section that does not start with a paragraph warns" 'en 첫 챕터가 문단으로 시작하지 않습니다' 0
    # Opening (2026-11-28): two measured values at most in the summary paragraph, in one key point, in the excerpt and in the
    # Korean first section, and none in its title. The fixture has two in its summary paragraph and in its key point and passes.
    tb_case openthesis && tb_edit "$TB_R" '나누면 전체 시간이 40분에서 26분으로 줄어듭니다.' '나누면 20분이던 읽기가 줄어 전체 시간이 40분에서 26분으로 줄어듭니다.' \
        && tb_check "a summary paragraph with three measured values warns and lists them" \
            '요약 문단(thesis)에 측정값이 3개 있습니다(20분, 40분, 26분). 서두는 의미로 열고 측정값은 한 곳에 2개까지 쓰며 나머지는 결과를 다루는 챕터에 둡니다. 이전에 올린 글은 사용자가 요청할 때 고칩니다.' 0
    tb_case openfact && tb_edit "$TB_R" '전체 실행 시간 40분에서 26분' '전체 실행 시간 40분에서 26분, 35% 단축' \
        && tb_check "a key point with three measured values warns and names the point" \
            '요점(facts) 1번에 측정값이 2개 넘게 있습니다. 요점은 한 줄에 독자가 가져갈 판단 하나를 씁니다.' 0
    tb_case openexcerpt && tb_edit "$TB_R" '실행 시간을 줄인 예시입니다.' '실행 시간을 40분에서 26분으로 35% 줄인 예시입니다.' \
        && tb_check "an excerpt with three measured values warns" '목록 카드의 요약(excerpt)에 측정값이 3개 있습니다(40분, 26분, 35%).' 0
    tb_case opentitle && tb_edit "$TB_R" '<h2>문제와 측정</h2>' '<h2>40분 걸리는 배치</h2>' \
        && tb_check "a measured value in the title of the Korean first section warns" \
            'ko 첫 챕터의 제목에 측정값이 있습니다(40분). 첫 챕터의 제목은 의미나 독자의 상황으로 짓습니다.' 0 \
        && assert_not_contains "check_post: two measured values in the first section (title and paragraph) are within the limit; the caption number in '그림 1. 배치' is not a value" \
            "$("${TB_PY[@]}" "$TB_CHECK" "$TB_R" 2>&1)" "ko 첫 챕터에 측정값이"
    tb_case openchapter && tb_edit "$TB_R" '<p>단계별로 시간을 재면 읽기 단계가 전체의 절반을 차지합니다.</p>' '<p>단계별로 시간을 재면 읽기 20분, 집계 12분입니다.</p>' \
        && tb_check "a Korean first section with three measured values warns" 'ko 첫 챕터에 측정값이 3개 있습니다(40분, 20분, 12분).' 0
    tb_case openmany && tb_edit "$TB_R" '<p>단계별로 시간을 재면 읽기 단계가 전체의 절반을 차지합니다.</p>' '<p>읽기 20분, 집계 12분, 쓰기 8분, 합계 40분입니다.</p>' \
        && tb_check "more than four measured values are listed as the first four and the rest" 'ko 첫 챕터에 측정값이 5개 있습니다(40분, 20분, 12분, 8분 등).' 0
    tb_case opencompound && tb_edit "$TB_R" '나누면 전체 시간이 40분에서 26분으로 줄어듭니다.' '나누면 전체 시간이 40분에서 26분 30초로 줄어듭니다.' \
        && tb_check "minutes followed by seconds are one measured value" '결과: ERROR 0 / WARN 0' 0
    tb_case opendate && tb_edit "$TB_R" '나누면 전체 시간이 40분에서 26분으로 줄어듭니다.' '나누면 2026년 1월 15일 기준 버전 2.1.7과 서버 6개, 워커 4대에서 전체 시간이 40분에서 26분으로 줄어듭니다.' \
        && tb_check "a date, a version and counts of things are not measured values" '결과: ERROR 0 / WARN 0' 0
    tb_case opencode && tb_edit "$TB_R" '<p>단계별로 시간을 재면 읽기 단계가' '<p><code>--timeout 30초 --retry 5회 --limit 10%</code>로 단계별로 시간을 재면 읽기 단계가' \
        && tb_check "numbers inside inline code are not counted" '결과: ERROR 0 / WARN 0' 0
    tb_case opencells && tb_edit "$TB_R" '<td>읽기</td>' '<td>읽기:</td>' '<td>집계</td>' '<td>집계:</td>' '<td>쓰기</td>' '<td>쓰기:</td>' \
            '느림' '분할 필요' '정상' '분리 완료' \
        && tb_check "a number in one table cell and a word in the next do not make a measured value" '결과: ERROR 0 / WARN 0' 0
    tb_case openen && tb_edit "$TB_R" 'cuts the run from 40 minutes to 26.' 'cuts the run from 40 minutes to 26, by 35% and 840초, in 3회.' \
        && assert_not_contains "check_post: measured values are counted on the Korean side only" \
            "$("${TB_PY[@]}" "$TB_CHECK" "$TB_R" 2>&1)" "측정값"
    tb_case altdot && tb_resub "$TB_R" 'alt="([^"]{3})' 'alt="\\1·' \
        && tb_check "middle dot in an image alt" '은 그림 alt에도 쓰지 않습니다' 1
    tb_case descdash && tb_resub "$TB_R" '<meta name="description" content="([^"]{3})' '<meta name="description" content="\\1—' \
        && tb_check "em dash in the meta description" '은 요약(meta description, excerpt)에도 쓰지 않습니다' 1
    tb_case copyko && tb_edit "$TB_R" '<span class="i">Copy</span><span class="ok">Copied</span>' '<span class="i">복사</span><span class="ok">복사됨</span>' \
        && tb_check "Korean copy button on the English side warns" '영어 쪽에 한글이 있습니다' 0
    tb_case hangul && tb_edit "$TB_R" '<td>Aggregate</td>' '<td>집계 Aggregate</td>' \
        && tb_check "Korean text on the English side warns" '영어 쪽에 한글이 있습니다 1곳' 0
    tb_case size && tb_edit "$TB_R" ' width="8" height="8"' '' \
        && tb_check "image without width and height warns" '그림에 width와 height가 없습니다' 0
    tb_case target && tb_edit "$TB_R" ' target="_blank" rel="noopener">example guide' '>example guide' \
        && tb_check "outside link without target warns" '바깥 링크는 target="_blank" rel="noopener"로 엽니다' 0
    tb_case layout && tb_edit "$TB_F" 'layout: report' 'layout: post' \
        && tb_check "front matter layout changed" 'front matter의 layout은 report여야 합니다' 1
    tb_case nokey && tb_resub "$TB_F" 'icon: sample\n' '' \
        && tb_check "front matter key removed" 'front matter에 icon 값이 없습니다' 1
    tb_case src && tb_edit "$TB_F" "$TB_SLUG-report.html" "$TB_SLUG-page.html" \
        && tb_check "report_src points at another file" 'front matter의 report_src가 이 파일을 가리키지 않습니다' 1
    tb_case body && printf '본문 한 줄\n' >> "$TB_F" \
        && tb_check "text after the front matter" 'front matter 파일에는 본문을 쓰지 않습니다' 1
    tb_case nofront && rm -f "$TB_F" \
        && tb_check "missing front matter file warns" 'front matter 파일을 찾지 못해 검사하지 않았습니다' 0
    tb_case blogcat && tb_edit "$TB_F" 'category: Sample' 'category: Missing' \
        && tb_check "category not in the blog's _config.yml" 'category가 블로그 _config.yml의 blog_categories에 없습니다: Missing' 1 --blog "$TB_BLOG"
    tb_case blogdir && tb_edit "$TB_F" 'category: Sample' 'category: Elsewhere' \
        && tb_check "report_src outside the category folder" 'report_src가 분류 폴더(/docs/other/) 아래가 아닙니다' 1 --blog "$TB_BLOG"
    tb_case blogicon && tb_edit "$TB_F" 'icon: sample' 'icon: nosuchicon' \
        && tb_check "icon not in the blog's assets/icons" 'icon 파일이 블로그 assets/icons에 없습니다: nosuchicon' 1 --blog "$TB_BLOG"

    # --- place_post.py: fake blog repository, git and bundle stubbed so a call would be recorded ---
    for tb_tool in git bundle; do
        printf '#!/bin/sh\necho "%s $*" >> "%s"\n' "$tb_tool" "$TB_W/bin/called.log" > "$TB_W/bin/$tb_tool"
        chmod +x "$TB_W/bin/$tb_tool"
    done
    TB_POSTS="$TB_BLOG/docs/techblog/sample"
    tb_place "places the built post (out/ also holds ko.md and urls.md)" "placed (stage these one by one" 0 "$TB_OUT"
    for tb_f in "$TB_SLUG.md" "$TB_SLUG-report.html" "$TB_SLUG-assets/fig01-flow.png"; do
        assert_file_exists "place_post: $tb_f is in the category folder" "$TB_POSTS/$tb_f"
        assert_contains "place_post: lists git add for $tb_f" "$TB_PLACED" "  git add docs/techblog/sample/$tb_f"
    done
    assert_eq "place_post: only the post's files are placed" "$TB_SLUG-assets $TB_SLUG-report.html $TB_SLUG.md " \
        "$(ls "$TB_POSTS" | sort | tr '\n' ' ')"
    tb_case replace && tb_edit "$TB_F" 'minutes: 3' 'minutes: 4' \
        && tb_place "stops at an existing slug without --replace" "같은 slug의 글이 이미 있습니다" 1 "$TB_C" \
        && assert_contains "place_post: the existing post is left as it was" "$(cat "$TB_POSTS/$TB_SLUG.md")" "minutes: 3" \
        && tb_place "overwrites with --replace" "placed (stage these one by one" 0 "$TB_C" --replace \
        && assert_contains "place_post: --replace wrote the new file" "$(cat "$TB_POSTS/$TB_SLUG.md")" "minutes: 4"
    mkdir -p "$TB_W/notblog"
    TB_BLOG="$TB_W/notblog" tb_place "refuses a folder that is not the blog repository" "블로그 저장소가 아닙니다" 1 "$TB_OUT"
    tb_blog cat
    tb_case placecat && tb_edit "$TB_F" 'category: Sample' 'category: Missing' \
        && tb_place "category not in _config.yml" "category가 _config.yml의 blog_categories에 없습니다: Missing" 1 "$TB_C"
    tb_case placedir && tb_edit "$TB_F" 'category: Sample' 'category: Elsewhere' \
        && tb_place "category that is not a post folder" "이 분류는 게시물 폴더가 아닙니다: /docs/other/" 1 "$TB_C"
    rm -f "$TB_BLOG/assets/icons/sample.svg"
    tb_place "runs check_post.py --blog on the placed files" "icon 파일이 블로그 assets/icons에 없습니다: sample" 1 "$TB_OUT"
    assert_contains "place_post: says the placed post failed the check" "$TB_PLACED" "배치한 글이 검사를 통과하지 못했습니다"
    assert_eq "place_post: never runs git (and bundle only with --build)" "" "$(cat "$TB_W/bin/called.log" 2>/dev/null | tr '\n' ' ')"
else
    fail "techblogs: built fixture" "build_post.py did not write $TB_OUT/$TB_SLUG-report.html: $TB_MSG"
fi

# --- build_post.py: an origin moves the canonical link; missing or unfinished input stops the build ---
tb_work origin
tb_meta '.origin = {name: {ko: "예시 블로그", en: "Example blog"}, url: "https://example.com/blog/original-post/", date: "2026-01-10"}'
TB_MSG=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" 2>&1); TB_RC=$?
assert_eq "build_post: a post with an origin builds (exit 0)" "0" "$TB_RC"
TB_PAGE=$(cat "$TB_WK/out/$TB_SLUG-report.html" 2>/dev/null)
assert_contains "build_post: canonical is the origin address" "$TB_PAGE" '<link rel="canonical" href="https://example.com/blog/original-post/">'
assert_contains "build_post: the head links the original" "$TB_PAGE" \
    'First published on <a href="https://example.com/blog/original-post/" target="_blank" rel="noopener">Example blog</a>'
assert_contains "build_post: the end names the original and its date" "$TB_PAGE" '</a>, published 2026-01-10.'
# A republished post keeps the structure of the original: no background paragraph check
tb_edit "$TB_WK/out/$TB_SLUG-report.html" '실행된다고 가정합니다.</p>' '실행된다고 가정합니다. 읽기 단계가 가장 깁니다.</p>'
TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1); TB_RC=$?
assert_not_contains "check_post: a republished post is not checked for the background paragraph" "$TB_MSG" "첫 챕터"
assert_contains "check_post: a republished post with a long first paragraph has no ERROR and no WARN" "$TB_MSG" "결과: ERROR 0 / WARN 0"
# A republished post keeps the opening of the original: no count of measured values
tb_edit "$TB_WK/out/$TB_SLUG-report.html" '나누면 전체 시간이 40분에서 26분으로 줄어듭니다.' '나누면 20분이던 읽기가 줄어 전체 시간이 40분에서 26분으로 줄어듭니다.' \
    '<h2>문제와 측정</h2>' '<h2>40분 걸리는 배치</h2>'
TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1); TB_RC=$?
assert_not_contains "check_post: a republished post is not checked for measured values in the opening" "$TB_MSG" "측정값"
assert_contains "check_post: a republished post with numbers in its opening has no ERROR and no WARN" "$TB_MSG" "결과: ERROR 0 / WARN 0"

# --- Reading time: a new post stays within 15 minutes; build_post.py and check_post.py count the same characters ---
# tb_fill_ko TOTAL [pre]: add filler to ko.body.html of TB_WK. Without "pre" the Korean body ends up with TOTAL
# characters outside code boxes (no whitespace, no tags); with "pre" TOTAL characters go into its code box
tb_fill_ko() {
    local msg
    msg=$("${TB_PY[@]}" - "$TB_WK/ko.body.html" "$@" 2>&1 <<'PY'
import pathlib, re, sys
path, total = sys.argv[1], int(sys.argv[2])
p = pathlib.Path(path)
s = p.read_text(encoding="utf-8")
count = lambda t: len(re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", re.sub(r"<pre>.*?</pre>", "", t, flags=re.S))))
if sys.argv[3:] == ["pre"]:
    s, n = re.subn(r"(<pre><code>)", lambda m: m.group(1) + "가" * total, s, count=1)
else:
    need = total - count(s)
    if need <= 0:
        sys.exit("the fixture is already longer than %d" % total)
    s, n = re.subn(r'(id="ko-s2".*?</p>)', lambda m: m.group(1) + "\n<p>" + "가" * need + "</p>", s, count=1, flags=re.S)
    if count(s) != total:
        sys.exit("filler did not reach %d: %d" % (total, count(s)))
if n != 1:
    sys.exit("place for the filler not found")
p.write_text(s, encoding="utf-8")
PY
    ) && return 0
    fail "techblogs reading-time fixture" "$msg"
    return 1
}
# 15.4 minutes rounds to 15 and passes; 15.6 minutes rounds to 16 and warns
tb_work min15
if tb_fill_ko 10780 && "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1; then
    assert_contains "build_post: 10,780 characters of Korean body read in 15 minutes" "$(cat "$TB_WK/out/$TB_SLUG.md" 2>/dev/null)" "minutes: 15"
    TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1)
    assert_not_contains "check_post: a 15-minute post has no reading-time warning" "$TB_MSG" "읽는 시간이"
    assert_contains "check_post: a 15-minute post has no ERROR and no WARN" "$TB_MSG" "결과: ERROR 0 / WARN 0"
else
    fail "build_post: a 15-minute post builds" "tb_fill_ko or build_post.py failed"
fi
tb_work min16
if tb_fill_ko 10920 && "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1; then
    assert_contains "build_post: 10,920 characters of Korean body read in 16 minutes" "$(cat "$TB_WK/out/$TB_SLUG.md" 2>/dev/null)" "minutes: 16"
    TB_MSG=$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1); TB_RC=$?
    assert_contains "check_post: a 16-minute post warns with the minutes build_post.py shows and says to cut or split" "$TB_MSG" \
        "읽는 시간이 16분입니다. 새 글은 15분을 넘기지 않습니다. 겹치는 내용을 줄이거나 연재(1부, 2부)로 나눕니다. 이전에 올린 글은 사용자가 요청할 때 고칩니다."
    assert_contains "check_post: the reading-time finding is a WARN, not an ERROR" "$TB_MSG" "결과: ERROR 0 / WARN 1"
    assert_eq "check_post: the reading-time warning leaves the exit code 0" "0" "$TB_RC"
else
    fail "build_post: a 16-minute post builds" "tb_fill_ko or build_post.py failed"
fi
# minutes written by hand in meta.json changes what the page shows, not what the checker counts
tb_work minhand
tb_meta '.minutes = 9'
if tb_fill_ko 10920 && "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1; then
    assert_contains "build_post: minutes in meta.json is shown as written" "$(cat "$TB_WK/out/$TB_SLUG.md" 2>/dev/null)" "minutes: 9"
    assert_contains "check_post: minutes written by hand does not hide a long post" \
        "$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1)" "읽는 시간이 16분입니다."
else
    fail "build_post: a post with minutes in meta.json builds" "tb_fill_ko or build_post.py failed"
fi
# text inside a code box is not counted
tb_work mincode
if tb_fill_ko 12000 pre && "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1; then
    assert_contains "build_post: characters inside a code box do not add reading time" "$(cat "$TB_WK/out/$TB_SLUG.md" 2>/dev/null)" "minutes: 3"
    assert_not_contains "check_post: characters inside a code box do not add reading time" \
        "$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1)" "읽는 시간이"
else
    fail "build_post: a post with a long code box builds" "tb_fill_ko or build_post.py failed"
fi
# a republished post keeps the length of the original
tb_work minorigin
tb_meta '.origin = {name: {ko: "예시 블로그", en: "Example blog"}, url: "https://example.com/blog/original-post/", date: "2026-01-10"}'
if tb_fill_ko 10920 && "${TB_PY[@]}" "$TB_BUILD" "$TB_WK" >/dev/null 2>&1; then
    assert_not_contains "check_post: a republished post is not checked for the reading time" \
        "$("${TB_PY[@]}" "$TB_CHECK" "$TB_WK/out/$TB_SLUG-report.html" 2>&1)" "읽는 시간이"
else
    fail "build_post: a long republished post builds" "tb_fill_ko or build_post.py failed"
fi
tb_work alt
TB_MSG=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" --out "$TB_W/alt-out" 2>&1); TB_RC=$?
assert_eq "build_post: --out DIR builds (exit 0)" "0" "$TB_RC"
assert_file_exists "build_post: --out DIR holds the report" "$TB_W/alt-out/$TB_SLUG-report.html"
[ ! -e "$TB_WK/out" ] && pass "build_post: --out DIR leaves the default out/ alone" \
    || fail "build_post: --out DIR leaves the default out/ alone" "$TB_WK/out exists"
tb_work todo && tb_meta '.thesis.en = "TODO"'
tb_build_fails 'a "TODO" in meta.json' 'meta.json: thesis.en 가 TODO로 남아 있습니다'
assert_eq 'build_post: a "TODO" in meta.json leaves no report' "" "$(find "$TB_WK" -name '*-report.html' | tr '\n' ' ')"
tb_work noen && rm -f "$TB_WK/en.body.html"
tb_build_fails "no English fragment" 'en.body.html 가 없습니다'
tb_work pair && tb_meta '.title.en = ""'
tb_build_fails "a value without its English text" 'meta.json: title 에 ko와 en 값이 모두 있어야 합니다'
tb_work slug && tb_meta '.slug = "Bad_Slug"'
tb_build_fails "slug with other characters" 'meta.json: slug는 영문 소문자, 숫자, 하이픈만 씁니다'
tb_work noimg && rm -f "$TB_WK/images/fig01-flow.png"
tb_build_fails "image file missing" '그림 파일이 없습니다: images/fig01-flow.png'
tb_work secid && tb_edit "$TB_WK/ko.body.html" 'id="ko-s2"' 'id="ko-s3"'
tb_build_fails "section id out of sequence" 'ko.body.html: 2번째 챕터의 id가 ko-s2 가 아니라 ko-s3 입니다'
tb_work seccount && tb_resub "$TB_WK/en.body.html" '<section class="sec" id="en-s2">.*?</section>\n' ''
tb_build_fails "English fragment with fewer sections" '챕터 수가 다릅니다: ko 2, en 1'
tb_work storyline-unknown; tb_meta '.storyline = "essay"'
tb_build_fails "a storyline that is not in the list" \
    'meta.json: storyline은 qa, troubleshoot, measure, compare, build, anatomy, change, retro 가운데 하나입니다: essay'
tb_work storyline-missing; tb_meta 'del(.storyline)'
TB_SL=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" 2>&1); TB_SL_RC=$?
assert_eq "build_post: a new post without a storyline still builds (exit 0)" "0" "$TB_SL_RC"
assert_contains "build_post: warns when a new post has no storyline" "$TB_SL" \
    "WARN  meta.json에 storyline이 없습니다. 새 글은 references/storylines.md에서 스토리라인을 골라 적습니다."
tb_work storyline-origin
tb_meta 'del(.storyline) | .origin = {"name": {"ko": "예시 블로그", "en": "Example blog"}, "url": "https://example.com/original", "date": "2026-01-10"}'
TB_SL=$("${TB_PY[@]}" "$TB_BUILD" "$TB_WK" 2>&1); TB_SL_RC=$?
assert_eq "build_post: a republished post without a storyline builds (exit 0)" "0" "$TB_SL_RC"
assert_not_contains "build_post: a republished post gets no storyline warning" "$TB_SL" "WARN"
# The --out guard is tried on a copy of the skill, so a broken guard cannot write into skills/
mkdir -p "$TB_W/skillcopy" && cp -a "$TB_DIR" "$TB_W/skillcopy/techblogs"
tb_work guard
TB_MSG=$("${TB_PY[@]}" "$TB_W/skillcopy/techblogs/scripts/build_post.py" "$TB_WK" --out "$TB_W/skillcopy/techblogs/assets/out" 2>&1); TB_RC=$?
assert_contains "build_post: --out inside the skill folder is refused" "$TB_MSG" "skill 폴더 안에는 쓰지 않습니다"
assert_eq "build_post: --out inside the skill folder exits 1" "1" "$TB_RC"
[ ! -e "$TB_W/skillcopy/techblogs/assets/out" ] && pass "build_post: nothing written into the skill folder" \
    || fail "build_post: nothing written into the skill folder" "$TB_W/skillcopy/techblogs/assets/out exists"

# --- import_aws_post.py: a saved page (no images, no network) becomes a work folder ---
TB_IMP="$TB_W/imp"
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "$TB_FIX/aws-post.html" "$TB_IMP" 2>&1); TB_RC=$?
assert_eq "import_aws_post: the saved page imports (exit 0)" "0" "$TB_RC"
assert_contains "import_aws_post: counts sections, figures and sources" "$TB_MSG" "sections: 3, figures: 0, sources: 2"
assert_eq "import_aws_post: meta.json slug, title, date, tag, origin" \
    "sample-import-post|가상의 대기열 작업자 수 정하기|2026-01-10|Sample Category|https://aws.amazon.com/ko/blogs/tech/sample-import-post/" \
    "$(jq -r '[.slug, .title.ko, .date, .tags[0], .origin.url] | join("|")' "$TB_IMP/meta.json" 2>/dev/null)"
assert_eq "import_aws_post: references become sources with a kind" \
    "예시 사용 설명서|https://docs.aws.amazon.com/example/latest/guide.html|AWS docs|TODO;예시 노트|https://example.com/notes|Web|TODO" \
    "$(jq -r '[.sources[] | [.title, .url, .kind.en, .accessed] | join("|")] | join(";")' "$TB_IMP/meta.json" 2>/dev/null)"
assert_eq "import_aws_post: the closing note goes to meta.json, fields to fill are TODO" \
    "이 글의 수치는 지어낸 값입니다.|TODO|TODO|TODO" \
    "$(jq -r '[.note.ko, .category, .title.en, .thesis.ko] | join("|")' "$TB_IMP/meta.json" 2>/dev/null)"
TB_BODY=$(cat "$TB_IMP/ko.body.html" 2>/dev/null)
for tb_t in '<section class="sec" id="ko-s1"><header class="sec-head"><h2>들어가며</h2>' \
            '<section class="sec" id="ko-s2"><header class="sec-head"><p class="eyebrow">01</p><h2>측정</h2>' \
            '<section class="sec" id="ko-s3"><header class="sec-head"><p class="eyebrow">02</p><h2>설정</h2>' \
            '<div class="scroll"><table>' '<tr><th>작업자 수</th><th>처리 시간(초)</th></tr>' \
            '<p class="cap"><b>표 1.</b> 작업자 수별 처리 시간</p>' '<h3>고른 값</h3>' \
            '<li>작업자 <b>4개</b>를 씁니다.</li>' \
            '<a href="https://aws.amazon.com/ko/sample-page/" target="_blank" rel="noopener">예시 페이지</a>의 권장값입니다.' \
            '<span class="lang">bash</span>' '<pre><code>queue-tool set --workers 4 &amp;&amp; queue-tool show</code></pre>' \
            '<blockquote><p>값을 바꾼 뒤에는 처리 시간을 다시 잽니다.</p></blockquote>'; do
    assert_contains "import_aws_post body: $tb_t" "$TB_BODY" "$tb_t"
done
assert_not_contains "import_aws_post body: the reference list is not a section" "$TB_BODY" "참고 자료"
assert_not_contains "import_aws_post body: inline style is dropped" "$TB_BODY" "style="
TB_WK="$TB_IMP" tb_build_fails "an imported folder does not build while TODO remains" 'meta.json: category 가 TODO로 남아 있습니다'
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "$TB_FIX/aws-post.html" "$TB_W/imp-slug" --slug custom-slug 2>&1); TB_RC=$?
assert_eq "import_aws_post: --slug NAME imports (exit 0)" "0" "$TB_RC"
assert_eq "import_aws_post: --slug NAME sets the slug" "custom-slug" "$(jq -r '.slug' "$TB_W/imp-slug/meta.json" 2>/dev/null)"
# An image on another host is not fetched: the host check comes before any connection
cp "$TB_FIX/aws-post.html" "$TB_W/aws-post-img.html"
tb_edit "$TB_W/aws-post-img.html" '<h2>2. 설정</h2>' \
    '<p><img src="https://img.invalid/shots/queue.png" alt="대기열 화면" width="960" height="540"></p><p>그림 1. 대기열 화면 예시</p><h2>2. 설정</h2>'
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "$TB_W/aws-post-img.html" "$TB_W/imp-img" 2>&1); TB_RC=$?
assert_eq "import_aws_post: an image it does not fetch does not stop the import (exit 0)" "0" "$TB_RC"
assert_contains "import_aws_post: warns about the image it did not fetch" "$TB_MSG" "WARN  그림을 받지 못했습니다: https://img.invalid/shots/queue.png"
assert_contains "import_aws_post: fetches images only from the AWS blog hosts" "$TB_MSG" "AWS 블로그 호스트가 아닙니다"
assert_contains "import_aws_post: the figure is in the body with its caption" "$(cat "$TB_W/imp-img/ko.body.html" 2>/dev/null)" \
    '<figure class="fig"><div class="canvas wide"><img src="images/fig01-queue.png" alt="대기열 화면" width="960" height="540" loading="lazy"></div><figcaption><b>그림 1.</b> 대기열 화면 예시</figcaption></figure>'
[ ! -e "$TB_W/imp-img/images/fig01-queue.png" ] && pass "import_aws_post: no empty file is left for an image it did not fetch" \
    || fail "import_aws_post: no empty file is left for an image it did not fetch" "$TB_W/imp-img/images/fig01-queue.png exists"
# Pictures and links in other shapes: a picture at the end of a text paragraph as inline base64, an editor placeholder,
# a reference with a note after the link, a javascript: link, a root-relative link on a /ko/ page, a block it cannot place
TB_B64=$(base64 -w0 "$TB_FIX/work/images/fig01-flow.png")
cp "$TB_FIX/aws-post.html" "$TB_W/aws-post-media.html"
tb_edit "$TB_W/aws-post-media.html" '<h2>2. 설정</h2>' \
    "<p>처리 흐름은 다음 그림에 정리했습니다.<img src=\"image/png;base64,$TB_B64\" alt=\"\" width=\"8\" height=\"8\"><img src=\"PLACEHOLDER_IMAGE_01\" alt=\"\"></p><h2>2. 설정</h2>" \
    '<li><a href="https://example.com/notes">예시 노트</a></li>' \
    '<li><a href="https://example.com/notes">예시 노트</a> – 예시 게시처 (2026-01-10 확인)</li><li><a href="javascript:alert(1)">위험한 링크</a></li>' \
    '<p>다음 명령으로 작업자 수를 바꿉니다.</p>' \
    '<p>다음 명령으로 <a href="javascript:alert(1)">작업자 수</a>를 바꿉니다. 발표는 <a href="/about-aws/whats-new/sample/">새 소식</a>에 있습니다.</p><dl><dt>옮기지 않는 블록</dt></dl>'
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "$TB_W/aws-post-media.html" "$TB_W/imp-media" 2>&1); TB_RC=$?
assert_eq "import_aws_post: a page with mixed pictures imports (exit 0)" "0" "$TB_RC"
assert_contains "import_aws_post: counts the one real picture and reports the coverage" "$TB_MSG" "figures: 1, sources: 2, coverage: "
assert_contains "import_aws_post: warns about a picture without caption and alt" "$TB_MSG" "WARN  그림 1에 캡션과 alt가 없습니다"
assert_contains "import_aws_post: reports a block it left out" "$TB_MSG" "WARN  옮기지 않은 블록: dl: 옮기지 않는 블록"
TB_BODY=$(cat "$TB_W/imp-media/ko.body.html" 2>/dev/null)
assert_contains "import_aws_post: text before a picture stays a paragraph" "$TB_BODY" '<p>처리 흐름은 다음 그림에 정리했습니다.</p>'
assert_contains "import_aws_post: the picture becomes a figure with its number" "$TB_BODY" \
    '<figure class="fig"><div class="canvas"><img src="images/fig01.png" alt="그림 1" width="8" height="8" loading="lazy"></div><figcaption><b>그림 1.</b></figcaption></figure>'
assert_eq "import_aws_post: the figure follows the paragraph it was in" "1" \
    "$(printf '%s\n' "$TB_BODY" | grep -n -F -e '<p>처리 흐름은 다음 그림에 정리했습니다.</p>' -e 'src="images/fig01.png"' | cut -d: -f1 | paste -sd' ' | awk '{print $2 - $1}')"
cmp -s "$TB_W/imp-media/images/fig01.png" "$TB_FIX/work/images/fig01-flow.png" && pass "import_aws_post: an inline base64 picture is saved as a file" \
    || fail "import_aws_post: an inline base64 picture is saved as a file" "images/fig01.png differs from the source picture"
assert_not_contains "import_aws_post: an editor placeholder picture is dropped" "$TB_BODY" "PLACEHOLDER"
assert_not_contains "import_aws_post: the base64 data does not stay in the body" "$TB_BODY" "base64"
assert_contains "import_aws_post: a javascript: link keeps its text and loses the link" "$TB_BODY" '<p>다음 명령으로 작업자 수를 바꿉니다.'
assert_not_contains "import_aws_post: no javascript: address in the body" "$TB_BODY" "javascript:"
assert_not_contains "import_aws_post: no javascript: address in meta.json" "$(cat "$TB_W/imp-media/meta.json" 2>/dev/null)" "javascript:"
assert_contains "import_aws_post: a root-relative link on a /ko/ page gets the /ko/ address" "$TB_BODY" \
    '<a href="https://aws.amazon.com/ko/about-aws/whats-new/sample/" target="_blank" rel="noopener">새 소식</a>'
assert_eq "import_aws_post: the note after a reference link stays in the title, with a hyphen for the dash" \
    "예시 노트 - 예시 게시처 (2026-01-10 확인)" "$(jq -r '.sources[1].title' "$TB_W/imp-media/meta.json" 2>/dev/null)"
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "https://blog.invalid/sample-post/" "$TB_W/imp-url" 2>&1); TB_RC=$?
assert_contains "import_aws_post: an address outside the AWS blog hosts is refused" "$TB_MSG" "AWS 블로그 호스트가 아닙니다: https://blog.invalid/sample-post/"
assert_eq "import_aws_post: a refused address exits 1" "1" "$TB_RC"
printf '<html><body><p>no article here</p></body></html>\n' > "$TB_W/no-article.html"
TB_MSG=$("${TB_PY[@]}" "$TB_IMPORT" "$TB_W/no-article.html" "$TB_W/imp-none" 2>&1); TB_RC=$?
assert_contains "import_aws_post: a page without the article body is refused" "$TB_MSG" "본문(section.blog-post-content)을 찾지 못했습니다"
assert_eq "import_aws_post: a page without the article body exits 1" "1" "$TB_RC"

# --- new_post.py: a work folder from the storyline template chosen for the topic and the material ---
TB_NEW="$TB_DIR/scripts/new_post.py"
TB_NL=$("${TB_PY[@]}" "$TB_NEW" --list 2>&1); TB_NL_RC=$?
assert_eq "new_post --list: exit 0" "0" "$TB_NL_RC"
assert_eq "new_post --list: every storyline with the material it fits, its signals and its section flow" "8 8 8 8" \
    "$(printf '%s\n' "$TB_NL" | LC_ALL=C awk '/^[a-z]+ \(/{k++} /^  맞는 소재: ./{f++} /^  보이는 신호: ./{g++} /^  챕터 흐름: ./{w++} END{print k, f, g, w}')"
for tb_k in qa troubleshoot measure compare build anatomy change retro; do
    assert_contains "new_post --list: names $tb_k" "$TB_NL" "$tb_k ("
    TB_NP=$("${TB_PY[@]}" "$TB_NEW" "$TB_W/np-$tb_k" --storyline "$tb_k" --slug "np-$tb_k" --date 2026-01-15 2>&1); TB_NP_RC=$?
    assert_eq "new_post $tb_k: writes the work folder (exit 0)" "0" "$TB_NP_RC"
    assert_eq "new_post $tb_k: meta.json has the storyline, slug and date, the rest is TODO" "$tb_k|np-$tb_k|2026-01-15|TODO|TODO" \
        "$(jq -r '[.storyline, .slug, .date, .title.ko, .category] | join("|")' "$TB_W/np-$tb_k/meta.json" 2>/dev/null)"
    # grep, not a sed pattern with ".": under C.UTF-8 "." does not match every Hangul syllable
    tb_n=$(printf '%s\n' "$TB_NP" | grep -o 'sections: [0-9]*$' | head -1 | tr -dc '0-9')
    assert_eq "new_post $tb_k: one section per step of the flow in both bodies, a guide per section and one for the background paragraph" "$tb_n $tb_n $((tb_n + 1))" \
        "$(grep -c 'id="ko-s' "$TB_W/np-$tb_k/ko.body.html" 2>/dev/null) $(grep -c 'id="en-s' "$TB_W/np-$tb_k/en.body.html" 2>/dev/null) $(grep -c '<!-- 안내: ' "$TB_W/np-$tb_k/ko.body.html" 2>/dev/null)"
    [ "${tb_n:-0}" -ge 5 ] && pass "new_post $tb_k: at least five sections" || fail "new_post $tb_k: at least five sections" "sections: ${tb_n:-none}"
    # The place of the background paragraph: once per body, with the line of this storyline in storylines.md
    tb_lead='<!-- 안내: 배경 문단. 한두 문장으로 쓴다. '
    assert_eq "new_post $tb_k: one place for the background paragraph in each body" "1 1" \
        "$(grep -cF -- "$tb_lead" "$TB_W/np-$tb_k/ko.body.html" 2>/dev/null) $(grep -cF -- "$tb_lead" "$TB_W/np-$tb_k/en.body.html" 2>/dev/null)"
    tb_bg=$(grep -F -- "$tb_lead" "$TB_W/np-$tb_k/ko.body.html" 2>/dev/null | head -1)
    tb_bg=${tb_bg#"$tb_lead"}; tb_bg=${tb_bg%' -->'}
    [ -n "$tb_bg" ] && sed -n "/^## $tb_k: /,/^## /p" "$TB_DIR/references/storylines.md" | grep -qxF -- "- **배경 문단**: $tb_bg" \
        && pass "new_post $tb_k: the background guide is the line of this storyline in storylines.md" \
        || fail "new_post $tb_k: the background guide is the line of this storyline in storylines.md" "guide: ${tb_bg:-none}"
    assert_contains "new_post $tb_k: the output says the first section opens with the background paragraph" "$TB_NP" \
        "첫 챕터는 배경 문단(주제의 배경이나 필요, 한두 문장)으로 시작합니다: $tb_bg"
    # Opening (2026-11-28): the guide of the first section and the output carry the meaning line of this storyline
    tb_mean=$(sed -n "/^## $tb_k: /,/^## /p" "$TB_DIR/references/storylines.md" | sed -n 's/^- \*\*서두의 의미\*\*: //p' | head -1)
    tb_how=$(sed -n "/^## $tb_k: /,/^## /p" "$TB_DIR/references/storylines.md" | sed -n 's/^- \*\*여는 방식\*\*: //p' | head -1)
    [ -n "$tb_mean" ] && [ -n "$tb_how" ] && grep -qF -- " 서두의 의미: $tb_mean 여는 방식: $tb_how -->" "$TB_W/np-$tb_k/ko.body.html" \
        && grep -qF -- " 서두의 의미: $tb_mean 여는 방식: $tb_how -->" "$TB_W/np-$tb_k/en.body.html" \
        && pass "new_post $tb_k: the first section guide names the meaning of the opening, then how the storyline opens" \
        || fail "new_post $tb_k: the first section guide names the meaning of the opening, then how the storyline opens" "meaning: ${tb_mean:-none}"
    assert_eq "new_post $tb_k: the meaning is named in the first section only" "1" \
        "$(grep -cF -- " 서두의 의미: " "$TB_W/np-$tb_k/ko.body.html" 2>/dev/null)"
    assert_contains "new_post $tb_k: the output says the opening starts with the meaning, with two measured values at most in each place" "$TB_NP" \
        "서두(요약 문단, 요점, 첫 챕터)는 테스트 결과가 아니라 의미로 엽니다. 측정값은 한 곳에 둘까지 쓰고 나머지는 결과를 다루는 챕터에 둡니다: $tb_mean"
    assert_contains "new_post $tb_k: the output states the reading-time limit" "$TB_NP" \
        "읽는 시간은 15분 이하로 씁니다(한국어 본문 약 10,500자, 코드 상자 제외). 넘으면 줄이거나 연재로 나눕니다."
done
assert_eq "new_post: the troubleshoot template has the six steps of storylines.md" "6" \
    "$(grep -c 'id="ko-s' "$TB_W/np-troubleshoot/ko.body.html" 2>/dev/null)"
TB_BODY=$(cat "$TB_W/np-troubleshoot/ko.body.html" 2>/dev/null)
assert_contains "new_post: the first section carries the step, the meaning of the opening and how the storyline opens" "$TB_BODY" \
    '<!-- 안내: 1번째 챕터. 이 장애가 드러낸 것과 증상(에러 원문, 화면, 발생 시각) 서두의 의미: 이 장애가 드러낸 잘못된 가정과 같은 구성을 쓰는 독자가 확인할 것 여는 방식: 의미를 말한 뒤 증상을 그대로 보여 준다.'
assert_contains "new_post: the background paragraph comes first in the first section, then the step" "$TB_BODY" \
    $'<div class="prose">\n<!-- 안내: 배경 문단. 한두 문장으로 쓴다. 증상이 생긴 시스템이 맡은 일과 이 증상 때문에 멈추거나 틀어지는 것 -->\n<p>TODO</p>\n<!-- 안내: 1번째 챕터. 이 장애가 드러낸 것과 증상('
assert_eq "new_post: only the first section has the place of the background paragraph" "1" \
    "$(sed -n '/id="ko-s1"/,/<\/section>/p' "$TB_W/np-troubleshoot/ko.body.html" 2>/dev/null | grep -cF '<!-- 안내: 배경 문단.')"
assert_contains "new_post: the last section carries how the storyline closes" "$TB_BODY" '<!-- 안내: 6번째 챕터. 재발을 막는 장치 닫는 방식: '
assert_contains "new_post: the first section has no number, the second is 01" "$TB_BODY" \
    '<section class="sec" id="ko-s2"><header class="sec-head"><p class="eyebrow">01</p><h2>TODO</h2></header>'
# The template does not build as it is: meta.json first, then the bodies
TB_WK="$TB_W/np-troubleshoot" tb_build_fails "a new work folder does not build while meta.json is TODO" 'meta.json: category 가 TODO로 남아 있습니다'
jq --slurpfile f "$TB_FIX/work/meta.json" '$f[0] + {slug: .slug, storyline: .storyline}' "$TB_W/np-troubleshoot/meta.json" \
    > "$TB_W/np-troubleshoot/meta.tmp" && mv "$TB_W/np-troubleshoot/meta.tmp" "$TB_W/np-troubleshoot/meta.json"
TB_WK="$TB_W/np-troubleshoot" tb_build_fails "a template body does not build while TODO and guide comments remain" \
    'ko.body.html: 템플릿의 TODO나 안내 주석이 남아 있습니다'
# tb_fill FILE todo|guide: fill in the TODO titles and paragraphs, or take out the guide comments
tb_fill() {
    "${TB_PY[@]}" - "$1" "$2" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
if sys.argv[2] == "guide":
    s = re.sub(r"<!-- 안내: [^\n]*-->\n", "", s)
else:
    s = s.replace("<h2>TODO</h2>", "<h2>Sample</h2>").replace("<p>TODO</p>", "<p>Sample.</p>")
p.write_text(s, encoding="utf-8")
PY
}
tb_fill "$TB_W/np-troubleshoot/ko.body.html" todo
TB_WK="$TB_W/np-troubleshoot" tb_build_fails "a body with only the guide comments left does not build" \
    'ko.body.html: 템플릿의 TODO나 안내 주석이 남아 있습니다'
tb_fill "$TB_W/np-troubleshoot/ko.body.html" guide
tb_fill "$TB_W/np-troubleshoot/en.body.html" guide
TB_WK="$TB_W/np-troubleshoot" tb_build_fails "a body with only the TODO text left does not build" \
    'en.body.html: 템플릿의 TODO나 안내 주석이 남아 있습니다'
tb_fill "$TB_W/np-troubleshoot/en.body.html" todo
TB_NP=$("${TB_PY[@]}" "$TB_BUILD" "$TB_W/np-troubleshoot" 2>&1); TB_NP_RC=$?
assert_eq "new_post: the folder builds once the template is filled in (exit 0)" "0" "$TB_NP_RC"
assert_contains "new_post: the built post names its storyline" "$TB_NP" "storyline: troubleshoot"
# Refusals: nothing is overwritten, unknown values stop, the skill folder is not a work folder
TB_NP=$("${TB_PY[@]}" "$TB_NEW" "$TB_W/np-qa" --storyline measure --slug again 2>&1); TB_NP_RC=$?
assert_contains "new_post: an existing work folder is not overwritten" "$TB_NP" "이미 있는 파일은 덮어쓰지 않습니다"
assert_eq "new_post: an existing work folder exits 1" "1" "$TB_NP_RC"
assert_eq "new_post: the existing meta.json is left as it was" "qa" "$(jq -r '.storyline' "$TB_W/np-qa/meta.json" 2>/dev/null)"
TB_NP=$("${TB_PY[@]}" "$TB_NEW" "$TB_W/np-bad" --storyline essay --slug bad 2>&1); TB_NP_RC=$?
assert_contains "new_post: a storyline that is not in the list is refused" "$TB_NP" \
    "storyline은 qa, troubleshoot, measure, compare, build, anatomy, change, retro 가운데 하나입니다: essay"
assert_eq "new_post: an unknown storyline exits 1" "1" "$TB_NP_RC"
[ ! -e "$TB_W/np-bad" ] && pass "new_post: a refused run leaves no folder" || fail "new_post: a refused run leaves no folder" "$TB_W/np-bad exists"
TB_NP=$("${TB_PY[@]}" "$TB_NEW" "$TB_W/np-slug" --storyline qa --slug Bad_Slug 2>&1); TB_NP_RC=$?
assert_contains "new_post: a slug with other characters is refused" "$TB_NP" "slug는 영문 소문자, 숫자, 하이픈만 씁니다: Bad_Slug"
assert_eq "new_post: a bad slug exits 1" "1" "$TB_NP_RC"
TB_NP=$("${TB_PY[@]}" "$TB_W/skillcopy/techblogs/scripts/new_post.py" "$TB_W/skillcopy/techblogs/newpost" --storyline qa --slug inside 2>&1); TB_NP_RC=$?
assert_contains "new_post: the skill folder is not a work folder" "$TB_NP" "skill 폴더 안에는 쓰지 않습니다"
assert_eq "new_post: a work folder inside the skill exits 1" "1" "$TB_NP_RC"
[ ! -e "$TB_W/skillcopy/techblogs/newpost" ] && pass "new_post: nothing is written inside the skill" \
    || fail "new_post: nothing is written inside the skill" "newpost exists in the skill copy"

# --- nothing was written into the skill folder ---
assert_eq "techblogs: the skill folder is unchanged by the scripts" "$TB_FILES_BEFORE" "$(find "$TB_DIR" | sort)"
assert_eq "techblogs: no __pycache__ in the skill" "" "$(find "$TB_DIR" -name __pycache__ | tr '\n' ' ')"

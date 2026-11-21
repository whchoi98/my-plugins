#!/bin/bash
# aws-ppt-skills: the output-format question and the HTML deck. SKILL.md and references/html-deck.md agree with
# the shipped scripts and the runtime files; the helpers of deck_to_html.py that need no deck (number formats,
# tick scale, preset shapes); and, when the deck tools are installed, a deck built from the SKILL.md helper
# block, templated, converted to HTML and opened in a browser (sourced by tests/run-all.sh). The deck content is
# tests/fixtures/aws-ppt-skills/html-deck.js. Nothing is written into skills/ (Python bytecode goes to $TEST_TMP).

PP_DIR=skills/aws-ppt-skills
PP_FIX=tests/fixtures/aws-ppt-skills
PP_PY=(python3 -X pycache_prefix="$TEST_TMP/pp-pycache")        # may use python-pptx, lxml, Pillow, fontTools from the user site
PP_PYI=(python3 -I -X pycache_prefix="$TEST_TMP/pp-pycache")    # standard library only
PP_REPO=$(pwd -P)
PP_W="$TEST_TMP/pp"
mkdir -p "$PP_W/deck/icons" "$PP_W/emptybin"
PP_SKILL=$(cat "$PP_DIR/SKILL.md" 2>/dev/null)
PP_REF=$(cat "$PP_DIR/references/html-deck.md" 2>/dev/null)
PP_DESC=$(sed -n '2,/^---$/s/^description: //p' "$PP_DIR/SKILL.md" 2>/dev/null)
PP_JS=$(cat "$PP_DIR/assets/html/deck.js" 2>/dev/null)
PP_CSS=$(cat "$PP_DIR/assets/html/deck.css" 2>/dev/null)
touch "$PP_W/before"

# --- Skill files ---
for pp_f in SKILL.md scripts/deck_to_html.py scripts/preview_html_deck.py assets/html/deck.css assets/html/deck.js \
            references/html-deck.md; do
    assert_file_exists "aws-ppt-skills: $pp_f" "$PP_DIR/$pp_f"
done

# --- Description: both outputs are named, and it still triggers on decks ---
for pp_t in "PowerPoint" "HTML" "presenter view" "browser"; do
    assert_contains "aws-ppt-skills description: '$pp_t'" "$PP_DESC" "$pp_t"
done

# --- Workflow: the output format is asked first, as one question with three answers ---
assert_contains "workflow: five things are confirmed" "$PP_SKILL" "always confirm five things BEFORE generating"
assert_not_contains "workflow: the old count is gone" "$PP_SKILL" "confirm four things"
PP_WF=$(printf '%s\n' "$PP_SKILL" | sed -n '/^## Workflow (mandatory first step)/,/^---$/p')
PP_FIRST=$(printf '%s\n' "$PP_WF" | grep -m1 '^1\. ')
assert_contains "workflow: item 1 is the output format" "$PP_FIRST" "1. **Output format**"
assert_contains "workflow: the question is part of item 1" "$PP_FIRST" 'PPT와 HTML 두 가지를 모두 만들까요, 한 가지만 만들까요? (PPT만 / HTML만 / PPT와 HTML 둘 다)'
for pp_t in '   - `PPT만` - ' '   - `HTML만` - ' '   - `PPT와 HTML 둘 다` - ' \
            'Never pick a format for the user' \
            'the format is `PPT만` unless the user asked for an HTML deck' \
            '`HTML만` or `PPT와 HTML 둘 다`: convert the checked `.pptx` and check the page'; do
    assert_contains "workflow: '$pp_t'" "$PP_WF" "$pp_t"
done
PP_ITEMS=$(printf '%s\n' "$PP_WF" | sed -n '1,/^After generation:/p' | grep -c '^[0-9]\. \*\*')
assert_eq "workflow: five numbered items" "5" "$PP_ITEMS"
assert_contains "forbidden list: the format is never chosen without asking" "$PP_SKILL" "Choosing the output format (PPT, HTML or both) without asking"

# --- HTML Deck section: where the page comes from, the two commands, the rules ---
PP_SEC=$(printf '%s\n' "$PP_SKILL" | sed -n '/^## HTML Deck$/,/^## /p')
for pp_t in 'python3 "$SKILL_DIR/scripts/deck_to_html.py" <DeckName>.pptx' \
            'uv run --no-project --with playwright==1.64.1 python "$SKILL_DIR/scripts/preview_html_deck.py" <DeckName>.html --out-dir qa-html' \
            'converted from the finished `.pptx`' 'Never write or edit the HTML by hand' '`--no-notes`' \
            'references/html-deck.md' '`HTML만`' 'one self-contained file' 'key N'; do
    assert_contains "HTML Deck section: '$pp_t'" "$PP_SEC" "$pp_t"
done
for pp_t in '`scripts/deck_to_html.py`' '`scripts/preview_html_deck.py`' '`assets/html/deck.css`, `assets/html/deck.js`' \
            '`references/html-deck.md`'; do
    assert_contains "bundled assets table: $pp_t" "$(printf '%s\n' "$PP_SKILL" | grep '^| ')" "$pp_t"
done
assert_contains "build workflow: the HTML step" "$(printf '%s\n' "$PP_SKILL" | sed -n '/^## Build Workflow Detail/,/^---$/p')" 'deck_to_html.py'
assert_contains "final delivery: the .html is named" "$(printf '%s\n' "$PP_SKILL" | sed -n '/^## Final Delivery/,$p')" '<DeckName>.html'
assert_contains "final delivery: the key guide goes with the page" "$(printf '%s\n' "$PP_SKILL" | sed -n '/^## Final Delivery/,$p')" '발표자 안내'

# --- references/html-deck.md: tools, presenter guide, handoff, limits ---
for pp_t in '| `--no-notes` |' '| `--chrome-width N` |' '| `--out FILE` |' '| `--title TEXT` |' '| `--lang ko` or `--lang en` |' \
            'Never edit the HTML' '발표자 보기' 'fontTools' 'LibreOffice' 'my-plugins:setup' \
            '## 발표자 안내' '## Handoff' '## What the page does not carry' 'PDF' '팝업'; do
    assert_contains "html-deck.md: '$pp_t'" "$PP_REF" "$pp_t"
done
# every key the page's own help lists is in the guide, so the two never drift
PP_KEYS=$("${PP_PYI[@]}" - "$PP_DIR/assets/html/deck.js" "$PP_DIR/references/html-deck.md" <<'PY' 2>&1
import re, sys
js = open(sys.argv[1], encoding="utf-8").read()
md = open(sys.argv[2], encoding="utf-8").read()
blocks = re.findall(r"keys:\s*\[(.*?)\]\]", js, flags=re.S)
if len(blocks) != 2:
    sys.exit("deck.js: %d key lists, expected 2 (ko, en)" % len(blocks))
labels = [re.findall(r'\[\s*"([^"]+)"\s*,', b) for b in blocks]
if len(labels[0]) != len(labels[1]) or len(labels[0]) < 8:
    sys.exit("deck.js: the ko and en key lists differ in length (%d, %d)" % (len(labels[0]), len(labels[1])))
missing = [k for k in labels[0] if "\n| `%s` |" % k not in md]      # a row of the key table, not a mention in a sentence
print("missing: " + ", ".join(missing) if missing else "ok %d keys" % len(labels[0]))
PY
)
assert_contains "html-deck.md lists every key of the page's help" "$PP_KEYS" "ok "
for pp_f in "$PP_DIR/references/html-deck.md" "$PP_DIR/assets/html/deck.js" "$PP_DIR/assets/html/deck.css"; do
    assert_eq "$(basename "$pp_f"): no middle dot or em dash" "" "$(grep -n '[·—]' "$pp_f" 2>/dev/null | head -3)"
done

# --- Runtime files: one stage size, no network, both windows in one file ---
for pp_t in 'W = 1280, H = 720' '#presenter' 'postMessage' 'window.open(' 'requestFullscreen' 'localStorage'; do
    assert_contains "deck.js: '$pp_t'" "$PP_JS" "$pp_t"
done
for pp_t in 'width: 1280px; height: 720px' '@page { size: 13.333in 7.5in; margin: 0; }' '@media print' 'body.presenter' \
            'background-position: center; background-size: 100% 100%; background-repeat: no-repeat;'; do
    assert_contains "deck.css: '$pp_t'" "$PP_CSS" "$pp_t"
done
assert_not_contains "deck.css: .pic sets no background shorthand (it would reset the picture)" "$PP_CSS" ".slide .pic { background:"
assert_eq "runtime files load nothing from the network" "" "$(grep -nE 'https?://|@import' "$PP_DIR/assets/html/deck.js" "$PP_DIR/assets/html/deck.css" 2>/dev/null | head -3)"
if command -v node >/dev/null 2>&1; then
    PP_ERR=$(node --check "$PP_DIR/assets/html/deck.js" 2>&1) && pass "deck.js parses" || fail "deck.js parses" "$(printf '%s' "$PP_ERR" | head -3)"
else
    skip "deck.js parses" "node is not installed"
fi
for pp_s in deck_to_html.py preview_html_deck.py; do
    PP_ERR=$("${PP_PYI[@]}" -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$PP_DIR/scripts/$pp_s" 2>&1) \
        && pass "$pp_s parses" || fail "$pp_s parses" "$(printf '%s' "$PP_ERR" | tail -1)"
done
assert_contains "preview_html_deck.py: retries with the system node" "$(cat "$PP_DIR/scripts/preview_html_deck.py" 2>/dev/null)" 'os.environ["PLAYWRIGHT_NODEJS_PATH"] = node'

# --- deck_to_html.py helpers that need no deck ---
if "${PP_PY[@]}" -c "import pptx, lxml" >/dev/null 2>&1; then
    PP_OUT=$("${PP_PY[@]}" - "$PP_REPO/$PP_DIR/scripts" <<'PY' 2>&1
import sys
from lxml import etree
sys.path.insert(0, sys.argv[1])
import deck_to_html as d
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
def fill(val):
    return etree.fromstring('<a:ln xmlns:a="%s"><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>' % (A, val))
cases = [
    (d.format_number(0.55, "0%"), "55%"), (d.format_number(0.125, "0.0%"), "12.5%"),
    (d.format_number(1234.5, "#,##0"), "1,234"), (d.format_number(1234.56, "#,##0.0"), "1,234.6"),
    (d.format_number(38, '0"ms"'), "38ms"), (d.format_number(7, '"$"0'), "$7"),
    (d.format_number(12, "General"), "12"), (d.format_number(2.5, None), "2.5"), (d.format_number(None, "0%"), ""),
    (d.format_number(3, "0.00"), "3.00"),
    (d.nice_scale(0, 410, 5), (0, 500, 100)), (d.nice_scale(0, 1, 4), (0, 1, 0.25)), (d.nice_scale(0, 0, 5)[:2], (0, 1)),
    (d.polygon_points("nope", 10, 10), None), (len(d.polygon_points("diamond", 10, 20)), 4),
    (d.polygon_points("triangle", 10, 20), [(5.0, 0), (10, 20), (0, 20)]),
    (d.n(1.0), "1"), (d.n(0.126), "0.13"), (d.n(-0.001), "0"),
    (d.css_family("D2Coding").endswith("monospace"), True), (d.css_family("NanumSquareOTF Bold").endswith("sans-serif"), True),
    (d.LINE_EM, 1.2),
    (d.color(fill("FF9900")), "#FF9900"), (d.color(fill("red;}&lt;/style&gt;")), None),
    (d.css_family('x"}</style><script>'), '"xstylescript",' + d.SANS_FALLBACK),
    ('</style>' in d.font_face('a"}</style>', b"x", "woff"), False),
    (bool(d.EXTERNAL.search('<img src="https://example.com/a.png">')), True),
    (bool(d.EXTERNAL.search('.a{background:url(//cdn.example.com/a.png)}')), True),
    (bool(d.EXTERNAL.search('<a href="https://example.com/">x</a> url(data:image/png;base64,AAAA)')), False),
]
bad = ["case %d: got %r, want %r" % (i, got, want) for i, (got, want) in enumerate(cases) if got != want]
print("\n".join(bad) if bad else "ok %d cases" % len(cases))
PY
)
    assert_eq "deck_to_html.py: number formats, tick scale, shapes, safe colors and font names, external-file pattern" "ok 29 cases" "$PP_OUT"
    PP_OUT=$("${PP_PY[@]}" "$PP_DIR/scripts/deck_to_html.py" --help 2>&1); PP_RC=$?
    assert_eq "deck_to_html.py --help (exit 0)" "0" "$PP_RC"
    for pp_t in "--no-notes" "--chrome-width" "--lang" "--title" "--out"; do
        assert_contains "deck_to_html.py --help: $pp_t" "$PP_OUT" "$pp_t"
    done
    PP_OUT=$("${PP_PY[@]}" "$PP_DIR/scripts/deck_to_html.py" "$PP_W/none.pptx" 2>&1); PP_RC=$?
    assert_eq "deck_to_html.py: a missing file fails (exit 1)" "1" "$PP_RC"
    printf 'not a deck' > "$PP_W/broken.pptx"
    PP_OUT=$("${PP_PY[@]}" "$PP_DIR/scripts/deck_to_html.py" "$PP_W/broken.pptx" 2>&1); PP_RC=$?
    assert_eq "deck_to_html.py: a file that is not a deck fails (exit 1)" "1" "$PP_RC"
    assert_contains "deck_to_html.py: says the file cannot be opened" "$PP_OUT" "PowerPoint 파일로 열 수 없습니다"
else
    skip "deck_to_html.py helpers" "python-pptx or lxml is not importable by python3; run my-plugins:setup install"
fi

# --- End to end: build the fixture deck, apply the template, convert, read the page ---
PP_NODE_PATH=""
if command -v node >/dev/null 2>&1; then
    for pp_r in $(printf '%s' "${NODE_PATH:-}" | tr ':' ' ') $(npm root -g 2>/dev/null); do
        [ -d "$pp_r/pptxgenjs" ] && { PP_NODE_PATH="$pp_r"; break; }
    done
fi
PP_HTML="$PP_W/deck/fixture.html"
if [ -n "$PP_NODE_PATH" ] && "${PP_PY[@]}" -c "import pptx, lxml, PIL" >/dev/null 2>&1 \
   && command -v soffice >/dev/null 2>&1 && command -v pdftoppm >/dev/null 2>&1; then
    "${PP_PYI[@]}" - "$PP_DIR/SKILL.md" "$PP_FIX/html-deck.js" "$PP_W/deck/build_fixture.js" "$PP_W/deck/icons/service-Amazon-Bedrock.png" "$PP_W/deck/arch.png" <<'PY' 2>&1
import re, struct, sys, zlib
skill, content, out, icon, arch = sys.argv[1:]
hit = [b for b in re.findall(r"```javascript\n(.*?)```", open(skill, encoding="utf-8").read(), flags=re.S) if "function newSlide(" in b]
if len(hit) != 1:
    sys.exit("SKILL.md: %d javascript blocks with newSlide(), expected 1" % len(hit))
open(out, "w", encoding="utf-8").write(hit[0] + "\n" + open(content, encoding="utf-8").read())
def png(path, w, h, rgba):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = b"".join(b"\x00" + rgba * w for _ in range(h))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
png(icon, 16, 16, b"\xff\x99\x00\xff")
png(arch, 88, 32, b"\x16\x1d\x26\xff")
PY
    cp "$PP_FIX/arch.svg" "$PP_W/deck/arch.svg"
    PP_OUT=$( (cd "$PP_W/deck" && NODE_PATH="$PP_NODE_PATH" node build_fixture.js 2>&1 \
        && "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/apply_template.py" fixture_raw.pptx --out fixture.pptx 2>&1) ); PP_RC=$?
    assert_eq "fixture deck: builds and takes the template (exit 0)" "0" "$PP_RC"
    [ "$PP_RC" -eq 0 ] || echo "    $PP_OUT" | head -5

    PP_OUT=$( (cd "$PP_W/deck" && "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture.pptx 2>&1) ); PP_RC=$?
    assert_eq "deck_to_html.py: converts the fixture deck (exit 0)" "0" "$PP_RC"
    [ "$PP_RC" -eq 0 ] || echo "    $PP_OUT" | head -5
    assert_file_exists "deck_to_html.py: writes <Deck>.html next to the deck by default" "$PP_HTML"
    assert_contains "deck_to_html.py: reports slides and notes" "$PP_OUT" "슬라이드 8장, 노트 8장"
    assert_contains "deck_to_html.py: reports charts, the table and the pictures" "$PP_OUT" "차트 3, 표 1, 그림 2"
    PP_PAGE=$(cat "$PP_HTML" 2>/dev/null)
    PP_FACTS=$("${PP_PY[@]}" - "$PP_HTML" "$PP_DIR/assets/html/deck.css" "$PP_DIR/assets/html/deck.js" "$PP_W/deck/fixture.pptx" <<'PY' 2>&1
import re, sys
from pptx import Presentation
page = open(sys.argv[1], encoding="utf-8").read()
css = open(sys.argv[2], encoding="utf-8").read()
js = open(sys.argv[3], encoding="utf-8").read()
prs = Presentation(sys.argv[4])
slides = re.findall(r'<section class="slide".*?</section>', page, flags=re.S)
print("slides %d of %d" % (len(slides), len(prs.slides)))
print("notes %d" % sum(1 for s in slides if '<aside class="notes">' in s))
print("chrome on every slide %s" % all('<div class="chrome im' in s for s in slides))
layouts = {s.slide_layout.name for s in prs.slides}
chrome = set(re.findall(r'<div class="chrome (im\d+)"', page))
print("chrome pictures %d for %d layouts" % (len(chrome), len(layouts)))
content = [s for s in slides if 'data-layout="Title Only"' in s]
print("page-number patches %d on %d content slides" % (sum(1 for s in content if '<div class="patch"' in s), len(content)))
runtime = re.search(r'<style id="deck-runtime">\n(.*?)</style>', page, flags=re.S)
script = re.search(r'<script id="deck-script">\n(.*?)</script>', page, flags=re.S)
print("runtime css verbatim %s" % (runtime is not None and runtime.group(1) == css))
print("runtime js verbatim %s" % (script is not None and script.group(1) == js))
print("scripts %d" % len(re.findall(r"<script\b", page)))
body = re.sub(r"<style.*?</style>|<script.*?</script>", "", page, flags=re.S)
loads = re.findall(r"""(?i)(?:\bsrc\s*=\s*["']?|url\(\s*["']?)\s*(?:https?:)?//[^"')\s]*""", page)
print("network loads %d" % len(loads))
print("font faces %s" % sorted(set(re.findall(r'@font-face\{font-family:"([^"]+)"', re.search(r'<style id="deck-fonts">(.*?)</style>', page, flags=re.S).group(1)))))
print("charts %d tables %d pictures %d svg pictures %d" % (body.count('<svg class="chart'), body.count("<table"), body.count('class="pic '), page.count("data:image/svg+xml;base64,")))
print("links %s" % re.findall(r'<a href="([^"]+)"', body))
print("title %s" % re.search(r"<title>(.*?)</title>", page).group(1))
print("lang %s" % re.search(r'<html lang="(\w+)"', page).group(1))
print("first slide title %s" % re.search(r'id="s1"[^>]*data-title="([^"]*)"', page).group(1))
PY
)
    assert_contains "page: one section per slide" "$PP_FACTS" "slides 8 of 8"
    assert_contains "page: every slide carries its notes" "$PP_FACTS" "notes 8"
    assert_contains "page: template chrome behind every slide" "$PP_FACTS" "chrome on every slide True"
    assert_contains "page: one chrome picture per layout" "$PP_FACTS" "chrome pictures 5 for 5 layouts"
    assert_contains "page: content slides after the first get a page-number patch" "$PP_FACTS" "page-number patches 3 on 4 content slides"
    assert_contains "page: deck.css is in the page unchanged" "$PP_FACTS" "runtime css verbatim True"
    assert_contains "page: deck.js is in the page unchanged" "$PP_FACTS" "runtime js verbatim True"
    assert_contains "page: one script, the runtime" "$PP_FACTS" "scripts 1"
    assert_contains "page: nothing is loaded from the network" "$PP_FACTS" "network loads 0"
    assert_contains "page: both deck fonts are embedded" "$PP_FACTS" "font faces ['D2Coding', 'NanumSquareOTF Bold']"
    assert_contains "page: charts are SVG, the table is a table, pictures are there" "$PP_FACTS" "charts 3 tables 1 pictures 2"
    assert_contains "page: only the http link becomes a link" "$PP_FACTS" "links ['https://aws.amazon.com/bedrock/']"
    assert_contains "page: title from the cover" "$PP_FACTS" "title HTML 덱 변환 검증"
    assert_contains "page: Korean controls for a Korean deck" "$PP_FACTS" "lang ko"
    assert_contains "page: slide title for the list" "$PP_FACTS" "first slide title HTML 덱 변환 검증"
    if "${PP_PY[@]}" -c "import fontTools" >/dev/null 2>&1; then
        assert_contains "page: fonts are WOFF subsets" "$PP_PAGE" 'format("woff")'
        assert_contains "page: the diagram is the vector SVG" "$PP_FACTS" "svg pictures 1"
        assert_contains "deck_to_html.py: reports the SVG picture" "$PP_OUT" "그림 2(SVG 1)"
        PP_SIZE=$(wc -c < "$PP_HTML")
        [ "$PP_SIZE" -lt 3000000 ] && pass "page: under 3 MB with subset fonts ($PP_SIZE bytes)" || fail "page: under 3 MB with subset fonts" "$PP_SIZE bytes"
    else
        skip "page: WOFF subsets and the vector diagram" "fontTools is not importable; run my-plugins:setup install"
    fi
    assert_contains "page: slide text is HTML text" "$PP_PAGE" "정의 상자와 카드"
    assert_contains "page: markup in slide text is escaped" "$PP_PAGE" "&lt;b&gt;굵게 아님&lt;/b&gt; &amp; 꺾쇠"
    assert_not_contains "page: slide text cannot open a tag" "$PP_PAGE" "<b>굵게 아님</b>"
    assert_contains "page: markup in notes is escaped" "$PP_PAGE" "&lt;/aside&gt;&lt;script&gt;alert(1)&lt;/script&gt; 노트 안의 꺾쇠"
    assert_not_contains "page: a javascript: link is dropped" "$PP_PAGE" "javascript:alert"
    assert_contains "page: the link text of the dropped link stays" "$PP_PAGE" "나쁜 링크"
    assert_contains "page: code keeps its spaces" "$PP_PAGE" "status:   READY"
    assert_contains "page: data labels use the chart's number format" "$PP_PAGE" ">1,280</text>"
    assert_contains "page: doughnut labels are shares of the total, not the raw values" "$PP_PAGE" ">55%</text>"
    assert_not_contains "page: no raw value under a percent format" "$PP_PAGE" ">11000%</text>"
    assert_contains "page: the picture keeps its description" "$PP_PAGE" 'aria-label="요청 흐름 그림"'
    assert_contains "page: bullets" "$PP_PAGE" 'class="bu '

    # without fontTools the page still comes out: whole font files, and the diagram's PNG instead of its SVG
    mkdir -p "$PP_W/nofont/fontTools" && printf 'raise ImportError("shadowed by the test")\n' > "$PP_W/nofont/fontTools/__init__.py"
    PP_OUT=$( (cd "$PP_W/deck" && PYTHONPATH="$PP_W/nofont" "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture.pptx --out sub/nofont.html 2>&1) ); PP_RC=$?
    assert_eq "without fontTools: still converts, into a new folder (exit 0)" "0" "$PP_RC"
    assert_contains "without fontTools: says the fonts are whole files" "$PP_OUT" "글꼴 파일을 통째로 넣었습니다"
    assert_contains "without fontTools: says the diagram is its PNG" "$PP_OUT" "다이어그램을 SVG 대신 PNG로 넣었습니다"
    PP_NOFONT=$(cat "$PP_W/deck/sub/nofont.html" 2>/dev/null)
    assert_contains "without fontTools: the whole OpenType file is embedded" "$PP_NOFONT" 'format("opentype")'
    assert_not_contains "without fontTools: no SVG picture without its fonts" "$PP_NOFONT" "data:image/svg+xml;base64,"

    # the notes can be left out, and then no sentence of them is in the file
    PP_OUT=$( (cd "$PP_W/deck" && "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture.pptx --no-notes --out share.html --lang en --title "Shared deck" 2>&1) ); PP_RC=$?
    assert_eq "deck_to_html.py --no-notes (exit 0)" "0" "$PP_RC"
    assert_contains "deck_to_html.py --no-notes: says so" "$PP_OUT" "노트 없음(--no-notes)"
    PP_SHARE=$(cat "$PP_W/deck/share.html" 2>/dev/null)
    assert_not_contains "--no-notes: no notes element" "$PP_SHARE" '<aside class="notes">'
    assert_not_contains "--no-notes: no note sentence" "$PP_SHARE" "표지 노트 첫 문장입니다."
    assert_contains "--no-notes: the slides are still there" "$PP_SHARE" "정의 상자와 카드"
    assert_contains "--lang en: English controls" "$PP_SHARE" '<html lang="en">'
    assert_contains "--title: the page title" "$PP_SHARE" "<title>Shared deck</title>"

    # a deck that never got the template is refused: its chrome would be empty masters
    PP_OUT=$( (cd "$PP_W/deck" && "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture_raw.pptx --out raw.html 2>&1) ); PP_RC=$?
    assert_eq "deck_to_html.py: a raw deck fails (exit 1)" "1" "$PP_RC"
    assert_contains "deck_to_html.py: names the missing template step" "$PP_OUT" "템플릿을 적용하기 전 파일입니다"
    [ -e "$PP_W/deck/raw.html" ] && fail "deck_to_html.py: a raw deck writes no page" "raw.html exists" || pass "deck_to_html.py: a raw deck writes no page"
    # without LibreOffice the chrome cannot be drawn: fail and point to setup, never a page without the template
    PP_OUT=$( (cd "$PP_W/deck" && PATH="$PP_W/emptybin" "$(command -v python3)" -X pycache_prefix="$TEST_TMP/pp-pycache" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture.pptx --out notool.html 2>&1) ); PP_RC=$?
    assert_eq "deck_to_html.py: no soffice on PATH fails (exit 1)" "1" "$PP_RC"
    assert_contains "deck_to_html.py: missing tools point to the setup skill" "$PP_OUT" "my-plugins:setup"
    [ -e "$PP_W/deck/notool.html" ] && fail "deck_to_html.py: no page without the template chrome" "notool.html exists" || pass "deck_to_html.py: no page without the template chrome"
    PP_OUT=$( (cd "$PP_W/deck" && "${PP_PY[@]}" "$PP_REPO/$PP_DIR/scripts/deck_to_html.py" fixture.pptx --chrome-width 100 2>&1) ); PP_RC=$?
    assert_eq "deck_to_html.py: an unusable --chrome-width fails (exit 1)" "1" "$PP_RC"
else
    skip "aws-ppt-skills HTML deck end to end" "node with pptxgenjs, python-pptx, lxml, Pillow, soffice or pdftoppm not reachable; run my-plugins:setup install"
fi

# --- In a browser: every slide is shown, the keys work, the presenter window follows (offline: cached Playwright only) ---
if [ -f "$PP_HTML" ] && command -v uv >/dev/null 2>&1 \
   && (cd "$TEST_TMP" && UV_OFFLINE=1 uv run --quiet --no-project --with playwright==1.64.1 python -c 'import playwright') >/dev/null 2>&1; then
    PP_OUT=$(cd "$PP_W/deck" && UV_OFFLINE=1 uv run --quiet --no-project --with playwright==1.64.1 python -B \
             "$PP_REPO/$PP_DIR/scripts/preview_html_deck.py" fixture.html --out-dir "$PP_W/shots" 2>&1); PP_RC=$?
    if printf '%s' "$PP_OUT" | grep -qE "Executable doesn't exist|BrowserType.launch|playwright install"; then
        skip "preview_html_deck.py in a browser" "Playwright has no usable Chromium here; run my-plugins:setup install"
    else
        assert_eq "preview_html_deck.py: the fixture page passes (exit 0)" "0" "$PP_RC"
        [ "$PP_RC" -eq 0 ] || echo "    $PP_OUT" | grep -v '\.png$' | head -5
        assert_eq "preview_html_deck.py: one picture per slide" "8" "$(find "$PP_W/shots" -name 'fixture-[0-9][0-9].png' | wc -l | tr -d ' ')"
        assert_file_exists "preview_html_deck.py: the slide list picture" "$PP_W/shots/fixture-list.png"
        assert_file_exists "preview_html_deck.py: the presenter view picture" "$PP_W/shots/fixture-presenter.png"
        # a page whose script is broken must not pass
        sed 's/function go(i, fromPeer) {/function go(i, fromPeer) { return;/' "$PP_HTML" > "$PP_W/deck/stuck.html"
        PP_OUT=$(cd "$PP_W/deck" && UV_OFFLINE=1 uv run --quiet --no-project --with playwright==1.64.1 python -B \
                 "$PP_REPO/$PP_DIR/scripts/preview_html_deck.py" stuck.html --out-dir "$PP_W/shots-stuck" 2>&1); PP_RC=$?
        assert_eq "preview_html_deck.py: a deck that does not move fails (exit 1)" "1" "$PP_RC"
        assert_contains "preview_html_deck.py: says which key did nothing" "$PP_OUT" "WARN the → key did not move to slide 2"
        assert_contains "preview_html_deck.py: says which slide never showed" "$PP_OUT" "WARN slide 1 did not show when the address asked for it"
        assert_not_contains "preview_html_deck.py: a stuck deck is reported, not a traceback" "$PP_OUT" "Traceback"
    fi
else
    skip "preview_html_deck.py in a browser" "no converted page, or uv with a cached Playwright 1.64.1 is not available (tests stay offline)"
fi

# --- The new dependency goes through setup, and the README says what the skill delivers ---
assert_eq "setup.sh: fonttools in the check list and in the install list" "2" "$(grep -c 'fontTools:fonttools' skills/setup/scripts/setup.sh)"
assert_contains "setup SKILL.md: fonttools in the install table" "$(grep '^| ' skills/setup/SKILL.md)" "python-pptx, lxml, Pillow, cairosvg, fonttools"
PP_README_EN=$(sed -n '/<a id="english"><\/a>/,/<a id="korean"><\/a>/p' README.md)
PP_README_KO=$(sed -n '/<a id="korean"><\/a>/,$p' README.md)
assert_contains "README (English): fonttools among the dependencies" "$PP_README_EN" "Pillow, cairosvg, fonttools"
assert_contains "README (Korean): fonttools among the dependencies" "$PP_README_KO" "Pillow, cairosvg, fonttools"
assert_contains "README (English): the aws-ppt-skills row names the HTML deck" "$(printf '%s\n' "$PP_README_EN" | grep '^| `/my-plugins:aws-ppt-skills`')" "one HTML file presented in a browser"
assert_contains "README (Korean): the aws-ppt-skills row names the HTML deck" "$(printf '%s\n' "$PP_README_KO" | grep '^| `/my-plugins:aws-ppt-skills`')" "브라우저에서 발표하는 HTML 한 파일"
assert_file_exists "ADR-007 records the conversion decision" "docs/decisions/ADR-007-html-deck-converted-from-pptx.md"

assert_eq "aws-ppt-skills: nothing written into the skill folder" "" \
    "$(find "$PP_DIR" \( -name __pycache__ -o -newer "$PP_W/before" \) -print 2>/dev/null | tr '\n' ' ')"

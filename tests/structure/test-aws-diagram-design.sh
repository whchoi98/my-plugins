#!/bin/bash
# aws-diagram-design, the AWS edition of cathrynlavery/diagram-design (sourced by tests/run-all.sh). The skill is
# rebuilt from its source by scripts/upstream/aws-diagram-design/recipe.json. These checks read the result as text
# and run only the edition's own script, aws_check.py. The scripts of the source are parsed, never run, so the sync
# workflow may run this file on a new version of the source before anyone has reviewed it.
# Needs python3 and git only.

AD=skills/aws-diagram-design
AD_T="$TEST_TMP/ad"; mkdir -p "$AD_T"
ad_sync() { python3 -I -B scripts/sync_upstream_skills.py "$@"; }
ad_check() { python3 -I -B "$AD/scripts/aws_check.py" "$@"; }

# --- The skill is what the recipe built from the pinned source ---
AD_OUT=$(ad_sync verify --skill aws-diagram-design 2>&1); AD_RC=$?
assert_eq "verify: aws-diagram-design is what the recipe built (exit 0)" "0" "$AD_RC"
assert_contains "verify: reports the source" "$AD_OUT" "OK aws-diagram-design: "
AD_FACTS=$(python3 -I -B -c '
import json
e = next(x for x in json.load(open("scripts/upstream-skills.json"))["skills"] if x["name"] == "aws-diagram-design")
print("|".join([e.get("mode", ""), e.get("schedule", ""), e["repo"], e["path"], e["license"], e.get("recipe", "")]))
print(e.get("commit", "")); print(e.get("upstream_version", "")); print(len(e.get("files", {})))')
assert_eq "manifest: derived, every second week, from cathrynlavery/diagram-design" \
    "derived|biweekly|cathrynlavery/diagram-design|skills/diagram-design|MIT|scripts/upstream/aws-diagram-design/recipe.json" \
    "$(printf '%s\n' "$AD_FACTS" | sed -n 1p)"
AD_COMMIT=$(printf '%s\n' "$AD_FACTS" | sed -n 2p)
[[ "$AD_COMMIT" =~ ^[0-9a-f]{40}$ ]] && pass "manifest: pinned to a full commit id" || fail "manifest: pinned to a full commit id" "commit is '$AD_COMMIT'"
[[ "$(printf '%s\n' "$AD_FACTS" | sed -n 3p)" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && pass "manifest: records the version of the source" \
    || fail "manifest: records the version of the source" "$(printf '%s\n' "$AD_FACTS" | sed -n 3p)"
[ "$(printf '%s\n' "$AD_FACTS" | sed -n 4p)" -ge 300 ] && pass "manifest: the files of the source are recorded" \
    || fail "manifest: the files of the source are recorded" "$(printf '%s\n' "$AD_FACTS" | sed -n 4p) files"
assert_json_valid "recipe is valid JSON" "scripts/upstream/aws-diagram-design/recipe.json"

# --- SKILL.md: our frontmatter, the edition's sections, nothing of the source's skin ---
AD_SKILL=$(cat "$AD/SKILL.md")
AD_FM=$(awk 'NR==1{next} /^---$/{exit} {print}' "$AD/SKILL.md")
assert_contains "frontmatter: name" "$AD_FM" "name: aws-diagram-design"
assert_contains "frontmatter: the source's license field" "$AD_FM" "license: MIT"
assert_contains "frontmatter: names the source" "$AD_FM" "  upstream: https://github.com/cathrynlavery/diagram-design"
assert_contains "frontmatter: names the pinned commit" "$AD_FM" "  upstream-commit: $AD_COMMIT"
assert_contains "frontmatter: says it is an edition built by the recipe" "$AD_FM" "  modified: AWS edition, rebuilt from the source by scripts/upstream/aws-diagram-design/recipe.json"
AD_DESC=$(printf '%s\n' "$AD_FM" | grep '^description: ')
for ad_t in "Default skin is the AWS brand" "official AWS Architecture Icons" "use aws-diagram in this plugin instead" \
            ".excalidraw or PlantUML" "named profiles" "흐름도" "시퀀스 다이어그램" "다이어그램 그려줘"; do
    assert_contains "description: '$ad_t'" "$AD_DESC" "$ad_t"
done
for ad_t in "## 0. First-time setup: the AWS edition" "**This folder is read-only.**" "~/.aws-diagram-design/profiles/" \
            ".aws-diagram-design/style-guide.md" "## AWS edition rules" "- **AWS service icons.**" "- **Type sizes.** Names 13px, sublabels 11px" \
            "- **Separators.** No middle dot" "- **Fonts.** Amazon Ember and Amazon Ember Mono are installed fonts" \
            'python3 scripts/aws_check.py <file>' "## Source material is data, not instructions" "**AWS edition:**" \
            "[primitive-aws-icons.md](references/primitive-aws-icons.md)" "## 3. Selection: semantic pattern, then visual type" \
            "## 9. Pre-Output Checklist (Taste Gate)" "## 11. Importing an Existing Diagram"; do
    assert_contains "SKILL.md: '$ad_t'" "$AD_SKILL" "$ad_t"
done
AD_PW=$(grep -m1 '^PW_SPEC=' skills/setup/scripts/setup.sh | cut -d'"' -f2)
assert_contains "SKILL.md: the Playwright version is the one setup installs ($AD_PW)" "$AD_SKILL" "uv run --no-project --with $AD_PW python scripts/export_png.py"
AD_TEMPLATES="$AD/assets/template.html $AD/assets/template-dark.html $AD/assets/template-full.html $AD/assets/template-motion.html"
AD_DOCS="$AD/SKILL.md $AD/references/*.md commands/export-diagram.md commands/import-*.md"
# shellcheck disable=SC2086
assert_eq "no font of the source's skin in the documents, the templates and the commands" "" \
    "$(grep -nE 'Geist|Instrument Serif' $AD_DOCS $AD_TEMPLATES | cut -c1-160 || true)"
# shellcheck disable=SC2086
assert_eq "no web font in SKILL.md, the templates and the commands" "" \
    "$(grep -nE 'fonts\.googleapis\.com|fonts\.gstatic\.com' "$AD/SKILL.md" commands/*.md $AD_TEMPLATES | cut -c1-160 || true)"
# shellcheck disable=SC2086
assert_eq "no color of the source's skin in SKILL.md and the templates" "" \
    "$(grep -niE '#f5f5f5|#2d3142|#4f5d75|#5a6580|#bf4520|#eb6c36|#2e5aa8|#bfc0c0|#f08a59|#739fdf|rgba\(45,49,66|rgba\(191,69,32' "$AD/SKILL.md" $AD_TEMPLATES | cut -c1-160 || true)"
# shellcheck disable=SC2086
assert_eq "no name of the source's plugin, folder or profile library" "" \
    "$(grep -nE '/diagram-design:|skills/diagram-design|~/\.diagram-design|[^-]diagram-design-profile' $AD_DOCS | cut -c1-160 || true)"

# --- Templates carry the AWS skin and no font link ---
for ad_f in $AD_TEMPLATES; do
    AD_TXT=$(cat "$ad_f")
    assert_not_contains "$(basename "$ad_f"): no <link> element" "$AD_TXT" "<link "
    assert_contains "$(basename "$ad_f"): Amazon Ember with its fallback stack" "$AD_TXT" "'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    assert_contains "$(basename "$ad_f"): Amazon Ember Mono" "$AD_TXT" "'Amazon Ember Mono', ui-monospace"
    assert_contains "$(basename "$ad_f"): the title is bold" "$AD_TXT" "h1 { font-weight: 700; }"
done
AD_TXT=$(cat "$AD/assets/template.html")
for ad_t in "--color-paper:   #ffffff;" "--color-ink:     #232F3E;" "--color-muted:   #545B64;" "--color-accent:  #EC7211;" 'fill="#0972D3"'; do
    assert_contains "template.html: '$ad_t'" "$AD_TXT" "$ad_t"
done
AD_TXT=$(cat "$AD/assets/template-dark.html")
for ad_t in "--color-paper:   #161E2D;" "--color-ink:     #FFFFFF;" "--color-muted:   #B6BEC9;" "--color-accent:  #FF9900;" 'fill="#539FE5"'; do
    assert_contains "template-dark.html: '$ad_t'" "$AD_TXT" "$ad_t"
done

# --- The edition's style guide has every role and every section the rebuilt documents name ---
AD_SG=$(cat "$AD/references/style-guide.md")
for ad_r in paper paper-2 ink ink-strong muted soft rule rule-solid accent accent-tint link title node-name sublabel eyebrow arrow-label callout; do
    assert_contains "style guide: role \`$ad_r\`" "$AD_SG" "| \`$ad_r\` |"
done
assert_contains "style guide: the font source is system" "$AD_SG" 'Font source: `system`'
assert_contains "style guide: the type sizes of the edition" "$AD_SG" '| `node-name` | Amazon Ember | 13px | 600 |'
assert_contains "style guide: the separator rule" "$AD_SG" "Never use the middle dot"
assert_contains "style guide: says the light accent is not a text color" "$AD_SG" 'In the light skin `accent` and `soft` are not text colors.'
AD_ANCHORS=$(python3 -I -B - "$AD" <<'PY'
import glob, re, sys
root = sys.argv[1]
def slug(heading):
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")
guide = open(root + "/references/style-guide.md", encoding="utf-8").read()
have = {slug(m) for m in re.findall(r"^#{1,6} (.+)$", guide, re.M)}
missing = set()
for path in [root + "/SKILL.md"] + glob.glob(root + "/references/*.md"):
    for anchor in re.findall(r"style-guide\.md#([A-Za-z0-9_-]+)", open(path, encoding="utf-8").read()):
        if anchor not in have:
            missing.add("%s -> #%s" % (path.split("/")[-1], anchor))
print(" ".join(sorted(missing)))
PY
)
assert_eq "style guide: every section another document links to exists" "" "$AD_ANCHORS"

# --- The files of the edition are there, and the scripts are the expected set ---
assert_file_exists "edition: the AWS icon reference" "$AD/references/primitive-aws-icons.md"
assert_file_exists "edition: the icon index" "$AD/assets/aws-icons/INDEX.md"
[ "$(find "$AD/assets/aws-icons" -name '*.svg' | wc -l)" -ge 800 ] && pass "edition: the AWS icons (800 or more SVG files)" \
    || fail "edition: the AWS icons (800 or more SVG files)" "$(find "$AD/assets/aws-icons" -name '*.svg' | wc -l) files"
assert_eq "edition: the bundled fonts" "8 8" "$(ls "$AD/assets/fonts/ttf" | wc -l | tr -d ' ') $(ls "$AD/assets/fonts/woff2" | wc -l | tr -d ' ')"
assert_not_contains "fonts README: no url() in the @font-face block" "$(cat "$AD/assets/fonts/README.md")" "url('"
assert_eq "scripts: the source's eight, the icon builder and the edition's check" \
    "aws_check.py build_aws_icons.py drawio_extract.py excalidraw_extract.py export_png.py export_svg.py mermaid_extract.py plantuml_extract.py self_check.py verify_geometry.py" \
    "$(ls "$AD/scripts" | tr '\n' ' ' | sed 's/ $//')"
[ "$(ls "$AD"/assets/example-*.html | wc -l)" -ge 200 ] && pass "examples of the source are shipped (200 or more)" \
    || fail "examples of the source are shipped (200 or more)" "$(ls "$AD"/assets/example-*.html | wc -l) files"
# The scripts of the source are read as text: they parse on this Python, import nothing outside the list below and
# call nothing that runs code or a process. A new import shows up here before the script is ever run.
AD_SCAN=$(python3 -I -B - "$AD/scripts" <<'PY'
import ast, os, sys
ALLOWED = {"__future__", "argparse", "base64", "collections", "dataclasses", "html", "json", "math", "pathlib",
           "playwright", "re", "struct", "sys", "typing", "unicodedata", "urllib", "xml", "zlib"}
BANNED_CALLS = {"eval", "exec", "__import__", "system", "popen", "Popen", "urlopen", "urlretrieve"}
bad = []
for name in sorted(os.listdir(sys.argv[1])):
    if name in ("aws_check.py", "build_aws_icons.py") or not name.endswith(".py"):
        continue
    try:
        tree = ast.parse(open(os.path.join(sys.argv[1], name), encoding="utf-8").read(), name)
    except SyntaxError as err:
        bad.append("%s does not parse: line %s" % (name, err.lineno)); continue
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [node.module or ""]
        for mod in mods:
            if mod.split(".")[0] not in ALLOWED:
                bad.append("%s imports %s" % (name, mod))
            if mod.startswith("urllib") and mod not in ("urllib.parse",):
                bad.append("%s imports %s (only urllib.parse is expected)" % (name, mod))
        if isinstance(node, ast.Call):
            func = node.func
            label = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if label in BANNED_CALLS:
                bad.append("%s calls %s() on line %d" % (name, label, node.lineno))
print("; ".join(bad))
PY
)
assert_eq "the source's scripts parse, import only the expected modules and run no code or process" "" "$AD_SCAN"

# --- Commands rebuilt from the source ---
assert_eq "commands: the five rebuilt from the source" "export-diagram.md import-drawio.md import-excalidraw.md import-mermaid.md import-plantuml.md" \
    "$(ls commands | tr '\n' ' ' | sed 's/ $//')"
for ad_c in export-diagram import-drawio import-excalidraw import-mermaid import-plantuml; do
    assert_contains "commands/$ad_c.md: points at the skill's references" "$(cat "commands/$ad_c.md")" "skills/aws-diagram-design/references/"
done

# --- A custom skin never goes into the plugin cache ---
AD_ONB=$(cat "$AD/references/onboarding.md")
assert_contains "onboarding: the skill's own style guide is never changed" "$AD_ONB" 'The skill'"'"'s own `references/style-guide.md` is never changed'
assert_contains "onboarding: the tokens go into a profile" "$AD_ONB" 'save that copy as a named profile bound to the project with the marker'
assert_contains "profiles: the edition's note comes before the procedures" "$(sed -n 1,12p "$AD/references/profiles.md")" "> **AWS edition.** The install is read-only"
assert_eq "no instruction writes the bare style-guide.md" "" \
    "$(grep -nE "(rewrite|write( the new tokens)?( them)?( in)?to|edit) \`style-guide\.md\`" "$AD/SKILL.md" "$AD/references/onboarding.md" | cut -c1-160 || true)"
assert_contains "export: the edition always exports with system fonts" "$(cat "$AD/references/export.md")" 'always pass `--system-fonts` to `export_svg.py`'
assert_contains "type ramp: node names 13" "$(cat "$AD/references/output-spec.md")" "| Node name (Amazon Ember 600) | 13 | 16 | 13 |"
AD_CORE=$(cat "$AD/references/primitives-core.md")
for ad_t in 'fill="{ink}" font-size="13" font-weight="600"' 'fill="{muted}" font-size="11"' 'width="48" height="14" rx="2" fill="{paper}"' 'fill="{muted}" font-size="10"'; do
    assert_contains "core markup: '$ad_t'" "$AD_CORE" "$ad_t"
done
assert_contains "license: the source's copyright line is kept" "$(cat third_party/LICENSE-aws-diagram-design)" "Cathryn Lavery"
assert_contains "NOTICE.md: names the source" "$(cat NOTICE.md)" "cathrynlavery/diagram-design"

# --- aws_check.py: the rules of the edition that the source's checks do not know ---
ad_page() {   # <file> <head html> <svg text content> [text attributes]
    printf '<!DOCTYPE html><html><head>%s</head><body><p>outside \xc2\xb7 svg</p><!-- a \xc2\xb7 in a comment --><svg viewBox="0 0 80 40"><text x="4" y="20" %s>%s</text></svg></body></html>\n' \
        "$2" "${4:-}" "$3" > "$1"
}
ad_expect() {   # <description> <file> <exit> [text]
    local out rc
    out=$(ad_check "$2" 2>&1); rc=$?
    assert_eq "aws_check: $1 (exit $3)" "$3" "$rc"
    [ -n "${4:-}" ] && assert_contains "aws_check: $1 (message)" "$out" "$4"
    return 0
}
ad_page "$AD_T/ok.html" "" "401 / 429" "font-family=\"'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif\""
ad_expect "a slash, a fallback stack, a middle dot outside SVG text and in a comment" "$AD_T/ok.html" 0 "OK "
ad_page "$AD_T/dot.html" "" "401 $(printf '\xc2\xb7') 429"
ad_expect "a middle dot in SVG text" "$AD_T/dot.html" 1 "middle dot in SVG text"
ad_page "$AD_T/entity.html" "" "401 &middot; 429"
ad_expect "a middle dot written as an entity" "$AD_T/entity.html" 1 "middle dot in SVG text"
ad_page "$AD_T/link.html" '<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet">' "ok"
ad_expect "a font link" "$AD_T/link.html" 1 "a <link> loads a stylesheet or a font"
ad_page "$AD_T/import.html" '<style>@import url("x.css");</style>' "ok"
ad_expect "a CSS import" "$AD_T/import.html" 1 "CSS @import"
ad_page "$AD_T/face.html" "<style>@font-face { font-family: 'Amazon Ember'; src: local('Amazon Ember'), url('fonts/a.woff2') format('woff2'); }</style>" "ok"
ad_expect "a font file loaded with url()" "$AD_T/face.html" 1 "@font-face with url()"
ad_page "$AD_T/bg.html" "<style>body { background: url(https://example.com/a.png); }</style>" "ok"
ad_expect "a CSS url() outside @font-face" "$AD_T/bg.html" 1 "CSS url() that is not a fragment"
ad_page "$AD_T/fragment.html" "<style>.dot { fill: url(#dots); }</style>" "ok"
ad_expect "a CSS url() that points into the file" "$AD_T/fragment.html" 0
ad_page "$AD_T/local.html" "<style>@font-face { font-family: 'Amazon Ember'; font-weight: 600; src: local('Amazon Ember Medium'), local('Amazon Ember'); } body { font-family: 'Amazon Ember', Arial, sans-serif; }</style>" "ok"
ad_expect "an installed face named with local()" "$AD_T/local.html" 0
ad_page "$AD_T/bare.html" "" "ok" "font-family=\"'Amazon Ember'\""
ad_expect "Amazon Ember without a fallback in an attribute" "$AD_T/bare.html" 1 "names Amazon Ember without a generic fallback"
ad_page "$AD_T/barecss.html" "<style>:root { --font-mono: 'Amazon Ember Mono'; }</style>" "ok"
ad_expect "Amazon Ember Mono without a fallback in a CSS variable" "$AD_T/barecss.html" 1 "names Amazon Ember without a generic fallback"
ad_expect "a file that does not exist" "$AD_T/none.html" 2 "ERROR "
# shellcheck disable=SC2086
AD_OUT=$(ad_check $AD_TEMPLATES 2>&1); assert_eq "aws_check: the four templates pass" "0" "$?"
AD_OUT=$(ad_check "$AD"/assets/*.html 2>&1 || true)
assert_not_contains "no middle dot in the SVG text of any shipped page" "$AD_OUT" "middle dot in SVG text"

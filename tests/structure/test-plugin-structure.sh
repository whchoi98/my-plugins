#!/bin/bash
# my-plugins structure and shipped-content invariants (sourced by tests/run-all.sh).
# Generic checks over every skill, command, manifest and harness file. Skill-specific checks live in
# test-aws-blog-skills.sh and test-kor-deslop.sh; the behaviour of the merge fixes in test-integration.sh.

PS_PJ=.claude-plugin/plugin.json
PS_MJ=.claude-plugin/marketplace.json

# --- Manifests ---
for ps_f in "$PS_PJ" "$PS_MJ" .claude/settings.json .mcp.json; do
    assert_json_valid "$ps_f is valid JSON" "$ps_f"
done
PS_NAME=$(jq -r '.name' "$PS_PJ" 2>/dev/null || true)
PS_VER=$(jq -r '.version' "$PS_PJ" 2>/dev/null || true)
PS_MKT=$(jq -r '.name' "$PS_MJ" 2>/dev/null || true)
assert_eq "plugin.json name" "my-plugins" "$PS_NAME"
assert_eq "marketplace name" "my-plugins" "$PS_MKT"
assert_eq "marketplace has exactly one plugin" "1" "$(jq '.plugins | length' "$PS_MJ" 2>/dev/null)"
assert_eq "marketplace entry name == plugin.json name" "$PS_NAME" "$(jq -r '.plugins[0].name' "$PS_MJ" 2>/dev/null)"
assert_eq "marketplace entry source is the repo root" "./" "$(jq -r '.plugins[0].source' "$PS_MJ" 2>/dev/null)"
[[ "$PS_VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && pass "plugin.json version is semver ($PS_VER)" \
    || fail "plugin.json version is semver" "got '$PS_VER'"
PS_MVER=$(jq -r '.plugins[0].version // empty' "$PS_MJ" 2>/dev/null || true)
[ -z "$PS_MVER" ] || [ "$PS_MVER" = "$PS_VER" ] && pass "marketplace entry has no version or the plugin.json one" \
    || fail "marketplace entry has no version or the plugin.json one" "marketplace $PS_MVER vs plugin.json $PS_VER"

# --- Version consistency (plugin.json, README badge, CHANGELOG both languages) ---
grep -qF "Version-${PS_VER}-" README.md && pass "README version badge matches $PS_VER" \
    || fail "README version badge matches $PS_VER" "badge 'Version-${PS_VER}-' not found"
PS_CL_EN=$(sed -n '/<a id="english"><\/a>/,/<a id="korean"><\/a>/p' CHANGELOG.md)
PS_CL_KO=$(sed -n '/<a id="korean"><\/a>/,$p' CHANGELOG.md)
assert_eq "CHANGELOG (English) latest release == plugin.json" "$PS_VER" \
    "$(printf '%s\n' "$PS_CL_EN" | grep -m1 -oP '^## \[\K[0-9]+\.[0-9]+\.[0-9]+' || true)"
assert_eq "CHANGELOG (Korean) latest release == plugin.json" "$PS_VER" \
    "$(printf '%s\n' "$PS_CL_KO" | grep -m1 -oP '^## \[\K[0-9]+\.[0-9]+\.[0-9]+' || true)"
assert_eq "CHANGELOG: both languages list the same versions" \
    "$(printf '%s\n' "$PS_CL_EN" | grep -oP '^## \[\K[^]]+' | tr '\n' ' ')" \
    "$(printf '%s\n' "$PS_CL_KO" | grep -oP '^## \[\K[^]]+' | tr '\n' ' ')"
assert_contains "CHANGELOG: English has [Unreleased]" "$PS_CL_EN" "## [Unreleased]"
assert_contains "CHANGELOG: Korean has [Unreleased]" "$PS_CL_KO" "## [Unreleased]"

# --- Every shipped skill: SKILL.md frontmatter ---
# One line per check: PASS|FAIL TAB <description> TAB <reason>. Handles quoted values and folded (>) blocks.
PS_FM=$(python3 -I - <<'PY' 2>&1 || true
import glob, os, re

def emit(ok, desc, reason=""):
    print("%s\t%s\t%s" % ("PASS" if ok else "FAIL", desc, reason))

def unquote(v):
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return re.sub(r'\\(.)', r'\1', v[1:-1])
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v

for d in sorted(glob.glob("skills/*/")):
    skill = os.path.basename(d.rstrip("/"))
    path = os.path.join(d, "SKILL.md")
    if not os.path.isfile(path):
        emit(False, "skill %s: SKILL.md exists" % skill, "missing %s" % path)
        continue
    lines = open(path, encoding="utf-8").read().split("\n")
    emit(lines[0] == "---", "skill %s: frontmatter opens with ---" % skill, "first line is %r" % lines[0][:40])
    try:
        end = lines.index("---", 1)
    except ValueError:
        emit(False, "skill %s: frontmatter closes with ---" % skill, "no closing --- line")
        continue
    fields, key, block = {}, None, None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            block = value if value in (">", "|", ">-", "|-") else None
            fields[key] = "" if block else unquote(value)
        elif key and line[:1] in (" ", "\t"):
            sep = "\n" if (block or "").startswith("|") else " "
            fields[key] = (fields[key] + sep + line.strip()) if fields[key] else line.strip()
    emit(fields.get("name") == skill, "skill %s: frontmatter name == directory" % skill,
         "name is %r" % fields.get("name"))
    n = len(fields.get("description", ""))
    # Claude Code truncates the skill listing at 1,536 characters, and Claude routes on that text
    emit(50 <= n <= 1536, "skill %s: description length %d (50-1536)" % (skill, n), "%d characters" % n)
PY
)
while IFS=$'\t' read -r ps_status ps_desc ps_reason; do
    case "$ps_status" in
        PASS) pass "$ps_desc" ;;
        FAIL) fail "$ps_desc" "$ps_reason" ;;
        "") ;;
        *) fail "SKILL.md frontmatter scan ran" "$ps_status $ps_desc $ps_reason" ;;
    esac
done <<< "$PS_FM"
assert_eq "no CLAUDE.md inside shipped skill directories" "" \
    "$(find skills -mindepth 2 -name CLAUDE.md | tr '\n' ' ')"

# --- Root plugin components: only commands/ ships as a component ---
for ps_p in hooks agents bin output-styles settings.json; do
    [ ! -e "$ps_p" ] && pass "root has no '$ps_p' (would run for every user)" \
        || fail "root has no '$ps_p'" "'$ps_p' is a plugin component path; move dev tooling under .claude/"
done
[ -d commands ] && pass "root commands/ exists" || fail "root commands/ exists" "missing"
assert_eq "commands/ holds only Markdown prompts" "" "$(find commands -type f ! -name '*.md' | tr '\n' ' ')"
for ps_cmd in commands/*.md; do
    sed -n '2,/^---$/p' "$ps_cmd" | grep -q '^description: .\{10,\}' && pass "command $(basename "$ps_cmd"): has description" \
        || fail "command $(basename "$ps_cmd"): has description" "no description in frontmatter"
done
assert_eq ".mcp.json has only the mcpServers key" '["mcpServers"]' "$(jq -c 'keys' .mcp.json 2>/dev/null)"
assert_eq ".mcp.json mcpServers is empty (it ships as plugin MCP config)" "0" "$(jq '.mcpServers | length' .mcp.json 2>/dev/null)"

# --- Stale names from the four source plugins ---
# Fixed strings, plus a bare /aws-diagram or /aws-diagram-design slash command. A path segment such as
# skills/aws-diagram-design/ or ../aws-diagram-design/assets is not a command: the regex skips a slash
# preceded by a path character and a name followed by ':', '/', '-' or a word character.
cat > "$TEST_TMP/ps-stale.py" <<'PY'
import os, re, sys
FIXED = ["aws-diagrams:", "kor-writing:", "aws-deck@", "whchoi:", "/aws-diagram-design:",
         "aws-diagrams 플러그인", "kor-writing 플러그인"]
BARE = re.compile(r"(?<![\w.:/~*-])/aws-diagram(?:-design)?(?![\w:/-])")
for top in sys.argv[1:]:
    for root, dirs, files in os.walk(top):
        dirs.sort()
        for f in sorted(files):
            path = os.path.join(root, f)
            data = open(path, "rb").read()
            if b"\0" in data[:8192]:
                continue  # binary (fonts, pptx, png)
            text = data.decode("utf-8", "replace")
            for no, line in enumerate(text.split("\n"), 1):
                hits = [s for s in FIXED if s in line] + BARE.findall(line)
                for h in hits:
                    print("%s:%d: %s" % (path, no, h))
PY
mkdir -p "$TEST_TMP/ps-stale-fixture"
cat > "$TEST_TMP/ps-stale-fixture/sample.md" <<'EOF'
call `/aws-diagram` here
then /aws-diagram-design.
Skill aws-diagrams:aws-diagram
ok /my-plugins:aws-diagram and /my-plugins:aws-diagram-design
ok skills/aws-diagram-design/assets and ../aws-diagram-design/assets and **/aws-diagram-design/scripts
ok `skills/aws-diagram-design` and https://github.com/whchoi98/aws-diagrams
EOF
PS_STALE_SELF=$(python3 -I "$TEST_TMP/ps-stale.py" "$TEST_TMP/ps-stale-fixture" 2>&1 | sed 's#.*/sample.md:##' | tr '\n' '|')
assert_eq "stale-name scanner: flags bare commands and old prefixes, ignores paths (self-test)" \
    "1: /aws-diagram|2: /aws-diagram-design|3: aws-diagrams:|" "$PS_STALE_SELF"
PS_STALE=$(python3 -I "$TEST_TMP/ps-stale.py" skills commands 2>&1 | head -20 | tr '\n' ' ')
assert_eq "no stale plugin names or bare /aws-diagram commands under skills/ and commands/" "" "$PS_STALE"

# --- Relative Markdown links and skill-dir paths resolve ---
# Links inside fenced code blocks and inline code are not links. Anchors and URLs are skipped.
PS_LINKS=$(python3 -I - <<'PY' 2>&1 || true
import glob, os, re
LINK = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
for f in sorted(glob.glob("commands/*.md") + glob.glob("skills/*/SKILL.md")
                + ["README.md", "CHANGELOG.md", "NOTICE.md"]):
    body, fence = [], False
    for line in open(f, encoding="utf-8").read().split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            continue
        if not fence:
            body.append(re.sub(r"`[^`\n]*`", "", line))
    for target in LINK.findall("\n".join(body)):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            continue
        path = target.split("#")[0]
        if path and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), path))):
            print("%s -> %s" % (f, target))
PY
)
assert_eq "relative links in commands/*.md, skills/*/SKILL.md, README, CHANGELOG, NOTICE resolve" "" "$(printf '%s' "$PS_LINKS" | tr '\n' ' ')"
# ${CLAUDE_SKILL_DIR}/x, $SKILL_DIR/x, {SKILL_DIR}/x and <skill-dir>/x in a skill's SKILL.md and references
PS_SKILLDIR=$(python3 -I - <<'PY' 2>&1 || true
import glob, os, re
REF = re.compile(r"(?:\$\{CLAUDE_SKILL_DIR\}|\$\{SKILL_DIR\}|\$SKILL_DIR|\{SKILL_DIR\}|<skill-dir>)/([\w.\-/]+)")
for d in sorted(glob.glob("skills/*/")):
    docs = [os.path.join(d, "SKILL.md")] + sorted(glob.glob(os.path.join(d, "references", "*.md")))
    for doc in docs:
        if not os.path.isfile(doc):
            continue
        for ref in sorted({m.rstrip(".,/") for m in REF.findall(open(doc, encoding="utf-8").read())}):
            if ref and not os.path.exists(os.path.join(d, ref)):
                print("%s -> %s" % (doc, ref))
PY
)
assert_eq "skill-dir paths in SKILL.md and references exist in that skill" "" "$(printf '%s' "$PS_SKILLDIR" | tr '\n' ' ')"

# --- Script validation: every shipped and dev script parses ---
while IFS= read -r ps_sh; do
    [ -n "$ps_sh" ] && assert_bash_syntax "bash -n $ps_sh" "$ps_sh"
done < <(find skills scripts .claude/hooks -name '*.sh' -type f 2>/dev/null | sort)
PS_PYC="$TEST_TMP/ps-pycache"   # bytecode goes here, never into skills/
while IFS= read -r ps_py; do
    [ -z "$ps_py" ] && continue
    PS_ERR=$(python3 -I -X pycache_prefix="$PS_PYC" -m py_compile "$ps_py" 2>&1) \
        && pass "py_compile $ps_py" || fail "py_compile $ps_py" "$(printf '%s' "$PS_ERR" | tail -1)"
done < <(find skills scripts -name '*.py' -type f 2>/dev/null | sort)
if command -v node >/dev/null 2>&1; then
    while IFS= read -r ps_js; do
        [ -z "$ps_js" ] && continue
        PS_ERR=$(node --check "$ps_js" 2>&1) && pass "node --check $ps_js" \
            || fail "node --check $ps_js" "$(printf '%s' "$PS_ERR" | head -1)"
    done < <(find skills -name '*.js' -type f -not -path '*/node_modules/*' | sort)
else
    skip "node --check for skills/**/*.js" "node is not installed"
fi

# --- License files and notices ---
for ps_f in LICENSE NOTICE.md third_party/LICENSE-aws-diagram-design \
            third_party/THIRD_PARTY_LICENSES-aws-diagrams.md third_party/NOTICE-kor-deslop.md; do
    assert_file_exists "license file: $ps_f" "$ps_f"
done
grep -qF "MIT License" LICENSE 2>/dev/null && pass "LICENSE is the MIT text NOTICE.md points to" \
    || fail "LICENSE is the MIT text NOTICE.md points to" "LICENSE missing or not MIT"
assert_contains "kor-deslop SKILL.md points at third_party/NOTICE-kor-deslop.md" \
    "$(cat skills/kor-deslop/SKILL.md 2>/dev/null)" "third_party/NOTICE-kor-deslop.md"
PS_NOTICE=$(cat NOTICE.md 2>/dev/null)
for ps_d in skills/*/; do
    assert_contains "NOTICE.md names the license source of ${ps_d%/}" "$PS_NOTICE" "${ps_d%/}/"
done

# --- Bilingual documents use ASCII anchors ---
for ps_doc in README.md CHANGELOG.md $(grep -rlF '<a id="english">' docs --include='*.md' 2>/dev/null | sort); do
    if grep -qF '<a id="english"></a>' "$ps_doc" && grep -qF '<a id="korean"></a>' "$ps_doc"; then
        pass "bilingual anchors: $ps_doc"
    else
        fail "bilingual anchors: $ps_doc" "missing <a id=\"english\"></a> or <a id=\"korean\"></a>"
    fi
done
PS_EMOJI=$(LC_ALL=C.UTF-8 grep -lP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' README.md CHANGELOG.md NOTICE.md \
    $(find docs -name '*.md' 2>/dev/null) 2>/dev/null | tr '\n' ' ')
assert_eq "no emojis in user-facing docs" "" "$PS_EMOJI"

# --- docs/reference: INDEX links, layers linked from CLAUDE.md, Code Pointers ---
PS_INDEX_BAD=""
for ps_link in $(grep -oP '\]\(\K[^)#[:space:]]+(?=[)#])' docs/reference/INDEX.md 2>/dev/null | grep -vE '^[a-z]+:' | sort -u); do
    [ -e "docs/reference/$ps_link" ] || PS_INDEX_BAD+=" $ps_link"
done
assert_file_exists "docs/reference/INDEX.md exists" docs/reference/INDEX.md
assert_eq "docs/reference/INDEX.md links resolve" "" "${PS_INDEX_BAD# }"
for ps_layer in $(grep -oP 'docs/reference/\K[a-z-]+(?=\.md\))' CLAUDE.md | grep -v '^INDEX$' | sort -u); do
    assert_file_exists "reference layer linked from CLAUDE.md: $ps_layer" "docs/reference/$ps_layer.md"
done
PS_BAD_POINTERS=""
for ps_ref in docs/reference/*.md; do
    [ "$(basename "$ps_ref")" = "INDEX.md" ] && continue
    while IFS= read -r ps_pointer; do
        ps_path="${ps_pointer%%:*}"
        ps_range="${ps_pointer#"$ps_path"}"; ps_range="${ps_range#:}"
        if [ ! -e "$ps_path" ]; then
            PS_BAD_POINTERS+=" $ps_ref->$ps_pointer"
        elif [ -n "$ps_range" ] && [ "$(wc -l < "$ps_path")" -lt "${ps_range##*-}" ]; then
            PS_BAD_POINTERS+=" $ps_ref->$ps_pointer(line)"
        fi
    done < <(sed -n '/^### 4\./,/^### 5\./p' "$ps_ref" | grep -oP '^- `\K[^`]+(?=`)' | grep -E '^[A-Za-z0-9_./-]+(:[0-9-]+)?$' || true)
done
assert_eq "reference Code Pointers resolve to existing paths and lines" "" "${PS_BAD_POINTERS# }"

# --- Harness files ---
for ps_f in CLAUDE.md README.md CHANGELOG.md LICENSE NOTICE.md .editorconfig .env.example .gitignore .mcp.json \
            skills/CLAUDE.md tests/CLAUDE.md .claude/settings.json \
            docs/architecture.md docs/onboarding.md docs/decisions/.template.md docs/runbooks/.template.md \
            docs/runbooks/release-plugin.md docs/reference/INDEX.md; do
    assert_file_exists "harness file: $ps_f" "$ps_f"
done
for ps_script in scripts/setup.sh scripts/install-hooks.sh tests/run-all.sh tests/hooks/*.sh tests/structure/*.sh; do
    assert_file_executable "$ps_script is executable" "$ps_script"
    assert_bash_syntax "$ps_script valid bash" "$ps_script"
done
# Test files are sourced into run-all.sh; assigning its variables corrupts the totals
PS_CLOBBER=$(grep -nE '^\s*(TOTAL|PASSED|FAILED|SKIPPED|FAILURES|FILTER|TEST_TMP|PROJECT_ROOT|SCRIPT_DIR)\+?=' \
    tests/hooks/*.sh tests/structure/*.sh 2>/dev/null | tr '\n' ' ')
assert_eq "test files do not assign run-all.sh variables" "" "$PS_CLOBBER"
PS_TEST_REFS=""
for ps_t in $(grep -ohE 'tests/(hooks|structure)/[A-Za-z0-9_.-]+\.sh' CLAUDE.md tests/CLAUDE.md 2>/dev/null | sort -u); do
    [ -f "$ps_t" ] || PS_TEST_REFS+=" $ps_t"
done
assert_eq "test files named in CLAUDE.md and tests/CLAUDE.md exist" "" "${PS_TEST_REFS# }"

# --- .gitignore keeps secrets and work folders out (checked in a scratch repo, so no git checkout is needed) ---
PS_GI="$TEST_TMP/ps-gitignore"
mkdir -p "$PS_GI" && git -C "$PS_GI" init -q 2>/dev/null && cp .gitignore "$PS_GI/"
for ps_pattern in ".env" ".claude/settings.local.json" "*.zip" "__pycache__/"; do
    assert_contains ".gitignore has $ps_pattern" "$(cat .gitignore)" "$ps_pattern"
done
git -C "$PS_GI" check-ignore -q .env && pass ".env is ignored" || fail ".env is ignored" "not ignored"
git -C "$PS_GI" check-ignore -q .env.example && fail ".env.example is tracked" "ignored" || pass ".env.example is tracked"
git -C "$PS_GI" check-ignore -q 2026-01-01-sample/x.md && pass "blog work folders are ignored" \
    || fail "blog work folders are ignored" "<YYYY-MM-DD>-<slug>/ not ignored"

# --- Dev harness: commands, project skills, agents ---
for ps_cmd in .claude/commands/*.md; do
    [ -f "$ps_cmd" ] || continue
    PS_CMD_CONTENT=$(cat "$ps_cmd")
    assert_contains "dev command $(basename "$ps_cmd"): has description" "$PS_CMD_CONTENT" "description:"
    assert_contains "dev command $(basename "$ps_cmd"): has allowed-tools" "$PS_CMD_CONTENT" "allowed-tools:"
done
if [ -f .claude/commands/deploy.md ]; then
    PS_DEPLOY_TOOLS=$(sed -n 's/^allowed-tools: //p' .claude/commands/deploy.md)
    assert_not_contains "dev command deploy: git push is not pre-allowed" "$PS_DEPLOY_TOOLS" "git push"
    assert_not_contains "dev command deploy: git commit is not pre-allowed" "$PS_DEPLOY_TOOLS" "git commit"
fi
for ps_sk in .claude/skills/*/SKILL.md; do
    [ -f "$ps_sk" ] || continue
    ps_skn=$(basename "$(dirname "$ps_sk")")
    assert_eq "project skill $ps_skn: name matches directory" "$ps_skn" \
        "$(sed -n '2,/^---$/s/^name: //p' "$ps_sk" | head -1 | tr -d '"')"
    grep -q '^description: .\{20,\}' "$ps_sk" && pass "project skill $ps_skn: has description" \
        || fail "project skill $ps_skn: has description" "missing"
done
[ ! -e .claude/skills/code-review ] && pass "no project skill shadows built-in /code-review" \
    || fail "no project skill shadows built-in /code-review" ".claude/skills/code-review exists"
for ps_agent in .claude/agents/*.md; do
    [ -f "$ps_agent" ] || continue
    assert_eq "agent $(basename "$ps_agent" .md): name matches file" "$(basename "$ps_agent" .md)" \
        "$(sed -n '2,/^---$/s/^name: //p' "$ps_agent" | head -1)"
done
assert_eq "no .yml agents (not loaded by Claude Code)" "" "$(find .claude/agents -name '*.yml' 2>/dev/null | tr '\n' ' ')"

# --- CLAUDE.md ---
PS_CLAUDE=$(cat CLAUDE.md)
for ps_section in "Overview" "Tech Stack" "Project Structure" "Conventions" "Key Commands" "Auto-Sync Rules"; do
    grep -qF "## $ps_section" CLAUDE.md && pass "CLAUDE.md: has $ps_section" || fail "CLAUDE.md: has $ps_section" "not found"
done
PS_LINES=$(wc -l < CLAUDE.md | tr -d ' ')
[ "$PS_LINES" -le 500 ] && pass "CLAUDE.md under 500 lines ($PS_LINES)" || fail "CLAUDE.md under 500 lines" "$PS_LINES lines"
assert_contains "CLAUDE.md: install id ${PS_NAME}@${PS_MKT}" "$PS_CLAUDE" "${PS_NAME}@${PS_MKT}"
printf '%s\n' "$PS_CLAUDE" | grep -qiE 'No `?Co-Authored-By' && pass "CLAUDE.md: no Co-Authored-By rule" \
    || fail "CLAUDE.md: no Co-Authored-By rule" "rule not stated"
grep -qF "<!-- AUTO-MANAGED:references -->" CLAUDE.md \
    && pass "CLAUDE.md: has references AUTO-MANAGED block" || fail "CLAUDE.md: has references AUTO-MANAGED block" "missing"

# --- README install commands match the manifests and the repository ---
PS_README=$(cat README.md)
assert_contains "README: install id" "$PS_README" "claude plugin install ${PS_NAME}@${PS_MKT}"
assert_contains "README: marketplace update command" "$PS_README" "claude plugin marketplace update ${PS_MKT}"
assert_contains "README: plugin update command" "$PS_README" "claude plugin update ${PS_NAME}@${PS_MKT}"
PS_REMOTE=$(git remote get-url origin 2>/dev/null | sed -E 's#(\.git)?$##; s#.*github\.com[:/]##' || true)
[ -z "$PS_REMOTE" ] && PS_REMOTE=$(jq -r '.repository // empty' "$PS_PJ" 2>/dev/null | sed -E 's#(\.git)?$##; s#.*github\.com[:/]##')
if [ -n "$PS_REMOTE" ]; then
    assert_contains "README: marketplace add uses the repository ($PS_REMOTE)" "$PS_README" "claude plugin marketplace add $PS_REMOTE"
else
    skip "README: marketplace add uses the repository" "no origin remote and no plugin.json repository"
fi
for ps_heading in Overview Prerequisites Installation Usage Configuration "Project Structure" Testing License Contact \
                  "개요" "사전 요구 사항" "설치 방법" "사용법" "설정" "프로젝트 구조" "테스트" "라이선스" "연락처"; do
    grep -qx "## $ps_heading" README.md && pass "README: section '$ps_heading'" || fail "README: section '$ps_heading'" "missing"
done

# --- Claude Code's own validation (ICON_MISSING is a plugin-directory warning and is expected) ---
if command -v claude >/dev/null 2>&1; then
    PS_VALIDATE=$(claude plugin validate . 2>&1); PS_VALIDATE_RC=$?
    assert_eq "claude plugin validate . exits 0" "0" "$PS_VALIDATE_RC"
    assert_contains "claude plugin validate . passes" "$PS_VALIDATE" "Validation passed"
else
    skip "claude plugin validate . passes" "Claude Code CLI not installed"
fi

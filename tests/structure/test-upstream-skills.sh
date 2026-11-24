#!/bin/bash
# Skills vendored from other repositories (sourced by tests/run-all.sh): ui-deslop from heydamir/unslop and
# eng-deslop from blader/humanizer, the manifest scripts/upstream-skills.json, scripts/sync_upstream_skills.py
# and the weekly workflow. Everything here is offline: a source is a folder passed with --source.
# The skill that is rebuilt from its source by a recipe (aws-diagram-design) is in test-upstream-derived.sh.
# Needs python3 and git only, so the workflow can run this file on a GitHub runner.

US_SYNC=scripts/sync_upstream_skills.py
US_MAN=scripts/upstream-skills.json
US_WF=.github/workflows/sync-upstream-skills.yml
us_sync() { python3 -I -B "$US_SYNC" "$@"; }
us_sha() { sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }
# us_fm <SKILL.md>: the frontmatter lines; us_body <SKILL.md>: everything after the frontmatter
us_fm() { awk 'NR==1{next} /^---$/{exit} {print}' "$1"; }
us_body() { awk 'c>=2{print} /^---$/{c++}' "$1"; }
# us_vendored_manifest <dest folder>: the manifest with the vendored skills only, for a copy that holds just those
us_vendored_manifest() {
    python3 -I -B - "$US_MAN" "$1/upstream-skills.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
d["skills"] = [e for e in d["skills"] if e.get("mode") != "derived"]
json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
}

assert_file_exists "sync script: $US_SYNC" "$US_SYNC"
assert_json_valid "manifest: $US_MAN is valid JSON" "$US_MAN"

# --- The vendored skills are what the manifest records ---
US_OUT=$(us_sync verify 2>&1); US_RC=$?
assert_eq "verify: the vendored skills are what the manifest records" "0" "$US_RC"
US_FACTS=$(python3 -I -B -c '
import json
for e in json.load(open("scripts/upstream-skills.json"))["skills"]:
    if e.get("mode") == "derived":
        continue
    print("|".join([e["name"], e["repo"], e["license"], e.get("commit", ""), str(len(e.get("files", {})))]))')
assert_eq "manifest: the vendored skills, their sources and licenses" \
    "ui-deslop|heydamir/unslop|CC-BY-4.0 eng-deslop|blader/humanizer|MIT" \
    "$(printf '%s\n' "$US_FACTS" | cut -d'|' -f1-3 | tr '\n' ' ' | sed 's/ $//')"
US_NOTICE=$(cat NOTICE.md 2>/dev/null)
while IFS='|' read -r us_n us_repo us_lic us_commit us_count; do
    [ -n "$us_n" ] || continue
    assert_contains "verify: reports $us_n" "$US_OUT" "OK $us_n: $us_count files, $us_repo ${us_commit:0:7}"
    [[ "$us_commit" =~ ^[0-9a-f]{40}$ ]] && pass "manifest: $us_n is pinned to a full commit id" \
        || fail "manifest: $us_n is pinned to a full commit id" "commit is '$us_commit'"
    US_FM=$(us_fm "skills/$us_n/SKILL.md")
    assert_contains "$us_n SKILL.md: name is the folder name" "$US_FM" "name: $us_n"
    assert_contains "$us_n SKILL.md: keeps the source's license field" "$US_FM" "license: $us_lic"
    assert_contains "$us_n SKILL.md: metadata names the source" "$US_FM" "  upstream: https://github.com/$us_repo"
    assert_contains "$us_n SKILL.md: metadata names the pinned commit" "$US_FM" "  upstream-commit: $us_commit"
    assert_contains "$us_n SKILL.md: metadata says what was changed" "$US_FM" "  modified: frontmatter name and description replaced by my-plugins"
    assert_file_exists "license copy: third_party/LICENSE-$us_n" "third_party/LICENSE-$us_n"
    US_ROW=$(printf '%s\n' "$US_NOTICE" | grep -F "\`skills/$us_n/\`" || true)
    assert_contains "NOTICE.md row of $us_n: names the source" "$US_ROW" "github.com/$us_repo"
    assert_contains "NOTICE.md row of $us_n: points at the license copy" "$US_ROW" "third_party/LICENSE-$us_n"
    assert_contains "NOTICE.md row of $us_n: says what was changed" "$US_ROW" "name and description"
done <<< "$US_FACTS"

US_UI_DESC=$(us_fm skills/ui-deslop/SKILL.md | grep '^description: ')
US_EN_DESC=$(us_fm skills/eng-deslop/SKILL.md | grep '^description: ')
for us_t in "UI의 AI 슬롭을 제거한다" "unslop this dashboard" "UI 슬롭 제거" "my-plugins:kor-deslop" "my-plugins:eng-deslop" \
            "heydamir/unslop(CC BY 4.0)"; do
    assert_contains "ui-deslop description: '$us_t'" "$US_UI_DESC" "$us_t"
done
for us_t in "영어 글의 AI 슬롭을 제거한다" "humanize this" "영어 AI 슬롭 제거" "my-plugins:kor-deslop" "my-plugins:ui-deslop" \
            "blader/humanizer(MIT)"; do
    assert_contains "eng-deslop description: '$us_t'" "$US_EN_DESC" "$us_t"
done
assert_contains "kor-deslop description: sends English text to eng-deslop" \
    "$(us_fm skills/kor-deslop/SKILL.md | grep '^description: ')" "my-plugins:eng-deslop"
# The credit the CC BY 4.0 source asks to keep, and the license texts
US_UI_BODY=$(us_body skills/ui-deslop/SKILL.md)
assert_contains "ui-deslop body: keeps the author's credit" "$US_UI_BODY" "created by Damir Sokolovsky"
assert_contains "ui-deslop body: keeps the license line" "$US_UI_BODY" "CC BY 4.0"
assert_contains "third_party/LICENSE-ui-deslop is the CC BY 4.0 text" "$(head -3 third_party/LICENSE-ui-deslop 2>/dev/null)" "Attribution 4.0 International"
assert_contains "third_party/LICENSE-eng-deslop is the MIT text with its copyright line" \
    "$(head -4 third_party/LICENSE-eng-deslop 2>/dev/null | tr '\n' ' ')" "MIT License  Copyright (c) 2025 Siqi Chen"
[ ! -e skills/ui-deslop/agents ] && pass "ui-deslop: the source's agents folder is left out" \
    || fail "ui-deslop: the source's agents folder is left out" "skills/ui-deslop/agents exists"
assert_eq "eng-deslop: SKILL.md is the only file" "SKILL.md" "$(cd skills/eng-deslop 2>/dev/null && find . -type f | sed 's#^\./##' | sort | tr '\n' ' ' | sed 's/ $//')"
if command -v node >/dev/null 2>&1; then
    for us_js in skills/ui-deslop/scripts/*.mjs; do
        US_ERR=$(node --check "$us_js" 2>&1) && pass "node --check $us_js" || fail "node --check $us_js" "$(printf '%s' "$US_ERR" | head -1)"
    done
else
    skip "node --check skills/ui-deslop/scripts/*.mjs" "node is not installed"
fi

# --- A vendored file changed by hand is found (on a copy, so the repository is not touched) ---
US_T="$TEST_TMP/us-tamper"
mkdir -p "$US_T/scripts" "$US_T/skills" "$US_T/third_party"
us_vendored_manifest "$US_T/scripts"
cp -R skills/ui-deslop skills/eng-deslop "$US_T/skills/"
cp third_party/LICENSE-ui-deslop third_party/LICENSE-eng-deslop "$US_T/third_party/"
us_t() { us_sync "$@" --root "$US_T" 2>&1; }
# us_tamper <description> <expected text>: verify must fail and name the problem
us_tamper() {
    local out rc
    out=$(us_t verify); rc=$?
    assert_eq "verify finds: $1 (exit 1)" "1" "$rc"
    assert_contains "verify finds: $1 (message)" "$out" "$2"
}
us_restore() { rm -rf "$US_T/skills/ui-deslop" "$US_T/skills/eng-deslop"; cp -R skills/ui-deslop skills/eng-deslop "$US_T/skills/"
               cp third_party/LICENSE-ui-deslop "$US_T/third_party/"; us_vendored_manifest "$US_T/scripts"; }
US_OUT=$(us_t verify); assert_eq "verify: the copy passes before it is changed" "0" "$?"
echo "extra rule" >> "$US_T/skills/ui-deslop/references/tokens.md"
us_tamper "a reference file edited by hand" "ui-deslop: references/tokens.md differs from the source"; us_restore
echo "console.log(1)" >> "$US_T/skills/ui-deslop/scripts/story.mjs"
us_tamper "a script edited by hand" "ui-deslop: scripts/story.mjs differs from the source"; us_restore
echo "note" > "$US_T/skills/ui-deslop/notes.md"
us_tamper "a file added by hand" "ui-deslop: notes.md is not a file of the source"; us_restore
rm "$US_T/skills/ui-deslop/references/rtl.md"
us_tamper "a file removed by hand" "ui-deslop: references/rtl.md is missing"; us_restore
echo "One more rule." >> "$US_T/skills/eng-deslop/SKILL.md"
us_tamper "a SKILL.md body edited by hand" "eng-deslop: SKILL.md differs from what"; us_restore
sed -i 's/^name: ui-deslop$/name: unslop/' "$US_T/skills/ui-deslop/SKILL.md"
us_tamper "a frontmatter name put back" "ui-deslop: SKILL.md \`name\` is not the manifest's"; us_restore
echo "more terms" >> "$US_T/third_party/LICENSE-ui-deslop"
us_tamper "a license copy edited" "ui-deslop: third_party/LICENSE-ui-deslop differs from the source's license"; us_restore
rm -rf "$US_T/skills/eng-deslop"
us_tamper "a vendored skill removed" "eng-deslop: skills/eng-deslop is missing"; us_restore
# The description is changed in the manifest and written by `render`, never in SKILL.md
python3 -I -B - "$US_T/scripts/upstream-skills.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8"))
d["skills"][1]["description"] = "영어 글의 AI 슬롭을 제거한다. 새 설명: 콜론 뒤 공백과 \"따옴표\"가 있어도 그대로 들어가야 한다. my-plugins:kor-deslop"
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
us_tamper "a description changed in the manifest only" "eng-deslop: SKILL.md \`description\` is not the manifest's; run \`render\`"
US_OUT=$(us_t render --skill eng-deslop); assert_eq "render: exit 0" "0" "$?"
assert_contains "render: reports the skill" "$US_OUT" "RENDERED eng-deslop"
US_OUT=$(us_t verify); assert_eq "render: verify passes again" "0" "$?"
assert_contains "render: the new description is in SKILL.md, quoted because of ': '" \
    "$(us_fm "$US_T/skills/eng-deslop/SKILL.md")" 'description: "영어 글의 AI 슬롭을 제거한다. 새 설명: 콜론 뒤 공백과 \"따옴표\"가 있어도 그대로 들어가야 한다. my-plugins:kor-deslop"'
assert_eq "render: the body is untouched" "$(us_body skills/eng-deslop/SKILL.md | sha256sum)" "$(us_body "$US_T/skills/eng-deslop/SKILL.md" | sha256sum)"
assert_contains "render: the other frontmatter lines stay" "$(us_fm "$US_T/skills/eng-deslop/SKILL.md")" "  upstream-commit: "

# --- update from a source folder: first import ---
US_E="$TEST_TMP/us-e2e"; US_R="$US_E/root"; US_S1="$US_E/src1"
mkdir -p "$US_R/scripts" "$US_R/skills" "$US_R/third_party" "$US_S1/skills/demo/references" "$US_S1/skills/demo/scripts" "$US_S1/skills/demo/agents"
cat > "$US_R/scripts/upstream-skills.json" <<'EOF'
{"schema": 1, "skills": [{"name": "demo-skill", "repo": "example/demo", "ref": "HEAD", "path": "skills/demo",
  "exclude": ["agents/*"], "allow_ext": [".md", ".mjs"], "license": "MIT", "license_file": "LICENSE",
  "changes": "frontmatter name and description replaced, agents folder left out",
  "description": "데모 화면을 다듬는다. \"demo this\" 요청에 사용한다: 콜론 뒤에 공백이 있어도 frontmatter가 깨지지 않아야 한다."}]}
EOF
cat > "$US_R/CHANGELOG.md" <<'EOF'
# Changelog

<a id="english"></a>

# English

## [Unreleased]

### Added
- `other`: something new

### Fixed
- `other`: a fix

## [1.0.0] - 2026-01-01

[Unreleased]: https://example.com/compare/v1.0.0...HEAD

---

<a id="korean"></a>

# 한국어

## [Unreleased]

## [1.0.0] - 2026-01-01

[Unreleased]: https://example.com/compare/v1.0.0...HEAD
EOF
cat > "$US_S1/skills/demo/SKILL.md" <<'EOF'
---
name: demo
description: |
  Demo skill of the source.
  Second line.
license: MIT
metadata:
  author: Someone
---

# Demo

Body line one. Run `node <skill folder>/scripts/run.mjs`. See https://example.com/one.
EOF
echo "# A" > "$US_S1/skills/demo/references/a.md"
echo 'console.log("demo");' > "$US_S1/skills/demo/scripts/run.mjs"
echo "interface: {}" > "$US_S1/skills/demo/agents/openai.yaml"
printf 'MIT License\n\nCopyright (c) 2026 Someone\n' > "$US_S1/LICENSE"
echo "# readme of the source" > "$US_S1/README.md"
US_C1=1111111111111111111111111111111111111111; US_C2=2222222222222222222222222222222222222222
us_e() { us_sync "$@" --root "$US_R" 2>&1; }
us_commit() { python3 -I -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["skills"][0].get("commit"))' "$US_R/scripts/upstream-skills.json"; }

US_OUT=$(us_e verify); assert_eq "verify: a skill that was never imported fails (exit 1)" "1" "$?"
assert_contains "verify: a skill that was never imported fails (message)" "$US_OUT" "demo-skill: not vendored yet"
US_OUT=$(us_e update --skill demo-skill --source "$US_S1" --commit "$US_C1" --date 2026-01-02 --report "$US_E/report1.md")
assert_eq "update (first import): exit 0" "0" "$?"
assert_contains "update (first import): reports the files" "$US_OUT" "UPDATED demo-skill: example/demo 1111111, 3 added, 0 changed, 0 removed"
US_D="$US_R/skills/demo-skill"
assert_eq "update: the skill's files, without agents/ and without the source's README" \
    "SKILL.md references/a.md scripts/run.mjs" "$(cd "$US_D" 2>/dev/null && find . -type f | sed 's#^\./##' | sort | tr '\n' ' ' | sed 's/ $//')"
US_FM=$(us_fm "$US_D/SKILL.md")
assert_contains "update: name is ours" "$US_FM" "name: demo-skill"
assert_contains "update: description is ours, quoted because it holds ': '" "$US_FM" \
    'description: "데모 화면을 다듬는다. \"demo this\" 요청에 사용한다: 콜론 뒤에 공백이 있어도 frontmatter가 깨지지 않아야 한다."'
assert_not_contains "update: the source's description is gone" "$US_FM" "Demo skill of the source."
assert_not_contains "update: the source's block lines are gone" "$US_FM" "Second line."
assert_contains "update: the source's license field stays" "$US_FM" "license: MIT"
assert_contains "update: the source's metadata stays" "$US_FM" "  author: Someone"
assert_contains "update: metadata names the source" "$US_FM" "  upstream: https://github.com/example/demo"
assert_contains "update: metadata names the commit" "$US_FM" "  upstream-commit: $US_C1"
assert_contains "update: metadata says what was changed" "$US_FM" "  modified: frontmatter name and description replaced, agents folder left out"
assert_eq "update: frontmatter has no line twice" "" "$(printf '%s\n' "$US_FM" | sed 's/:.*//' | sort | uniq -d | tr '\n' ' ')"
assert_eq "update: the body is the source's, byte for byte" "$(us_body "$US_S1/skills/demo/SKILL.md" | sha256sum)" "$(us_body "$US_D/SKILL.md" | sha256sum)"
cmp -s "$US_S1/skills/demo/references/a.md" "$US_D/references/a.md" && cmp -s "$US_S1/skills/demo/scripts/run.mjs" "$US_D/scripts/run.mjs" \
    && pass "update: the other files are the source's, byte for byte" || fail "update: the other files are the source's, byte for byte" "a file differs"
cmp -s "$US_S1/LICENSE" "$US_R/third_party/LICENSE-demo-skill" && pass "update: the license is copied to third_party/LICENSE-demo-skill" \
    || fail "update: the license is copied to third_party/LICENSE-demo-skill" "missing or different"
assert_eq "update: the manifest records the commit" "$US_C1" "$(us_commit)"
# CHANGELOG: one line per language under ### Changed of [Unreleased], between Added and Fixed
US_CL=$(cat "$US_R/CHANGELOG.md")
US_EN_LINE='- `demo-skill`: synced with upstream example/demo `1111111` (2026-01-02), 3 files changed'
US_KO_LINE='- `demo-skill`: upstream example/demo `1111111`(2026-01-02)와 동기화, 파일 3개 변경'
assert_contains "CHANGELOG: English line" "$US_CL" "$US_EN_LINE"
assert_contains "CHANGELOG: Korean line" "$US_CL" "$US_KO_LINE"
assert_eq "CHANGELOG (English): Added, Changed with the line, Fixed, then the release" \
    "## [Unreleased]|### Added|### Changed|$US_EN_LINE|### Fixed|## [1.0.0] - 2026-01-01" \
    "$(sed -n '/<a id="english">/,/<a id="korean">/p' "$US_R/CHANGELOG.md" | grep -E '^## \[|^### |demo-skill' | tr '\n' '|' | sed 's/|$//')"
assert_eq "CHANGELOG (Korean): Changed with the line inside [Unreleased]" \
    "## [Unreleased]|### Changed|$US_KO_LINE|## [1.0.0] - 2026-01-01" \
    "$(sed -n '/<a id="korean">/,$p' "$US_R/CHANGELOG.md" | grep -E '^## \[|^### |demo-skill' | tr '\n' '|' | sed 's/|$//')"
assert_eq "CHANGELOG: the other entries and the link lines stay" "2 2 2" \
    "$(grep -c '`other`' "$US_R/CHANGELOG.md") $(grep -c '^\[Unreleased\]: ' "$US_R/CHANGELOG.md") $(grep -c '^## \[1.0.0\]' "$US_R/CHANGELOG.md")"
US_REP=$(cat "$US_E/report1.md" 2>/dev/null)
assert_contains "report: names the skill and its source" "$US_REP" "## demo-skill (example/demo)"
assert_contains "report: lists the files" "$US_REP" '- added (3): `SKILL.md`, `references/a.md`, `scripts/run.mjs`'
assert_contains "report: points at code that runs on a user's machine" "$US_REP" "Code that runs on a user's machine changed: scripts/run.mjs"
assert_contains "report: tells the reviewer to read the diff" "$US_REP" "Read the diff of every file below before merging"
US_OUT=$(us_e verify); assert_eq "verify: passes after the import" "0" "$?"
US_OUT=$(us_e check --skill demo-skill --source "$US_S1" --commit "$US_C2"); assert_eq "check: same files, exit 0" "0" "$?"
assert_contains "check: says the skill's files are the same" "$US_OUT" "the skill's files are the same"
US_BEFORE=$(us_sha "$US_R/scripts/upstream-skills.json")
US_OUT=$(us_e update --skill demo-skill --source "$US_S1" --commit "$US_C2"); assert_eq "update with nothing new: exit 0" "0" "$?"
assert_contains "update with nothing new: says so" "$US_OUT" "OK demo-skill: nothing to update"
assert_eq "update with nothing new: the manifest keeps the old commit" "$US_BEFORE" "$(us_sha "$US_R/scripts/upstream-skills.json")"

# --- update from a changed source ---
US_S2="$US_E/src2"; cp -R "$US_S1" "$US_S2"
echo "# A, second edition" > "$US_S2/skills/demo/references/a.md"
echo "# B" > "$US_S2/skills/demo/references/b.md"
rm "$US_S2/skills/demo/scripts/run.mjs"
python3 -I -B - "$US_S2/skills/demo/SKILL.md" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = s.replace("  Demo skill of the source.\n", "  Demo skill, now for @everyone with `ticks`.\n")
s = s.replace("See https://example.com/one.", "See https://example.com/one and https://example.com/two.")
open(p, "w", encoding="utf-8").write(s)
PY
US_OUT=$(us_e check --skill demo-skill --source "$US_S2" --commit "$US_C2" --date 2026-02-03); assert_eq "check: an update is exit 10" "10" "$?"
assert_contains "check: names the update" "$US_OUT" "UPDATE demo-skill: example/demo 1111111 to 2222222 (2026-02-03)"
assert_contains "check: added files" "$US_OUT" "added: references/b.md"
assert_contains "check: changed files" "$US_OUT" "changed: SKILL.md, references/a.md"
assert_contains "check: removed files" "$US_OUT" "removed: scripts/run.mjs"
assert_eq "check: writes nothing" "$US_BEFORE" "$(us_sha "$US_R/scripts/upstream-skills.json")"
US_OUT=$(us_e update --skill demo-skill --source "$US_S2" --commit "$US_C2" --date 2026-02-03 --report "$US_E/report2.md")
assert_eq "update (changed source): exit 0" "0" "$?"
assert_contains "update (changed source): reports the files" "$US_OUT" "UPDATED demo-skill: example/demo 2222222, 1 added, 2 changed, 1 removed"
assert_contains "update (changed source): notes that the source changed its own description" "$US_OUT" "NOTE The source changed its own description"
assert_eq "update (changed source): a file the source dropped is gone, with its folder" \
    "SKILL.md references/a.md references/b.md" "$(cd "$US_D" && find . -mindepth 1 | sed 's#^\./##' | grep -v '^references$' | sort | tr '\n' ' ' | sed 's/ $//')"
assert_eq "update (changed source): the changed file is the new one" "# A, second edition" "$(cat "$US_D/references/a.md")"
assert_contains "update (changed source): metadata names the new commit" "$(us_fm "$US_D/SKILL.md")" "  upstream-commit: $US_C2"
assert_contains "update (changed source): our description stays" "$(us_fm "$US_D/SKILL.md")" 'description: "데모 화면을 다듬는다.'
assert_eq "update (changed source): the manifest records the new commit" "$US_C2" "$(us_commit)"
assert_eq "CHANGELOG: still one line per language for the skill, the new one" \
    "1 1 1 1" "$(grep -c 'demo-skill`: synced with upstream' "$US_R/CHANGELOG.md") $(grep -c 'demo-skill`: upstream ' "$US_R/CHANGELOG.md") $(grep -cF '`2222222` (2026-02-03), 4 files changed' "$US_R/CHANGELOG.md") $(grep -cF '`2222222`(2026-02-03)와 동기화, 파일 4개 변경' "$US_R/CHANGELOG.md")"
assert_eq "CHANGELOG: one Changed heading per language" "2" "$(grep -c '^### Changed$' "$US_R/CHANGELOG.md")"
US_REP=$(cat "$US_E/report2.md" 2>/dev/null)
assert_contains "report: links the comparison of the two commits" "$US_REP" "https://github.com/example/demo/compare/$US_C1...$US_C2"
assert_contains "report: the source's text sits in a code span, backticks removed" "$US_REP" "\`Demo skill, now for @everyone with 'ticks'. Second line.\`"
assert_contains "report: lists a link that is new" "$US_REP" 'Links that were not in the skill before: `https://example.com/two`'
assert_contains "report: removed files" "$US_REP" '- removed (1): `scripts/run.mjs`'
US_OUT=$(us_e verify); assert_eq "verify: passes after the update" "0" "$?"

# --- A source that breaks a rule is refused and nothing is written ---
US_S3="$US_E/src3"; US_C3=3333333333333333333333333333333333333333
US_BEFORE=$(us_sha "$US_R/scripts/upstream-skills.json")
us_fresh() { rm -rf "$US_S3"; cp -R "$US_S2" "$US_S3"; }
# us_refuse <description> <expected text>: update exits 1 with the text, the skill and the manifest stay
us_refuse() {
    local out rc
    out=$(us_e update --skill demo-skill --source "$US_S3" --commit "$US_C3"); rc=$?
    assert_eq "refused: $1 (exit 1)" "1" "$rc"
    assert_contains "refused: $1 (message)" "$out" "$2"
    [ "$(us_sha "$US_R/scripts/upstream-skills.json")" = "$US_BEFORE" ] && us_e verify >/dev/null \
        && pass "refused: $1 (the skill and the manifest are untouched)" \
        || fail "refused: $1 (the skill and the manifest are untouched)" "the manifest changed or verify fails"
}
us_fresh; sed -i 's/^license: MIT$/license: GPL-3.0-only/' "$US_S3/skills/demo/SKILL.md"
us_refuse "the source changed its license" "the source's license is 'GPL-3.0-only', the manifest says 'MIT'"
us_fresh; ln -s /etc/hostname "$US_S3/skills/demo/references/link.md"
us_refuse "a symbolic link" "references/link.md is a symbolic link in the source"
us_fresh; mv "$US_S3/skills/demo/references" "$US_S3/skills/demo/real-references"; ln -s real-references "$US_S3/skills/demo/references"
us_refuse "a linked folder" "the folder references is a symbolic link in the source"
us_fresh; echo "rm -rf /" > "$US_S3/skills/demo/references/x.sh"
us_refuse "a file type the manifest does not allow" "references/x.sh has a file type the manifest does not allow (.sh)"
us_fresh; echo "x" > "$US_S3/skills/demo/references/noext"
us_refuse "a file without an extension" "references/noext has a file type the manifest does not allow (no extension)"
us_fresh; head -c 2100000 /dev/zero > "$US_S3/skills/demo/references/big.md"
us_refuse "a file over the size limit" "references/big.md is 2100000 bytes, over the limit"
us_fresh; echo "x" > "$US_S3/skills/demo/references/a@b.md"
us_refuse "an unusual file name" "is an unusual file name"
us_fresh; echo "x" > "$US_S3/skills/demo/references/.hidden.md"
us_refuse "a hidden file" "references/.hidden.md is a hidden file"
us_fresh; sed -i '1d' "$US_S3/skills/demo/SKILL.md"
us_refuse "a SKILL.md without frontmatter" "SKILL.md does not open with ---"
us_fresh; rm "$US_S3/skills/demo/SKILL.md"
us_refuse "a source without SKILL.md" "no SKILL.md in skills/demo of the source"
us_fresh; rm "$US_S3/LICENSE"
us_refuse "a source without its license file" "the source has no LICENSE"
us_fresh; sed -i 's/^  author: Someone$/  author: Someone\n  upstream: elsewhere/' "$US_S3/skills/demo/SKILL.md"
us_refuse "metadata that already has our keys" "the source's metadata already has upstream"
us_fresh; rm -rf "$US_S3/skills"
us_refuse "a source without the skill folder" "the source has no folder skills/demo"

# --- The manifest and the arguments are checked before anything runs ---
us_bad_manifest() {   # <description> <python expression that edits entry e> <expected text>
    cp "$US_R/scripts/upstream-skills.json" "$US_E/manifest.keep"
    python3 -I -B - "$US_R/scripts/upstream-skills.json" "$2" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8")); e = d["skills"][0]
exec(sys.argv[2])
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
    local out rc
    out=$(us_e verify); rc=$?
    cp "$US_E/manifest.keep" "$US_R/scripts/upstream-skills.json"
    assert_eq "manifest: $1 (exit 1)" "1" "$rc"
    assert_contains "manifest: $1 (message)" "$out" "$3"
}
us_bad_manifest "a description that is too short" 'e["description"] = "짧다"' "the description is one line of 50 to 1536 characters (it has 2)"
us_bad_manifest "a description over 1,536 characters" 'e["description"] = "가" * 1537' "the description is one line of 50 to 1536 characters (it has 1537)"
us_bad_manifest "a repo that is not owner/name" 'e["repo"] = "https://example.com/x.git"' "\`repo\` is owner/name on GitHub"
us_bad_manifest "a name that is not a skill name" 'e["name"] = "Demo Skill"' "a skill name is lowercase letters, digits and hyphens"
us_bad_manifest "no list of allowed file types" 'del e["allow_ext"]' "\`allow_ext\` is missing in the manifest"
us_bad_manifest "the same skill twice" 'd["skills"].append(dict(e))' "holds a name twice"
US_OUT=$(us_e check --skill nope 2>&1); assert_eq "arguments: an unknown --skill is exit 1" "1" "$?"
assert_contains "arguments: an unknown --skill is named" "$US_OUT" "no skill named nope in the manifest"
US_OUT=$(us_sync check --source "$US_S1" 2>&1); assert_eq "arguments: --source without --skill is exit 1" "1" "$?"
assert_contains "arguments: --source without --skill says why" "$US_OUT" "--source needs --skill"

# --- Helpers of the script that need no source ---
US_UNIT=$(python3 -I -B - <<'PY' 2>&1
import importlib.util
spec = importlib.util.spec_from_file_location("sync", "scripts/sync_upstream_skills.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad, n = [], 0
def eq(what, got, want):
    global n
    n += 1
    if got != want:
        bad.append("%s: got %r, want %r" % (what, got, want))

eq("plain scalar", m.yaml_scalar("한국어 글은 my-plugins:kor-deslop을 쓴다."), "한국어 글은 my-plugins:kor-deslop을 쓴다.")
eq("quotes inside stay plain", m.yaml_scalar('보기 "unslop" 요청'), '보기 "unslop" 요청')
eq("': ' is quoted", m.yaml_scalar("a: b"), '"a: b"')
eq("' #' is quoted", m.yaml_scalar("a #b"), '"a #b"')
eq("leading quote is quoted and escaped", m.yaml_scalar('"x" y'), '"\\"x\\" y"')
eq("leading bracket is quoted", m.yaml_scalar("[x]"), '"[x]"')
eq("trailing colon is quoted", m.yaml_scalar("x:"), '"x:"')
eq("backslash is escaped", m.yaml_scalar("a: \\b"), '"a: \\\\b"')
for text in ["a: b", '"x" y', "a: \\b", "plain", "it's"]:
    eq("round trip %r" % text, m.scalar(["description: " + m.yaml_scalar(text)]), text)
eq("folded block", m.scalar(["description: >", "  one", "  two"]), "one two")
eq("literal block", m.scalar(["description: |", "  one", "  two"]), "one\ntwo")
eq("single quotes", m.scalar(["description: 'it''s'"]), "it's")

entry = {"name": "x-skill", "repo": "o/r", "description": "d" * 60, "changes": "name replaced"}
out = m.render_frontmatter(entry, ["name: x", "description: old", "license: MIT"], "abc")
eq("no metadata in the source: a block is added",
   out, ["name: x-skill", "description: " + "d" * 60, "license: MIT", "metadata:", "  upstream: https://github.com/o/r",
         "  upstream-commit: abc", "  modified: name replaced"])
out = m.render_frontmatter(entry, ["name: x", "description: >-", "  old", "  text", "metadata:", "    deep: 1"], "abc")
eq("the source's indentation is kept", out[-3:], ["    upstream: https://github.com/o/r", "    upstream-commit: abc", "    modified: name replaced"])
eq("a block description is replaced whole", out[:2], ["name: x-skill", "description: " + "d" * 60])
for fm, why in ((["description: x"], "no name"), (["name: x"], "no description"),
                (["name: x", "description: y", "metadata: flat"], "metadata is not a block")):
    try:
        m.render_frontmatter(entry, fm, "abc"); bad.append("not refused: " + why)
    except m.Refused:
        pass
    n += 1

def section(lines):
    text = lines[:]
    ok = m.add_to_unreleased(text, "- `s`: synced with upstream o/r `abc` (d), 1 file changed", "- `s`: synced with upstream ")
    return ok, text
ok, text = section(["## [Unreleased]", "", "## [1.0.0]"])
eq("empty section", text, ["## [Unreleased]", "", "### Changed", "- `s`: synced with upstream o/r `abc` (d), 1 file changed", "", "## [1.0.0]"])
ok, text = section(["## [Unreleased]", "", "### Added", "- a", "", "## [1.0.0]"])
eq("after Added", text[2:6], ["### Added", "- a", "", "### Changed"])
ok, text = section(["## [Unreleased]", "", "### Fixed", "- f", "", "## [1.0.0]"])
eq("before Fixed", text[2:6], ["### Changed", "- `s`: synced with upstream o/r `abc` (d), 1 file changed", "", "### Fixed"])
ok, text = section(["## [Unreleased]", "", "### Changed", "- other", "- `s`: synced with upstream o/r `old` (d), 9 files changed", "", "### Fixed", "- f", "", "## [1.0.0]"])
eq("an older line of the same skill is replaced",
   text, ["## [Unreleased]", "", "### Changed", "- other", "- `s`: synced with upstream o/r `abc` (d), 1 file changed", "", "### Fixed", "- f", "", "## [1.0.0]"])
ok, text = section(["# Changelog", "", "## [1.0.0]"])
eq("no [Unreleased] section", (ok, text), (False, ["# Changelog", "", "## [1.0.0]"]))
ok, text = section(["## [Unreleased]", "", "### Added", "- a", "", "[Unreleased]: https://x"])
eq("the link line ends the section", text[-3:], ["- `s`: synced with upstream o/r `abc` (d), 1 file changed", "", "[Unreleased]: https://x"])
eq("singular and plural", m.changelog_lines({"name": "s", "repo": "o/r", "commit": "abcdef0123", "date": "d", "added": ["a"], "changed": [], "removed": []})[0],
   "- `s`: synced with upstream o/r `abcdef0` (d), 1 file changed")
eq("report text of a source is one code span", m.quoted("a `b`\n  @c"), "`a 'b' @c`")
eq("report text is cut", len(m.quoted("x" * 2000)), 605)
eq("diff", m.diff_files({"a": "1", "b": "1", "c": "1"}, {"a": "1", "b": "2", "d": "1"}), (["d"], ["b"], ["c"]))
print("ok %d cases" % n if not bad else "\n".join(bad))
PY
)
assert_eq "script helpers: frontmatter values, metadata, CHANGELOG placement, report text" "ok 32 cases" "$US_UNIT"
US_OUT=$(us_sync --help 2>&1); assert_eq "sync script: --help exits 0" "0" "$?"
for us_t in "check" "update" "render" "verify" "--source" "--report" "exit 10"; do
    assert_contains "sync script --help: '$us_t'" "$US_OUT" "$us_t"
done
assert_eq "the tests left no bytecode next to the script" "" "$(find scripts -name '__pycache__' -newer "$US_MAN" 2>/dev/null | head -1)"

# --- The weekly workflow: asks for a review, merges and releases nothing, runs no file of a source ---
assert_file_exists "workflow: $US_WF" "$US_WF"
US_W=$(cat "$US_WF" 2>/dev/null)
printf '%s\n' "$US_W" | grep -qE '^ +- cron: "[0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+ [0-9*/,-]+"' && pass "workflow: runs on a schedule" \
    || fail "workflow: runs on a schedule" "no cron line with five fields"
assert_contains "workflow: can be started by hand" "$US_W" "  workflow_dispatch:"
for us_t in "contents: write" "pull-requests: write" "issues: write"; do
    assert_contains "workflow permissions: $us_t" "$US_W" "  $us_t"
done
assert_eq "workflow: every action is pinned to a full commit id" "" \
    "$(printf '%s\n' "$US_W" | grep -E '^ +-? *uses: ' | grep -vE 'uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}( |$)' | tr '\n' ' ')"
assert_contains "workflow: updates the weekly skills through the sync script with a report" "$US_W" 'python3 scripts/sync_upstream_skills.py update --schedule weekly --report "$RUNNER_TEMP/sync-report.md"'
assert_contains "workflow: verifies the copy" "$US_W" "python3 scripts/sync_upstream_skills.py verify"
assert_contains "workflow: runs this test file" "$US_W" "bash tests/run-all.sh upstream-skills"
assert_contains "workflow: works on its own branch" "$US_W" "branch=sync/upstream-skills"
assert_eq "workflow: the only push is the sync branch" 'git push --force origin "$branch"' \
    "$(printf '%s\n' "$US_W" | grep -E 'git push' | sed 's/^ *//' | tr '\n' '|' | sed 's/|$//')"
assert_contains "workflow: opens a pull request" "$US_W" 'gh pr create --base "$GITHUB_REF_NAME" --head "$branch"'
assert_contains "workflow: leaves an issue when it may not open one" "$US_W" 'gh issue create --title "$title"'
assert_eq "workflow: merges, tags and releases nothing" "" \
    "$(printf '%s\n' "$US_W" | grep -nE 'gh pr merge|gh pr review|--auto|git tag|gh release|plugin\.json|git merge' | tr '\n' ' ')"
assert_eq "workflow: runs no file of a vendored skill" "" \
    "$(printf '%s\n' "$US_W" | grep -nE '(node|bash|sh|python3?|source|\.) +"?\.?/?skills/' | tr '\n' ' ')"
assert_not_contains "workflow: no text of an event goes into a command" "$US_W" 'github.event'
if python3 -I -c "import yaml" 2>/dev/null; then
    US_YAML=$(python3 -I -B - "$US_WF" "$TEST_TMP" <<'PY' 2>&1
import subprocess, sys, yaml
doc = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
steps = doc["jobs"]["sync"]["steps"]
gated = [s.get("name") for s in steps[3:] if s.get("if") != "steps.diff.outputs.changed == 'true'"]
bad = []
for i, step in enumerate(s for s in steps if "run" in s):
    path = "%s/us-step-%d.sh" % (sys.argv[2], i)
    open(path, "w", encoding="utf-8").write(step["run"])
    if subprocess.run(["bash", "-n", path], capture_output=True).returncode:
        bad.append(step.get("name"))
print("steps=%d runs=%d bad=%s ungated=%s triggers=%s" % (len(steps), sum("run" in s for s in steps), bad, gated,
      sorted(doc.get(True, doc.get("on", {})).keys())))
PY
)
    assert_eq "workflow: parses, every command block is valid bash, the steps after the diff wait for a change" \
        "steps=5 runs=4 bad=[] ungated=[] triggers=['schedule', 'workflow_dispatch']" "$US_YAML"
else
    skip "workflow: parses, every command block is valid bash" "PyYAML is not installed"
fi

# --- Documents ---
US_CM=$(cat CLAUDE.md 2>/dev/null)
assert_contains "CLAUDE.md: the vendored skills are never edited by hand" "$US_CM" "ui-deslop, eng-deslop: vendored"
assert_contains "CLAUDE.md: names the sync script" "$US_CM" "scripts/sync_upstream_skills.py"
assert_contains "skills/CLAUDE.md: the rule for vendored skills" "$(cat skills/CLAUDE.md 2>/dev/null)" "scripts/upstream-skills.json"
US_RB=docs/runbooks/sync-upstream-skills.md
assert_file_exists "runbook: $US_RB" "$US_RB"
US_RBT=$(cat "$US_RB" 2>/dev/null)
for us_t in '<a id="english"></a>' '<a id="korean"></a>' "sync_upstream_skills.py check" "sync_upstream_skills.py update" \
            "sync_upstream_skills.py verify" "sync_upstream_skills.py render" ".github/workflows/sync-upstream-skills.yml" "allow_ext"; do
    assert_contains "runbook: '$us_t'" "$US_RBT" "$us_t"
done
assert_file_exists "ADR-008" "docs/decisions/ADR-008-vendored-skills-synced-by-pull-request.md"
US_SETUP=$(cat skills/setup/scripts/setup.sh 2>/dev/null)
assert_contains "setup.sh: reports ffmpeg for ui-deslop" "$US_SETUP" "ffmpeg"
assert_contains "setup.sh: the check run includes the ui-deslop group" "$(printf '%s\n' "$US_SETUP" | sed -n '/^run_checks() {/,/^}/p')" "check_ui"
assert_eq "setup.sh: ffmpeg is optional, never counted as missing" "" "$(printf '%s\n' "$US_SETUP" | grep -n 'miss ffmpeg\|miss "ffmpeg' | tr '\n' ' ')"
US_SEC=$(cat docs/reference/security.md 2>/dev/null)
assert_contains "security.md: names the workflow" "$US_SEC" "sync-upstream-skills.yml"
for us_t in "heydamir/unslop" "blader/humanizer"; do
    assert_eq "README names the source $us_t in both languages" "2" \
        "$( (sed -n '/<a id="english"><\/a>/,/<a id="korean"><\/a>/p' README.md | grep -qF "$us_t" && echo 1; sed -n '/<a id="korean"><\/a>/,$p' README.md | grep -qF "$us_t" && echo 1) | grep -c 1)"
done

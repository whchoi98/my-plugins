#!/bin/bash
# A skill rebuilt from its source by a recipe (sourced by tests/run-all.sh): the `derived` mode of
# scripts/sync_upstream_skills.py and the workflow that runs it every second week. Everything here is offline
# and runs on a made-up source: nothing of a real source is read or run. The real skill built this way,
# aws-diagram-design, is checked in test-aws-diagram-design.sh.
# Needs python3 and git only, so the workflow can run this file on a GitHub runner.

UD_SYNC=scripts/sync_upstream_skills.py
UD_WF=.github/workflows/sync-aws-diagram-design.yml
ud_sync() { python3 -I -B "$UD_SYNC" "$@"; }
ud_tree() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1); }

UD="$TEST_TMP/ud"; UD_R="$UD/root"; UD_S1="$UD/src1"
mkdir -p "$UD_R/scripts/recipe/blocks" "$UD_R/skills/demo-edition/references" "$UD_R/skills/demo-edition/own" \
    "$UD_R/third_party" "$UD_S1/skills/demo/references" "$UD_S1/skills/demo/assets" "$UD_S1/skills/demo/scripts" \
    "$UD_S1/commands" "$UD_S1/.claude-plugin"
cat > "$UD_R/scripts/upstream-skills.json" <<'EOF'
{"schema": 1, "skills": [{"name": "demo-edition", "mode": "derived", "schedule": "biweekly", "repo": "example/demo",
  "ref": "HEAD", "path": "skills/demo", "allow_ext": [".md", ".html", ".py"], "license": "MIT", "license_file": "LICENSE",
  "recipe": "scripts/recipe/recipe.json", "changes": "edition rebuilt by a recipe",
  "description": "데모 판을 만든다. 원본을 받아 정해진 규칙으로 다시 만드는 skill의 테스트용 설명이다. \"demo\" 요청에 사용한다."}]}
EOF
cat > "$UD_R/scripts/recipe/recipe.json" <<'EOF'
{"schema": 1,
 "local": ["references/style.md", "own/*"],
 "replaced": ["references/style.md"],
 "extra": [{"from": "commands/go.md", "to": "commands/go.md"}],
 "steps": [
  {"files": ["SKILL.md", "references/*.md", "extra:commands/*.md"],
   "pairs": [["/demo:", "/my-plugins:"], ["Geist Mono", "Ember Mono"], ["Geist", "Ember"]]},
  {"files": ["SKILL.md"], "ignore_case": true, "pairs": [["#111111", "#232F3E"]]},
  {"files": ["assets/*.html"], "regex": [["^<link [^\\n]*\\n", "<!-- no link -->\\n"]]},
  {"files": ["assets/*.html"], "transform": "svg-text-separators"}],
 "edits": [
  {"id": "gate", "file": "SKILL.md", "from": "## 0. Gate\n", "to": "## 1. Rules\n", "replace_file": "blocks/gate.md"},
  {"id": "icons", "file": "SKILL.md", "before": "- Icon set", "insert": "- Edition icons, named beside Geist.\n"},
  {"id": "band", "file": "SKILL.md", "keep": "Keep `#111111` here"},
  {"id": "guide", "file": "references/guide.md", "find": "Write to `style.md`.", "replace": "Save a profile."}],
 "forbid": [
  {"files": ["SKILL.md", "references/*.md", "extra:commands/*.md"], "tokens": ["Geist", "/demo:"]},
  {"files": ["SKILL.md"], "ignore_case": true, "tokens": ["#111111"]}]}
EOF
printf '## 0. Edition gate\n\nThis block names Geist and #111111 on purpose.\n\n' > "$UD_R/scripts/recipe/blocks/gate.md"
echo "# Edition style" > "$UD_R/skills/demo-edition/references/style.md"
echo "<svg/>" > "$UD_R/skills/demo-edition/own/icon.svg"
echo "stale" > "$UD_R/skills/demo-edition/stale.md"
printf 'MIT License\n\nCopyright (c) 2026 Someone\nCopyright (c) 2026 The edition\n' > "$UD_R/third_party/LICENSE-demo-edition"
cat > "$UD_S1/skills/demo/SKILL.md" <<'EOF'
---
name: demo
description: The source's own description.
license: MIT
metadata:
  version: "1.0"
---

# Demo

## 0. Gate

The old gate, set in Geist.

## 1. Rules

Use Geist for names and `#111111` for ink. Run `/demo:go` first.
- Icon set: [icons.md](references/icons.md).
Keep `#111111` here as a band color.
EOF
printf 'Write to `style.md`. Geist Mono labels at 9px.\n' > "$UD_S1/skills/demo/references/guide.md"
echo "# Source style" > "$UD_S1/skills/demo/references/style.md"
printf '<link href="https://fonts.example/css?x" rel="stylesheet">\n<svg><text x="1">A \xc2\xb7 B</text><text>C\xc2\xb7D <tspan>E \xc2\xb7 F</tspan></text></svg><p>G \xc2\xb7 H</p>\n' \
    > "$UD_S1/skills/demo/assets/t.html"
printf "print('Geist #111111 /demo:')\n" > "$UD_S1/skills/demo/scripts/tool.py"
echo "Run /demo:go with Geist." > "$UD_S1/commands/go.md"
printf 'MIT License\n\nCopyright (c) 2026 Someone\n' > "$UD_S1/LICENSE"
echo '{"name": "demo", "version": "1.2.3"}' > "$UD_S1/.claude-plugin/plugin.json"
UD_C1=1111111111111111111111111111111111111111; UD_C2=2222222222222222222222222222222222222222
ud_r() { ud_sync "$@" --root "$UD_R" 2>&1; }
# ud_field and ud_recipe run a Python expression written in this file, never text of a source
ud_field() { python3 -I -B -c 'import json,sys; e=json.load(open(sys.argv[1]))["skills"][0]; print(eval(sys.argv[2]))' "$UD_R/scripts/upstream-skills.json" "$1"; }

# --- First build ---
UD_OUT=$(ud_r verify); assert_eq "verify: a skill that was never built fails (exit 1)" "1" "$?"
assert_contains "verify: a skill that was never built fails (message)" "$UD_OUT" "demo-edition: not derived yet"
UD_OUT=$(ud_r check --skill demo-edition --source "$UD_S1" --commit "$UD_C1"); assert_eq "check: an update is available (exit 10)" "10" "$?"
assert_contains "check: says the recipe applies" "$UD_OUT" "the recipe applies to the new source"
UD_OUT=$(ud_r update --skill demo-edition --source "$UD_S1" --commit "$UD_C1" --date 2026-01-02 --no-changelog --report "$UD/report1.md")
assert_eq "update (first build): exit 0" "0" "$?"
assert_contains "update (first build): reports the files" "$UD_OUT" "UPDATED demo-edition: example/demo 1111111, 6 added, 0 changed, 0 removed"
UD_D="$UD_R/skills/demo-edition"
assert_eq "update: the files of the source and of the edition, nothing else" \
    "SKILL.md assets/t.html own/icon.svg references/guide.md references/style.md scripts/tool.py" \
    "$(cd "$UD_D" 2>/dev/null && find . -type f | sed 's#^\./##' | sort | tr '\n' ' ' | sed 's/ $//')"
UD_SKILL=$(cat "$UD_D/SKILL.md")
assert_contains "frontmatter: name is ours" "$UD_SKILL" "name: demo-edition"
assert_contains "frontmatter: names the pinned commit" "$UD_SKILL" "  upstream-commit: $UD_C1"
assert_contains "frontmatter: keeps the source's metadata" "$UD_SKILL" '  version: "1.0"'
assert_contains "span edit: the block replaces the section" "$UD_SKILL" "## 0. Edition gate"
assert_not_contains "span edit: the source's section is gone" "$UD_SKILL" "The old gate"
assert_contains "a block is not rewritten by the steps and may hold a forbidden token" "$UD_SKILL" "This block names Geist and #111111 on purpose."
assert_contains "pairs: applied to the source's text, in order" "$UD_SKILL" 'Use Ember for names and `#232F3E` for ink. Run `/my-plugins:go` first.'
assert_contains "insert edit: the line goes in before its anchor, unchanged" "$UD_SKILL" "- Edition icons, named beside Geist.
- Icon set: [icons.md](references/icons.md)."
assert_contains "keep edit: the text is left as the source has it" "$UD_SKILL" 'Keep `#111111` here as a band color.'
assert_eq "find edit and pairs in a reference" 'Save a profile. Ember Mono labels at 9px.' "$(cat "$UD_D/references/guide.md")"
assert_eq "regex step and separator transform: SVG text only, tags untouched" \
    '<!-- no link -->|<svg><text x="1">A, B</text><text>C/D <tspan>E, F</tspan></text></svg><p>G · H</p>' "$(tr '\n' '|' < "$UD_D/assets/t.html" | sed 's/|$//')"
assert_eq "a script of the source is copied byte for byte" "$(sha256sum < "$UD_S1/skills/demo/scripts/tool.py")" "$(sha256sum < "$UD_D/scripts/tool.py")"
assert_eq "a replaced file stays the edition's" "# Edition style" "$(cat "$UD_D/references/style.md")"
assert_eq "an extra file is written outside the skill folder, rewritten" "Run /my-plugins:go with Ember." "$(cat "$UD_R/commands/go.md")"
assert_eq "the edition keeps its own license file" "4" "$(wc -l < "$UD_R/third_party/LICENSE-demo-edition" | tr -d ' ')"
assert_eq "manifest: hashes of what was written, for the rewritten files only" "assets/t.html references/guide.md" "$(ud_field '" ".join(sorted(e["written"]))')"
assert_eq "manifest: the source's files, the replaced one too" "5" "$(ud_field 'len(e["files"])')"
assert_eq "manifest: the span an edit replaced, the extra file, the source's version" "gate commands/go.md 1.2.3" \
    "$(ud_field '" ".join(list(e["spans"]) + list(e["extra_written"]) + [e["upstream_version"]])')"
UD_REP=$(cat "$UD/report1.md")
assert_contains "report: the source's version" "$UD_REP" '- version of the source: `1.2.3`'
assert_contains "report: flags the script" "$UD_REP" "Code that runs on a user's machine changed: scripts/tool.py"
UD_OUT=$(ud_r verify); assert_eq "verify: passes after the build" "0" "$?"
assert_contains "verify: reports the skill" "$UD_OUT" "OK demo-edition: 5 files, example/demo 1111111"
UD_OUT=$(ud_r update --skill demo-edition --source "$UD_S1" --commit "$UD_C1" --no-changelog)
assert_contains "update: the same source and recipe again writes nothing" "$UD_OUT" "OK demo-edition: nothing to update"
UD_OUT=$(ud_r update --schedule weekly --source "$UD_S1" --commit "$UD_C1" --no-changelog 2>&1)
assert_not_contains "--schedule weekly leaves a biweekly skill alone" "$UD_OUT" "demo-edition"
UD_OUT=$(ud_r render --skill demo-edition); assert_eq "render: works on a derived skill" "0" "$?"
ud_r verify >/dev/null; assert_eq "render: verify still passes" "0" "$?"

# --- verify finds a change made by hand (on a copy) ---
UD_T="$UD/tamper"
ud_copy() { rm -rf "$UD_T"; cp -R "$UD_R" "$UD_T"; }
ud_tamper() {   # <description> <expected text>
    local out rc
    out=$(ud_sync verify --root "$UD_T" 2>&1); rc=$?
    assert_eq "verify finds: $1 (exit 1)" "1" "$rc"
    assert_contains "verify finds: $1 (message)" "$out" "$2"
}
ud_copy; echo "by hand" >> "$UD_T/skills/demo-edition/references/guide.md"
ud_tamper "a rewritten file edited by hand" "references/guide.md differs from what \`update\` wrote"
ud_copy; echo "# by hand" >> "$UD_T/skills/demo-edition/scripts/tool.py"
ud_tamper "a script edited by hand" "scripts/tool.py differs from what \`update\` wrote"
ud_copy; echo "by hand" >> "$UD_T/skills/demo-edition/SKILL.md"
ud_tamper "SKILL.md edited by hand" "SKILL.md differs from what \`update\` or \`render\` wrote"
ud_copy; echo "by hand" >> "$UD_T/commands/go.md"
ud_tamper "an extra file edited by hand" "commands/go.md differs from what \`update\` wrote; change the recipe, not the file"
ud_copy; echo "x" > "$UD_T/skills/demo-edition/notes.md"
ud_tamper "a file that is neither the source's nor the edition's" "notes.md is neither a file of the source nor listed in the recipe's \`local\`"
ud_copy; rm "$UD_T/skills/demo-edition/own/icon.svg"
ud_tamper "a file of the edition removed" "no file matches \`own/*\`, which the recipe lists as a file of the edition"
ud_copy; rm "$UD_T/skills/demo-edition/assets/t.html"
ud_tamper "a file of the source removed" "assets/t.html is missing"
ud_copy; sed -i 's/Ember Mono/Ember Code/' "$UD_T/scripts/recipe/recipe.json"
ud_tamper "a recipe changed after the build" "the recipe changed after the last update; run \`update --skill demo-edition --pinned\`"
ud_copy; echo "more" >> "$UD_T/scripts/recipe/blocks/gate.md"
ud_tamper "a block of the recipe changed after the build" "the recipe changed after the last update"
ud_copy; echo "edited by its owner" >> "$UD_T/skills/demo-edition/references/style.md"
ud_sync verify --root "$UD_T" >/dev/null 2>&1; assert_eq "verify: a file of the edition may change by hand" "0" "$?"
UD_OUT=$(ud_sync update --skill demo-edition --source "$UD_S1" --commit "$UD_C1" --no-changelog --root "$UD_T" 2>&1)
assert_contains "update: keeps the edition's own change" "$(cat "$UD_T/skills/demo-edition/references/style.md")" "edited by its owner"

# --- A changed source: notes for what the recipe replaces ---
UD_S2="$UD/src2"; cp -R "$UD_S1" "$UD_S2"
echo "# Source style, second edition" > "$UD_S2/skills/demo/references/style.md"
sed -i 's/The old gate, set in Geist\./A new gate, set in Geist./' "$UD_S2/skills/demo/SKILL.md"
echo "# New reference in Geist" > "$UD_S2/skills/demo/references/new.md"
rm "$UD_S2/skills/demo/assets/t.html"
echo "print('changed')" > "$UD_S2/skills/demo/scripts/tool.py"
echo '{"version": "1.3.0"}' > "$UD_S2/.claude-plugin/plugin.json"
UD_OUT=$(ud_r update --skill demo-edition --source "$UD_S2" --commit "$UD_C2" --date 2026-02-03 --no-changelog --report "$UD/report2.md")
assert_contains "update (changed source): reports the files" "$UD_OUT" "UPDATED demo-edition: example/demo 2222222, 1 added, 3 changed, 1 removed"
UD_REP=$(cat "$UD/report2.md")
assert_contains "report: a file the edition replaces changed in the source" "$UD_REP" "The source changed references/style.md, which the edition replaces with its own file."
assert_contains "report: the text an edit replaces changed in the source" "$UD_REP" "The source changed the text that recipe edit \`gate\` replaces."
assert_contains "report: the compare link" "$UD_REP" "https://github.com/example/demo/compare/$UD_C1...$UD_C2"
assert_eq "update: a new file of the source is rewritten" "# New reference in Ember" "$(cat "$UD_D/references/new.md")"
[ ! -e "$UD_D/assets/t.html" ] && pass "update: a file the source dropped is removed" || fail "update: a file the source dropped is removed" "assets/t.html is still there"
assert_eq "update: the replaced file is still the edition's" "# Edition style" "$(cat "$UD_D/references/style.md")"
ud_r verify >/dev/null; assert_eq "verify: passes after the second build" "0" "$?"

# --- A source or a recipe the recipe does not cover is refused and nothing is written ---
UD_S3="$UD/src3"
ud_fresh() { rm -rf "$UD_S3" "$UD_T"; cp -R "$UD_S2" "$UD_S3"; cp -R "$UD_R" "$UD_T"; }
ud_refuse() {   # <description> <expected text>
    local out rc before
    before=$(ud_tree "$UD_T")
    out=$(ud_sync update --skill demo-edition --source "$UD_S3" --commit "$UD_C2" --no-changelog --root "$UD_T" 2>&1); rc=$?
    assert_eq "refused: $1 (exit 1)" "1" "$rc"
    assert_contains "refused: $1 (message)" "$out" "$2"
    assert_eq "refused: $1 (nothing written)" "$before" "$(ud_tree "$UD_T")"
}
ud_fresh; sed -i 's/^- Icon set/- Icons/' "$UD_S3/skills/demo/SKILL.md"
ud_refuse "an anchor that is gone" "recipe edit \`icons\` no longer applies to SKILL.md: its \`before\` text occurs 0 time(s), not 1"
ud_fresh; echo "- Icon set again" >> "$UD_S3/skills/demo/SKILL.md"
ud_refuse "an anchor that occurs twice" "recipe edit \`icons\` no longer applies to SKILL.md: its \`before\` text occurs 2 time(s), not 1"
ud_fresh; sed -i 's/^## 1\. Rules$/## 1. Laws/' "$UD_S3/skills/demo/SKILL.md"
ud_refuse "the end of a replaced section that is gone" "recipe edit \`gate\` no longer applies to SKILL.md: its \`to\` text occurs 0 time(s), not 1"
ud_fresh; echo 'Keep `#111111` here too.' >> "$UD_S3/skills/demo/SKILL.md"
ud_refuse "a kept text that occurs twice" "recipe edit \`band\` no longer applies to SKILL.md: its \`keep\` text occurs 2 time(s), not 1"
ud_fresh; echo "Old path: run /demo:go here." >> "$UD_S3/skills/demo/references/new.md"; sed -i 's#\["/demo:", "/my-plugins:"\], ##' "$UD_T/scripts/recipe/recipe.json"
ud_refuse "a forbidden token that survives the steps" "\`/demo:\` survives in SKILL.md: \`Use Ember for names and '#232F3E' for ink. Run '/demo:go' first.\`. Add a replacement to the recipe"
ud_fresh; mkdir -p "$UD_S3/skills/demo/own"; echo "x" > "$UD_S3/skills/demo/own/theirs.md"
ud_refuse "the source gains a file the recipe lists as the edition's" "the source now has own/theirs.md, which the recipe lists as a file of the edition"
ud_fresh; rm "$UD_S3/skills/demo/references/style.md"
ud_refuse "the source drops a file the recipe replaces" "the source no longer has references/style.md, which the recipe replaces"
ud_fresh; rm "$UD_S3/commands/go.md"
ud_refuse "the source drops an extra file" "the source has no file commands/go.md, which the recipe takes"
ud_fresh; rm -rf "$UD_T/skills/demo-edition/own"
ud_refuse "a file of the edition is missing before the build" "nothing in skills/demo-edition matches \`own/*\`"
ud_fresh; rm "$UD_T/third_party/LICENSE-demo-edition"
ud_refuse "the edition has no license file" "third_party/LICENSE-demo-edition is missing; a derived skill keeps its own license file"
ud_fresh; sed -i 's/^license: MIT$/license: GPL-3.0-only/' "$UD_S3/skills/demo/SKILL.md"
ud_refuse "the source changed its license" "the source's license is 'GPL-3.0-only', the manifest says 'MIT'"
ud_fresh; ln -s /etc/hostname "$UD_S3/skills/demo/references/link.md"
ud_refuse "a symbolic link in the source" "references/link.md is a symbolic link in the source"
ud_recipe() {   # <python statement that edits recipe r>
    python3 -I -B - "$UD_T/scripts/recipe/recipe.json" "$1" <<'PY'
import json, sys
p = sys.argv[1]; r = json.load(open(p, encoding="utf-8")); exec(sys.argv[2])
json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False)
PY
}
ud_fresh; ud_recipe 'r["edits"].append({"id": "py", "file": "scripts/tool.py", "find": "changed", "replace": "x"})'
ud_refuse "a recipe edit that targets a script" "recipe edit \`py\`: a recipe changes .md and .html files only"
ud_fresh; ud_recipe 'r["edits"].append({"id": "nofile", "file": "references/none.md", "find": "a", "replace": "b"})'
ud_refuse "a recipe edit for a file the source does not have" "recipe edit \`nofile\` names references/none.md, which is not a file taken from the source"
ud_fresh; ud_recipe 'r["edits"].append(dict(r["edits"][1]))'
ud_refuse "two recipe edits with one id" "a recipe edit needs a unique \`id\`"
ud_fresh; ud_recipe 'r["edits"][0]["replace_file"] = "../upstream-skills.json"'
ud_refuse "a block outside the recipe's folder" "which is not a file in its folder"
ud_fresh; ud_recipe 'r["surprise"] = 1'
ud_refuse "an unknown key in the recipe" "the recipe has an unknown key: surprise"
ud_fresh; ud_recipe 'r["extra"][0]["to"] = "../outside.md"'
ud_refuse "an extra file that leaves the repository" "a plain \`to\` path outside skills/"
ud_fresh; ud_recipe 'r["replaced"].append("references/guide.md")'
ud_refuse "a replaced file that is not listed as local" "every \`replaced\` file of the recipe is also listed in \`local\`"
ud_fresh; ud_recipe 'r["steps"].append({"files": ["SKILL.md"], "regex": [["(", "x"]]})'
ud_refuse "a recipe regex that does not compile" "recipe regex '('"
echo "One more line." >> "$UD_S3/skills/demo/references/guide.md"
UD_OUT=$(ud_sync check --skill demo-edition --source "$UD_S3" --commit 3333333333333333333333333333333333333333 --root "$UD_T" 2>&1)
assert_contains "check: lists what changed in the source" "$UD_OUT" "  changed: references/guide.md"
assert_contains "check: says when the recipe does not apply" "$UD_OUT" "RECIPE demo-edition: recipe regex"

# --- Parts of the script that need no source ---
UD_UNIT=$(python3 -I -B - <<'PY' 2>&1
import importlib.util
spec = importlib.util.spec_from_file_location("sync", "scripts/sync_upstream_skills.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad, n = [], 0
def eq(what, got, want):
    global n
    n += 1
    if got != want:
        bad.append("%s: got %r, want %r" % (what, got, want))
dot = "·"
eq("separator: spaced dot", m.no_middle_dot("<text>A %s B</text>" % dot), "<text>A, B</text>")
eq("separator: bare dot", m.no_middle_dot("<text>A%sB</text>" % dot), "<text>A/B</text>")
eq("separator: outside <text> stays", m.no_middle_dot("<p>A %s B</p>" % dot), "<p>A %s B</p>" % dot)
eq("separator: an attribute stays", m.no_middle_dot('<text><tspan data-x="a %s b">c %s d</tspan></text>' % (dot, dot)),
   '<text><tspan data-x="a %s b">c, d</tspan></text>' % dot)
recipe = {"edits": [{"id": "a", "file": "f.md", "after": "first\n", "insert": "TWO one\n"}],
          "steps": [{"files": ["*.md"], "pairs": [["one", "1"]]}], "forbid": [{"files": ["*.md"], "tokens": ["one"]}]}
eq("an inserted text is not rewritten and not forbidden", m.derive_text("s", "f.md", "first\nthree one\n", recipe), ("first\nTWO one\nthree 1\n", {}))
eq("a file the steps do not name is left alone", m.derive_text("s", "g.html", "one\n", recipe), ("one\n", {}))
try:
    m.derive_text("s", "f.md", "one\x00\n", recipe); bad.append("a NUL character in the source is refused: no error")
except m.Refused:
    n += 1
eq("patterns: * crosses folders", m.matches("assets/aws-icons/a/b.svg", ["assets/aws-icons/*"]), True)
eq("patterns: no match", m.matches("assets/other.svg", ["assets/aws-icons/*"]), False)
print("%d checks, %d wrong%s" % (n, len(bad), "".join("\n  " + b for b in bad)))
PY
)
assert_eq "script parts without a source" "9 checks, 0 wrong" "$UD_UNIT"

# --- The workflow that runs every second week ---
assert_file_exists "workflow: $UD_WF" "$UD_WF"
UD_W=$(cat "$UD_WF" 2>/dev/null)
assert_contains "workflow: one weekly cron line" "$UD_W" '    - cron: "47 21 * * 0"'
assert_contains "workflow: lets every second week through, counted from 1970-01-01" "$UD_W" 'week=$(( $(date -u +%s) / 604800 ))'
assert_contains "workflow: a run started by hand always goes on" "$UD_W" '[ "$GITHUB_EVENT_NAME" = "workflow_dispatch" ] || [ $(( week % 2 )) -eq 0 ]'
assert_contains "workflow: can be started by hand" "$UD_W" "  workflow_dispatch:"
assert_contains "workflow: rebuilds the biweekly skills through the sync script" "$UD_W" "python3 scripts/sync_upstream_skills.py update --schedule biweekly"
assert_contains "workflow: verifies the result" "$UD_W" "python3 scripts/sync_upstream_skills.py verify"
assert_contains "workflow: runs the offline tests of the sync script" "$UD_W" "bash tests/run-all.sh upstream"
assert_contains "workflow: runs the static tests of the skill" "$UD_W" "bash tests/run-all.sh 'aws-diagram-design\$'"
assert_not_contains "workflow: does not run the tests that run the source's scripts" "$UD_W" "aws-diagram-design-run"
assert_contains "workflow: works on its own branch" "$UD_W" "branch=sync/aws-diagram-design"
assert_eq "workflow: the only push is the sync branch" 'git push --force origin "$branch"' \
    "$(printf '%s\n' "$UD_W" | grep -E 'git push' | sed 's/^ *//' | sort -u)"
assert_contains "workflow: opens a pull request" "$UD_W" 'gh pr create --base "$GITHUB_REF_NAME" --head "$branch"'
assert_contains "workflow: leaves an issue when the recipe does not apply" "$UD_W" 'title="aws-diagram-design: the sync recipe needs a change"'
assert_contains "workflow: text of the source cannot close the code block or notify anyone" "$UD_W" "tr '\`@' \"'.\""
assert_eq "workflow: every action is pinned to a full commit id" "" \
    "$(printf '%s\n' "$UD_W" | grep -E '^ +- uses: |^ +uses: ' | grep -vE '@[0-9a-f]{40}( |$)' || true)"
assert_eq "workflow: merges, tags and releases nothing" "" \
    "$(printf '%s\n' "$UD_W" | grep -nE 'gh pr merge|git merge|git tag|gh release|plugin update|--auto' || true)"
assert_eq "workflow: runs no file of the skill it rebuilds" "" \
    "$(printf '%s\n' "$UD_W" | grep -nE '(python3?|node|bash|sh) +[^ ]*skills/' || true)"
assert_not_contains "workflow: no text of an event goes into a command" "$UD_W" 'github.event.'
assert_contains "weekly workflow: leaves the biweekly skills alone" "$(cat .github/workflows/sync-upstream-skills.yml)" "update --schedule weekly"
if python3 -I -c 'import yaml' 2>/dev/null; then
    UD_YAML=$(python3 -I -B - "$UD_WF" "$TEST_TMP" <<'PY' 2>&1
import subprocess, sys, yaml
wf = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
steps = wf["jobs"]["sync"]["steps"]
bad, ungated = [], []
for i, step in enumerate(steps):
    if "run" in step:
        path = "%s/ud-step-%d.sh" % (sys.argv[2], i)
        open(path, "w", encoding="utf-8").write(step["run"])
        if subprocess.run(["bash", "-n", path], capture_output=True).returncode != 0:
            bad.append(step.get("name", i))
    if i > 0 and "steps.due.outputs.run == 'true'" not in str(step.get("if", "")):
        ungated.append(step.get("name", step.get("uses", i)))
print("steps=%d bad=%s ungated=%s triggers=%s" % (len(steps), bad, ungated, sorted(wf[True] if True in wf else wf["on"])))
PY
)
    assert_eq "workflow: parses, every command block is valid bash, every step after the first waits for its week" \
        "steps=6 bad=[] ungated=[] triggers=['schedule', 'workflow_dispatch']" "$UD_YAML"
else
    skip "workflow: parses, every command block is valid bash" "PyYAML is not installed"
fi

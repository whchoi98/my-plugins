#!/bin/bash
# Tests for .claude/hooks/*.sh (sourced by tests/run-all.sh)

# --- Existence and permissions ---
for hook in check-doc-sync secret-scan session-context notify; do
    assert_file_exists "$hook.sh exists" ".claude/hooks/$hook.sh"
    assert_file_executable "$hook.sh is executable" ".claude/hooks/$hook.sh"
    assert_bash_syntax "$hook.sh valid bash" ".claude/hooks/$hook.sh"
done

# --- settings.json hook registration ---
assert_file_exists "settings.json exists" ".claude/settings.json"
assert_json_valid "settings.json is valid JSON" ".claude/settings.json"

SETTINGS=$(cat .claude/settings.json)
assert_contains "SessionStart hook registered" "$SETTINGS" "session-context.sh"
assert_contains "PreToolUse hook registered" "$SETTINGS" "secret-scan.sh"
assert_contains "PostToolUse hook registered" "$SETTINGS" "check-doc-sync.sh"
assert_contains "Notification hook registered" "$SETTINGS" "notify.sh"
assert_eq "PostToolUse matcher is Write|Edit" "Write|Edit" "$(jq -r '.hooks.PostToolUse[0].matcher' .claude/settings.json)"

# Hooks read event JSON on stdin; the template's fake $TOOL_INPUT_PATH/$EVENT variables must not return
assert_not_contains "settings: no fake env-var arguments" "$SETTINGS" "TOOL_INPUT_PATH"

# The PreToolUse command must propagate exit 2, so it must not swallow the status
PRE_CMD=$(jq -r '.hooks.PreToolUse[0].hooks[0].command' .claude/settings.json)
assert_not_contains "PreToolUse command keeps exit status" "$PRE_CMD" "|| true"
assert_eq "PreToolUse matcher is Bash" "Bash" "$(jq -r '.hooks.PreToolUse[0].matcher' .claude/settings.json)"

DENY=$(jq -r '.permissions.deny[]' .claude/settings.json)
assert_contains "deny: rm -rf" "$DENY" "Bash(rm -rf:*)"
assert_contains "deny: force push" "$DENY" "Bash(git push --force:*)"
assert_contains "deny: read .env" "$DENY" "Read(./.env)"

# --- check-doc-sync behavior ---
OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "" 2>&1 || true)
assert_eq "check-doc-sync: empty path produces no output" "" "$OUTPUT"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "README.md" 2>&1 || true)
assert_eq "check-doc-sync: non-source file is quiet" "" "$OUTPUT"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "skills/aws-blog-skills/references/style.md" 2>&1 || true)
assert_not_contains "check-doc-sync: skills/CLAUDE.md is found for nested files" "$OUTPUT" "CLAUDE.md is missing"
assert_contains "check-doc-sync: style.md edit asks to mirror lint_prose.py" "$OUTPUT" "scripts/lint_prose.py"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "skills/aws-blog-skills/references/humanize-checklist.md" 2>&1 || true)
assert_contains "check-doc-sync: humanize-checklist.md edit asks to mirror lint_prose.py" "$OUTPUT" "Writing rules changed"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "skills/aws-blog-skills/assets/templates/blog-template.md" 2>&1 || true)
assert_contains "check-doc-sync: template edit reminds about the author bio" "$OUTPUT" "author bio identical"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "skills/aws-blog-skills/scripts/package_blog.sh" 2>&1 || true)
assert_contains "check-doc-sync: script edit asks for script tests" "$OUTPUT" "tests/run-all.sh scripts"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "tests/hooks/test-hooks.sh" 2>&1 || true)
assert_not_contains "check-doc-sync: tests/CLAUDE.md is found" "$OUTPUT" "CLAUDE.md is missing"

OUTPUT=$(bash .claude/hooks/check-doc-sync.sh "skills/aws-blog-skills/SKILL.md" 2>&1 || true)
assert_contains "check-doc-sync: SKILL.md edit reminds about frontmatter" "$OUTPUT" "frontmatter name"
assert_contains "check-doc-sync: SKILL.md edit reminds about CLAUDE_SKILL_DIR" "$OUTPUT" '${CLAUDE_SKILL_DIR}'

OUTPUT=$(echo "{\"tool_input\":{\"file_path\":\"$PROJECT_ROOT/.claude-plugin/plugin.json\"}}" \
    | bash .claude/hooks/check-doc-sync.sh 2>&1 || true)
assert_eq "check-doc-sync: hook mode emits PostToolUse JSON" "PostToolUse" \
    "$(echo "$OUTPUT" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null || true)"
assert_contains "check-doc-sync: manifest edit asks for validation" \
    "$(echo "$OUTPUT" | jq -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null || true)" "claude plugin validate"

# Version-bump reminder depends on git state, so exercise it in a throwaway repo
SYNC_REPO="$TEST_TMP/sync-repo"
mkdir -p "$SYNC_REPO/skills/demo" "$SYNC_REPO/.claude-plugin" "$SYNC_REPO/docs/decisions"
echo '{"name":"demo","version":"1.0.0"}' > "$SYNC_REPO/.claude-plugin/plugin.json"
echo "# Skills" > "$SYNC_REPO/skills/CLAUDE.md"
echo "x" > "$SYNC_REPO/skills/demo/SKILL.md"
echo "# ADR" > "$SYNC_REPO/docs/decisions/ADR-001-x.md"
git -C "$SYNC_REPO" init -q
git -C "$SYNC_REPO" add -A
git -C "$SYNC_REPO" -c user.name=t -c user.email=t@t commit -qm init --no-verify
OUTPUT=$(CLAUDE_PROJECT_DIR="$SYNC_REPO" bash .claude/hooks/check-doc-sync.sh "skills/demo/SKILL.md" 2>&1 || true)
assert_contains "check-doc-sync: skill edit without version bump asks for one" "$OUTPUT" "bump .claude-plugin/plugin.json"
assert_not_contains "check-doc-sync: ADR present means no ADR warning" "$OUTPUT" "No ADRs found"
echo '{"name":"demo","version":"1.0.1"}' > "$SYNC_REPO/.claude-plugin/plugin.json"
OUTPUT=$(CLAUDE_PROJECT_DIR="$SYNC_REPO" bash .claude/hooks/check-doc-sync.sh "skills/demo/SKILL.md" 2>&1 || true)
assert_not_contains "check-doc-sync: bumped version silences the reminder" "$OUTPUT" "bump .claude-plugin/plugin.json"
rm -f "$SYNC_REPO/skills/CLAUDE.md"
OUTPUT=$(CLAUDE_PROJECT_DIR="$SYNC_REPO" bash .claude/hooks/check-doc-sync.sh "skills/demo/SKILL.md" 2>&1 || true)
assert_contains "check-doc-sync: missing module doc is reported" "$OUTPUT" "skills/CLAUDE.md is missing"

# Hook mode reminds once per session: a message already sent under the same session_id is dropped.
# State lives in $TMPDIR, so each call points TMPDIR at a scratch folder.
HK_SYNC_TMP="$TEST_TMP/doc-sync-state"
mkdir -p "$HK_SYNC_TMP"
hk_sync_hook() {  # $1 = session_id JSON fragment ('' omits it), $2 = repo-relative path; prints additionalContext
    printf '{%s"tool_input":{"file_path":"%s/%s"}}' "$1" "$PROJECT_ROOT" "$2" \
        | TMPDIR="$HK_SYNC_TMP" bash .claude/hooks/check-doc-sync.sh 2>/dev/null \
        | jq -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null || true
}
assert_contains "check-doc-sync: first reminder in a session is sent" \
    "$(hk_sync_hook '"session_id":"hk-s1",' .claude-plugin/plugin.json)" "claude plugin validate"
assert_eq "check-doc-sync: same reminder in the same session is not repeated" "" \
    "$(hk_sync_hook '"session_id":"hk-s1",' .claude-plugin/plugin.json)"
assert_eq "check-doc-sync: same message from another file is not repeated" "" \
    "$(hk_sync_hook '"session_id":"hk-s1",' .mcp.json)"
assert_contains "check-doc-sync: a new message in the same session is still sent" \
    "$(hk_sync_hook '"session_id":"hk-s1",' tests/hooks/test-hooks.sh)" "Harness changed"
assert_contains "check-doc-sync: another session gets the reminder again" \
    "$(hk_sync_hook '"session_id":"hk-s2",' .claude-plugin/plugin.json)" "claude plugin validate"
hk_sync_hook '' .claude-plugin/plugin.json >/dev/null
assert_contains "check-doc-sync: no session_id means no dedupe" \
    "$(hk_sync_hook '' .claude-plugin/plugin.json)" "claude plugin validate"
hk_sync_hook '"session_id":"../../hk-escape",' .claude-plugin/plugin.json >/dev/null
assert_eq "check-doc-sync: session_id with path characters still dedupes" "" \
    "$(hk_sync_hook '"session_id":"../../hk-escape",' .claude-plugin/plugin.json)"
assert_eq "check-doc-sync: state file stays inside TMPDIR" "" \
    "$(find "$TEST_TMP" -name '*hk-escape*' -not -path "$HK_SYNC_TMP/*" 2>/dev/null)"
OUTPUT=$(bash .claude/hooks/check-doc-sync.sh ".claude-plugin/plugin.json" 2>&1 || true)
assert_contains "check-doc-sync: manual runs are never deduped" "$OUTPUT" "claude plugin validate"

# --- secret-scan behavior (PreToolUse mode, isolated git repo) ---
OUTPUT=$(echo '{"tool_input":{"command":"ls -la"}}' | bash .claude/hooks/secret-scan.sh 2>&1; echo "exit=$?")
assert_eq "secret-scan: non-commit command passes silently" "exit=0" "$OUTPUT"

SCAN_REPO="$TEST_TMP/scan-repo"
mkdir -p "$SCAN_REPO"
git -C "$SCAN_REPO" init -q
echo '# 안내' > "$SCAN_REPO/clean.md"
git -C "$SCAN_REPO" add clean.md
STATUS=$(echo '{"tool_input":{"command":"git commit -m test"}}' \
    | CLAUDE_PROJECT_DIR="$SCAN_REPO" bash .claude/hooks/secret-scan.sh >/dev/null 2>&1; echo $?)
assert_eq "secret-scan: clean staged files allow commit" "0" "$STATUS"

AWS_KEY_PREFIX="AKIA"
AWS_KEY_BODY="IOSFODNN7EXAMPLE"
echo "키: ${AWS_KEY_PREFIX}${AWS_KEY_BODY}" > "$SCAN_REPO/leak.md"
STATUS=$(echo '{"tool_input":{"command":"git add -A && git commit -m test"}}' \
    | CLAUDE_PROJECT_DIR="$SCAN_REPO" bash .claude/hooks/secret-scan.sh >/dev/null 2>&1; echo $?)
assert_eq "secret-scan: unstaged secret in Markdown blocks 'git add && commit' with exit 2" "2" "$STATUS"

git -C "$SCAN_REPO" add leak.md
STATUS=$(bash -c "cd '$SCAN_REPO' && bash '$PROJECT_ROOT/.claude/hooks/secret-scan.sh' --staged" >/dev/null 2>&1; echo $?)
assert_eq "secret-scan: --staged (git pre-commit) blocks with exit 1" "1" "$STATUS"

# --- session-context ---
OUTPUT=$(bash .claude/hooks/session-context.sh 2>&1 || true)
HK_NAME=$(jq -r .name .claude-plugin/plugin.json)
HK_MKT=$(jq -r .name .claude-plugin/marketplace.json)
assert_contains "session-context: shows project header" "$OUTPUT" "Project Context"
assert_contains "session-context: shows plugin name and version" "$OUTPUT" \
    "Plugin: $HK_NAME $(jq -r .version .claude-plugin/plugin.json)"
assert_contains "session-context: shows install id" "$OUTPUT" "${HK_NAME}@${HK_MKT}"
assert_not_contains "session-context: no old install id" "$OUTPUT" "aws-blog-skills@aws-blog-skills"
# The skill inventory line format is the hook's choice; whatever it counts must match the tree
if printf '%s\n' "$OUTPUT" | grep -q '^Skill aws-blog-skills: [0-9]* reference files'; then
    assert_contains "session-context: aws-blog-skills reference count matches" "$OUTPUT" \
        "Skill aws-blog-skills: $(find skills/aws-blog-skills/references -name '*.md' | wc -l | tr -d ' ') reference files"
fi
if printf '%s\n' "$OUTPUT" | grep -qiE '^Skills?: [0-9]+'; then
    assert_eq "session-context: skill count matches skills/*/SKILL.md" \
        "$(find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')" \
        "$(printf '%s\n' "$OUTPUT" | grep -m1 -oiP '^Skills?: \K[0-9]+')"
fi

# --- AI co-author exclusion (contributors) ---
assert_eq "settings: commit attribution disabled" "" "$(jq -r '.attribution.commit' .claude/settings.json)"
assert_eq "settings: PR attribution disabled" "" "$(jq -r '.attribution.pr' .claude/settings.json)"

MSG_REPO="$TEST_TMP/msg-repo"
mkdir -p "$MSG_REPO/scripts"
git -C "$MSG_REPO" init -q
cp scripts/install-hooks.sh "$MSG_REPO/scripts/"
bash "$MSG_REPO/scripts/install-hooks.sh" >/dev/null
assert_file_executable "install-hooks: pre-commit installed" "$MSG_REPO/.git/hooks/pre-commit"
assert_file_executable "install-hooks: commit-msg installed" "$MSG_REPO/.git/hooks/commit-msg"
printf 'feat: sample\n\nBody line.\n\nCo-Authored-By: Claude <noreply@anthropic.com>\nco-authored-by: Bot <b@x>\n  CO-AUTHORED-BY: Other <o@x>\n\n' \
    > "$MSG_REPO/msg.txt"
bash "$MSG_REPO/.git/hooks/commit-msg" "$MSG_REPO/msg.txt"
MSG_OUT=$(cat "$MSG_REPO/msg.txt")
assert_not_contains "commit-msg: removes Co-Authored-By in any case" "$(echo "$MSG_OUT" | tr '[:upper:]' '[:lower:]')" "co-authored-by"
assert_contains "commit-msg: keeps subject and body" "$MSG_OUT" "Body line."
assert_eq "commit-msg: no trailing blank lines" "Body line." "$(tail -n 1 "$MSG_REPO/msg.txt")"

# --- notify ---
OUTPUT=$(CLAUDE_NOTIFY_WEBHOOK="" bash .claude/hooks/notify.sh "test" "msg" 2>&1 || true)
assert_eq "notify.sh: no webhook URL produces no output" "" "$OUTPUT"

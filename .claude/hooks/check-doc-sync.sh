#!/bin/bash
# Detect documentation sync needs after file changes (CLAUDE.md "Change Sync Rules").
# Triggered by PostToolUse (Write|Edit). Claude Code passes the event as JSON on
# stdin; a path argument is accepted for manual runs and tests.
# Walks parent directories (module root included) to find CLAUDE.md before warning.
# Hook mode sends each message once per session: messages already sent under the event's
# session_id are listed in ${TMPDIR:-/tmp}/claude-doc-sync-<session_id>.seen and dropped.
# Manual runs and events without a session_id always print every message.

SESSION_ID=""
if [ "$#" -ge 1 ]; then
    FILE_PATH="$1"
    FROM_HOOK=false
else
    INPUT=$(cat)
    FILE_PATH=$(jq -r '.tool_input.file_path // empty' <<<"$INPUT" 2>/dev/null)
    # Keep only [A-Za-z0-9_-] so the id cannot point the state file outside TMPDIR
    SESSION_ID=$(jq -r '.session_id // empty' <<<"$INPUT" 2>/dev/null | tr -cd 'A-Za-z0-9_-')
    FROM_HOOK=true
fi
[ -z "$FILE_PATH" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0
FILE_PATH="${FILE_PATH#"$PROJECT_DIR"/}"
FILE_PATH="${FILE_PATH#./}"

# Top-level directories with a module doc. skills/ is the shipped plugin content; its module
# doc is skills/CLAUDE.md (never inside skills/<name>/, which ships as the skill).
SOURCE_ROOTS="skills tests"

MESSAGES=()

IS_SOURCE=false
for ROOT in $SOURCE_ROOTS; do
    if [[ "$FILE_PATH" == ${ROOT}/* ]]; then
        IS_SOURCE=true
        DIR=$(dirname "$FILE_PATH")
        FOUND_CLAUDE=false
        CHECK_DIR="$DIR"
        while [ "$CHECK_DIR" != "." ] && [ -n "$CHECK_DIR" ]; do
            if [ -f "$CHECK_DIR/CLAUDE.md" ]; then
                FOUND_CLAUDE=true
                break
            fi
            [ "$CHECK_DIR" = "$ROOT" ] && break
            CHECK_DIR=$(dirname "$CHECK_DIR")
        done
        if ! $FOUND_CLAUDE; then
            MESSAGES+=("[doc-sync] $ROOT/CLAUDE.md is missing. Create module documentation.")
        fi
        break
    fi
done
[[ "$FILE_PATH" == commands/* ]] && IS_SOURCE=true

# Alert if no ADRs exist when source or architecture files change
if $IS_SOURCE || [[ "$FILE_PATH" == docs/architecture.md ]]; then
    ADR_COUNT=$(find docs/decisions -name 'ADR-*.md' 2>/dev/null | wc -l)
    if [ "$ADR_COUNT" -eq 0 ]; then
        MESSAGES+=("[doc-sync] No ADRs found. Record architectural decisions with /add-adr.")
    fi
fi

# --- Shipped content: any skill or command change is a release ---------------------------------
# Installed copies only update when the version changes
if [[ "$FILE_PATH" == skills/*/* || "$FILE_PATH" == commands/* ]]; then
    if git diff --quiet HEAD -- .claude-plugin/plugin.json 2>/dev/null; then
        MESSAGES+=("[doc-sync] Shipped skill or command changed: bump .claude-plugin/plugin.json version, the README badge, and add a CHANGELOG.md [Unreleased] entry in both languages (docs/runbooks/release-plugin.md).")
    fi
fi

SKILL_NAME=""
[[ "$FILE_PATH" == skills/*/* ]] && { SKILL_NAME="${FILE_PATH#skills/}"; SKILL_NAME="${SKILL_NAME%%/*}"; }

# New skill: not yet in the skills/CLAUDE.md table
if [[ "$FILE_PATH" == skills/*/SKILL.md ]] && ! grep -qF "\`$SKILL_NAME/\`" skills/CLAUDE.md 2>/dev/null; then
    MESSAGES+=("[doc-sync] New skill '$SKILL_NAME': add it to skills/CLAUDE.md (table and cross-skill links), the README skill tables (both languages) and docs/reference/agent-llm.md.")
fi

if [[ "$FILE_PATH" == skills/*/SKILL.md ]]; then
    MESSAGES+=("[doc-sync] SKILL.md changed: keep the frontmatter name equal to the directory name, call bundled files through \${CLAUDE_SKILL_DIR} (or the SKILL_DIR the skill defines), call other skills as my-plugins:<skill>, keep sibling paths relative (../<skill>/...), and re-check trigger phrases against README.md Usage.")
fi

# --- aws-blog-skills ---------------------------------------------------------------------------
if [[ "$FILE_PATH" == skills/aws-blog-skills/references/style.md || "$FILE_PATH" == skills/aws-blog-skills/references/humanize-checklist.md ]]; then
    MESSAGES+=("[doc-sync] Writing rules changed: mirror added or removed terms in scripts/lint_prose.py (HARD, HARD_RE, COUNT) and mark confirmed rules with (YYYY-MM-DD 확정).")
fi

if [[ "$FILE_PATH" == skills/aws-blog-skills/references/structure.md || "$FILE_PATH" == skills/aws-blog-skills/assets/templates/blog-template.md ]]; then
    MESSAGES+=("[doc-sync] Draft skeleton changed: keep the author bio identical in references/structure.md and assets/templates/blog-template.md, and BIO_HEAD in scripts/check_structure.py.")
fi

if [[ "$FILE_PATH" == skills/aws-blog-skills/SKILL.md ]]; then
    MESSAGES+=("[doc-sync] aws-blog-skills SKILL.md: list every references/*.md in the table, keep the step 0 source-material rule and the step 4 .aws-diagram-assets pointer line; run 'bash tests/run-all.sh aws-blog-skills'.")
fi

if [[ "$FILE_PATH" == skills/aws-blog-skills/scripts/* ]]; then
    MESSAGES+=("[doc-sync] aws-blog-skills script changed: run 'bash tests/run-all.sh scripts'; if arguments or exit codes changed, update its SKILL.md, README.md in both languages and tests/structure/test-aws-blog-skills-scripts.sh.")
fi

if [[ "$FILE_PATH" == skills/aws-blog-skills/scripts/diagram_lib.py ]]; then
    MESSAGES+=("[doc-sync] diagram_lib.py changed: if the find_assets() order changed, update CLAUDE.md (Diagram assets), docs/architecture.md and README.md Configuration in both languages; run 'bash tests/run-all.sh integration'.")
fi

# --- Other skills ------------------------------------------------------------------------------
if [[ "$FILE_PATH" == skills/*/scripts/* || "$FILE_PATH" == skills/*/tools/* || "$FILE_PATH" == skills/*/lib/* ]] \
    && [[ "$SKILL_NAME" != aws-blog-skills && "$SKILL_NAME" != setup ]]; then
    MESSAGES+=("[doc-sync] Bundled script changed in $SKILL_NAME: run 'bash tests/run-all.sh structure'; if arguments changed, update the SKILL.md that calls it. A new external tool or font goes into skills/setup/scripts/setup.sh, skills/setup/SKILL.md and README.md (both languages).")
fi

if [[ "$FILE_PATH" == skills/kor-deslop/references/* || "$FILE_PATH" == skills/kor-deslop/SKILL.md ]]; then
    MESSAGES+=("[doc-sync] kor-deslop rules changed: keep one pattern count in SKILL.md, references/patterns.md, README.md (both languages), skills/CLAUDE.md and CLAUDE.md; never renumber existing IDs; run 'bash tests/run-all.sh kor-deslop'.")
fi

if [[ "$FILE_PATH" == skills/aws-ppt-skills/* || "$FILE_PATH" == skills/consulting-ppt-white-ppt/* || "$FILE_PATH" == skills/pptx-template-fill/* ]]; then
    MESSAGES+=("[doc-sync] Deck skill changed: slides keep the template's background, logo, footer and page numbers; no '·' or '—' in slide copy; node build steps keep NODE_PATH=\"\$(npm root -g)\".")
fi

if [[ "$FILE_PATH" == skills/aws-ppt-skills/scripts/install_fonts.sh ]]; then
    MESSAGES+=("[doc-sync] install_fonts.sh changed: skills/setup/scripts/setup.sh runs it by this path for NanumSquareOTF and D2Coding; keep the path and the 'NanumSquareOTF Bold' alias it checks.")
fi

if [[ "$FILE_PATH" == skills/aws-diagram-design/assets/* ]]; then
    MESSAGES+=("[doc-sync] aws-diagram-design assets changed: aws-blog-skills/scripts/diagram_lib.py reads ../aws-diagram-design/assets (aws-icons/) and setup.sh copies assets/fonts/ttf; renaming either breaks them.")
fi

if [[ "$FILE_PATH" == skills/aws-diagram-design/references/export.md || "$FILE_PATH" == skills/aws-diagram-design/references/import-*.md \
    || "$FILE_PATH" == skills/aws-diagram-design/references/output-spec.md || "$FILE_PATH" == commands/* ]]; then
    MESSAGES+=("[doc-sync] Export/import flow changed: commands/*.md follow skills/aws-diagram-design/references/; keep the argument-hint in step with the reference, and the command table in docs/diagrams/guide-claude-code.md.")
fi

if [[ "$FILE_PATH" == skills/setup/* ]]; then
    MESSAGES+=("[doc-sync] setup changed: keep skills/setup/scripts/setup.sh, skills/setup/SKILL.md, README.md (both languages) and docs/runbooks/setup-dependencies.md in step; never sudo without --sudo, and then only sudo -n; run 'bash tests/run-all.sh integration' (check mode only, never install).")
fi

if [[ "$FILE_PATH" == skills/CLAUDE.md ]]; then
    MESSAGES+=("[doc-sync] skills/CLAUDE.md changed: keep its skill table and cross-skill links in step with the README tables and docs/architecture.md.")
fi

# --- Manifests and harness ---------------------------------------------------------------------
if [[ "$FILE_PATH" == .claude-plugin/*.json || "$FILE_PATH" == .mcp.json ]]; then
    MESSAGES+=("[doc-sync] Plugin manifest changed: run 'claude plugin validate .' and 'bash tests/run-all.sh structure'.")
fi

if [[ "$FILE_PATH" == .claude/* || "$FILE_PATH" == tests/* || "$FILE_PATH" == scripts/* ]]; then
    MESSAGES+=("[doc-sync] Harness changed: update tests/CLAUDE.md and docs/reference/security.md if behavior changed; run 'bash tests/run-all.sh'.")
fi

[ "${#MESSAGES[@]}" -eq 0 ] && exit 0

# Once per session: drop messages already sent, record the rest
if $FROM_HOOK && [ -n "$SESSION_ID" ]; then
    SEEN_FILE="${TMPDIR:-/tmp}/claude-doc-sync-$SESSION_ID.seen"
    UNSENT=()
    for MSG in "${MESSAGES[@]}"; do
        grep -qxF -- "$MSG" "$SEEN_FILE" 2>/dev/null && continue
        UNSENT+=("$MSG")
        printf '%s\n' "$MSG" >> "$SEEN_FILE" 2>/dev/null
    done
    MESSAGES=("${UNSENT[@]}")
    [ "${#MESSAGES[@]}" -eq 0 ] && exit 0
fi

if $FROM_HOOK; then
    # additionalContext reaches Claude without blocking the completed tool call
    printf '%s\n' "${MESSAGES[@]}" | jq -Rs '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: .}}'
else
    printf '%s\n' "${MESSAGES[@]}"
fi
exit 0

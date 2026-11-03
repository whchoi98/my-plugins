#!/bin/bash
# Load project context at Claude Code session start.
# SessionStart stdout is added to Claude's context, so keep it short and factual.

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0

echo "=== Project Context ==="

NAME=$(jq -r '.name // empty' .claude-plugin/plugin.json 2>/dev/null)
VERSION=$(jq -r '.version // empty' .claude-plugin/plugin.json 2>/dev/null)
MARKET=$(jq -r '.name // empty' .claude-plugin/marketplace.json 2>/dev/null)
echo "Plugin: ${NAME:-$(basename "$(pwd)")} ${VERSION} (Claude Code plugin, install id ${NAME}@${MARKET}, skills called as /${NAME}:<skill>)"

# Skill inventory: one line per shipped skill
SKILLS=()
for SKILL_MD in skills/*/SKILL.md; do
    [ -f "$SKILL_MD" ] && SKILLS+=("$(basename "$(dirname "$SKILL_MD")")")
done
COMMANDS=$(find commands -maxdepth 1 -name '*.md' 2>/dev/null | sed 's#.*/##; s#\.md$##' | sort | tr '\n' ' ')
echo "Skills: ${#SKILLS[@]} (${SKILLS[*]}); commands: ${COMMANDS% }"
for SKILL in "${SKILLS[@]}"; do
    D="skills/$SKILL"
    REFS=$(find "$D/references" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    SCRIPTS=$(find "$D/scripts" "$D/tools" "$D/lib" -type f \( -name '*.py' -o -name '*.sh' -o -name '*.js' \) \
        -not -path '*/__pycache__/*' 2>/dev/null | wc -l | tr -d ' ')
    echo "Skill $SKILL: $REFS reference files, $SCRIPTS scripts"
done
echo "Conventions: bundled files via \${CLAUDE_SKILL_DIR} or the skill's SKILL_DIR; cross-skill calls my-plugins:<skill>; user deps: bash skills/setup/scripts/setup.sh"

# Version drift between the manifest and the latest released CHANGELOG entry
RELEASED=$(grep -m1 -oP '^## \[\K[0-9]+\.[0-9]+\.[0-9]+' CHANGELOG.md 2>/dev/null)
if [ -n "$VERSION" ] && [ -n "$RELEASED" ] && [ "$VERSION" != "$RELEASED" ]; then
    echo "Note: plugin.json is $VERSION but the latest CHANGELOG release is $RELEASED"
fi

LAST_COMMIT=$(git log -1 --format="%h %s (%cr)" 2>/dev/null)
[ -n "$LAST_COMMIT" ] && echo "Last commit: $LAST_COMMIT"

BRANCH=$(git branch --show-current 2>/dev/null)
[ -n "$BRANCH" ] && echo "Branch: $BRANCH"

CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
[ "${CHANGES:-0}" -gt 0 ] && echo "Uncommitted changes: $CHANGES file(s)"

if [ -d .git ] && [ ! -x .git/hooks/pre-commit ]; then
    echo "Warning: git hooks not installed - run: bash scripts/install-hooks.sh"
fi

CLAUDE_COUNT=$(find . -name "CLAUDE.md" -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
ADR_COUNT=$(find docs/decisions -name 'ADR-*.md' 2>/dev/null | wc -l | tr -d ' ')
echo "CLAUDE.md files: $CLAUDE_COUNT, ADRs: $ADR_COUNT"

echo "======================"

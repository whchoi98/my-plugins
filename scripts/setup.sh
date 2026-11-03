#!/bin/bash
# Project setup script for new developers of my-plugins.
# Usage: bash scripts/setup.sh
# The plugin needs no build. This prepares the dev harness: tool checks, executable bits, git hooks.
# User dependencies of the skills (Playwright Chromium, fonts, pptxgenjs, python-pptx, LibreOffice, ...)
# are checked and installed by: bash skills/setup/scripts/setup.sh [install [--sudo]]

set -e

cd "$(dirname "$0")/.."

echo "=== my-plugins dev setup ==="

# Check prerequisites
command -v git >/dev/null 2>&1 || { echo "ERROR: git is required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required (hooks parse event JSON with it)"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required (bundled scripts and tests)"; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "ERROR: zip is required (aws-blog-skills package_blog.sh)"; exit 1; }
[ "${BASH_VERSINFO[0]}" -ge 4 ] || { echo "ERROR: Bash 4+ is required (found $BASH_VERSION)"; exit 1; }
if ! command -v claude >/dev/null 2>&1; then
    echo "WARNING: Claude Code CLI not found; 'claude plugin validate .' tests will be skipped"
fi
if ! command -v node >/dev/null 2>&1; then
    echo "WARNING: node not found; 'node --check' on the deck skills' JavaScript will be skipped"
fi
if ! command -v uv >/dev/null 2>&1 && ! python3 -c "import playwright" >/dev/null 2>&1; then
    echo "WARNING: neither uv nor the playwright module found; diagram PNG rendering will not work"
    echo "         run: bash skills/setup/scripts/setup.sh install"
fi

# Executable bits: harness hooks, dev scripts, tests, and the shipped shell and Python entry points
chmod +x .claude/hooks/*.sh scripts/*.sh tests/run-all.sh tests/*/*.sh
chmod +x scripts/diagrams/verify-geometry.py scripts/diagrams/verify-motion.py
chmod +x skills/aws-blog-skills/scripts/{check_structure.py,check_urls.py,lint_prose.py,package_blog.sh}
chmod +x skills/setup/scripts/setup.sh skills/aws-ppt-skills/scripts/install_fonts.sh
echo "Hooks and scripts are executable"

# Git hooks (commit-msg, pre-commit)
if [ -d ".git" ]; then
    bash scripts/install-hooks.sh
else
    echo "WARNING: not a git checkout; git hooks not installed"
fi

# Validate the plugin manifests when the CLI is available
if command -v claude >/dev/null 2>&1; then
    claude plugin validate . >/dev/null && echo "claude plugin validate: passed"
fi

echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Run the tests: bash tests/run-all.sh"
echo "  2. Check user dependencies of the skills: bash skills/setup/scripts/setup.sh"
echo "     (install with 'install', system packages with 'install --sudo')"
echo "  3. Read CLAUDE.md, skills/CLAUDE.md and docs/onboarding.md"
echo "  4. Try unreleased skill changes: claude --plugin-dir ."

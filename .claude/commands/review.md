---
description: Review current changes to the plugin with confidence-based filtering
allowed-tools: Read, Glob, Grep, Bash(git diff:*), Bash(git log:*), Bash(git status:*)
---

# Review

Review the current changes using confidence-based scoring.

## Step 1: Get Changes

- If $ARGUMENTS specifies files or a git ref, review those
- Otherwise, review unstaged changes: `git diff`
- If no unstaged changes, review staged changes: `git diff --cached`

## Step 2: Review

Apply the criteria in `.claude/skills/plugin-review/SKILL.md` to each changed file:
- Shipped-content invariants for all nine skills and three commands: frontmatter and triggers, skill-dir
  script paths, `my-plugins:<skill>` calls and no old namespaces, sibling-relative paths, nothing written into
  a skill folder
- Per-skill rules: aws-blog-skills (reference table, `lint_prose.py` in sync with `style.md`, author bio,
  no claude.ai-only names), kor-deslop (one pattern count), deck skills (template elements, punctuation,
  `NODE_PATH`), aws-diagram-design and `commands/` (export and import references), setup (sudo gating)
- Script behavior: exit codes, the no-zip-on-failure rule, `setup.sh` check mode changes nothing
- Release hygiene: `skills/` and `commands/` changes come with a version bump and a bilingual CHANGELOG entry
- Korean writing quality of new rules and examples
- Harness correctness (stdin JSON, exit 2, non-vacuous tests)

## Step 3: Score and Filter

Rate each issue 0-100. Only report issues with confidence >= 75.

## Step 4: Output

Present findings with file paths, line numbers, and fix suggestions.
If no high-confidence issues, confirm the change meets standards.

## Error Recovery

### If no changes found (Step 1)
- Check if changes are committed: `git log -1 --oneline`
- Check the branch: `git branch --show-current`
- Suggest specifying files directly: `/review skills/aws-diagram-design/SKILL.md`

### If CLAUDE.md is missing or empty (Step 2)
Project guidelines cannot be evaluated. Suggest `/init-project` or restoring `CLAUDE.md` from git.

### If the diff is too large (>500 lines)
Focus on high-risk files first:
1. `skills/setup/scripts/setup.sh` (downloads, sudo gating) and other `skills/*/scripts/*`, `tools/*`, `lib/*`
   (behavior and exit codes)
2. `skills/*/SKILL.md` (frontmatter, paths, cross-skill calls, workflow)
3. `skills/aws-blog-skills/scripts/diagram_lib.py` (`find_assets()` order) and `skills/aws-diagram-design/assets/`
4. `skills/aws-blog-skills/references/style.md` and `humanize-checklist.md` (rules mirrored in `lint_prose.py`),
   the kor-deslop rulebook (pattern count)
5. `.claude-plugin/*.json`, `.mcp.json`, `commands/`
6. Harness (`.claude/hooks/`, `tests/`)
7. Other documentation

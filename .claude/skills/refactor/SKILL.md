---
name: refactor
description: Restructure the my-plugins skill files (any skills/<name>/ SKILL.md, references/, scripts/, tools/, lib/), commands/, skills/setup/scripts/setup.sh or the bash harness without changing behavior, verifying with tests/run-all.sh after each step. Use when asked to reorganize, deduplicate, shorten, or split a skill, its scripts, or the harness.
---

# Refactor Skill

Improve structure without changing what the skills do or what the harness checks.

## What "behavior" means here
- **aws-blog-skills**: the workflow steps 0-7, the deliverable set (md + PNG + SVG + zip), the work-folder
  layout, the confirmed rules in `references/` and their dates, and the author bio text.
- **aws-diagram, aws-diagram-design, commands**: the visual-type selection and design rules, the icon lookup, the
  output contract (self-contained SVG/HTML, export formats), and each command's arguments.
- **kor-deslop**: the rule priority, the meaning-preservation rules, the pattern IDs and count, the output modes.
- **Deck skills**: the confirmation questions, template handling, lint rules, and the QA loop.
- **setup**: the three modes, the items checked and installed, where they go, and sudo gating.
- **Scripts**: which inputs each script accepts or rejects and its exit codes (`lint_prose.py` and
  `check_structure.py` exit 1 on findings, `check_urls.py` exit 1 on FAIL/REDIRECT, `package_blog.sh` writes no
  zip on failure, `setup.sh` exits 2 on a bad mode).
- **Cross-skill links**: `my-plugins:<skill>` calls and sibling-relative paths (`../aws-diagram-design/assets`,
  `../aws-ppt-skills/scripts/install_fonts.sh`), and the `find_assets()` order.
- **Harness**: which inputs each hook and test accepts or rejects.

Moving text between SKILL.md and a reference file is a refactor; changing any of the above is not.

## Process

### 1. Analysis
- Read root `CLAUDE.md` and `skills/CLAUDE.md`
- Identify the target and the tests covering it (`tests/structure/*.sh`, `tests/hooks/*.sh`; `tests/CLAUDE.md`
  maps each file)
- Record the baseline: `bash tests/run-all.sh` and `claude --plugin-dir . plugin details my-plugins`
  (always-on and on-invoke token cost per skill)

### 2. Plan
Present the plan to the user:
- What will change
- What will NOT change (the behavior list above)
- Expected effect on always-on cost (every skill and command `description` is loaded every session)
- Risk assessment (low/medium/high)

### 3. Execute
- Small steps; after each one run `bash tests/run-all.sh` and `claude plugin validate .`
- Keep rule dates `(YYYY-MM-DD 확정)`, the `lint_prose.py` term lists and the kor-deslop pattern count in sync
- Keep commits atomic

### 4. Verify
- All tests pass
- `git diff --stat` touches only the intended files
- `claude --plugin-dir . plugin details my-plugins` shows no unintended cost change
- A skill-text refactor still ships to users, so bump the PATCH version (see `release` skill)

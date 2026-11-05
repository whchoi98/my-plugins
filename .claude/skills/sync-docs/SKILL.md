---
name: sync-docs
description: Synchronize my-plugins documentation (root and module CLAUDE.md, docs/architecture.md, docs/reference/, ADRs, runbooks, docs/diagrams/, README, CHANGELOG) with the current nine skills, three commands, scripts, setup.sh and manifests, and score CLAUDE.md quality. Use after changing skills/, commands/ or the harness, or when asked to update or audit docs.
---

# Sync Docs Skill

Synchronize project documentation with the current repository state. The sync rules are in root
`CLAUDE.md` ("Change Sync Rules").

## Actions

### 1. Quality Assessment
Score each CLAUDE.md file (0-100) across:
- Commands/workflows (20 pts)
- Architecture clarity (20 pts)
- Non-obvious patterns (15 pts)
- Conciseness (15 pts)
- Currency (15 pts)
- Actionability (15 pts)

Apply anti-pattern deductions:
- Over 500 lines (-15)
- Vague instructions (-10)
- Duplicated docs (-10)
- No test guidance (-10)
- Contains secrets (-20)

Output a quality report with grades (A-F) before making changes.

### 2. Root CLAUDE.md Sync
- Update Overview, Tech Stack, Project Structure, Conventions, Key Commands
- Keep inventories current: skills under `skills/*/SKILL.md`, commands under `commands/`, the `find_assets()`
  order in `skills/aws-blog-skills/scripts/diagram_lib.py`, the kor-deslop pattern count
- Verify commands are copy-paste ready

### 3. Architecture Doc Sync
- Update `docs/architecture.md` (English and Korean sections identically)
- Keep the skill and command table, the cross-skill call diagram (`my-plugins:<skill>` calls in every
  SKILL.md and reference, sibling-relative paths) and the asset lookup list in step with the code
- Keep the Packaging table accurate: which files ship, which are loaded, which are inert

### 4. Module CLAUDE.md Audit
- Source roots: `skills/ tests/`
- Module docs live at `skills/CLAUDE.md` and `tests/CLAUDE.md`; never add one inside `skills/<name>/`
  (that directory ships as the skill)
- `skills/CLAUDE.md`: the skill table and cross-skill links match the tree
- Score each module CLAUDE.md

### 5. Reference, ADR and Runbook Audit
- Check every Code Pointer path (and line range) in `docs/reference/*.md` exists; refresh
  `docs/reference/INDEX.md` and the root `<!-- AUTO-MANAGED:references -->` block
- `docs/reference/agent-llm.md` covers every skill; refresh its token table with
  `claude --plugin-dir . plugin details my-plugins`
- `docs/reference/security.md` lists every shipped script and every `setup.sh` download
- Check recent commits for undocumented decisions (`docs/decisions/ADR-*.md`)
- Verify `docs/runbooks/release-plugin.md` matches the README update commands, and
  `docs/runbooks/setup-dependencies.md` matches `skills/setup/scripts/setup.sh` and `skills/setup/SKILL.md`

### 6. docs/diagrams Sync
- `docs/diagrams/guide-claude-code.md` and `guide-kiro.md`: install commands use `my-plugins@my-plugins`, command
  names use `/my-plugins:`, the command table matches `commands/*.md` `argument-hint`

### 7. README.md and CHANGELOG.md Sync
- Skill and command tables, project structure, configuration variables, install id and version badge in both
  language sections
- CHANGELOG `[Unreleased]` covers every user-facing change since the last tag

### 8. Report
Output before/after quality scores, anti-patterns detected, and the list of changes.
Finish with `bash tests/run-all.sh`.

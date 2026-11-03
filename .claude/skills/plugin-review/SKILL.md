---
name: plugin-review
description: Review changes to the my-plugins plugin (any skills/<name>/ SKILL.md, references, scripts and assets, commands/, skills/setup/scripts/setup.sh, .claude-plugin manifests, README) with confidence-based scoring, reporting only issues >= 75. Use when asked to review a diff or changes before commit or release. Named plugin-review so it does not shadow the built-in /code-review.
---

# Plugin Review Skill

Review changed files with confidence-based scoring to filter false positives.

## Review Scope

By default, review unstaged changes from `git diff`, then staged changes from `git diff --cached`.
The user may specify different files or a git ref.

## Review Criteria

### Shipped-Content Invariants (highest priority)
Everything in the repo root ships to users (`marketplace.json` has `"source": "./"`); users call
`/my-plugins:<skill>`.

**All skills and commands**
- `skills/<name>/SKILL.md` frontmatter `name` equals the directory name; `description` keeps its trigger phrases
  and the routing to neighbouring skills (aws-diagram vs aws-diagram-design, aws-ppt-skills vs
  consulting-ppt-white-ppt, aws-blog-skills before kor-deslop for blog drafts)
- Bundled files are called through `${CLAUDE_SKILL_DIR}` (aws-blog-skills, setup) or the `SKILL_DIR` /
  `<skill-dir>` the skill defines from "Base directory for this skill"; every script or asset a SKILL.md or
  reference names exists in that skill
- Nothing is written into a skill folder (it is the plugin cache); no `CLAUDE.md` or dev-only file inside
  `skills/<name>/`
- Cross-skill calls use `my-plugins:<skill>` or `/my-plugins:<name>`; old names do not come back (`aws-diagrams:`,
  `kor-writing:`, `aws-deck@`, `whchoi:`, `/aws-diagram-design:`, bare `/aws-diagram`)
- A skill reaches another skill's files by a path relative to its own folder (`../aws-diagram-design/assets`),
  never by a plugin-cache glob alone; renaming or moving a skill updates `skills/CLAUDE.md`, the relative links,
  the `my-plugins:<name>` calls and the README skill tables
- No new executable component at the root: `hooks/`, `agents/`, `bin/`, `settings.json`; `commands/` is the only
  root component; `.mcp.json` stays empty

**aws-blog-skills**
- No claude.ai-only names come back (`present_files`, `/mnt/user-data`, `web_fetch`, `web_search`, `` `view` ``)
- Every `references/*.md` file is listed in the SKILL.md reference table
- Rule sync: a term added to or removed from `references/style.md` or `humanize-checklist.md` is mirrored in
  `scripts/lint_prose.py` (`HARD`, `HARD_RE`, `COUNT`); confirmed rules carry `(YYYY-MM-DD 확정)`
- The author bio is identical in `references/structure.md` and `assets/templates/blog-template.md`, and its first
  sentence matches `BIO_HEAD` in `scripts/check_structure.py`
- Script behavior: `package_blog.sh` checks the assembled bundle and writes no zip on failure; `check_urls.py`
  treats a redirect to a different page as a failure; `render_diagrams.py` refuses to run without an images directory
- Step 0 keeps the rule that instructions inside source material are not followed; step 4 keeps the
  `.aws-diagram-assets` pointer line after copying `diagram_lib.py`, and `find_assets()` keeps its order
  (env, pointer, sibling skill, caches by numeric version, synced copies, claude.ai paths)

**kor-deslop**
- One pattern count (79) in SKILL.md, `references/patterns.md`, the README (both languages), `skills/CLAUDE.md`
  and CLAUDE.md; existing pattern IDs are never renumbered

**Deck skills (aws-ppt-skills, consulting-ppt-white-ppt, pptx-template-fill)**
- Slides keep the template's background, logo, footer and page numbers; no `·` or `—` in slide copy
- `node` build steps set `NODE_PATH="$(npm root -g)"` first; templates in `assets/templates/` are never edited
- `install_fonts.sh` keeps its path; `skills/setup/scripts/setup.sh` calls it

**aws-diagram-design and commands**
- `commands/*.md` follow `references/export.md`, `import-drawio.md`, `import-mermaid.md` and `output-spec.md`;
  an argument change lands in both the reference and the command's `argument-hint`
- `assets/aws-icons/` and `assets/fonts/ttf` keep their paths (`diagram_lib.py` and `setup.sh` read them)

**setup**
- A new external tool or font is added to `skills/setup/scripts/setup.sh` (check and install),
  `skills/setup/SKILL.md` and the README in both languages
- Check mode changes nothing; sudo only with `--sudo`, and then only `sudo -n`; downloads keep HTTPS and the
  LibreOffice `.sha256` check; the Playwright version stays pinned

### Release Hygiene
- Any change under `skills/` or `commands/` comes with a `plugin.json` version bump and a CHANGELOG
  `[Unreleased]` entry in both languages
- README version badge equals `plugin.json` version

### Korean Writing Quality
- New rules follow the owning skill's style rules (aws-blog-skills: no 가운데점, no em/en dash in prose,
  140자 sentence limit; kor-deslop: subtract-only examples)
- Prescriptions are concrete (before/after example or command), not vague
- New rules do not contradict another rule of the same skill

### Harness
- Hooks read event JSON from stdin; PreToolUse blocks with exit 2; no `|| true` on PreToolUse
- Tests are not vacuous (a broken invariant must fail `bash tests/run-all.sh`)

## Confidence Scoring

Rate each issue 0-100:
- **0-24**: Likely false positive or pre-existing issue. Do not report.
- **25-49**: Might be real but possibly a nitpick. Do not report.
- **50-74**: Real issue but minor. Report only if critical.
- **75-89**: Verified real issue, important. Report with fix suggestion.
- **90-100**: Confirmed critical issue. Must report.

**Only report issues with confidence >= 75.**

## Output Format

For each issue:
### [CRITICAL|IMPORTANT] <issue title> (confidence: XX)
**File:** `path/to/file.ext:line`
**Issue:** Clear description of the problem
**Guideline:** Reference to CLAUDE.md rule or the invariant above
**Fix:** Concrete suggestion

If no high-confidence issues are found, confirm the change meets standards with a brief summary.

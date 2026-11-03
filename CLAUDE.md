# Project Context

## Overview
`my-plugins` 1.0.0 is one Claude Code plugin that bundles four earlier plugins by WooHyung Choi:
aws-blog-skills (AWS Korea Tech Blog drafts), aws-diagrams (AWS architecture and structure diagrams),
kor-writing (Korean AI-tell removal) and aws-deck (AWS PowerPoint decks). It ships eight skills, three
slash commands, and Python, Bash and Node.js scripts that Claude runs on the user's machine. The `setup`
skill checks and installs the external tools and fonts the other skills need.

The repo root **is** the shipped plugin and its marketplace (`.claude-plugin/marketplace.json`,
`"source": "./"`). Users install it as `my-plugins@my-plugins` and invoke `/my-plugins:<skill>`.
Public repo `github.com/whchoi98/my-plugins`, MIT (bundled third-party files keep their own terms, `NOTICE.md`).

## Tech Stack
- **Content** — Markdown skills (`skills/<name>/SKILL.md`) with on-demand references, templates and assets
- **Shipped scripts** — Python 3 (blog lint, structure, URL, diagram generation; icon lookup and embedding;
  diagram self-checks; python-pptx template tools), Playwright for Python (`uv run --no-project --with playwright`),
  Node.js + pptxgenjs v4 (deck builds), Bash (`package_blog.sh`, `install_fonts.sh`, `setup.sh`)
- **Render QA tools** — LibreOffice `soffice`, Poppler `pdftoppm`/`pdftotext`, `rsvg-convert` or cairosvg
- **Packaging** — Claude Code plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`), JSON
- **Harness** — Bash 5 hooks and tests, `jq` 1.7, Python 3
- **Tooling** — Claude Code CLI (`claude plugin validate|details|marketplace|update`), git, GitHub

## Project Structure
```
.claude-plugin/   - plugin.json (name, version) + marketplace.json (source ./)        [ships, loaded]
skills/           - Shipped skills; module doc skills/CLAUDE.md                        [ships, loaded]
  aws-blog-skills/  aws-diagram/  aws-diagram-design/  kor-deslop/
  aws-ppt-skills/  consulting-ppt-white-ppt/  pptx-template-fill/  setup/
commands/         - export-diagram, import-drawio, import-mermaid (aws-diagram-design)  [ships, loaded]
third_party/      - upstream licenses and notices                                        [ships, inert]
LICENSE, NOTICE.md, README.md, CHANGELOG.md                                              [ships, inert]
.mcp.json         - Must stay empty: it is also the plugin's MCP config                  [ships, loaded]
.claude/          - Dev harness: settings, hooks, project skills, commands, agents       [ships, inert]
docs/             - architecture, onboarding, ADRs, runbooks, reference/; docs/diagrams/ [ships, inert]
scripts/          - setup.sh, install-hooks.sh; scripts/diagrams/ (diagram repo gates, fixtures)
tests/            - run-all.sh, hooks/, structure/, fixtures/; module doc tests/CLAUDE.md
```
"Ships" means it is copied into every installer's plugin cache. "Loaded" means Claude Code reads it as
a plugin component there. Everything under `.claude/` is only active when this repo is the working directory.

## Conventions
- **Plugin components at the root are limited to `commands/`** (three Markdown prompts from aws-diagrams).
  Never add `hooks/`, `agents/`, `settings.json`, `bin/`, or entries in `.mcp.json`; they would run for every
  user. Dev-only tooling goes under `.claude/`. `tests/structure` enforces this.
- **One namespace**: skills call each other as `my-plugins:<skill>` (Skill tool) or `/my-plugins:<name>`.
  Old names (`aws-diagrams:`, `kor-writing:`, `aws-deck@`, `whchoi:`, `/aws-diagram-design:`, bare
  `/aws-diagram`) must not come back; tests reject them.
- **Any change under `skills/` or `commands/` is a release**: installed copies update only when
  `.claude-plugin/plugin.json` `version` changes. Bump it, update the README badge and add a bilingual
  CHANGELOG entry (`docs/runbooks/release-plugin.md`). Users then need both
  `claude plugin marketplace update my-plugins` and `claude plugin update my-plugins@my-plugins`.
- **Skill paths**: a SKILL.md calls its scripts through `${CLAUDE_SKILL_DIR}` (aws-blog-skills, setup) or the
  `SKILL_DIR` / `<skill-dir>` the skill defines from "Base directory for this skill". Nothing is written into a
  skill folder, which is the plugin cache. A skill reaches another skill's files only by a path relative to
  its own folder (`../aws-diagram-design/assets`), never by a cache glob alone.
- **Diagram assets**: `skills/aws-blog-skills/scripts/diagram_lib.py` `find_assets()` order is
  `AWS_DIAGRAM_ASSETS` → `.aws-diagram-assets` next to the file → sibling skill → plugin caches (numeric
  version order) → synced copies → claude.ai container paths. Keep the pointer step in SKILL.md when the
  work-folder copy step changes.
- **Dependencies go through `setup`**: a new external tool or font is added to `skills/setup/scripts/setup.sh`
  (check and install), `skills/setup/SKILL.md` and the README in both languages. `setup.sh` never runs sudo
  without `--sudo`, and then only `sudo -n`.
- **Per-skill rules carried over from the source repos**:
  - aws-blog-skills: confirmed rules are appended to references with `(YYYY-MM-DD 확정)`; a term added to
    `style.md` or `humanize-checklist.md` is mirrored in `scripts/lint_prose.py`; the author bio is verbatim in
    `references/structure.md` and `assets/templates/blog-template.md`; keep the description trigger phrases.
  - kor-deslop: the pattern count (79) comes from `references/patterns.md` and is the same in `skills/CLAUDE.md`, this file
    and the README in both languages.
  - aws-ppt-skills: slides keep the template's background, logo, footer and page numbers; no `·` or `—`.
- **Module docs**: never put `CLAUDE.md` inside `skills/<name>/`; that directory ships as the skill.
- **Docs**: user-facing docs are bilingual (English first, `<a id="english">` / `<a id="korean">`),
  Korean sections in 합니다체, skill text in 한다체, no emojis, Mermaid for diagrams.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-Authored-By`
  (settings `attribution` is empty and the `commit-msg` hook strips it).

## Key Commands
```bash
bash scripts/setup.sh                     # dev: check tools, chmod hooks and scripts, install git hooks
bash skills/setup/scripts/setup.sh        # user deps: check; add "install" or "install --sudo"
bash tests/run-all.sh                     # all harness tests
bash tests/run-all.sh structure           # structure and shipped-script tests
claude plugin validate .                  # manifest + skill validation (ICON_MISSING warning is expected)
claude --plugin-dir . plugin details my-plugins   # token cost of the working tree, before installing
claude plugin details my-plugins@my-plugins   # components and always-on / on-invoke token cost (installed)
claude --plugin-dir .                     # session with this working tree loaded as a plugin
claude plugin marketplace update my-plugins && claude plugin update my-plugins@my-plugins
```

## Implementation References
<!-- AUTO-MANAGED:references -->
Layer-by-layer implementation guides in `docs/reference/`. See [INDEX](docs/reference/INDEX.md).
- [Security](docs/reference/security.md)
- [Agent · LLM](docs/reference/agent-llm.md)
<!-- /AUTO-MANAGED -->

---

## Auto-Sync Rules

Rules below are applied automatically after Plan mode exit and on major changes.

### Post-Plan Mode Actions
After exiting Plan mode (`/plan`), before starting implementation:

1. **Architecture decision made** -> Update `docs/architecture.md`
2. **Technical choice/trade-off made** -> Create `docs/decisions/ADR-NNN-title.md`
3. **New module added** -> Create `CLAUDE.md` in that module directory (not inside `skills/<name>/`)
4. **Operational procedure defined** -> Create runbook in `docs/runbooks/`
5. **Changes needed in this file** -> Update relevant sections above

### Change Sync Rules
- New skill under `skills/` -> Update `skills/CLAUDE.md`, README skill table (both languages), `docs/reference/agent-llm.md`
- New external tool or font -> Update `skills/setup/scripts/setup.sh`, `skills/setup/SKILL.md`, README (both languages)
- New or changed aws-blog-skills script -> Update its SKILL.md and `tests/structure/test-aws-blog-skills-scripts.sh`
- Anything under `skills/` or `commands/` changed -> Version bump + CHANGELOG `[Unreleased]` (both languages)
- Harness changed (`.claude/`, `tests/`, `scripts/`) -> Update `tests/CLAUDE.md` and `docs/reference/security.md`

### ADR Numbering
Find the highest number in `docs/decisions/ADR-*.md` and increment by 1.
Format: `ADR-NNN-concise-title.md`

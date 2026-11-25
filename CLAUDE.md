# Project Context

## Overview
`my-plugins` 1.10.0 is one Claude Code plugin that bundles five earlier plugins by WooHyung Choi:
aws-blog-skills (AWS Korea Tech Blog drafts), aws-diagrams (AWS architecture and structure diagrams),
kor-writing (Korean AI-tell removal), aws-deck (AWS PowerPoint decks) and aws-reports (benchmark and PoC
reports as MS Word + HTML), plus the new html-report skill (common-design bilingual HTML reports), the new
techblogs skill (posts for the author's personal tech blog) and the new aws-infographic skill (fact-checked
infographics and an editable deck of the same content), and two skills vendored from other authors' repositories:
ui-deslop (heydamir/unslop, AI slop in UI) and eng-deslop (blader/humanizer, AI slop in English text). aws-diagram-design
is the AWS edition of cathrynlavery/diagram-design, rebuilt from that repository by a recipe. It ships fourteen
skills, five slash commands, and Python, Bash and Node.js scripts that Claude runs on the user's machine. The `setup`
skill checks and installs the external tools and fonts the other skills need.

The repo root **is** the shipped plugin and its marketplace (`.claude-plugin/marketplace.json`,
`"source": "./"`). Users install it as `my-plugins@my-plugins` and invoke `/my-plugins:<skill>`.
Public repo `github.com/whchoi98/my-plugins`, MIT (bundled third-party files keep their own terms, `NOTICE.md`).

## Tech Stack
- **Content** — Markdown skills (`skills/<name>/SKILL.md`) with on-demand references, templates and assets
- **Shipped scripts** — Python 3 (blog lint, structure, URL, diagram generation, pre-check metrics and report check, WordPress HTML conversion; icon lookup and embedding;
  diagram self-checks; python-pptx template tools and the deck-to-HTML converter; HTML report checks and image embedding; personal blog post import,
  build, check and placement; infographic SVG builder, render QA and the editable-deck check), Playwright for Python (`uv run --no-project --with playwright`),
  Node.js + pptxgenjs v4 (deck builds), Node.js + docx 9 + marked 18 (report builds, `report.mjs`),
  Bash (`package_blog.sh`, `install_fonts.sh`, `setup.sh`), the ES modules of ui-deslop (Node Playwright and ffmpeg,
  both optional and left to the user)
- **Render QA tools** — LibreOffice `soffice`, Poppler `pdftoppm`/`pdftotext`, `rsvg-convert` or cairosvg
- **Packaging** — Claude Code plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`), JSON
- **Harness** — Bash 5 hooks and tests, `jq` 1.7, Python 3; `scripts/sync_upstream_skills.py` and two GitHub Actions
  workflows keep the vendored skills (weekly) and aws-diagram-design (every second week) in step with their sources
- **Tooling** — Claude Code CLI (`claude plugin validate|details|marketplace|update`), git, GitHub

## Project Structure
```
.claude-plugin/   - plugin.json (name, version) + marketplace.json (source ./)        [ships, loaded]
skills/           - Shipped skills; module doc skills/CLAUDE.md                        [ships, loaded]
  aws-blog-skills/  aws-diagram/  aws-diagram-design/  kor-deslop/
  aws-ppt-skills/  consulting-ppt-white-ppt/  pptx-template-fill/  aws-reports/  html-report/  techblogs/
  aws-infographic/  ui-deslop/  eng-deslop/  setup/
commands/         - export-diagram, import-drawio, import-excalidraw, import-mermaid, import-plantuml
                    (aws-diagram-design; written by the sync from the source's commands)  [ships, loaded]
third_party/      - upstream licenses and notices                                        [ships, inert]
.github/          - workflows/sync-upstream-skills.yml (weekly, vendored skills) and
                    sync-aws-diagram-design.yml (every second week)                      [ships, inert]
LICENSE, NOTICE.md, README.md, CHANGELOG.md                                              [ships, inert]
.mcp.json         - Must stay empty: it is also the plugin's MCP config                  [ships, loaded]
.claude/          - Dev harness: settings, hooks, project skills, commands, agents       [ships, inert]
docs/             - architecture, onboarding, ADRs, runbooks, reference/; docs/diagrams/ [ships, inert]
scripts/          - setup.sh, install-hooks.sh, sync_upstream_skills.py + upstream-skills.json (vendored and derived
                    skills); scripts/upstream/aws-diagram-design/ (recipe.json and blocks/ of the AWS edition);
                    scripts/diagrams/ (diagram repo gates, fixtures)
tests/            - run-all.sh, hooks/, structure/, fixtures/; module doc tests/CLAUDE.md
```
"Ships" means it is copied into every installer's plugin cache. "Loaded" means Claude Code reads it as
a plugin component there. Everything under `.claude/` is only active when this repo is the working directory.

## Conventions
- **Plugin components at the root are limited to `commands/`** (five Markdown prompts of aws-diagram-design, written by the sync).
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
    The pre-check (step 6) is one rule in three places: the criteria and minimums of `references/precheck.md` equal
    `CRITERIA` and `PASS_TOTAL` in `scripts/check_gate.py`, and the example report in `precheck.md` is one the checker
    accepts. `scripts/package_blog.sh` writes no zip without a gate report it accepts (`--no-gate` only when the user
    asked), and ends its output with the score table (`scores:`) that the last response of a session shows without
    being asked (user rule of 2026-11-25; SKILL.md steps 6 and 7 and `precheck.md` say so together). The markup `scripts/md_to_wordpress.py` writes is the one `references/publishing.md` shows; the converter
    uploads nothing and escapes raw HTML. The criteria, the report layout and the measures follow
    comeddy/blog-precheck-plugin (MIT, `third_party/LICENSE-blog-precheck`), so keep the report's names and verdict words.
  - kor-deslop: the pattern count (81) comes from `references/patterns.md` and is the same in `skills/CLAUDE.md`, this file
    and the README in both languages.
  - aws-ppt-skills: slides keep the template's background, logo, footer and page numbers; no `·` or `—`. The HTML
    deck is only ever converted from the finished `.pptx` (`scripts/deck_to_html.py`); a key or a control of the page
    goes into `assets/html/deck.js`, the key table of `references/html-deck.md` and `scripts/preview_html_deck.py`
    together, and the output format (PPT, HTML or both) stays the first question of the Workflow.
  - aws-reports: a wording correction goes into `references/style-rules.md` and `scripts/style_terms.json`
    together (`"profiles": ["poc"]` for PoC-only terms); a layout rule goes into `report.mjs` `tableLayout()`
    and `check_report.py` together; example numbers come from each example's `make_charts.py`. `report.mjs`
    is ESM, so it finds the global npm packages itself (`NODE_PATH`, then `npm root -g`).
  - html-report: a design rule goes into `references/design-spec.md`, `assets/template.html` and
    `scripts/check_html.py` together; a report keeps the template's `<style>` and `<script>`; Korean and English
    are element pairs (`lang="ko"`, then the same tag with `lang="en"`).
  - techblogs: a design rule goes into `references/design-spec.md`, `assets/template.html` and
    `scripts/check_post.py` together; a report keeps the template's `<style>` and `<script>`; the page body is
    built from the fragment files in the work folder (`meta.json`, `ko.body.html`, `en.body.html`). A new post
    opens with the background paragraph (one or two sentences on the background of the topic or why it is needed):
    the rule lives in `references/storylines.md` (one `배경 문단` line per storyline, which `scripts/new_post.py`
    reads), SKILL.md step 2, `references/design-spec.md` and the WARN of `scripts/check_post.py` together.
    A new post stays within a reading time of 15 minutes (overlap is cut first, then the post is split into a
    series): SKILL.md steps 0, 2 and 5, `references/storylines.md`, `references/design-spec.md`, the WARN of
    `scripts/check_post.py` and the line `scripts/new_post.py` prints change together, and `READ_CHARS_PER_MIN`
    is the same number in `scripts/build_post.py` and `scripts/check_post.py`.
  - aws-infographic: the code lives in `scripts/` and is copied into the work folder, never pasted into SKILL.md;
    the icon bundle lookup in `infokit.py` and the `.aws-icon-bundle` step in SKILL.md change together; the deck
    of an infographic holds text boxes, shapes, tables, charts and `icon:` PNG pictures only, so a rule about it
    goes into `references/ppt-deck.md`, `scripts/check_editable.py` and the aws-ppt-skills `addIcon()` and
    `check_deck.py` together (one `ICON_MAX_IN`).
  - aws-diagram-design: the AWS edition of cathrynlavery/diagram-design (MIT), `"mode": "derived"` in
    `scripts/upstream-skills.json`. `sync_upstream_skills.py update` rebuilds it from the source by
    `scripts/upstream/aws-diagram-design/recipe.json`: literal replacements (AWS colors, Amazon Ember, plugin names),
    anchored edits that put the edition's blocks in, and a list of tokens that may not survive. A file that comes from
    the source, the five `commands/*.md` included, is never edited by hand: change the recipe or a block, then run
    `update --skill aws-diagram-design --pinned`. The edition's own files are the ones the recipe lists as `local`
    (`references/style-guide.md`, `references/primitive-aws-icons.md`, `assets/aws-icons/`, `assets/fonts/`,
    `scripts/aws_check.py`, `scripts/build_aws_icons.py`); `style-guide.md` keeps the roles and section headings of the
    source's style guide. The sync, the workflows and `tests/structure/test-aws-diagram-design.sh` run no script of the
    source: the scripts are copied byte for byte and read as text.
  - ui-deslop, eng-deslop: vendored from heydamir/unslop (CC BY 4.0) and blader/humanizer (MIT) and never edited by
    hand. `scripts/upstream-skills.json` holds the source, the pinned commit, a hash of every file and the `name` and
    `description` my-plugins gives the skill; `scripts/sync_upstream_skills.py update` writes the folders, `render`
    writes a description changed in the manifest, `verify` checks the copy. A file type that is new in a source goes
    into `allow_ext` only after the file was read, and a sync reaches `main` through a reviewed pull request.
- **Module docs**: never put `CLAUDE.md` inside `skills/<name>/`; that directory ships as the skill.
- **Docs**: user-facing docs are bilingual (English first, `<a id="english">` / `<a id="korean">`),
  Korean sections in 합니다체, skill text in 한다체, no emojis, Mermaid for diagrams.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-Authored-By`
  (settings `attribution` is empty and the `commit-msg` hook strips it).

## Key Commands
```bash
bash scripts/setup.sh                     # dev: check tools, chmod hooks and scripts, install git hooks
bash skills/setup/scripts/setup.sh        # user deps: check; add "install" or "install --sudo"
python3 scripts/sync_upstream_skills.py check   # vendored and derived skills against their sources (exit 10: update); update [--pinned], render, verify
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
- Changed `skills/aws-ppt-skills/scripts/deck_to_html.py`, `preview_html_deck.py` or `assets/html/` -> Run `bash tests/run-all.sh aws-ppt-skills` with the deck tools and a cached Playwright (the fixture deck is converted and opened in a browser there)
- Changed deck helper in `skills/aws-infographic/references/ppt-deck.md` or `addIcon()` -> Run `bash tests/run-all.sh aws-infographic` with the deck tools installed (the example deck is built there)
- Vendored skill (`skills/ui-deslop`, `skills/eng-deslop`) -> Change it only with `scripts/sync_upstream_skills.py` (`update`, or `render` for the description), read the source's diff first, run `bash tests/run-all.sh upstream-skills` (`docs/runbooks/sync-upstream-skills.md`)
- aws-diagram-design -> Never edit a file of the source or `commands/*.md` by hand. Change `scripts/upstream/aws-diagram-design/recipe.json` or a block, run `python3 scripts/sync_upstream_skills.py update --skill aws-diagram-design --pinned`, then `bash tests/run-all.sh upstream` and `bash tests/run-all.sh 'aws-diagram-design$'`. An edition file (`local` in the recipe) is edited directly (`docs/runbooks/sync-upstream-skills.md`)
- New vendored skill -> Manifest entry, NOTICE.md row, the lists of a new skill above, and the expected names in `tests/structure/test-upstream-skills.sh`
- Anything under `skills/` or `commands/` changed -> Version bump + CHANGELOG `[Unreleased]` (both languages)
- Harness changed (`.claude/`, `tests/`, `scripts/`) -> Update `tests/CLAUDE.md` and `docs/reference/security.md`

### ADR Numbering
Find the highest number in `docs/decisions/ADR-*.md` and increment by 1.
Format: `ADR-NNN-concise-title.md`

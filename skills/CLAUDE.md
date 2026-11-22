# skills/

Shipped skills. Each directory is one skill, invoked as `/my-plugins:<name>`. This file sits directly in
`skills/`, so it is not part of any skill.

| Skill | Source | Entry points |
|---|---|---|
| `aws-blog-skills/` | aws-blog-skills 1.2.2 | SKILL.md, `references/` (rule files per step), `scripts/` (lint, structure, URL, diagram lib, render, package), `assets/templates/` |
| `aws-diagram/` | aws-diagrams 1.0.0 | SKILL.md, `scripts/find_icon.py`, `embed.py`, `build_bundle.py`, `assets/` (icon bundle) |
| `aws-diagram-design/` | aws-diagrams 1.0.0 | SKILL.md, `references/` (style guide, types, export, import), `scripts/` (self_check, verify-geometry, extractors), `assets/aws-icons/`, `assets/fonts/` |
| `kor-deslop/` | kor-writing 1.0.0 | SKILL.md, `references/patterns.md` (A~K, 81 patterns) |
| `aws-ppt-skills/` | aws-deck 1.0.0 | SKILL.md (output format asked first: PPT, HTML or both), `scripts/` (apply_template, check_deck, svg_to_png, install_fonts.sh; deck_to_html and preview_html_deck for the HTML deck), `assets/templates/`, `assets/fonts/`, `assets/html/` (deck.css, deck.js: the page's stage, controls and presenter view), `references/` (diagrams, html-deck) |
| `consulting-ppt-white-ppt/` | aws-deck 1.0.0 | SKILL.md, `lib/consult_helpers.js`, `tools/` (fix_pptx, fix_notes, extract_brand_color), `examples/` |
| `pptx-template-fill/` | aws-deck 1.0.0 | SKILL.md, `scripts/` (tfill, inventory, qa_check, swap_font) |
| `aws-reports/` | aws-reports 1.0.0 | SKILL.md (report type, then one procedure), `references/` (markdown-spec, style-rules, benchmark-structure, poc-structure, poc-verdict-rules), `scripts/` (report.mjs, check_report.py, chart_style.py, fonts.py, preview.py, svg2png.py, style_terms.json), `assets/examples/` (benchmark, poc) |
| `html-report/` | new | SKILL.md, `references/design-spec.md` (tokens, page order, language pairs, components), `assets/template.html`, `scripts/` (check_html, embed_images, preview) |
| `techblogs/` | new (replaces the user-level techblogs skill) | SKILL.md, `references/design-spec.md` (meta.json keys, fragment markup, text rules), `references/publish.md` (placing, build, viewing, git rules), `assets/template.html`, `scripts/` (import_aws_post, build_post, check_post, place_post, preview) |
| `aws-infographic/` | new (replaces the claude.ai-synced aws-infographic skill) | SKILL.md, `scripts/` (infokit: SVG builder; buildkit: render, layout QA, text lint; icon_png: icons for a deck; check_editable: deck made of editable objects only), `assets/page_template.py`, `references/ppt-deck.md` (content mapping, deck helpers, example) |
| `ui-deslop/` | heydamir/unslop (CC BY 4.0), vendored | SKILL.md (audit, direction, ordered passes on an existing screen), `references/` (signs, tokens, visuals, effects, rtl, refs and `refs/*.webp`), `scripts/` (snapshot.mjs, story.mjs, story-path.mjs: Node Playwright and ffmpeg, both optional). Never edited by hand |
| `eng-deslop/` | blader/humanizer (MIT), vendored | SKILL.md only (numbered patterns for English text). Never edited by hand |
| `setup/` | new | SKILL.md, `scripts/setup.sh` (check, install, install --sudo) |

## Cross-skill links
- aws-blog-skills → `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`,
  `my-plugins:setup`; `scripts/diagram_lib.py` reads `../aws-diagram-design/assets` (fonts, icons)
- aws-ppt-skills → `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:setup`;
  `scripts/deck_to_html.py` reads `../aws-diagram-design/assets/fonts/ttf` (Amazon Ember, for diagram SVGs that name it)
- aws-reports → `my-plugins:aws-diagram` (architecture figures), `my-plugins:setup` (npm packages, fonts);
  `../aws-blog-skills/scripts/lint_prose.py` (prose check)
- html-report → `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design` (figures), `my-plugins:kor-deslop`
  (check-only), `my-plugins:setup` (Playwright); `../aws-blog-skills/scripts/lint_prose.py` and
  `../aws-blog-skills/references/style.md` (Korean text)
- techblogs → `my-plugins:kor-deslop` (check-only), `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`
  (figures), `my-plugins:setup` (Playwright); `../aws-blog-skills/scripts/lint_prose.py` and `check_urls.py`,
  `../aws-blog-skills/references/style.md`, `humanize-checklist.md` and `verification.md`
- aws-infographic → `my-plugins:aws-ppt-skills` (the editable deck), `my-plugins:setup` (Pillow, Playwright, fonts,
  deck tools); `../aws-diagram/assets/icons.json` and `scripts/find_icon.py` (icons), `../aws-ppt-skills/scripts/`
  `apply_template.py` and `check_deck.py`
- aws-ppt-skills → `../aws-infographic/scripts/icon_png.py`, `check_editable.py` and `references/ppt-deck.md`
  (editable decks, `addIcon()`)
- setup → `../aws-diagram-design/assets/fonts/ttf` (Amazon Ember), `../aws-ppt-skills/scripts/install_fonts.sh`
- ui-deslop, eng-deslop → no other skill and no file outside their folders; the three deslop descriptions name each other (`my-plugins:kor-deslop` for Korean text, `my-plugins:eng-deslop` for English text, `my-plugins:ui-deslop` for a screen)

## Rules
- Do not add `CLAUDE.md` or dev-only files inside `skills/<name>/`; everything there ships.
- Renaming or moving a skill breaks the relative links above and the `my-plugins:<name>` calls; update both
  and the README skill table.
- Trigger phrases of aws-blog-skills overlap with the claude.ai-synced `anthropic-skills:aws-blog-skills` and
  `blog-writing`, and those of aws-infographic with `anthropic-skills:aws-infographic`; README explains how to turn
  the synced copies off.
- `ui-deslop/` and `eng-deslop/` are copies of other repositories. `scripts/upstream-skills.json` holds the source, the
  pinned commit, a hash of every file and the name and description my-plugins gives the skill.
  `scripts/sync_upstream_skills.py update` is the only thing that writes those folders (`render` after a description
  change in the manifest); `verify` and `tests/structure/test-upstream-skills.sh` fail on a hand edit. A rule that should
  change goes to the source's repository, not into the copy.
- A user who also installs the sources (`unslop@heydamir`, `humanizer@humanizer`) or another humanizer skill gets two
  skills for the same request; the README says so.

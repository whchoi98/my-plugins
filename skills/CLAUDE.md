# skills/

Shipped skills. Each directory is one skill, invoked as `/my-plugins:<name>`. This file sits directly in
`skills/`, so it is not part of any skill.

| Skill | Source | Entry points |
|---|---|---|
| `aws-blog-skills/` | aws-blog-skills 1.2.2 | SKILL.md, `references/` (rule files per step), `scripts/` (lint, structure, URL, diagram lib, render, package), `assets/templates/` |
| `aws-diagram/` | aws-diagrams 1.0.0 | SKILL.md, `scripts/find_icon.py`, `embed.py`, `build_bundle.py`, `assets/` (icon bundle) |
| `aws-diagram-design/` | aws-diagrams 1.0.0 | SKILL.md, `references/` (style guide, types, export, import), `scripts/` (self_check, verify-geometry, extractors), `assets/aws-icons/`, `assets/fonts/` |
| `kor-deslop/` | kor-writing 1.0.0 | SKILL.md, `references/patterns.md` (A~K, 79 patterns) |
| `aws-ppt-skills/` | aws-deck 1.0.0 | SKILL.md, `scripts/` (apply_template, check_deck, svg_to_png, install_fonts.sh), `assets/templates/`, `assets/fonts/` |
| `consulting-ppt-white-ppt/` | aws-deck 1.0.0 | SKILL.md, `lib/consult_helpers.js`, `tools/` (fix_pptx, fix_notes, extract_brand_color), `examples/` |
| `pptx-template-fill/` | aws-deck 1.0.0 | SKILL.md, `scripts/` (tfill, inventory, qa_check, swap_font) |
| `aws-reports/` | aws-reports 1.0.0 | SKILL.md (report type, then one procedure), `references/` (markdown-spec, style-rules, benchmark-structure, poc-structure, poc-verdict-rules), `scripts/` (report.mjs, check_report.py, chart_style.py, fonts.py, preview.py, svg2png.py, style_terms.json), `assets/examples/` (benchmark, poc) |
| `setup/` | new | SKILL.md, `scripts/setup.sh` (check, install, install --sudo) |

## Cross-skill links
- aws-blog-skills → `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`,
  `my-plugins:setup`; `scripts/diagram_lib.py` reads `../aws-diagram-design/assets` (fonts, icons)
- aws-ppt-skills → `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:setup`
- aws-reports → `my-plugins:aws-diagram` (architecture figures), `my-plugins:setup` (npm packages, fonts);
  `../aws-blog-skills/scripts/lint_prose.py` (prose check)
- setup → `../aws-diagram-design/assets/fonts/ttf` (Amazon Ember), `../aws-ppt-skills/scripts/install_fonts.sh`

## Rules
- Do not add `CLAUDE.md` or dev-only files inside `skills/<name>/`; everything there ships.
- Renaming or moving a skill breaks the relative links above and the `my-plugins:<name>` calls; update both
  and the README skill table.
- Trigger phrases of aws-blog-skills overlap with the claude.ai-synced `anthropic-skills:aws-blog-skills` and
  `blog-writing`; README explains how to turn the synced copies off.

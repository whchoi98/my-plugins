# NOTICE

my-plugins bundles five plugins by WooHyung Choi. Each part keeps the license of the plugin it came from.
Two skills, `ui-deslop` and `eng-deslop`, are copies of other authors' repositories and keep those authors' licenses.

| Part | Source | License |
|---|---|---|
| `skills/aws-blog-skills/` | github.com/whchoi98/aws-blog-skills 1.2.2 | MIT, [LICENSE](LICENSE) |
| `skills/kor-deslop/` | github.com/whchoi98/kor-writing 1.0.0 | MIT, [LICENSE](LICENSE). Patterns and rules are condensed from humanize-korean v2.3.2 (MIT): [third_party/NOTICE-kor-deslop.md](third_party/NOTICE-kor-deslop.md) |
| `skills/aws-diagram/`, `skills/aws-diagram-design/`, `commands/`, `scripts/diagrams/`, `docs/diagrams/` | github.com/whchoi98/aws-diagrams 1.0.0 | MIT, derived from cathrynlavery/diagram-design. `skills/aws-diagram-design/` and `commands/` are rebuilt from that repository at the commit `scripts/upstream-skills.json` records, by `scripts/upstream/aws-diagram-design/recipe.json` (AWS skin, AWS icons, edition rules): [third_party/LICENSE-aws-diagram-design](third_party/LICENSE-aws-diagram-design). AWS Architecture Icons, Amazon Ember and other icon sets follow their own terms: [third_party/THIRD_PARTY_LICENSES-aws-diagrams.md](third_party/THIRD_PARTY_LICENSES-aws-diagrams.md) |
| `skills/aws-ppt-skills/`, `skills/consulting-ppt-white-ppt/`, `skills/pptx-template-fill/` | github.com/whchoi98/aws-deck 1.0.0 | MIT, [LICENSE](LICENSE), chosen by the author when merging into my-plugins (the source repository had none). The bundled AWS PowerPoint templates (`skills/aws-ppt-skills/assets/templates/`), NanumSquareOTF and D2Coding fonts (`skills/aws-ppt-skills/assets/fonts/`) are not covered by the MIT license and follow their own terms |
| `skills/aws-reports/` | github.com/whchoi98/aws-reports 1.0.0 | MIT, [LICENSE](LICENSE), chosen by the author when merging into my-plugins (the source repository had none). No fonts are bundled: `setup` installs NanumSquareOTF from npm `@kfonts/nanum-square-otf` (OFL-1.1), and the HTML reports embed subsets of the installed NanumSquareOTF and D2Coding (both OFL-1.1) |
| `skills/html-report/` | this repository | MIT, [LICENSE](LICENSE). No fonts or images are bundled; pages name NanumSquareOTF_ac and D2Coding (OFL-1.1) in the font stack and use the reader's installed copies |
| `skills/techblogs/` | this repository (new; replaces the user-level techblogs skill) | MIT, [LICENSE](LICENSE). No fonts or images are bundled; pages name NanumSquareOTF_ac and D2Coding (OFL-1.1) in the font stack and use the reader's installed copies or the font files the blog serves |
| `skills/aws-infographic/` | this repository (new; replaces the author's claude.ai-synced aws-infographic skill) | MIT, [LICENSE](LICENSE). No fonts or icons are bundled: the infographics name NanumSquareOTF and D2Coding (OFL-1.1) in the font stack and embed AWS Architecture Icons from `skills/aws-diagram/assets/icons.json`, which keep the terms in [third_party/THIRD_PARTY_LICENSES-aws-diagrams.md](third_party/THIRD_PARTY_LICENSES-aws-diagrams.md) |
| `skills/ui-deslop/` | github.com/heydamir/unslop (`skills/unslop/`), "unslop" by Damir Sokolovsky | CC BY 4.0: [third_party/LICENSE-ui-deslop](third_party/LICENSE-ui-deslop). Not covered by the MIT license of this repository. Copied at the commit recorded in `scripts/upstream-skills.json` and in the `metadata` of its SKILL.md. Changes: the frontmatter name and description are replaced by my-plugins and the `agents/` folder is left out; every other byte is the source's, and the author's credit in SKILL.md and the reference files is kept |
| `skills/eng-deslop/` | github.com/blader/humanizer (`SKILL.md`), "Humanizer", Copyright (c) 2025 Siqi Chen | MIT: [third_party/LICENSE-eng-deslop](third_party/LICENSE-eng-deslop). Copied at the commit recorded in `scripts/upstream-skills.json` and in the `metadata` of its SKILL.md. Changes: the frontmatter name and description are replaced by my-plugins; the body is the source's |
| `skills/setup/`, repository harness | this repository | MIT, [LICENSE](LICENSE) |

Paths in the third-party files refer to the source repositories; in this repository the aws-diagrams
`LICENSE` is `third_party/LICENSE-aws-diagram-design` and the kor-writing `NOTICE.md` is
`third_party/NOTICE-kor-deslop.md`.

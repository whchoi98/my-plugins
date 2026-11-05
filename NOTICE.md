# NOTICE

my-plugins bundles five plugins by WooHyung Choi. Each part keeps the license of the plugin it came from.

| Part | Source | License |
|---|---|---|
| `skills/aws-blog-skills/` | github.com/whchoi98/aws-blog-skills 1.2.2 | MIT, [LICENSE](LICENSE) |
| `skills/kor-deslop/` | github.com/whchoi98/kor-writing 1.0.0 | MIT, [LICENSE](LICENSE). Patterns and rules are condensed from humanize-korean v2.3.2 (MIT): [third_party/NOTICE-kor-deslop.md](third_party/NOTICE-kor-deslop.md) |
| `skills/aws-diagram/`, `skills/aws-diagram-design/`, `commands/`, `scripts/diagrams/`, `docs/diagrams/` | github.com/whchoi98/aws-diagrams 1.0.0 | MIT, derived from cathrynlavery/diagram-design: [third_party/LICENSE-aws-diagram-design](third_party/LICENSE-aws-diagram-design). AWS Architecture Icons, Amazon Ember and other icon sets follow their own terms: [third_party/THIRD_PARTY_LICENSES-aws-diagrams.md](third_party/THIRD_PARTY_LICENSES-aws-diagrams.md) |
| `skills/aws-ppt-skills/`, `skills/consulting-ppt-white-ppt/`, `skills/pptx-template-fill/` | github.com/whchoi98/aws-deck 1.0.0 | MIT, [LICENSE](LICENSE), chosen by the author when merging into my-plugins (the source repository had none). The bundled AWS PowerPoint templates (`skills/aws-ppt-skills/assets/templates/`), NanumSquareOTF and D2Coding fonts (`skills/aws-ppt-skills/assets/fonts/`) are not covered by the MIT license and follow their own terms |
| `skills/aws-reports/` | github.com/whchoi98/aws-reports 1.0.0 | MIT, [LICENSE](LICENSE), chosen by the author when merging into my-plugins (the source repository had none). No fonts are bundled: `setup` installs NanumSquareOTF from npm `@kfonts/nanum-square-otf` (OFL-1.1), and the HTML reports embed subsets of the installed NanumSquareOTF and D2Coding (both OFL-1.1) |
| `skills/setup/`, repository harness | this repository | MIT, [LICENSE](LICENSE) |

Paths in the third-party files refer to the source repositories; in this repository the aws-diagrams
`LICENSE` is `third_party/LICENSE-aws-diagram-design` and the kor-writing `NOTICE.md` is
`third_party/NOTICE-kor-deslop.md`.

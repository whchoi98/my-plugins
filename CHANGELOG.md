# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.10.0] - 2026-11-24

### Added
- `aws-diagram-design`: rebuilt from cathrynlavery/diagram-design 2.6.174 (`0eeda75`, 2026-11-23) in place of the 2.3.2 it started from. The source's visual types go from 27 to 52 (heatmap, treemap, waterfall, Sankey, fishbone, kanban, user journey, service blueprint, deployment, dependency graph, UML class, database schema, git graph, steps, story map, Wardley map and others), with Excalidraw and PlantUML import, the packaged `export_svg.py`, `export_png.py` and `verify_geometry.py`, a plan stated before drawing, a render-and-look step and named profiles for custom skins
- Commands `/my-plugins:import-excalidraw` and `/my-plugins:import-plantuml`, and the three existing diagram commands rebuilt from the source's commands
- `skills/aws-diagram-design/scripts/aws_check.py`: the AWS edition's own check (no middle dot in SVG text, no font loaded from outside the file, a fallback on every Amazon Ember `font-family`)
- `scripts/sync_upstream_skills.py`: a `derived` mode that rebuilds a skill from its source by a recipe (`scripts/upstream/aws-diagram-design/recipe.json`: replacement steps, edits anchored on the source's text, tokens that may not survive, the edition's own files). `update` refuses before writing when the recipe does not apply, `verify` fails on a hand edit and on a recipe changed after the last update, `--pinned` rebuilds at the recorded commit and `--schedule` selects the weekly or the biweekly skills. Decision: ADR-009
- `.github/workflows/sync-aws-diagram-design.yml`: every second Monday the workflow rebuilds the skill. When the source changed it pushes the branch `sync/aws-diagram-design` and opens a pull request, or an issue when Actions may not open one or when the recipe no longer applies. It merges and releases nothing and runs no file of the source

### Changed
- `aws-diagram-design`: a custom skin is a profile under `~/.aws-diagram-design/profiles/`, bound to a project by a `.aws-diagram-design` marker, and the skill folder is read-only. A project folder `.aws-diagram-design/style-guide.md` from an earlier version is still read
- `aws-diagram-design`: fonts follow the source's `system` mode. A diagram names the installed Amazon Ember faces and carries no font `<link>`, `@import` or `@font-face` with a file path, because the source's `self_check.py` rejects CSS `url()`. `assets/fonts/README.md` gives a `local()`-only block
- `aws-diagram-design`: the style guide follows the structure of the source's (the `ink-strong` role, the contrast contract, the font source, Korean, Chinese and Cyrillic labels) and states the measured contrast of the AWS skin: in the light skin `accent` (3.01:1) and `soft` (3.56:1) are for marks and large text, not for small text. The colors did not change
- `aws-diagram-design`: the separator check moved from `self_check.py`, which is the source's file again, to `aws_check.py`; the skill's own `scripts/verify-geometry.py` gave way to the source's `verify_geometry.py`
- The weekly workflow runs `update --schedule weekly`, so it leaves aws-diagram-design to the workflow above
- `techblogs`: a newly written post stays within a reading time of 15 minutes, so that it is easy to understand and to read. A longer post is cut first (the same number in a table and a figure, repeated sentences, settings the claim does not need) and, if it is still longer, split into a series whose parts each stay within 15 minutes. SKILL.md settles the length with the scope (step 0), has the rule in step 2 and does not keep the warning in a new post (step 5); `references/storylines.md` and `references/design-spec.md` name it. `scripts/check_post.py` warns when the Korean body reads in more than 15 minutes (characters outside code boxes divided by 700, the number `build_post.py` shows; `minutes` written by hand in meta.json does not change it; republished posts are not checked) and `scripts/new_post.py` prints the limit. A post from before the rule is cut or split only when the user asks

## [1.9.1] - 2026-11-22

### Changed
- `aws-blog-skills`, `techblogs`, `kor-deslop`: write "트레이드 오프가 있다" for "대가가 있다" (something gained comes with something lost). `references/style.md` has the row, `lint_prose.py` flags every form as HARD, `check_post.py` warns in a techblogs page (table cells and headings included) and kor-deslop D-9 lists the phrase. "시간대가 있다" and "기대가 있다", where 대가 ends another word, are left alone

## [1.9.0] - 2026-11-22

### Changed
- `techblogs`: a newly written post opens with a background paragraph. The first paragraph of the first section tells the background of the topic or why it is needed in one or two sentences, in plain words, and the storyline's opening follows it. `references/storylines.md` has the rule (place, length, what to write and what to leave out, a worked example) and one `배경 문단` line per storyline; `scripts/new_post.py` puts the place of the paragraph with that line into the first section of both bodies; `scripts/check_post.py` warns when the first section of a new post does not start with a paragraph or when its Korean first paragraph has three sentences or more (republished posts are not checked; posts from before the rule are changed only when the user asks). SKILL.md settles the background or the need with the scope (step 0), writes the paragraph in step 2 and keeps it through polishing (step 3)

## [1.8.0] - 2026-11-22

### Added
- `ui-deslop`: new skill that removes AI slop from UI, vendored from [heydamir/unslop](https://github.com/heydamir/unslop) (CC BY 4.0, by Damir Sokolovsky) at `620163e`. It lists the tells of an AI-made screen, sets a direction from the product and fixes spacing, color, icons, copy, type, layout, details, visuals and motion. Only the frontmatter `name` and description are ours, and the source's `agents/` folder is left out
- `eng-deslop`: new skill that removes AI slop from English text, vendored from [blader/humanizer](https://github.com/blader/humanizer) (MIT, Copyright (c) 2025 Siqi Chen) at `a32f244` (Humanizer 4.0.0, 26 patterns). Only the frontmatter `name` and description are ours
- `scripts/sync_upstream_skills.py` and `scripts/upstream-skills.json`: the vendored skills are pinned to a commit with a hash of every file. `check` compares them with their sources, `update` copies a changed source in and writes the frontmatter, the license copy, the manifest and the `[Unreleased]` line, `render` writes a changed description, `verify` fails on a hand edit. `update` refuses a changed license, a symbolic link, a hidden file, a file type outside `allow_ext`, an unusual file name and a file over 2 MB
- `.github/workflows/sync-upstream-skills.yml`: every Monday the workflow runs `update`. When a source changed it pushes the branch `sync/upstream-skills` and opens a pull request, or an issue when Actions may not open one. It merges and releases nothing. Decision in ADR-008, steps in `docs/runbooks/sync-upstream-skills.md`. 230 tests added
- `setup`: reports ffmpeg, which `ui-deslop` uses for its optional story video, without counting it as missing

### Changed
- `kor-deslop`: the description sends English text to `eng-deslop` and a screen to `ui-deslop`

## [1.7.0] - 2026-11-21

### Added
- `aws-ppt-skills`: HTML deck. The skill asks the output format first (`PPT만`, `HTML만`, `PPT와 HTML 둘 다`). `scripts/deck_to_html.py` converts the finished `.pptx` into one self-contained `.html` presented in a browser: text, shapes and tables as HTML at the deck's coordinates, charts as SVG drawn from the chart data, diagrams as their vector SVG, the template background, logo and page numbers as pictures rendered from the template, subset fonts, and the notes for a presenter view. The page (`assets/html/deck.css`, `deck.js`) has keyboard navigation, a presenter window with the notes, the next slide and a timer (`N`), a slide list (`G`), a laser pointer (`P`), a blank screen (`B`), fullscreen (`F`) and a one-slide-per-page print layout for a PDF backup. `--no-notes` leaves the notes out of a page that will be published. `scripts/preview_html_deck.py` screenshots every slide, the list and the presenter view in Chromium and fails when the keys, the presenter window or the fonts do not work. `references/html-deck.md` holds the options, warnings, limits and the presenter guide. Decision in ADR-007. 155 tests added
- `setup`: checks and installs fonttools (`pip install --user`), which `deck_to_html.py` uses to embed only the characters a deck needs
- `aws-blog-skills`, `techblogs`, `kor-deslop`: word rule confirmed on 2026-11-18. A part of a text is written "챕터" or "장", not "절", and "비교하다" replaces "견주다". `style.md` lists both words. `lint_prose.py` reports them as HARD findings: "절" as a word of its own, with or without a particle, and every form of "견주다". Compounds such as 절차 and 절반, grammar terms such as 관형절, and an SQL clause after an English word ("WHERE 절") are left out. `check_post.py` warns about both words in every text node, tables and headings included. kor-deslop gains pattern D-9 (81 patterns). 38 tests added

### Changed
- `aws-blog-skills`: `lint_prose.py` counts "이 챕터에서는" as a heading guide sentence (C-6) and reports a numbered reference with 챕터 ("챕터 3에서", "2챕터의") as a section-number reference, like "3.1절"
- `techblogs`, `html-report`, `kor-deslop`, `aws-blog-skills`: the skills' own documents and script messages (`check_post.py`, `build_post.py`, `new_post.py`, `check_html.py`), the storyline label ("챕터 흐름") and the sample text of the html-report template say "챕터". html-report follows because its Korean text runs through the same `lint_prose.py`. The `<style>` and `<script>` of both templates are unchanged, so published pages still pass their checks

### Fixed
- `tests/run-all.sh`: `assert_contains` and `assert_not_contains` compare inside the shell. Under `pipefail`, `printf | grep -q` failed by SIGPIPE when grep exited on an early match in a long text, so a correct check could fail at random and `assert_not_contains` could pass when it had to fail

## [1.6.0] - 2026-11-18

### Added
- `aws-infographic`: new skill, moved into the plugin from the author's claude.ai skill of the same name. It makes fact-checked technical infographics in the AWS palette: per page a 16:9 dark and light SVG with embedded icons and a 2x PNG, and 4:5 on request. The code the old SKILL.md carried as pasted blocks now ships as files (`scripts/infokit.py`, `scripts/buildkit.py`, `assets/page_template.py`) and is copied into the work folder. `infokit.py` finds the aws-diagram icon bundle (`AWS_ICON_BUNDLE`, a `.aws-icon-bundle` file next to the copy, the sibling skill, installed copies) and the fonts by file name (`INFOKIT_FONTS`, fontconfig, the user font folders); Pillow and Playwright are imported only where they are used. The drawing API is unchanged, so page modules written for the earlier skill build the same SVG
- `aws-infographic`: step 9 makes an editable PowerPoint deck of the same content through `my-plugins:aws-ppt-skills`. The infographic's SVG or PNG never goes on a slide. Each section becomes one content slide rebuilt from text boxes, shapes, PowerPoint tables, native charts and AWS icon PNGs, with the wording taken from the page module's `T` dict. `references/ppt-deck.md` holds the content mapping, the helpers `addGrid()`, `addSteps()`, `addIconRow()` and `addLanes()`, and an example deck for the page template. `scripts/icon_png.py` exports bundle icons as PNG, and `scripts/check_editable.py` fails a deck that links an SVG, holds a picture that is not an icon, or holds an icon larger than 1.2 in ([ADR-006](docs/decisions/ADR-006-infographic-editable-deck.md)). 163 tests added

### Changed
- `aws-ppt-skills`: `addIcon()` places an AWS icon as one small PNG picture named `icon:<set/name>`, and `check_deck.py` no longer asks such a picture (up to 1.2 in) for a vector SVG. "Charts and Diagrams" says how an editable deck is built: no `addDiagram()`, no SVG, and `check_editable.py` at the end
- `setup`: the render group of the check names aws-infographic, which uses the same tools and fonts. Nothing new is installed

## [1.5.2] - 2026-11-17

### Changed
- `aws-blog-skills`: "Changelog" is written in English. The banned-word table in `references/style.md` lists its translations "변경 기록" and "변경기록" (the document that records what changed in each version) with `Changelog` as the word to write, without a translation in parentheses; a sentence about something else, such as an audit log, says "변경 내역" or "변경을 기록한다". `lint_prose.py` reports both spellings as HARD findings, so techblogs, html-report and aws-reports, which run the same check, follow the rule too (confirmed 2026-11-17). 9 tests added
- `techblogs`: `check_post.py` warns about "변경 기록" and "변경기록" anywhere in the page text, including the tables, captions and source kind names that `lint_prose.py` does not read, and names `Changelog` as the word to write. SKILL.md step 3 and the text rules of `references/design-spec.md` state the rule; it also covers `note` and the `kind` of `sources` in `meta.json`. 8 tests added
- `kor-deslop`: `Changelog` joins the English terms the polish leaves untouched, and SKILL.md says not to turn it into "변경 기록". 2 tests added

## [1.5.1] - 2026-11-17

### Changed
- `techblogs`: the report page fits its title on one line. The title of the visible language shrinks until it fits (not below 30px; a title that is still too long wraps at 30px) and is fitted again on resize and on a language switch (`fitTitle` in `assets/template.html`, `h1.one`). SKILL.md step 0 and design-spec.md say to keep a new title to one line (about 45 Korean characters at 44px in a 1440px-wide window). Posts built with an earlier template need a rebuild to get it. 3 tests added

## [1.5.0] - 2026-11-16

### Added
- `techblogs`: a new post follows a storyline chosen for its material instead of one fixed skeleton. `references/storylines.md` describes eight of them (`qa`, `troubleshoot`, `measure`, `compare`, `build`, `anatomy`, `change`, `retro`), each with its section flow, how it opens and closes, where the analogy and the figures go, and what to avoid. SKILL.md step 0 picks one (and looks at the last three posts so that the opening and the closing do not repeat), step 2 orders the sections by it, the first section no longer repeats the conclusion list of the head, and the first and last sections are no longer titled "들어가며" and "마치며" by default. `meta.json` takes a `storyline` key: `build_post.py` rejects an unknown value and warns when a new post has none; republished posts keep the structure of the original. Sixteen tests cover the rule
- `techblogs`: `scripts/new_post.py` starts a new post from the storyline template chosen for its topic and material. `--list` prints every storyline with the material it fits and the signals to look for; `<work-dir> --storyline KEY --slug NAME` writes `meta.json` and both body fragments with one empty section per step of that storyline's section flow, read from `references/storylines.md`, each with a guide comment. `build_post.py` refuses to build while a template `TODO` or guide comment remains. `storylines.md` gains the signals to look for in the topic and the material and rules for material that fits two storylines. Seventy-one tests cover it

## [1.4.2] - 2026-11-15

### Added
- `techblogs`: a newly written post explains its core concept with an analogy to a familiar situation (SKILL.md step 2, with a worked example). The analogy covers every item being compared, maps their differences onto roles in the situation, never replaces the facts, and is carried into the English body; decorative figures of speech stay banned, republished posts get none, and polishing keeps the analogy. Three tests cover the rule

## [1.4.1] - 2026-11-15

### Changed
- `techblogs`: a figure with text in it gets an English version, `<name>-en.<ext>`, that the English body points to, so the figure changes with the language switch. `check_post.py` accepts the same file or its English version on the English side (it used to require the same file); SKILL.md and design-spec.md describe the rule, and two tests cover it

## [1.4.0] - 2026-11-15

### Added
- `html-report` skill: one shareable HTML page in a common report design. Korean and English sit in one file behind a language switch; light and dark themes start from the system setting; one column up to 1440px; NanumSquareOTF_ac and D2Coding; white boxes for tables and figures with "그림 N." captions; superscript citations; rounded status pills; and a fixed page order (top bar, head, sections, source table, method, sharing line). `data-report="research"` makes the source parts required, `general` keeps them optional
- `scripts/check_html.py`: a `<style>` or `<script>` that differs from the template, inline `style`, tokens, page order, language pairs, Korean outside its pair, banned symbols (·, —, –, →) in text and in the tab title, `alt` and `aria-label`, caption numbers, citations against the source table, source-mix counts, relative images, and template sample sentences (read from the template itself) are ERRORs; 한다체 or 해요체 sentences, "~하세요" and an uncited source are WARNs; `--dump-ko` hands the Korean text to aws-blog-skills `lint_prose.py`
- `scripts/embed_images.py` (images as data URIs, only files inside the page folder) and `scripts/preview.py` (four views: 1440 and 390 px, light Korean and dark English; warns when the buttons do not switch the page; retries with the system `node` when Playwright's bundled Node.js does not start, as on hosts without `libatomic.so.1`)
- `tests/structure/test-html-report.sh` and ADR-004
- `techblogs` skill: the workflow for a post on the author's personal tech blog (whchoi98.github.io, Jekyll), from source material to a placed and built post. It has the same steps as aws-blog-skills (fact check with every URL verified, Korean text, AI-tell removal, figures, rule registration) and another destination: a bilingual report page (`<slug>-report.html`), a front matter file (`<slug>.md`) and an image folder (`<slug>-assets/`). The page design is fixed: one column up to 1440px, NanumSquareOTF_ac and D2Coding, light and dark themes, a language switch, a sideways section menu and code boxes with a copy button. It replaces the user-level techblogs skill
- `scripts/build_post.py` fills `assets/template.html` from the work folder (`meta.json`, `ko.body.html`, `en.body.html`, `images/`) and stops on a `"TODO"`, a missing English fragment, a missing image or an `--out` inside the skill folder; `scripts/check_post.py` reports a `<style>` or `<script>` that differs from the template, different component counts in the two languages, caption numbers, missing image files, banned symbols (·, —, –), inline `style` and front matter errors as ERRORs, and writes the Korean text (`--dump-ko`) and the links (`--urls`) for aws-blog-skills `lint_prose.py` and `check_urls.py`
- `scripts/import_aws_post.py` (a published AWS blog post, from its address or a saved page, into a work folder; fetches only from the AWS blog hosts), `scripts/place_post.py` (copies a built post into the blog repository, checks it there, builds the site with `--build`, never runs git) and `scripts/preview.py` (Playwright screenshots of the report page and of the post page that embeds it)
- `import_aws_post.py` takes pictures wherever they sit (alone in a paragraph, at the end of a text paragraph, inline as base64), drops editor placeholder images, keeps the note after a reference link, writes root-relative links with the locale of the page, drops links that are not http(s), keeps a figure in the body when its file could not be fetched, and ends with the share of the article text it carried over (`coverage`) and every block it left out
- `check_post.py` also flags banned symbols in image `alt` text and in the excerpt and a Korean copy button on the English side; `--dump-ko` also writes the excerpt, the masthead facts and the closing note, so they pass through `lint_prose.py`; `build_post.py` empties the assets folder before it copies the images
- `tests/structure/test-techblogs.sh`, `tests/fixtures/techblogs/` and ADR-005

### Changed
- The aws-reports description sends HTML-only reports to `my-plugins:html-report`
- The aws-blog-skills description sends posts for the author's personal blog to `my-plugins:techblogs`
- Token cost table in `docs/reference/agent-llm.md` measured again (2026-11-15)

## [1.3.0] - 2026-11-11

### Added
- kor-deslop pattern D-8 (S1): the jargon-sounding nouns AI text favors, "실측" (실측 결과, 실측값), "축" (세 가지 축, 평가 축) and "레버" (비용 레버, 레버를 당기다), are replaced with 측정 / 측정값, 기준 / 관점 / 방향 / 측면, and 해법 / 수단 / 방법. Chart axes (x축, y축), physical axles and levers, and compounds such as 축소, 압축, 구축, 단축, 축적 are left alone. SKILL.md does not treat these words as content anchors. The pattern count is now 80
- aws-blog-skills: "실측" is a banned word in `style.md` and a HARD finding in `lint_prose.py` (2026-11-11). `style.md` now lists the "축" rule that `lint_prose.py` already enforced, and 레버 may become 해법, 수단 or 방법
- aws-reports: `style_terms.json` and `style-rules.md` flag "실측", "축" and "레버" in every report type. The PoC example says 측정한 입력·출력 토큰 instead of 실측 입력·출력 토큰

### Fixed
- The "축" check in aws-blog-skills `lint_prose.py` (a HARD finding) flagged chart axes and unrelated words: x축, y축, 가로축, 세로축, 건축, 저축, 축약, 축하. It now flags only 축 as a standalone word (두 축, 평가 축) and the joined forms 평가축, 핵심축, 중심축; aws-reports uses the same pattern. Tests cover both sides

## [1.2.1] - 2026-11-05

### Fixed
- `setup.sh` check mode printed no version for docx and docx-preview: their `package.json` uses a 4-space indent and CRLF line endings. `pkg_version()` reads the version whatever the indent or line ending, with a test for both formats

## [1.2.0] - 2026-11-05

### Added
- `aws-reports` skill, merged from github.com/whchoi98/aws-reports 1.0.0 as one skill with two report types: benchmark reports (setup and method first, overall verdict and recommendations last) and PoC result reports (success criteria with the fixed verdict words 충족 / 부분 충족 / 미충족 / 측정하지 않음, an overall decision 진행 / 조건부 진행 / 보류, issues, cost and next steps). One Markdown draft builds an MS Word file and a standalone HTML file in the same style
- `scripts/check_report.py --profile benchmark|poc`: page, font, caption, box, table-header and caption-note checks, wording terms from `style_terms.json`, and per-profile structure and verdict checks
- `scripts/chart_style.py` `criteria()`: each success criterion against its target, colored by verdict, with a legend and the verdict word
- `setup` checks and installs the aws-reports dependencies: docx 9.15.1, marked 18.1.1, docx-preview 0.4.1 and jszip 3.10.1 (`npm install -g`), and NanumSquareOTF Regular and Bold from npm `@kfonts/nanum-square-otf` 0.2.0 through `npm pack`
- `tests/structure/test-aws-reports.sh`, and ADR-003 (one report skill, npm packages from the global folder)

### Changed
- `report.mjs` finds npm packages in a local `node_modules`, then `NODE_PATH`, then `npm root -g`, because ES module imports do not read `NODE_PATH`; `preview.py` finds the docx-preview and jszip bundles the same way. Nothing is written into the skill folder: chart scripts run with `python -B` and the examples' `make_charts.py` write to `./charts` or a given folder
- Report layout rules from the user's 2026-11-04 Word edits: a table header that does not fit on one line puts its trailing unit on a second line and centers every header cell of that table; caption notes are centered on one line and left-aligned when they wrap; tables with 8-9 columns use 7.5/7 pt and 10+ columns 6.5 pt; the box title "고객 권고" is "권고"

## [1.1.0] - 2026-11-04

### Changed
- aws-diagram-design type sizes: node names 13px, sublabels 11px, arrow labels, legend text and notes 10px (were 12 / 9 / 8px), so labels stay readable when a README scales the exported PNG; label masks are 14px tall
- aws-diagram-design service icons sit on the title row (`Y+16`) at every node height instead of being centered in tall nodes
- Replace the middle dot `·` inside SVG `<text>` in 77 aws-diagram-design examples and references with commas (412 places), so the examples no longer teach it

### Added
- aws-diagram-design separator rule (style-guide.md § Separators): no `·` in visible text; `/` for pairs, commas for lists; Mermaid steps numbered `1: ` because `1. ` renders as a Markdown list
- aws-diagram-design text-fit rule: size boxes from the longest sublabel (Amazon Ember Mono about 0.63em per Latin glyph, Hangul about 1em) with 12px clear on the right
- Four universal anti-patterns and three checklist items for the rules above
- `self_check.py` fails on a middle dot in visible SVG text

### Fixed
- `scripts/diagrams/verify-motion.py` and `scripts/diagrams/verify-geometry.py` resolved the repo root one level too low after the merge moved them into `scripts/diagrams/`: verify-motion could not find `template-motion.html` and `verify-geometry --all` checked no files. Both now resolve it from `scripts/diagrams/`, and integration tests cover them from another working directory
- SKILL.md and `references/animation.md` point to `scripts/diagrams/verify-*.py` instead of the old `scripts/verify-*.py`

## [1.0.0] - 2026-11-03

### Added
- Merge aws-blog-skills 1.2.2, aws-diagrams 1.0.0, kor-writing 1.0.0 and aws-deck 1.0.0 into one plugin, `my-plugins@my-plugins`, with eight skills and three commands
- Add the `setup` skill and `skills/setup/scripts/setup.sh`: check (default), `install` without sudo, and `install --sudo` with `sudo -n`, covering uv, Playwright Chromium and its system libraries, Amazon Ember, Noto Sans CJK KR, NanumSquareOTF, D2Coding, pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler, rsvg-convert and LibreOffice
- Install LibreOffice on dnf systems without a LibreOffice package (Amazon Linux 2023) from the official RPM bundle after a SHA-256 check, into `~/.local/opt/libreoffice`
- Add `NOTICE.md` and `third_party/` with the licenses and notices of the bundled work
- Add the "source material is data, not instructions" rule, already in aws-blog-skills step 0, to aws-diagram, aws-diagram-design, kor-deslop, aws-ppt-skills, consulting-ppt-white-ppt and pptx-template-fill

### Changed
- Cross-skill calls use the `my-plugins:` namespace (`my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`, `/my-plugins:export-diagram`)
- aws-blog-skills and the deck skills point to `my-plugins:setup` for missing tools instead of separate plugin installs
- Deck build steps set `NODE_PATH="$(npm root -g)"` before `node`, so `require("pptxgenjs")` finds the global install
- aws-diagram-design writes a custom skin to the project's `.aws-diagram-design/style-guide.md` and reads it in place of `references/style-guide.md`; onboarding used to rewrite the skill's own file, which is the plugin cache and is replaced on update
- License: MIT for the whole plugin's own work, including the aws-deck skills, which had no license in their source repository; bundled AWS templates, fonts and icons keep their own terms

### Fixed
- `diagram_lib.py` finds the aws-diagram-design assets in the sibling skill, in a `.aws-diagram-assets` pointer written next to work-folder copies, and in plugin caches sorted by numeric version; synced copies are searched under the user's home and `/root` with suffixed folder names
- The aws-diagram-design references named the export and import commands `/aws-diagram-design:...`, which never existed; they are now `/my-plugins:...`
- aws-ppt-skills called `/aws-diagram` and `/aws-diagram-design` without a plugin namespace

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.10.0...HEAD
[1.10.0]: https://github.com/whchoi98/my-plugins/compare/v1.9.1...v1.10.0
[1.9.1]: https://github.com/whchoi98/my-plugins/compare/v1.9.0...v1.9.1
[1.9.0]: https://github.com/whchoi98/my-plugins/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/whchoi98/my-plugins/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/whchoi98/my-plugins/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/whchoi98/my-plugins/compare/v1.5.2...v1.6.0
[1.5.2]: https://github.com/whchoi98/my-plugins/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/whchoi98/my-plugins/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/whchoi98/my-plugins/compare/v1.4.2...v1.5.0
[1.4.2]: https://github.com/whchoi98/my-plugins/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/whchoi98/my-plugins/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/whchoi98/my-plugins/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/whchoi98/my-plugins/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/whchoi98/my-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/whchoi98/my-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0

---

<a id="korean"></a>

# 한국어

이 프로젝트의 주요 변경 사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고,
버전은 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

## [1.10.0] - 2026-11-24

### Added
- `aws-diagram-design`: 처음 가져온 2.3.2 대신 cathrynlavery/diagram-design 2.6.174(`0eeda75`, 2026-11-23)에서 다시 만듦. 원본의 시각 유형이 27가지에서 52가지로 늘어남(히트맵, 트리맵, 워터폴, Sankey, 피시본, 칸반, 사용자 여정, 서비스 블루프린트, 배포, 의존 그래프, UML 클래스, 데이터베이스 스키마, git 그래프, 단계, 스토리 맵, Wardley 맵 등). Excalidraw와 PlantUML 가져오기, 함께 배포되는 `export_svg.py`, `export_png.py`, `verify_geometry.py`, 그리기 전 계획 제시, 렌더해서 확인하는 단계, 사용자 스킨용 프로필 추가
- command `/my-plugins:import-excalidraw`, `/my-plugins:import-plantuml` 추가. 기존 다이어그램 command 3개도 원본의 command에서 다시 만듦
- `skills/aws-diagram-design/scripts/aws_check.py` 추가. AWS 판이 따로 두는 검사(SVG 텍스트의 가운뎃점, 파일 밖에서 불러오는 글꼴, 대체 글꼴이 없는 Amazon Ember `font-family`)
- `scripts/sync_upstream_skills.py`에 `derived` 방식 추가. 변환 규칙(`scripts/upstream/aws-diagram-design/recipe.json`: 치환 단계, 원본 문장을 기준으로 한 편집, 남으면 안 되는 토큰, AWS 판의 파일)으로 skill을 원본에서 다시 만듦. 변환 규칙이 맞지 않으면 `update`가 쓰기 전에 거부하고, 손으로 수정한 파일이나 마지막 업데이트 뒤에 바뀐 변환 규칙이 있으면 `verify`가 실패함. `--pinned`는 기록한 커밋에서 다시 만들고 `--schedule`은 주간 또는 격주 skill을 고름. 결정은 ADR-009
- `.github/workflows/sync-aws-diagram-design.yml` 추가. 2주에 한 번 월요일에 skill을 다시 만들고, 원본이 바뀌었으면 `sync/aws-diagram-design` 브랜치를 push한 뒤 pull request를 엶(Actions가 열 수 없거나 변환 규칙이 더 맞지 않으면 issue). 병합과 릴리스는 하지 않고 원본의 파일을 실행하지 않음

### Changed
- `aws-diagram-design`: 사용자 스킨을 `~/.aws-diagram-design/profiles/`의 프로필로 두고 `.aws-diagram-design` 마커로 프로젝트에 연결함. skill 폴더는 읽기 전용. 이전 버전이 만든 프로젝트 폴더 `.aws-diagram-design/style-guide.md`도 계속 읽음
- `aws-diagram-design`: 글꼴을 원본의 `system` 방식으로 변경. 다이어그램은 설치된 Amazon Ember의 이름만 적고 글꼴 `<link>`, `@import`, 파일 경로가 든 `@font-face`를 넣지 않음. 원본의 `self_check.py`가 CSS `url()`을 거부하기 때문. `assets/fonts/README.md`의 블록도 `local()`만 사용
- `aws-diagram-design`: 스타일 가이드를 원본의 구조(`ink-strong` 역할, 대비 기준, 글꼴 출처, 한국어와 중국어, 키릴 문자 레이블)에 맞추고 AWS 스킨의 대비 측정값을 적음. 밝은 스킨의 `accent`(3.01:1)와 `soft`(3.56:1)는 표시와 큰 글자에만 쓰고 작은 글자에는 쓰지 않음. 색은 바꾸지 않음
- `aws-diagram-design`: 구분 기호 검사를 원본의 파일로 되돌린 `self_check.py`에서 `aws_check.py`로 옮김. skill의 `scripts/verify-geometry.py`는 원본의 `verify_geometry.py`로 대체
- 주간 워크플로가 `update --schedule weekly`를 실행하여 aws-diagram-design은 위 워크플로에 맡김
- `techblogs`: 새로 쓰는 글은 이해하기 쉽고 읽기 편하도록 읽는 시간 15분 이하로 씀. 넘으면 먼저 겹치는 내용(표와 그림의 같은 수치, 되풀이하는 문장, 주장과 관계없는 세부 설정)을 줄이고, 그래도 넘으면 편마다 15분 이하인 연재로 나눔. SKILL.md는 0단계에서 분량을 정하고 2단계에 규칙을 두며 5단계에서 새 글에 경고를 남기지 않음. `references/storylines.md`와 `references/design-spec.md`에 같은 규칙 추가. `scripts/check_post.py`는 한국어 본문의 읽는 시간이 15분을 넘으면 경고(코드 상자를 뺀 글자 수를 700으로 나눈 값으로 `build_post.py`가 표시하는 값과 같음, meta.json에 직접 적은 `minutes`로 바뀌지 않음, 옮겨 싣는 글은 검사하지 않음). `scripts/new_post.py`는 한도를 출력. 규칙 전에 올린 글은 사용자가 요청할 때만 줄이거나 나눔

## [1.9.1] - 2026-11-22

### Changed
- `aws-blog-skills`, `techblogs`, `kor-deslop`: 얻는 것과 잃는 것이 함께 있다는 뜻의 "대가가 있다"를 "트레이드 오프가 있다"로 씀. `references/style.md`에 행 추가, `lint_prose.py`는 활용형을 모두 HARD로 잡음, `check_post.py`는 techblogs 페이지에서 경고(표와 제목 포함), kor-deslop D-9에 표현 추가. "시간대가 있다", "기대가 있다"처럼 앞 낱말에 붙은 것은 제외

## [1.9.0] - 2026-11-22

### Changed
- `techblogs`: 새로 쓰는 글이 배경 문단으로 시작. 첫 챕터의 첫 문단에 주제의 배경이나 필요를 한두 문장의 평이한 말로 쓰고 스토리라인의 여는 방식은 그 다음에 씀. `references/storylines.md`에 규칙(자리, 길이, 쓸 내용과 쓰지 않는 것, 예)과 스토리라인마다 `배경 문단` 줄을 추가. `scripts/new_post.py`가 두 본문의 첫 챕터에 그 줄과 함께 배경 문단 자리를 넣음. `scripts/check_post.py`는 새 글의 첫 챕터가 문단으로 시작하지 않거나 한국어 첫 문단이 세 문장 이상이면 경고(옮겨 싣는 글은 보지 않고, 규칙 전에 올린 글은 사용자가 요청할 때만 수정). SKILL.md는 0단계에서 배경이나 필요를 범위와 함께 정하고 2단계에서 문단을 쓰며 3단계 윤문에서 지우지 않음

## [1.8.0] - 2026-11-22

### Added
- `ui-deslop`: UI의 AI 슬롭을 제거하는 skill 추가. [heydamir/unslop](https://github.com/heydamir/unslop)(CC BY 4.0, Damir Sokolovsky)을 `620163e`에서 가져옴. AI가 만든 화면의 흔적을 찾아 보여 주고, 제품에서 방향을 정한 뒤 간격, 색, 아이콘, 문구, 글꼴, 레이아웃, 세부, 그림, 모션을 수정. frontmatter의 `name`과 description만 이 플러그인의 것이며 원본의 `agents/` 폴더는 제외
- `eng-deslop`: 영어 글의 AI 슬롭을 제거하는 skill 추가. [blader/humanizer](https://github.com/blader/humanizer)(MIT, Copyright (c) 2025 Siqi Chen)를 `a32f244`(Humanizer 4.0.0, 패턴 26개)에서 가져옴. frontmatter의 `name`과 description만 이 플러그인의 것
- `scripts/sync_upstream_skills.py`와 `scripts/upstream-skills.json` 추가. 가져온 skill을 커밋과 파일별 해시로 고정. `check`는 원본과 비교, `update`는 바뀐 원본을 복사하고 frontmatter, 라이선스 사본, 매니페스트, `[Unreleased]` 줄을 작성, `render`는 바꾼 description을 반영, `verify`는 손으로 수정한 파일이 있으면 실패. `update`는 바뀐 라이선스, 심볼릭 링크, 숨김 파일, `allow_ext`에 없는 파일 형식, 특이한 파일 이름, 2 MB를 넘는 파일을 거부
- `.github/workflows/sync-upstream-skills.yml` 추가. 매주 월요일 `update`를 실행하고, 원본이 바뀌었으면 `sync/upstream-skills` 브랜치를 push한 뒤 pull request를 엶(Actions가 열 수 없으면 issue). 병합과 릴리스는 하지 않음. 결정은 ADR-008, 절차는 `docs/runbooks/sync-upstream-skills.md`. 테스트 230개 추가
- `setup`: `ui-deslop`의 선택 기능인 스토리 영상에 쓰는 ffmpeg가 있는지 알림. 빠진 항목으로 세지 않음

### Changed
- `kor-deslop`: description이 영어 글은 `eng-deslop`으로, 화면은 `ui-deslop`으로 안내

## [1.7.0] - 2026-11-21

### Added
- `aws-ppt-skills`: HTML 덱 추가. 출력 형식(`PPT만`, `HTML만`, `PPT와 HTML 둘 다`)을 가장 먼저 물음. `scripts/deck_to_html.py`가 완성한 `.pptx`를 브라우저에서 발표하는 한 파일짜리 `.html`로 변환. 글자, 도형, 표는 덱의 좌표 그대로 HTML로, 차트는 차트 데이터에서 그린 SVG로, 다이어그램은 벡터 SVG로, 템플릿의 배경, 로고, 쪽 번호는 템플릿에서 렌더한 그림으로 넣고, 글꼴은 쓰인 글자만 포함하며, 노트는 발표자 보기에 표시. 페이지(`assets/html/deck.css`, `deck.js`)는 키보드 이동, 노트와 다음 슬라이드와 시간이 나오는 발표자 창(`N`), 슬라이드 목록(`G`), 레이저 포인터(`P`), 화면 가리기(`B`), 전체 화면(`F`), 슬라이드 한 장이 한 쪽인 인쇄 배치(PDF 백업)를 제공. `--no-notes`는 게시할 페이지에서 노트를 뺌. `scripts/preview_html_deck.py`가 Chromium에서 슬라이드, 목록, 발표자 보기를 캡처하고 키, 발표자 창, 글꼴이 동작하지 않으면 실패. `references/html-deck.md`에 옵션, 경고, 한계, 발표자 안내 수록. 결정은 ADR-007. 테스트 155개 추가
- `setup`: fonttools 점검과 설치(`pip install --user`) 추가. `deck_to_html.py`가 덱에 쓰인 글자만 글꼴로 넣는 데 사용
- `aws-blog-skills`, `techblogs`, `kor-deslop`: 2026-11-18에 확정한 낱말 규칙 추가. 글의 한 부분은 "절"이 아니라 "챕터"나 "장"으로, "견주다"는 "비교하다"로 씀. `style.md`에 두 낱말을 올림. `lint_prose.py`가 HARD로 잡음(조사가 붙거나 붙지 않은 낱말 "절", "견주다"의 모든 활용형). 절차, 절반 같은 합성어, 관형절 같은 문법 용어, 영어 낱말 뒤의 SQL 절("WHERE 절")은 제외. `check_post.py`가 표와 제목을 포함한 모든 글에서 두 낱말을 WARN으로 알림. kor-deslop에 패턴 D-9 추가(패턴 81개). 테스트 38개 추가

### Changed
- `aws-blog-skills`: `lint_prose.py`가 "이 챕터에서는"을 헤딩 아래 안내문(C-6)으로 세고, 번호를 붙여 가리키는 챕터("챕터 3에서", "2챕터의")를 "3.1절"과 같은 섹션 번호 참조로 잡음
- `techblogs`, `html-report`, `kor-deslop`, `aws-blog-skills`: skill 문서와 스크립트 메시지(`check_post.py`, `build_post.py`, `new_post.py`, `check_html.py`), 스토리라인 항목 이름("챕터 흐름"), html-report 템플릿의 예시 문장을 "챕터"로 바꿈. html-report는 한국어 글이 같은 `lint_prose.py`를 거치므로 함께 맞춤. 두 템플릿의 `<style>`과 `<script>`는 그대로여서 이미 게시한 페이지의 검사 결과는 바뀌지 않음

### Fixed
- `tests/run-all.sh`: `assert_contains`와 `assert_not_contains`가 셸 안에서 비교하도록 수정. `pipefail`에서 `printf | grep -q`는 긴 글의 앞쪽에서 일치해 grep이 먼저 끝나면 SIGPIPE로 실패해, 맞는 검사가 가끔 실패하고 `assert_not_contains`는 실패해야 할 때 통과할 수 있었음

## [1.6.0] - 2026-11-18

### Added
- `aws-infographic`: 새 skill 추가. 글쓴이의 claude.ai skill(같은 이름)을 플러그인으로 옮김. 사실 검증한 AWS 팔레트 기술 인포그래픽을 장마다 16:9 다크와 라이트 SVG(아이콘 내장)와 2x PNG로 만들고 요청하면 4:5 세로를 더함. 예전 SKILL.md에 코드 블록으로 들어 있던 코드를 파일(`scripts/infokit.py`, `scripts/buildkit.py`, `assets/page_template.py`)로 배포하고 작업 폴더에 복사해 씀. `infokit.py`가 aws-diagram 아이콘 번들을 `AWS_ICON_BUNDLE`, 사본 옆의 `.aws-icon-bundle` 파일, 옆 skill, 설치된 사본 순서로 찾고 폰트는 파일 이름으로 찾음(`INFOKIT_FONTS`, fontconfig, 사용자 폰트 폴더). Pillow와 Playwright는 쓰는 곳에서만 불러옴. 그리기 API는 그대로여서 예전 skill로 쓴 장 모듈이 같은 SVG를 만듦
- `aws-infographic`: 9단계에서 같은 내용을 `my-plugins:aws-ppt-skills`로 편집 가능한 PowerPoint 덱으로 만듦. 인포그래픽 SVG, PNG는 슬라이드에 넣지 않음. 섹션 하나를 내용 슬라이드 한 장으로 옮기고 텍스트 상자, 도형, PowerPoint 표, 차트, AWS 아이콘 PNG로 다시 만들며 문구는 장 모듈의 `T` dict에서 가져옴. `references/ppt-deck.md`에 내용 대응표, helper `addGrid()`, `addSteps()`, `addIconRow()`, `addLanes()`, 장 템플릿의 예시 덱을 둠. `scripts/icon_png.py`가 번들 아이콘을 PNG로 내보내고, `scripts/check_editable.py`가 SVG가 연결된 덱, 아이콘이 아닌 그림이 든 덱, 1.2 in보다 큰 아이콘이 든 덱을 실패로 처리함([ADR-006](docs/decisions/ADR-006-infographic-editable-deck.md)). 테스트 163개 추가

### Changed
- `aws-ppt-skills`: `addIcon()` 추가. AWS 아이콘을 `icon:<set/name>` 이름의 작은 PNG 그림 하나로 놓음. `check_deck.py`는 이런 그림(1.2 in 이하)에 벡터 SVG 경고를 내지 않음. "Charts and Diagrams"에 편집 가능한 덱을 만드는 방법(`addDiagram()`과 SVG 없이, 마지막에 `check_editable.py`)을 적음
- `setup`: 점검의 렌더 묶음 이름에 aws-infographic 추가. 같은 도구와 폰트를 쓰며 새로 설치하는 것은 없음

## [1.5.2] - 2026-11-17

### Changed
- `aws-blog-skills`: "Changelog"를 영어 그대로 쓰는 규칙 추가. `references/style.md` 금지어 표에 번역어 "변경 기록"과 "변경기록"(버전마다 바뀐 내용을 적은 문서)을 올리고 대체어를 `Changelog`로 지정. 괄호로 번역을 덧붙이지 않으며, 감사 로그처럼 다른 것을 가리키는 문장은 "변경 내역", "변경을 기록한다"로 씀. `lint_prose.py`가 두 표기를 HARD로 잡으므로 같은 검사를 쓰는 techblogs, html-report, aws-reports에도 적용됨(2026-11-17 확정). 테스트 9개 추가
- `techblogs`: `check_post.py`가 페이지 글 어디에서든 "변경 기록"과 "변경기록"을 WARN으로 알리고 `Changelog`로 쓰라고 안내함. `lint_prose.py`가 읽지 않는 표, 캡션, 참고 자료의 종류 이름까지 봄. SKILL.md 3단계와 `references/design-spec.md`의 글자 규칙에 같은 기준을 적었고, `meta.json`의 `note`와 `sources`의 `kind`에도 적용함. 테스트 8개 추가
- `kor-deslop`: 윤문할 때 건드리지 않는 영어 용어에 `Changelog` 추가. SKILL.md에 "변경 기록"으로 바꾸지 않는다고 명시. 테스트 2개 추가

## [1.5.1] - 2026-11-17

### Changed
- `techblogs`: 리포트 페이지가 제목을 한 줄에 맞춤. 보이는 언어의 제목이 한 줄에 들어갈 때까지 글자 크기를 줄이고(30px 아래로는 줄이지 않으며 그래도 긴 제목은 30px에서 줄을 바꿈) 창 크기와 언어가 바뀌면 다시 맞춤(`assets/template.html`의 `fitTitle`, `h1.one`). SKILL.md 0단계와 design-spec.md에 새 글의 제목을 한 줄 길이로 정하라는 기준 추가(창 폭 1440px, 44px에서 한국어 45자 안팎). 이전 템플릿으로 만든 글은 다시 빌드해야 적용됨. 테스트 3개 추가

## [1.5.0] - 2026-11-16

### Added
- `techblogs`: 새 글을 하나의 고정된 뼈대 대신 소재에 맞게 고른 스토리라인으로 쓰는 규칙 추가. `references/storylines.md`에 여덟 가지(`qa`, `troubleshoot`, `measure`, `compare`, `build`, `anatomy`, `change`, `retro`)의 절 흐름, 여는 방식과 닫는 방식, 비유와 그림의 자리, 피할 것을 정리. SKILL.md 0단계에서 하나를 고르고(최근 글 세 편과 여는 방식, 닫는 방식이 겹치지 않게 확인) 2단계에서 그 순서로 절을 배열. 본문 첫 절에서 머리의 결론 목록을 되풀이하지 않고, 첫 절과 끝 절의 제목을 "들어가며", "마치며"로 고정하지 않음. `meta.json`에 `storyline` 키 추가: `build_post.py`가 목록에 없는 값은 거부하고 새 글에 값이 없으면 경고. 옮겨 싣는 글은 원문 구성을 유지. 테스트 16개 추가
- `techblogs`: 주제와 내용에 맞게 고른 스토리라인 템플릿으로 새 글을 시작하는 `scripts/new_post.py` 추가. `--list`는 스토리라인마다 맞는 소재와 소재에서 볼 신호를 출력하고, `<작업 폴더> --storyline 키 --slug 이름`은 `meta.json`과 두 본문 조각을 만들며 본문에는 `references/storylines.md`의 절 흐름대로 안내 주석이 든 빈 절이 들어감. 템플릿의 `TODO`나 안내 주석이 남아 있으면 `build_post.py`가 빌드를 멈춤. `storylines.md`에 주제와 내용에서 볼 신호 표와 두 스토리라인에 걸친 소재를 가르는 기준 추가. 테스트 71개 추가

## [1.4.2] - 2026-11-15

### Added
- `techblogs`: 새로 쓰는 글에 핵심 개념을 익숙한 상황에 빗댄 비유를 넣는 규칙 추가 (SKILL.md 2단계, 예시 포함). 비교하는 대상 전부를 한 상황 안에서 설명하고 차이를 역할의 차이로 드러내며, 사실을 대신하지 않고 영어 본문에도 옮김. 꾸미는 수사 금지는 그대로이고 옮겨 싣는 글에는 넣지 않으며 윤문할 때 지우지 않음. 테스트 3개 추가

## [1.4.1] - 2026-11-15

### Changed
- `techblogs`: 글자가 들어간 그림은 영어판 `<이름>-en.<확장자>`를 만들어 영어 본문에서 가리키도록 변경. 언어를 전환하면 그림도 함께 바뀜. `check_post.py`는 영어 쪽 그림이 같은 파일이거나 그 영어판이면 통과시킴(이전에는 같은 파일만 허용). SKILL.md와 design-spec.md에 규칙을 적고 테스트 2개 추가

## [1.4.0] - 2026-11-15

### Added
- `html-report` skill 추가. 공통 디자인의 공유용 단일 HTML 보고서를 만듦. 한국어와 영어를 한 파일에 넣고 버튼으로 바꾸며, 라이트와 다크 테마(처음에는 시스템 설정), 최대 1440px 한 컬럼, NanumSquareOTF_ac와 D2Coding, "그림 N." 캡션이 붙는 흰 상자의 표와 그림, 위 첨자 인용 번호, 둥근 상태 알약, 고정된 페이지 순서(상단 막대, 머리, 절, 출처 표, 조사 방법, 공유 범위)를 갖춤. `data-report="research"`이면 출처 관련 요소가 필수, `general`이면 선택
- `scripts/check_html.py`: 템플릿과 다른 `<style>`이나 `<script>`, 인라인 `style`, 토큰, 페이지 순서, 두 언어 짝, 짝 밖의 한국어, 본문과 탭 제목, `alt`, `aria-label`의 금지 기호(·, —, –, →), 캡션 번호, 출처 표와 인용 번호, 출처 구성 건수, 상대 경로 그림, 템플릿에서 직접 읽은 예시 문장을 ERROR로, 한다체나 해요체 문장과 "~하세요"와 인용하지 않은 출처를 WARN으로 알림. `--dump-ko`로 한국어 글을 aws-blog-skills `lint_prose.py`에 넘김
- `scripts/embed_images.py`(그림을 data URI로, 페이지 폴더 안의 파일만)와 `scripts/preview.py`(1440px와 390px, 라이트 한국어와 다크 영어의 화면 네 가지. 버튼을 눌러도 화면이 바뀌지 않으면 경고. `libatomic.so.1`이 없는 호스트처럼 Playwright에 포함된 Node.js가 시작되지 않으면 시스템 `node`로 다시 시도)
- `tests/structure/test-html-report.sh`와 ADR-004
- `techblogs` skill 추가. 글쓴이 개인 기술 블로그(whchoi98.github.io, Jekyll)에 올릴 글을 소재부터 배치와 빌드까지 만듦. aws-blog-skills와 절차(URL 전수 확인을 포함한 사실 검증, 한국어 본문, AI 티 제거 윤문, 그림, 규칙 등록)가 같고 올리는 곳이 다름. 결과물은 한영 리포트 페이지(`<slug>-report.html`), front matter 파일(`<slug>.md`), 그림 폴더(`<slug>-assets/`). 디자인은 최대 1440px 한 컬럼, NanumSquareOTF_ac와 D2Coding, 라이트와 다크 테마, 언어 전환, 가로 이동 메뉴, 복사 버튼이 있는 코드 상자로 고정. 사용자 개인 skill로 쓰던 techblogs를 대체
- `scripts/build_post.py`: 작업 폴더(`meta.json`, `ko.body.html`, `en.body.html`, `images/`)를 `assets/template.html`에 채움. `"TODO"`가 남았거나 영어 조각이나 그림 파일이 없거나 `--out`이 skill 폴더 안이면 멈춤. `scripts/check_post.py`: 템플릿과 다른 `<style>`이나 `<script>`, 두 언어의 구성 요소 수 차이, 캡션 번호, 없는 그림 파일, 금지 기호(·, —, –), 인라인 `style`, front matter 오류를 ERROR로 알리고 한국어 글(`--dump-ko`)과 링크 목록(`--urls`)을 aws-blog-skills `lint_prose.py`와 `check_urls.py`에 넘김
- `scripts/import_aws_post.py`(게시된 AWS 블로그 글을 주소나 저장한 페이지에서 작업 폴더로 옮김. AWS 블로그 호스트에서만 내려받음), `scripts/place_post.py`(빌드한 글을 블로그 저장소에 배치하고 그 자리에서 검사, `--build`로 사이트 빌드. git은 실행하지 않음), `scripts/preview.py`(리포트 페이지와 그 페이지를 넣은 글 페이지의 Playwright 화면 캡처)
- `import_aws_post.py`가 그림을 놓인 자리와 관계없이 옮김(문단에 혼자 있는 그림, 글 문단 끝의 그림, base64로 든 그림). 편집용 자리 표시 그림은 버리고, 참고 자료 링크 뒤의 설명을 유지하며, 루트 상대 링크를 페이지의 언어 경로로 쓰고, http(s)가 아닌 링크는 글자만 남김. 받지 못한 그림도 본문에 자리를 남기고, 원문 글자 가운데 옮긴 비율(`coverage`)과 옮기지 않은 블록을 마지막에 출력
- `check_post.py`가 그림 `alt`와 요약의 금지 기호, 영어 쪽 복사 버튼의 한글도 검사. `--dump-ko`가 요약, 머리의 요점, 끝의 고지문도 뽑아 `lint_prose.py` 검사를 받게 함. `build_post.py`가 그림을 복사하기 전에 assets 폴더를 비움
- `tests/structure/test-techblogs.sh`, `tests/fixtures/techblogs/`, ADR-005

### Changed
- aws-reports description이 HTML만 필요한 보고서를 `my-plugins:html-report`로 안내
- aws-blog-skills description이 글쓴이 개인 블로그에 올릴 글을 `my-plugins:techblogs`로 안내
- `docs/reference/agent-llm.md`의 토큰 비용 표를 다시 측정(2026-11-15)

## [1.3.0] - 2026-11-11

### Added
- kor-deslop 패턴 D-8(S1) 추가. AI 글이 전문어처럼 들리게 즐겨 쓰는 "실측"(실측 결과, 실측값), "축"(세 가지 축, 평가 축), "레버"(비용 레버, 레버를 당기다)를 각각 "측정, 측정값", "기준, 관점, 방향, 측면", "해법, 수단, 방법"으로 바꿈. 그래프의 x축과 y축, 기계 부품인 축과 레버, 축소, 압축, 구축, 단축, 축적 같은 합성어는 대상에서 제외. SKILL.md는 이 어휘를 내용 앵커로 잡지 않음. 패턴 수는 80개
- aws-blog-skills: "실측"을 `style.md` 금지어와 `lint_prose.py` HARD 항목에 추가(2026-11-11). `lint_prose.py`만 잡던 "축" 규칙을 `style.md` 표에도 적고, 레버의 대체어를 해법, 수단, 방법으로 넓힘
- aws-reports: `style_terms.json`과 `style-rules.md`가 모든 보고서 유형에서 "실측", "축", "레버"를 경고함. PoC 예제의 "실측 입력·출력 토큰"을 "측정한 입력·출력 토큰"으로 바꿈

### Fixed
- aws-blog-skills `lint_prose.py`의 "축" HARD 검사가 그래프 축과 관계없는 낱말(x축, y축, 가로축, 세로축, 건축, 저축, 축약, 축하)까지 잡던 문제 수정. 독립된 낱말 "축"(두 축, 평가 축)과 붙여 쓴 평가축, 핵심축, 중심축만 잡음. aws-reports도 같은 패턴을 씀. 잡는 경우와 잡지 않는 경우를 모두 테스트로 확인

## [1.2.1] - 2026-11-05

### Fixed
- `setup.sh` 점검 모드가 docx와 docx-preview의 버전을 표시하지 못하던 문제 수정. 두 패키지의 `package.json`은 4칸 들여쓰기와 CRLF 줄 끝을 씀. `pkg_version()`이 들여쓰기와 줄 끝에 관계없이 버전을 읽고, 두 형식을 확인하는 테스트 추가

## [1.2.0] - 2026-11-05

### Added
- `aws-reports` skill 추가. github.com/whchoi98/aws-reports 1.0.0을 보고서 유형 둘을 담은 skill 하나로 합침: 벤치마크 보고서(측정 환경과 방법이 먼저, 종합 평가와 권고가 마지막)와 PoC 결과 보고서(고정된 판정 단어 충족 / 부분 충족 / 미충족 / 측정하지 않음을 쓰는 성공 기준, 전체 판정 진행 / 조건부 진행 / 보류, 이슈, 비용, 다음 단계). Markdown 원고 하나로 MS Word 파일과 단일 HTML 파일을 같은 스타일로 생성
- `scripts/check_report.py --profile benchmark|poc` 추가. 쪽, 글꼴, 캡션, 박스, 표 머리글, 캡션 주석 검사와 `style_terms.json` 표현 검사, 프로필별 구조와 판정 검사
- `scripts/chart_style.py`의 `criteria()` 추가. 성공 기준별 목표 대비 결과를 판정 색과 범례, 판정 단어로 표시
- `setup`이 aws-reports 의존 프로그램을 점검·설치: docx 9.15.1, marked 18.1.1, docx-preview 0.4.1, jszip 3.10.1(`npm install -g`), npm `@kfonts/nanum-square-otf` 0.2.0의 NanumSquareOTF Regular·Bold(`npm pack`)
- `tests/structure/test-aws-reports.sh`와 ADR-003(보고서 skill 하나, 전역 폴더의 npm 패키지) 추가

### Changed
- `report.mjs`가 로컬 `node_modules`, `NODE_PATH`, `npm root -g` 순서로 npm 패키지를 찾도록 변경. ES 모듈 import는 `NODE_PATH`를 읽지 않기 때문. `preview.py`도 같은 순서로 docx-preview와 jszip 번들을 찾음. skill 폴더에는 쓰지 않음: 차트 스크립트는 `python -B`로 실행하고 예제의 `make_charts.py`는 `./charts`나 지정한 폴더에 씀
- 2026-11-04 사용자가 Word에서 직접 고친 보고서 레이아웃 규칙 반영: 한 줄에 들어가지 않는 표 머리글은 끝의 단위를 둘째 줄로 내리고 그 표의 머리글을 모두 가운데 정렬, 캡션 주석은 한 줄이면 가운데·두 줄 이상이면 왼쪽 정렬, 8~9열 표는 7.5/7pt·10열 이상은 6.5pt, 박스 제목 "고객 권고"는 "권고"

## [1.1.0] - 2026-11-04

### Changed
- aws-diagram-design 글자 크기: 노드 이름 13px, sublabel 11px, 화살표 라벨, 범례, 노트 10px(기존 12 / 9 / 8px). README가 내보낸 PNG를 줄여 보여 줘도 읽을 수 있습니다. 라벨 마스크 높이는 14px입니다.
- aws-diagram-design 서비스 아이콘을 노드 높이와 관계없이 제목 줄(`Y+16`)에 둡니다. 높은 노드에서 세로 가운데로 두지 않습니다.
- aws-diagram-design 예제와 reference 77개 파일의 SVG `<text>` 안 가운데 점 `·`을 쉼표로 바꿨습니다(412곳). 예제가 이 패턴을 다시 가르치지 않도록 하기 위해서입니다.

### Added
- aws-diagram-design 구분자 규칙(style-guide.md § Separators): 보이는 텍스트에 `·`를 쓰지 않고, 짝이나 대안은 `/`, 목록은 쉼표로 씁니다. Mermaid 단계 번호는 `1. `이 Markdown 목록으로 렌더링되므로 `1: `로 씁니다.
- aws-diagram-design 텍스트 폭 규칙: 가장 긴 sublabel 기준으로 박스 크기를 정합니다(Amazon Ember Mono는 라틴 글자당 약 0.63em, 한글은 약 1em). 오른쪽에 12px 여백을 둡니다.
- 위 규칙에 대한 공통 anti-pattern 4개와 체크리스트 항목 3개
- `self_check.py`가 보이는 SVG 텍스트에서 가운데 점을 찾으면 실패합니다.

### Fixed
- 통합 과정에서 `scripts/diagrams/`로 옮긴 `verify-motion.py`와 `verify-geometry.py`가 repo 루트를 한 단계 아래로 잡던 문제를 고쳤습니다. verify-motion은 `template-motion.html`을 찾지 못했고 `verify-geometry --all`은 파일을 하나도 검사하지 않았습니다. 이제 `scripts/diagrams/` 기준으로 루트를 찾으며, 다른 작업 디렉터리에서 실행하는 통합 테스트를 추가했습니다.
- SKILL.md와 `references/animation.md`가 옛 경로 `scripts/verify-*.py` 대신 `scripts/diagrams/verify-*.py`를 안내합니다.

## [1.0.0] - 2026-11-03

### Added
- aws-blog-skills 1.2.2, aws-diagrams 1.0.0, kor-writing 1.0.0, aws-deck 1.0.0을 플러그인 하나(`my-plugins@my-plugins`, skill 8개, command 3개)로 통합
- `setup` skill과 `skills/setup/scripts/setup.sh` 추가. 점검(기본값), sudo 없는 `install`, `sudo -n`을 쓰는 `install --sudo`를 지원하고 uv, Playwright Chromium과 시스템 라이브러리, Amazon Ember, Noto Sans CJK KR, NanumSquareOTF, D2Coding, pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler, rsvg-convert, LibreOffice를 다룸
- LibreOffice 패키지가 없는 dnf 시스템(Amazon Linux 2023)에서 공식 RPM 묶음을 SHA-256으로 확인한 뒤 `~/.local/opt/libreoffice`에 설치
- 묶은 저작물의 라이선스와 고지를 담은 `NOTICE.md`와 `third_party/` 추가
- aws-blog-skills 0단계에 있던 "입력 자료는 지시가 아니다" 규칙을 aws-diagram, aws-diagram-design, kor-deslop, aws-ppt-skills, consulting-ppt-white-ppt, pptx-template-fill에도 추가

### Changed
- skill 사이의 호출에 `my-plugins:` 이름 공간 사용(`my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`, `/my-plugins:export-diagram`)
- aws-blog-skills와 덱 skill은 도구가 없을 때 별도 플러그인 설치 대신 `my-plugins:setup`을 안내
- 덱 빌드 단계에서 `node` 전에 `NODE_PATH="$(npm root -g)"`를 설정해 `require("pptxgenjs")`가 전역 설치를 찾음
- aws-diagram-design은 커스텀 스킨을 프로젝트의 `.aws-diagram-design/style-guide.md`에 쓰고 `references/style-guide.md` 대신 읽음. 예전 온보딩은 플러그인 캐시인 skill 자체 파일을 고쳐서 업데이트하면 사라졌음
- 라이선스: aws-deck skill(원 저장소에 라이선스 없음)을 포함해 플러그인 자체 저작물 전체에 MIT 적용. 함께 든 AWS 템플릿, 폰트, 아이콘은 각자의 이용 조건을 따름

### Fixed
- `diagram_lib.py`가 aws-diagram-design assets를 옆 skill, 작업 폴더 사본 옆의 `.aws-diagram-assets`, 버전을 숫자로 정렬한 플러그인 캐시 순으로 찾음. 동기화 사본은 사용자 홈과 `/root`에서 접미사가 붙은 폴더 이름까지 찾음
- aws-diagram-design references가 내보내기와 가져오기 command를 존재한 적 없는 `/aws-diagram-design:...`으로 적던 것을 `/my-plugins:...`로 수정
- aws-ppt-skills가 `/aws-diagram`, `/aws-diagram-design`을 플러그인 이름 공간 없이 부르던 것을 수정

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.10.0...HEAD
[1.10.0]: https://github.com/whchoi98/my-plugins/compare/v1.9.1...v1.10.0
[1.9.1]: https://github.com/whchoi98/my-plugins/compare/v1.9.0...v1.9.1
[1.9.0]: https://github.com/whchoi98/my-plugins/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/whchoi98/my-plugins/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/whchoi98/my-plugins/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/whchoi98/my-plugins/compare/v1.5.2...v1.6.0
[1.5.2]: https://github.com/whchoi98/my-plugins/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/whchoi98/my-plugins/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/whchoi98/my-plugins/compare/v1.4.2...v1.5.0
[1.4.2]: https://github.com/whchoi98/my-plugins/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/whchoi98/my-plugins/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/whchoi98/my-plugins/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/whchoi98/my-plugins/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/whchoi98/my-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/whchoi98/my-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0

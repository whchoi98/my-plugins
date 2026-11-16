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

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.4.2...HEAD
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

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.4.2...HEAD
[1.4.2]: https://github.com/whchoi98/my-plugins/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/whchoi98/my-plugins/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/whchoi98/my-plugins/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/whchoi98/my-plugins/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/whchoi98/my-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/whchoi98/my-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0

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

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.2.0...HEAD
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

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/whchoi98/my-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0

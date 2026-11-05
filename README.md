# my-plugins

[![Version](https://img.shields.io/badge/Version-1.2.0-green.svg)](CHANGELOG.md)
<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

One Claude Code plugin that bundles aws-blog-skills, aws-diagrams, kor-writing, aws-deck and aws-reports | aws-blog-skills, aws-diagrams, kor-writing, aws-deck, aws-reports를 하나로 묶은 Claude Code 플러그인

---

<a id="english"></a>

# English

## Overview

`my-plugins` merges five plugins into one install: the AWS Korea Tech Blog drafting workflow, AWS architecture
and structure diagrams, Korean AI-tell removal, AWS PowerPoint decks, and customer reports as MS Word + HTML
(benchmarks and PoC results). The skills call each other inside
the same plugin, so a blog post can draw its diagrams and run the 윤문 check without a second plugin, and a
deck can embed the same diagrams. A `setup` skill checks and installs every external tool and font the skills
need, including the cases that broke on Amazon Linux 2023.

## Included Skills and Commands

| Skill / command | Source plugin | What it does |
|---|---|---|
| `/my-plugins:aws-blog-skills` | aws-blog-skills 1.2.2 | Korean AWS Korea Tech Blog draft from source to zip: scope, fact and URL check, diagrams, 윤문, packaging |
| `/my-plugins:aws-diagram` | aws-diagrams 1.0.0 | AWS architecture diagrams with the official AWS and Bedrock AgentCore icon sets |
| `/my-plugins:aws-diagram-design` | aws-diagrams 1.0.0 | AWS-branded structure diagrams: flowchart, sequence, timeline, ER, charts and more |
| `/my-plugins:export-diagram`, `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | aws-diagrams 1.0.0 | Export an aws-diagram-design HTML file to SVG/PNG; redraw draw.io or Mermaid sources |
| `/my-plugins:kor-deslop` | kor-writing 1.0.0 | Removes AI tells from Korean text in one pass (79 patterns), content unchanged |
| `/my-plugins:aws-ppt-skills` | aws-deck 1.0.0 | AWS Korea 2026 black or white template decks with pptxgenjs and Korean speaker notes |
| `/my-plugins:consulting-ppt-white-ppt` | aws-deck 1.0.0 | Dense consulting-report decks with a customer brand accent |
| `/my-plugins:pptx-template-fill` | aws-deck 1.0.0 | Fills an existing .pptx template in place, keeping its layout |
| `/my-plugins:aws-reports` | aws-reports 1.0.0 | Customer reports as MS Word + standalone HTML from one Markdown draft: benchmarks, and PoC results with success criteria, verdicts and next steps |
| `/my-plugins:setup` | new | Checks and installs the external tools and fonts above |

## What Changed from the Four Plugins

- **One namespace**: every cross-skill call uses `my-plugins:<skill>`. The originals mixed `aws-diagrams:`,
  `kor-writing:`, bare `/aws-diagram`, and a wrong `/aws-diagram-design:export-diagram`.
- **Diagram assets are found in place**: `diagram_lib.py` (aws-blog-skills) reads the icons and Amazon Ember
  fonts from the sibling `aws-diagram-design` skill. When the skill copies `diagram_lib.py` into a work folder,
  it also writes `.aws-diagram-assets` next to the copy, so the copy finds the same folder. The old lookup only
  searched `/root` for synced plugins and sorted cache versions as strings.
- **One installer for dependencies**: `/my-plugins:setup` covers what each plugin left to the user: Playwright
  Chromium and its system libraries, Noto Sans CJK KR, Amazon Ember, NanumSquareOTF and D2Coding (the deck
  fonts were installed only when a deck build ran), pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler,
  rsvg-convert and LibreOffice. LibreOffice is not in the Amazon Linux 2023 repositories, so `setup` unpacks the
  official RPM bundle into `~/.local/opt/libreoffice` after a SHA-256 check.
- **pptxgenjs is found**: deck build steps set `NODE_PATH="$(npm root -g)"` before `node`, because a global
  npm install is not on `require()`'s search path.
- **One marketplace name**: aws-deck was published as `aws-deck@whchoi`; everything is now `my-plugins@my-plugins`.

## Prerequisites

- [Claude Code](https://code.claude.com) with plugin support
- Python 3, Node.js and npm, `zip`, `curl`
- Everything else is installed by `/my-plugins:setup` (see [Usage](#usage))

## Installation

```bash
claude plugin marketplace add whchoi98/my-plugins
claude plugin install my-plugins@my-plugins
```

From a local clone instead of GitHub:

```bash
claude plugin marketplace add /path/to/my-plugins
claude plugin install my-plugins@my-plugins
```

### Moving from the standalone plugins

The standalone plugins load the same skills under their old names, so remove them after installing:

```bash
claude plugin uninstall aws-blog-skills@aws-blog-skills
claude plugin uninstall aws-diagrams@aws-diagrams
claude plugin uninstall kor-writing@kor-writing
claude plugin uninstall aws-deck@whchoi
claude plugin uninstall aws-reports@aws-reports
claude plugin marketplace remove aws-blog-skills
claude plugin marketplace remove aws-diagrams
claude plugin marketplace remove kor-writing
claude plugin marketplace remove whchoi
claude plugin marketplace remove aws-reports
```

If the same plugins are also attached to your claude.ai account, Claude Code loads those synced copies
(`aws-diagrams@synced`, `kor-writing@synced`, `aws-deck@synced`) once the local plugins with the same names are
gone. Remove them from the claude.ai account, or turn their skills off with `skillOverrides` in
`~/.claude/settings.json`.

### Update

```bash
claude plugin marketplace update my-plugins
claude plugin update my-plugins@my-plugins
```

Run `/reload-plugins` in open sessions afterwards.

## Usage

Check the machine once, then install what is missing:

```text
/my-plugins:setup
```

The skill runs `skills/setup/scripts/setup.sh`: without arguments it only checks; `install` installs everything
that needs no sudo; `install --sudo` also installs system packages with `sudo -n` and prints the command when
sudo needs a password. Claude asks before running the sudo step.

aws-reports builds its Word and HTML files with the npm packages docx, marked, docx-preview and jszip and the
NanumSquareOTF font; `setup` installs them (`npm install -g` at fixed versions, the font from npm `@kfonts`).

Then ask in plain Korean, or call a skill directly:

```text
이 PDF를 AWS 블로그 스타일로 블로그 초안 작성해줘
이 구성을 AWS 아키텍처 다이어그램으로 그려줘
이 글 AI 티 빼줘
화이트 테마로 50명 미만 기술 세미나 덱 만들어줘
이 CSV로 Graviton vs Intel 벤치마크 보고서 Word랑 HTML로 만들어줘
PoC 결과를 성공 기준별 판정으로 정리해서 보고서로 만들어줘
/my-plugins:pptx-template-fill
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `AWS_DIAGRAM_ASSETS` | aws-diagram-design `assets` folder for `diagram_lib.py`, when auto-detection fails | `.aws-diagram-assets` next to the file, then the sibling skill, then the plugin cache |
| `BLOG_IMAGES` | Output folder for the blog diagram generator and `render_diagrams.py` | None (required) |
| `NODE_PATH` | Set to `$(npm root -g)` so deck build scripts find the global pptxgenjs (aws-reports also asks `npm root -g` itself) | Unset |
| `CLAUDE_NOTIFY_WEBHOOK` | Dev harness only: webhook for Claude Code notifications | Unset |

## Project Structure

```text
.claude-plugin/          # plugin.json and marketplace.json (source ./)
skills/
├── aws-blog-skills/     # blog workflow, references, scripts, template
├── aws-diagram/         # AWS architecture diagrams, icon finder and embedder
├── aws-diagram-design/  # structure diagrams; assets/ holds AWS icons and Amazon Ember fonts
├── kor-deslop/          # Korean AI-tell removal, references/patterns.md
├── aws-ppt-skills/      # AWS template decks, bundled templates and fonts
├── consulting-ppt-white-ppt/  # consulting-report decks
├── pptx-template-fill/  # fill an existing template
├── aws-reports/         # benchmark and PoC reports: Word + HTML engine, references, examples
└── setup/               # dependency check and install (scripts/setup.sh)
commands/                # export-diagram, import-drawio, import-mermaid
third_party/             # upstream licenses and notices
scripts/                 # dev setup, git hooks; scripts/diagrams/ holds the diagram repo gates
docs/                    # architecture, onboarding, ADRs, runbooks; docs/diagrams/ holds diagram guides and samples
tests/                   # run-all.sh, hooks/, structure/, fixtures/
```

## Testing

```bash
bash tests/run-all.sh             # hooks, secret patterns, plugin structure, shipped scripts
claude plugin validate .          # Claude Code manifest and skill validation (ICON_MISSING is expected)
```

## License

MIT ([LICENSE](LICENSE)) for the plugin's own work: aws-blog-skills, kor-deslop, the aws-deck skills, aws-reports and setup.
Details per part are in [NOTICE.md](NOTICE.md). aws-diagram-design is MIT from its upstream
([third_party/LICENSE-aws-diagram-design](third_party/LICENSE-aws-diagram-design)); AWS icons, Amazon Ember and
the AWS PowerPoint templates and deck fonts follow their own terms and are not covered by the MIT license.

## Contact

WooHyung Choi, [github.com/whchoi98](https://github.com/whchoi98)

---

<a id="korean"></a>

# 한국어

## 개요

`my-plugins`는 플러그인 다섯 개를 하나로 합친 Claude Code 플러그인입니다. AWS Korea Tech Blog 원고 작성, AWS
아키텍처와 구조 다이어그램, 한국어 AI 티 제거 윤문, AWS PowerPoint 덱 제작, 벤치마크·PoC 결과 보고서(MS Word +
HTML)를 한 번에 설치합니다. skill끼리 같은
플러그인 안에서 서로를 부르므로 블로그 원고가 다른 플러그인 없이 다이어그램을 그리고 윤문 점검을 하며, 덱도 같은
다이어그램을 넣습니다. `setup` skill은 skill들이 쓰는 외부 프로그램과 폰트를 점검하고 설치하며, Amazon Linux
2023에서 막혔던 경우도 처리합니다.

## 포함된 skill과 command

| skill / command | 원래 플러그인 | 하는 일 |
|---|---|---|
| `/my-plugins:aws-blog-skills` | aws-blog-skills 1.2.2 | 소재부터 zip까지 AWS Korea Tech Blog 한국어 원고: 범위, 사실과 URL 검증, 다이어그램, 윤문, 패키징 |
| `/my-plugins:aws-diagram` | aws-diagrams 1.0.0 | 공식 AWS 아이콘과 Bedrock AgentCore 아이콘으로 그리는 AWS 아키텍처 구성도 |
| `/my-plugins:aws-diagram-design` | aws-diagrams 1.0.0 | 흐름도, 시퀀스, 타임라인, ER, 차트 등 AWS 브랜드 스킨의 구조 다이어그램 |
| `/my-plugins:export-diagram`, `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | aws-diagrams 1.0.0 | aws-diagram-design HTML을 SVG/PNG로 내보내기, draw.io와 Mermaid 다시 그리기 |
| `/my-plugins:kor-deslop` | kor-writing 1.0.0 | 한국어 글의 AI 티를 한 번에 제거(패턴 79개). 내용은 그대로 둡니다 |
| `/my-plugins:aws-ppt-skills` | aws-deck 1.0.0 | 2026 AWS Korea 블랙·화이트 템플릿 덱(pptxgenjs, 한국어 발표 대본) |
| `/my-plugins:consulting-ppt-white-ppt` | aws-deck 1.0.0 | 고객 브랜드 색을 쓰는 고밀도 컨설팅 리포트 덱 |
| `/my-plugins:pptx-template-fill` | aws-deck 1.0.0 | 기존 .pptx 템플릿의 레이아웃을 유지하며 내용 채우기 |
| `/my-plugins:aws-reports` | aws-reports 1.0.0 | Markdown 원고 하나로 만드는 고객 공유용 Word + 단일 HTML 보고서: 벤치마크, 성공 기준별 판정과 다음 단계를 담은 PoC 결과 |
| `/my-plugins:setup` | 신규 | 위 skill들의 외부 프로그램과 폰트 점검·설치 |

## 네 플러그인에서 달라진 점

- **이름 공간 통일**: skill 사이의 호출은 모두 `my-plugins:<skill>`을 씁니다. 원래는 `aws-diagrams:`,
  `kor-writing:`, 이름 공간 없는 `/aws-diagram`, 잘못된 `/aws-diagram-design:export-diagram`이 섞여 있었습니다.
- **다이어그램 assets를 제자리에서 찾음**: aws-blog-skills의 `diagram_lib.py`는 옆에 있는 `aws-diagram-design`
  skill에서 아이콘과 Amazon Ember 폰트를 읽습니다. skill이 `diagram_lib.py`를 작업 폴더로 복사할 때는 사본 옆에
  `.aws-diagram-assets`를 함께 써서 사본도 같은 폴더를 찾습니다. 예전에는 동기화 플러그인을 `/root`에서만 찾았고,
  캐시 버전을 문자열로 정렬했습니다.
- **의존 프로그램 설치를 한곳에서**: `/my-plugins:setup`이 각 플러그인이 사용자에게 맡겼던 것을 처리합니다.
  Playwright Chromium과 시스템 라이브러리, Noto Sans CJK KR, Amazon Ember, NanumSquareOTF와 D2Coding(덱 폰트는
  덱을 빌드할 때만 설치되었습니다), pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler, rsvg-convert,
  LibreOffice입니다. Amazon Linux 2023 저장소에는 LibreOffice가 없으므로 공식 RPM 묶음을 SHA-256으로 확인한 뒤
  `~/.local/opt/libreoffice`에 풉니다.
- **pptxgenjs를 찾음**: 전역 npm 모듈은 `require()`가 찾지 않으므로 덱 빌드 단계에서 `node` 전에
  `NODE_PATH="$(npm root -g)"`를 설정합니다.
- **마켓플레이스 이름 통일**: aws-deck은 `aws-deck@whchoi`로 배포되었습니다. 이제 모두 `my-plugins@my-plugins`입니다.

## 사전 요구 사항

- 플러그인을 지원하는 [Claude Code](https://code.claude.com)
- Python 3, Node.js와 npm, `zip`, `curl`
- 나머지는 `/my-plugins:setup`이 설치합니다([사용법](#사용법) 참고)

## 설치 방법

```bash
claude plugin marketplace add whchoi98/my-plugins
claude plugin install my-plugins@my-plugins
```

GitHub 대신 로컬 클론에서 설치할 때:

```bash
claude plugin marketplace add /path/to/my-plugins
claude plugin install my-plugins@my-plugins
```

### 단독 플러그인에서 옮겨 올 때

단독 플러그인은 같은 skill을 예전 이름으로 불러오므로 설치 후 제거합니다.

```bash
claude plugin uninstall aws-blog-skills@aws-blog-skills
claude plugin uninstall aws-diagrams@aws-diagrams
claude plugin uninstall kor-writing@kor-writing
claude plugin uninstall aws-deck@whchoi
claude plugin uninstall aws-reports@aws-reports
claude plugin marketplace remove aws-blog-skills
claude plugin marketplace remove aws-diagrams
claude plugin marketplace remove kor-writing
claude plugin marketplace remove whchoi
claude plugin marketplace remove aws-reports
```

같은 플러그인이 claude.ai 계정에도 연결되어 있으면, 이름이 같은 로컬 플러그인이 사라진 뒤 Claude Code가 동기화
사본(`aws-diagrams@synced`, `kor-writing@synced`, `aws-deck@synced`)을 불러옵니다. claude.ai 계정에서 제거하거나
`~/.claude/settings.json`의 `skillOverrides`로 해당 skill을 끕니다.

### 갱신

```bash
claude plugin marketplace update my-plugins
claude plugin update my-plugins@my-plugins
```

열려 있는 세션에서는 `/reload-plugins`를 실행합니다.

## 사용법

머신마다 한 번 점검하고 빠진 것을 설치합니다.

```text
/my-plugins:setup
```

이 skill은 `skills/setup/scripts/setup.sh`를 실행합니다. 인자 없이 실행하면 점검만 하고, `install`은 sudo가 필요
없는 것을 설치하며, `install --sudo`는 시스템 패키지까지 `sudo -n`으로 설치하고 sudo에 암호가 필요하면 명령만
출력합니다. sudo 단계는 Claude가 실행 전에 묻습니다.

aws-reports는 npm 패키지 docx, marked, docx-preview, jszip과 NanumSquareOTF 폰트로 Word와 HTML을 만듭니다.
`setup`이 이들을 설치합니다(`npm install -g` 고정 버전, 폰트는 npm `@kfonts`).

그다음 한국어로 요청하거나 skill을 직접 부릅니다.

```text
이 PDF를 AWS 블로그 스타일로 블로그 초안 작성해줘
이 구성을 AWS 아키텍처 다이어그램으로 그려줘
이 글 AI 티 빼줘
화이트 테마로 50명 미만 기술 세미나 덱 만들어줘
이 CSV로 Graviton vs Intel 벤치마크 보고서 Word랑 HTML로 만들어줘
PoC 결과를 성공 기준별 판정으로 정리해서 보고서로 만들어줘
/my-plugins:pptx-template-fill
```

## 설정

| 변수 | 설명 | 기본값 |
|---|---|---|
| `AWS_DIAGRAM_ASSETS` | 자동 탐색이 실패할 때 `diagram_lib.py`가 쓸 aws-diagram-design `assets` 폴더 | 파일 옆 `.aws-diagram-assets`, 옆 skill, 플러그인 캐시 순으로 탐색 |
| `BLOG_IMAGES` | 블로그 다이어그램 생성기와 `render_diagrams.py`의 출력 폴더 | 없음(필수) |
| `NODE_PATH` | 덱 빌드 스크립트가 전역 pptxgenjs를 찾도록 `$(npm root -g)`로 설정(aws-reports는 `npm root -g`를 직접 찾습니다) | 없음 |
| `CLAUDE_NOTIFY_WEBHOOK` | 개발 하네스 전용: Claude Code 알림 웹훅 | 없음 |

## 프로젝트 구조

```text
.claude-plugin/          # plugin.json, marketplace.json(source ./)
skills/
├── aws-blog-skills/     # 블로그 워크플로우, references, scripts, 템플릿
├── aws-diagram/         # AWS 아키텍처 구성도, 아이콘 검색과 내장
├── aws-diagram-design/  # 구조 다이어그램. assets/에 AWS 아이콘과 Amazon Ember 폰트
├── kor-deslop/          # 한국어 AI 티 제거, references/patterns.md
├── aws-ppt-skills/      # AWS 템플릿 덱, 템플릿과 폰트 포함
├── consulting-ppt-white-ppt/  # 컨설팅 리포트 덱
├── pptx-template-fill/  # 기존 템플릿 채우기
├── aws-reports/         # 벤치마크·PoC 보고서: Word + HTML 변환기, references, 예제
└── setup/               # 의존 프로그램 점검과 설치(scripts/setup.sh)
commands/                # export-diagram, import-drawio, import-mermaid
third_party/             # 원 저작물의 라이선스와 고지
scripts/                 # 개발 설정, git hooks. scripts/diagrams/에 다이어그램 저장소 검사 스크립트
docs/                    # 아키텍처, 온보딩, ADR, 런북. docs/diagrams/에 다이어그램 가이드와 샘플
tests/                   # run-all.sh, hooks/, structure/, fixtures/
```

## 테스트

```bash
bash tests/run-all.sh             # hooks, 시크릿 패턴, 플러그인 구조, 포함된 스크립트
claude plugin validate .          # Claude Code manifest와 skill 검증(ICON_MISSING 경고는 정상)
```

## 라이선스

플러그인 자체 저작물(aws-blog-skills, kor-deslop, aws-deck skill, aws-reports, setup)은 MIT([LICENSE](LICENSE))입니다.
부분별 내용은 [NOTICE.md](NOTICE.md)에 있습니다. aws-diagram-design은 원 저작물의 MIT
([third_party/LICENSE-aws-diagram-design](third_party/LICENSE-aws-diagram-design))이고, AWS 아이콘, Amazon Ember,
AWS PowerPoint 템플릿, 덱 폰트는 MIT 대상이 아니며 각자의 이용 조건을 따릅니다.

## 연락처

WooHyung Choi, [github.com/whchoi98](https://github.com/whchoi98)

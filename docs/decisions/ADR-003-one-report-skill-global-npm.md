# ADR-003: One aws-reports skill for benchmark and PoC reports, npm packages from the global folder

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-05)

## Context
github.com/whchoi98/aws-reports 1.0.0 shipped two skills, `benchmark-report` and `poc-report`, that build a
customer report as MS Word and standalone HTML from one Markdown draft. Both used the same engine and rules in
a plugin-level `shared/` folder, reached as `${CLAUDE_SKILL_DIR}/../../shared`, and its `setup.sh` ran
`npm install` inside that folder. Merging it into my-plugins meets three rules of this repository: a skill
reaches another skill's files only by a path relative to its own folder, nothing is written into a skill folder
(the plugin cache), and dependencies go through the `setup` skill.

## Options Considered

### Option 1: Two skills, the engine in benchmark-report, poc-report uses `../benchmark-report/scripts`
- **Pros**: same triggers as the source plugin; each report type has its own SKILL.md
- **Cons**: two descriptions always loaded (about 980 tokens); poc-report depends on another skill's folder;
  the shared rules live in one skill and are read by the other

### Option 2: One skill `aws-reports` with two report types
- **Pros**: one description (about 430 tokens always on), one engine in its own `scripts/`, no cross-skill path;
  SKILL.md picks the type, then loads only that type's references; one place for wording and layout rules
- **Cons**: the SKILL.md body is longer (about 3.8k tokens on invoke); a request has to be routed to a type
  inside the skill instead of by the skill list

## Decision
Option 2, chosen by the user. `skills/aws-reports/` holds `references/benchmark-structure.md`,
`poc-structure.md` and `poc-verdict-rules.md` next to the common `markdown-spec.md` and `style-rules.md`, and
`check_report.py --profile benchmark|poc` keeps the two structure checks apart.

The npm packages (docx, marked, docx-preview, jszip) are installed globally by `setup` at fixed versions,
like pptxgenjs. `report.mjs` is an ES module, and ESM imports do not read `NODE_PATH`, so the script looks for a
package itself: a `node_modules` above the script, then `NODE_PATH` entries, then `npm root -g`, and imports the
package's ESM entry by file URL. `preview.py` uses the same order for the docx-preview and jszip browser bundles.
The body font NanumSquareOTF Regular is not in the plugin (the deck skill bundles only NanumSquareOTF_ac Bold),
so `setup` fetches `@kfonts/nanum-square-otf` with `npm pack`, which checks the registry's integrity hash.

## Consequences

### Positive
- The skill folder stays read-only: outputs go to the work folder, chart scripts run with `python -B`, and the
  examples' `make_charts.py` write to `./charts` or a given folder.
- `NODE_PATH` is optional for reports; the deck rule (`export NODE_PATH="$(npm root -g)"`) is unchanged.

### Negative
- npm redacts UUID-like strings in its output, so `npm root -g` returns a masked path when the global prefix
  contains a UUID; the lookup then falls back to `NODE_PATH`. Normal prefixes (`~/.npm-global`, `/usr/local`)
  are not affected.
- Users of the standalone aws-reports plugin get the skill under a new name, `/my-plugins:aws-reports`.

## References
- `skills/aws-reports/SKILL.md`, `skills/aws-reports/scripts/report.mjs` (`load()`), `skills/setup/scripts/setup.sh`
  (`check_reports`, `install_reports_user`)
- [ADR-002](ADR-002-merge-four-plugins-into-one.md)

---

<a id="korean"></a>

# 한국어

## 상태
채택(2026-11-05)

## 배경
github.com/whchoi98/aws-reports 1.0.0은 Markdown 원고 하나로 고객 보고서를 MS Word와 단일 HTML로 만드는 skill 두 개, `benchmark-report`와 `poc-report`를 배포했습니다. 두 skill은 플러그인 수준의 `shared/` 폴더에 있는 변환기와 규칙을 `${CLAUDE_SKILL_DIR}/../../shared`로 함께 썼고, `setup.sh`는 그 폴더 안에서 `npm install`을 실행했습니다. my-plugins에 합치려면 이 저장소의 세 규칙과 맞아야 합니다. 다른 skill의 파일은 자기 폴더 기준 상대 경로로만 찾고, skill 폴더(플러그인 캐시)에는 아무것도 쓰지 않으며, 의존 프로그램은 `setup` skill로 설치합니다.

## 검토한 선택지

### 선택지 1: skill 두 개, 변환기는 benchmark-report에 두고 poc-report는 `../benchmark-report/scripts` 사용
- **장점**: 원래 플러그인과 트리거가 같고, 보고서 유형마다 SKILL.md가 따로 있습니다
- **단점**: description 두 개가 항상 로드됩니다(약 980토큰). poc-report가 다른 skill 폴더에 기대고, 공통 규칙이 한 skill에 있으면서 다른 skill이 읽습니다

### 선택지 2: 보고서 유형 둘을 담은 skill 하나, `aws-reports`
- **장점**: description 하나(항상 로드 약 430토큰), 자기 `scripts/`에 있는 변환기 하나, skill 사이의 경로 없음. SKILL.md가 유형을 고른 뒤 그 유형의 참조 파일만 읽고, 문구와 레이아웃 규칙을 한곳에서 관리합니다
- **단점**: SKILL.md 본문이 깁니다(호출할 때 약 3.8k토큰). 요청을 skill 목록이 아니라 skill 안에서 유형으로 나눠야 합니다

## 결정
사용자가 고른 선택지 2입니다. `skills/aws-reports/`에 공통 `markdown-spec.md`, `style-rules.md`와 함께 `references/benchmark-structure.md`, `poc-structure.md`, `poc-verdict-rules.md`를 두고, `check_report.py --profile benchmark|poc`로 두 구조 검사를 나눕니다.

npm 패키지(docx, marked, docx-preview, jszip)는 pptxgenjs처럼 `setup`이 고정 버전으로 전역에 설치합니다. `report.mjs`는 ES 모듈이고 ESM import는 `NODE_PATH`를 읽지 않으므로, 스크립트 위의 `node_modules`, `NODE_PATH` 항목, `npm root -g` 순서로 패키지를 직접 찾아 패키지의 ESM 진입 파일을 파일 URL로 import합니다. `preview.py`도 docx-preview와 jszip 브라우저 번들을 같은 순서로 찾습니다. 본문 글꼴 NanumSquareOTF Regular는 플러그인에 없으므로(덱 skill에는 NanumSquareOTF_ac Bold 하나만 있습니다) `setup`이 `npm pack`으로 `@kfonts/nanum-square-otf`를 받습니다. `npm pack`은 레지스트리의 integrity 해시를 확인합니다.

## 결과

### 긍정적
- skill 폴더는 읽기 전용으로 남습니다. 결과물은 작업 폴더에 쓰고, 차트 스크립트는 `python -B`로 실행하며, 예제의 `make_charts.py`는 `./charts`나 지정한 폴더에 씁니다.
- 보고서에는 `NODE_PATH`가 필요 없습니다. 덱 규칙(`export NODE_PATH="$(npm root -g)"`)은 그대로입니다.

### 부정적
- npm은 출력에서 UUID처럼 생긴 문자열을 가리므로, 전역 prefix에 UUID가 들어 있으면 `npm root -g`가 가려진 경로를 돌려줍니다. 그때는 `NODE_PATH`로 찾습니다. 보통의 prefix(`~/.npm-global`, `/usr/local`)는 영향이 없습니다.
- 단독 aws-reports 플러그인 사용자는 새 이름 `/my-plugins:aws-reports`로 skill을 부릅니다.

## 참고
- `skills/aws-reports/SKILL.md`, `skills/aws-reports/scripts/report.mjs`(`load()`), `skills/setup/scripts/setup.sh`(`check_reports`, `install_reports_user`)
- [ADR-002](ADR-002-merge-four-plugins-into-one.md)

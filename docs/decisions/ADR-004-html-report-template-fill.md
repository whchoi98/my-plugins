# ADR-004: html-report fills a fixed template, Korean and English as element pairs in one file

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-11)

## Context
The user gave one design format for every HTML report: NanumSquareOTF_ac and D2Coding, fixed light and dark
colors, one column up to 1440px, a top bar with a list link and language and theme switches, a fixed page order
(head with as-of date, searched sources, title, summary, tags and source mix; sections with a 2px rule, source
kind and H2; source table; method; one sharing line), white boxes with 10px corners, "그림 N." captions,
superscript citations, rounded status pills, Korean and English in one file, and AWS Korea Tech Blog 합쇼체.
aws-reports already writes HTML, but its HTML mirrors its Word file (820px, other colors, no language switch).

## Options Considered

### Option 1: A third report type inside aws-reports
- **Pros**: one report skill; reuses `report.mjs`
- **Cons**: `report.mjs` builds Word and HTML from one Markdown draft with one style; a second HTML style and a
  bilingual draft format would fork the engine and its checker; Node.js and npm become a requirement for an
  HTML-only page

### Option 2: A new skill that builds the page from a Markdown draft
- **Pros**: the model writes Markdown, a script writes HTML
- **Cons**: needs a bilingual Markdown dialect (or two drafts that drift apart) and a renderer to maintain;
  every new component needs syntax first

### Option 3: A new skill that fills a fixed template, with a checker
- **Pros**: the template already holds every component, token and the toggle script; the model edits content
  only; Python standard library only; the checker can verify what a renderer would have guaranteed (pairs,
  order, numbering, tokens)
- **Cons**: the model edits HTML by hand, so mistakes are caught after writing instead of prevented

## Decision
Option 3. `skills/html-report/` ships `assets/template.html`, `references/design-spec.md` and
`scripts/check_html.py`, which hold the same values; a design change goes into the three together.
Korean and English sit in one file as element pairs: a `lang="ko"` element followed by the same tag with
`lang="en"`, and one CSS rule hides the language not chosen. Figures appear once and only captions pair up.
The checker rejects Korean outside a `lang="ko"` element because it would show in the English view.
`data-report="research"` makes the source parts required; `general` keeps them optional. The page stays one
file: `embed_images.py` turns relative images into data URIs and reads only files inside the page's folder.

## Consequences

### Positive
- No new dependency; `preview.py` uses the Playwright that `setup` already installs, and falls back to the
  system `node` when Playwright's bundled Node.js does not start (missing `libatomic.so.1`)
- The source-mix counts are checked against the source table, so the head cannot drift from the sources
- aws-reports stays as it is

### Negative
- Two HTML styles exist in the plugin: aws-reports HTML follows its Word file, html-report follows this format
- Writing every block twice makes the page about twice as long to edit

## References
- `skills/html-report/references/design-spec.md`
- `tests/structure/test-html-report.sh`
- [ADR-003](ADR-003-one-report-skill-global-npm.md)

---

<a id="korean"></a>

# 한국어

## 상태
승인(2026-11-11)

## 배경
사용자가 모든 HTML 보고서에 쓸 디자인 형식 하나를 정했습니다. 글꼴(NanumSquareOTF_ac, D2Coding), 라이트와 다크 색, 최대 1440px 한 컬럼, 목록 링크와 언어 및 테마 전환이 있는 상단 막대를 정했습니다. 페이지 순서도 고정했습니다. 머리(기준일, 검색한 곳, 제목, 요약, 태그, 출처 구성), 2px 구분선과 출처 종류와 H2가 있는 절, 출처 표, 조사 방법, 공유 범위 한 줄 순서입니다. 그 밖에 둥근 모서리 10px의 흰 상자, "그림 N." 캡션, 위 첨자 인용 번호, 둥근 상태 알약, 한 파일 안의 한국어와 영어, AWS Korea Tech Blog 합쇼체가 들어 있습니다. aws-reports도 HTML을 만들지만, 그 HTML은 Word 파일과 같은 모양을 따릅니다(820px, 다른 색, 언어 전환 없음).

## 검토한 선택지

### 선택지 1: aws-reports의 세 번째 보고서 유형
- **장점**: 보고서 skill이 하나로 남고 `report.mjs`를 다시 씁니다
- **단점**: `report.mjs`는 Markdown 원고 하나로 Word와 HTML을 같은 스타일로 만듭니다. 두 번째 HTML 스타일과 두 언어 원고 형식을 넣으면 변환기와 검사기가 갈라집니다. HTML만 필요한 페이지에도 Node.js와 npm이 필요해집니다

### 선택지 2: Markdown 원고로 페이지를 빌드하는 새 skill
- **장점**: 모델은 Markdown을 쓰고 HTML은 스크립트가 만듭니다
- **단점**: 두 언어를 담는 Markdown 문법(또는 서로 어긋나는 원고 두 개)과 변환기를 관리해야 합니다. 구성 요소를 하나 늘릴 때마다 문법부터 정해야 합니다

### 선택지 3: 고정된 템플릿을 채우고 검사기로 확인하는 새 skill
- **장점**: 템플릿에 구성 요소, 토큰, 전환 스크립트가 모두 들어 있어 모델은 내용만 고칩니다. Python 표준 라이브러리만 씁니다. 변환기가 보장했을 것(짝, 순서, 번호, 토큰)을 검사기가 확인합니다
- **단점**: 모델이 HTML을 직접 고치므로 실수를 미리 막지 못하고 쓴 뒤에 잡습니다

## 결정
선택지 3을 택합니다. `skills/html-report/`에 `assets/template.html`, `references/design-spec.md`, `scripts/check_html.py`를 두고 세 파일이 같은 값을 갖습니다. 디자인을 바꿀 때는 세 파일을 함께 고칩니다. 한국어와 영어는 요소 짝으로 한 파일에 넣습니다. `lang="ko"` 요소 바로 뒤에 같은 태그의 `lang="en"` 요소를 두고, CSS 규칙 하나가 고르지 않은 언어를 숨깁니다. 그림은 한 번만 넣고 캡션만 짝을 이룹니다. 검사기는 `lang="ko"` 밖의 한국어를 거부합니다. 영어 화면에도 보이기 때문입니다. `data-report="research"`이면 출처 관련 요소가 필수이고 `general`이면 선택입니다. 페이지는 파일 하나로 유지합니다. `embed_images.py`가 상대 경로 그림을 data URI로 바꾸며, 페이지 폴더 안의 파일만 읽습니다.

## 결과

### 긍정적
- 새 의존성이 없습니다. `preview.py`는 `setup`이 이미 설치하는 Playwright를 쓰고, Playwright에 포함된 Node.js가 시작되지 않으면(`libatomic.so.1` 없음) 시스템 `node`로 다시 시도합니다
- 출처 구성 목록의 건수를 출처 표와 대조하므로 머리와 출처가 어긋나지 않습니다
- aws-reports는 그대로 둡니다

### 부정적
- 플러그인 안에 HTML 스타일이 둘 있습니다. aws-reports HTML은 Word 파일을, html-report는 이 형식을 따릅니다
- 블록마다 두 번 쓰므로 고칠 분량이 두 배쯤 됩니다

## 참고
- `skills/html-report/references/design-spec.md`
- `tests/structure/test-html-report.sh`
- [ADR-003](ADR-003-one-report-skill-global-npm.md)

# ADR-007: The HTML deck is converted from the finished PowerPoint deck

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-21)

## Context
aws-ppt-skills produced one thing, a `.pptx` on the bundled AWS template. The user asked for the same deck as HTML
as well, with the skill asking which output is wanted (PPT, HTML or both). The reference was the presenter guide
of another plugin's browser decks: a page that is presented in a browser, with a presenter view that shows the
notes, keyboard navigation, a slide overview and a pointer.

The skill already has a strict path for a deck: pptxgenjs helpers at fixed coordinates, the template applied by
`apply_template.py`, a lint (`check_deck.py`) and a render QA with LibreOffice. Whatever makes the HTML must not
open a second path where slides can differ from the deck.

## Options Considered

### Option 1: Slide pictures in a page
- **Pros**: a few lines of code (PDF pages to PNG, one `<img>` per slide); exact look
- **Cons**: text cannot be selected or searched and is not read by screen readers; large files; blurry on a
  bigger screen; the reference's own picture export has the same limits

### Option 2: A second source format for the page
- **Pros**: interactive slides (tabs, quizzes, step by step reveals), as in the reference plugin
- **Cons**: two sources for one talk, so the page and the deck drift; the design system, the helpers and the lint
  of this skill do not apply to it; the user asked for the same deck in two formats, not for a second deck

### Option 3: Record the helper calls during the build
- **Pros**: one build writes both files
- **Cons**: every pptxgenjs default has to be mirrored in the recorder; the template chrome is applied after the
  build, so the recorder never sees it; decks built by other skills (aws-infographic) would need the same block

### Option 4: Convert the finished `.pptx`
- **Pros**: one source and one QA path; the page holds what PowerPoint shows, read from the file itself; any deck
  this skill can deliver converts, including the editable decks of aws-infographic; the build script is unchanged
- **Cons**: a converter for the OOXML subset the helpers write (text, preset shapes, tables, pictures, charts);
  the template chrome needs a renderer; no interactive slide types

## Decision
Option 4.

- The Workflow asks the output format first: `PPT만`, `HTML만`, `PPT와 HTML 둘 다`. `HTML만` still builds and checks
  the `.pptx`, and delivers only the page.
- `scripts/deck_to_html.py` reads the final `.pptx` and writes one self-contained `.html`: text, shapes and tables
  as HTML at the deck's coordinates, charts as SVG drawn from the chart data, diagrams as their embedded SVG with
  the fonts they name, and the notes in a hidden block per slide.
- The template chrome (background, logo, copyright, page number, "Thank you!") is rendered by LibreOffice from a
  copy of the deck without slide content. One picture per layout is kept; a slide that differs from it (the page
  number) adds the differing rectangle only.
- Text geometry follows the renderer of the QA step, measured on LibreOffice output: a line is 1.2 times the font
  size, proportional spacing multiplies it, and the extra leading sits above the line.
- `assets/html/deck.css` and `deck.js` are the page's stage, controls and presenter view, copied into every page
  unchanged. The presenter view is the same file opened with `#presenter`; the two windows talk through
  `postMessage`, which also works for a file opened from a disk.
- `scripts/preview_html_deck.py` opens the page in Chromium, saves a picture of every slide, the slide list and
  the presenter view, and fails when the keys, the presenter window or the fonts do not work.
- The page is never written or edited by hand.

## Consequences

### Positive
- The deck and the page cannot differ in content: there is one build script and one checked `.pptx`
- The page works offline from one file, with selectable text, vector charts and vector diagrams
- The presenter gets notes, the next slide, a timer, a slide list, a laser pointer and a blank screen in a browser
- Printing the page gives a PDF with one slide per page

### Negative
- The converter must follow what the helpers write. A preset shape or a chart kind it does not know is reported
  as `WARN` and drawn as a rectangle or left out
- Charts in the page are drawings: tick steps and label placement are the converter's, not PowerPoint's
- The chrome is a raster picture (1920 px wide by default) and needs LibreOffice and Poppler at conversion time
- The notes are readable text inside the file unless `--no-notes` is given
- No animations, no theme switch and no interactive slide types; the reference's richer page is out of scope

## References
- `skills/aws-ppt-skills/SKILL.md` ("Workflow", "HTML Deck"), `skills/aws-ppt-skills/references/html-deck.md`
- `skills/aws-ppt-skills/scripts/deck_to_html.py`, `preview_html_deck.py`, `assets/html/`
- `tests/structure/test-aws-ppt-skills.sh`
- [ADR-006](ADR-006-infographic-editable-deck.md)

---

<a id="korean"></a>

# 한국어

## 상태
승인됨 (2026-11-21)

## 배경
aws-ppt-skills의 결과물은 포함된 AWS 템플릿 위에 만든 `.pptx` 하나였습니다. 사용자가 같은 덱을 HTML로도 받을 수
있게 하고, 어느 것을 만들지(PPT, HTML, 둘 다) skill이 묻게 해 달라고 요청했습니다. 참고 자료는 다른 플러그인의
브라우저 덱 발표자 안내였습니다. 브라우저에서 발표하고, 노트가 나오는 발표자 보기, 키보드 이동, 슬라이드 목록,
포인터가 있는 페이지입니다.

이 skill에는 덱을 만드는 정해진 경로가 있습니다. pptxgenjs 헬퍼로 고정 좌표에 그리고, `apply_template.py`로
템플릿을 적용하고, `check_deck.py`로 검사한 뒤 LibreOffice로 렌더해 확인합니다. HTML을 만드는 방법이 무엇이든
슬라이드가 덱과 달라질 수 있는 두 번째 경로를 열어서는 안 됩니다.

## 검토한 옵션

### 옵션 1: 슬라이드 그림을 페이지에 넣기
- **장점**: 코드가 몇 줄(PDF 쪽을 PNG로, 슬라이드마다 `<img>` 하나). 모양이 똑같음
- **단점**: 글자를 선택하거나 검색할 수 없고 화면 낭독기가 읽지 못함. 파일이 큼. 큰 화면에서 흐림. 참고한
  플러그인의 그림 내보내기도 같은 한계가 있음

### 옵션 2: 페이지용 원본 형식을 따로 두기
- **장점**: 탭, 퀴즈, 단계별 표시 같은 상호작용 슬라이드를 만들 수 있음(참고한 플러그인의 방식)
- **단점**: 발표 하나에 원본이 둘이라 페이지와 덱이 달라짐. 이 skill의 디자인 규칙, 헬퍼, 검사가 적용되지 않음.
  요청은 같은 덱의 두 형식이지 두 번째 덱이 아님

### 옵션 3: 빌드 중에 헬퍼 호출을 기록하기
- **장점**: 빌드 한 번으로 두 파일이 나옴
- **단점**: pptxgenjs의 기본값을 기록기에서 모두 다시 구현해야 함. 템플릿은 빌드 뒤에 적용되므로 기록기가 보지
  못함. 다른 skill(aws-infographic)이 만든 덱에도 같은 코드를 넣어야 함

### 옵션 4: 완성한 `.pptx`를 변환하기
- **장점**: 원본과 QA 경로가 하나. 페이지에는 PowerPoint가 보여 주는 내용이 파일에서 읽혀 들어감. 이 skill이
  전달할 수 있는 덱은 모두 변환됨(aws-infographic의 편집 가능한 덱 포함). 빌드 스크립트는 그대로임
- **단점**: 헬퍼가 쓰는 OOXML 범위(글자, 기본 도형, 표, 그림, 차트)를 읽는 변환기가 필요함. 템플릿 배경을 그릴
  렌더러가 필요함. 상호작용 슬라이드는 없음

## 결정
옵션 4를 택합니다.

- Workflow가 출력 형식을 가장 먼저 묻습니다. `PPT만`, `HTML만`, `PPT와 HTML 둘 다` 가운데 하나입니다. `HTML만`도
  `.pptx`를 만들고 검사한 뒤 페이지만 전달합니다.
- `scripts/deck_to_html.py`가 최종 `.pptx`를 읽어 한 파일짜리 `.html`을 만듭니다. 글자, 도형, 표는 덱의 좌표 그대로
  HTML로, 차트는 차트 데이터에서 그린 SVG로, 다이어그램은 덱에 든 SVG와 그 글꼴로 들어가고, 노트는 슬라이드마다
  숨긴 블록에 들어갑니다.
- 템플릿의 배경, 로고, 저작권 문구, 쪽 번호, "Thank you!"는 슬라이드 내용을 뺀 덱 사본을 LibreOffice가 그립니다.
  레이아웃마다 그림 하나를 두고, 그 그림과 다른 슬라이드(쪽 번호)는 달라진 사각형만 더합니다.
- 글자 배치는 QA 단계의 렌더러를 따릅니다. LibreOffice 결과를 재서 정했습니다. 한 줄은 글자 크기의 1.2배이고,
  배수 줄 간격은 그 값에 곱하며, 늘어난 간격은 줄 위쪽에 둡니다.
- `assets/html/deck.css`와 `deck.js`가 페이지의 무대, 조작 막대, 발표자 보기이고 모든 페이지에 그대로 들어갑니다.
  발표자 보기는 같은 파일을 `#presenter`로 연 것입니다. 두 창은 `postMessage`로 통신하므로 디스크에서 연
  파일에서도 동작합니다.
- `scripts/preview_html_deck.py`가 Chromium으로 페이지를 열어 슬라이드마다 그림을 저장하고, 슬라이드 목록과
  발표자 보기도 저장하며, 키, 발표자 창, 글꼴이 동작하지 않으면 실패합니다.
- 페이지는 손으로 쓰거나 수정하지 않습니다.

## 영향

### 긍정적
- 빌드 스크립트와 검사를 마친 `.pptx`가 하나뿐이므로 덱과 페이지의 내용이 달라지지 않습니다
- 페이지는 파일 하나로 오프라인에서 동작하고, 글자를 선택할 수 있으며 차트와 다이어그램이 벡터입니다
- 발표자는 브라우저에서 노트, 다음 슬라이드, 시간, 슬라이드 목록, 레이저 포인터, 화면 가리기를 사용합니다
- 페이지를 인쇄하면 슬라이드 한 장이 한 쪽인 PDF가 됩니다

### 부정적
- 변환기가 헬퍼가 쓰는 범위를 따라가야 합니다. 모르는 도형이나 차트 종류는 `WARN`으로 알리고 사각형으로
  그리거나 비워 둡니다
- 페이지의 차트는 그림입니다. 눈금 간격과 레이블 위치는 PowerPoint가 아니라 변환기가 정합니다
- 템플릿 배경은 래스터 그림(기본 너비 1920 px)이고 변환할 때 LibreOffice와 Poppler가 필요합니다
- `--no-notes`를 주지 않으면 노트가 파일 안에 읽을 수 있는 글자로 들어갑니다
- 애니메이션, 테마 전환, 상호작용 슬라이드는 없습니다. 참고한 페이지의 더 많은 기능은 범위 밖입니다

## 참고 자료
- `skills/aws-ppt-skills/SKILL.md` ("Workflow", "HTML Deck"), `skills/aws-ppt-skills/references/html-deck.md`
- `skills/aws-ppt-skills/scripts/deck_to_html.py`, `preview_html_deck.py`, `assets/html/`
- `tests/structure/test-aws-ppt-skills.sh`
- [ADR-006](ADR-006-infographic-editable-deck.md)

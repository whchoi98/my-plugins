# ADR-006: aws-infographic joins the plugin and rebuilds its content as an editable deck

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-18)

## Context
The author's aws-infographic skill existed only as a claude.ai skill: one SKILL.md with `infokit.py`,
`buildkit.py` and the page template pasted as code blocks, and paths that exist only in the claude.ai container.
Claude Code loaded it as a synced copy (`anthropic-skills:aws-infographic`). claude.ai overwrites that copy, so a
change made on the machine does not last and nothing in it can be tested.

The user then asked for a PowerPoint deck of the infographic's content, made with aws-ppt-skills, with one
condition: the SVG must not be placed on the slides, and the deck must be built from icons and shapes so that it
can be edited.

## Options Considered

### Option 1: Place the infographic on slides as a picture
- **Pros**: the deck looks exactly like the infographic; `addDiagram()` already embeds an SVG with a PNG fallback
- **Cons**: one picture per slide, so no text or shape can be changed in PowerPoint; the request excludes it

### Option 2: Convert the drawing into shapes at the same coordinates
- **Pros**: deterministic; a second backend of `infokit.py` could emit a rectangle, line or text box per SVG element
- **Cons**: the infographic is drawn for a 1920px canvas, so its 14px body text becomes 7pt on a 13.33 in slide;
  the result ignores the deck's type scale, colors and body zone; hundreds of small text boxes are editable only
  in name

### Option 3: Rebuild the content with the deck's own design system, and check the result
- **Pros**: slides are readable and follow the template; tables and graphs become PowerPoint tables and charts
  with data; the text comes from the same `T` dict as the infographic; a script can prove what "editable" means
- **Cons**: the model rebuilds each section, so the deck's layout differs from the infographic and needs its own
  render QA

## Decision
Option 3, with the skill moved into the plugin.

- `skills/aws-infographic/` ships the code as files (`scripts/infokit.py`, `scripts/buildkit.py`,
  `assets/page_template.py`). The work folder gets copies, and `infokit.py` finds the aws-diagram icon bundle
  through `AWS_ICON_BUNDLE`, a `.aws-icon-bundle` file next to the copy, the sibling skill, then installed copies.
- Step 9 of the skill calls `my-plugins:aws-ppt-skills` and follows `references/ppt-deck.md`: one content slide
  per section, built from text boxes, shapes, native tables (`addGrid()`), native charts and AWS icons.
- Icons are PNG pictures, one per icon, named `icon:<set/name>` by `addIcon()`. No SVG is placed, icons included,
  because the request asks for a deck without SVG.
- `scripts/check_editable.py` (standard library) fails a deck that links an SVG, holds a picture that is not an
  icon, or holds an icon larger than 1.2 in. `check_deck.py` in aws-ppt-skills uses the same limit when it skips
  its vector-SVG warning for icon pictures.

## Consequences

### Positive
- The skill is versioned, tested and released with the other skills, and reaches aws-ppt-skills by a relative path
- Every element of the deck can be selected and changed in PowerPoint; a pasted figure is caught by a script
- The infographic and the deck cannot drift in wording: both read the page module's `T` dict

### Negative
- Two layouts to check for each topic: the infographic's QA report and the deck's rendered slides
- Icons are raster images (256px by default) and cannot be recolored in PowerPoint
- `check_editable.py` proves which kinds of objects a deck holds, not that the deck carries the whole content
- A claude.ai skill named `aws-infographic` answers the same requests until the user turns it off

## References
- `skills/aws-infographic/SKILL.md`, `skills/aws-infographic/references/ppt-deck.md`
- `skills/aws-ppt-skills/SKILL.md` ("Charts and Diagrams", `addIcon()`)
- `tests/structure/test-aws-infographic.sh`
- [ADR-002](ADR-002-merge-four-plugins-into-one.md)

---

<a id="korean"></a>

# 한국어

## 상태
승인됨 (2026-11-18)

## 배경
글쓴이의 aws-infographic skill은 claude.ai skill로만 있었습니다. `SKILL.md` 한 파일에 `infokit.py`, `buildkit.py`,
장 템플릿이 코드 블록으로 들어 있었고 경로는 claude.ai 컨테이너에만 있는 것이었습니다. Claude Code는 이를 동기화
사본(`anthropic-skills:aws-infographic`)으로 불러왔습니다. claude.ai가 그 사본을 덮어쓰므로 장비에서 고친 내용은
유지되지 않고 테스트도 할 수 없었습니다.

이어서 사용자가 인포그래픽 내용을 aws-ppt-skills로 PowerPoint 덱으로도 만들어 달라고 요청했습니다. 조건은 하나였습니다.
슬라이드에 SVG를 넣지 않고, 고칠 수 있도록 아이콘과 도형으로 만드는 것입니다.

## 검토한 옵션

### 옵션 1: 인포그래픽을 그림으로 슬라이드에 넣기
- **장점**: 덱이 인포그래픽과 똑같이 보임. `addDiagram()`이 이미 SVG와 PNG 대체 그림을 넣어 줌
- **단점**: 슬라이드마다 그림 한 장이라 PowerPoint에서 글자와 도형을 고칠 수 없음. 요청에서 제외한 방식

### 옵션 2: 그림을 같은 좌표의 도형으로 변환하기
- **장점**: 결과가 정해져 있음. `infokit.py`에 출력 방식을 하나 더 두고 SVG 요소마다 사각형, 선, 텍스트 상자를 내면 됨
- **단점**: 인포그래픽은 1920px 캔버스 기준이라 14px 본문이 13.33 in 슬라이드에서 7pt가 됨. 덱의 글자 크기, 색,
  본문 영역 규칙을 따르지 않음. 작은 텍스트 상자 수백 개는 이름만 편집 가능

### 옵션 3: 덱의 디자인 규칙으로 내용을 다시 만들고 결과를 검사하기
- **장점**: 슬라이드를 읽을 수 있고 템플릿을 따름. 표와 그래프가 데이터가 든 PowerPoint 표와 차트가 됨. 문구가
  인포그래픽과 같은 `T` dict에서 나옴. "편집 가능"의 뜻을 스크립트로 확인할 수 있음
- **단점**: 모델이 섹션마다 다시 만들기 때문에 배치가 인포그래픽과 다르고, 덱의 렌더 QA가 따로 필요함

## 결정
옵션 3을 택하고 skill을 플러그인 안으로 옮깁니다.

- `skills/aws-infographic/`은 코드를 파일로 배포합니다(`scripts/infokit.py`, `scripts/buildkit.py`,
  `assets/page_template.py`). 작업 폴더에는 사본을 두고, `infokit.py`는 aws-diagram 아이콘 번들을 `AWS_ICON_BUNDLE`,
  사본 옆의 `.aws-icon-bundle` 파일, 옆 skill, 설치된 사본 순서로 찾습니다.
- skill의 9단계가 `my-plugins:aws-ppt-skills`를 부르고 `references/ppt-deck.md`를 따릅니다. 섹션 하나가 내용 슬라이드
  한 장이고 텍스트 상자, 도형, PowerPoint 표(`addGrid()`), 차트, AWS 아이콘으로 만듭니다.
- 아이콘은 하나씩 놓는 PNG 그림이고 `addIcon()`이 `icon:<set/name>`으로 이름을 붙입니다. 요청이 SVG 없는 덱이므로
  아이콘도 SVG로 넣지 않습니다.
- `scripts/check_editable.py`(표준 라이브러리)는 SVG가 연결된 덱, 아이콘이 아닌 그림이 든 덱, 1.2 in보다 큰 아이콘이
  든 덱을 실패로 처리합니다. aws-ppt-skills의 `check_deck.py`는 아이콘 그림에 벡터 SVG 경고를 내지 않을 때 같은
  한도를 씁니다.

## 영향

### 긍정적
- skill이 다른 skill과 함께 버전을 갖고 테스트와 릴리스를 거치며, aws-ppt-skills를 상대 경로로 찾습니다
- 덱의 모든 요소를 PowerPoint에서 선택해 고칠 수 있고, 그림을 붙인 슬라이드는 스크립트가 잡습니다
- 인포그래픽과 덱이 같은 장 모듈의 `T` dict를 읽으므로 문구가 서로 달라지지 않습니다

### 부정적
- 주제마다 확인할 배치가 둘입니다. 인포그래픽의 QA 리포트와 덱의 렌더 결과를 따로 봐야 합니다
- 아이콘은 래스터 이미지(기본 256px)라서 PowerPoint에서 색을 바꿀 수 없습니다
- `check_editable.py`는 덱에 든 개체의 종류를 확인할 뿐이고, 내용이 빠짐없이 옮겨졌는지는 확인하지 않습니다
- claude.ai의 `aws-infographic` skill은 사용자가 끄기 전까지 같은 요청에 반응합니다

## 참고 자료
- `skills/aws-infographic/SKILL.md`, `skills/aws-infographic/references/ppt-deck.md`
- `skills/aws-ppt-skills/SKILL.md` ("Charts and Diagrams", `addIcon()`)
- `tests/structure/test-aws-infographic.sh`
- [ADR-002](ADR-002-merge-four-plugins-into-one.md)

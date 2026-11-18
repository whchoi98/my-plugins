# 인포그래픽 내용을 편집 가능한 PowerPoint 덱으로

인포그래픽 QA가 끝난 뒤 읽는다. 덱은 `my-plugins:aws-ppt-skills`의 규칙과 helper로 만든다. 이 문서는 그 위에 더하는 것만 정한다: 편집 가능 규칙, 인포그래픽 내용을 슬라이드로 옮기는 대응, 추가 helper, 검사.

## 1. 준비

1. Skill 도구로 `my-plugins:aws-ppt-skills`를 부른다. 그 skill이 묻는 네 가지(템플릿 테마, 청중 규모, 발표자 정보, 내용)는 인포그래픽 1단계에서 받은 답으로 채우고 다시 묻지 않는다. 답이 없었으면 블랙 테마, 50명 미만 기술 세미나, 기본 발표자로 진행한다.
2. 덱 작업 폴더는 `$W/deck`이다. `build_deck.js`, 아이콘 PNG(`icons/`), 결과 `.pptx`를 여기에 둔다. `<DeckName>`은 인포그래픽의 slug이고, 시리즈면 시리즈 이름이다.
3. 내용은 장 모듈의 `T` dict와 검증 로그(`$W/sources.md`)에서 가져온다. 인포그래픽에 없는 수치, 주장, 서비스를 덱에서 새로 만들지 않는다. 표 머리글, 콜아웃 label, 체크 표시를 대신하는 "있음", "없음"처럼 구조를 읽게 하는 이름표는 붙여도 된다. 검증 로그가 없으면 발표자 노트에는 `T`의 문구만 풀어 쓴다.

## 2. 편집 가능 규칙

- 인포그래픽 SVG, PNG를 슬라이드에 넣지 않는다. 일부를 잘라 넣는 것도 같다.
- 이 덱에서는 aws-ppt-skills의 `addDiagram()`, `svg_to_png.py`를 쓰지 않는다. 구조도와 흐름도도 `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`의 SVG로 넣지 않고 도형으로 만든다.
- 그림은 AWS 아이콘만 쓴다. 아이콘도 SVG가 아니라 `icon_png.py`가 만든 PNG를 `addIcon()`으로 하나씩 놓는다.
- 글자를 그림으로 굽지 않는다. 도형 안의 글자는 그 도형 위에 놓은 텍스트 상자다.
- 슬라이드의 모든 요소는 아래 표의 PowerPoint 기본 개체로 만든다.

| 요소 | 만드는 방법 | PowerPoint에서 고칠 수 있는 것 |
|---|---|---|
| 글 | `s.addText()` | 문구, 크기, 색 |
| 상자, 칩, 막대, 원 | `s.addShape()`의 `roundRect`, `rect`, `ellipse` | 위치, 크기, 채움, 테두리 |
| 선, 화살표, 점선 | `s.addShape("line", { line: { endArrowType: "triangle", dashType: "dash" } })` | 끝 모양, 굵기, 방향 |
| 표 | `addGrid()` (PowerPoint 표) | 셀 문구, 행과 열 추가와 삭제 |
| 수치 그래프 | `addNativeChart()` (Excel 데이터 포함) | 데이터 편집 |
| AWS 아이콘 | `addIcon()`, `addIconRow()` (PNG 그림 한 개씩) | 위치, 크기, 교체 |

## 3. 덱 구성

| 인포그래픽 | 덱 |
|---|---|
| 장 제목, 영문 부제, 한글 부제 | 표지(COVER)의 제목, 부제, tagline. eyebrow는 시리즈 이름이고, 한 장짜리면 주제를 가리키는 영문 두세 낱말이다 |
| 시리즈의 장 목록(`series_nav`) | Agenda(AGENDA) 한 장과 장마다 구분 슬라이드(DIVIDER). 표지 제목은 시리즈 이름으로 쓰고 장 제목은 구분 슬라이드에 둔다. 한 장짜리 인포그래픽에는 Agenda를 넣지 않는다 |
| 섹션 하나(번호, 제목, take) | 내용 슬라이드(CONTENT) 한 장. 제목은 번호를 붙인 섹션 제목("1. 요청 경로"), 부제는 take. 문구가 "4단계"처럼 번호로 다른 섹션을 가리키므로 번호를 뺀 제목은 쓰지 않는다 |
| 섹션의 시각 표현 | 4번 대응표에 따라 기본 개체로 다시 만든 본문 |
| 콜아웃 | `addDefBox()`. 슬라이드당 1개까지 |
| 각주(가정, 근사, 설명용 예시) | 그 수치가 나오는 슬라이드의 발표자 노트. 덱 전체에 걸친 각주는 마무리 슬라이드의 tagline에 한 줄로 줄여 쓰고, 줄이면서 뺀 부분은 그 슬라이드의 노트에 둔다 |
| 검증 로그 | 발표자 노트의 수치 설명. 출처 URL은 최종 답변의 Sources에 둔다 |
| 0부 통합 개요 | 계층 표와 진단표를 `addGrid()`로 한 장씩 |
| 섹션 밖 요소 | 장 전체를 요약하는 띠는 표지 다음의 내용 슬라이드 한 장으로 만든다. 범례와 섹션 사이 화살표는 옮기지 않는다 |

- 한 장에 다 들어가지 않으면 글자를 줄이지 않고 두 장으로 나눈다. 표는 머리글을 빼고 6행, 타임라인은 6레인이 한 장의 기준이다.
- 마지막 장은 마무리 슬라이드(CLOSING)다.
- 발표자 노트는 aws-ppt-skills 규칙대로 모든 슬라이드에 넣는다. 인포그래픽의 한 줄 요지와 검증한 수치를 문장으로 풀어 쓴다.

## 4. 시각 표현 대응표

| 인포그래픽의 표현 | 덱에서 만드는 방법 |
|---|---|
| 비교 표, 세대 비교 표, 증상 진단표, 계층 매트릭스 | `addGrid()` |
| 요청 타임라인, 간트 | `addLanes()` |
| 비중 비교 스택 바 | `addNativeChart(s, "stackedBar", data, { raw: { barGrouping: "percentStacked", valAxisLabelFormatCode: "0%" } })`. 값이 두세 개면 `addBudgetBars()` |
| Roofline, 수치 추이 | `addNativeChart()`의 `line`, `scatter` |
| dot list | `addSteps()` (번호 배지와 문구). 두 목록을 나란히 비교하면 `add2Col()` |
| 줌인 패널 | 패널마다 `roundRect`, 줌인 선은 점선 `line` 두 개 |
| 계층 사다리 | 층마다 `roundRect`와 텍스트 상자, 층 사이는 `line` |
| 칩, 태그, 알약 | `roundRect`(`rectRadius`는 높이의 절반)와 텍스트 상자 |
| 이름표와 한 줄 내용이 반복되는 행 | `addGrid(s, null, rows)` (머리글 없는 표) |
| 상자와 화살표로 그린 흐름, 갈림 | 상자는 `roundRect`와 텍스트 상자, 화살표는 `line`에 `endArrowType: "triangle"` |
| 주의, 경고 상자 | `addDefBox()`. label을 "주의"처럼 뜻이 드러나는 말로 쓴다 |
| 체크, 엑스 표시 | 표 안의 "있음", "없음" 같은 글자. 덱 본문 폰트에는 "✓", "✗", "•" 글리프가 없다 |
| AWS 아이콘과 이름, 설명 | `addIconRow()`. 한 줄에 2개, 설명이 짧으면 3개까지 놓고 더 많으면 줄을 나눠 다시 부른다 |

대응표에 없는 표현은 가장 가까운 행을 따른다. 어느 경우든 2번 표의 기본 개체만 쓴다.

## 5. 색과 글자

- 색은 aws-ppt-skills의 정책을 그대로 따른다. 50명 미만이면 강조색은 `C.subtitleOrange` 하나다. 부제, label, 강조 값이 그 색을 쓰고, 도형은 강조할 것만 그 색으로 칠하며 나머지는 회색 계열로 둔다. 인포그래픽에서 색으로 구분하던 뜻(경고, 조치)은 "주의", "조치" 같은 label 글자로 옮긴다.
- 인포그래픽의 색 의미(blue 연산, yellow 메모리, purple 모델, pink 경고)는 청중 규모가 100명 이상일 때만 `C.awsBlue`, `C.awsYellow`, `C.awsPurple`, `C.awsPink`로 옮긴다. 덱 팔레트에 없는 green(조치, 정상)은 `C.awsCyan`으로 쓴다.
- 글자 크기는 aws-ppt-skills의 `SZ`를 쓴다. 인포그래픽의 좌표와 글자 크기를 그대로 옮기지 않는다(1920px 그림의 14px 본문은 슬라이드에서 7pt가 된다). 옮기는 것은 문구와 구조다.
- 표기 규칙은 인포그래픽과 같다. 명사형으로 끝내고 "·"와 "—"를 쓰지 않는다. 문구가 한 줄에 들어가지 않으면 뜻을 지키면서 줄인다.
- 도형 옆이나 안에 놓는 한 줄 글(칩, 배지 옆 문구, 막대 안 글자)은 `lineSpacingMultiple`을 1.0~1.2로 둔다. 1.5는 여러 줄 본문에 쓴다. 1.5로 두면 한 줄 글이 도형의 가운데보다 아래로 내려간다.
- 인포그래픽에서 `CODE_FAMILY`로 그린 실제 코드는 `addCodeBox()`에 넣는다. 문장 안의 짧은 식별자와 숫자 나열은 본문 폰트로 쓴다.

## 6. 아이콘

```bash
uv run --no-project --with playwright==1.64.1 --with pillow python -B "${CLAUDE_SKILL_DIR}/scripts/icon_png.py" \
  "$W/deck/icons" --theme dark service/Amazon-Bedrock service/Amazon-CloudWatch
```

- `--theme dark`는 블랙 템플릿, `--theme light`는 화이트 템플릿에 쓴다. 다크는 인포그래픽과 같이 어두운 글리프를 밝게 바꾼다.
- 이름은 인포그래픽에서 쓴 `set/name` 그대로다. 파일은 `<set>-<name>.png`로 생긴다.
- 아이콘 한 변은 design 단위 0.30~0.60으로 둔다. 슬라이드에서 1.2 in보다 큰 아이콘은 검사에서 걸린다.

## 7. 추가 helper

aws-ppt-skills의 helper 블록 바로 뒤에 붙인다. `addIcon()`은 aws-ppt-skills helper 블록에 있다.

```javascript
// ── Infographic deck helpers: paste right after the aws-ppt-skills helper block ──
// Each one draws PowerPoint objects only (table, shapes, text boxes, icon pictures), so every element
// stays editable. Coordinates are design units like the rest of the build.

// PowerPoint table with N columns. head = ["구간", "지연 원인"] or null (no header row), rows = [["네트워크", "리전 거리"], ...]
// opts: { x, y, w, h, colW: [..] (design in, sums to w), size, emphRow: row index painted with the accent }
function addGrid(s, head, rows, opts = {}) {
  const x = opts.x ?? 0.42, y = opts.y ?? 1.50, w = opts.w ?? 9.16, h = opts.h ?? 2.95;
  const size = opts.size || SZ.body;
  const colW = opts.colW || rows[0].map(() => w / rows[0].length);
  const line = { type: "solid", pt: 0.75, color: C.hairline };
  const cell = (t, o) => ({ text: String(t), options: { fontFace: FONT, fontSize: size, valign: "middle", border: line, ...o } });
  const table = head ? [head.map((t) => cell(t, { color: C.subtitleOrange, fill: { color: C.bgCard } }))] : [];
  rows.forEach((r, ri) => {
    const emph = ri === opts.emphRow;
    table.push(r.map((t, ci) => cell(t, emph
      ? { color: C.onAccent, fill: { color: C.subtitleOrange } }
      : { color: ci === 0 ? C.ink : C.charcoal })));
  });
  s.addTable(table, { x: x, y: y, w: w, colW: colW, rowH: table.map(() => h / table.length), autoPage: false });
}

// Numbered list in one card: a badge with the number, one phrase per row. items = ["...", "..."]
// opts: { x, y, w, h, size }
function addSteps(s, items, opts = {}) {
  const x = opts.x ?? 0.42, y = opts.y ?? 1.50, w = opts.w ?? 9.16, h = opts.h ?? 1.75;
  const size = opts.size || SZ.emph, rowH = (h - 0.24) / items.length, d = Math.min(0.30, rowH - 0.10);
  s.addShape("roundRect", { x: x, y: y, w: w, h: h, fill: { color: C.bgCard }, line: { color: C.hairline, width: 0.75 }, rectRadius: 0.06 });
  items.forEach((t, i) => {
    const ry = y + 0.12 + i * rowH, by = ry + (rowH - d) / 2;
    s.addShape("ellipse", { x: x + 0.20, y: by, w: d, h: d, fill: { color: C.bgCard }, line: { color: C.subtitleOrange, width: 1 } });
    s.addText(String(i + 1), { x: x + 0.20, y: by, w: d, h: d, fontFace: FONT, fontSize: 10, color: C.subtitleOrange, align: "center", valign: "middle", lineSpacingMultiple: 1.0, margin: 0 });
    s.addText(t, { x: x + 0.34 + d, y: ry, w: w - d - 0.54, h: rowH, fontFace: FONT, fontSize: size, color: C.charcoal, valign: "middle", lineSpacingMultiple: 1.2 });
  });
}

// Icon cards in one row: AWS icon, name, one-line description. items = [{ png, ref, name, desc }]
// 2 cards per row at full width (3 when the descriptions are short); call it again for another row.
// opts: { x, y, w, h }
function addIconRow(s, items, opts = {}) {
  const x = opts.x ?? 0.42, y = opts.y ?? 3.40, w = opts.w ?? 9.16, h = opts.h ?? 0.95;
  const gap = 0.10, cw = (w - gap * (items.length - 1)) / items.length, ic = Math.min(0.50, h - 0.30);
  items.forEach((it, i) => {
    const cx = x + i * (cw + gap), tx = cx + 0.18 + ic + 0.14, tw = cw - ic - 0.46;
    s.addShape("roundRect", { x: cx, y: y, w: cw, h: h, fill: { color: C.bgCard }, line: { color: C.hairline, width: 0.75 }, rectRadius: 0.06 });
    addIcon(s, { png: it.png, ref: it.ref, x: cx + 0.18, y: y + (h - ic) / 2, size: ic, alt: it.name });
    s.addText(it.name, { x: tx, y: y + 0.10, w: tw, h: (h - 0.20) / 2, fontFace: FONT, fontSize: SZ.emph, color: C.ink, valign: "middle", lineSpacingMultiple: 1.2 });
    s.addText(it.desc, { x: tx, y: y + h / 2, w: tw, h: (h - 0.20) / 2, fontFace: FONT, fontSize: SZ.body, color: C.slate, valign: "middle", lineSpacingMultiple: 1.2 });
  });
}

// Lane timeline (request timeline, Gantt): one row per lane, bars on a shared 0..total scale.
// lanes = [{ label, bars: [{ from, to, text, emph: true, dashed: true }] }]
// opts: { x, y, w, h, total: 1000, labelW: 1.50, marks: [{ from, to, text }] }   marks = spans under the lanes (TTFT, E2E)
function addLanes(s, lanes, opts = {}) {
  const x = opts.x ?? 0.42, y = opts.y ?? 1.50, w = opts.w ?? 9.16, h = opts.h ?? 2.95;
  const total = opts.total ?? 1000, labelW = opts.labelW ?? 1.50, marks = opts.marks || [];
  const markH = 0.36, laneH = (h - marks.length * markH) / lanes.length, barH = Math.min(0.40, laneH - 0.12);
  const tx = x + labelW, tw = w - labelW, px = (v) => tx + tw * v / total;
  lanes.forEach((lane, i) => {
    const ly = y + i * laneH, by = ly + (laneH - barH) / 2;
    s.addText(lane.label, { x: x, y: ly, w: labelW - 0.10, h: laneH, fontFace: FONT, fontSize: SZ.body, color: C.charcoal, valign: "middle", lineSpacingMultiple: 1.2 });
    s.addShape("line", { x: tx, y: ly + laneH, w: tw, h: 0, line: { color: C.hairline, width: 0.5 } });
    lane.bars.forEach((b) => {
      const bx = px(b.from), bw = px(b.to) - bx;
      s.addShape("rect", { x: bx, y: by, w: bw, h: barH, fill: { color: b.emph ? C.subtitleOrange : C.bgCard },
        line: { color: b.emph ? C.subtitleOrange : C.steel, width: 0.75, dashType: b.dashed ? "dash" : "solid" } });
      if (b.text) s.addText(b.text, { x: bx, y: by, w: bw, h: barH, fontFace: FONT, fontSize: 10, color: b.emph ? C.onAccent : C.charcoal, align: "center", valign: "middle", lineSpacingMultiple: 1.0, margin: 0 });
    });
  });
  marks.forEach((m, i) => {
    const my = y + lanes.length * laneH + i * markH + 0.10, mx = px(m.from), mw = px(m.to) - mx;
    s.addShape("line", { x: mx, y: my, w: mw, h: 0, line: { color: C.subtitleOrange, width: 1.5, beginArrowType: "oval", endArrowType: "triangle" } });
    s.addText(m.text, { x: mx, y: my + 0.02, w: mw, h: markH - 0.12, fontFace: FONT, fontSize: 10, color: C.subtitleOrange, align: "center", valign: "middle", lineSpacingMultiple: 1.0, margin: 0 });
  });
}
```

## 8. 예시: 페이지 템플릿의 내용을 옮긴 덱

`assets/page_template.py`의 `T` dict를 덱으로 옮긴 것이다. 섹션 1은 표와 콜아웃, 섹션 2는 번호 목록과 AWS 아이콘이다. helper 블록 두 개 뒤에 이어 붙이고 문구만 바꿔 쓴다.

```javascript
// ── Deck content: one CONTENT slide per infographic section ──
const ICONS = "icons";                              // icon_png.py output folder, next to build_deck.js

let s = newSlide("COVER");
addCoverSlide(s, { eyebrow: "LLM API Latency", title: "요청 경로별 지연 구조",
  subtitle: "Where Latency Comes From", tagline: "구간별 원인과 대응 조치" });
s.addNotes(["안녕하세요, 오늘은 LLM 서비스의 지연이 요청 경로의 어느 구간에서 생기는지 살펴보겠습니다.",
  "같은 내용을 한 장으로 정리한 인포그래픽이 있고, 이 덱은 그 내용을 구간별로 나눠 설명합니다.",
  "먼저 구간마다 지연이 생기는 원인을 보고, 이어서 효과가 큰 순서로 대응 조치를 정리하겠습니다.",
  "수치는 설명을 돕는 예시이므로 실제 값은 운영 환경에서 측정해 확인하시기 바랍니다."]);

s = newSlide("CONTENT");                            // 섹션 1: rows -> PowerPoint 표, insight -> 콜아웃
addContentHeader(s, "1. 요청 경로", "구간마다 보는 지표가 다름");
addGrid(s, ["구간", "지연 원인", "재시도 효과"], [
  ["네트워크", "리전 거리, TLS 핸드셰이크", "있음"],
  ["대기열", "동시 요청 급증", "있음"],
  ["Prefill", "긴 입력", "없음"],
], { y: 1.50, h: 1.90, colW: [2.00, 5.16, 2.00] });
addDefBox(s, "KEY INSIGHT", ["첫 글자 지연의 대부분은 대기와 Prefill", "입력 길이와 동시 요청 수를 함께 확인"], 3.55);
s.addNotes(["요청 경로를 Network, Queue, Prefill 세 구간으로 나누면 구간마다 봐야 할 지표가 달라집니다.",
  "Network 구간의 지연은 리전까지의 거리와 TLS 핸드셰이크에서 생기고, 재시도로 줄어드는 경우가 있습니다.",
  "Queue 구간은 동시 요청이 몰릴 때 길어지며, 이 구간도 재시도가 효과를 냅니다.",
  "Prefill 구간은 입력이 길수록 길어지고 재시도로는 줄어들지 않습니다.",
  "따라서 첫 글자가 늦을 때는 입력 길이와 동시 요청 수를 함께 확인해야 합니다."]);

s = newSlide("CONTENT");                            // 섹션 2: bullets -> 번호 목록, aws -> 아이콘 카드
addContentHeader(s, "2. 대응 조치", "효과가 큰 순서");
addSteps(s, ["스트리밍으로 첫 글자를 앞당김", "Prompt caching으로 반복 입력 재사용", "작은 모델로 라우팅"], { y: 1.50, h: 1.75 });
addIconRow(s, [{ png: ICONS + "/service-Amazon-Bedrock.png", ref: "service/Amazon-Bedrock",
  name: "Amazon Bedrock", desc: "교차 리전 추론으로 처리량 분산" }], { y: 3.40, h: 0.95 });
s.addNotes(["대응 조치는 효과가 큰 순서로 세 가지입니다.",
  "첫째로 Streaming을 사용하면 전체 응답을 기다리지 않고 첫 글자를 먼저 받습니다.",
  "둘째로 Prompt caching은 반복되는 입력을 다시 계산하지 않게 해 Prefill 구간을 줄입니다.",
  "셋째로 작은 모델로 라우팅하면 같은 요청을 더 짧은 시간에 처리합니다.",
  "AWS에서는 Amazon Bedrock의 교차 리전 추론으로 처리량을 여러 리전에 나눌 수 있습니다."]);

s = newSlide("CLOSING");
addClosingSlide(s, { tagline: "수치는 설명용 예시" });
s.addNotes(["지금까지 요청 경로의 구간별 지연 원인과 대응 조치를 살펴봤습니다.",
  "첫 글자 지연은 대기와 Prefill에서 대부분 생긴다는 점을 기억해 주시기 바랍니다.",
  "이 덱의 표와 도형은 모두 PowerPoint에서 직접 고칠 수 있습니다.",
  "궁금하신 점은 메일이나 LinkedIn으로 연락해 주시면 답변드리겠습니다."]);

pres.writeFile({ fileName: "infographic_raw.pptx" });
```

## 9. 빌드와 검사

```bash
cd "$W/deck"
bash "${CLAUDE_SKILL_DIR}/../aws-ppt-skills/scripts/install_fonts.sh"   # 세션에 한 번: 렌더 확인에 쓰는 덱 폰트
export NODE_PATH="$(npm root -g)"
node build_deck.js                                                     # → <DeckName>_raw.pptx
python3 "${CLAUDE_SKILL_DIR}/../aws-ppt-skills/scripts/apply_template.py" <DeckName>_raw.pptx --out <DeckName>.pptx
python3 "${CLAUDE_SKILL_DIR}/../aws-ppt-skills/scripts/check_deck.py" <DeckName>.pptx      # ERROR 0, WARN은 하나씩 확인
python3 "${CLAUDE_SKILL_DIR}/scripts/check_editable.py" <DeckName>.pptx                    # ERROR 0
soffice --headless --convert-to pdf <DeckName>.pptx && rm -f qa-*.jpg && pdftoppm -jpeg -r 100 <DeckName>.pdf qa
```

- `check_deck.py`의 WARN은 하나씩 읽고 고친다. 내용인 시간 값(예: "IP당 5분 300회")에 뜬 발표 시간 경고는 그대로 두고 최종 답변에 적는다. 문장을 바꿔 검사를 피하지 않는다.
- `check_editable.py`는 슬라이드에 연결된 SVG, 아이콘이 아닌 그림, 1.2 in보다 큰 아이콘을 ERROR로 알린다. ERROR가 있으면 그 요소를 도형, 표, 차트로 다시 만든다. `--icon-max`를 올려서 통과시키지 않는다.
- 슬라이드마다 텍스트와 도형, 선, 표, 차트, 아이콘의 개수가 나온다. 내용 슬라이드인데 표와 차트가 0이고 도형이 서너 개뿐이면 인포그래픽의 구조가 빠진 것이므로 대응표를 다시 본다.
- 렌더한 `qa-*.jpg`를 한 장씩 보고 글자 넘침, 줄바꿈, 겹침을 고친다. 점검 항목은 aws-ppt-skills의 Pre-Delivery QA Checklist를 따른다. 다만 17번(다이어그램은 SVG)은 이 덱에 적용하지 않고, 15번의 GitHub 링크는 사용자가 저장소를 알려 준 경우에만 넣는다.
- PowerPoint에서 표의 셀, 도형, 아이콘이 하나씩 선택되는지는 사용자가 열어 보고 확인한다. 최종 답변에 그 확인이 남아 있다고 적는다.

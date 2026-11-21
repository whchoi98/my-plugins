// Deck content for tests/structure/test-aws-ppt-skills.sh. The test puts the helper block of
// skills/aws-ppt-skills/SKILL.md in front of this file, so every helper below is the shipped one.
// One slide per kind of element the HTML deck must carry: cover, agenda, divider, cards, bullets and a card
// table, a terminal box, three native charts, a diagram picture with its SVG, an icon, a native table,
// a link, text that looks like markup, and the closing slide.
let s = newSlide("COVER");
addCoverSlide(s, { eyebrow: "html deck fixture", title: "HTML 덱 변환 검증", subtitle: "PPT와 같은 내용의 브라우저 발표 자료", tagline: "변환 시험용 덱" });
s.addNotes(["표지 노트 첫 문장입니다.", "표지 노트 둘째 문장입니다.", "표지 노트 셋째 문장입니다.", "</aside><script>alert(1)</script> 노트 안의 꺾쇠"]);

s = newSlide("AGENDA");
addAgendaSlide(s, "Fixture", [{ num: "01", title: "구성 요소", meta: "카드, 표, 코드" }, { num: "02", title: "차트와 그림", meta: "막대, 도넛, 선" }]);
s.addNotes(["목차 노트 첫 문장입니다.", "목차 노트 둘째 문장입니다.", "목차 노트 셋째 문장입니다.", "목차 노트 넷째 문장입니다."]);

s = newSlide("DIVIDER");
addSectionDivider(s, "01", "구성 요소", "카드, 표, 코드 상자");
s.addNotes(["구분 노트 첫 문장입니다.", "구분 노트 둘째 문장입니다.", "구분 노트 셋째 문장입니다.", "구분 노트 넷째 문장입니다."]);

s = newSlide("CONTENT");
addContentHeader(s, "정의 상자와 카드", "DEFINITION + 4-CARD GRID");
const boxH = addDefBox(s, "DEFINITION", ["세션 단위 격리 실행 환경", "컨테이너 이미지 배포"], 1.45);
addFourCardGrid(s, [
  { label: "RUNTIME", title: "세션 격리 실행", body: "microVM 단위 격리" }, { label: "MEMORY", title: "단기, 장기 기억", body: "이벤트 저장" },
  { label: "GATEWAY", title: "도구 연결", body: "MCP 변환" }, { label: "IDENTITY", title: "자격 증명 위임", body: "토큰 보관" }], { y: 1.45 + boxH + 0.10, h: 2.40 });
s.addNotes(["카드 노트 첫 문장입니다.", "카드 노트 둘째 문장입니다.", "카드 노트 셋째 문장입니다.", "카드 노트 넷째 문장입니다."]);

s = newSlide("CONTENT");
addContentHeader(s, "두 칸 비교와 코드", "2-COL + TERMINAL");
add2Col(s, { label: "기존 방식", lines: ["서버 직접 운영", "확장 수동 설정"] }, { label: "새 방식", lines: ["관리형 실행 환경", "요청 단위 확장"] }, { y: 1.45, h: 1.50 });
addCodeBox(s, "deploy.sh", ["# 배포 명령", "$ agentcore launch", "status:   READY"], { y: 3.10, h: 1.90 });
s.addNotes(["코드 노트 첫 문장입니다.", "코드 노트 둘째 문장입니다.", "코드 노트 셋째 문장입니다.", "코드 노트 넷째 문장입니다."]);

s = newSlide("CONTENT");
addContentHeader(s, "차트 세 가지", "COL + DOUGHNUT + LINE");
const cats = ["1월", "2월", "3월"];
addNativeChart(s, "col", [{ name: "요청", labels: cats, values: [120, 340, 1280] }], { x: 0.42, y: 1.45, w: 2.95, h: 3.50 });
addNativeChart(s, "doughnut", [{ name: "비중", labels: ["입력", "출력", "캐시"], values: [110, 60, 30] }], { x: 3.52, y: 1.45, w: 2.95, h: 3.50 });
addNativeChart(s, "line", [{ name: "p50", labels: cats, values: [12, 14, 11] }, { name: "p99", labels: cats, values: [40, 52, 38] }], { x: 6.62, y: 1.45, w: 2.95, h: 3.50 });
s.addNotes(["차트 노트 첫 문장입니다.", "차트 노트 둘째 문장입니다.", "차트 노트 셋째 문장입니다.", "차트 노트 넷째 문장입니다."]);

s = newSlide("CONTENT");
addContentHeader(s, "그림과 표", "DIAGRAM + ICON + TABLE");
addDiagram(s, { svg: "arch.svg", png: "arch.png", x: 0.42, y: 1.45, w: 4.40, h: 1.60, alt: "요청 흐름 그림" });
addIcon(s, { png: "icons/service-Amazon-Bedrock.png", ref: "service/Amazon-Bedrock", x: 5.10, y: 1.50, size: 0.50 });
s.addText([{ text: "문서 ", options: {} }, { text: "링크", options: { hyperlink: { url: "https://aws.amazon.com/bedrock/" } } },
  { text: " 그리고 ", options: {} }, { text: "나쁜 링크", options: { hyperlink: { url: "javascript:alert(1)" } } }],
  { x: 5.10, y: 2.15, w: 4.40, h: 0.40, fontFace: FONT, fontSize: 12, color: C.charcoal, valign: "middle" });
s.addText("<b>굵게 아님</b> & 꺾쇠", { x: 5.10, y: 2.60, w: 4.40, h: 0.36, fontFace: FONT, fontSize: 11, color: C.slate, valign: "middle", align: "right" });
s.addTable([[{ text: "항목", options: { color: C.subtitleOrange, fill: { color: C.bgCard } } }, { text: "값", options: { color: C.subtitleOrange, fill: { color: C.bgCard } } }],
  [{ text: "세션", options: { color: C.charcoal } }, { text: "8시간", options: { color: C.charcoal } }]],
  { x: 0.42, y: 3.30, w: 9.16, colW: [4.58, 4.58], rowH: 0.42, fontFace: FONT, fontSize: 11, valign: "middle", border: { type: "solid", pt: 0.75, color: C.hairline } });
s.addNotes(["그림 노트 첫 문장입니다.", "그림 노트 둘째 문장입니다.", "그림 노트 셋째 문장입니다.", "그림 노트 넷째 문장입니다."]);

s = newSlide("CLOSING");
addClosingSlide(s, { github: "github.com/whchoi98/my-plugins", tagline: "HTML 덱 변환 예시" });
s.addNotes(["맺음 노트 첫 문장입니다.", "맺음 노트 둘째 문장입니다.", "맺음 노트 셋째 문장입니다.", "맺음 노트 넷째 문장입니다."]);

pres.writeFile({ fileName: "fixture_raw.pptx" });

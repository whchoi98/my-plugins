// =============================================================================
//  build_sample.js  -  example deck in the AWS Consulting Report (Light/Dense) style.
//  Usage:  ACCENT=$(python tools/extract_brand_color.py logo.png --json | jq -r .accent) \
//          node examples/build_sample.js
//  (ACCENT optional; defaults to the Yogiyo magenta #FB0050)
// =============================================================================
const pptxgen = require("pptxgenjs");
const { execSync } = require("child_process");
const path = require("path");
const { makeHelpers } = require("../lib/consult_helpers");

const pres = new pptxgen();
pres.defineLayout({ name: "W16x9", width: 10, height: 5.625 });
pres.layout = "W16x9";
pres.author = "Choi, WooHyung";
pres.title = "AWS WADD - Consulting Report Style Sample";

const H = makeHelpers(pres, { accent: process.env.ACCENT, client: "요기요" });
const { C, FONT, CLIENT, COPYRIGHT, COL_W, COL_L_X, COL_R_X, BODY_Y, BODY_H } = H;
const { fullBg, contentFrame, header, summary, card, footer, clientChip, analysis, notes } = H;
const c = H.cell;

// ============================ SLIDE 1 : COVER ===============================
(() => {
  const s = pres.addSlide(); fullBg(s, C.navy);
  clientChip(s);
  s.addText("AMAZON WEB SERVICES", { x: 0.46, y: 0.42, w: 4.5, h: 0.30, fontFace: FONT, fontSize: 10, color: "A6ABBE", charSpacing: 2, valign: "middle", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.46, y: 2.35, w: 9.08, h: 0, line: { color: "8A93A6", width: 0.75 } });
  s.addText("요기요을 위한 AWS WADD (Well-Architected Deep Dive)", { x: 0.46, y: 2.42, w: 9.08, h: 1.12, fontFace: FONT, fontSize: 26, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, lineSpacingMultiple: 1.05 });
  s.addShape(pres.shapes.LINE, { x: 0.46, y: 3.62, w: 9.08, h: 0, line: { color: "8A93A6", width: 0.75 } });
  s.addText("Amazon Web Services", { x: 0.46, y: 3.80, w: 9.08, h: 0.30, fontFace: FONT, fontSize: 14, bold: true, color: "E2E4EC", align: "center", valign: "middle", margin: 0 });
  s.addText("2026.02.22", { x: 0.46, y: 4.12, w: 9.08, h: 0.28, fontFace: FONT, fontSize: 12, color: "A6ABBE", align: "center", valign: "middle", margin: 0 });
  s.addText(COPYRIGHT, { x: 0.46, y: 5.34, w: 9.08, h: 0.22, fontFace: FONT, fontSize: 7, color: "5E6478", valign: "middle", margin: 0 });
  notes(s, "안녕하세요. AWS Korea의 최우형입니다. 오늘은 요기요 환경을 대상으로 한 Well-Architected Deep Dive (WADD) 결과를 공유드리겠습니다. 본 리포트는 비용 기반 아키텍처 분석을 출발점으로, 컴퓨팅, 네트워크, 스토리지, 데이터베이스, OpenSearch, 보안 영역의 현황 (AS-IS) 과 개선 방향 (TO-BE) 을 함께 다룹니다. 2026년 1월 사용량을 기준으로 분석했으며, 동종 규모의 타사 벤치마크와 비교한 시사점도 포함했습니다.");
})();

// ============================ SLIDE 2 : DIVIDER =============================
(() => {
  const s = pres.addSlide(); fullBg(s, C.navy);
  clientChip(s);
  s.addText([
    { text: "II.", options: { bold: true, color: C.accent } },
    { text: "    클라우드 인프라 분석 (AS-IS)", options: { bold: true, color: C.white } },
  ], { x: 0.70, y: 2.18, w: 8.7, h: 0.72, fontFace: FONT, fontSize: 33, valign: "middle", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.74, y: 3.02, w: 7.4, h: 0, line: { color: "8A93A6", width: 0.75 } });
  s.addText("계정 구조 / 네트워크 / EKS / CICD / Observability / 보안 현황 진단", { x: 0.74, y: 3.12, w: 8.0, h: 0.30, fontFace: FONT, fontSize: 12, color: "A6ABBE", valign: "middle", margin: 0 });
  s.addText(COPYRIGHT, { x: 0.46, y: 5.34, w: 9.08, h: 0.22, fontFace: FONT, fontSize: 7, color: "5E6478", valign: "middle", margin: 0 });
  notes(s, "이제 두 번째 장, 클라우드 인프라 분석 AS-IS 로 넘어가겠습니다. 요기요는 운영, 스테이징, DevOps 를 포함한 5개 AWS 계정으로 환경을 분리하여 운영하고 있습니다. 이 장에서는 계정 구조와 역할, 네트워크 구성, EKS 컨테이너 현황, CICD 파이프라인, Observability, 보안 환경을 차례로 진단합니다.");
})();

// ================== SLIDE 3 : COST SUMMARY (chart + table) ==================
(() => {
  const s = pres.addSlide(); contentFrame(s);
  header(s, "1. AWS 비용 분석 - 전체 서비스 사용량", 1, "비용 기반 아키텍처 분석");
  summary(s, "2026년 1월 AWS 총 비용은 $369,409로 12월 대비 2.55% 감소했으며, 8월 $410K 정점 이후 $380K 내외의 안정화 구간이 이어지고 있습니다. EC2-Compute는 전체의 30.2%로 최근 3개월간 3.0% 감소한 반면, RDS는 24.9% 비중에 3.9% 증가, OpenSearch는 14.1%에 16.0% 증가했습니다. 전반적으로 Compute는 조정 국면에 진입한 반면, 데이터/검색 계열 중심의 점진적 비용 확대 흐름이 나타나는 양상입니다.");

  const L = card(s, COL_L_X, BODY_Y, COL_W, BODY_H, "월별 비용 추이 및 Top 5 서비스");
  s.addChart(pres.charts.BAR, [
    { name: "Usage", labels: ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"], values: [343, 305, 316, 328, 312, 302] },
    { name: "SP & RI", labels: ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"], values: [67, 64, 64, 67, 67, 67] },
  ], {
    x: L.x, y: L.y, w: L.w, h: 1.28, barDir: "col", barGrouping: "stacked",
    chartColors: [C.navy, C.accent], chartArea: { fill: { color: C.white } },
    showLegend: true, legendPos: "t", legendFontSize: 7, legendFontFace: FONT,
    catAxisLabelColor: C.muted, catAxisLabelFontSize: 7.5, catAxisLabelFontFace: FONT,
    valAxisLabelColor: C.muted, valAxisLabelFontSize: 7, valAxisLabelFontFace: FONT,
    valGridLine: { color: "EAECEF", size: 0.5 }, catGridLine: { style: "none" },
    valAxisMaxVal: 450, valAxisMinVal: 0, valAxisMajorUnit: 150, showValue: false,
  });
  const rows = [[
    c("#", { fill: C.navy, color: C.white, b: true, al: "center" }),
    c("AWS 서비스", { fill: C.navy, color: C.white, b: true }),
    c("사용 비용", { fill: C.navy, color: C.white, b: true, al: "right" }),
    c("3M", { fill: C.navy, color: C.white, b: true, al: "right" }),
  ]];
  const top = [
    ["1", "Amazon EC2", "$111,495 (30.2%)", "-3.0%", false],
    ["2", "Amazon RDS", "$91,836 (24.9%)", "+3.9%", true],
    ["3", "Amazon OpenSearch", "$52,203 (14.1%)", "+16.0%", true],
    ["4", "Amazon EC2 Other", "$43,688 (11.8%)", "-3.4%", false],
    ["5", "Amazon DocumentDB", "$32,802 (8.9%)", "+11.5%", true],
  ];
  top.forEach((r, i) => rows.push([
    c(r[0], { fill: C.chip[i], color: C.white, b: true, al: "center" }),
    c(r[1], { color: C.ink, b: true }),
    c(r[2], { color: C.body, al: "right" }),
    c(r[3], { color: r[4] ? C.pos : C.neg, b: true, al: "right" }),
  ]));
  s.addTable(rows, { x: L.x, y: L.y + 1.34, w: L.w, colW: [0.28, 1.96, 1.46, 0.62], rowH: 0.235, fontFace: FONT, fontSize: 8, valign: "middle", border: { type: "solid", pt: 0.5, color: "E3E5E9" }, margin: [1, 3, 1, 3] });

  const R = card(s, COL_R_X, BODY_Y, COL_W, BODY_H, "상세 분석");
  analysis(s, R, [
    { h: "AWS 전체 비용 개요", b: [
      "1월 총 비용 $369,409 - 12월 대비 2.55% 감소, 6월 대비 약 1.4% 증가",
      "8월 $410K 정점 후 11월부터 $380K 내외 박스권 형성",
      "SP & RI 비용 $67,716 - 전체의 18.3%까지 확대, 구매 전략 점진적 전환" ] },
    { h: "AWS 서비스별 비용 개요", b: [
      "EC2-Compute 30.2% - 최근 3개월 3.0% 감소, Compute 조정 국면 진입",
      "RDS 24.9% (+3.9%), OpenSearch 14.1% (+16.0%) - 데이터/검색 계열 확대",
      "DocumentDB 8.9% (+11.5%) - 문서 DB 워크로드 점진적 증가" ] },
  ], { fsH: 10.5, fsB: 9 });
  footer(s, 3);
  notes(s, "전체 서비스 비용 현황입니다. 좌측 상단 차트는 월별 비용을 Usage 와 SP & RI 로 나눈 추이이며, 8월 $410K 를 정점으로 이후 $380K 내외에서 안정화되는 흐름을 보여줍니다. 그 아래 표는 비용 상위 5개 서비스로, EC2 가 30.2% 로 가장 크지만 최근 3개월 3.0% 감소했고, RDS 와 OpenSearch 는 각각 증가세를 보입니다. 핵심은 Compute 는 조정 국면, 데이터/검색 계열은 확대 국면이라는 점입니다.");
})();

// ============== SLIDE 4 : PEER BENCHMARK (comparison tables) ===============
(() => {
  const s = pres.addSlide(); contentFrame(s);
  header(s, "2. 컴퓨팅 분석 - 타사 벤치마크 비교", 2, "비용 기반 아키텍처 분석");
  summary(s, "동종 규모 (MRR 1M) A사/B사 대비, 요기요는 EC2 Savings Plan 73%, RDS RI 78%로 장기 계약 기반 비용 통제가 안정적이며 RDS 최신 세대 비중도 84%에 달합니다. 다만 EC2 Graviton 활용률이 31%로 A사 90% 대비 낮고 구세대가 24% 잔존해 인프라 현대화 여지가 큽니다. RDS vCPU 단가는 $0.09로 양사보다 우수하나, EC2는 $0.04 수준으로 세대 재정렬을 통한 단가 개선 검토가 필요합니다.");

  const L = card(s, COL_L_X, BODY_Y, COL_W, BODY_H, "EC2 / RDS 세대 구매옵션 비교");
  function cmpTable(title, data, y) {
    s.addText(title, { x: L.x, y, w: L.w, h: 0.20, fontFace: FONT, fontSize: 9, bold: true, color: C.ink, valign: "middle", margin: 0 });
    const head = [c("항목", { fill: C.navy, color: C.white, b: true }), c("A사", { fill: C.navy, color: C.white, b: true, al: "center" }), c("B사", { fill: C.navy, color: C.white, b: true, al: "center" }), c("요기요", { fill: C.navy, color: C.white, b: true, al: "center" })];
    const body = data.map((r) => [
      c(r[0], { color: C.body }),
      c(r[1], { color: C.muted, al: "center" }),
      c(r[2], { color: C.muted, al: "center" }),
      c(r[3], { color: C.ink, b: true, al: "center", fill: C.accentTint }),
    ]);
    s.addTable([head, ...body], { x: L.x, y: y + 0.22, w: L.w, colW: [1.44, 0.92, 0.92, 1.04], rowH: 0.225, fontFace: FONT, fontSize: 8, valign: "middle", border: { type: "solid", pt: 0.5, color: "E3E5E9" }, margin: [1, 3, 1, 3] });
  }
  cmpTable("EC2", [
    ["Graviton 활용", "90%", "16%", "31%"],
    ["최신 세대", "9%", "79%", "45%"],
    ["Savings Plan", "76%", "56%", "73%"],
    ["vCPU 단가", "$0.02", "$0.04", "$0.04"],
  ], L.y);
  cmpTable("RDS", [
    ["Graviton 활용", "82%", "99%", "60%"],
    ["최신 세대", "17%", "0%", "24%"],
    ["RI 비중", "84%", "66%", "78%"],
    ["vCPU 단가", "$0.11", "$0.13", "$0.09"],
  ], L.y + 1.44);

  const R = card(s, COL_R_X, BODY_Y, COL_W, BODY_H, "강점 및 전략 시사점");
  analysis(s, R, [
    { h: "요기요 강점", b: [
      "EC2 Savings Plan 73% 유지 - 장기 예측 기반 비용 통제 안정적",
      "EC2 On-Demand 17%로 과도하지 않음 - 비용 변동 리스크 통제",
      "RDS 최신 세대 84%, RI 78% - DB 현대화 및 장기계약 효율 우수" ] },
    { h: "전략 시사점", b: [
      "EC2 Graviton 31%로 A사 90% 대비 낮음 - Arm 기반 전환 확대 필요",
      "EC2 구세대 24% 잔존 - 단계적 세대 교체로 기술 부채 해소",
      "RDS On-Demand 22% - Reserved 확대로 추가 절감 여지",
      "EC2 vCPU $0.04 - 세대 재정렬 및 워크로드 최적화로 단가 개선" ] },
  ], { fsH: 10.5, fsB: 9 });
  footer(s, 4);
  notes(s, "타사 벤치마크 비교입니다. 좌측 두 개의 표는 동일 MRR 규모의 A사, B사와 요기요의 EC2, RDS 사용 구조를 비교한 것이며 요기요 열을 강조했습니다. EC2 Savings Plan 73%, RDS RI 78% 로 장기 계약 기반 비용 통제가 안정적이고 RDS 최신 세대 비중도 84% 로 높습니다. 반면 EC2 Graviton 활용률은 31% 로 A사 90% 대비 낮고, 구세대 인스턴스가 24% 남아 있습니다.");
})();

// ============== SLIDE 5 : INSIGHT + STRATEGY (signature 2-col) =============
(() => {
  const s = pres.addSlide(); contentFrame(s);
  header(s, "2. 컴퓨팅 분석 시사점과 최적화 전략", 2, "비용 기반 아키텍처 분석");
  summary(s, "요기요는 EC2에서 구세대 인스턴스 비중이 높고 Graviton 활용률이 낮아 인프라 현대화가 필요하며, RDS는 최신 세대 비중은 높지만 On-Demand 기반 운영으로 비용 효율 개선 여지가 있습니다. EC2는 Savings Plan을 적극 활용 중이나 인스턴스 구조가 표준화되지 않았고, vCPU 단가는 타사 대비 높은 편입니다. Graviton 확산, RDS 예약 구매 전환, 워크로드 재분류, 아키텍처 표준화를 통해 성능과 비용을 동시에 최적화할 수 있습니다.");

  const L = card(s, COL_L_X, BODY_Y, COL_W, BODY_H, "분석 시사점");
  analysis(s, L, [
    { h: "인스턴스 세대 혼합 구조 지속", b: [
      "Preceding 24% 유지 - 세대 전환 지연에 따른 기술 부채 누적 가능성",
      "Graviton 31%, Latest 45% 혼합 - 표준화되지 않은 아키텍처 구조" ] },
    { h: "Graviton 전환 확대 여지", b: [
      "Arm 기반 워크로드 비중 제한적 - 비용 대비 성능 최적화 기회 미활용",
      "경쟁사 대비 Graviton 활용률 낮음 - 구조적 단가 개선 잠재력 보유" ] },
    { h: "구매 전략은 안정적이나 정합성 점검 필요", b: [
      "Savings Plan 73% 적용 - 장기 예측 기반 비용 통제 체계 확보",
      "On-Demand 17% 유지 - 탄력 운영 확보, 추가 절감 여지 존재" ] },
    { h: "vCPU Unit Cost 상승 구조 발생", b: [
      "단가 $0.03 → $0.04 상승 - 워크로드 믹스/스펙 상향 영향 가능성" ] },
  ], { fsH: 10, fsB: 8.5 });

  const R = card(s, COL_R_X, BODY_Y, COL_W, BODY_H, "최적화 전략");
  analysis(s, R, [
    { h: "세대 재정렬 전략 수립", b: [
      "Preceding 인스턴스 단계적 감축 로드맵 수립",
      "신규 배포 시 Latest 또는 Graviton 표준화 정책 적용" ] },
    { h: "Graviton 전환 가속화", b: [
      "Arm 호환성 검증 프로세스 표준화",
      "전환 가능 서비스군 우선순위 정의 및 점진적 확대" ] },
    { h: "워크로드 재분류 기반 최적화", b: [
      "CPU/메모리 집약 워크로드 재매핑, 과대 스펙 다운사이징" ] },
    { h: "아키텍처 표준화 체계 구축", b: [
      "인스턴스 패밀리 표준 가이드 수립",
      "신규 프로젝트 승인 시 표준 세대 우선 적용 정책화" ] },
    { h: "Spot 활용 영역 확대", b: [
      "비핵심/배치 워크로드 분리, 중단 허용 아키텍처 설계 적용" ] },
  ], { fsH: 10, fsB: 8.5 });
  footer(s, 5);
  notes(s, "컴퓨팅 분석의 시사점과 최적화 전략을 좌우로 정리했습니다. 좌측 시사점은 세대 혼합 구조, Graviton 전환 여지, 구매 전략 정합성, vCPU 단가 상승의 네 가지입니다. 우측 전략은 세대 재정렬, Graviton 전환 가속화, 워크로드 재분류, 아키텍처 표준화, Spot 확대의 다섯 갈래로 제시했습니다.");
})();

// ============================ SLIDE 6 : CLOSING =============================
(() => {
  const s = pres.addSlide(); fullBg(s, C.navy);
  clientChip(s);
  s.addText("감사합니다.", { x: 0.46, y: 2.30, w: 9.08, h: 0.90, fontFace: FONT, fontSize: 48, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
  s.addText(COPYRIGHT, { x: 0.46, y: 5.34, w: 9.08, h: 0.22, fontFace: FONT, fontSize: 7, color: "5E6478", valign: "middle", margin: 0 });
  notes(s, "이상으로 발표를 마치겠습니다. 감사합니다.");
})();

pres.writeFile({ fileName: process.env.OUT || "WADD_Consulting_Style_Sample.pptx" }).then((f) => {
  // REQUIRED: PowerPoint-compat fixes (top-rounded cards + bullet fonts).
  try {
    execSync(`python3 "${path.join(__dirname, "..", "tools", "fix_pptx.py")}" "${f}"`, { stdio: "inherit" });
  } catch (e) {
    console.error("WARNING: round2SameRect post-process failed -", e.message);
  }
  console.log("WROTE", f);
});

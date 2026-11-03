# -*- coding: utf-8 -*-
# Example generators from the 2026-09-18 Direct Connect flat-rate post. Copy alongside diagram_lib.py into <workdir>/diagrams/,
# rename to diagrams.py, and set BLOG_IMAGES=<workdir>/images. Keep the layout patterns (zones, node rows, break-even chart, bars).
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from diagram_lib import *

OUT = os.environ.get("BLOG_IMAGES", os.path.join(os.path.dirname(__file__), "..", "images"))
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# 그림 1. 기존 구성 (종량제)
# --------------------------------------------------------------------------
def fig01():
    c = Canvas("dx-fig01", "기존 구성: 서울 리전 10 Gbps 전용 연결 2개, 합산 20 Gbps(종량제)",
               "서울 리전 VPC가 Direct Connect Gateway를 거쳐 서울 Direct Connect 로케이션의 10 Gbps 전용 연결 2개로 온프레미스 데이터센터에 연결되며, 포트 시간과 DTO가 각각 과금되는 종량제 구성")
    c.text("top", 40, 44, "기존 구성: 서울 리전 10 Gbps 전용 연결 2개, 합산 20 Gbps (종량제)", size=20, weight=600)
    # AWS Cloud / Region
    c.zone(40, 72, 432, 520, title="AWS Cloud")
    c.zone(64, 120, 384, 448, title="서울 리전 (ap-northeast-2)", fill=INK, fill_op=0.02, stroke=INK, stroke_op=0.20)
    c.node(88, 160, 160, 96, "VPC", sub="워크로드", icon="vpc")
    c.node(88, 344, 336, 96, "Direct Connect Gateway", sub="Private VIF 종단", icon="dxgw")
    c.text("zones", 88, 512, "DTO: 리전에서 로케이션으로 나가는 트래픽", size=16, fill=SOFT)
    c.text("zones", 88, 540, "$ 0.041/GB (서울 리전, 공개 단가)", size=16, fill=ACCENT, mono=True)
    # DX location
    c.zone(528, 72, 400, 520, title="서울 Direct Connect 로케이션")
    c.node(552, 152, 352, 96, "전용 연결 1", sub="10 Gbps / 장비 A / 평균 3 Gbps", icon="dx")
    c.node(552, 344, 352, 96, "전용 연결 2", sub="10 Gbps / 장비 B / 평균 3 Gbps", icon="dx")
    c.text("zones", 552, 476, "합산 20 Gbps / 2026년 8월 평균 회선당 3 Gbps 송신", size=16, fill=SOFT)
    c.text("zones", 552, 512, "포트 시간(Port-hour) 과금", size=16, fill=SOFT)
    c.text("zones", 552, 540, "$ 2.25/시간 × 포트 2개 (공개 단가)", size=16, fill=ACCENT, mono=True)
    # On-prem
    c.zone(968, 72, 272, 520, title="온프레미스", eyebrow="고객 데이터센터")
    c.node(1000, 344, 208, 96, "고객 라우터", sub="BGP / 다중 회선", icon="router")
    # arrows (drawn before nodes by layer order)
    c.arrow([(168, 256), (168, 344)], label="Private VIF", side="right", color=MUTED)
    c.arrow([(424, 392), (528, 392)], label=["DTO", "$0.041/GB"], color=ACCENT, label_fill=ACCENT)
    c.arrow([(928, 392), (1000, 392)], label=["전용 회선", "10 Gbps", "×2"], color=MUTED, label_shift=-12)
    c.legend([("solid", "트래픽 경로 (AWS에서 온프레미스 방향)"), ("price", "종량제 과금 항목"),
              ("fill-backend", "AWS 리소스 / 전용 포트")])
    c.check()
    c.write(os.path.join(OUT, "dx-flat-rate-fig01-current-architecture.html"),
            os.path.join(OUT, "dx-flat-rate-fig01-current-architecture.svg"))
    print("OK fig01")


# --------------------------------------------------------------------------
# 그림 2. 포트페어 3쌍 vs 독립 연결 6개
# --------------------------------------------------------------------------
def fig02():
    c = Canvas("dx-fig02", "정액제 전환 구성: 포트페어 1쌍(A)과 독립 연결 2개(B)",
               "같은 물리 회선 2개를 포트페어 1쌍으로 묶으면 정액 요금 1단위에 사용 가능 용량 10 Gbps, 독립 연결 2개로 운영하면 정액 요금 2단위에 사용 가능 용량 20 Gbps")
    c.text("top", 40, 44, "정액제 전환 구성: 포트페어 1쌍(A 구성)과 독립 연결 2개(B 구성)", size=20, weight=600)
    # A
    c.zone(40, 72, 592, 520, title="A 구성: 포트페어 1쌍", eyebrow="사용 가능 용량 10 Gbps")
    gy = 176
    c.zone(64, gy, 544, 256, fill=INK, fill_op=0.02, stroke=INK, stroke_op=0.35, dashed=True, rx=6)
    c.text("zones", 80, gy + 28, "Resiliency Group / 포트페어", size=16, fill=SOFT)
    c.text("zones", 592, gy + 28, "$10.96/시간 = 1단위", size=16, fill=ACCENT, mono=True, anchor="end")
    c.node(80, gy + 56, 240, 80, "포트 1", sub="10 Gbps 활성", sub2="AWS 장비 A", icon="dx")
    c.node(344, gy + 56, 240, 80, "포트 2", sub="예비 (요금 포함)", sub2="AWS 장비 B", icon="dx", kind="standby")
    c.text("zones", 80, gy + 176, "두 포트가 동시에 트래픽을 전달해도", size=16, fill=SOFT)
    c.text("zones", 80, gy + 204, "쌍의 사용 가능 용량은 10 Gbps", size=16, fill=SOFT)
    c.text("zones", 64, 496, "정액 요금 1단위 × $10.96/시간 = $8,154.24/월 (744시간)", size=16, fill=ACCENT, mono=True)
    c.text("zones", 64, 528, "포트 1개 장애 시 잔여 용량 10 Gbps", size=16, fill=SOFT)
    # B
    c.zone(656, 72, 584, 520, title="B 구성: 독립 연결 2개", eyebrow="합산 사용 가능 용량 20 Gbps")
    for i, y in enumerate([200, 328], 1):
        c.node(680, y, 536, 96, f"연결 {i}", sub=f"10 Gbps 활성 / AWS 장비 {'AB'[i-1]}", sub2="$10.96/시간 = 1단위", sub2_fill=ACCENT, icon="dx")
    c.text("zones", 680, 464, "이중화는 두 연결 간 BGP 라우팅 설계로 유지", size=16, fill=SOFT)
    c.text("zones", 680, 496, "정액 요금 2단위 × $10.96/시간 = $16,308.48/월 (744시간)", size=16, fill=ACCENT, mono=True)
    c.text("zones", 680, 528, "포트 1개 장애 시 잔여 용량 10 Gbps", size=16, fill=SOFT)
    c.legend([("fill-backend", "활성 포트"), ("fill-standby", "예비 포트 (요금 포함, 용량 미추가)"),
              ("dashed", "Resiliency Group"), ("price", "Tier 1 정액 단가")])
    c.check()
    c.write(os.path.join(OUT, "dx-flat-rate-fig02-port-pair-vs-single.html"),
            os.path.join(OUT, "dx-flat-rate-fig02-port-pair-vs-single.svg"))
    print("OK fig02")


# --------------------------------------------------------------------------
# 그림 3. 손익분기점 라인 차트
# --------------------------------------------------------------------------
def fig03():
    c = Canvas("dx-fig03", "월 DTO 양에 따른 종량제 비용과 정액 요금의 손익분기점",
               "가로축 월 DTO(TB), 세로축 월 비용(천 USD). 종량제 비용 직선과 A 구성, B 구성 정액 요금 수평선이 만나는 114 TB, 309 TB가 손익분기점이며 2026년 8월 가상 청구서 1,827 TB는 그 위에 있다")
    c.text("top", 40, 44, "월 DTO 양에 따른 종량제 비용과 정액 요금 (서울 리전과 서울 DX 로케이션 간 Tier 1, 744시간)", size=20, weight=600)
    X0, X1, Y0, Y1 = 120, 1160, 80, 560
    PORT = 3348.00; RATE = 0.041; TB = 1024.0
    def X(tb): return X0 + tb * (X1 - X0) / 2000.0
    def Y(usd): return Y1 - usd * (Y1 - Y0) / 96000.0
    L = c.layers
    # grid
    for k in range(0, 7):
        y = Y1 - k * 80
        L["zones"].append(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="rgba(35,47,62,0.08)" stroke-width="0.8"/>')
        c.text("zones", 108, y + 4, f"{k*16}", size=16, fill=MUTED, anchor="end", mono=True)
    c.text("zones", 108, 68, "천 USD", size=16, fill=MUTED, anchor="end", mono=True)
    for k in range(0, 6):
        x = X0 + k * 208
        L["zones"].append(f'<line x1="{x}" y1="{Y1}" x2="{x}" y2="{Y1+8}" stroke="rgba(35,47,62,0.25)" stroke-width="1"/>')
        c.text("zones", x, 588, f"{k*400:,}", size=16, fill=MUTED, anchor="middle", mono=True)
    c.text("zones", X1, 616, "월 DTO (TB, 1 TB = 1,024 GB)", size=16, fill=MUTED, anchor="end", mono=True)
    L["zones"].append(f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="rgba(35,47,62,0.25)" stroke-width="1"/>')
    L["zones"].append(f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="rgba(35,47,62,0.25)" stroke-width="1"/>')
    # lines
    payg = lambda tb: PORT + tb * TB * RATE
    L["arrows"].append(f'<line x1="{X(0):.1f}" y1="{Y(payg(0)):.1f}" x2="{X(2000):.1f}" y2="{Y(payg(2000)):.1f}" stroke="{INK}" stroke-width="2.4"/>')
    A, B = 8154.24, 16308.48
    L["arrows"].append(f'<line x1="{X0}" y1="{Y(A):.1f}" x2="{X1}" y2="{Y(A):.1f}" stroke="{SERIES_TEAL}" stroke-width="2.4"/>')
    L["arrows"].append(f'<line x1="{X0}" y1="{Y(B):.1f}" x2="{X1}" y2="{Y(B):.1f}" stroke="{SERIES_PURPLE}" stroke-width="2.4"/>')
    c.text("labels", 800, 500, "A 구성 정액 요금: 포트페어 1쌍 $8,154/월", size=16, fill=SERIES_TEAL, mono=True)
    c.text("labels", 800, 460, "B 구성 정액 요금: 독립 연결 2개 $16,308/월", size=16, fill=SERIES_PURPLE, mono=True)
    c.text("labels", 160, 116, "종량제 비용 = 포트 2개 $3,348/월 + DTO × $0.041/GB", size=16, fill=INK, mono=True)
    # break-even points
    beA = (A - PORT) / RATE / TB; beB = (B - PORT) / RATE / TB
    for (tb, usd, tag, txt, dy) in [(beA, A, "A", f"손익분기 A: {beA:,.0f} TB (평균 376 Mbps)", 32),
                                    (beB, B, "B", f"손익분기 B: {beB:,.0f} TB (평균 1.01 Gbps)", 32)]:
        x, y = X(tb), Y(usd)
        L["top"].append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{Y1}" stroke="{ACCENT}" stroke-width="1" stroke-dasharray="3,3"/>')
        L["top"].append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{ACCENT}"/>')
        tx = ((int(x) + 16) // 4) * 4
        ty = ((int(y) + dy) // 4) * 4
        c.text("top", tx, ty, txt, size=16, fill=ACCENT, mono=True)
    x, y = X(1826.99), Y(80052.47)
    L["top"].append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    c.text("top", ((int(x) - 16) // 4) * 4, ((int(y) + 8) // 4) * 4, "2026년 8월 가상 청구 1,827 TB / $80,052", size=16, fill=INK, mono=True, anchor="end")
    c.legend([("ink", "종량제 (포트 + DTO)"), ("teal", "A 구성 정액"), ("purple", "B 구성 정액"),
              ("dot-accent", "손익분기점"), ("dot-ink", "8월 가상 청구서")], y=664)
    c.check()
    c.write(os.path.join(OUT, "dx-flat-rate-fig03-break-even-chart.html"),
            os.path.join(OUT, "dx-flat-rate-fig03-break-even-chart.svg"))
    print("OK fig03", round(beA, 2), round(beB, 2))


# --------------------------------------------------------------------------
# 그림 4. 월별 비용 비교 막대
# --------------------------------------------------------------------------
def fig04():
    c = Canvas("dx-fig04", "2026년 8월 가상 청구서의 요금제별 월 비용",
               "2026년 8월 가상 청구서 기준 종량제 비용(포트와 DTO로 분리)과 포트페어 1쌍(A), 독립 연결 2개(B)의 정액 비용을 비교한 막대 그래프")
    c.text("top", 40, 44, "2026년 8월 가상 청구서의 요금제별 월 비용 (천 USD, 세전, 744시간, 회선당 평균 3 Gbps)", size=20, weight=600)
    X0, X1, Y0, Y1 = 120, 1240, 80, 560
    def Y(usd): return Y1 - usd * (Y1 - Y0) / 96000.0
    L = c.layers
    for k in range(0, 7):
        y = Y1 - k * 80
        L["zones"].append(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="rgba(35,47,62,0.08)" stroke-width="0.8"/>')
        c.text("zones", 108, y + 4, f"{k*16}", size=16, fill=MUTED, anchor="end", mono=True)
    c.text("zones", 108, 68, "천 USD", size=16, fill=MUTED, anchor="end", mono=True)
    L["zones"].append(f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="rgba(35,47,62,0.25)" stroke-width="1"/>')
    L["zones"].append(f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="rgba(35,47,62,0.25)" stroke-width="1"/>')
    W = 200
    def bar(x, y_top, y_bot, f, fo, st):
        L["nodes"].append(f'<rect x="{x}" y="{y_top:.1f}" width="{W}" height="{y_bot - y_top:.1f}" fill="{PAPER}"/>')
        L["nodes"].append(f'<rect x="{x}" y="{y_top:.1f}" width="{W}" height="{y_bot - y_top:.1f}" fill="{f}" fill-opacity="{fo}" stroke="{st}" stroke-width="1.2"/>')
    x = 240
    bar(x, Y(3348.00), Y1, INK, 0.35, INK)
    bar(x, Y(80052.47), Y(3348.00), INK, 0.12, INK)
    c.text("top", x + W // 2, ((int(Y(80052.47)) - 12) // 4) * 4, "80.1 (DTO 76.7 + 포트 3.3)", size=16, fill=INK, anchor="middle", mono=True)
    c.text("top", x + W // 2, 588, "종량제", size=20, weight=600, fill=INK, anchor="middle")
    c.text("top", x + W // 2, 616, "사용 가능 20 Gbps", size=16, fill=SOFT, anchor="middle")
    x = 560
    bar(x, Y(8154.24), Y1, SERIES_TEAL, 0.18, SERIES_TEAL)
    c.text("top", x + W // 2, ((int(Y(8154.24)) - 12) // 4) * 4, "8.2", size=16, fill=SERIES_TEAL, anchor="middle", mono=True)
    c.text("top", x + W // 2, 588, "A 구성: 포트페어 1쌍", size=20, weight=600, fill=INK, anchor="middle")
    c.text("top", x + W // 2, 616, "절감 89.81% / 사용 가능 10 Gbps", size=16, fill=ACCENT, anchor="middle", mono=True)
    x = 880
    bar(x, Y(16308.48), Y1, SERIES_PURPLE, 0.18, SERIES_PURPLE)
    c.text("top", x + W // 2, ((int(Y(16308.48)) - 12) // 4) * 4, "16.3", size=16, fill=SERIES_PURPLE, anchor="middle", mono=True)
    c.text("top", x + W // 2, 588, "B 구성: 독립 연결 2개", size=20, weight=600, fill=INK, anchor="middle")
    c.text("top", x + W // 2, 616, "절감 79.63% / 사용 가능 20 Gbps", size=16, fill=ACCENT, anchor="middle", mono=True)
    c.legend([("fill-ink", "종량제 (연한 부분 DTO / 진한 부분 포트)"), ("fill-teal", "A 구성 정액"),
              ("fill-purple", "B 구성 정액"), ("price", "종량제 대비 절감률")], y=664)
    c.check()
    c.write(os.path.join(OUT, "dx-flat-rate-fig04-monthly-cost-comparison.html"),
            os.path.join(OUT, "dx-flat-rate-fig04-monthly-cost-comparison.svg"))
    print("OK fig04")


if __name__ == "__main__":
    fig01(); fig02(); fig03(); fig04()

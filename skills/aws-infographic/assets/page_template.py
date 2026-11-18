"""Page template: copy, rename, replace T and the section bodies."""
from infokit import (Doc, F, rw, para, dot_list, items_h, cell, tag, callout, header, series_nav, section,
                     footer_note, check, cross)

SERIES = [("0", "개요"), ("1", "API 호출")]  # omit series_nav for a single page
T = dict(
    title="요청 경로별 지연 구조",
    sub_en="Where Latency Comes From",
    sub_ko="구간별 원인과 대응 조치",
    s1=("요청 경로", "구간마다 보는 지표가 다름"),
    s2=("대응 조치", "효과가 큰 순서"),
    rows=[("네트워크", "리전 거리, TLS 핸드셰이크", True), ("대기열", "동시 요청 급증", True), ("Prefill", "긴 입력", False)],
    bullets=["스트리밍으로 첫 글자를 앞당김", "Prompt caching으로 반복 입력 재사용", "작은 모델로 라우팅"],
    aws=("service/Amazon-Bedrock", "Amazon Bedrock", "교차 리전 추론으로 처리량 분산"),
    insight=("첫 글자 지연의 대부분은 대기와 Prefill", "입력 길이와 동시 요청 수를 함께 확인"),
    note="수치는 설명용 예시",
)


def s1(d, x, y, w, h, k=1.0):
    cy = section(d, x, y, w, h, 1, *T["s1"], tsize=F(21, k), ksize=F(15, k))
    box = (x, y, w, h)
    ix, iw = x + 24, w - 48
    rh = 48 * k
    for i, (name, cause, retry) in enumerate(T["rows"]):
        mid = cy + 10 + i * rh + rh / 2
        tag(d, ix, mid - 12 * k, name, "orange", F(13, k), 24 * k, 10, box=box)
        cell(d, ix + 140 * k, mid, iw - 200 * k, cause, F(15, k), F(20, k), 400, "text2", box, k)
        (check if retry else cross)(d, ix + iw - 20 * k, mid - 7 * k, 14 * k)
    callout(d, ix, y + h - 22 - 58 * k, iw, *T["insight"], k=k, box=box)


def s2(d, x, y, w, h, k=1.0):
    cy = section(d, x, y, w, h, 2, *T["s2"], tsize=F(21, k), ksize=F(15, k))
    box = (x, y, w, h)
    ix, iw = x + 24, w - 48
    bh = items_h(T["bullets"], iw, F(15, k), F(21, k), F(9, k))
    dot_list(d, ix, cy + 16 * k, iw, T["bullets"], F(15, k), F(21, k), F(9, k), dot="green", box=box)
    ref, name, desc = T["aws"]
    ay = cy + 16 * k + bh + 24 * k
    d.icon(ref, ix, ay, 40 * k)
    d.text(ix + 52 * k, ay + 16 * k, name, F(15, k), 800, "text", box=box)
    para(d, ix + 52 * k, ay + 36 * k, iw - 52 * k, desc, F(13, k), None, 400, "text2", box=box)


def landscape(theme):
    d = Doc(1920, 1080, theme)
    d.rect(0, 0, 1920, 1080, fill="bg")
    header(d, 48, 76, T["title"], T["sub_en"], T["sub_ko"])
    series_nav(d, 1872, 48, SERIES, "1")
    s1(d, 48, 140, 1080, 904)
    s2(d, 1148, 140, 724, 904)
    footer_note(d, 1872, 1064, T["note"])
    return d.svg()


def portrait(theme):  # 4:5, only when requested
    d = Doc(1536, 1920, theme)
    d.rect(0, 0, 1536, 1920, fill="bg")
    header(d, 56, 104, T["title"], T["sub_en"], T["sub_ko"], tsize=54, ssize=25, kosize=20)
    series_nav(d, 56, 180, SERIES, "1", anchor="start")
    s1(d, 56, 236, 1424, 900, 1.15)
    s2(d, 56, 1158, 1424, 712, 1.15)
    footer_note(d, 1480, 1898, T["note"])
    return d.svg()

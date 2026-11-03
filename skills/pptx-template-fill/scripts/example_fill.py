#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
example_fill - 헬퍼 동작 확인용 스모크 테스트 겸 사용 예시.

임의의 템플릿을 받아 첫 텍스트 도형 / 첫 표 / 첫 차트를 자동으로 찾아
각 헬퍼를 한 번씩 적용해 본다. 실제 작업에서는 이렇게 자동 탐색하지 않고
inventory.py 로 확인한 shape_id 를 슬라이드별로 명시한다(SKILL.md 의 골격 참고).

사용법
  python example_fill.py template.pptx demo_out.pptx
"""
import sys

import tfill as T


def find_first(slide, kind):
    def shapes_of(shapes):
        for sh in shapes:
            yield sh
            if sh.shape_type == 6:
                yield from shapes_of(sh.shapes)

    for sh in shapes_of(slide.shapes):
        if kind == "table" and getattr(sh, "has_table", False) and sh.has_table:
            return sh
        if kind == "chart" and getattr(sh, "has_chart", False) and sh.has_chart:
            return sh
        if kind == "text" and sh.has_text_frame and sh.text_frame.text.strip():
            return sh
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]

    prs = T.load(src)
    S = T.slides(prs)
    print(f"템플릿 {src}: {len(S)}장")
    did = []

    # 1) 텍스트 - run 단위 소비형 교체
    sh = find_first(S[0], "text")
    if sh is not None:
        original = sh.text_frame.text.strip().split("\n")[0]
        runs = [r.text for pa in sh.text_frame.paragraphs for r in pa.runs if r.text.strip()]
        target = runs[0].strip() if runs else original
        T.apply_runs(S[0], [(target, "템플릿-필 데모 제목")], label="S1 title")
        did.append(f"apply_runs: '{target[:24]}' -> 교체")

    # 2) 표 - 셀 서식 유지 채우기
    for i, sl in enumerate(S):
        tb_sh = find_first(sl, "table")
        if tb_sh is None:
            continue
        tb = tb_sh.table
        matrix = [[f"R{r}C{c}" for c in range(len(tb.columns))]
                  for r in range(min(2, len(tb.rows)))]
        T.fill_table(sl, tb_sh.shape_id, matrix)
        did.append(f"fill_table: S{i+1} id{tb_sh.shape_id} {len(tb.rows)}x{len(tb.columns)}")
        if len(tb.rows) > 3:
            n = T.drop_last_rows(sl, tb_sh.shape_id, 1)
            did.append(f"drop_last_rows: {n}행 삭제")
        break

    # 3) 차트 - 단일 plot 은 chart_replace, 콤보는 combo_edit
    for i, sl in enumerate(S):
        ch_sh = find_first(sl, "chart")
        if ch_sh is None:
            continue
        chart = ch_sh.chart
        plot = chart.plots[0]
        cats = list(plot.categories)
        n = len(cats)
        if len(chart.plots) > 1:
            vals = [[float(v + 1) * 10 for v in range(n)]]
            T.combo_edit(sl, ch_sh.shape_id, cats=[f"C{j+1}" for j in range(n)],
                         series_vals=vals, series_names=["데모 시리즈"])
            did.append(f"combo_edit: S{i+1} id{ch_sh.shape_id} (plots={len(chart.plots)})")
        else:
            series = [(f"데모 {si+1}", [float((si + 1) * (j + 1)) for j in range(n)])
                      for si in range(len(list(plot.series)))]
            T.chart_replace(sl, ch_sh.shape_id, [f"C{j+1}" for j in range(n)], series)
            did.append(f"chart_replace: S{i+1} id{ch_sh.shape_id} cats={n}")
        did.append(f"clear_axis_scale: 고정 축 {T.clear_axis_scale(chart)}개 제거")
        break

    # 4) 발표 노트 - 문장별 줄바꿈
    T.set_notes(S[0], "첫 문장입니다.\n두 번째 문장입니다.\n세 번째 문장입니다.", donor=S[0])
    did.append("set_notes: 3문장 3줄")

    # 5) 전역 잔존 토큰 정리
    T.sweep_tokens(prs, {"20XX": "2026", "Lorem": "데모"})

    T.save(prs, dst)
    print("\n적용 내역")
    for line in did:
        print(f"  - {line}")
    T.report()
    return 0


if __name__ == "__main__":
    sys.exit(main())

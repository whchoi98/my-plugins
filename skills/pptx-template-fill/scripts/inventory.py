#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿 인벤토리 덤프.

템플릿-필의 모든 편집은 shape_id 로 대상을 지정하므로, 필을 시작하기 전에
반드시 이 스크립트로 인벤토리를 확보한다. 사람이 읽을 용도이며
"어떤 도형에 무엇이 들어 있고, 어디에 놓여 있는지"를 한눈에 보여준다.

사용법
  python inventory.py deck.pptx                    # 전체
  python inventory.py deck.pptx --slides 1,3,5-7   # 특정 슬라이드만
  python inventory.py deck.pptx --out inv.txt      # 파일로 저장
  python inventory.py deck.pptx --geometry         # 좌표/크기까지 (진행률 바, 간트 조정 시 필요)

출력 항목
  [shape_id] 이름 (형식) x/y/w/h  TXT="..."     <- apply_runs / delete_shape / 좌표 조정 대상
  TABLE RxC + 행별 셀 미리보기                    <- fill_table / drop_last_rows 대상
  CHART type / plots / cats / series             <- chart_replace(단일 plot) / combo_edit(2 plots 이상)
  DUP 경고: 동일 텍스트가 여러 run 에 존재         <- apply_runs 순서 의존성 주의 지점
"""
import argparse
import collections
import sys

from pptx import Presentation
from pptx.util import Emu

SHAPE_GROUP = 6


def inches(v):
    return round(Emu(v).inches, 2) if v is not None else None


def parse_slides(spec, total):
    if not spec:
        return list(range(1, total + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return [i for i in out if 1 <= i <= total]


def dump_shape(sh, w, depth, geometry):
    ind = "  " * depth
    head = f"{ind}[{sh.shape_id}] {sh.name} ({sh.shape_type})"
    if geometry:
        head += f" x={inches(sh.left)} y={inches(sh.top)} w={inches(sh.width)} h={inches(sh.height)}"
    if sh.has_text_frame and sh.text_frame.text.strip():
        txt = sh.text_frame.text.replace("\n", "|")
        head += f' TXT="{txt[:110]}"'
        # run 분할 상태는 apply_runs 매칭 단위와 직결되므로 여러 run 이면 표시
        runs = [r.text for pa in sh.text_frame.paragraphs for r in pa.runs]
        if len(runs) > 1:
            head += f"  RUNS={runs[:6]}"
    w(head)

    if sh.shape_type == SHAPE_GROUP:
        for sub in sh.shapes:
            dump_shape(sub, w, depth + 1, geometry)

    if getattr(sh, "has_table", False) and sh.has_table:
        tb = sh.table
        w(f"{ind}  TABLE {len(tb.rows)}x{len(tb.columns)}")
        if geometry:
            w(f"{ind}   colW={[inches(c.width) for c in tb.columns]}")
            w(f"{ind}   rowH={[inches(r.height) for r in tb.rows]}")
        for ri, row in enumerate(tb.rows):
            cells = [c.text.replace("\n", "|")[:24] for c in row.cells]
            w(f"{ind}   r{ri}: {cells}")

    if getattr(sh, "has_chart", False) and sh.has_chart:
        ch = sh.chart
        w(f"{ind}  CHART type={ch.chart_type} plots={len(ch.plots)}")
        for pi, pl in enumerate(ch.plots):
            try:
                cats = list(pl.categories)
            except Exception:
                cats = "?"
            w(f"{ind}   plot{pi} cats={cats}")
            for s in pl.series:
                try:
                    vals = list(s.values)
                except Exception:
                    vals = "?"
                w(f"{ind}   plot{pi} series '{s.name}': {vals}")
        if len(ch.plots) > 1:
            w(f"{ind}   -> 복합(콤보) 차트: replace_data 금지, combo_edit 사용")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--slides", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--geometry", action="store_true")
    args = ap.parse_args()

    prs = Presentation(args.pptx)
    slides = list(prs.slides)
    targets = parse_slides(args.slides, len(slides))

    lines = []
    w = lines.append
    w(f"file: {args.pptx}")
    w(f"slide size: {inches(prs.slide_width)} x {inches(prs.slide_height)} in "
      f"({prs.slide_width} x {prs.slide_height} EMU)")
    w(f"slides: {len(slides)} (덤프 대상 {len(targets)}장)")

    text_counter = collections.Counter()
    tally = collections.Counter()

    for idx in targets:
        sl = slides[idx - 1]
        w(f"\n===== SLIDE {idx} =====")
        for sh in sl.shapes:
            dump_shape(sh, w, 0, args.geometry)
            for pa_sh in ([sh] if sh.has_text_frame else []):
                for pa in pa_sh.text_frame.paragraphs:
                    for r in pa.runs:
                        t = r.text.strip()
                        if t:
                            text_counter[(idx, t)] += 1
            tally["shapes"] += 1
            if getattr(sh, "has_table", False) and sh.has_table:
                tally["tables"] += 1
            if getattr(sh, "has_chart", False) and sh.has_chart:
                tally["charts"] += 1
                if len(sh.chart.plots) > 1:
                    tally["combo_charts"] += 1
        has_notes = sl.has_notes_slide and bool(sl.notes_slide.notes_text_frame
                                                and sl.notes_slide.notes_text_frame.text.strip())
        w(f"  NOTES: {'있음' if has_notes else '없음'}")

    dups = {k: v for k, v in text_counter.items() if v > 1}
    w("\n===== 요약 =====")
    w(f"도형 {tally['shapes']} / 표 {tally['tables']} / 차트 {tally['charts']} "
      f"(콤보 {tally['combo_charts']})")
    if dups:
        w("DUP (동일 텍스트 중복 run) - apply_runs 는 위에서 아래로 1회씩 소비하므로 순서를 맞출 것:")
        for (sidx, t), c in sorted(dups.items())[:40]:
            w(f"  S{sidx} x{c}: '{t[:40]}'")
    else:
        w("DUP: 없음")

    out = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {args.out} ({len(lines)} lines)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

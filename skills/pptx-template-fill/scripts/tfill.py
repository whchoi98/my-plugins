#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tfill - PowerPoint 템플릿-필 헬퍼 라이브러리 (python-pptx 기반).

설계 원칙
  템플릿의 서식(폰트, 색, 정렬, 그림자, 표 스타일)은 거의 전부 run/cell 수준
  속성에 들어 있다. 따라서 도형을 새로 만들거나 text_frame.text / cell.text 에
  통째로 대입하면 그 서식이 사라진다. 이 라이브러리의 모든 함수는
  "기존 run/cell/차트 캐시를 제자리에서 수정"하는 방식만 사용한다.

빠른 사용
  import tfill as T
  prs = T.load('template.pptx');  S = T.slides(prs)
  T.apply_runs(S[0], [('First Half', 'AWS WADD '), ('20XX / MM / DD', '2026 / 07 / 29')])
  T.fill_table(S[5], 21, [['지역','목표','실적'], ['서울','320','338']])
  T.chart_replace(S[2], 51, ['6월','최근'], [('월 비용', [52.4, 50.7])])
  T.set_notes(S[0], '첫 문장입니다.\\n두 번째 문장입니다.')
  T.save(prs, 'out.pptx')
"""
from __future__ import annotations

import copy

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.parts.image import Image
from pptx.util import Emu

SHAPE_GROUP = 6

# 미매칭 항목을 모아 두고 빌드 마지막에 report() 로 한번에 확인한다.
UNMATCHED: list[tuple[str, str]] = []


# --------------------------------------------------------------------------
# 로드/저장
# --------------------------------------------------------------------------
def load(path):
    return Presentation(path)


def slides(prs):
    return list(prs.slides)


def save(prs, path):
    prs.save(path)
    print(f"SAVED {path}")
    return path


def report():
    """빌드 종료 시 호출. 미매칭이 있으면 인벤토리의 실제 문자열과 대조할 것."""
    if UNMATCHED:
        print(f"\n! 미매칭 {len(UNMATCHED)}건:")
        for where, what in UNMATCHED:
            print(f"   {where}: '{what}'")
    else:
        print("\n미매칭 없음")
    return list(UNMATCHED)


# --------------------------------------------------------------------------
# 도형 탐색
# --------------------------------------------------------------------------
def iter_text_shapes(shapes):
    """그룹 안쪽까지 재귀. 템플릿은 카드/배지를 그룹으로 묶어 두는 경우가 많다."""
    for sh in shapes:
        if sh.shape_type == SHAPE_GROUP:
            yield from iter_text_shapes(sh.shapes)
        elif sh.has_text_frame:
            yield sh


def shape_by_id(slide, sid, deep=True):
    def walk(shapes):
        for sh in shapes:
            if sh.shape_id == sid:
                return sh
            if deep and sh.shape_type == SHAPE_GROUP:
                found = walk(sh.shapes)
                if found is not None:
                    return found
        return None

    sh = walk(slide.shapes)
    if sh is None:
        UNMATCHED.append((f"shape_by_id({sid})", "not found"))
    return sh


def delete_shape(slide, sid):
    """placeholder 그림처럼 내용을 바꿀 수 없는 도형은 삭제하고 새로 그린다."""
    sh = shape_by_id(slide, sid)
    if sh is not None:
        sh._element.getparent().remove(sh._element)
        return True
    return False


def move_resize(slide, sid, left=None, top=None, width=None, height=None):
    """Inches/Emu 값 지정. 진행률 바, 간트 바, 구분선 이동에 사용."""
    sh = shape_by_id(slide, sid)
    if sh is None:
        return None
    for attr, val in (("left", left), ("top", top), ("width", width), ("height", height)):
        if val is not None:
            setattr(sh, attr, int(val))
    return sh


# --------------------------------------------------------------------------
# 텍스트: run 단위 소비형 교체
# --------------------------------------------------------------------------
def apply_runs(slide, entries, label=""):
    """
    entries: [(old, new)] 또는 [(old, new, mode)] 순서 리스트.
      mode 'e' 완전일치(기본) / 'p' 접두일치 / 'c' 포함
    각 항목은 한 번만 소비된다. 템플릿에는 'Text 15' 같은 동일 문구가 반복되므로
    위에서 아래로 1회씩 소비하는 규칙이 순서 제어의 핵심이다.

    run 단위로 먼저 시도하고, 실패하면 문단 전체 텍스트로 폴백한다.
    (템플릿이 'First Half ' + 'Business Performance Report' 처럼 한 문단을
     여러 run 으로 쪼개 두는 경우가 흔하다.)
    """
    todo = [list(e) + (["e"] if len(e) == 2 else []) for e in entries]

    def match(t):
        for item in todo:
            if item[1] is None:
                continue
            old, mode = item[0], item[2]
            if mode == "e":
                ok = (t == old)
            elif mode == "p":
                ok = t.startswith(old)
            else:
                ok = old in t
            if ok:
                return item
        return None

    for sh in iter_text_shapes(slide.shapes):
        for pa in sh.text_frame.paragraphs:
            hit = False
            for r in pa.runs:
                t = r.text.strip()
                if not t:
                    continue
                item = match(t)
                if item is not None:
                    r.text = item[1]
                    item[1] = None
                    hit = True
            if not hit and pa.runs:
                full = "".join(r.text for r in pa.runs).strip()
                if full:
                    item = match(full)
                    if item is not None:
                        # 첫 run 에 넣고 나머지를 비우면 첫 run 의 서식이 유지된다
                        pa.runs[0].text = item[1]
                        for r in pa.runs[1:]:
                            r.text = ""
                        item[1] = None

    for item in todo:
        if item[1] is not None:
            UNMATCHED.append((label or "apply_runs", item[0]))
    return [i[0] for i in todo if i[1] is not None]


def apply_runs_in(slide, sid, entries, label=""):
    """특정 도형에만 적용. 같은 문구가 여러 카드에 있을 때 오작동을 막는다."""
    sh = shape_by_id(slide, sid)
    if sh is None or not sh.has_text_frame:
        UNMATCHED.append((label or f"apply_runs_in({sid})", "shape/text_frame 없음"))
        return [e[0] for e in entries]

    class _Proxy:  # apply_runs 가 slide.shapes 를 순회하므로 단일 도형으로 감싼다
        shapes = [sh]

    return apply_runs(_Proxy, entries, label=label or f"shape {sid}")


def _set_lines(tf, lines, grow):
    """
    text_frame 의 문단들을 lines 로 교체하는 공통 로직.
    grow=True 면 문단이 부족할 때 마지막 문단 XML 을 복제해 늘린다
    (add_paragraph 은 서식이 초기화되므로 복제가 안전하다).
    grow=False 면 남는 줄을 마지막 문단에 공백으로 합친다
    (표 셀처럼 높이가 고정된 곳에서 행 높이가 커지는 것을 막는다).
    """
    paras = list(tf.paragraphs)
    if grow and len(lines) > len(paras):
        last = paras[-1]._p
        for _ in range(len(lines) - len(paras)):
            last.addnext(copy.deepcopy(last))
        paras = list(tf.paragraphs)

    for i, pa in enumerate(paras):
        if i < len(lines):
            line = lines[i]
            if not grow and i == len(paras) - 1 and len(lines) > len(paras):
                line = " ".join(lines[i:])
        else:
            line = ""
        if pa.runs:
            pa.runs[0].text = line
            for r in pa.runs[1:]:
                r.text = ""
        elif line:
            pa.add_run().text = line


def set_paragraph_lines(slide, sid, lines, grow=True):
    """
    한 텍스트 상자의 문단들을 위에서부터 lines 로 교체.
    본문 여러 줄을 순서대로 갈아끼울 때 apply_runs 보다 간단하다.
    """
    sh = shape_by_id(slide, sid)
    if sh is None or not sh.has_text_frame:
        return False
    _set_lines(sh.text_frame, list(lines), grow)
    return True


# --------------------------------------------------------------------------
# 표
# --------------------------------------------------------------------------
def set_cell(cell, text, grow=False):
    """
    cell.text = ... 은 셀의 폰트/정렬을 날린다. 기존 문단의 첫 run 에 값을 넣고
    나머지 run 을 비우는 방식으로 서식을 보존한다.
    text 에 '\\n' 을 넣으면 셀 안의 문단으로 나눠 배치한다.
    기본은 grow=False - 셀 문단 수보다 줄이 많으면 마지막 문단에 합친다
    (행 높이가 늘어 표가 밀리는 것을 막는다). 줄을 반드시 나눠야 하면 grow=True.
    None 이면 해당 셀은 건드리지 않는다(원본 유지).
    """
    if text is None:
        return
    _set_lines(cell.text_frame, str(text).split("\n"), grow)


def fill_table(slide, sid, matrix, start_row=0, start_col=0):
    """matrix 는 2차원 리스트. None 셀은 원본 유지. 범위를 넘는 값은 무시한다."""
    sh = shape_by_id(slide, sid)
    if sh is None or not getattr(sh, "has_table", False) or not sh.has_table:
        UNMATCHED.append((f"fill_table({sid})", "표 아님/없음"))
        return None
    tb = sh.table
    for ri, row in enumerate(matrix):
        r = start_row + ri
        if r >= len(tb.rows):
            break
        for ci, val in enumerate(row):
            c = start_col + ci
            if c < len(tb.columns):
                set_cell(tb.cell(r, c), val)
    return tb


def drop_last_rows(slide, sid, n):
    """
    행이 남을 때는 빈칸으로 두지 말고 삭제한다. 파이 차트 범례 표처럼
    항목 수가 줄어든 경우 빈 행이 그대로 보이면 미완성처럼 읽힌다.
    """
    sh = shape_by_id(slide, sid)
    if sh is None or not getattr(sh, "has_table", False) or not sh.has_table:
        return 0
    tbl = sh.table._tbl
    trs = tbl.findall(qn("a:tr"))
    n = min(n, len(trs) - 1)  # 최소 1행은 남긴다
    for tr in trs[len(trs) - n:]:
        tbl.remove(tr)
    return n


# --------------------------------------------------------------------------
# 차트
# --------------------------------------------------------------------------
def chart_replace(slide, sid, cats, series, autoscale=True):
    """
    단일 plot 차트용. series 는 [(name, [values...])].
    plots 가 2개 이상(콤보)인 차트에 쓰면 plot 구조가 하나로 붕괴되므로
    그 경우에는 combo_edit 을 사용한다.
    """
    sh = shape_by_id(slide, sid)
    if sh is None or not getattr(sh, "has_chart", False) or not sh.has_chart:
        UNMATCHED.append((f"chart_replace({sid})", "차트 아님/없음"))
        return None
    if len(sh.chart.plots) > 1:
        UNMATCHED.append((f"chart_replace({sid})", "콤보 차트 -> combo_edit 사용"))
        return None
    cd = CategoryChartData()
    cd.categories = list(cats)
    for name, vals in series:
        cd.add_series(name, list(vals))
    sh.chart.replace_data(cd)
    if autoscale:
        clear_axis_scale(sh.chart)
    return sh.chart


def combo_edit(slide, sid, cats=None, series_vals=None, series_names=None, autoscale=True):
    """
    콤보(복합) 차트 및 plot 구조를 유지해야 하는 차트용 in-place XML 편집.
    데이터 포인트 개수는 원본과 같아야 한다(캐시된 c:pt 를 덮어쓰는 방식).
    series_vals: [[...], [...]] 시리즈 순서대로. 부족하면 마지막 값을 재사용한다.
    series_names: 범례 이름. 템플릿의 'DATA', '20XX' 같은 잔존 영문 제거에 필수.
    """
    sh = shape_by_id(slide, sid)
    if sh is None or not getattr(sh, "has_chart", False) or not sh.has_chart:
        UNMATCHED.append((f"combo_edit({sid})", "차트 아님/없음"))
        return None
    cs = sh.chart._chartSpace
    sers = cs.findall(".//" + qn("c:ser"))
    for si, ser in enumerate(sers):
        if series_names and si < len(series_names):
            tx = ser.find(qn("c:tx"))
            if tx is not None:
                for v in tx.findall(".//" + qn("c:v")):
                    v.text = str(series_names[si])
        if cats:
            cat = ser.find(qn("c:cat"))
            if cat is not None:
                for pt in cat.findall(".//" + qn("c:pt")):
                    idx = int(pt.get("idx"))
                    v = pt.find(qn("c:v"))
                    if v is not None and idx < len(cats):
                        v.text = str(cats[idx])
        if series_vals:
            vals = series_vals[min(si, len(series_vals) - 1)]
            val = ser.find(qn("c:val"))
            if val is not None:
                for pt in val.findall(".//" + qn("c:pt")):
                    idx = int(pt.get("idx"))
                    v = pt.find(qn("c:v"))
                    if v is not None and idx < len(vals):
                        v.text = str(vals[idx])
    if autoscale:
        clear_axis_scale(sh.chart)
    return sh.chart


def clear_axis_scale(chart, axes=("c:valAx",)):
    """
    템플릿 차트는 원본 수치에 맞춘 축 최대/최소가 하드코딩된 경우가 있다.
    새 데이터의 크기가 다르면 막대가 잘리거나 눌려 보이므로 고정값을 제거해
    자동 스케일로 되돌린다.
    """
    removed = 0
    cs = chart._chartSpace
    for ax_tag in axes:
        for ax in cs.findall(".//" + qn(ax_tag)):
            sc = ax.find(qn("c:scaling"))
            if sc is None:
                continue
            for tag in ("c:max", "c:min"):
                el = sc.find(qn(tag))
                if el is not None:
                    sc.remove(el)
                    removed += 1
    return removed


def set_series_point_count(*_args, **_kwargs):
    """
    포인트 개수를 바꿔야 하는 콤보 차트는 안전한 일반해가 없다.
    이 경우 (1) 카테고리 수가 같은 다른 슬라이드 차트를 재활용하거나
    (2) 표현할 항목 수를 템플릿에 맞춰 재구성하는 편이 낫다.
    """
    raise NotImplementedError("포인트 수 변경 대신 항목 수를 템플릿에 맞춰 구성할 것")


# --------------------------------------------------------------------------
# 진행률 바 / 타임라인
# --------------------------------------------------------------------------
def set_bar_fraction(slide, track_sid, fill_sid, fraction):
    """
    '트랙(회색 배경) + 필(강조색)' 2겹 도형으로 만든 진행률 바의 폭 조정.
    숫자 라벨만 고치고 바 길이를 그대로 두면 수치와 그림이 어긋난다.
    """
    track = shape_by_id(slide, track_sid)
    fill = shape_by_id(slide, fill_sid)
    if track is None or fill is None:
        return None
    fill.width = int(track.width * max(0.0, min(1.0, fraction)))
    return fill.width


def place_span(slide, sid, col0_left, col_width, start_index, span, inset=0.0):
    """
    간트/로드맵 바를 표 열 격자에 맞춘다. 단위는 EMU 또는 Inches 반환값.
      col0_left  : 첫 데이터 열의 좌측 x
      col_width  : 열 하나의 폭
      start_index: 0-based 시작 열
      span       : 걸치는 열 수
      inset      : 좌우 여백(EMU). 셀 경계선과 붙지 않게 살짝 띄울 때 사용
    """
    sh = shape_by_id(slide, sid)
    if sh is None:
        return None
    sh.left = int(col0_left + start_index * col_width + inset)
    sh.width = int(span * col_width - 2 * inset)
    return sh.left, sh.width


def table_grid(slide, sid, first_data_col=1):
    """place_span 에 넣을 (col0_left, col_width) 를 표에서 직접 계산한다."""
    sh = shape_by_id(slide, sid)
    if sh is None or not getattr(sh, "has_table", False) or not sh.has_table:
        return None
    tb = sh.table
    x = sh.left
    for ci in range(first_data_col):
        x += tb.columns[ci].width
    return x, tb.columns[first_data_col].width


# --------------------------------------------------------------------------
# 그림
# --------------------------------------------------------------------------
def swap_picture(slide, sid, image_path, mode="contain", pad=0.0):
    """
    사진/로고 교체. 그림 placeholder 는 이미지 소스를 바꿀 수 없으므로
    원래 도형의 사각 영역을 기억한 뒤 삭제하고 그 안에 새 이미지를 넣는다.
      mode 'contain': 비율 유지하며 영역 안에 맞춘 뒤 가운데 정렬 (로고 권장)
      mode 'fill'   : 영역을 그대로 채움 (비율 왜곡 가능, 배경 사진용)
      pad          : 영역 안쪽 여백 비율 0~0.4
    """
    sh = shape_by_id(slide, sid)
    if sh is None:
        return None
    bx, by, bw, bh = sh.left, sh.top, sh.width, sh.height
    parent = sh._element.getparent()
    parent.remove(sh._element)

    if pad:
        dx, dy = int(bw * pad), int(bh * pad)
        bx, by, bw, bh = bx + dx, by + dy, bw - 2 * dx, bh - 2 * dy

    if mode == "fill":
        return slide.shapes.add_picture(image_path, bx, by, width=bw, height=bh)

    img = Image.from_file(image_path)
    ar = img.size[0] / img.size[1]
    w, h = bw, int(bw / ar)
    if h > bh:
        h, w = bh, int(bh * ar)
    return slide.shapes.add_picture(image_path, bx + (bw - w) // 2, by + (bh - h) // 2,
                                    width=w, height=h)


# --------------------------------------------------------------------------
# 발표 노트
# --------------------------------------------------------------------------
def set_notes(slide, text, donor=None):
    """
    노트 텍스트 설정. '\\n' 은 별도 문단(<a:p>)이 되어 PowerPoint 에서 실제
    줄바꿈으로 렌더링된다. 한 문장당 한 줄로 넣으면 발표 중 읽기 쉽다.

    일부 템플릿은 노트 마스터에 body placeholder 가 없어 notes_text_frame 이
    None 이다. 그때는 donor 슬라이드(기본: 노트를 가진 첫 슬라이드)에서
    placeholder 를 복제해 붙인다.
    """
    ns = slide.notes_slide
    tf = ns.notes_text_frame
    if tf is None:
        donor_sp = None
        if donor is not None:
            for shp in donor.notes_slide.shapes:
                pf = shp.placeholder_format
                if shp.has_text_frame and pf is not None and pf.idx == 1:
                    donor_sp = shp._element
                    break
        if donor_sp is not None:
            ns.shapes._spTree.append(copy.deepcopy(donor_sp))
            tf = ns.notes_text_frame
    if tf is None:
        UNMATCHED.append(("set_notes", "노트 placeholder 없음(donor 지정 필요)"))
        return False
    tf.text = str(text)
    return True


# --------------------------------------------------------------------------
# 문서 전역 정리
# --------------------------------------------------------------------------
def sweep_tokens(prs, mapping, verbose=True):
    """
    남은 템플릿 잔존 문자열을 전 슬라이드에서 일괄 치환한다.
    슬라이드별 매핑을 끝낸 뒤 '20XX', 'DATA', 'Lorem' 같은 잔여물을 쓸어내는 마무리 단계.
    """
    hits = 0
    for sl in prs.slides:
        for sh in iter_text_shapes(sl.shapes):
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    for old, new in mapping.items():
                        if old in r.text:
                            r.text = r.text.replace(old, new)
                            hits += 1
        for sh in sl.shapes:
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        for pa in c.text_frame.paragraphs:
                            for r in pa.runs:
                                for old, new in mapping.items():
                                    if old in r.text:
                                        r.text = r.text.replace(old, new)
                                        hits += 1
    if verbose:
        print(f"sweep_tokens: {hits}건 치환")
    return hits


def emu(inches_value):
    return Emu(int(inches_value * 914400))


# --------------------------------------------------------------------------
# 슬라이드 개수 조정
# --------------------------------------------------------------------------
def delete_slide(prs, index):
    """
    0-based 인덱스의 슬라이드 삭제. 템플릿이 필요보다 많은 장수를 가진 경우
    남는 장을 빈 슬라이드로 두지 말고 지운다.
    python-pptx 에 공식 API 가 없어 sldIdLst 항목과 관계를 함께 제거한다.
    삭제 후 인덱스가 밀리므로 여러 장을 지울 때는 큰 인덱스부터 처리할 것.
    """
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    if not (0 <= index < len(ids)):
        return False
    sldId = ids[index]
    prs.part.drop_rel(sldId.rId)
    sldIdLst.remove(sldId)
    return True


def keep_slides(prs, keep_indices):
    """유지할 0-based 인덱스만 남기고 나머지를 삭제한다."""
    keep = set(keep_indices)
    for i in range(len(prs.slides) - 1, -1, -1):
        if i not in keep:
            delete_slide(prs, i)
    return len(prs.slides)


def move_slide(prs, old_index, new_index):
    """슬라이드 순서 변경. 간지 순서를 콘텐츠 흐름에 맞출 때 사용."""
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    if not (0 <= old_index < len(ids)):
        return False
    el = ids[old_index]
    sldIdLst.remove(el)
    sldIdLst.insert(new_index, el)
    return True

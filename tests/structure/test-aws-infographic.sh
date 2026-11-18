#!/bin/bash
# aws-infographic: SKILL.md and references agree with the shipped scripts; infokit.py finds the icon bundle and
# fonts; the page template renders and passes the text lint; check_editable.py on decks made in $TEST_TMP where
# each rule is broken once; icon_png.py; the aws-ppt-skills side of the editable deck (addIcon, check_deck.py);
# and, when the deck tools are installed, the example deck built, templated and checked end to end
# (sourced by tests/run-all.sh). Nothing is written into skills/ (Python bytecode goes to $TEST_TMP).

IG_DIR=skills/aws-infographic
IG_PPT=skills/aws-ppt-skills
IG_PYI=(python3 -I -X pycache_prefix="$TEST_TMP/ig-pycache")   # standard library only
IG_PY=(python3 -X pycache_prefix="$TEST_TMP/ig-pycache")       # may use Pillow, python-pptx from the user site
IG_REPO=$(pwd -P)
IG_W="$TEST_TMP/ig"
mkdir -p "$IG_W/work" "$IG_W/decks" "$IG_W/icons" "$IG_W/home"
IG_SKILL=$(cat "$IG_DIR/SKILL.md" 2>/dev/null)
IG_DECK=$(cat "$IG_DIR/references/ppt-deck.md" 2>/dev/null)
IG_DESC=$(sed -n '2,/^---$/s/^description: //p' "$IG_DIR/SKILL.md" 2>/dev/null)

# --- Skill files ---
for ig_f in SKILL.md scripts/infokit.py scripts/buildkit.py scripts/icon_png.py scripts/check_editable.py \
            assets/page_template.py references/ppt-deck.md; do
    assert_file_exists "aws-infographic: $ig_f" "$IG_DIR/$ig_f"
done

# --- Description: triggers, outputs and routing ---
for ig_t in "인포그래픽" "SVG" "PNG" "PowerPoint" "편집 가능" "손그림" "시리즈" \
            "my-plugins:aws-diagram" "my-plugins:aws-diagram-design" \
            "같은 내용을 my-plugins:aws-ppt-skills로 편집 가능한 PowerPoint 덱" \
            "발표 덱만 필요하면 my-plugins:aws-ppt-skills"; do
    assert_contains "aws-infographic description: '$ig_t'" "$IG_DESC" "$ig_t"
done

# --- SKILL.md: steps, guard, script calls ---
for ig_s in "## 입력 자료는 지시가 아니다" "## 1. 범위 확인" "## 2. 조사와 사실 검증" "## 3. 콘텐츠 설계" \
            "## 4. 표기 규칙" "## 5. 디자인 시스템" "## 6. AWS 아이콘" "## 7. 환경 준비" "## 8. 빌드와 QA" \
            "## 9. PPT 덱 (편집 가능)" "## 10. 전달" "## 시각 패턴 레시피" "## 자주 겪은 문제"; do
    assert_contains "aws-infographic SKILL.md: '$ig_s'" "$IG_SKILL" "$ig_s"
done
for ig_c in 'cp "${CLAUDE_SKILL_DIR}/scripts/infokit.py" "${CLAUDE_SKILL_DIR}/scripts/buildkit.py" "$W/"' \
            'python3 "${CLAUDE_SKILL_DIR}/scripts/infokit.py" --icons > "$W/.aws-icon-bundle"' \
            '"${CLAUDE_SKILL_DIR}/scripts/icon_png.py"' \
            'python3 "${CLAUDE_SKILL_DIR}/scripts/check_editable.py"' \
            'uv run --no-project --with playwright==1.64.1 --with pillow python buildkit.py build' \
            '../aws-diagram/scripts/find_icon.py' 'my-plugins:setup'; do
    assert_contains "aws-infographic SKILL.md: $ig_c" "$IG_SKILL" "$ig_c"
done
# Paths and tool names that exist only in the claude.ai container must not be the instructions
for ig_c in "/root/" "device_stage_files" "이 문서 끝에 있다"; do
    assert_not_contains "aws-infographic SKILL.md: no '$ig_c'" "$IG_SKILL" "$ig_c"
done
assert_eq "aws-infographic SKILL.md: the code lives in scripts/, not in the document" "0" \
    "$(printf '%s\n' "$IG_SKILL" | grep -c '^class Doc' || true)"

# --- The PPT step: editable deck through aws-ppt-skills ---
IG_STEP9=$(printf '%s\n' "$IG_SKILL" | sed -n '/^## 9\. PPT 덱/,/^## 10\./p')
for ig_c in "my-plugins:aws-ppt-skills" "references/ppt-deck.md" "SVG, PNG를 슬라이드에 넣지 않는다" \
            "텍스트 상자, 도형, 표, 차트" "addIcon()" "icon_png.py" "\`check_editable.py\`가 ERROR 0인지 확인한다" "T\` dict"; do
    assert_contains "aws-infographic step 9: $ig_c" "$IG_STEP9" "$ig_c"
done
assert_contains "aws-infographic step 1 asks the deck questions in the same round" \
    "$(printf '%s\n' "$IG_SKILL" | sed -n '/^## 1\. 범위 확인/,/^## 2\./p')" "PPT 덱"
for ig_c in "addDiagram()" "svg_to_png.py" "function addGrid(" "function addSteps(" "function addIconRow(" "function addLanes(" \
            "addIcon(" "addNativeChart(" "addDefBox(" "icon_png.py" "check_editable.py" "check_deck.py" \
            "apply_template.py" "newSlide(\"COVER\")" "newSlide(\"CLOSING\")" "s.addNotes("; do
    assert_contains "ppt-deck.md: $ig_c" "$IG_DECK" "$ig_c"
done
assert_contains "ppt-deck.md: addDiagram() is named as not used" "$IG_DECK" "\`addDiagram()\`, \`svg_to_png.py\`를 쓰지 않는다"
assert_contains "ppt-deck.md: a lint warning is not written around" "$IG_DECK" "문장을 바꿔 검사를 피하지 않는다"
assert_contains "ppt-deck.md: section numbers stay in the slide titles" "$IG_DECK" "제목은 번호를 붙인 섹션 제목"
assert_contains "ppt-deck.md: the content comes from T and the verification log" "$IG_DECK" "\`T\` dict와 검증 로그(\`\$W/sources.md\`)"
assert_contains "aws-infographic step 2 keeps the verification log in the work folder" \
    "$(printf '%s\n' "$IG_SKILL" | sed -n '/^## 2\. 조사와 사실 검증/,/^## 3\./p')" "검증 로그를 \`\$W/sources.md\`에 유지한다"
# The helper and example blocks never call the picture path of a normal deck
IG_JS=$("${IG_PYI[@]}" - "$IG_DIR/references/ppt-deck.md" <<'PY' 2>/dev/null || true
import re, sys
md = open(sys.argv[1], encoding="utf-8").read()
print("\n".join(re.findall(r"```javascript\n(.*?)```", md, flags=re.S)))
PY
)
assert_not_contains "ppt-deck.md code: no addDiagram( call" "$IG_JS" "addDiagram("
assert_not_contains "ppt-deck.md code: no svg: picture name" "$IG_JS" '"svg:'
assert_not_contains "ppt-deck.md code: no .svg file" "$IG_JS" ".svg"

# --- buildkit.py and icon_png.py import Playwright only when they render ---
assert_eq "buildkit.py: no module-level playwright import" "" \
    "$(grep -nE '^(from|import) playwright' "$IG_DIR/scripts/buildkit.py" 2>/dev/null | tr '\n' ' ')"
assert_eq "icon_png.py: no module-level playwright import" "" \
    "$(grep -nE '^(from|import) playwright' "$IG_DIR/scripts/icon_png.py" 2>/dev/null | tr '\n' ' ')"
assert_eq "infokit.py: no module-level Pillow import (--icons and --fonts run on plain python3)" "" \
    "$(grep -nE '^(from|import) PIL' "$IG_DIR/scripts/infokit.py" 2>/dev/null | tr '\n' ' ')"

# --- infokit.py: icon bundle lookup (env, pointer next to the copy, sibling skill) ---
IG_OUT=$(env -u AWS_ICON_BUNDLE HOME="$IG_W/home" "${IG_PYI[@]}" "$IG_DIR/scripts/infokit.py" --icons 2>&1); IG_RC=$?
assert_eq "infokit --icons: finds the sibling aws-diagram bundle" "$IG_REPO/skills/aws-diagram/assets/icons.json" "$IG_OUT"
assert_eq "infokit --icons: exit 0" "0" "$IG_RC"
cp "$IG_DIR/scripts/infokit.py" "$IG_DIR/scripts/buildkit.py" "$IG_W/work/" 2>/dev/null
cp "$IG_DIR/assets/page_template.py" "$IG_W/work/page_template.py" 2>/dev/null
IG_OUT=$(env -u AWS_ICON_BUNDLE HOME="$IG_W/home" "${IG_PYI[@]}" "$IG_W/work/infokit.py" --icons 2>&1); IG_RC=$?
assert_eq "infokit --icons: a copy with no pointer, env or installed plugin exits 1" "1" "$IG_RC"
assert_contains "infokit --icons: says how to point at the bundle" "$IG_OUT" "AWS_ICON_BUNDLE"
printf '%s\n' "$IG_REPO/skills/aws-diagram/assets/icons.json" > "$IG_W/work/.aws-icon-bundle"
IG_OUT=$(env -u AWS_ICON_BUNDLE HOME="$IG_W/home" "${IG_PYI[@]}" "$IG_W/work/infokit.py" --icons 2>&1)
assert_eq "infokit --icons: the copy follows .aws-icon-bundle" "$IG_REPO/skills/aws-diagram/assets/icons.json" "$IG_OUT"
printf '{"sets": {}}\n' > "$IG_W/empty-icons.json"
IG_OUT=$(env AWS_ICON_BUNDLE="$IG_W/empty-icons.json" HOME="$IG_W/home" "${IG_PYI[@]}" "$IG_W/work/infokit.py" --icons 2>&1)
assert_eq "infokit --icons: AWS_ICON_BUNDLE wins over the pointer" "$IG_W/empty-icons.json" "$IG_OUT"

# --- infokit.py: font lookup by file name (INFOKIT_FONTS first, any folder layout) ---
mkdir -p "$IG_W/fonts/nanumsquare-otf" "$IG_W/fonts/d2coding"
: > "$IG_W/fonts/nanumsquare-otf/NanumSquareB.otf"; : > "$IG_W/fonts/nanumsquare-otf/NanumSquareEB.otf"
: > "$IG_W/fonts/d2coding/D2Coding.ttf"; : > "$IG_W/fonts/d2coding/D2CodingBold.ttf"
IG_OUT=$(env INFOKIT_FONTS="$IG_W/fonts" "${IG_PYI[@]}" "$IG_DIR/scripts/infokit.py" --fonts 2>&1)
assert_contains "infokit --fonts: Bold from INFOKIT_FONTS" "$IG_OUT" "700 $IG_W/fonts/nanumsquare-otf/NanumSquareB.otf"
assert_contains "infokit --fonts: ExtraBold from INFOKIT_FONTS" "$IG_OUT" "800 $IG_W/fonts/nanumsquare-otf/NanumSquareEB.otf"
assert_contains "infokit --fonts: D2Coding regular" "$IG_OUT" "code $IG_W/fonts/d2coding/D2Coding.ttf"
assert_contains "infokit --fonts: D2Coding bold is its own file, not face 1 of a .ttf" "$IG_OUT" "code-bold $IG_W/fonts/d2coding/D2CodingBold.ttf"

# --- The page template renders in both themes and sizes and passes the text lint ---
if "${IG_PY[@]}" -c "import PIL" >/dev/null 2>&1; then
    IG_OUT=$( (cd "$IG_W/work" && env -u AWS_ICON_BUNDLE "${IG_PY[@]}" - <<'PY' 2>&1
import buildkit, page_template
for fn, box in (("landscape", "0 0 1920 1080"), ("portrait", "0 0 1536 1920")):
    for theme in ("dark", "light"):
        svg = getattr(page_template, fn)(theme)
        issues = buildkit.lint(svg)
        print(fn, theme, "viewBox=%s" % (('viewBox="%s"' % box) in svg), "icon=%s" % ("<image href=\"data:image/" in svg),
              "boxes=%d" % svg.count("data-box="), "lint=%d" % len(issues), issues[:3])
print("bad", [a for a, _ in buildkit.lint('<svg><text>A · B</text><text>지연이 줄어듭니다</text><text>서비스 지연은 어디서 생기나</text><text>요청 경로별 지연 구조</text></svg>')])
PY
    ) )
    for ig_c in "landscape dark viewBox=True icon=True" "landscape light viewBox=True icon=True" \
                "portrait dark viewBox=True icon=True" "portrait light viewBox=True icon=True"; do
        assert_contains "page template: $ig_c" "$IG_OUT" "$ig_c"
    done
    assert_eq "page template: lint is clean in every theme and size" "4" "$(printf '%s\n' "$IG_OUT" | grep -c 'lint=0 \[\]' || true)"
    assert_not_contains "page template: every text carries its box for the overflow QA" "$IG_OUT" "boxes=0"
    assert_contains "buildkit.lint: middle dot, predicate ending and question title, noun phrase left alone" "$IG_OUT" \
        "bad ['banned-char', 'ending', 'question']"

    # --- icon_png.py: unknown name, PNG icons without a browser ---
    IG_OUT=$("${IG_PY[@]}" "$IG_DIR/scripts/icon_png.py" "$IG_W/icons" service/No-Such-Service 2>&1); IG_RC=$?
    assert_eq "icon_png: unknown icon exits 2" "2" "$IG_RC"
    assert_contains "icon_png: names the unknown icon" "$IG_OUT" "service/No-Such-Service"
    assert_eq "icon_png: nothing written for an unknown icon" "" "$(ls "$IG_W/icons" 2>/dev/null | tr '\n' ' ')"
    IG_OUT=$("${IG_PY[@]}" "$IG_DIR/scripts/icon_png.py" "$IG_W/icons" --theme dark agentcore-light/Agentcore 2>&1); IG_RC=$?
    assert_eq "icon_png: a PNG icon needs no browser (exit 0)" "0" "$IG_RC"
    assert_contains "icon_png: prints the icon and its file" "$IG_OUT" "agentcore-light/Agentcore	$IG_W/icons/agentcore-light-Agentcore.png"
    assert_eq "icon_png: the file is a PNG" "89504e47" "$(head -c 4 "$IG_W/icons/agentcore-light-Agentcore.png" 2>/dev/null | od -An -tx1 | tr -d ' \n')"
else
    skip "aws-infographic page template and icon_png" "Pillow is not importable by python3; run my-plugins:setup install"
fi
assert_eq "aws-infographic: no __pycache__ in the skill" "" "$(find "$IG_DIR" -name __pycache__ | tr '\n' ' ')"

# --- check_editable.py: one deck per rule, made with the standard library ---
cat > "$IG_W/mkdeck.py" <<'PY'
"""mkdeck.py OUT.pptx [svgrel] [svgblip] [dtd] [noslides] [name=<picture name>] [in=<picture size in inches>]"""
import sys, zipfile
out, opts = sys.argv[1], sys.argv[2:]
name = next((o[5:] for o in opts if o.startswith("name=")), "icon:service/Amazon-Bedrock")
size = int(float(next((o[3:] for o in opts if o.startswith("in=")), "0.53")) * 914400)
NS = ('xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
blip = ('<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}"><asvg:svgBlip '
        'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="rId2"/></a:ext></a:extLst>'
        if "svgblip" in opts else "")
dtd = '<!DOCTYPE p:sld [<!ENTITY a "aaaaaaaaaa">]>' if "dtd" in opts else ""
slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{dtd}
<p:sld {NS}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Text 1"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="457200"/></a:xfrm><a:prstGeom prst="roundRect"/></p:spPr><p:txBody><a:bodyPr/><a:p><a:r><a:t>요청 경로</a:t></a:r></a:p></p:txBody></p:sp>
<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="3" name="Line 2"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="0"/></a:xfrm><a:prstGeom prst="line"/></p:spPr></p:cxnSp>
<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="4" name="Table 3"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="914400"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblGrid><a:gridCol w="914400"/></a:tblGrid><a:tr h="457200"><a:tc><a:txBody><a:bodyPr/><a:p><a:r><a:t>구간</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>
<p:pic><p:nvPicPr><p:cNvPr id="5" name="{name}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId1">{blip}</a:blip><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{size}" cy="{size}"/></a:xfrm><a:prstGeom prst="rect"/></p:spPr></p:pic>
</p:spTree></p:cSld></p:sld>"""
IMG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
rels = [f'<Relationship Id="rId1" Type="{IMG}" Target="../media/image1.png"/>']
if "svgrel" in opts or "svgblip" in opts:
    rels.append(f'<Relationship Id="rId2" Type="{IMG}" Target="../media/image2.svg"/>')
with zipfile.ZipFile(out, "w") as z:
    z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
    if "noslides" not in opts:
        z.writestr("ppt/slides/slide1.xml", slide)
        z.writestr("ppt/slides/_rels/slide1.xml.rels",
                   '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(rels) + "</Relationships>")
PY
# ig_deck NAME EXPECT RC [mkdeck options...] [-- check_editable options...]
ig_deck() {
    local name=$1 expect=$2 rc=$3 out got; shift 3
    local mk=() chk=()
    while [ $# -gt 0 ] && [ "$1" != "--" ]; do mk+=("$1"); shift; done
    [ $# -gt 0 ] && shift
    chk=("$@")
    "${IG_PYI[@]}" "$IG_W/mkdeck.py" "$IG_W/decks/$name.pptx" "${mk[@]}" 2>&1
    out=$("${IG_PYI[@]}" "$IG_DIR/scripts/check_editable.py" "$IG_W/decks/$name.pptx" "${chk[@]}" 2>&1); got=$?
    assert_contains "check_editable: $name" "$out" "$expect"
    assert_eq "check_editable: $name (exit $rc)" "$rc" "$got"
}
ig_deck clean "결과: ERROR 0" 0
ig_deck counts "slide 1: 텍스트와 도형 1, 선 1, 표 1, 차트 0, 아이콘 1" 0
ig_deck svgrel "ERROR slide 1: SVG 파일이 연결되어 있음 (../media/image2.svg)" 1 svgrel
ig_deck svgblip "ERROR slide 1: 그림 'icon:service/Amazon-Bedrock'에 SVG가 들어 있음" 1 svgblip
ig_deck picture "ERROR slide 1: 아이콘이 아닌 그림 'Picture 4' (9.20 x 9.20 in)" 1 "name=Picture 4" in=9.2
ig_deck smallpicture "ERROR slide 1: 아이콘이 아닌 그림 'Diagram flow'" 1 "name=Diagram flow"
ig_deck bigicon "ERROR slide 1: 아이콘 'icon:service/Amazon-Bedrock'이 한도보다 큼 (3.00 x 3.00 in, 한도 1.20 in)" 1 in=3
ig_deck bigicon-allowed "결과: ERROR 0" 0 in=3 -- --icon-max 4
ig_deck noslides "슬라이드가 없습니다" 2 noslides
ig_deck dtd "슬라이드 XML을 읽지 못했습니다: ppt/slides/slide1.xml (DTD가 있는 XML)" 2 dtd
IG_OUT=$("${IG_PYI[@]}" "$IG_DIR/scripts/check_editable.py" "$IG_W/decks/none.pptx" 2>&1); IG_RC=$?
assert_eq "check_editable: a missing file exits 2" "2" "$IG_RC"

# --- aws-ppt-skills side: addIcon() and the icon exemption in check_deck.py ---
IG_PPT_SKILL=$(cat "$IG_PPT/SKILL.md" 2>/dev/null)
assert_contains "aws-ppt-skills: addIcon() helper" "$IG_PPT_SKILL" "function addIcon(s, i)"
assert_contains "aws-ppt-skills: addIcon() names the picture icon:<ref>" "$IG_PPT_SKILL" 'objectName: "icon:" + i.ref'
assert_contains "aws-ppt-skills: names the editable deck as its own case" "$IG_PPT_SKILL" "- **Editable decks** ("
assert_contains "aws-ppt-skills: editable decks use no addDiagram() and no SVG" "$IG_PPT_SKILL" "no \`addDiagram()\` and no SVG anywhere"
assert_contains "aws-ppt-skills: editable decks end with check_editable.py" "$IG_PPT_SKILL" "../aws-infographic/scripts/check_editable.py"
assert_contains "aws-ppt-skills: icon PNG source" "$IG_PPT_SKILL" "../aws-infographic/scripts/icon_png.py"
assert_eq "check_deck.py and check_editable.py use one icon size limit" "ICON_MAX_IN = 1.2|ICON_MAX_IN = 1.2|" \
    "$(grep -ho '^ICON_MAX_IN = [0-9.]*' "$IG_PPT/scripts/check_deck.py" "$IG_DIR/scripts/check_editable.py" 2>/dev/null | tr '\n' '|')"
if "${IG_PY[@]}" -c "import pptx, PIL" >/dev/null 2>&1; then
    (cd "$IG_W" && "${IG_PY[@]}" - <<'PY' 2>&1
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
Image.new("RGB", (8, 8), (255, 153, 0)).save("dot.png")
for fname, pic_name, size in (("pd-icon.pptx", "icon:service/Amazon-Bedrock", 0.53),
                              ("pd-plain.pptx", "Picture 1", 0.53),
                              ("pd-bigicon.pptx", "icon:service/Amazon-Bedrock", 3.0)):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    pic = slide.shapes.add_picture("dot.png", Inches(1), Inches(1), Inches(size), Inches(size))
    pic._element.nvPicPr.cNvPr.set("name", pic_name)
    prs.save(fname)
PY
    )
    IG_OUT=$("${IG_PY[@]}" "$IG_PPT/scripts/check_deck.py" "$IG_W/pd-icon.pptx" 2>&1)
    assert_not_contains "check_deck: an icon: picture of icon size is not asked for a vector SVG" "$IG_OUT" "has no vector SVG"
    IG_OUT=$("${IG_PY[@]}" "$IG_PPT/scripts/check_deck.py" "$IG_W/pd-plain.pptx" 2>&1)
    assert_contains "check_deck: any other picture still is" "$IG_OUT" "picture 'Picture 1' has no vector SVG"
    IG_OUT=$("${IG_PY[@]}" "$IG_PPT/scripts/check_deck.py" "$IG_W/pd-bigicon.pptx" 2>&1)
    assert_contains "check_deck: a figure named icon: is not exempt" "$IG_OUT" "picture 'icon:service/Amazon-Bedrock' has no vector SVG"
else
    skip "check_deck.py icon exemption" "python-pptx or Pillow is not importable; run my-plugins:setup install"
fi

# --- The example deck: helper blocks + example content, built, templated, linted and checked ---
IG_NODE_PATH=""
if command -v node >/dev/null 2>&1; then
    for ig_r in $(printf '%s' "${NODE_PATH:-}" | tr ':' ' ') $(npm root -g 2>/dev/null); do
        [ -d "$ig_r/pptxgenjs" ] && { IG_NODE_PATH="$ig_r"; break; }
    done
fi
"${IG_PYI[@]}" - "$IG_PPT/SKILL.md" "$IG_DIR/references/ppt-deck.md" "$IG_W/deck-build.js" <<'PY' 2>&1
import re, sys
ppt, deck, out = sys.argv[1:]
def blocks(path):
    return re.findall(r"```javascript\n(.*?)```", open(path, encoding="utf-8").read(), flags=re.S)
def one(path, marker):
    hit = [b for b in blocks(path) if marker in b]
    if len(hit) != 1:
        sys.exit("%s: %d javascript blocks with %r, expected 1" % (path, len(hit), marker))
    return hit[0]
parts = [one(ppt, "function newSlide("), one(deck, "function addGrid("), one(deck, 'newSlide("COVER")')]
open(out, "w", encoding="utf-8").write("\n".join(parts))
PY
if command -v node >/dev/null 2>&1; then
    IG_ERR=$(node --check "$IG_W/deck-build.js" 2>&1) && pass "example deck script parses (helper block + deck helpers + example)" \
        || fail "example deck script parses (helper block + deck helpers + example)" "$(printf '%s' "$IG_ERR" | head -3)"
else
    skip "example deck script parses" "node is not installed"
fi
if [ -n "$IG_NODE_PATH" ] && "${IG_PY[@]}" -c "import pptx, lxml" >/dev/null 2>&1; then
    mkdir -p "$IG_W/deck/icons"
    cp "$IG_W/deck-build.js" "$IG_W/deck/build_deck.js"
    "${IG_PYI[@]}" - "$IG_W/deck/icons/service-Amazon-Bedrock.png" <<'PY'
import struct, sys, zlib
def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
raw = b"".join(b"\x00" + b"\xff\x99\x00\xff" * 8 for _ in range(8))
open(sys.argv[1], "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
PY
    IG_OUT=$( (cd "$IG_W/deck" && NODE_PATH="$IG_NODE_PATH" node build_deck.js 2>&1 \
        && "${IG_PY[@]}" "$IG_REPO/$IG_PPT/scripts/apply_template.py" infographic_raw.pptx --out infographic.pptx 2>&1) ); IG_RC=$?
    assert_eq "example deck: builds and takes the template (exit 0)" "0" "$IG_RC"
    [ "$IG_RC" -eq 0 ] || echo "    $IG_OUT" | head -5
    IG_OUT=$("${IG_PY[@]}" "$IG_PPT/scripts/check_deck.py" "$IG_W/deck/infographic.pptx" 2>&1); IG_RC=$?
    assert_contains "example deck: check_deck.py has no errors and no warnings" "$IG_OUT" "0 error(s), 0 warning(s)"
    IG_OUT=$("${IG_PYI[@]}" "$IG_DIR/scripts/check_editable.py" "$IG_W/deck/infographic.pptx" 2>&1); IG_RC=$?
    assert_eq "example deck: check_editable.py passes (exit 0)" "0" "$IG_RC"
    assert_contains "example deck: a native table on the first content slide" "$IG_OUT" "slide 2: 텍스트와 도형"
    assert_contains "example deck: table and no chart counted" "$(printf '%s\n' "$IG_OUT" | grep '^slide 2:')" "표 1"
    assert_contains "example deck: the AWS icon is an icon picture" "$(printf '%s\n' "$IG_OUT" | grep '^slide 3:')" "아이콘 1"
    assert_eq "example deck: no SVG part in the file" "" "$(unzip -Z1 "$IG_W/deck/infographic.pptx" 2>/dev/null | grep -i '\.svg$' | tr '\n' ' ')"
    # a timeline and a table without a header row, as the mapping table names them
    "${IG_PYI[@]}" - "$IG_W/deck/build_deck.js" "$IG_W/deck/build_more.js" <<'PY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
more = '''
s = newSlide("CONTENT");
addContentHeader(s, "3. 요청 타임라인", "첫 글자까지 걸리는 구간");
addLanes(s, [
  { label: "Client", bars: [{ from: 0, to: 60, text: "전송" }] },
  { label: "Model", bars: [{ from: 330, to: 620, text: "Prefill", emph: true }, { from: 620, to: 1000, text: "Decode", dashed: true }] },
], { y: 1.50, h: 1.60, marks: [{ from: 0, to: 620, text: "TTFT" }] });
addGrid(s, null, [["결정", "민감 규칙, 업무, 첨부 순서"], ["대기열", "상담 0, 배치 10"]], { y: 3.30, h: 1.10 });   // default column widths come from the rows
s.addNotes(["요청 타임라인은 구간을 같은 눈금 위에 놓은 그림입니다.", "Prefill 구간이 첫 글자까지의 시간을 대부분 차지합니다.",
  "아래 표는 모델을 정하는 순서와 대기열의 우선순위를 보여 줍니다.", "다음 장에서 마무리하겠습니다."]);

s = newSlide("CLOSING");'''
assert src.count('s = newSlide("CLOSING");') == 1
open(sys.argv[2], "w", encoding="utf-8").write(src.replace('s = newSlide("CLOSING");', more).replace("infographic_raw.pptx", "more_raw.pptx"))
PY
    IG_OUT=$( (cd "$IG_W/deck" && NODE_PATH="$IG_NODE_PATH" node build_more.js 2>&1 \
        && "${IG_PY[@]}" "$IG_REPO/$IG_PPT/scripts/apply_template.py" more_raw.pptx --out more.pptx 2>&1) ); IG_RC=$?
    assert_eq "timeline and header-less table: builds and takes the template (exit 0)" "0" "$IG_RC"
    IG_OUT=$("${IG_PY[@]}" "$IG_PPT/scripts/check_deck.py" "$IG_W/deck/more.pptx" 2>&1)
    assert_contains "timeline and header-less table: check_deck.py has no errors and no warnings" "$IG_OUT" "0 error(s), 0 warning(s)"
    IG_OUT=$("${IG_PYI[@]}" "$IG_DIR/scripts/check_editable.py" "$IG_W/deck/more.pptx" 2>&1); IG_RC=$?
    assert_eq "timeline and header-less table: check_editable.py passes (exit 0)" "0" "$IG_RC"
    assert_contains "timeline and header-less table: lane rules and the span are lines, the rows one table" \
        "$(printf '%s\n' "$IG_OUT" | grep '^slide 4:')" "선 3, 표 1, 차트 0, 아이콘 0"
    # the same deck with the infographic pasted as one picture is refused
    sed 's#^pres.writeFile#s.addImage({ path: "icons/service-Amazon-Bedrock.png", x: 0.42, y: 1.50, w: 9.16, h: 3.00 });\npres.writeFile#' \
        "$IG_W/deck/build_deck.js" > "$IG_W/deck/build_pasted.js"
    IG_OUT=$( (cd "$IG_W/deck" && NODE_PATH="$IG_NODE_PATH" node build_pasted.js >/dev/null 2>&1 \
        && "${IG_PY[@]}" "$IG_REPO/$IG_PPT/scripts/apply_template.py" infographic_raw.pptx --out pasted.pptx >/dev/null 2>&1; \
        "${IG_PYI[@]}" "$IG_REPO/$IG_DIR/scripts/check_editable.py" pasted.pptx 2>&1) ); IG_RC=$?
    assert_eq "pasted figure: check_editable.py fails (exit 1)" "1" "$IG_RC"
    assert_contains "pasted figure: named as a picture that is not an icon" "$IG_OUT" "아이콘이 아닌 그림"
else
    skip "aws-infographic example deck build" "node with pptxgenjs, python-pptx or lxml not reachable; run my-plugins:setup install"
fi

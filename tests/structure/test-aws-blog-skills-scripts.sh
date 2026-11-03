#!/bin/bash
# Behavior of the scripts aws-blog-skills ships (sourced by tests/run-all.sh; filter: scripts).
# Everything runs on fixtures in $TEST_TMP; nothing is written under skills/.

SCR=skills/aws-blog-skills/scripts
SCR_SLUG=2026-01-01-fixture
SCR_W="$TEST_TMP/$SCR_SLUG"
mkdir -p "$SCR_W"/{drafts,images,out}
ln -sfn ../images "$SCR_W/drafts/images"

# A minimal draft that satisfies references/structure.md and style.md
scr_write_draft() {
    cat > "$1" <<'EOF'
---
title: "샘플 원고 – Amazon VPC 구성 점검"
date: 2026-01-01
author: "Woohyung Choi"
status: draft
---

# 샘플 원고 – Amazon VPC 구성 점검

by WOO HYUNG CHOI on 1 1월 2026 in [Best Practices](https://aws.amazon.com/ko/blogs/tech/category/post-types/best-practices/), [Intermediate (200)](https://aws.amazon.com/ko/blogs/tech/category/learning-levels/intermediate-200/)

이 원고는 하네스 테스트용 샘플입니다. 이 글은 VPC를 운영하는 엔지니어를 대상으로 하며, 서브넷의 기본 개념을 알고 있다면 무리 없이 읽을 수 있습니다.

## 1. 구성 개요

샘플 구성은 서브넷 두 개로 시작합니다.

| 항목 | 값 |
|---|---|
| 서브넷 수 | 2개 |

*표 1. 샘플 구성 항목(단위: 개)*

![서울 리전 VPC가 Direct Connect Gateway를 거쳐 온프레미스 라우터로 연결되는 기존 구성](images/fixture-fig01-arch.png)

*그림 1. 샘플 아키텍처*

## 2. 마치며

이 글의 표가 여러분의 VPC 검토에 실질적인 참고가 되기를 바랍니다.

## 참고 자료

- [What is Amazon VPC? – User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)

## 저자 소개

**최우형 (Woohyung Choi)** 님은 AWS Korea의 Principal Solutions Architect로, 국내 주요 엔터프라이즈 및 디지털 기업의 클라우드 전환과 아키텍처 현대화를 지원하고 있습니다.
EOF
}
SCR_MD="$SCR_W/drafts/$SCR_SLUG.md"
scr_write_draft "$SCR_MD"
printf 'png' > "$SCR_W/images/fixture-fig01-arch.png"
printf '<svg xmlns="http://www.w3.org/2000/svg"/>' > "$SCR_W/images/fixture-fig01-arch.svg"

# --- lint_prose.py ---
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "lint_prose: clean draft exits 0" "0" "$SCR_RC"
assert_contains "lint_prose: reports zero hard findings" "$SCR_OUT" "hard_findings=0"
sed 's/샘플 구성은 서브넷 두 개로 시작합니다./샘플 구성은 비용 레버를 다룹니다./' "$SCR_MD" > "$TEST_TMP/lint-bad.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-bad.md" 2>&1); SCR_RC=$?
assert_eq "lint_prose: banned word exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: names the banned word" "$SCR_OUT" "[HARD] '레버'"
SCR_LONG=$(printf '가%.0s' $(seq 1 150))
sed "s/샘플 구성은 서브넷 두 개로 시작합니다./${SCR_LONG}입니다./" "$SCR_MD" > "$TEST_TMP/lint-long.md"
SCR_OUT=$(python3 -I "$SCR/lint_prose.py" "$TEST_TMP/lint-long.md" 2>&1); SCR_RC=$?
assert_eq "lint_prose: sentence over 140 chars exits 1" "1" "$SCR_RC"
assert_contains "lint_prose: reports the long sentence" "$SCR_OUT" "140자 초과 문장 1개"

# --- check_structure.py ---
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_MD" 2>&1); SCR_RC=$?
assert_eq "check_structure: valid draft exits 0 (drafts/images link resolves)" "0" "$SCR_RC"
assert_contains "check_structure: reports OK" "$SCR_OUT" "OK: structure checks passed"
awk '/^\*표 1\./{next} /^\| 항목 \| 값 \|/{print "*표 1. 샘플 구성 항목(단위: 개)*"; print ""} {print}' "$SCR_MD" > "$SCR_W/drafts/caption-above.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/caption-above.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: caption above table exits 1" "1" "$SCR_RC"
assert_contains "check_structure: names the misplaced caption" "$SCR_OUT" "표 1 캡션이 표 바로 아래에 없음"
sed 's#images/fixture-fig01-arch.png#images/missing.png#' "$SCR_MD" > "$SCR_W/drafts/missing-img.md"
SCR_OUT=$(python3 -I "$SCR/check_structure.py" "$SCR_W/drafts/missing-img.md" 2>&1); SCR_RC=$?
assert_eq "check_structure: missing image exits 1" "1" "$SCR_RC"
assert_contains "check_structure: names the missing image" "$SCR_OUT" "이미지 파일 없음: images/missing.png"
rm -f "$SCR_W/drafts/caption-above.md" "$SCR_W/drafts/missing-img.md"

# --- package_blog.sh ---
echo keep > "$SCR_W/out/keep.txt"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: valid draft exits 0" "0" "$SCR_RC"
assert_file_exists "package_blog: zip in <workdir>/out by default" "$SCR_W/out/$SCR_SLUG.zip"
SCR_ZIP=$(unzip -Z1 "$SCR_W/out/$SCR_SLUG.zip" 2>/dev/null | tr '\n' ' ')
for entry in "$SCR_SLUG/$SCR_SLUG.md" "$SCR_SLUG/images/fixture-fig01-arch.png" "$SCR_SLUG/images/fixture-fig01-arch.svg"; do
    assert_contains "package_blog: zip has $entry" "$SCR_ZIP" "$entry"
done
assert_contains "package_blog: prints deliverables" "$SCR_OUT" "deliverables:"
assert_contains "package_blog: deliverables are absolute paths" "$SCR_OUT" "  $SCR_W/out/$SCR_SLUG.zip"
assert_file_exists "package_blog: leaves other files in out/ alone" "$SCR_W/out/keep.txt"
rm -f "$SCR_W/drafts/images"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" "$TEST_TMP/custom-out" 2>&1); SCR_RC=$?
assert_eq "package_blog: works without the drafts/images link (checks the assembled copy)" "0" "$SCR_RC"
assert_file_exists "package_blog: third argument sets the out dir" "$TEST_TMP/custom-out/$SCR_SLUG.zip"
sed -i 's#images/fixture-fig01-arch.png#images/missing.png#' "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" "$SCR_W" "$SCR_SLUG" 2>&1); SCR_RC=$?
assert_eq "package_blog: broken image exits 1" "1" "$SCR_RC"
[ ! -e "$SCR_W/out/$SCR_SLUG.zip" ] && pass "package_blog: no zip after a failed check" \
    || fail "package_blog: no zip after a failed check" "stale zip left in out/"
scr_write_draft "$SCR_MD"
SCR_OUT=$(bash "$SCR/package_blog.sh" 2>&1); SCR_RC=$?
assert_eq "package_blog: missing arguments exits 2" "2" "$SCR_RC"
assert_contains "package_blog: prints usage" "$SCR_OUT" "Usage: package_blog.sh <workdir> <slug>"
assert_not_contains "package_blog: no claude.ai output path" "$(cat "$SCR/package_blog.sh")" "/mnt/user-data"

# --- check_urls.py against a local server (no external network) ---
cat > "$TEST_TMP/url-server.py" <<'EOF'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/moved":
            self.send_response(302); self.send_header("Location", "/landing/"); self.end_headers(); return
        if self.path == "/ok":  # like real servers: add the trailing slash
            self.send_response(301); self.send_header("Location", "/ok/"); self.end_headers(); return
        code = 200 if self.path in ("/ok/", "/landing/") else 404
        self.send_response(code); self.send_header("Content-Type", "text/html"); self.end_headers()
        self.wfile.write(b"<title>t</title>")
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1], "w").write(str(srv.server_address[1]))
srv.serve_forever()
EOF
python3 -I "$TEST_TMP/url-server.py" "$TEST_TMP/url-port" &
SCR_SRV=$!
for _ in $(seq 1 50); do [ -s "$TEST_TMP/url-port" ] && break; sleep 0.1; done
SCR_PORT=$(cat "$TEST_TMP/url-port" 2>/dev/null)
if [ -n "$SCR_PORT" ]; then
    SCR_BASE="http://127.0.0.1:$SCR_PORT"
    cat > "$TEST_TMP/urls.md" <<EOF
- [ok]($SCR_BASE/ok/)
- [moved]($SCR_BASE/moved)
- [missing]($SCR_BASE/missing)
- example https://api.example.com/v1 and template \`https://aws.amazon.com/ko/blogs/tech/category/<path>/\`
EOF
    SCR_OUT=$(no_proxy=127.0.0.1 NO_PROXY=127.0.0.1 python3 -I "$SCR/check_urls.py" "$TEST_TMP/urls.md" 2>&1); SCR_RC=$?
    assert_eq "check_urls: failures exit 1" "1" "$SCR_RC"
    assert_contains "check_urls: 200 is OK" "$SCR_OUT" "[OK] $SCR_BASE/ok/"
    assert_contains "check_urls: redirect to another page is REDIRECT" "$SCR_OUT" "[REDIRECT] $SCR_BASE/moved  -> $SCR_BASE/landing/"
    assert_contains "check_urls: 404 is FAIL" "$SCR_OUT" "[FAIL] $SCR_BASE/missing  -> HTTP 404"
    assert_contains "check_urls: example host and template are skipped" "$SCR_OUT" "checked=3 skipped=2 failed=2"
    printf -- '- [ok](%s/ok)\n' "$SCR_BASE" > "$TEST_TMP/urls-ok.md"
    SCR_OUT=$(no_proxy=127.0.0.1 NO_PROXY=127.0.0.1 python3 -I "$SCR/check_urls.py" "$TEST_TMP/urls-ok.md" 2>&1); SCR_RC=$?
    assert_eq "check_urls: trailing-slash difference alone is OK (exit 0)" "0" "$SCR_RC"
else
    skip "check_urls: local server tests" "test HTTP server did not start"
fi
kill "$SCR_SRV" 2>/dev/null; wait "$SCR_SRV" 2>/dev/null

# --- render_diagrams.py refuses to guess an output folder ---
SCR_OUT=$(python3 -I "$SCR/render_diagrams.py" 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && pass "render_diagrams: no images dir exits non-zero" \
    || fail "render_diagrams: no images dir exits non-zero" "exit 0"
if printf '%s' "$SCR_OUT" | grep -qE 'usage: render_diagrams.py|playwright is not installed'; then
    pass "render_diagrams: explains usage or how to get Playwright"
else
    fail "render_diagrams: explains usage or how to get Playwright" "$SCR_OUT"
fi
assert_not_contains "render_diagrams: no default inside the skill folder" "$(cat "$SCR/render_diagrams.py")" \
    'os.path.dirname(__file__), "..", "images"'

# --- diagram_lib.py and the example generator, set up the way SKILL.md step 4 does it ---
# The cp and pointer lines of the step 4 block run as written, with CLAUDE_SKILL_DIR and W set and HOME pointed
# at an empty folder, so the copy can only find the assets through the .aws-diagram-assets pointer.
SCR_HOME="$TEST_TMP/scr-home"
SCR_DW="$TEST_TMP/scr-work"
mkdir -p "$SCR_HOME" "$SCR_DW"/{diagrams,images}
SCR_STEPS=$(awk '/^## 4\. /{s=1} s && /^```bash/{b=1; next} b && /^```/{exit} b' "$SCR/../SKILL.md" \
    | grep -E '^(cp|python3) "\$\{CLAUDE_SKILL_DIR\}/scripts/(diagram_lib|example_diagrams)\.py"' || true)
assert_eq "SKILL.md step 4: three setup lines (copy lib, write pointer, copy example)" "3" \
    "$(printf '%s\n' "$SCR_STEPS" | grep -c . || true)"
SCR_OUT=$(cd "$SCR_DW" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" CLAUDE_SKILL_DIR="$PROJECT_ROOT/skills/aws-blog-skills" \
    W="$SCR_DW" bash -c "$SCR_STEPS" 2>&1); SCR_RC=$?
assert_eq "SKILL.md step 4 setup lines run (exit 0)" "0" "$SCR_RC"
for scr_f in diagram_lib.py .aws-diagram-assets diagrams.py; do
    assert_file_exists "step 4 setup: $scr_f in the work folder" "$SCR_DW/diagrams/$scr_f"
done
SCR_ASSETS=$(cat "$SCR_DW/diagrams/.aws-diagram-assets" 2>/dev/null)
[ -d "$SCR_ASSETS/aws-icons" ] && pass "step 4 setup: pointer names an assets folder with aws-icons ($SCR_ASSETS)" \
    || fail "step 4 setup: pointer names an assets folder with aws-icons" "'$SCR_ASSETS'"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" BLOG_IMAGES="$SCR_DW/images" python3 diagrams.py 2>&1); SCR_RC=$?
assert_eq "example generator: exits 0 in the work folder" "0" "$SCR_RC"
assert_eq "example generator: 4 SVG figures" "4" "$(find "$SCR_DW/images" -name '*.svg' | wc -l | tr -d ' ')"
assert_eq "example generator: 4 HTML render pages" "4" "$(find "$SCR_DW/images" -name '*.html' | wc -l | tr -d ' ')"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" python3 -c 'from diagram_lib import Canvas
c = Canvas("t", "t", "t")
c.node(40, 40, 200, 96, "A")
c.node(120, 80, 200, 96, "B")' 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && printf '%s' "$SCR_OUT" | grep -qF "node overlap" \
    && pass "diagram_lib: overlapping nodes fail the geometry assert" \
    || fail "diagram_lib: overlapping nodes fail the geometry assert" "rc=$SCR_RC"
SCR_OUT=$(cd "$SCR_DW/diagrams" && env -u AWS_DIAGRAM_ASSETS HOME="$SCR_HOME" python3 -c 'from diagram_lib import Canvas
Canvas("t", "t", "t").node(42, 40, 200, 96, "A")' 2>&1); SCR_RC=$?
[ "$SCR_RC" -ne 0 ] && printf '%s' "$SCR_OUT" | grep -qF "not on 4px grid" \
    && pass "diagram_lib: off-grid coordinates fail the 4px assert" \
    || fail "diagram_lib: off-grid coordinates fail the 4px assert" "rc=$SCR_RC"
rm -rf "$SCR_DW/diagrams/__pycache__"

# --- None of the above wrote into the shipped skill folder ---
assert_eq "scripts left no generated files in skills/ (caches, images, out, zips)" "" \
    "$(find skills \( -name __pycache__ -o -name '*.pyc' -o -name '*.zip' -o -type d -name images -o -type d -name out \) -print | tr '\n' ' ')"

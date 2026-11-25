#!/usr/bin/env bash
# Usage: package_blog.sh [--no-gate] <workdir> <slug> [outdir]
# Expects <workdir>/drafts/<slug>.md, <workdir>/images/ (png, svg, jpg, jpeg, gif, webp) and
# <workdir>/gate-report.md (the pre-check report). <slug> is a file name, not a path.
# Assembles <outdir>/<slug>/ (md + images/), runs the structure check and prose lint on that assembled copy
# (so image paths resolve exactly as in the delivered bundle), checks the gate report against that copy and
# copies it in, converts the draft to wordpress.md (HTML for the WordPress code editor; nothing is uploaded),
# zips the folder to <outdir>/<slug>.zip, then prints the absolute paths to report and the score table of the
# pre-check, which the last response of the session shows without being asked. <outdir> defaults to
# <workdir>/out. When a check or the conversion fails, when the gate report is missing, was written for another
# state of the draft or says 반려, no zip is written and the assembled folder is removed.
# --no-gate packages without a gate report (only when the user asked to leave the pre-check out).
set -euo pipefail
GATE=1
if [ "${1:-}" = "--no-gate" ]; then GATE=0; shift; fi
[ $# -ge 2 ] || { sed -n '2,12p' "$0"; exit 2; }
S="$2"
# The slug names the folder this script deletes and writes: a path in it would reach outside the out folder
[[ "$S" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || { echo "slug is not a plain file name (letters, digits, '.', '_', '-'): $S"; exit 2; }
W="$(cd "$1" && pwd)"; OUT="${3:-$W/out}"
D="$(cd "$(dirname "$0")" && pwd)"
MD="$W/drafts/$S.md"
[ -f "$MD" ] || { echo "draft not found: $MD"; exit 1; }
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
rm -rf "${OUT:?}/$S" "$OUT/$S.zip"; mkdir -p "$OUT/$S/images"
stop() { echo "$1"; rm -rf "${OUT:?}/$S"; exit 1; }
cp "$MD" "$OUT/$S/"
shopt -s nullglob
imgs=("$W"/images/*.png "$W"/images/*.svg "$W"/images/*.jpg "$W"/images/*.jpeg "$W"/images/*.gif "$W"/images/*.webp)
if [ ${#imgs[@]} -gt 0 ]; then cp "${imgs[@]}" "$OUT/$S/images/"; fi
python3 "$D/check_structure.py" "$OUT/$S/$S.md" || stop "structure check failed"
python3 "$D/lint_prose.py" "$OUT/$S/$S.md" || stop "prose lint found hard findings"
if [ "$GATE" = 1 ]; then
    [ -f "$W/gate-report.md" ] || stop "gate report not found: $W/gate-report.md (run the pre-check first: references/precheck.md)"
    GATE_OUT="$(python3 "$D/check_gate.py" "$W/gate-report.md" --draft "$OUT/$S/$S.md")" || { echo "$GATE_OUT"; stop "gate report check failed"; }
    echo "$GATE_OUT"
    cp "$W/gate-report.md" "$OUT/$S/"
fi
python3 "$D/md_to_wordpress.py" "$OUT/$S/$S.md" --out "$OUT/$S/wordpress.md" || stop "WordPress conversion failed"
( cd "$OUT" && zip -qr "$S.zip" "$S" )
echo "deliverables:"
echo "  $OUT/$S/$S.md"
echo "  $OUT/$S/wordpress.md"
if [ "$GATE" = 1 ]; then echo "  $OUT/$S/gate-report.md"; fi
for f in "$OUT/$S/images/"*; do echo "  $f"; done
echo "  $OUT/$S.zip"
if [ "$GATE" = 1 ]; then
    echo "scores (show this table in the last response):"
    printf '%s\n' "$GATE_OUT" | grep -E '^  (OK:|\|)'
else
    echo "scores: none (--no-gate: the pre-check was left out)"
fi

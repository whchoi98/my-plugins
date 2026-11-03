#!/usr/bin/env bash
# Usage: package_blog.sh <workdir> <slug> [outdir]
# Expects <workdir>/drafts/<slug>.md and <workdir>/images/*.png|*.svg.
# Assembles <outdir>/<slug>/ (md + images/), runs the structure check and prose lint on that assembled copy
# (so image paths resolve exactly as in the delivered bundle), zips it to <outdir>/<slug>.zip,
# then prints the absolute paths to report. <outdir> defaults to <workdir>/out.
set -euo pipefail
[ $# -ge 2 ] || { sed -n '2,6p' "$0"; exit 2; }
W="$(cd "$1" && pwd)"; S="$2"; OUT="${3:-$W/out}"
D="$(cd "$(dirname "$0")" && pwd)"
MD="$W/drafts/$S.md"
[ -f "$MD" ] || { echo "draft not found: $MD"; exit 1; }
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
rm -rf "${OUT:?}/$S" "$OUT/$S.zip"; mkdir -p "$OUT/$S/images"
cp "$MD" "$OUT/$S/"
shopt -s nullglob
imgs=("$W"/images/*.png "$W"/images/*.svg)
if [ ${#imgs[@]} -gt 0 ]; then cp "${imgs[@]}" "$OUT/$S/images/"; fi
python3 "$D/check_structure.py" "$OUT/$S/$S.md" || { echo "structure check failed"; exit 1; }
python3 "$D/lint_prose.py" "$OUT/$S/$S.md" || { echo "prose lint found hard findings"; exit 1; }
( cd "$OUT" && zip -qr "$S.zip" "$S" )
echo "deliverables:"
echo "  $OUT/$S/$S.md"
for f in "$OUT/$S/images/"*.png "$OUT/$S/images/"*.svg; do echo "  $f"; done
echo "  $OUT/$S.zip"

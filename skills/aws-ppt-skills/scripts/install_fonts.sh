#!/usr/bin/env bash
# Install the bundled fonts so LibreOffice QA renders slides with the real typefaces.
#   NanumSquareOTF_acB.otf  -> body font. The templates name it "NanumSquareOTF Bold", so a
#                              fontconfig alias maps that name (and the Korean name) to this file.
#   D2Coding-*.ttf          -> code font (terminal boxes only).
# Safe to run repeatedly. Usage: bash scripts/install_fonts.sh
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONT_DIR="$HOME/.fonts"
CONF_DIR="$HOME/.config/fontconfig/conf.d"
mkdir -p "$FONT_DIR" "$CONF_DIR"
cp "$SKILL_DIR"/assets/fonts/*.otf "$SKILL_DIR"/assets/fonts/*.ttf "$FONT_DIR"/

ALIASES='<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias binding="same"><family>NanumSquareOTF Bold</family><prefer><family>NanumSquareOTF_ac</family></prefer></alias>
  <alias binding="same"><family>나눔스퀘어OTF Bold</family><prefer><family>NanumSquareOTF_ac</family></prefer></alias>
  <alias binding="same"><family>NanumSquareOTF_ac Bold</family><prefer><family>NanumSquareOTF_ac</family></prefer></alias>
</fontconfig>'
printf '%s\n' "$ALIASES" > "$CONF_DIR/60-aws-ppt-fonts.conf"
fc-cache -f >/dev/null 2>&1 || true

# Some images do not read ~/.config/fontconfig/conf.d; fall back to the user fonts.conf.
if ! fc-match "NanumSquareOTF Bold" | grep -q "NanumSquareOTF_ac"; then
  if [ ! -f "$HOME/.config/fontconfig/fonts.conf" ]; then
    printf '%s\n' "$ALIASES" > "$HOME/.config/fontconfig/fonts.conf"
    fc-cache -f >/dev/null 2>&1 || true
  fi
fi

for n in "NanumSquareOTF Bold" "D2Coding"; do
  printf '%-20s -> %s\n' "$n" "$(fc-match "$n")"
done

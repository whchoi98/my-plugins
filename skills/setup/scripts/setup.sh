#!/usr/bin/env bash
# my-plugins 의존 프로그램 점검과 설치.
#
#   bash setup.sh            # 점검만(기본값). 아무것도 바꾸지 않는다
#   bash setup.sh install    # sudo 없이 되는 것만 사용자 영역에 설치
#   bash setup.sh install --sudo
#                            # 시스템 패키지도 설치. sudo -n(비대화식)으로만 실행하고,
#                            # 암호가 필요하면 실행할 명령만 출력한다
#
# 사용자 영역 설치 위치: ~/.local/bin(uv, soffice 링크), ~/.local/opt/libreoffice,
# ~/.local/share/fonts(Linux) 또는 ~/Library/Fonts(macOS), ~/.cache/ms-playwright, pip --user, npm -g.
# 마지막 줄의 "missing: N"이 0이면 모든 skill을 쓸 수 있다.
set -uo pipefail

MODE="${1:-check}"
USE_SUDO=0
for a in "$@"; do [ "$a" = "--sudo" ] && USE_SUDO=1; done
case "$MODE" in check|install) ;; *) echo "usage: setup.sh [check|install [--sudo]]" >&2; exit 2 ;; esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="$(cd "$HERE/../.." && pwd)"
EMBER_TTF="$SKILLS/aws-diagram-design/assets/fonts/ttf"
DECK_FONTS_SH="$SKILLS/aws-ppt-skills/scripts/install_fonts.sh"

export PATH="$HOME/.local/bin:$PATH"
# aws-blog-skills의 SKILL.md, references/diagrams.md, scripts/render_diagrams.py와 같은 버전으로 고정한다.
# 고정하지 않으면 uv가 새 Playwright를 고를 때마다 설치된 브라우저 revision과 어긋난다.
PW_SPEC="playwright==1.64.1"
OS="$(uname -s)"; ARCH="$(uname -m)"
if [ "$OS" = "Darwin" ]; then FONT_HOME="$HOME/Library/Fonts"; else FONT_HOME="$HOME/.local/share/fonts"; fi
PKG=none
if [ "$OS" = "Darwin" ] && command -v brew >/dev/null; then PKG=brew
elif command -v dnf >/dev/null; then PKG=dnf
elif command -v apt-get >/dev/null; then PKG=apt
fi

MISSING=0
SYS_PKGS=()      # sudo가 필요한 시스템 패키지
ok()   { printf '  [ok]   %-26s %s\n' "$1" "${2:-}"; }
miss() { printf '  [miss] %-26s %s\n' "$1" "${2:-}"; MISSING=$((MISSING + 1)); }
info() { printf '  [info] %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
# grep -q가 먼저 끝나면 pipefail 아래에서 fc-list의 SIGPIPE가 실패로 잡히므로 -q를 쓰지 않는다
font_has() { fc-list : family 2>/dev/null | grep -i -- "$1" >/dev/null; }
nanum_ok() { fc-match "NanumSquareOTF Bold" 2>/dev/null | grep "NanumSquareOTF_ac" >/dev/null; }

# --------------------------------------------------------------------------- 점검 항목

check_base() {
  for c in python3 zip node npm; do
    if have "$c"; then ok "$c" "$(command -v "$c")"; else miss "$c" "직접 설치 필요(Node.js는 nodejs.org 또는 nvm)"; fi
  done
  if ! grep -qs '.local/bin' "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zshrc" 2>/dev/null; then
    info "~/.local/bin이 셸 설정 파일의 PATH에 없습니다. uv, soffice를 새 셸에서 찾으려면 추가하세요"
  fi
}

chromium_runs() {
  have uv || return 1
  uv run --no-project --quiet --with "$PW_SPEC" python - <<'PY' >/dev/null 2>&1
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); b.close()
PY
}

check_render() {
  if have uv; then ok uv "$(uv --version 2>/dev/null)"; else miss uv "다이어그램 PNG 렌더(Playwright 실행)"; fi
  if chromium_runs; then ok "playwright chromium" "headless 실행 확인"
  else
    miss "playwright chromium" "브라우저가 없거나 시스템 라이브러리가 빠짐"
    local shell_bin; shell_bin=$(ls -d "$HOME"/.cache/ms-playwright/chromium_headless_shell-*/chrome-*/*headless_shell 2>/dev/null | tail -1)
    if [ -n "$shell_bin" ] && have ldd; then
      local libs; libs=$(ldd "$shell_bin" 2>/dev/null | awk '/not found/{print $1}' | tr '\n' ' ')
      [ -n "$libs" ] && info "빠진 라이브러리: $libs"
    fi
  fi
}

check_fonts() {
  if ! have fc-list; then miss fontconfig "fc-list 없음"; return; fi
  if font_has "Amazon Ember"; then ok "Amazon Ember"; else miss "Amazon Ember" "다이어그램 영문 폰트(플러그인에 포함)"; fi
  if font_has "Noto Sans CJK KR"; then ok "Noto Sans CJK KR"; else miss "Noto Sans CJK KR" "다이어그램 한글 폰트"; fi
  if nanum_ok; then ok "NanumSquareOTF Bold"; else miss "NanumSquareOTF Bold" "덱 본문 폰트(플러그인에 포함)"; fi
  if font_has "D2Coding"; then ok "D2Coding"; else miss "D2Coding" "덱 코드 폰트(플러그인에 포함)"; fi
}

check_deck() {
  if have npm && NODE_PATH="$(npm root -g 2>/dev/null)" node -e 'require("pptxgenjs")' >/dev/null 2>&1; then
    ok pptxgenjs "$(npm ls -g pptxgenjs 2>/dev/null | grep -o 'pptxgenjs@[0-9.]*' | head -1)"
  else miss pptxgenjs "덱 생성(npm -g)"; fi
  local mod
  for mod in pptx:python-pptx lxml:lxml PIL:Pillow cairosvg:cairosvg; do
    if python3 -c "import ${mod%%:*}" >/dev/null 2>&1; then ok "${mod#*:}"; else miss "${mod#*:}" "pip --user"; fi
  done
  if have soffice; then ok soffice "$(soffice --version 2>/dev/null | head -1 | awk '{print $1, $2}')"; else miss soffice "LibreOffice, 렌더 QA"; fi
  for c in pdftoppm pdftotext rsvg-convert; do
    if have "$c"; then ok "$c"; else miss "$c" "렌더 QA, SVG 미리보기"; fi
  done
}

run_checks() {
  echo "== 기본 도구"; check_base
  echo "== 다이어그램 렌더 (aws-blog-skills, aws-diagram-design export)"; check_render
  echo "== 폰트"; check_fonts
  echo "== 덱 (aws-ppt-skills, consulting-ppt-white-ppt, pptx-template-fill)"; check_deck
}

# --------------------------------------------------------------------------- 설치

install_uv() {
  have uv && return
  echo "-> uv 설치(~/.local/bin)"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
}

install_chromium() {
  have uv || return
  echo "-> Playwright Chromium 내려받기(~/.cache/ms-playwright)"
  uv run --no-project --quiet --with "$PW_SPEC" python -m playwright install chromium 2>&1 \
    | grep -vE '^\s+at |BEWARE' | grep -v '^$' | head -3 || true
  chromium_runs && return
  case "$PKG" in
    dnf) SYS_PKGS+=(atk at-spi2-atk at-spi2-core libxkbcommon alsa-lib mesa-libgbm libXcomposite libXdamage libXfixes libXrandr) ;;
    apt) SYS_PKGS+=(__playwright_install_deps__) ;;
  esac
}

install_fonts() {
  mkdir -p "$FONT_HOME"
  if ! font_has "Amazon Ember" && [ -d "$EMBER_TTF" ]; then
    echo "-> Amazon Ember 복사($FONT_HOME/ember)"
    mkdir -p "$FONT_HOME/ember" && cp "$EMBER_TTF"/*.ttf "$FONT_HOME/ember/"
  fi
  if ! font_has "Noto Sans CJK KR"; then
    echo "-> Noto Sans CJK KR 내려받기($FONT_HOME/noto-cjk)"
    mkdir -p "$FONT_HOME/noto-cjk"
    local w
    for w in Regular Medium Bold; do
      curl -fsSL -o "$FONT_HOME/noto-cjk/NotoSansCJKkr-$w.otf" \
        "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-$w.otf" || echo "   실패: $w"
    done
  fi
  have fc-cache && fc-cache -f >/dev/null 2>&1
  if ! nanum_ok || ! font_has D2Coding; then
    echo "-> NanumSquareOTF, D2Coding 설치(aws-ppt-skills/scripts/install_fonts.sh)"
    bash "$DECK_FONTS_SH" >/dev/null
  fi
}

install_deck_user() {
  if have npm && ! NODE_PATH="$(npm root -g)" node -e 'require("pptxgenjs")' >/dev/null 2>&1; then
    echo "-> pptxgenjs 설치(npm -g)"
    npm install -g pptxgenjs >/dev/null 2>&1 || echo "   실패: npm 전역 폴더에 쓸 수 없으면 nvm 등 사용자 Node를 쓰세요"
  fi
  local need=() mod
  for mod in pptx:python-pptx lxml:lxml PIL:Pillow cairosvg:cairosvg; do
    python3 -c "import ${mod%%:*}" >/dev/null 2>&1 || need+=("${mod#*:}")
  done
  if [ ${#need[@]} -gt 0 ]; then
    echo "-> pip --user ${need[*]}"
    python3 -m pip install --user -q "${need[@]}" 2>&1 | tail -2
  fi
}

# Amazon Linux 2023처럼 패키지 저장소에 LibreOffice가 없는 dnf 시스템: 공식 RPM 묶음을 홈에 푼다
install_libreoffice_tarball() {
  local lo_arch
  case "$ARCH" in aarch64|arm64) lo_arch=aarch64 ;; x86_64) lo_arch=x86-64 ;; *) echo "   지원하지 않는 아키텍처: $ARCH"; return ;; esac
  have rpm2cpio && have cpio || { echo "   rpm2cpio, cpio가 필요합니다"; return; }
  local base=https://download.documentfoundation.org/libreoffice/stable ver f tmp
  ver=$(curl -fsSL "$base/" | grep -oE 'href="[0-9.]+/"' | grep -oE '[0-9]+(\.[0-9]+)+' | sort -V | tail -1)
  [ -n "$ver" ] || { echo "   최신 버전을 찾지 못했습니다"; return; }
  f="LibreOffice_${ver}_Linux_${lo_arch}_rpm.tar.gz"
  tmp=$(mktemp -d)
  echo "-> LibreOffice $ver 내려받기와 체크섬 확인"
  if curl -fsSL -o "$tmp/$f" "$base/$ver/rpm/$lo_arch/$f" && curl -fsSL -o "$tmp/$f.sha256" "$base/$ver/rpm/$lo_arch/$f.sha256" \
     && (cd "$tmp" && sha256sum -c "$f.sha256" >/dev/null); then
    local dest="$HOME/.local/opt/libreoffice" r prog
    rm -rf "$dest"; mkdir -p "$dest" "$HOME/.local/bin"
    tar xzf "$tmp/$f" -C "$tmp"
    for r in "$tmp"/LibreOffice_*_rpm/RPMS/*.rpm; do (cd "$dest" && rpm2cpio "$r" | cpio -idm --quiet); done
    prog=$(ls -d "$dest"/opt/libreoffice*/program | head -1)
    ln -sf "$prog/soffice" "$HOME/.local/bin/soffice"
    echo "   $prog -> ~/.local/bin/soffice"
    SYS_PKGS+=(libXinerama)      # oosplash가 링크한다
  else
    echo "   내려받기 또는 체크섬 실패"
  fi
  rm -rf "$tmp"
}

install_deck_system() {
  case "$PKG" in
    brew)
      have pdftoppm || brew install poppler
      have rsvg-convert || brew install librsvg
      have soffice || brew install --cask libreoffice ;;
    dnf)
      have pdftoppm && have pdftotext || SYS_PKGS+=(poppler-utils)
      have rsvg-convert || SYS_PKGS+=(librsvg2-tools)
      if ! have soffice; then
        if dnf -q list --available libreoffice-impress >/dev/null 2>&1; then SYS_PKGS+=(libreoffice-impress)
        else install_libreoffice_tarball; fi
      fi
      if have soffice && ! soffice --version >/dev/null 2>&1; then SYS_PKGS+=(libXinerama); fi ;;
    apt)
      have pdftoppm && have pdftotext || SYS_PKGS+=(poppler-utils)
      have rsvg-convert || SYS_PKGS+=(librsvg2-bin)
      have soffice || SYS_PKGS+=(libreoffice-impress) ;;
    *) echo "   패키지 관리자를 찾지 못했습니다. LibreOffice, Poppler, rsvg-convert를 직접 설치하세요" ;;
  esac
}

install_system_pkgs() {
  [ ${#SYS_PKGS[@]} -eq 0 ] && return
  local pkgs=() p cmd=() deps=0
  for p in "${SYS_PKGS[@]}"; do
    if [ "$p" = "__playwright_install_deps__" ]; then deps=1; else pkgs+=("$p"); fi
  done
  # 중복 제거
  if [ ${#pkgs[@]} -gt 0 ]; then mapfile -t pkgs < <(printf '%s\n' "${pkgs[@]}" | sort -u); fi
  echo "== sudo가 필요한 시스템 패키지"
  [ ${#pkgs[@]} -gt 0 ] && case "$PKG" in
    dnf) cmd=(sudo dnf install -y "${pkgs[@]}") ;;
    apt) cmd=(sudo apt-get install -y "${pkgs[@]}") ;;
  esac
  local deps_cmd=(sudo env "PATH=$PATH" uv run --no-project --with "$PW_SPEC" python -m playwright install-deps chromium)
  if [ "$USE_SUDO" -eq 1 ] && sudo -n true 2>/dev/null; then
    [ ${#cmd[@]} -gt 0 ] && { echo "-> ${cmd[*]}"; sudo -n "${cmd[@]:1}" 2>&1 | tail -1; }
    [ "$deps" -eq 1 ] && { echo "-> playwright install-deps chromium"; sudo -n "${deps_cmd[@]:1}" 2>&1 | tail -1; }
  else
    [ "$USE_SUDO" -eq 1 ] && echo "  sudo에 암호가 필요합니다. 아래 명령을 직접 실행하세요:" \
                          || echo "  --sudo 없이 실행해서 건너뛰었습니다. 직접 실행하거나 install --sudo로 다시 실행하세요:"
    [ ${#cmd[@]} -gt 0 ] && echo "    ${cmd[*]}"
    [ "$deps" -eq 1 ] && echo "    ${deps_cmd[*]}"
  fi
}

# --------------------------------------------------------------------------- 실행

echo "my-plugins setup: $MODE (OS=$OS, arch=$ARCH, pkg=$PKG)"
if [ "$MODE" = "install" ]; then
  echo "== 설치"
  install_uv
  install_chromium
  install_fonts
  install_deck_user
  install_deck_system
  install_system_pkgs
  echo
fi
run_checks
echo "missing: $MISSING"
[ "$OS" = "Linux" ] && ! grep -qiE 'ubuntu|debian' /etc/os-release 2>/dev/null && \
  info "Playwright가 공식 지원하지 않는 OS에서는 렌더할 때 'BEWARE: your OS is not officially supported' 경고가 나옵니다. 결과에는 영향이 없습니다"
exit 0

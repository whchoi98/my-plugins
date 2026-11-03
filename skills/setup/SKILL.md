---
name: setup
description: "my-plugins의 skill들이 쓰는 외부 프로그램과 폰트를 점검하고 설치한다. 대상은 다이어그램 PNG 렌더(uv, Playwright Chromium과 시스템 라이브러리, Amazon Ember, Noto Sans CJK KR)와 덱 생성·렌더 QA(pptxgenjs, python-pptx, lxml, Pillow, cairosvg, LibreOffice soffice, Poppler pdftoppm/pdftotext, rsvg-convert, NanumSquareOTF, D2Coding)다. \"my-plugins 설치 점검\", \"의존성 설치\", \"setup\", \"렌더링이 안 돼\", \"soffice 없음\", \"playwright 실행 안 됨\", \"폰트가 깨져\" 같은 요청이나, aws-blog-skills, aws-diagram-design, aws-ppt-skills, consulting-ppt-white-ppt, pptx-template-fill이 도구나 폰트가 없다고 할 때 사용한다."
---

# my-plugins setup

`${CLAUDE_SKILL_DIR}`는 이 skill 폴더의 절대 경로다. 값이 치환되지 않고 그대로 보이면 skill을 불러올 때 표시된 "Base directory for this skill" 경로를 쓴다.

## 1. 점검

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"
```

아무것도 바꾸지 않고 항목마다 `[ok]` 또는 `[miss]`를 출력한다. 마지막 줄 `missing: 0`이면 끝이다. 빠진 항목은 어떤 skill에 필요한지와 함께 사용자에게 짧게 알린다.

## 2. 사용자 영역 설치

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" install
```

sudo 없이 되는 것만 설치한다. 사용자가 설치를 요청했으면 바로 실행한다.

| 항목 | 위치 |
|---|---|
| uv | `~/.local/bin` (astral.sh 설치 스크립트) |
| Playwright Chromium | `~/.cache/ms-playwright` |
| Amazon Ember | 플러그인의 `aws-diagram-design/assets/fonts/ttf`에서 `~/.local/share/fonts/ember`로 복사 (macOS는 `~/Library/Fonts`) |
| Noto Sans CJK KR | notofonts/noto-cjk의 OTF 3종을 `~/.local/share/fonts/noto-cjk`로 |
| NanumSquareOTF, D2Coding | `aws-ppt-skills/scripts/install_fonts.sh`(fontconfig 별칭 포함) |
| pptxgenjs | `npm install -g` |
| python-pptx, lxml, Pillow, cairosvg | `pip install --user` |
| LibreOffice | dnf 저장소에 없을 때(Amazon Linux 2023) 공식 RPM 묶음을 sha256 확인 후 `~/.local/opt/libreoffice`에 풀고 `~/.local/bin/soffice`로 연결 |

## 3. 시스템 패키지 (sudo)

install 단계가 끝에 "sudo가 필요한 시스템 패키지"와 명령을 출력하면, **실행 전에 사용자에게 그 명령을 보여 주고 허락을 받는다.** 허락하면:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" install --sudo
```

`sudo -n`(비대화식)으로만 실행한다. 암호가 필요하면 명령만 출력하므로, 사용자에게 프롬프트에서 `! <명령>`으로 직접 실행하라고 안내한다. 명령 앞에 공백이 있으면 `!` 명령으로 인식되지 않는다.

패키지 관리자별로 설치하는 것:
- dnf(Amazon Linux, Fedora, RHEL): Chromium용 `atk at-spi2-atk at-spi2-core libxkbcommon alsa-lib mesa-libgbm libXcomposite libXdamage libXfixes libXrandr`, `poppler-utils`, `librsvg2-tools`, 홈에 푼 LibreOffice용 `libXinerama`
- apt(Ubuntu, Debian): `playwright install-deps chromium`, `poppler-utils`, `librsvg2-bin`, `libreoffice-impress`
- brew(macOS): `poppler`, `librsvg`, `--cask libreoffice` (sudo 불필요, install 단계에서 실행)

## 4. 재점검과 보고

설치 후 1의 점검을 다시 실행하고 `missing:` 값을 보고한다. 다른 skill 작업 중에 불려 왔으면 그 작업으로 돌아간다.

## 알려진 동작

- Amazon Linux 2023처럼 Playwright가 공식 지원하지 않는 OS에서는 Ubuntu용 Chromium 빌드가 쓰이고, 렌더할 때마다 `BEWARE: your OS is not officially supported` 경고가 나온다. 결과에는 영향이 없다.
- LibreOffice를 홈에 풀었을 때 KDE, Qt, GTK, GStreamer 라이브러리가 없다고 나오는 것은 GUI 플러그인용이다. skill이 쓰는 `soffice --headless` 변환에는 필요 없다.
- 전역 npm 모듈은 `require()`가 기본으로 찾지 않는다. 덱을 만드는 node 명령 앞에는 `export NODE_PATH="$(npm root -g)"`를 둔다.
- `~/.local/bin`이 셸 설정의 PATH에 없으면 점검이 `[info]`로 알린다. 그때는 사용자에게 `~/.bashrc`에 `export PATH="$HOME/.local/bin:$PATH"`를 추가하라고 안내한다.

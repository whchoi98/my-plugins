# Runbook: Set Up User Dependencies

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Overview
`skills/setup/scripts/setup.sh` checks and installs the external tools and fonts the my-plugins skills need.
The `/my-plugins:setup` skill runs it for users; maintainers can run it directly from a clone. It is separate
from `scripts/setup.sh`, which only prepares the dev harness.

| Mode | Command | Effect |
|---|---|---|
| check (default) | `bash skills/setup/scripts/setup.sh` | Changes nothing; prints `[ok]` or `[miss]` per item and `missing: N` |
| install | `bash skills/setup/scripts/setup.sh install` | Installs everything that needs no sudo into the user's home, then checks |
| install with sudo | `bash skills/setup/scripts/setup.sh install --sudo` | Also installs system packages with `sudo -n`; prints the command when sudo needs a password |

Any other first argument prints the usage and exits 2. Otherwise the script exits 0; read `missing: N`.

## When to Use
- First use of the plugin on a machine
- A skill reports a missing tool or font: diagram PNG render fails, `soffice` not found, Playwright does not
  launch, fonts fall back to Helvetica or a substitute
- After adding a dependency to `setup.sh` (verify on a clean machine)

## Prerequisites
- Python 3, `zip`, Node.js and npm, `curl`; `rpm2cpio` and `cpio` on dnf systems without a LibreOffice package
- sudo rights only for system packages

## Procedure

### 1. Check
```bash
bash skills/setup/scripts/setup.sh
```
The groups are base tools, diagram render (uv, Playwright Chromium headless launch), fonts (Amazon Ember, Noto
Sans CJK KR, NanumSquareOTF Bold, D2Coding) and decks (pptxgenjs, python-pptx, lxml, Pillow, cairosvg,
`soffice`, `pdftoppm`, `pdftotext`, `rsvg-convert`) and reports (NanumSquareOTF Regular, docx, marked, docx-preview,
jszip). When Chromium does not launch, the check lists the shared
libraries `ldd` cannot find.

### 2. Install user-level items
```bash
bash skills/setup/scripts/setup.sh install
```
| Item | Where |
|---|---|
| uv | `~/.local/bin`, from the astral.sh installer |
| Playwright Chromium | `~/.cache/ms-playwright`, through `uv run --with` the Playwright version pinned in `PW_SPEC` |
| Amazon Ember | copied from `skills/aws-diagram-design/assets/fonts/ttf` to `~/.local/share/fonts/ember` (macOS `~/Library/Fonts/ember`) |
| Noto Sans CJK KR | Regular, Medium, Bold OTF from github.com/notofonts/noto-cjk to `~/.local/share/fonts/noto-cjk` |
| NanumSquareOTF, D2Coding | `skills/aws-ppt-skills/scripts/install_fonts.sh`: `~/.fonts` plus a fontconfig alias in `~/.config/fontconfig/conf.d/` |
| pptxgenjs | `npm install -g` |
| docx, marked, docx-preview, jszip (aws-reports) | `npm install -g` at fixed versions (`REPORT_NPM` in `setup.sh`) |
| NanumSquareOTF Regular and Bold (aws-reports) | npm `@kfonts/nanum-square-otf` 0.2.0 (OFL-1.1) through `npm pack`, `src/*.otf` copied to `~/.local/share/fonts/nanumsquare-otf` |
| python-pptx, lxml, Pillow, cairosvg | `pip install --user` |
| LibreOffice (dnf without a package) | official RPM bundle, SHA-256 checked, unpacked to `~/.local/opt/libreoffice`, linked as `~/.local/bin/soffice` |

On macOS with Homebrew, Poppler, librsvg and the LibreOffice cask are installed in this step (no sudo).

### 3. Install system packages (sudo)
The install step ends with "sudo가 필요한 시스템 패키지" and the commands it skipped. Show them to the user
and get approval, then:
```bash
bash skills/setup/scripts/setup.sh install --sudo
```
| Package manager | Packages |
|---|---|
| dnf (Amazon Linux, Fedora, RHEL) | Chromium libraries `atk at-spi2-atk at-spi2-core libxkbcommon alsa-lib mesa-libgbm libXcomposite libXdamage libXfixes libXrandr`, `poppler-utils`, `librsvg2-tools`, `libXinerama` for the unpacked LibreOffice, or `libreoffice-impress` when the repositories have it |
| apt (Ubuntu, Debian) | `playwright install-deps chromium`, `poppler-utils`, `librsvg2-bin`, `libreoffice-impress` |

If `sudo -n` needs a password, the script prints the command instead. In Claude Code, the user runs it from the
prompt as `! <command>` with no space before `!`.

### 4. Re-check
Run step 1 again and report `missing:`.

## Amazon Linux 2023
- **Chromium system libraries** — Playwright's bundled Chromium needs the dnf libraries in step 3; without them
  the headless launch fails and the check lists the missing `.so` files.
- **LibreOffice** — not in the Amazon Linux 2023 repositories. `setup.sh` reads the latest version from
  download.documentfoundation.org, downloads `LibreOffice_<ver>_Linux_<arch>_rpm.tar.gz` and its `.sha256`,
  verifies it, unpacks the RPMs with `rpm2cpio | cpio` into `~/.local/opt/libreoffice`, and queues `libXinerama`,
  which `oosplash` links. Supported architectures: aarch64 and x86_64.
- **Playwright warning** — Amazon Linux 2023 is not officially supported by Playwright, so it uses the Ubuntu
  Chromium build and prints `BEWARE: your OS is not officially supported` on every render. Output is not affected.
- **LibreOffice GUI libraries** — the unpacked LibreOffice reports missing KDE, Qt, GTK or GStreamer libraries.
  They serve GUI plugins; `soffice --headless` conversion does not need them.
- **PATH** — if `~/.local/bin` is not in a shell profile, the check prints `[info]`; add
  `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`.

## Verification
- [ ] `bash skills/setup/scripts/setup.sh` ends with `missing: 0`
- [ ] `fc-match "NanumSquareOTF Bold"` names `NanumSquareOTF_ac`
- [ ] `fc-list : file | grep NanumSquareR.otf` lists the aws-reports body font
- [ ] `soffice --headless --version` prints a version

## Rollback
Everything except system packages lives in the user's home. Remove what is no longer wanted:
```bash
rm -rf ~/.local/opt/libreoffice ~/.local/share/fonts/ember ~/.local/share/fonts/noto-cjk ~/.cache/ms-playwright
rm -rf ~/.local/share/fonts/nanumsquare-otf
rm -f ~/.local/bin/soffice ~/.config/fontconfig/conf.d/60-aws-ppt-fonts.conf
rm -f ~/.fonts/NanumSquareOTF_acB.otf ~/.fonts/D2Coding-*.ttf && fc-cache -f
npm uninstall -g pptxgenjs docx marked docx-preview jszip
python3 -m pip uninstall python-pptx lxml Pillow cairosvg
```
`install_fonts.sh` also writes `~/.config/fontconfig/fonts.conf` when it did not exist and the `conf.d` alias was
not read; remove it only if it holds nothing but these aliases. System packages are removed with the package
manager (`sudo dnf remove ...`, `sudo apt-get remove ...`).

## Notes
- A new external tool or font is added to `skills/setup/scripts/setup.sh` (check and install),
  `skills/setup/SKILL.md` and the README in both languages.
- Last verified: 2026-11-03 (check mode, Amazon Linux 2023 aarch64, `missing: 0`)

---

<a id="korean"></a>

# 한국어

## 개요
`skills/setup/scripts/setup.sh`는 my-plugins skill들이 쓰는 외부 프로그램과 폰트를 점검하고 설치합니다. 사용자에게는 `/my-plugins:setup` skill이 이 스크립트를 실행하고, 관리자는 클론에서 직접 실행할 수 있습니다. 개발 하네스만 준비하는 `scripts/setup.sh`와는 다른 스크립트입니다.

| 모드 | 명령 | 동작 |
|---|---|---|
| 점검(기본값) | `bash skills/setup/scripts/setup.sh` | 아무것도 바꾸지 않고 항목마다 `[ok]`나 `[miss]`, 마지막에 `missing: N`을 출력 |
| 설치 | `bash skills/setup/scripts/setup.sh install` | sudo 없이 되는 것을 사용자 홈에 설치한 뒤 점검 |
| sudo 설치 | `bash skills/setup/scripts/setup.sh install --sudo` | 시스템 패키지도 `sudo -n`으로 설치. sudo에 암호가 필요하면 명령만 출력 |

첫 인자가 그 밖의 값이면 사용법을 출력하고 exit 2로 끝납니다. 그 외에는 항상 exit 0이므로 `missing: N`을 읽습니다.

## 사용 시점
- 머신에서 플러그인을 처음 쓸 때
- skill이 도구나 폰트가 없다고 할 때: 다이어그램 PNG 렌더 실패, `soffice` 없음, Playwright 실행 실패, 폰트가 Helvetica나 대체 폰트로 보임
- `setup.sh`에 의존 프로그램을 추가한 뒤(깨끗한 머신에서 확인)

## 사전 요구 사항
- Python 3, `zip`, Node.js와 npm, `curl`. LibreOffice 패키지가 없는 dnf 시스템에서는 `rpm2cpio`와 `cpio`
- sudo 권한은 시스템 패키지에만 필요합니다

## 절차

### 1. 점검
```bash
bash skills/setup/scripts/setup.sh
```
항목은 기본 도구, 다이어그램 렌더(uv, Playwright Chromium headless 실행), 폰트(Amazon Ember, Noto Sans CJK KR, NanumSquareOTF Bold, D2Coding), 덱(pptxgenjs, python-pptx, lxml, Pillow, cairosvg, `soffice`, `pdftoppm`, `pdftotext`, `rsvg-convert`), 보고서(NanumSquareOTF Regular, docx, marked, docx-preview, jszip)로 나뉩니다. Chromium이 실행되지 않으면 `ldd`가 찾지 못한 공유 라이브러리를 함께 보여 줍니다.

### 2. 사용자 영역 설치
```bash
bash skills/setup/scripts/setup.sh install
```
| 항목 | 위치 |
|---|---|
| uv | `~/.local/bin`, astral.sh 설치 스크립트 |
| Playwright Chromium | `~/.cache/ms-playwright`. `PW_SPEC`에 고정한 Playwright 버전으로 `uv run --with` 실행 |
| Amazon Ember | `skills/aws-diagram-design/assets/fonts/ttf`에서 `~/.local/share/fonts/ember`로 복사(macOS는 `~/Library/Fonts/ember`) |
| Noto Sans CJK KR | github.com/notofonts/noto-cjk의 Regular, Medium, Bold OTF를 `~/.local/share/fonts/noto-cjk`로 |
| NanumSquareOTF, D2Coding | `skills/aws-ppt-skills/scripts/install_fonts.sh`: `~/.fonts`와 `~/.config/fontconfig/conf.d/`의 fontconfig 별칭 |
| pptxgenjs | `npm install -g` |
| docx, marked, docx-preview, jszip(aws-reports) | `npm install -g`, 버전 고정(`setup.sh`의 `REPORT_NPM`) |
| NanumSquareOTF Regular·Bold(aws-reports) | npm `@kfonts/nanum-square-otf` 0.2.0(OFL-1.1)을 `npm pack`으로 받아 `src/*.otf`를 `~/.local/share/fonts/nanumsquare-otf`로 복사 |
| python-pptx, lxml, Pillow, cairosvg | `pip install --user` |
| LibreOffice(패키지가 없는 dnf) | 공식 RPM 묶음을 SHA-256으로 확인한 뒤 `~/.local/opt/libreoffice`에 풀고 `~/.local/bin/soffice`로 연결 |

Homebrew가 있는 macOS에서는 Poppler, librsvg, LibreOffice cask를 이 단계에서 설치합니다(sudo 불필요).

### 3. 시스템 패키지 설치(sudo)
설치 단계는 마지막에 "sudo가 필요한 시스템 패키지"와 건너뛴 명령을 출력합니다. 이 명령을 사용자에게 보여 주고 허락을 받은 뒤 실행합니다.
```bash
bash skills/setup/scripts/setup.sh install --sudo
```
| 패키지 관리자 | 패키지 |
|---|---|
| dnf(Amazon Linux, Fedora, RHEL) | Chromium 라이브러리 `atk at-spi2-atk at-spi2-core libxkbcommon alsa-lib mesa-libgbm libXcomposite libXdamage libXfixes libXrandr`, `poppler-utils`, `librsvg2-tools`, 홈에 푼 LibreOffice용 `libXinerama`. 저장소에 있으면 `libreoffice-impress` |
| apt(Ubuntu, Debian) | `playwright install-deps chromium`, `poppler-utils`, `librsvg2-bin`, `libreoffice-impress` |

`sudo -n`에 암호가 필요하면 스크립트는 명령만 출력합니다. Claude Code에서는 사용자가 프롬프트에 `! <명령>`으로 직접 실행합니다. `!` 앞에 공백이 있으면 안 됩니다.

### 4. 재점검
1단계를 다시 실행하고 `missing:` 값을 알립니다.

## Amazon Linux 2023
- **Chromium 시스템 라이브러리** — Playwright가 내려받는 Chromium에는 3단계의 dnf 라이브러리가 필요합니다. 없으면 headless 실행이 실패하고 점검이 빠진 `.so` 파일을 보여 줍니다.
- **LibreOffice** — Amazon Linux 2023 저장소에는 없습니다. `setup.sh`가 download.documentfoundation.org에서 최신 버전을 읽어 `LibreOffice_<ver>_Linux_<arch>_rpm.tar.gz`와 `.sha256`을 내려받아 확인하고, `rpm2cpio | cpio`로 RPM을 `~/.local/opt/libreoffice`에 풀며, `oosplash`가 링크하는 `libXinerama`를 시스템 패키지 목록에 넣습니다. 지원 아키텍처는 aarch64와 x86_64입니다.
- **Playwright 경고** — Playwright는 Amazon Linux 2023을 공식 지원하지 않으므로 Ubuntu용 Chromium 빌드를 쓰고, 렌더할 때마다 `BEWARE: your OS is not officially supported`를 출력합니다. 결과에는 영향이 없습니다.
- **LibreOffice GUI 라이브러리** — 홈에 푼 LibreOffice는 KDE, Qt, GTK, GStreamer 라이브러리가 없다고 알립니다. GUI 플러그인용이며 `soffice --headless` 변환에는 필요 없습니다.
- **PATH** — `~/.local/bin`이 셸 설정 파일에 없으면 점검이 `[info]`로 알립니다. `~/.bashrc`에 `export PATH="$HOME/.local/bin:$PATH"`를 추가합니다.

## 검증
- [ ] `bash skills/setup/scripts/setup.sh`가 `missing: 0`으로 끝납니다
- [ ] `fc-match "NanumSquareOTF Bold"`가 `NanumSquareOTF_ac`를 가리킵니다
- [ ] `fc-list : file | grep NanumSquareR.otf`가 aws-reports 본문 폰트를 보여 줍니다
- [ ] `soffice --headless --version`이 버전을 출력합니다

## 롤백
시스템 패키지를 뺀 나머지는 모두 사용자 홈에 있습니다. 필요 없는 것을 지웁니다.
```bash
rm -rf ~/.local/opt/libreoffice ~/.local/share/fonts/ember ~/.local/share/fonts/noto-cjk ~/.cache/ms-playwright
rm -rf ~/.local/share/fonts/nanumsquare-otf
rm -f ~/.local/bin/soffice ~/.config/fontconfig/conf.d/60-aws-ppt-fonts.conf
rm -f ~/.fonts/NanumSquareOTF_acB.otf ~/.fonts/D2Coding-*.ttf && fc-cache -f
npm uninstall -g pptxgenjs docx marked docx-preview jszip
python3 -m pip uninstall python-pptx lxml Pillow cairosvg
```
`install_fonts.sh`는 `conf.d` 별칭이 읽히지 않을 때 없던 `~/.config/fontconfig/fonts.conf`도 만듭니다. 이 별칭만 들어 있을 때만 지웁니다. 시스템 패키지는 패키지 관리자로 제거합니다(`sudo dnf remove ...`, `sudo apt-get remove ...`).

## 참고
- 새 외부 프로그램이나 폰트는 `skills/setup/scripts/setup.sh`(점검과 설치), `skills/setup/SKILL.md`, README 두 언어 섹션에 추가합니다.
- 최종 검증일: 2026-11-03 (점검 모드, Amazon Linux 2023 aarch64, `missing: 0`). aws-reports 항목은 2026-11-05에 점검 모드와, 격리된 `HOME`과 npm prefix에서 `install_reports_user`를 확인했습니다

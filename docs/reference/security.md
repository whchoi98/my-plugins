# Security / 보안 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<a id="english"></a>
## English

### 1. Overview
The repo is planned as a public repo and its root is the installed plugin. Security goals: nothing secret is
ever committed; no plugin component that runs by itself ships to installers; the scripts that the eight skills
run on a user's machine stay inside the user's working folder or home, and fetch only what their step needs;
`setup` never escalates without the user's say; instructions hidden in source material are not followed; and
the dev harness cannot be bypassed silently.

### 2. Components
| Component | Path | Purpose |
|---|---|---|
| Secret scanner | `.claude/hooks/secret-scan.sh` | PreToolUse on `git commit` (exit 2), git pre-commit (`--staged`, exit 1), manual `--files` |
| Git hook installer | `scripts/install-hooks.sh` | Installs `pre-commit` (secret scan) and `commit-msg` (strips `Co-Authored-By`) |
| Doc-sync reminder | `.claude/hooks/check-doc-sync.sh` | PostToolUse on Write/Edit; sends each reminder once per session and records it in `${TMPDIR:-/tmp}/claude-doc-sync-<session_id>.seen` (`session_id` reduced to `[A-Za-z0-9_-]`) |
| Claude settings | `.claude/settings.json` | Deny list, `Read(./.env)` denied, empty commit/PR attribution, hook registration |
| Ignore rules | `.gitignore` | `.env`, `.claude/settings.local.json`, archives, `__pycache__/`, blog work folders `<YYYY-MM-DD>-<slug>/` |
| Shipped MCP config | `.mcp.json` | Must stay `{"mcpServers": {}}`; installers read it as the plugin's MCP config |
| Shipped commands | `commands/` | Three prompts the user invokes explicitly; they declare `allowed-tools` (Read, Write, Edit, Bash, Glob) for export and import |
| Dependency installer | `skills/setup/scripts/setup.sh` | Check by default; user-level installs with `install`; system packages only with `--sudo`, through `sudo -n` |
| Deck font installer | `skills/aws-ppt-skills/scripts/install_fonts.sh` | Copies two bundled fonts to `~/.fonts` and writes a fontconfig alias under `~/.config/fontconfig/` |
| Blog packaging | `skills/aws-blog-skills/scripts/package_blog.sh` | Deletes only `<out>/<slug>` and `<out>/<slug>.zip` (`${OUT:?}` guard) |
| URL checker | `skills/aws-blog-skills/scripts/check_urls.py` | GET only, URLs taken from the given drafts, no credentials |
| Blog renderer | `skills/aws-blog-skills/scripts/render_diagrams.py` | Opens only local `file://` pages from the given images directory |
| Diagram import parsers | `skills/aws-diagram-design/scripts/mermaid_extract.py`, `drawio_extract.py` | Mermaid is parsed as bounded text and never evaluated, rendered, fetched or executed; draw.io XML with DTD or entity declarations is rejected and decompression is size-limited |
| Diagram self-check | `skills/aws-diagram-design/scripts/self_check.py` | Flags remote assets (except the approved Google Fonts stylesheet), executable attributes and extra scripts in a generated HTML file |
| Source-material rule | `skills/aws-blog-skills/SKILL.md` step 0 | Instructions inside sources and fetched pages are not followed, kept out of the draft, and reported to the user |
| Structure tests | `tests/structure/test-plugin-structure.sh` | Root component paths, empty `.mcp.json`, stale namespaces under `skills/` and `commands/`, no `CLAUDE.md` inside skill folders |
| Skill tests | `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-integration.sh` | The step 0 rule; `setup.sh` check mode and exit codes, every executed sudo is `sudo -n` inside the `--sudo` path |

**Scripts by skill.** Claude runs these only when it follows a SKILL.md and the user approves the command.

| Skill | Reads | Writes | Runs or fetches |
|---|---|---|---|
| aws-blog-skills | drafts, sibling `aws-diagram-design/assets` | work folder `<YYYY-MM-DD>-<slug>/` only | Playwright Chromium on local files; GET on draft URLs |
| aws-diagram | bundled `assets/icons.json`, the draft SVG | output SVG in the working directory | nothing |
| aws-diagram-design | the HTML, `.drawio` or `.mmd` given | HTML/SVG/PNG next to the source or at `--output` | Playwright Chromium for export |
| aws-ppt-skills | bundled templates and fonts, built deck | deck and QA images in the working directory; fonts in the home | `node`, `soffice`, `pdftoppm`; `svg_to_png.py` tries Playwright, cairosvg, `rsvg-convert`, `convert` |
| consulting-ppt-white-ppt | logo image, built deck | deck in the working directory; `fix_pptx.py` rewrites it in place | `node`, `soffice`, `pdftoppm` |
| pptx-template-fill | the user's template | filled deck in the working directory | `qa_check.py --render` runs `soffice` and `pdftotext` |
| kor-deslop | the text in the conversation | nothing | nothing |
| setup | its own and sibling skill folders | user home (see below); system packages only with `--sudo` | downloads below |

`build_bundle.py` (aws-diagram) and `build_aws_icons.py` (aws-diagram-design) rebuild a skill's own `assets/`
from an icon package. They are maintainer tools for a clone; no workflow step runs them.

**What `setup.sh install` downloads.**

| Item | Source | Integrity |
|---|---|---|
| uv | `https://astral.sh/uv/install.sh`, piped to `sh` | HTTPS only |
| Noto Sans CJK KR (3 OTF) | `github.com/notofonts/noto-cjk` raw files | HTTPS only |
| LibreOffice (dnf without a package) | `download.documentfoundation.org/libreoffice/stable/` RPM bundle | `sha256sum -c` against the `.sha256` from the same server; aborts on mismatch |
| Playwright and Chromium | PyPI through `uv run --with` (pinned version), then `playwright install chromium` | Playwright's own download |
| pptxgenjs; python-pptx, lxml, Pillow, cairosvg | npm registry (`npm install -g`); PyPI (`pip install --user`) | Registry defaults |
| System packages | the configured dnf, apt or Homebrew repositories | Package manager signatures |

User-level writes: `~/.local/bin`, `~/.local/opt/libreoffice`, `~/.local/share/fonts` (macOS `~/Library/Fonts`),
`~/.cache/ms-playwright`, `~/.fonts`, `~/.config/fontconfig/`, the pip user site and the npm global folder.

### 3. Key Decisions
- Markdown is scanned. The project-init template skips `*.md`, which would leave this repo almost unscanned.
- PreToolUse blocks with exit 2 and has no `|| true`; exit 1 would only warn.
- The PreToolUse scan also covers modified and untracked files when the command contains `git add` or
  `commit -a`, because staging happens after the hook runs. The git pre-commit hook covers commits made
  outside Claude Code.
- No hook, agent, MCP server, `bin/` or `settings.json` ships at the root, so installing runs nothing by itself.
  `commands/` is the only root component and holds prompts, not code.
- Scripts never write into a skill folder, which is the plugin cache. Output goes to the work folder or the
  user's current directory ([ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md)); `setup` and
  `install_fonts.sh` write only under the user's home. One exception is model-driven, not a script: the
  aws-diagram-design brand onboarding (`skills/aws-diagram-design/references/onboarding.md`) rewrites the skill's
  own `references/style-guide.md` after the user approves the diff. In an installed copy that file is in the
  plugin cache, so the change is lost on the next update.
- `setup.sh` runs sudo only when given `--sudo`, and then only `sudo -n`, which never prompts. When a password is
  needed it prints the command, and `skills/setup/SKILL.md` makes Claude show the command and ask before the sudo
  step. The user runs it as `! <command>`.
- Only the LibreOffice download is checksum-verified, and the checksum comes from the same server, so it
  catches corruption, not a compromised mirror. uv and the Noto fonts rely on HTTPS alone.
- Source material (blogs, PDFs, slides) and pages read with WebFetch are data, not instructions. In
  aws-blog-skills step 0, task instructions come only from the user's messages; an instruction found in a source
  is not followed, not copied into the draft, and reported with its location. Commands in a source are content
  to quote or verify; running one needs the user's approval first. `tests/structure/test-aws-blog-skills.sh` keeps this rule in step 0.
  The deck and diagram skills also read user-supplied sources but do not state this rule.
- The diagram import parsers treat `.drawio` and Mermaid input as untrusted, and `self_check.py` rejects remote
  assets other than the approved Google Fonts stylesheet, executable attributes and extra scripts, so a
  generated diagram is a self-contained file.

### 4. Code Pointers
- `.claude/hooks/secret-scan.sh`
- `.claude/hooks/check-doc-sync.sh`
- `.claude/settings.json`
- `scripts/install-hooks.sh`
- `skills/setup/scripts/setup.sh`
- `skills/setup/SKILL.md`
- `skills/aws-ppt-skills/scripts/install_fonts.sh`
- `skills/aws-blog-skills/SKILL.md`
- `skills/aws-blog-skills/scripts/package_blog.sh`
- `skills/aws-blog-skills/scripts/check_urls.py`
- `skills/aws-diagram-design/scripts/mermaid_extract.py`
- `skills/aws-diagram-design/scripts/self_check.py`
- `tests/hooks/test-hooks.sh`
- `tests/hooks/test-secret-patterns.sh`
- `tests/structure/test-plugin-structure.sh`
- `tests/structure/test-integration.sh`

### 5. Cross-references
- Related modules: `skills/` (`skills/CLAUDE.md`), `tests/` (`tests/CLAUDE.md`)
- Related ADRs: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md),
  [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- Related runbooks: [release-plugin.md](../runbooks/release-plugin.md),
  [setup-dependencies.md](../runbooks/setup-dependencies.md)

<a id="korean"></a>
## 한국어

### 1. 개요
저장소는 공개 저장소로 배포할 예정이고 루트가 곧 설치되는 플러그인입니다. 보안 목표는 다음과 같이 정리됩니다. 비밀 정보를 커밋하지 않습니다. 스스로 실행되는 플러그인 구성 요소를 배포하지 않습니다. skill 8개가 사용자 머신에서 실행하는 스크립트는 사용자의 작업 폴더나 홈 안에서만 쓰고, 그 단계에 필요한 것만 내려받습니다. `setup`은 사용자가 허락하지 않으면 권한을 올리지 않습니다. 소재에 숨은 지시문은 따르지 않으며, 개발 하네스를 조용히 우회할 수 없게 합니다.

### 2. 구성요소
| 구성요소 | 경로 | 역할 |
|---|---|---|
| 시크릿 스캐너 | `.claude/hooks/secret-scan.sh` | `git commit` PreToolUse(exit 2), git pre-commit(`--staged`, exit 1), 수동 `--files` |
| Git 훅 설치기 | `scripts/install-hooks.sh` | `pre-commit`(시크릿 스캔)과 `commit-msg`(`Co-Authored-By` 제거) 설치 |
| 문서 동기화 리마인더 | `.claude/hooks/check-doc-sync.sh` | Write/Edit PostToolUse. 같은 리마인더는 세션당 한 번만 보내고 `${TMPDIR:-/tmp}/claude-doc-sync-<session_id>.seen`에 기록(`session_id`는 `[A-Za-z0-9_-]`만 남김) |
| Claude 설정 | `.claude/settings.json` | deny 목록, `Read(./.env)` 차단, 커밋과 PR attribution 비움, 훅 등록 |
| 무시 규칙 | `.gitignore` | `.env`, `.claude/settings.local.json`, 압축 파일, `__pycache__/`, 블로그 작업 폴더 `<YYYY-MM-DD>-<slug>/` |
| 배포되는 MCP 설정 | `.mcp.json` | `{"mcpServers": {}}` 유지. 설치자에게는 플러그인 MCP 설정으로 읽힘 |
| 배포되는 command | `commands/` | 사용자가 직접 부르는 프롬프트 3개. 내보내기와 가져오기를 위해 `allowed-tools`(Read, Write, Edit, Bash, Glob)를 선언 |
| 의존 프로그램 설치기 | `skills/setup/scripts/setup.sh` | 기본은 점검, `install`은 사용자 영역 설치, 시스템 패키지는 `--sudo`일 때만 `sudo -n`으로 |
| 덱 폰트 설치기 | `skills/aws-ppt-skills/scripts/install_fonts.sh` | 포함된 폰트 두 개를 `~/.fonts`에 복사하고 `~/.config/fontconfig/`에 fontconfig 별칭 기록 |
| 블로그 패키징 | `skills/aws-blog-skills/scripts/package_blog.sh` | `<out>/<slug>`와 `<out>/<slug>.zip`만 삭제(`${OUT:?}` 가드) |
| URL 검사기 | `skills/aws-blog-skills/scripts/check_urls.py` | GET만 사용, 지정한 원고에서 찾은 URL만 요청, 자격 증명 없음 |
| 블로그 렌더러 | `skills/aws-blog-skills/scripts/render_diagrams.py` | 지정한 images 폴더의 로컬 `file://` 페이지만 열기 |
| 다이어그램 가져오기 파서 | `skills/aws-diagram-design/scripts/mermaid_extract.py`, `drawio_extract.py` | Mermaid는 범위가 정해진 텍스트로만 파싱하고 평가, 렌더, 내려받기, 실행을 하지 않음. draw.io XML은 DTD와 엔티티 선언이 있으면 거부하고 압축 해제 크기를 제한 |
| 다이어그램 자체 점검 | `skills/aws-diagram-design/scripts/self_check.py` | 생성된 HTML에서 외부 자산(승인된 Google Fonts 스타일시트 제외), 실행 속성, 추가 스크립트를 잡아냄 |
| 소재 규칙 | `skills/aws-blog-skills/SKILL.md` 0단계 | 소재와 읽어 온 페이지 안의 지시문을 따르지 않고 원고에 넣지 않으며 사용자에게 알림 |
| 구조 테스트 | `tests/structure/test-plugin-structure.sh` | 루트 구성 요소 경로, 빈 `.mcp.json`, `skills/`와 `commands/`의 예전 이름 공간, skill 폴더 안 `CLAUDE.md` 금지 |
| skill 테스트 | `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-integration.sh` | 0단계 규칙, `setup.sh` 점검 모드와 종료 코드, 실행되는 sudo가 모두 `--sudo` 경로 안의 `sudo -n`인지 |

**skill별 스크립트.** Claude는 SKILL.md를 따를 때, 사용자가 명령을 승인한 경우에만 이 스크립트를 실행합니다.

| skill | 읽는 것 | 쓰는 곳 | 실행하거나 내려받는 것 |
|---|---|---|---|
| aws-blog-skills | 원고, 옆 skill의 `aws-diagram-design/assets` | 작업 폴더 `<YYYY-MM-DD>-<slug>/`만 | 로컬 파일을 여는 Playwright Chromium, 원고 URL에 GET |
| aws-diagram | 포함된 `assets/icons.json`, 초안 SVG | 작업 디렉터리의 결과 SVG | 없음 |
| aws-diagram-design | 지정한 HTML, `.drawio`, `.mmd` | 원본 옆이나 `--output`의 HTML/SVG/PNG | 내보내기용 Playwright Chromium |
| aws-ppt-skills | 포함된 템플릿과 폰트, 빌드한 덱 | 작업 디렉터리의 덱과 QA 이미지, 홈의 폰트 | `node`, `soffice`, `pdftoppm`. `svg_to_png.py`는 Playwright, cairosvg, `rsvg-convert`, `convert` 순으로 시도 |
| consulting-ppt-white-ppt | 로고 이미지, 빌드한 덱 | 작업 디렉터리의 덱. `fix_pptx.py`가 제자리에서 고침 | `node`, `soffice`, `pdftoppm` |
| pptx-template-fill | 사용자의 템플릿 | 작업 디렉터리의 채운 덱 | `qa_check.py --render`가 `soffice`와 `pdftotext` 실행 |
| kor-deslop | 대화 안의 글 | 없음 | 없음 |
| setup | 자기 폴더와 옆 skill 폴더 | 사용자 홈(아래 참고). 시스템 패키지는 `--sudo`일 때만 | 아래 내려받기 |

`build_bundle.py`(aws-diagram)와 `build_aws_icons.py`(aws-diagram-design)는 아이콘 패키지로 skill 자신의 `assets/`를 다시 만드는 관리자용 도구입니다. 클론에서만 쓰며, 워크플로 단계에서는 실행하지 않습니다.

**`setup.sh install`이 내려받는 것.**

| 항목 | 출처 | 무결성 |
|---|---|---|
| uv | `https://astral.sh/uv/install.sh`를 `sh`로 실행 | HTTPS만 |
| Noto Sans CJK KR(OTF 3개) | `github.com/notofonts/noto-cjk` 원본 파일 | HTTPS만 |
| LibreOffice(패키지가 없는 dnf) | `download.documentfoundation.org/libreoffice/stable/` RPM 묶음 | 같은 서버의 `.sha256`으로 `sha256sum -c`. 불일치하면 중단 |
| Playwright와 Chromium | `uv run --with`(버전 고정)로 PyPI에서, 그다음 `playwright install chromium` | Playwright 자체 내려받기 |
| pptxgenjs, python-pptx, lxml, Pillow, cairosvg | npm 레지스트리(`npm install -g`), PyPI(`pip install --user`) | 레지스트리 기본값 |
| 시스템 패키지 | 설정된 dnf, apt, Homebrew 저장소 | 패키지 관리자 서명 |

사용자 영역에 쓰는 곳: `~/.local/bin`, `~/.local/opt/libreoffice`, `~/.local/share/fonts`(macOS는 `~/Library/Fonts`), `~/.cache/ms-playwright`, `~/.fonts`, `~/.config/fontconfig/`, pip 사용자 경로, npm 전역 폴더.

### 3. 주요 결정
- Markdown도 스캔합니다. project-init 템플릿은 `*.md`를 건너뛰어 이 저장소를 거의 검사하지 못합니다.
- PreToolUse는 exit 2로 차단하고 `|| true`를 붙이지 않습니다. exit 1은 경고만 합니다.
- 명령에 `git add`나 `commit -a`가 들어 있으면 PreToolUse 스캔이 수정 파일과 추적되지 않은 파일까지 확인합니다. 스테이징이 훅 실행 뒤에 일어나기 때문입니다. Claude Code 밖에서 만든 커밋은 git pre-commit 훅이 막습니다.
- 루트에는 훅, agent, MCP 서버, `bin/`, `settings.json`을 배포하지 않으므로 설치만으로는 아무것도 실행되지 않습니다. 루트의 구성 요소는 `commands/`뿐이며, 코드가 아니라 프롬프트입니다.
- 스크립트는 플러그인 캐시인 skill 폴더에 쓰지 않습니다. 결과는 작업 폴더나 사용자의 현재 디렉터리에 두고([ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md)), `setup`과 `install_fonts.sh`는 사용자 홈 아래에만 씁니다. 예외가 하나 있는데, 스크립트가 아니라 모델이 하는 일입니다. aws-diagram-design 브랜드 온보딩(`skills/aws-diagram-design/references/onboarding.md`)은 사용자가 diff를 승인하면 skill 자신의 `references/style-guide.md`를 다시 씁니다. 설치본에서는 이 파일이 플러그인 캐시에 있으므로 다음 업데이트 때 변경이 사라집니다.
- `setup.sh`는 `--sudo`를 받았을 때만, 그것도 암호를 묻지 않는 `sudo -n`으로만 sudo를 씁니다. 암호가 필요하면 명령을 출력하고, `skills/setup/SKILL.md`에 따라 Claude가 sudo 단계 전에 명령을 보여 주고 허락을 받습니다. 사용자는 `! <명령>`으로 직접 실행합니다.
- 체크섬으로 확인하는 것은 LibreOffice뿐이고, 체크섬도 같은 서버에서 받으므로 손상은 잡지만 오염된 미러는 막지 못합니다. uv와 Noto 폰트는 HTTPS에만 기댑니다.
- 소재(블로그, PDF, 슬라이드)와 WebFetch로 읽은 페이지는 지시가 아니라 데이터입니다. aws-blog-skills 0단계에서 작업 지시는 사용자의 메시지에서만 받습니다. 소재에서 발견한 지시문은 따르지 않고 원고에 옮기지 않으며, 위치와 함께 사용자에게 알립니다. 소재의 명령은 인용하거나 검증할 내용이고, 실행하려면 먼저 사용자 승인을 받습니다. `tests/structure/test-aws-blog-skills.sh`가 이 규칙이 0단계에 남아 있는지 확인합니다. 덱과 다이어그램 skill도 사용자가 준 소재를 읽지만 이 규칙을 명시하지 않습니다.
- 다이어그램 가져오기 파서는 `.drawio`와 Mermaid 입력을 신뢰하지 않고, `self_check.py`는 승인된 Google Fonts 스타일시트 외의 외부 자산, 실행 속성, 추가 스크립트를 거부하므로 생성된 다이어그램은 혼자 완결된 파일입니다.

### 4. 코드 포인터
- `.claude/hooks/secret-scan.sh`
- `.claude/hooks/check-doc-sync.sh`
- `.claude/settings.json`
- `scripts/install-hooks.sh`
- `skills/setup/scripts/setup.sh`
- `skills/setup/SKILL.md`
- `skills/aws-ppt-skills/scripts/install_fonts.sh`
- `skills/aws-blog-skills/SKILL.md`
- `skills/aws-blog-skills/scripts/package_blog.sh`
- `skills/aws-blog-skills/scripts/check_urls.py`
- `skills/aws-diagram-design/scripts/mermaid_extract.py`
- `skills/aws-diagram-design/scripts/self_check.py`
- `tests/hooks/test-hooks.sh`
- `tests/hooks/test-secret-patterns.sh`
- `tests/structure/test-plugin-structure.sh`
- `tests/structure/test-integration.sh`

### 5. 상호 참조
- 관련 모듈: `skills/`(`skills/CLAUDE.md`), `tests/`(`tests/CLAUDE.md`)
- 관련 ADR: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md), [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- 관련 런북: [release-plugin.md](../runbooks/release-plugin.md), [setup-dependencies.md](../runbooks/setup-dependencies.md)

# Security / 보안 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<a id="english"></a>
## English

### 1. Overview
The repo is planned as a public repo and its root is the installed plugin. Security goals: nothing secret is
ever committed; no plugin component that runs by itself ships to installers; the scripts that the fourteen skills
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
| Editable-deck checker | `skills/aws-infographic/scripts/check_editable.py` | Standard library only; reads slide XML from the given `.pptx` and refuses XML that carries a DTD or entity declarations |
| Source-material rule | `skills/aws-blog-skills/SKILL.md` step 0 | Instructions inside sources and fetched pages are not followed, kept out of the draft, and reported to the user |
| Structure tests | `tests/structure/test-plugin-structure.sh` | Root component paths, empty `.mcp.json`, stale namespaces under `skills/` and `commands/`, no `CLAUDE.md` inside skill folders |
| Skill tests | `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-integration.sh`, `tests/structure/test-techblogs.sh` | The step 0 rule; `setup.sh` check mode and exit codes, every executed sudo is `sudo -n` inside the `--sudo` path; techblogs refuses an `--out` inside the skill folder, fetches only from the AWS blog hosts and never runs git |

**Scripts by skill.** Claude runs these only when it follows a SKILL.md and the user approves the command.

| Skill | Reads | Writes | Runs or fetches |
|---|---|---|---|
| aws-blog-skills | drafts, sibling `aws-diagram-design/assets` | work folder `<YYYY-MM-DD>-<slug>/` only | Playwright Chromium on local files; GET on draft URLs |
| aws-diagram | bundled `assets/icons.json`, the draft SVG | output SVG in the working directory | nothing |
| aws-diagram-design | the HTML, `.drawio` or `.mmd` given | HTML/SVG/PNG next to the source or at `--output` | Playwright Chromium for export |
| aws-ppt-skills | bundled templates and fonts, built deck | deck, HTML deck and QA images in the working directory; fonts in the home | `node`, `soffice`, `pdftoppm`; `svg_to_png.py` tries Playwright, cairosvg, `rsvg-convert`, `convert`; `deck_to_html.py` runs `soffice` (a LibreOffice profile of its own in a temporary folder) and `pdftoppm`; `preview_html_deck.py` opens the page in Playwright Chromium. The HTML deck loads nothing from the network, escapes slide and note text, keeps only `http`, `https` and `mailto` links, and holds the speaker notes as readable text unless `--no-notes` is given |
| consulting-ppt-white-ppt | logo image, built deck | deck in the working directory; `fix_pptx.py` rewrites it in place | `node`, `soffice`, `pdftoppm` |
| pptx-template-fill | the user's template | filled deck in the working directory | `qa_check.py --render` runs `soffice` and `pdftotext` |
| aws-reports | the user's data, notes and drafts; its own `scripts/`, `references/`, `assets/examples/` | the work folder (`report/`, `charts/`, `report/out/`); nothing in the skill folder (chart scripts run with `python -B`) | `node report.mjs` (imports docx and marked from the global npm folder), `uv run` fontTools for font subsets, Playwright Chromium for previews |
| html-report | the user's notes, data and sources; its own `assets/template.html` | the work folder (`report/`, `report/out/`); `embed_images.py` reads only image files inside the page's folder | Playwright Chromium for previews (the system `node` as the Playwright driver when the bundled one does not start) |
| techblogs | the user's notes and data; a published AWS blog post (its address or a saved page); its own `assets/template.html`; the blog repository's `_config.yml` and `assets/icons` | the work folder (`<YYYY-MM-DD>-<slug>/` and its `out/`); `build_post.py` refuses an `--out` inside the skill folder; `place_post.py` copies the post into `<blog repository>/docs/techblog/<category>/` and never runs git | `import_aws_post.py` GETs the post and its images only from `aws.amazon.com` and the AWS blog image host; `check_urls.py` (aws-blog-skills) GETs the page's links; `place_post.py --build` runs the blog repository's `scripts/build-lab-zip.sh` when it exists and `bundle exec jekyll build`; Playwright Chromium for previews (the system `node` as the Playwright driver when it is on `PATH`) |
| aws-infographic | the user's sketches, notes and sources; the sibling `aws-diagram/assets/icons.json`; installed font files | the work folder (copies of `infokit.py` and `buildkit.py`, `.aws-icon-bundle`, `build/`, `deck/`); nothing in the skill folder (`icon_png.py` runs with bytecode off) | Playwright Chromium on local SVG files and data URIs; `fc-list`, `fc-match`; the deck step runs the aws-ppt-skills tools |
| kor-deslop | the text in the conversation | nothing | nothing |
| ui-deslop | the source files of the screen, or a page address or screenshot the user gives | the user's project (the redesigned screen, `unslop/`, `unslop-story/`); nothing in the skill folder | `snapshot.mjs` opens the address in Node Playwright Chromium and saves the page; `story.mjs` serves the story folder on 127.0.0.1 and runs `ffmpeg`; an image tool only when the user has one and agrees to each run |
| eng-deslop | the text in the conversation, or the file the user names | that file, prose only | nothing |
| setup | its own and sibling skill folders | user home (see below); system packages only with `--sudo` | downloads below |

`build_bundle.py` (aws-diagram) and `build_aws_icons.py` (aws-diagram-design) rebuild a skill's own `assets/`
from an icon package. They are maintainer tools for a clone; no workflow step runs them.

**Vendored skills.** `ui-deslop` and `eng-deslop` are other authors' text that Claude follows, copied at a pinned commit
(`scripts/upstream-skills.json`). `scripts/sync_upstream_skills.py` copies files and never runs one. It refuses a source
whose license changed, a symbolic link, a hidden file, a file type outside the skill's `allow_ext`, an unusual file name
and a file over 2 MB, and `verify` fails when a vendored file differs from its recorded hash.
`.github/workflows/sync-upstream-skills.yml` runs the script every week on GitHub with a token for this repository only
(`contents`, `pull-requests` and `issues`: write). It pushes one branch, `sync/upstream-skills`, and opens a pull request
or an issue. It merges nothing, releases nothing, runs no file of a source and puts no text of a source or of an event
into a command; the report it writes shows a source's text inside code spans. Node Playwright and ffmpeg for the
optional parts of ui-deslop are installed by the user; `setup` only reports ffmpeg.

**What `setup.sh install` downloads.**

| Item | Source | Integrity |
|---|---|---|
| uv | `https://astral.sh/uv/install.sh`, piped to `sh` | HTTPS only |
| Noto Sans CJK KR (3 OTF) | `github.com/notofonts/noto-cjk` raw files | HTTPS only |
| LibreOffice (dnf without a package) | `download.documentfoundation.org/libreoffice/stable/` RPM bundle | `sha256sum -c` against the `.sha256` from the same server; aborts on mismatch |
| Playwright and Chromium | PyPI through `uv run --with` (pinned version), then `playwright install chromium` | Playwright's own download |
| pptxgenjs; python-pptx, lxml, Pillow, cairosvg, fonttools | npm registry (`npm install -g`); PyPI (`pip install --user`) | Registry defaults |
| docx, marked, docx-preview, jszip (aws-reports) | npm registry (`npm install -g`, exact versions in `REPORT_NPM`) | Registry defaults |
| NanumSquareOTF (aws-reports) | npm registry `@kfonts/nanum-square-otf@0.2.0` through `npm pack`; only `src/*.otf` is copied | npm checks the tarball against the registry's sha512 integrity |
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
- techblogs leaves the work folder only through `place_post.py`, which copies one post into the blog repository the
  user names and prints `git add` lines instead of running git; staging, commit and push stay with the user because a
  push to that repository publishes the site. `import_aws_post.py` treats the page as data: it keeps an allowlist of
  inline tags and fetches only from the AWS blog hosts ([ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md)).
- A change in the source of a vendored skill is a change of instructions for every installer, so it reaches `main` only
  through a pull request that a person reads and reaches users only through a release by the maintainer. The copy is
  pinned to a commit with a hash per file, and a new file type has to be allowed in the manifest first
  ([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).

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
- `skills/techblogs/scripts/import_aws_post.py`
- `skills/techblogs/scripts/place_post.py`
- `skills/aws-infographic/scripts/check_editable.py`
- `skills/aws-diagram-design/scripts/mermaid_extract.py`
- `skills/aws-diagram-design/scripts/self_check.py`
- `tests/hooks/test-hooks.sh`
- `tests/hooks/test-secret-patterns.sh`
- `tests/structure/test-plugin-structure.sh`
- `tests/structure/test-integration.sh`
- `tests/structure/test-techblogs.sh`
- `tests/structure/test-aws-infographic.sh`
- `scripts/sync_upstream_skills.py`
- `scripts/upstream-skills.json`
- `.github/workflows/sync-upstream-skills.yml`
- `tests/structure/test-upstream-skills.sh`

### 5. Cross-references
- Related modules: `skills/` (`skills/CLAUDE.md`), `tests/` (`tests/CLAUDE.md`)
- Related ADRs: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md),
  [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- Related runbooks: [release-plugin.md](../runbooks/release-plugin.md),
  [setup-dependencies.md](../runbooks/setup-dependencies.md)

<a id="korean"></a>
## 한국어

### 1. 개요
저장소는 공개 저장소로 배포할 예정이고 루트가 곧 설치되는 플러그인입니다. 보안 목표는 다음과 같이 정리됩니다. 비밀 정보를 커밋하지 않습니다. 스스로 실행되는 플러그인 구성 요소를 배포하지 않습니다. skill 14개가 사용자 머신에서 실행하는 스크립트는 사용자의 작업 폴더나 홈 안에서만 쓰고, 그 단계에 필요한 것만 내려받습니다. `setup`은 사용자가 허락하지 않으면 권한을 올리지 않습니다. 소재에 숨은 지시문은 따르지 않으며, 개발 하네스를 조용히 우회할 수 없게 합니다.

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
| 편집 가능 덱 검사기 | `skills/aws-infographic/scripts/check_editable.py` | 표준 라이브러리만 사용. 지정한 `.pptx`의 슬라이드 XML만 읽고, DTD나 entity 선언이 있는 XML은 거부 |
| 소재 규칙 | `skills/aws-blog-skills/SKILL.md` 0단계 | 소재와 읽어 온 페이지 안의 지시문을 따르지 않고 원고에 넣지 않으며 사용자에게 알림 |
| 구조 테스트 | `tests/structure/test-plugin-structure.sh` | 루트 구성 요소 경로, 빈 `.mcp.json`, `skills/`와 `commands/`의 예전 이름 공간, skill 폴더 안 `CLAUDE.md` 금지 |
| skill 테스트 | `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-integration.sh`, `tests/structure/test-techblogs.sh` | 0단계 규칙, `setup.sh` 점검 모드와 종료 코드, 실행되는 sudo가 모두 `--sudo` 경로 안의 `sudo -n`인지, techblogs가 skill 폴더 안의 `--out`을 거부하고 AWS 블로그 호스트에서만 내려받으며 git을 실행하지 않는지 |

**skill별 스크립트.** Claude는 SKILL.md를 따를 때, 사용자가 명령을 승인한 경우에만 이 스크립트를 실행합니다.

| skill | 읽는 것 | 쓰는 곳 | 실행하거나 내려받는 것 |
|---|---|---|---|
| aws-blog-skills | 원고, 옆 skill의 `aws-diagram-design/assets` | 작업 폴더 `<YYYY-MM-DD>-<slug>/`만 | 로컬 파일을 여는 Playwright Chromium, 원고 URL에 GET |
| aws-diagram | 포함된 `assets/icons.json`, 초안 SVG | 작업 디렉터리의 결과 SVG | 없음 |
| aws-diagram-design | 지정한 HTML, `.drawio`, `.mmd` | 원본 옆이나 `--output`의 HTML/SVG/PNG | 내보내기용 Playwright Chromium |
| aws-ppt-skills | 포함된 템플릿과 폰트, 빌드한 덱 | 작업 디렉터리의 덱, HTML 덱, QA 이미지, 홈의 폰트 | `node`, `soffice`, `pdftoppm`. `svg_to_png.py`는 Playwright, cairosvg, `rsvg-convert`, `convert` 순으로 시도. `deck_to_html.py`는 `soffice`(임시 폴더의 전용 LibreOffice 프로필)와 `pdftoppm`을 실행하고, `preview_html_deck.py`는 Playwright Chromium으로 페이지를 엽니다. HTML 덱은 네트워크에서 아무것도 불러오지 않고, 슬라이드와 노트의 글자를 이스케이프하며, `http`, `https`, `mailto` 링크만 남깁니다. 발표자 노트는 `--no-notes`를 주지 않으면 읽을 수 있는 글자로 들어갑니다 |
| consulting-ppt-white-ppt | 로고 이미지, 빌드한 덱 | 작업 디렉터리의 덱. `fix_pptx.py`가 제자리에서 고침 | `node`, `soffice`, `pdftoppm` |
| pptx-template-fill | 사용자의 템플릿 | 작업 디렉터리의 채운 덱 | `qa_check.py --render`가 `soffice`와 `pdftotext` 실행 |
| aws-reports | 사용자의 데이터, 메모, 초안. 자기 `scripts/`, `references/`, `assets/examples/` | 작업 폴더(`report/`, `charts/`, `report/out/`). skill 폴더에는 쓰지 않음(차트 스크립트는 `python -B`) | `node report.mjs`(전역 npm 폴더의 docx, marked를 import), 글꼴 부분집합용 `uv run` fontTools, 미리보기용 Playwright Chromium |
| html-report | 사용자의 메모, 데이터, 출처. 자기 `assets/template.html` | 작업 폴더(`report/`, `report/out/`). `embed_images.py`는 페이지 폴더 안의 그림 파일만 읽음 | 미리보기용 Playwright Chromium(포함된 드라이버가 시작되지 않으면 시스템 `node`를 Playwright 드라이버로 씀) |
| techblogs | 사용자의 메모와 데이터. 게시된 AWS 블로그 글(주소나 저장한 페이지). 자기 `assets/template.html`. 블로그 저장소의 `_config.yml`과 `assets/icons` | 작업 폴더(`<YYYY-MM-DD>-<slug>/`와 그 안의 `out/`). `build_post.py`는 skill 폴더 안의 `--out`을 거부함. `place_post.py`는 글을 `<블로그 저장소>/docs/techblog/<분류 폴더>/`에 복사하고 git을 실행하지 않음 | `import_aws_post.py`는 글과 그림을 `aws.amazon.com`과 AWS 블로그 그림 호스트에서만 GET. `check_urls.py`(aws-blog-skills)는 페이지의 링크를 GET. `place_post.py --build`는 블로그 저장소에 `scripts/build-lab-zip.sh`가 있으면 실행한 뒤 `bundle exec jekyll build`를 실행. 미리보기용 Playwright Chromium(`PATH`에 시스템 `node`가 있으면 Playwright 드라이버로 씀) |
| aws-infographic | 사용자의 손그림, 메모, 자료. 옆 skill의 `aws-diagram/assets/icons.json`. 설치된 폰트 파일 | 작업 폴더(`infokit.py`와 `buildkit.py` 사본, `.aws-icon-bundle`, `build/`, `deck/`). skill 폴더에는 쓰지 않음(`icon_png.py`는 바이트코드를 만들지 않음) | 로컬 SVG 파일과 data URI를 여는 Playwright Chromium. `fc-list`, `fc-match`. 덱 단계는 aws-ppt-skills의 도구를 실행 |
| kor-deslop | 대화 안의 글 | 없음 | 없음 |
| ui-deslop | 화면의 소스 파일, 또는 사용자가 준 페이지 주소나 스크린샷 | 사용자의 프로젝트(다시 디자인한 화면, `unslop/`, `unslop-story/`). skill 폴더에는 쓰지 않음 | `snapshot.mjs`가 Node Playwright Chromium으로 주소를 열어 페이지를 저장. `story.mjs`가 스토리 폴더를 127.0.0.1에서 제공하고 `ffmpeg`를 실행. 이미지 도구는 사용자가 연결해 두었고 실행마다 동의할 때만 |
| eng-deslop | 대화 안의 글, 또는 사용자가 지정한 파일 | 그 파일의 글 부분만 | 없음 |
| setup | 자기 폴더와 옆 skill 폴더 | 사용자 홈(아래 참고). 시스템 패키지는 `--sudo`일 때만 | 아래 내려받기 |

`build_bundle.py`(aws-diagram)와 `build_aws_icons.py`(aws-diagram-design)는 아이콘 패키지로 skill 자신의 `assets/`를 다시 만드는 관리자용 도구입니다. 클론에서만 쓰며, 워크플로 단계에서는 실행하지 않습니다.

**가져온 skill.** `ui-deslop`과 `eng-deslop`은 Claude가 따르는 다른 저작자의 글이며, 고정한 커밋에서 복사합니다(`scripts/upstream-skills.json`). `scripts/sync_upstream_skills.py`는 파일을 복사할 뿐 실행하지 않습니다. 라이선스가 바뀐 원본, 심볼릭 링크, 숨김 파일, skill의 `allow_ext`에 없는 파일 형식, 특이한 파일 이름, 2 MB를 넘는 파일은 거부하고, 가져온 파일이 기록한 해시와 다르면 `verify`가 실패합니다. `.github/workflows/sync-upstream-skills.yml`은 이 저장소에만 유효한 토큰(`contents`, `pull-requests`, `issues` 쓰기)으로 GitHub에서 매주 스크립트를 실행합니다. `sync/upstream-skills` 브랜치 하나만 push하고 pull request나 issue를 엽니다. 병합과 릴리스를 하지 않고, 원본의 파일을 실행하지 않으며, 원본이나 이벤트의 글을 명령에 넣지 않습니다. 보고서에는 원본의 글이 코드 표기 안에 들어갑니다. ui-deslop의 선택 기능에 쓰는 Node Playwright와 ffmpeg는 사용자가 설치하고, `setup`은 ffmpeg가 있는지만 알립니다.

**`setup.sh install`이 내려받는 것.**

| 항목 | 출처 | 무결성 |
|---|---|---|
| uv | `https://astral.sh/uv/install.sh`를 `sh`로 실행 | HTTPS만 |
| Noto Sans CJK KR(OTF 3개) | `github.com/notofonts/noto-cjk` 원본 파일 | HTTPS만 |
| LibreOffice(패키지가 없는 dnf) | `download.documentfoundation.org/libreoffice/stable/` RPM 묶음 | 같은 서버의 `.sha256`으로 `sha256sum -c`. 불일치하면 중단 |
| Playwright와 Chromium | `uv run --with`(버전 고정)로 PyPI에서, 그다음 `playwright install chromium` | Playwright 자체 내려받기 |
| pptxgenjs, python-pptx, lxml, Pillow, cairosvg, fonttools | npm 레지스트리(`npm install -g`), PyPI(`pip install --user`) | 레지스트리 기본값 |
| docx, marked, docx-preview, jszip(aws-reports) | npm 레지스트리(`npm install -g`, `REPORT_NPM`의 고정 버전) | 레지스트리 기본값 |
| NanumSquareOTF(aws-reports) | npm 레지스트리 `@kfonts/nanum-square-otf@0.2.0`을 `npm pack`으로. `src/*.otf`만 복사 | npm이 레지스트리의 sha512 integrity로 tarball을 확인 |
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
- techblogs가 작업 폴더 밖에 쓰는 경로는 `place_post.py` 하나입니다. 사용자가 지정한 블로그 저장소에 글 한 편을 복사하고 git을 실행하는 대신 `git add` 줄을 출력합니다. 그 저장소는 push하면 사이트가 배포되므로 스테이징, 커밋, push는 사용자가 합니다. `import_aws_post.py`는 페이지를 데이터로 다룹니다. 허용한 인라인 태그만 남기고 AWS 블로그 호스트에서만 내려받습니다([ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md)).
- 가져온 skill의 원본이 바뀌면 모든 설치자가 받는 지시문이 바뀝니다. 그래서 사람이 읽은 pull request로만 `main`에 들어가고, 관리자가 릴리스해야 사용자에게 전달됩니다. 복사본은 커밋과 파일별 해시로 고정하고, 새 파일 형식은 매니페스트에서 먼저 허용해야 들어옵니다([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).

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
- `skills/techblogs/scripts/import_aws_post.py`
- `skills/techblogs/scripts/place_post.py`
- `skills/aws-infographic/scripts/check_editable.py`
- `skills/aws-diagram-design/scripts/mermaid_extract.py`
- `skills/aws-diagram-design/scripts/self_check.py`
- `tests/hooks/test-hooks.sh`
- `tests/hooks/test-secret-patterns.sh`
- `tests/structure/test-plugin-structure.sh`
- `tests/structure/test-integration.sh`
- `tests/structure/test-techblogs.sh`
- `tests/structure/test-aws-infographic.sh`
- `scripts/sync_upstream_skills.py`
- `scripts/upstream-skills.json`
- `.github/workflows/sync-upstream-skills.yml`
- `tests/structure/test-upstream-skills.sh`

### 5. 상호 참조
- 관련 모듈: `skills/`(`skills/CLAUDE.md`), `tests/`(`tests/CLAUDE.md`)
- 관련 ADR: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md), [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- 관련 런북: [release-plugin.md](../runbooks/release-plugin.md), [setup-dependencies.md](../runbooks/setup-dependencies.md)

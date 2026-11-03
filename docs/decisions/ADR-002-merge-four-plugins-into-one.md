# ADR-002: Merge four plugins into one plugin with one namespace

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-03, my-plugins 1.0.0)

## Context
The skills were published as four plugins that users installed one by one: `aws-blog-skills@aws-blog-skills`,
`aws-diagrams@aws-diagrams`, `kor-writing@kor-writing` and `aws-deck@whchoi`. They depended on each other
across plugin boundaries:

- **Cross-plugin calls** — aws-blog-skills called `aws-diagrams:aws-diagram`, `aws-diagrams:aws-diagram-design`
  and `kor-writing:kor-deslop`; aws-ppt-skills drew its diagrams with the aws-diagrams skills. A missing plugin
  broke a step in the middle of a run.
- **Broken namespaces** — aws-ppt-skills called `/aws-diagram` and `/aws-diagram-design` without a plugin
  namespace, and the aws-diagram-design references named the commands `/aws-diagram-design:export-diagram` and
  so on, which never existed.
- **Diagram assets found by cache glob** — `diagram_lib.py` located the aws-diagram-design icons and fonts by
  globbing another plugin's cache folder. It sorted cache versions as strings, searched synced plugins only
  under `/root`, and a copy in a work folder had no stable way back to the assets.
- **Dependencies installed ad hoc** — each plugin left Playwright Chromium, fonts, LibreOffice, Poppler and
  pptxgenjs to the user. The deck fonts were installed only when a deck build ran, LibreOffice is not in the
  Amazon Linux 2023 repositories, and a global pptxgenjs install was not on `require()`'s search path.

## Options Considered

### Option 1: Keep four plugins, fix the names and document the dependencies
- **Pros**: smaller installs; each plugin versions on its own
- **Cons**: calls still cross plugin boundaries and fail when one plugin is missing; asset lookup still depends
  on another plugin's cache layout; four release flows

### Option 2: Copy the shared parts into each plugin
- **Pros**: each plugin works alone
- **Cons**: the diagram assets (about 7 MB) and rules are duplicated and drift apart; delegation turns into copying

### Option 3: One plugin with all skills (chosen)
- **Pros**: one install, one namespace, one version; skills find each other's files by relative path; one place
  for dependencies
- **Cons**: larger install; any skill change releases every skill; parts with different licenses ship together

## Decision
Ship one plugin, `my-plugins@my-plugins`, whose repo root is both the plugin and its marketplace
(`"source": "./"`), with eight skills and the three aws-diagrams commands.

- **One namespace** — cross-skill calls use `my-plugins:<skill>` (Skill tool) or `/my-plugins:<name>`. The old
  names (`aws-diagrams:`, `kor-writing:`, `aws-deck@`, `whchoi:`, `/aws-diagram-design:`, bare `/aws-diagram`)
  are rejected by the structure tests.
- **Sibling-relative asset paths** — `diagram_lib.py` reads `../aws-diagram-design/assets` from its own folder.
  When aws-blog-skills copies it into a work folder, it writes `.aws-diagram-assets` next to the copy. Plugin
  caches (numeric version order), synced copies and claude.ai container paths remain as fallbacks only.
  `setup` reaches the Amazon Ember fonts and the deck font installer the same way.
- **`setup` skill** — `skills/setup/scripts/setup.sh` checks by default, installs user-level tools with
  `install`, and system packages with `install --sudo` through `sudo -n` only. A new external tool or font is
  added there, in `skills/setup/SKILL.md` and in the README.
- **Licenses stay per part** — `NOTICE.md` and `third_party/` record the license of each source plugin.

## Consequences

### Positive
- One install and one update pair (`claude plugin marketplace update my-plugins`,
  `claude plugin update my-plugins@my-plugins`); a blog post draws its diagrams and runs kor-deslop without a
  second plugin, and a deck embeds the same diagrams
- A missing tool or font has one answer, `/my-plugins:setup`, including the Amazon Linux 2023 cases (Chromium
  system libraries, LibreOffice from the official RPM bundle)
- Asset lookup no longer depends on which other plugins are installed or how their cache folders are named

### Negative
- Users have to uninstall the four standalone plugins, or the same skills load twice under the old names
- Once the same-named local plugins are uninstalled, Claude Code loads the copies synced from the user's
  claude.ai account (`aws-diagrams@synced`, `kor-writing@synced`, `aws-deck@synced`); they come back until they
  are removed from the account or turned off with `skillOverrides` in `~/.claude/settings.json`
- The aws-deck parts had no license in their source repository; the author chose MIT for them when merging
  (`plugin.json` `license: MIT`). The bundled AWS templates and deck fonts stay under their own terms (`NOTICE.md`)
- The plugin is about 26 MB, mostly deck templates, fonts and icon sets, and every installer downloads all of it
- Always-on cost is the sum of every skill and command description, about 3.1k tokens per session
  (`claude --plugin-dir . plugin details my-plugins`, 2026-11-03), paid even by users of a single skill

## References
- `README.md` (Moving from the four plugins), `CHANGELOG.md` 1.0.0, `NOTICE.md`
- `skills/CLAUDE.md` (cross-skill links)
- `skills/aws-blog-skills/scripts/diagram_lib.py` (`find_assets()`), `skills/setup/scripts/setup.sh`
- [ADR-001](ADR-001-claude-code-skill-conventions.md), [architecture.md](../architecture.md),
  [setup-dependencies.md](../runbooks/setup-dependencies.md)

---

<a id="korean"></a>

# 한국어

## 상태
승인됨 (2026-11-03, my-plugins 1.0.0)

## 배경
skill들은 사용자가 하나씩 설치하는 플러그인 네 개(`aws-blog-skills@aws-blog-skills`, `aws-diagrams@aws-diagrams`, `kor-writing@kor-writing`, `aws-deck@whchoi`)로 배포되었고, 플러그인 경계를 넘어 서로에게 기대고 있었습니다.

- **플러그인을 넘는 호출** — aws-blog-skills는 `aws-diagrams:aws-diagram`, `aws-diagrams:aws-diagram-design`, `kor-writing:kor-deslop`을 불렀고, aws-ppt-skills는 aws-diagrams skill로 다이어그램을 그렸습니다. 플러그인 하나가 빠져 있으면 실행 도중 한 단계가 깨졌습니다.
- **깨진 이름 공간** — aws-ppt-skills는 `/aws-diagram`, `/aws-diagram-design`을 플러그인 이름 공간 없이 불렀고, aws-diagram-design references는 command를 존재한 적 없는 `/aws-diagram-design:export-diagram` 등으로 적었습니다.
- **캐시 glob으로 찾는 다이어그램 assets** — `diagram_lib.py`는 다른 플러그인의 캐시 폴더를 glob으로 뒤져 aws-diagram-design 아이콘과 폰트를 찾았습니다. 캐시 버전을 문자열로 정렬했고, 동기화 플러그인은 `/root`에서만 찾았으며, 작업 폴더로 복사한 사본은 assets로 돌아갈 확실한 경로가 없었습니다.
- **그때그때 설치하던 의존 프로그램** — 플러그인마다 Playwright Chromium, 폰트, LibreOffice, Poppler, pptxgenjs를 사용자에게 맡겼습니다. 덱 폰트는 덱을 빌드할 때만 설치되었고, Amazon Linux 2023 저장소에는 LibreOffice가 없으며, 전역으로 설치한 pptxgenjs는 `require()`가 찾지 못했습니다.

## 검토한 옵션

### 옵션 1: 플러그인 네 개를 유지하고 이름을 고친 뒤 의존 관계를 문서화
- **장점**: 설치본이 작고, 플러그인마다 버전을 따로 관리합니다
- **단점**: 호출이 여전히 플러그인 경계를 넘고 플러그인 하나가 없으면 실패합니다. assets 탐색이 여전히 다른 플러그인의 캐시 구조에 기대며, 릴리스 절차가 네 벌입니다

### 옵션 2: 공용 부분을 플러그인마다 복사
- **장점**: 플러그인마다 혼자 동작합니다
- **단점**: 다이어그램 assets(약 7 MB)와 규칙이 중복되어 서로 달라지고, 위임이 복사로 바뀝니다

### 옵션 3: 모든 skill을 담은 플러그인 하나 (선택)
- **장점**: 설치, 이름 공간, 버전이 하나입니다. skill끼리 상대 경로로 파일을 찾고, 의존 프로그램을 한곳에서 다룹니다
- **단점**: 설치본이 커지고, skill 하나만 바뀌어도 모든 skill이 함께 릴리스되며, 라이선스가 다른 부분이 함께 배포됩니다

## 결정
저장소 루트가 플러그인이자 마켓플레이스(`"source": "./"`)인 플러그인 하나, `my-plugins@my-plugins`를 배포합니다. skill 8개와 aws-diagrams의 command 3개를 담습니다.

- **이름 공간 하나** — skill 사이의 호출은 `my-plugins:<skill>`(Skill 도구) 또는 `/my-plugins:<name>`을 씁니다. 예전 이름(`aws-diagrams:`, `kor-writing:`, `aws-deck@`, `whchoi:`, `/aws-diagram-design:`, 이름 공간 없는 `/aws-diagram`)은 구조 테스트가 막습니다.
- **옆 skill 기준 assets 경로** — `diagram_lib.py`는 자기 폴더 기준 `../aws-diagram-design/assets`를 읽습니다. aws-blog-skills가 작업 폴더로 복사할 때는 사본 옆에 `.aws-diagram-assets`를 씁니다. 플러그인 캐시(버전 숫자 순), 동기화 사본, claude.ai 컨테이너 경로는 대비책으로만 남깁니다. `setup`도 같은 방식으로 Amazon Ember 폰트와 덱 폰트 설치 스크립트를 찾습니다.
- **`setup` skill** — `skills/setup/scripts/setup.sh`는 기본으로 점검만 하고, `install`로 사용자 영역 도구를, `install --sudo`로 시스템 패키지를 `sudo -n`으로만 설치합니다. 새 외부 프로그램이나 폰트는 이 스크립트, `skills/setup/SKILL.md`, README에 추가합니다.
- **라이선스는 부분별로 유지** — `NOTICE.md`와 `third_party/`에 원래 플러그인마다의 라이선스를 기록합니다.

## 영향

### 긍정적
- 설치 한 번과 갱신 명령 한 쌍(`claude plugin marketplace update my-plugins`, `claude plugin update my-plugins@my-plugins`)으로 끝납니다. 블로그 원고가 다른 플러그인 없이 다이어그램을 그리고 kor-deslop을 실행하며, 덱도 같은 다이어그램을 넣습니다
- 도구나 폰트가 없을 때의 답이 `/my-plugins:setup` 하나입니다. Amazon Linux 2023의 경우(Chromium 시스템 라이브러리, 공식 RPM 묶음의 LibreOffice)도 포함합니다
- assets 탐색이 다른 플러그인의 설치 여부나 캐시 폴더 이름에 기대지 않습니다

### 부정적
- 사용자는 단독 플러그인 네 개를 제거해야 합니다. 그렇지 않으면 같은 skill이 예전 이름으로 두 번 로드됩니다
- 이름이 같은 로컬 플러그인을 제거하면 Claude Code가 사용자의 claude.ai 계정에서 동기화된 사본(`aws-diagrams@synced`, `kor-writing@synced`, `aws-deck@synced`)을 불러옵니다. 계정에서 제거하거나 `~/.claude/settings.json`의 `skillOverrides`로 끄기 전까지 다시 나타납니다
- aws-deck 부분은 원 저장소에 라이선스가 없었고, 통합하면서 저작자가 MIT로 정했습니다(`plugin.json` `license: MIT`). 함께 든 AWS 템플릿과 덱 폰트는 각자의 이용 조건을 따릅니다(`NOTICE.md`)
- 플러그인 크기가 약 26 MB이고 대부분 덱 템플릿, 폰트, 아이콘 묶음입니다. 설치하는 사람은 모두 전부를 내려받습니다
- 항상 로드되는 비용은 모든 skill과 command description의 합으로 세션마다 약 3.1k 토큰입니다(`claude --plugin-dir . plugin details my-plugins`, 2026-11-03 측정). skill 하나만 쓰는 사용자도 이 비용을 냅니다

## 참고 자료
- `README.md`(네 플러그인에서 옮겨 올 때), `CHANGELOG.md` 1.0.0, `NOTICE.md`
- `skills/CLAUDE.md`(skill 사이의 연결)
- `skills/aws-blog-skills/scripts/diagram_lib.py`(`find_assets()`), `skills/setup/scripts/setup.sh`
- [ADR-001](ADR-001-claude-code-skill-conventions.md), [architecture.md](../architecture.md), [setup-dependencies.md](../runbooks/setup-dependencies.md)

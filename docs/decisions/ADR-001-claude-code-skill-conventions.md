# ADR-001: aws-blog-skills targets Claude Code in SKILL.md and checks the assembled bundle

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-01, aws-blog-skills 1.2.0). Carried into my-plugins 1.0.0, where it applies to the
`skills/aws-blog-skills/` skill; the other skills keep the conventions of their source plugins.

## Context
The aws-blog-skills skill was written in claude.ai, where a container provides `present_files`, `/mnt/user-data/outputs/`,
`web_fetch`, `view` and root access. Running 1.1.0 in Claude Code reproduced five failures: the packaging
script could not copy to `/mnt/user-data/outputs`, the structure check never found images (it looked under
`drafts/images/` while images lived in `<workdir>/images/`), Playwright had no install or run path, fonts
were installed into a root-only folder, and the example generator wrote into the skill folder, which in
Claude Code is the plugin cache that updates replace. URL checks by status code also passed for missing
docs.aws.amazon.com pages, which redirect to the guide root with HTTP 200.

## Options Considered

### Option 1: Keep claude.ai paths and document the differences in README
- **Pros**: no change to the skill; the same text works in claude.ai
- **Cons**: every Claude Code run fails at packaging; the model has to improvise paths each time

### Option 2: One SKILL.md for both runtimes with branches
- **Pros**: one copy to maintain
- **Cons**: every step doubles; the model must detect its runtime; the always-on description and body grow

### Option 3: Target Claude Code only (chosen)
- **Pros**: one set of instructions that the harness can test end to end; scripts take explicit paths
- **Cons**: the claude.ai copy diverges and is maintained separately (synced `anthropic-skills:aws-blog-skills`)

## Decision
`skills/aws-blog-skills/SKILL.md` targets Claude Code. Scripts are called as `${CLAUDE_SKILL_DIR}/scripts/...`; all output goes to the
work folder `<YYYY-MM-DD>-<slug>/` with `drafts/images -> ../images`; nothing is written into the skill
folder. `package_blog.sh` assembles the bundle first and runs the checks on that copy, writing no zip on
failure. A new `check_urls.py` treats a redirect to a different page as a failure. Rendering runs through
`uv run --no-project --with playwright`, and fonts go to the user font folder.

## Consequences
### Positive
- The whole pipeline ran in a fresh folder: 4 diagrams rendered with `fonts: True overflow: []`, URL,
  structure and lint checks passed, and the zip held the md, 4 PNG and 4 SVG files
- `tests/structure/test-aws-blog-skills-scripts.sh` guards these contracts, including the soft-404 case

### Negative
- claude.ai users need the older text; the synced copy has to be kept apart and disabled where my-plugins is installed
- `${CLAUDE_SKILL_DIR}` is not substituted inside reference files, so SKILL.md has to say how to read them

## References
- `skills/aws-blog-skills/SKILL.md` (실행 환경 section)
- `skills/aws-blog-skills/scripts/package_blog.sh`, `check_urls.py`, `render_diagrams.py`
- Commit `d1831b9` in the aws-blog-skills repository (Port aws-blog-skills skill to Claude Code)
- [ADR-002](ADR-002-merge-four-plugins-into-one.md): the merge that brought this skill into my-plugins

---

<a id="korean"></a>

# 한국어

## 상태
승인됨 (2026-11-01, aws-blog-skills 1.2.0). my-plugins 1.0.0에 그대로 옮겨 왔으며 `skills/aws-blog-skills/` skill에 적용됩니다. 다른 skill은 원래 플러그인의 규칙을 따릅니다.

## 배경
aws-blog-skills skill은 claude.ai에서 작성되었습니다. claude.ai 컨테이너에는 `present_files`, `/mnt/user-data/outputs/`, `web_fetch`, `view`와 root 권한이 있습니다. 1.1.0을 Claude Code에서 실행하자 다섯 가지 실패가 재현되었습니다. 패키징 스크립트가 `/mnt/user-data/outputs`로 복사하지 못했고, 구조 검사가 그림을 찾지 못했습니다(그림은 `<workdir>/images/`에 있는데 `drafts/images/`에서 찾음). Playwright 설치와 실행 방법이 없었고, 폰트를 root 전용 폴더에 설치하려 했으며, 예시 생성기가 skill 폴더에 파일을 썼습니다. Claude Code에서 skill 폴더는 업데이트 때 교체되는 플러그인 캐시입니다. 또한 docs.aws.amazon.com은 없는 페이지를 가이드 첫 페이지로 리디렉션하면서 HTTP 200을 돌려주므로, 상태 코드만으로 하는 URL 검사가 깨진 링크를 통과시켰습니다.

## 검토한 옵션

### 옵션 1: claude.ai 경로를 유지하고 차이를 README에 적기
- **장점**: skill을 바꾸지 않고, 같은 본문이 claude.ai에서도 동작합니다
- **단점**: Claude Code에서는 매번 패키징 단계에서 실패하고, 모델이 매번 경로를 임의로 바꿔야 합니다

### 옵션 2: 두 실행 환경을 분기하는 SKILL.md 하나
- **장점**: 관리할 사본이 하나입니다
- **단점**: 모든 단계가 두 배가 되고, 모델이 실행 환경을 판별해야 하며, 항상 로드되는 description과 본문이 커집니다

### 옵션 3: Claude Code만 대상으로 하기 (선택)
- **장점**: 하네스가 처음부터 끝까지 테스트할 수 있는 지침 한 벌이 되고, 스크립트가 명시적인 경로를 받습니다
- **단점**: claude.ai 사본은 갈라져 따로 관리됩니다(동기화되는 `anthropic-skills:aws-blog-skills`)

## 결정
`skills/aws-blog-skills/SKILL.md`는 Claude Code를 대상으로 합니다. 스크립트는 `${CLAUDE_SKILL_DIR}/scripts/...`로 부르고, 모든 결과는 작업 폴더 `<YYYY-MM-DD>-<slug>/`(`drafts/images -> ../images`)에 쓰며, skill 폴더에는 아무것도 쓰지 않습니다. `package_blog.sh`는 번들을 먼저 조립하고 조립본에 검사를 실행하며, 실패하면 zip을 만들지 않습니다. 새 `check_urls.py`는 다른 페이지로의 리디렉션을 실패로 봅니다. 렌더링은 `uv run --no-project --with playwright`로 실행하고, 폰트는 사용자 폰트 폴더에 설치합니다.

## 결과
### 긍정적
- 새 폴더에서 전체 파이프라인이 돌아갔습니다. 그림 4장이 `fonts: True overflow: []`로 렌더되었고, URL, 구조, lint 검사를 통과했으며, zip에 md, PNG 4개, SVG 4개가 들어갔습니다
- 이제 `tests/structure/test-aws-blog-skills-scripts.sh`가 soft 404를 포함한 이 계약들을 지킵니다

### 부정적
- claude.ai 사용자는 이전 본문이 필요하며, 동기화 사본은 따로 두고 my-plugins가 설치된 곳에서는 비활성화해야 합니다
- `${CLAUDE_SKILL_DIR}`는 참조 파일 안에서 치환되지 않으므로 SKILL.md가 읽는 방법을 안내해야 합니다

## 참고 자료
- `skills/aws-blog-skills/SKILL.md`(실행 환경 절)
- `skills/aws-blog-skills/scripts/package_blog.sh`, `check_urls.py`, `render_diagrams.py`
- aws-blog-skills 저장소의 커밋 `d1831b9`(Port aws-blog-skills skill to Claude Code)
- [ADR-002](ADR-002-merge-four-plugins-into-one.md): 이 skill을 my-plugins로 옮긴 통합 결정

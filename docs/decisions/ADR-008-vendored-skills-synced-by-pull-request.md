# ADR-008: Skills from other repositories are vendored and synced by pull request

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-21)

## Context
The user asked for two skills of other authors inside my-plugins: heydamir/unslop as the skill that removes AI
slop from UI, and blader/humanizer as the skill that removes AI slop from English text. Each gets a name and a
description of this plugin, and each is to follow its repository: the sources are checked regularly and the
skills are updated.

Every skill so far is the author's own work. These two are not: unslop is CC BY 4.0 (Damir Sokolovsky),
humanizer is MIT (Siqi Chen). A skill is also text that Claude follows on every installer's machine, and unslop
ships three Node.js scripts. A change in a source is therefore a change of instructions, and of code, for every
user of the plugin.

## Options Considered

### Option 1: Tell users to install the two plugins themselves
- **Pros**: nothing to maintain; updates come from the authors' marketplaces
- **Cons**: the request was one plugin; the names and descriptions stay the authors', so the skills do not route
  next to kor-deslop ("UI의 AI 슬롭 제거", "영어 글의 AI 슬롭 제거")

### Option 2: Git submodule or subtree
- **Pros**: git records the source commit
- **Cons**: Claude Code copies the plugin folder, and a submodule is empty in a marketplace clone that does not
  fetch it; the frontmatter cannot be changed without a fork; a subtree brings the whole repository (README,
  examples, tests, CI files) into the shipped plugin

### Option 3: Copy once and edit freely
- **Pros**: the body can be adapted to this plugin
- **Cons**: every later update is a manual merge, so the copy falls behind; an edited copy of CC BY 4.0 work has
  to track every change it made

### Option 4: Vendor at a pinned commit, sync with a script, review by pull request
- **Pros**: the body and every other file are the source's bytes, so an update is a copy; the pin and a hash per
  file make a hand edit and a silent change visible; a person reads the diff before it reaches `main`
- **Cons**: a manifest, a script and a workflow to maintain; a fix that belongs in the body has to go to the
  source's repository

### Option 5: Option 4 with automatic merge and release
- **Pros**: nothing to do by hand
- **Cons**: text and scripts from two outside repositories would reach every installer unread; a compromised or
  careless source becomes an instruction to Claude on users' machines

## Decision
Option 4.

- The skills are `skills/ui-deslop/` (heydamir/unslop, folder `skills/unslop/`, without `agents/`) and
  `skills/eng-deslop/` (blader/humanizer, `SKILL.md` only). The names follow `kor-deslop`.
- `scripts/upstream-skills.json` records per skill the source, the folder, the files to take, the allowed file
  types, the license, the `name` and `description` of this plugin, the pinned commit and a SHA-256 of every file.
- `scripts/sync_upstream_skills.py` is the only writer of the two folders. `update` copies the source, replaces
  the frontmatter `name` and `description`, adds `upstream`, `upstream-commit` and `modified` to `metadata`,
  copies the license to `third_party/LICENSE-<skill>` and adds a line to `[Unreleased]` in both languages.
  `render` writes a description that was changed in the manifest. `verify` fails when a file differs from the
  manifest. `check` reports whether a source has changed.
- `update` refuses a source whose license field changed, a symbolic link, a hidden file, a file type that is not
  in `allow_ext`, an unusual file name and a file over 2 MB. It copies files and never runs one.
- `.github/workflows/sync-upstream-skills.yml` runs `update` every Monday. When something changed it runs
  `verify` and the upstream-skills tests, pushes the branch `sync/upstream-skills` and opens a pull request with
  a report of the changed files, the changed scripts and the new links. When the repository does not let Actions
  open pull requests it opens an issue with the link. It never merges, tags or releases.
- A release stays the maintainer's step (`docs/runbooks/release-plugin.md`).
- Node Playwright and ffmpeg, which ui-deslop uses for two optional features, are left to the user. `setup`
  reports ffmpeg and counts nothing as missing.

## Consequences

### Positive
- One install gives three deslop skills that route to each other: Korean text, English text and UI
- An update of a source costs one review of a diff; nothing is merged by hand
- A hand edit, a changed license, a new kind of file and an unreviewed update each stop at a test or at the script
- The authors' credit, license texts and the list of changes ship with the copy (`NOTICE.md`, `third_party/`,
  the `metadata` of each SKILL.md)

### Negative
- The body of a vendored skill cannot follow this plugin's rules (Korean wording rules, `my-plugins:` cross
  references inside the body, `setup` for dependencies); only the description can
- The workflow needs GitHub Actions. A scheduled workflow stops after 60 days without repository activity, and
  pull requests from Actions need a repository setting; without it the workflow leaves an issue
- A user who also installs the sources as plugins has two skills for the same request
- ui-deslop adds about 1.4 MB of reference images to the plugin

## References
- `scripts/sync_upstream_skills.py`, `scripts/upstream-skills.json`, `.github/workflows/sync-upstream-skills.yml`
- `tests/structure/test-upstream-skills.sh`, `docs/runbooks/sync-upstream-skills.md`
- `NOTICE.md`, `third_party/LICENSE-ui-deslop`, `third_party/LICENSE-eng-deslop`
- [heydamir/unslop](https://github.com/heydamir/unslop), [blader/humanizer](https://github.com/blader/humanizer)

---

<a id="korean"></a>

# 한국어

## 상태
승인됨 (2026-11-21)

## 배경
사용자가 다른 저작자의 skill 두 개를 my-plugins에 넣어 달라고 요청했습니다. heydamir/unslop은 UI의 AI 슬롭을
제거하는 skill로, blader/humanizer는 영어 글의 AI 슬롭을 제거하는 skill로 넣고, 이름과 description은 이
플러그인의 것으로 바꿉니다. 두 skill은 원본 저장소를 따라가야 합니다. 원본을 정기적으로 확인해 skill을
갱신합니다.

지금까지의 skill은 모두 저작자 본인의 것이었습니다. 이 둘은 다릅니다. unslop은 CC BY 4.0(Damir Sokolovsky),
humanizer는 MIT(Siqi Chen)입니다. 또 skill은 설치한 사람의 머신에서 Claude가 따르는 글이고, unslop에는 Node.js
스크립트 세 개가 있습니다. 원본이 바뀌면 플러그인 사용자 모두가 받는 지시문과 코드가 바뀝니다.

## 검토한 옵션

### 옵션 1: 두 플러그인을 사용자가 직접 설치하게 하기
- **장점**: 관리할 것이 없음. 갱신은 저작자의 마켓플레이스에서 옴
- **단점**: 요청은 플러그인 하나였음. 이름과 description이 저작자의 것 그대로라 kor-deslop 옆에서 "UI의 AI 슬롭
  제거", "영어 글의 AI 슬롭 제거"로 안내되지 않음

### 옵션 2: git submodule 또는 subtree
- **장점**: 원본 커밋이 git에 기록됨
- **단점**: Claude Code는 플러그인 폴더를 복사하는데, submodule은 받아 오지 않는 마켓플레이스 클론에서 비어
  있음. fork 없이는 frontmatter를 바꿀 수 없음. subtree는 저장소 전체(README, 예제, 테스트, CI 파일)를 배포되는
  플러그인에 넣음

### 옵션 3: 한 번 복사하고 자유롭게 수정하기
- **장점**: 본문을 이 플러그인에 맞출 수 있음
- **단점**: 이후 갱신이 모두 수동 병합이라 복사본이 뒤처짐. CC BY 4.0 저작물을 수정하면 바꾼 내용을 모두
  기록해야 함

### 옵션 4: 고정한 커밋에서 가져오고, 스크립트로 동기화하고, pull request로 검토하기
- **장점**: 본문과 다른 파일이 모두 원본 그대로라 갱신이 복사로 끝남. 커밋과 파일별 해시로 손으로 한 수정과
  알리지 않은 변경이 드러남. `main`에 들어가기 전에 사람이 변경 내용을 읽음
- **단점**: 매니페스트, 스크립트, 워크플로를 관리해야 함. 본문에서 수정할 것은 원본 저장소에 요청해야 함

### 옵션 5: 옵션 4에 자동 병합과 릴리스 더하기
- **장점**: 손으로 할 일이 없음
- **단점**: 외부 저장소 두 곳의 글과 스크립트가 아무도 읽지 않은 채 모든 설치자에게 전달됨. 원본이 침해되거나
  부주의하게 바뀌면 그대로 사용자 머신의 Claude가 따르는 지시가 됨

## 결정
옵션 4를 택합니다.

- skill은 `skills/ui-deslop/`(heydamir/unslop의 `skills/unslop/` 폴더, `agents/` 제외)과
  `skills/eng-deslop/`(blader/humanizer의 `SKILL.md`만)입니다. 이름은 `kor-deslop`을 따릅니다.
- `scripts/upstream-skills.json`이 skill마다 원본, 폴더, 가져올 파일, 허용하는 파일 형식, 라이선스, 이 플러그인의
  `name`과 `description`, 고정한 커밋, 파일별 SHA-256을 기록합니다.
- 두 폴더에 쓰는 것은 `scripts/sync_upstream_skills.py`뿐입니다. `update`는 원본을 복사하고, frontmatter의
  `name`과 `description`을 바꾸고, `metadata`에 `upstream`, `upstream-commit`, `modified`를 더하고, 라이선스를
  `third_party/LICENSE-<skill>`로 복사하고, 두 언어의 `[Unreleased]`에 한 줄을 넣습니다. `render`는 매니페스트에서
  바꾼 description을 SKILL.md에 반영합니다. `verify`는 파일이 매니페스트와 다르면 실패합니다. `check`는 원본이 바뀌었는지
  알립니다.
- `update`는 라이선스 항목이 바뀐 원본, 심볼릭 링크, 숨김 파일, `allow_ext`에 없는 파일 형식, 특이한 파일 이름,
  2 MB를 넘는 파일을 거부합니다. 파일을 복사할 뿐 실행하지 않습니다.
- `.github/workflows/sync-upstream-skills.yml`이 매주 월요일 `update`를 실행합니다. 바뀐 것이 있으면 `verify`와
  upstream-skills 테스트를 실행하고, `sync/upstream-skills` 브랜치를 push하고, 바뀐 파일, 바뀐 스크립트, 새
  링크를 적은 보고서와 함께 pull request를 엽니다. 저장소 설정에서 Actions의 pull request 생성을 허용하지
  않았으면 링크를 담은 issue를 엽니다. 병합, 태그, 릴리스는 하지 않습니다.
- 릴리스는 관리자가 합니다(`docs/runbooks/release-plugin.md`).
- ui-deslop의 선택 기능 두 가지가 쓰는 Node Playwright와 ffmpeg는 사용자에게 맡깁니다. `setup`은 ffmpeg가 있는지
  알리기만 하고 빠진 항목으로 세지 않습니다.

## 영향

### 긍정적
- 한 번 설치하면 서로를 안내하는 deslop skill 세 개(한국어 글, 영어 글, UI)를 사용합니다
- 원본 갱신에 드는 일이 변경 내용을 한 번 읽는 것으로 끝납니다. 손으로 병합하지 않습니다
- 손으로 한 수정, 바뀐 라이선스, 새 파일 형식, 검토하지 않은 갱신은 각각 테스트나 스크립트에서 멈춥니다
- 저작자 표시, 라이선스 원문, 변경 내용이 복사본과 함께 배포됩니다(`NOTICE.md`, `third_party/`, 각 SKILL.md의
  `metadata`)

### 부정적
- 가져온 skill의 본문은 이 플러그인의 규칙(한국어 낱말 규칙, 본문 안의 `my-plugins:` 참조, 의존 프로그램을
  `setup`으로 설치)을 따르지 못합니다. description만 맞출 수 있습니다
- 워크플로는 GitHub Actions가 있어야 합니다. 예약 워크플로는 저장소 활동이 60일 동안 없으면 멈추고, Actions가
  pull request를 열려면 저장소 설정이 필요합니다. 설정이 없으면 issue를 남깁니다
- 원본 플러그인을 함께 설치한 사용자는 같은 요청에 skill 두 개가 반응합니다
- ui-deslop의 참고 이미지 때문에 플러그인이 약 1.4 MB 커집니다

## 참고 자료
- `scripts/sync_upstream_skills.py`, `scripts/upstream-skills.json`, `.github/workflows/sync-upstream-skills.yml`
- `tests/structure/test-upstream-skills.sh`, `docs/runbooks/sync-upstream-skills.md`
- `NOTICE.md`, `third_party/LICENSE-ui-deslop`, `third_party/LICENSE-eng-deslop`
- [heydamir/unslop](https://github.com/heydamir/unslop), [blader/humanizer](https://github.com/blader/humanizer)

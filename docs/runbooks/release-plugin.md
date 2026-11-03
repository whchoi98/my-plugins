# Runbook: Release the Plugin

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Overview
Publish a new version of `my-plugins` to everyone who installed it from GitHub. Installed copies are keyed by
`.claude-plugin/plugin.json` `version`; a push without a version change reaches nobody. All eight skills and
three commands share that one version.

## When to Use
- Any change under `skills/` (any skill's SKILL.md, references, scripts, templates, assets) or `commands/`
- A shipped doc change users should see (README install or migration steps)
- Not needed for harness-only changes (`.claude/`, `tests/`, `scripts/`, `docs/`)

## Prerequisites
- Push access to `github.com/whchoi98/my-plugins`
- Claude Code CLI

## Procedure

### 1. Check the tree
```bash
git status                     # clean
git branch --show-current      # main
bash tests/run-all.sh
claude plugin validate .       # one ICON_MISSING warning is expected
```

### 2. Pick the version
```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```
MAJOR: a skill or command is renamed or removed, a `/my-plugins:<name>` invocation changes, or a work-folder
layout, deliverable set or script argument changes incompatibly. MINOR: new skill, command, workflow step,
reference file, script, confirmed rule, or a new dependency in `setup`. PATCH: wording, lint terms, script bug
fixes, doc-only changes that ship.

### 3. Update the version everywhere
- `.claude-plugin/plugin.json` `version`
- README badge `Version-X.Y.Z-green`
- `CHANGELOG.md`: move `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` in both language sections; add the compare
  links at the bottom of both sections

### 4. Verify, commit, tag, push
```bash
bash tests/run-all.sh structure
git commit -am "chore: release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --follow-tags     # public: confirm with the maintainer first
```
Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`) and carry no
`Co-Authored-By` trailer; `.claude/settings.json` attribution is empty and the `commit-msg` hook strips it.

### 5. Refresh the installed copy
```bash
claude plugin marketplace update my-plugins
claude plugin update my-plugins@my-plugins
```
Then `/reload-plugins` or restart. The marketplace update alone does not move the installed version.

## Verification
- `git ls-remote --tags origin vX.Y.Z` returns the tag
- `claude plugin list` shows `my-plugins@my-plugins` at `X.Y.Z`
- `claude plugin details my-plugins@my-plugins` lists 11 entries under Skills: the eight skills and the three commands
- `diff -rq ~/.claude/plugins/cache/my-plugins/my-plugins/X.Y.Z/skills skills` prints nothing

## Rollback
```bash
git revert <sha>
# then repeat this runbook with the next PATCH version
```
Never reuse or delete a published version number.

## Notes
- Copies synced from claude.ai (`anthropic-skills:aws-blog-skills`, `aws-diagrams@synced`, `kor-writing@synced`,
  `aws-deck@synced`) are separate; this runbook does not update them.

---

<a id="korean"></a>

# 한국어

## 개요
GitHub에서 `my-plugins`를 설치한 모든 사용자에게 새 버전을 배포합니다. 설치본은 `.claude-plugin/plugin.json`의 `version`을 기준으로 갱신되므로, 버전을 바꾸지 않은 push는 아무에게도 전달되지 않습니다. skill 8개와 command 3개가 이 버전 하나를 함께 씁니다.

## 사용 시점
- `skills/` 아래의 모든 변경(어느 skill이든 SKILL.md, 참조 파일, 스크립트, 템플릿, assets)과 `commands/` 변경
- 사용자가 봐야 하는 배포 문서 변경(README 설치나 이전 절차)
- 하네스만 바꾼 경우(`.claude/`, `tests/`, `scripts/`, `docs/`)에는 필요 없습니다

## 사전 요구 사항
- `github.com/whchoi98/my-plugins` push 권한
- Claude Code CLI

## 절차

### 1. 작업 트리 확인
```bash
git status                     # clean
git branch --show-current      # main
bash tests/run-all.sh
claude plugin validate .       # one ICON_MISSING warning is expected
```

### 2. 버전 결정
```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```
MAJOR: skill이나 command의 이름이 바뀌거나 빠질 때, `/my-plugins:<name>` 호출 방식이 바뀔 때, 작업 폴더 구조, 결과물 구성, 스크립트 인자가 호환되지 않게 바뀔 때. MINOR: 새 skill, command, 워크플로 단계, 참조 파일, 스크립트, 확정 규칙, `setup`의 새 의존 프로그램. PATCH: 문구, lint 용어, 스크립트 버그 수정, 배포되는 문서만 바꾼 경우.

### 3. 모든 위치의 버전 갱신
- `.claude-plugin/plugin.json`의 `version`
- README 배지 `Version-X.Y.Z-green`
- `CHANGELOG.md`: 두 언어 섹션 모두 `[Unreleased]`를 `[X.Y.Z] - YYYY-MM-DD`로 옮기고, 두 섹션 아래에 비교 링크를 추가합니다

### 4. 검증, 커밋, 태그, push
```bash
bash tests/run-all.sh structure
git commit -am "chore: release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --follow-tags     # public: confirm with the maintainer first
```
커밋 메시지는 Conventional Commits(`feat:`, `fix:`, `docs:`, `chore:`)를 따르고 `Co-Authored-By` 줄을 넣지 않습니다. `.claude/settings.json`의 attribution이 비어 있고 `commit-msg` 훅이 이 줄을 지웁니다.

### 5. 설치된 사본 갱신
```bash
claude plugin marketplace update my-plugins
claude plugin update my-plugins@my-plugins
```
그다음 `/reload-plugins`를 실행하거나 재시작합니다. 마켓플레이스 갱신만으로는 설치 버전이 바뀌지 않습니다.

## 검증
- `git ls-remote --tags origin vX.Y.Z`가 태그를 돌려줍니다
- `claude plugin list`에 `my-plugins@my-plugins`가 `X.Y.Z`로 보입니다
- `claude plugin details my-plugins@my-plugins`의 Skills에 skill 8개와 command 3개, 모두 11개가 나옵니다
- `diff -rq ~/.claude/plugins/cache/my-plugins/my-plugins/X.Y.Z/skills skills`가 아무것도 출력하지 않습니다

## 롤백
```bash
git revert <sha>
# then repeat this runbook with the next PATCH version
```
배포한 버전 번호는 다시 쓰거나 지우지 않습니다.

## 참고
- claude.ai에서 동기화되는 사본(`anthropic-skills:aws-blog-skills`, `aws-diagrams@synced`, `kor-writing@synced`, `aws-deck@synced`)은 별도 사본이며, 이 런북으로 갱신되지 않습니다.

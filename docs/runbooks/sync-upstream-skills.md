# Runbook: Sync the Vendored Skills with Their Sources

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Overview
Two skills are copies of other authors' repositories: `skills/ui-deslop/` from heydamir/unslop (CC BY 4.0) and
`skills/eng-deslop/` from blader/humanizer (MIT). `scripts/upstream-skills.json` pins each to a commit and holds a
hash of every file and the `name` and `description` my-plugins gives the skill. `scripts/sync_upstream_skills.py`
is the only thing that writes those two folders ([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).

| Command | Effect |
|---|---|
| `python3 scripts/sync_upstream_skills.py check` | Compares the sources with the manifest. Writes nothing. Exit 10 when a skill has an update |
| `python3 scripts/sync_upstream_skills.py update` | Copies a changed source in; writes the frontmatter, the license copy, the manifest and the `[Unreleased]` line. `--report FILE` saves what changed |
| `python3 scripts/sync_upstream_skills.py render` | Writes the `name` and `description` of the manifest into SKILL.md again |
| `python3 scripts/sync_upstream_skills.py verify` | Offline. Fails when a vendored file differs from the manifest |

`--skill NAME` limits a command to one skill. `--source DIR` uses a local checkout in place of a download.

## When to Use
- The weekly workflow opened a pull request or an issue named "Sync vendored skills with their sources"
- You want to look for an update without waiting for Monday
- The description of a vendored skill needs a change
- A third skill from another repository is added

## Prerequisites
- python3 and git; network access to github.com for `check` and `update`
- For the workflow: GitHub Actions enabled on the repository

## Procedure

### 1. The weekly workflow
`.github/workflows/sync-upstream-skills.yml` runs every Monday at 06:23 in Seoul, and by hand from the Actions
tab ("Run workflow") or with `gh workflow run sync-upstream-skills.yml`. It runs `update`. When nothing changed
it ends there. Otherwise it runs `verify` and `bash tests/run-all.sh upstream-skills`, pushes the branch
`sync/upstream-skills` and opens a pull request whose text is the report. It never merges or releases.

If the repository does not let Actions open pull requests, the workflow opens an issue with a link that opens
the pull request. To let it open pull requests itself: Settings, Actions, General, "Allow GitHub Actions to
create and approve pull requests".

### 2. Review the pull request
A skill is text that Claude follows on a user's machine, so read the whole diff. The report lists what to read
first.

- **Scripts** (`skills/ui-deslop/scripts/*.mjs`): what they open, write, delete and run
- **New links**: every address that was not in the skill before
- **SKILL.md and references**: an instruction that reads files outside the project, sends data somewhere, installs
  something or tells Claude to skip a confirmation is a reason to stop
- **"The source changed its own description"**: read the new text and decide whether `description` in the
  manifest still says what the skill does (step 4)

Reject the update by closing the pull request. The copy stays at the pinned commit, and the workflow proposes
the newer state again the next week.

### 3. Sync by hand
```bash
python3 scripts/sync_upstream_skills.py check          # exit 10: an update is available
python3 scripts/sync_upstream_skills.py update --report /tmp/sync-report.md
git diff --stat && git diff skills/ui-deslop skills/eng-deslop    # read it as in step 2
bash tests/run-all.sh                                  # the full suite before a release
```

### 4. Change a description
Edit `description` of the skill in `scripts/upstream-skills.json` (one line, 50 to 1,536 characters), then:
```bash
python3 scripts/sync_upstream_skills.py render --skill ui-deslop
python3 scripts/sync_upstream_skills.py verify
```
Never edit SKILL.md of a vendored skill. Add a line to `[Unreleased]` of CHANGELOG.md in both languages.

### 5. Release
A sync changes files under `skills/`, so it reaches users only with a release
([release-plugin.md](release-plugin.md)). `update` has already added the `[Unreleased]` line; a sync alone is a
PATCH or MINOR release by what the source changed.

### 6. Add a skill from another repository
1. Read the source: SKILL.md, the references, every script. Check its license allows copying and adapting.
2. Add an entry to `scripts/upstream-skills.json`: `name`, `repo` (owner/name), `ref` (`HEAD` for the default
   branch), `path`, `include` or `exclude`, `allow_ext`, `license`, `license_file`, `changes`, `description`.
3. `python3 scripts/sync_upstream_skills.py update --skill <name> --no-changelog`, then `verify`.
4. Register it as a new skill (CLAUDE.md "Change Sync Rules"), add a NOTICE.md row and the expected names in
   `tests/structure/test-upstream-skills.sh`.

## When `update` Refuses
`update` exits 1, prints `REFUSED` and writes nothing for that skill. In the workflow the run fails and GitHub
sends the failure notice.

| Message | What to do |
|---|---|
| `the source's license is ..., the manifest says ...` | Read the new terms. If copying and adapting are still allowed, change `license` in the manifest and update NOTICE.md; otherwise keep the pinned copy |
| `has a file type the manifest does not allow` | Read the file. If it belongs in the skill, add the extension to `allow_ext` |
| `is a symbolic link`, `is a hidden file`, `is an unusual file name` | Look at the source. Name the path in `exclude` when the skill works without it |
| `is ... bytes, over the limit` | Decide whether the plugin should carry the file; `max_file_bytes` in the entry raises the limit |
| `the source's metadata already has ...` | The source started to use a metadata key of this plugin; rename the key in `OUR_META` of the script |

## Verification
- `python3 scripts/sync_upstream_skills.py verify` prints `OK` for both skills
- `bash tests/run-all.sh upstream-skills` passes; `bash tests/run-all.sh` before a release
- `claude plugin validate .` passes

## Rollback
- Before a merge: close the pull request and delete the branch `sync/upstream-skills`
- After a merge: `git revert` the sync commit. The manifest goes back with it, so `verify` passes again
- To stop the weekly run: Actions tab, "Sync upstream skills", "Disable workflow"

## Notes
- GitHub disables a scheduled workflow after 60 days without activity in the repository; enable it again in the
  Actions tab
- The workflow copies files and never runs one. The tests it runs parse the scripts with `node --check` only
- A pull request opened with the workflow's token does not start other workflows

---

<a id="korean"></a>

# 한국어

## 개요
skill 두 개는 다른 저작자의 저장소를 복사한 것입니다. `skills/ui-deslop/`은 heydamir/unslop(CC BY 4.0),
`skills/eng-deslop/`은 blader/humanizer(MIT)입니다. `scripts/upstream-skills.json`이 skill마다 커밋을 고정하고,
파일별 해시와 이 플러그인이 붙인 `name`, `description`을 기록합니다. 두 폴더에 쓰는 것은
`scripts/sync_upstream_skills.py`뿐입니다([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).

| 명령 | 동작 |
|---|---|
| `python3 scripts/sync_upstream_skills.py check` | 원본을 매니페스트와 비교합니다. 아무것도 쓰지 않습니다. 갱신할 skill이 있으면 exit 10 |
| `python3 scripts/sync_upstream_skills.py update` | 바뀐 원본을 복사하고 frontmatter, 라이선스 사본, 매니페스트, `[Unreleased]` 줄을 씁니다. `--report FILE`로 변경 내용을 저장합니다 |
| `python3 scripts/sync_upstream_skills.py render` | 매니페스트의 `name`과 `description`을 SKILL.md에 다시 씁니다 |
| `python3 scripts/sync_upstream_skills.py verify` | 오프라인으로 동작합니다. 가져온 파일이 매니페스트와 다르면 실패합니다 |

`--skill NAME`은 한 skill만 대상으로 합니다. `--source DIR`은 내려받지 않고 로컬 체크아웃을 사용합니다.

## 사용 시점
- 주간 워크플로가 "Sync vendored skills with their sources"라는 pull request나 issue를 열었을 때
- 월요일을 기다리지 않고 갱신이 있는지 볼 때
- 가져온 skill의 description을 바꿀 때
- 다른 저장소의 skill을 하나 더 넣을 때

## 사전 요구 사항
- python3와 git. `check`와 `update`는 github.com에 접속합니다
- 워크플로를 쓰려면 저장소에서 GitHub Actions가 켜져 있어야 합니다

## 절차

### 1. 주간 워크플로
`.github/workflows/sync-upstream-skills.yml`은 서울 시간으로 매주 월요일 06:23에 실행됩니다. Actions 탭의 "Run
workflow"나 `gh workflow run sync-upstream-skills.yml`로 직접 실행해도 됩니다. 워크플로는 `update`를 실행하고,
바뀐 것이 없으면 거기서 끝납니다. 바뀐 것이 있으면 `verify`와 `bash tests/run-all.sh upstream-skills`를
실행하고, `sync/upstream-skills` 브랜치를 push하고, 보고서를 본문으로 한 pull request를 엽니다. 병합과 릴리스는
하지 않습니다.

저장소가 Actions의 pull request 생성을 허용하지 않으면 워크플로는 pull request를 여는 링크를 담은 issue를
엽니다. 직접 열게 하려면 Settings, Actions, General의 "Allow GitHub Actions to create and approve pull
requests"를 켭니다.

### 2. pull request 검토
skill은 사용자 머신에서 Claude가 따르는 글이므로 변경 내용을 모두 읽습니다. 먼저 볼 것은 보고서에 나옵니다.

- **스크립트**(`skills/ui-deslop/scripts/*.mjs`): 무엇을 열고, 쓰고, 지우고, 실행하는지
- **새 링크**: 이전 skill에 없던 주소 모두
- **SKILL.md와 참조 파일**: 프로젝트 밖의 파일을 읽게 하거나, 데이터를 어딘가로 보내게 하거나, 무언가를 설치하게
  하거나, 확인 절차를 건너뛰라고 하는 지시가 있으면 멈춥니다
- **"The source changed its own description"**: 새 글을 읽고, 매니페스트의 `description`이 여전히 그 skill이 하는
  일을 말하는지 판단합니다(4단계)

갱신을 받지 않으려면 pull request를 닫습니다. 복사본은 고정한 커밋에 머물고, 워크플로는 다음 주에 더 새로운
상태를 다시 제안합니다.

### 3. 직접 동기화
```bash
python3 scripts/sync_upstream_skills.py check          # exit 10이면 갱신이 있음
python3 scripts/sync_upstream_skills.py update --report /tmp/sync-report.md
git diff --stat && git diff skills/ui-deslop skills/eng-deslop    # 2단계처럼 읽습니다
bash tests/run-all.sh                                  # 릴리스 전에는 전체 테스트
```

### 4. description 변경
`scripts/upstream-skills.json`에서 그 skill의 `description`을 수정합니다(한 줄, 50자 이상 1,536자 이하). 그다음
아래를 실행합니다.
```bash
python3 scripts/sync_upstream_skills.py render --skill ui-deslop
python3 scripts/sync_upstream_skills.py verify
```
가져온 skill의 SKILL.md는 직접 수정하지 않습니다. CHANGELOG.md의 `[Unreleased]`에 두 언어로 한 줄을 더합니다.

### 5. 릴리스
동기화는 `skills/` 아래 파일을 바꾸므로 릴리스해야 사용자에게 전달됩니다([release-plugin.md](release-plugin.md)).
`[Unreleased]` 줄은 `update`가 이미 넣었습니다. 동기화만 있는 릴리스는 원본이 바꾼 내용에 따라 PATCH나 MINOR입니다.

### 6. 다른 저장소의 skill 추가
1. 원본을 읽습니다. SKILL.md, 참조 파일, 스크립트 전부입니다. 라이선스가 복사와 수정을 허용하는지 확인합니다.
2. `scripts/upstream-skills.json`에 항목을 더합니다. `name`, `repo`(owner/name), `ref`(기본 브랜치는 `HEAD`),
   `path`, `include`나 `exclude`, `allow_ext`, `license`, `license_file`, `changes`, `description`입니다.
3. `python3 scripts/sync_upstream_skills.py update --skill <name> --no-changelog`를 실행하고 `verify`를 실행합니다.
4. 새 skill로 등록하고(CLAUDE.md "Change Sync Rules"), NOTICE.md에 행을 더하고,
   `tests/structure/test-upstream-skills.sh`의 기대값에 이름을 넣습니다.

## `update`가 거부할 때
`update`는 exit 1로 끝나며 `REFUSED`를 출력하고 그 skill에는 아무것도 쓰지 않습니다. 워크플로에서는 실행이
실패하고 GitHub가 실패 알림을 보냅니다.

| 메시지 | 할 일 |
|---|---|
| `the source's license is ..., the manifest says ...` | 새 조건을 읽습니다. 복사와 수정이 여전히 허용되면 매니페스트의 `license`를 바꾸고 NOTICE.md를 수정합니다. 아니면 고정한 복사본을 유지합니다 |
| `has a file type the manifest does not allow` | 파일을 읽습니다. skill에 필요한 파일이면 확장자를 `allow_ext`에 더합니다 |
| `is a symbolic link`, `is a hidden file`, `is an unusual file name` | 원본을 확인합니다. 없어도 skill이 동작하면 그 경로를 `exclude`에 넣습니다 |
| `is ... bytes, over the limit` | 플러그인에 넣을 파일인지 판단합니다. 항목의 `max_file_bytes`로 한도를 올립니다 |
| `the source's metadata already has ...` | 원본이 이 플러그인의 metadata 키를 쓰기 시작한 경우입니다. 스크립트의 `OUR_META`에서 키 이름을 바꿉니다 |

## 검증
- `python3 scripts/sync_upstream_skills.py verify`가 두 skill에 `OK`를 출력합니다
- `bash tests/run-all.sh upstream-skills`가 통과합니다. 릴리스 전에는 `bash tests/run-all.sh`를 실행합니다
- `claude plugin validate .`이 통과합니다

## 롤백
- 병합 전: pull request를 닫고 `sync/upstream-skills` 브랜치를 지웁니다
- 병합 후: 동기화 커밋을 `git revert`합니다. 매니페스트도 함께 이전 상태가 되므로 `verify`가 다시 통과합니다
- 주간 실행을 멈추려면 Actions 탭의 "Sync upstream skills"에서 "Disable workflow"를 선택합니다

## 참고
- GitHub는 저장소에 60일 동안 활동이 없으면 예약 워크플로를 멈춥니다. Actions 탭에서 다시 켭니다
- 워크플로는 파일을 복사할 뿐 실행하지 않습니다. 워크플로가 실행하는 테스트는 스크립트를 `node --check`로
  구문만 확인합니다
- 워크플로의 토큰으로 연 pull request는 다른 워크플로를 시작하지 않습니다

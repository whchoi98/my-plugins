# ADR-009: aws-diagram-design is rebuilt from its source by a recipe

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-24)

## Context
aws-diagram-design came into my-plugins as the AWS edition of cathrynlavery/diagram-design 2.3.2: 112 of the source's
145 files had been changed by hand (AWS colors, Amazon Ember, AWS icons, the plugin's names, a few rules of our own).
On 2026-11-24 the user asked to update the skill from that repository and to check it every two weeks. The source was
at 2.6.174 by then: 324 files in the skill folder, 52 visual types instead of 27, new importers, exporters and checks,
and nearly every file of 2.3.2 changed. A second hand merge would have taken as long as the first, and the source
publishes several releases a week.

Two facts made a different approach possible. The source now names colors and fonts by role in its type references and
keeps the values in one file, `style-guide.md`. And what our edition changes falls into three kinds: a fixed mapping of
tokens (colors, font names, plugin names), a small set of our own files (the style guide, the AWS icon reference, icons,
fonts), and a few paragraphs we put into the source's documents.

## Options Considered

### Option 1: Merge by hand again, every two weeks
- **Pros**: Full control over every line.
- **Cons**: Hours of work each time, mistakes that no test finds, and no way for a workflow to prepare a pull request.

### Option 2: Copy the source as it is and add the AWS rules as a layer on top
- **Pros**: No merge at all; the existing vendored mode would do.
- **Cons**: The documents and templates would name the source's fonts and colors while a layer says otherwise, so
  every diagram depends on the model translating tokens correctly.

### Option 3: Three-way merge with git
- **Pros**: Standard tooling.
- **Cons**: Conflicts in most files on the first run, because both sides changed the same lines; a conflict cannot go
  into an automatic pull request.

### Option 4: Rebuild the edition from the source by a recipe
- **Pros**: The same input gives the same output; a workflow can open a pull request; our changes are stated once, in
  a file that can be read and tested; a change the recipe does not cover stops the update.
- **Cons**: The recipe has to be kept in step with the source; an anchor that the source rewords fails the update
  until a person fixes the recipe.

## Decision
Option 4. The manifest marks the skill `"mode": "derived"` and names its recipe,
`scripts/upstream/aws-diagram-design/recipe.json`. `sync_upstream_skills.py update` then builds the skill in memory
and writes it only when the whole recipe applied:

- **Steps** rewrite `.md` and `.html` files of the source: literal pairs (colors, font names, plugin and folder names),
  a few regular expressions, and one transform that removes the middle dot from SVG text.
- **Edits** anchor on the source's own text: replace a section, insert a block before or after a line, replace one
  sentence, or keep a text as it is. An anchor that does not occur exactly as often as expected refuses the update.
  A block of ours is never rewritten by the steps.
- **Forbidden tokens** (the source's fonts, default colors, plugin names) may not survive outside a block or a kept
  text. A new place where the source hard-codes its skin therefore fails the update instead of slipping in.
- **Files of the edition** (`local` in the recipe) are never written by the sync: the style guide, the AWS icon
  reference, icons, fonts, `aws_check.py`. The style guide replaces the source's and keeps its roles and headings.
- **Scripts** of the source are copied byte for byte. The recipe cannot change a `.py` file.
- **Extra files**: the five `commands/*.md` are built from the source's commands by the same recipe.

`verify` fails on a hand edit of any rebuilt file and on a recipe that changed after the last update
(`update --pinned` rebuilds at the recorded commit). A second workflow runs every second week, on its own branch,
and opens a pull request, or an issue with the reason when the recipe no longer applies. As in ADR-008 nothing is
merged or released automatically and no file of the source is run: the workflow and the static test read the
source's scripts as text only.

With the first build the skill changed in three ways the user should know. Custom skins are now the source's
profiles, kept under `~/.aws-diagram-design/profiles/` and bound to a project by a marker, with the skill folder
declared read-only; the earlier project file `.aws-diagram-design/style-guide.md` is still read. Fonts follow the
source's `system` mode, because the source's self-check now rejects CSS `url()`: a diagram names installed fonts and
carries no `@font-face` with a file path. And two commands were added, `import-excalidraw` and `import-plantuml`.

## Consequences

### Positive
- An update of the source reaches a reviewable pull request without hand work when the recipe still applies.
- What the AWS edition changes is one readable file and five short blocks, covered by 145 offline tests on a made-up
  source and 139 static checks on the real skill.
- A change in the source that would bring its own skin back is refused, not merged.

### Negative
- The recipe breaks when the source rewords an anchor. The fix is a few lines, but a person has to make it.
- The source's examples stay in the source's skin; the style guide says to take layout from them and tokens from the
  guide.
- The manifest grew to about 66 KB, because it records a hash for each of the source's files.
- The light `accent` (3.01:1) and `soft` (3.56:1) of the AWS skin are below the 4.5:1 the source now asks of text
  colors. The style guide limits them to marks and large text; the colors themselves were not changed.

## References
- `scripts/sync_upstream_skills.py`, `scripts/upstream-skills.json`, `scripts/upstream/aws-diagram-design/`
- `.github/workflows/sync-aws-diagram-design.yml`
- `tests/structure/test-upstream-derived.sh`, `tests/structure/test-aws-diagram-design.sh`
- `docs/runbooks/sync-upstream-skills.md`, [ADR-008](ADR-008-vendored-skills-synced-by-pull-request.md)
- [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)

---

<a id="korean"></a>

# 한국어

## 상태
채택(2026-11-24)

## 배경
aws-diagram-design은 cathrynlavery/diagram-design 2.3.2의 AWS 판으로 my-plugins에 들어왔습니다. 원본 파일 145개 가운데
112개를 손으로 수정한 상태였습니다(AWS 색, Amazon Ember, AWS 아이콘, 플러그인 이름, 자체 규칙 몇 가지). 2026-11-24에
사용자가 이 저장소를 참조해 skill을 업데이트하고 2주에 한 번 확인하도록 요청했습니다. 그때 원본은 2.6.174였습니다. skill
폴더의 파일이 324개이고, 시각 유형이 27가지에서 52가지로 늘었으며, 가져오기와 내보내기, 검사 스크립트가 추가되었고, 2.3.2의
파일이 거의 모두 바뀌어 있었습니다. 손으로 다시 병합하면 처음만큼 시간이 걸리고, 원본은 한 주에도 여러 번 릴리스합니다.

다른 방식이 가능해진 이유는 두 가지입니다. 원본이 유형 참조 문서에서 색과 글꼴을 역할 이름으로 적고 값은 `style-guide.md`
한 파일에만 두게 되었습니다. 그리고 AWS 판이 바꾸는 내용은 세 종류로 나뉩니다. 정해진 토큰 치환(색, 글꼴 이름, 플러그인
이름), 자체 파일 몇 개(스타일 가이드, AWS 아이콘 참조, 아이콘, 글꼴), 원본 문서에 넣는 문단 몇 개입니다.

## 검토한 옵션

### 옵션 1: 2주마다 손으로 다시 병합하기
- **장점**: 모든 줄을 직접 정합니다.
- **단점**: 매번 몇 시간이 걸리고, 테스트가 잡지 못하는 실수가 생기며, 워크플로가 pull request를 준비할 수 없습니다.

### 옵션 2: 원본을 그대로 복사하고 AWS 규칙을 덧붙이기
- **장점**: 병합이 없습니다. 기존의 가져오기 방식으로 충분합니다.
- **단점**: 문서와 템플릿에는 원본의 글꼴과 색이 적혀 있고 덧붙인 규칙이 그것을 뒤집습니다. 다이어그램마다 모델이 토큰을
  올바르게 바꿔 주어야 합니다.

### 옵션 3: git의 3-way merge
- **장점**: 표준 도구입니다.
- **단점**: 양쪽이 같은 줄을 수정했기 때문에 첫 실행부터 대부분의 파일에서 충돌이 납니다. 충돌은 자동 pull request에 담을 수
  없습니다.

### 옵션 4: 변환 규칙(recipe)으로 원본에서 AWS 판을 다시 만들기
- **장점**: 같은 입력이면 같은 결과가 나옵니다. 워크플로가 pull request를 열 수 있습니다. AWS 판의 변경 내용이 읽고 테스트할
  수 있는 파일 하나에 정리됩니다. 변환 규칙이 다루지 않는 변경은 업데이트를 멈춥니다.
- **단점**: 변환 규칙을 원본에 맞춰 유지해야 합니다. 원본이 기준 문장을 고쳐 쓰면 사람이 변환 규칙을 수정할 때까지 업데이트가
  실패합니다.

## 결정
옵션 4를 채택합니다. 매니페스트에서 이 skill을 `"mode": "derived"`로 표시하고 변환 규칙
`scripts/upstream/aws-diagram-design/recipe.json`을 지정합니다. `sync_upstream_skills.py update`는 skill을 메모리에서 만들고,
변환 규칙 전체가 적용된 경우에만 파일로 씁니다.

- **단계(steps)**는 원본의 `.md`와 `.html` 파일을 변환합니다. 문자열 치환(색, 글꼴 이름, 플러그인과 폴더 이름), 정규식 몇 개,
  SVG 텍스트의 가운뎃점을 없애는 변환 하나입니다.
- **편집(edits)**은 원본의 문장을 기준으로 삼습니다. 섹션 교체, 줄 앞뒤에 블록 삽입, 문장 하나 교체, 그대로 두기가 있습니다.
  기준 문장이 정해진 횟수만큼 나오지 않으면 업데이트를 거부합니다. AWS 판의 블록은 단계가 변환하지 않습니다.
- **금지 토큰**(원본의 글꼴, 기본 색, 플러그인 이름)은 블록과 그대로 두는 문장 밖에 남을 수 없습니다. 원본이 자기 스킨을 새
  자리에 직접 적으면 그 내용이 들어오는 대신 업데이트가 실패합니다.
- **AWS 판의 파일**(변환 규칙의 `local`)은 동기화가 쓰지 않습니다. 스타일 가이드, AWS 아이콘 참조, 아이콘, 글꼴,
  `aws_check.py`입니다. 스타일 가이드는 원본의 것을 대신하며 원본의 역할 이름과 제목을 유지합니다.
- 원본의 **스크립트**는 바이트 그대로 복사합니다. 변환 규칙은 `.py` 파일을 바꿀 수 없습니다.
- **추가 파일**: `commands/*.md` 5개도 같은 변환 규칙으로 원본의 command에서 만듭니다.

`verify`는 다시 만든 파일을 손으로 수정했거나 마지막 업데이트 뒤에 변환 규칙이 바뀌었으면 실패합니다(`update --pinned`가 기록한
커밋에서 다시 만듭니다). 두 번째 워크플로가 2주에 한 번 자기 브랜치에서 실행되어 pull request를 열고, 변환 규칙이 더 맞지 않으면
이유를 담은 issue를 남깁니다. ADR-008과 같이 자동으로 병합하거나 릴리스하지 않고 원본의 파일을 실행하지 않습니다. 워크플로와
정적 테스트는 원본의 스크립트를 텍스트로만 읽습니다.

첫 번째 재구성에서 사용자가 알아야 할 변화가 세 가지 있습니다. 사용자 스킨은 원본의 프로필 방식으로 바뀌어
`~/.aws-diagram-design/profiles/`에 두고 마커로 프로젝트에 연결하며, skill 폴더는 읽기 전용으로 정했습니다. 이전 방식의
프로젝트 파일 `.aws-diagram-design/style-guide.md`도 계속 읽습니다. 글꼴은 원본의 `system` 방식을 따릅니다. 원본의 자체 검사가
CSS `url()`을 거부하게 되었기 때문에, 다이어그램은 설치된 글꼴의 이름만 적고 파일 경로가 든 `@font-face`를 넣지 않습니다.
그리고 command 두 개(`import-excalidraw`, `import-plantuml`)가 추가되었습니다.

## 영향

### 긍정적
- 변환 규칙이 그대로 맞는 동안에는 원본의 업데이트가 손작업 없이 검토할 수 있는 pull request가 됩니다.
- AWS 판이 바꾸는 내용이 읽을 수 있는 파일 하나와 짧은 블록 5개이고, 가상의 원본으로 하는 오프라인 테스트 145개와 실제 skill의
  정적 검사 139개가 이를 확인합니다.
- 원본의 스킨을 되살리는 변경은 병합되지 않고 거부됩니다.

### 부정적
- 원본이 기준 문장을 고쳐 쓰면 변환 규칙이 깨집니다. 몇 줄만 수정하면 되지만 사람이 해야 합니다.
- 원본의 예제는 원본의 스킨 그대로입니다. 스타일 가이드는 예제에서 배치만 가져오고 토큰은 가이드에서 가져오라고 적습니다.
- 원본의 파일마다 해시를 기록하므로 매니페스트가 약 66 KB로 커졌습니다.
- AWS 스킨의 밝은 `accent`(3.01:1)와 `soft`(3.56:1)는 원본이 이제 글자색에 요구하는 4.5:1보다 낮습니다. 스타일 가이드는 두 색을
  표시와 큰 글자에만 쓰도록 제한했고, 색 자체는 바꾸지 않았습니다.

## 참고 자료
- `scripts/sync_upstream_skills.py`, `scripts/upstream-skills.json`, `scripts/upstream/aws-diagram-design/`
- `.github/workflows/sync-aws-diagram-design.yml`
- `tests/structure/test-upstream-derived.sh`, `tests/structure/test-aws-diagram-design.sh`
- `docs/runbooks/sync-upstream-skills.md`, [ADR-008](ADR-008-vendored-skills-synced-by-pull-request.md)
- [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)

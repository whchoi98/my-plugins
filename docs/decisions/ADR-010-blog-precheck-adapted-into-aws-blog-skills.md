# ADR-010: The blog pre-check is adapted into aws-blog-skills, with the gate enforced by scripts

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-25)

## Context
github.com/comeddy/blog-precheck-plugin (MIT) ships a skill that an author of the AWS technical blog runs before
asking for a review: a self gate of six scored criteria written to `gate-report.md`, a conversion of the manuscript to
HTML for the WordPress code editor, a content review checklist and a notice text for after publishing. The author of
my-plugins asked for aws-blog-skills to be updated with reference to it.

aws-blog-skills already writes the draft and checks it with scripts (`check_structure.py`, `check_urls.py`,
`lint_prose.py`), and several items of the source's checklist were in its references since 2026-11-01. What it did
not have: a scored gate before hand-over, a measure of repetition and filler, the WordPress form of the draft and the
notice text.

## Options Considered

### Option 1: Vendor the source's skill as a separate skill (the mode of ui-deslop)
- **Pros**: No rewriting; a sync workflow keeps it current.
- **Cons**: Two skills answer one blog request and the user has to run both. The source reads docx or Markdown and
  scores by its own reading, so the checks aws-blog-skills already runs would be done twice with different results.
  Its metric script reads a Markdown table row as a paragraph, so the separator rows of two tables count as a
  repeated paragraph in the drafts this plugin writes.

### Option 2: Copy the source's files into aws-blog-skills unchanged
- **Pros**: Little work.
- **Cons**: The same double checks and the same false penalties; the source's text does not follow the wording rules
  of this skill (banned words, no middle dot), and a model-written conversion gives a different result each time.

### Option 3: Adapt the method into the skill's own steps, scripts and references
- **Pros**: One workflow. Each criterion is measured with the script that already owns that rule. The parts that are
  arithmetic or mechanical become scripts with exit codes. The report keeps the source's layout, so a reviewer who
  uses the source's tools reads it unchanged.
- **Cons**: The text and code are ours to maintain, and a change in the source does not arrive by itself.

## Decision
Option 3.

- **Step 6, pre-check**: the six criteria, their minimums (80, 70, 70, 60, 60, 60), the pass total (70) and the limit
  of two rounds are the source's. `references/precheck.md` says what each criterion looks at in this skill. Where the
  source gives no points per finding (consistency, notation), 10 points are taken off per finding. The only item that
  may be marked not applicable is the clean-up of resources, in a post where the reader creates none.
- **`redundancy_metrics.py`**: the source's six measures, limits and weights, on the prose the way `lint_prose.py`
  reads a draft. Markdown only. The hand-counted restatements are an argument, so the score of criterion 4 is printed
  by the script.
- **`check_gate.py`**: recomputes the total and the verdict from the six scores and fails on a statement the scores
  do not support, on a score the rules cannot give, on a judged score without a quoted sentence and on a lost point
  without the original and the corrected text. With `--draft` it measures the draft again, so a report belongs to
  the draft it is packaged with. Exit 0 hand over, 3 반려, 1 inconsistent.
- **`md_to_wordpress.py`**: the source's WordPress checklist as a converter. It uploads nothing, writes raw HTML as
  text, escapes attribute values, accepts only `http`, `https`, `mailto` and relative links, refuses images it cannot
  hand over and counts the draft's blocks a second way before it writes. Text that came from source material cannot
  become markup in the page the reviewer pastes.
- **`package_blog.sh`** runs both and writes no zip without a gate report it accepts. `--no-gate` exists for a user
  who asks to leave the pre-check out. Its output ends with the score table, and the session's last response shows
  that table without being asked (asked for by the author on 2026-11-25).
- **Credit**: `NOTICE.md`, `third_party/LICENSE-blog-precheck` and a line in each of the five files that follow the
  source. Nothing is taken from github.com/ssMinji/skills, which the source says it is based on and which carries no
  license file.

## Consequences

### Positive
- A draft cannot be packaged with a verdict its scores do not support, and criterion 4 is a number anyone can get again.
- The reviewer receives the report and the WordPress form in the same zip.
- The conversion is the same on every run and is covered by tests.

### Negative
- Every session is longer: the gate needs a web search for comparable posts and a written report.
- The converter reads the Markdown this skill writes. A construct it does not know stops the packaging until the
  draft or the converter is changed.
- `package_blog.sh` now refuses a work folder without `gate-report.md`; a caller written before this change has to
  pass `--no-gate` or run the pre-check.
- The source is not synced. Its later changes have to be read and brought over by hand.

## References
- `skills/aws-blog-skills/SKILL.md` (steps 6 and 7), `references/precheck.md`, `references/publishing.md`
- `skills/aws-blog-skills/scripts/redundancy_metrics.py`, `check_gate.py`, `md_to_wordpress.py`, `package_blog.sh`
- `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-aws-blog-skills-scripts.sh`
- [comeddy/blog-precheck-plugin](https://github.com/comeddy/blog-precheck-plugin) at commit `c3a09c9`

---

<a id="korean"></a>

# 한국어

## 상태
채택 (2026-11-25)

## 배경
github.com/comeddy/blog-precheck-plugin(MIT)은 AWS 기술 블로그 저자가 리뷰를 요청하기 전에 실행하는 skill을 배포합니다.
여섯 기준을 채점해 `gate-report.md`에 쓰는 셀프 게이트, 원고를 WordPress 코드 편집기용 HTML로 바꾸는 변환, 내용 리뷰
체크리스트, 게시 후 공지 문구로 이루어져 있습니다. my-plugins의 저자가 이 저장소를 참고해 aws-blog-skills를 업데이트해
달라고 요청했습니다.

aws-blog-skills는 이미 원고를 쓰고 스크립트(`check_structure.py`, `check_urls.py`, `lint_prose.py`)로 검사하며, 원본
체크리스트의 여러 항목은 2026-11-01부터 참조 파일에 들어 있었습니다. 없던 것은 넘기기 전에 점수를 매기는 게이트, 중복과
군더더기 지표, 원고의 WordPress 형식, 공지 문구입니다.

## 검토한 옵션

### 옵션 1: 원본 skill을 별도 skill로 가져오기(ui-deslop과 같은 방식)
- **장점**: 다시 쓸 필요가 없고 동기화 워크플로가 최신으로 유지합니다.
- **단점**: 블로그 요청 하나에 skill 두 개가 반응하고 사용자가 둘 다 실행해야 합니다. 원본은 docx나 Markdown을 읽어 직접
  판단해 채점하므로, aws-blog-skills가 이미 하는 검사를 다른 결과로 한 번 더 하게 됩니다. 원본의 지표 스크립트는 Markdown
  표의 행을 문단으로 읽어서, 이 플러그인이 쓰는 원고에서는 표 두 개의 구분 행이 문단 반복으로 잡힙니다.

### 옵션 2: 원본 파일을 aws-blog-skills에 그대로 복사하기
- **장점**: 작업이 적습니다.
- **단점**: 검사 중복과 잘못된 감점이 그대로 남습니다. 원본의 문장은 이 skill의 표기 규칙(금지어, 가운뎃점 금지)을 따르지
  않고, 모델이 직접 하는 변환은 실행할 때마다 결과가 달라집니다.

### 옵션 3: 방법을 이 skill의 단계, 스크립트, 참조 파일로 옮겨 쓰기
- **장점**: 워크플로가 하나입니다. 기준마다 그 규칙을 이미 맡고 있는 스크립트로 측정합니다. 계산과 기계적인 부분은 종료
  코드가 있는 스크립트가 됩니다. 리포트는 원본의 형식을 유지하므로 원본의 도구를 쓰는 리뷰어가 그대로 읽습니다.
- **단점**: 문서와 코드를 직접 유지해야 하고, 원본이 바뀌어도 자동으로 들어오지 않습니다.

## 결정
옵션 3을 선택했습니다.

- **6단계 사전 점검**: 여섯 기준, 최저선(80, 70, 70, 60, 60, 60), 통과 총점(70), 채점 두 회차 제한은 원본의 것입니다.
  `references/precheck.md`에 이 skill에서 기준마다 보는 것을 적었습니다. 원본에 건당 배점이 없는 기준(정합성, 표기 규범)은
  1건마다 10점을 뺍니다. "해당 없음"으로 둘 수 있는 항목은 독자가 리소스를 만들지 않는 글의 리소스 정리 하나입니다.
- **`redundancy_metrics.py`**: 원본의 여섯 지표, 한도, 가중치를 `lint_prose.py`가 원고를 읽는 방식으로 본문에 적용합니다.
  Markdown만 읽습니다. 직접 센 재진술 건수를 인자로 받아 기준 4 점수를 스크립트가 출력합니다.
- **`check_gate.py`**: 여섯 점수에서 총점과 판정을 다시 계산합니다. 점수와 맞지 않는 판정, 채점 규칙으로 나올 수 없는 점수,
  인용이 없는 판단 점수, 원문과 수정안이 없는 감점이 있으면 실패합니다. `--draft`를 주면 원고를 다시 측정하므로 리포트는
  함께 패키징되는 원고의 것이어야 합니다. 종료 코드 0은 전달 가능, 3은 반려, 1은 불일치입니다.
- **`md_to_wordpress.py`**: 원본의 WordPress 체크리스트를 변환기로 만들었습니다. 업로드하지 않고, 원고의 HTML 태그를 글자로
  바꾸고, 속성값을 이스케이프하고, 링크는 `http`, `https`, `mailto`, 상대 경로만 받습니다. 넘길 수 없는 이미지를 거부하며,
  쓰기 전에 원고의 블록 수를 다른 방법으로 한 번 더 셉니다. 소재에서 온 글자는 리뷰어가 붙여넣는 페이지의 마크업이 될 수
  없습니다.
- **`package_blog.sh`**는 두 스크립트를 실행하고, 통과한 게이트 리포트가 없으면 zip을 만들지 않습니다. 사용자가 사전 점검을
  빼 달라고 할 때를 위해 `--no-gate`가 있습니다. 출력의 끝에 점수표를 적고, 세션의 마지막 응답은 묻지 않아도 그 표를
  제시합니다(2026-11-25 저자 요청).
- **출처 표시**: `NOTICE.md`, `third_party/LICENSE-blog-precheck`, 그리고 원본을 따른 파일 다섯 개에 한 줄씩 적었습니다.
  원본이 바탕으로 삼았다고 밝힌 github.com/ssMinji/skills에서는 아무것도 가져오지 않았습니다. 그 저장소에는 라이선스
  파일이 없습니다.

## 결과

### 긍정적
- 점수와 맞지 않는 판정으로는 원고를 패키징할 수 없고, 기준 4는 누구나 다시 얻을 수 있는 숫자입니다.
- 리뷰어가 리포트와 WordPress 형식을 같은 zip으로 받습니다.
- 변환 결과가 실행마다 같고 테스트로 확인됩니다.

### 부정적
- 세션이 길어집니다. 게이트에는 비슷한 글을 찾는 웹 검색과 리포트 작성이 필요합니다.
- 변환기는 이 skill이 쓰는 Markdown을 읽습니다. 변환기가 모르는 문법이 있으면 원고나 변환기를 수정할 때까지 패키징이
  멈춥니다.
- `package_blog.sh`가 `gate-report.md`가 없는 작업 폴더를 거부합니다. 이 변경 전 방식으로 부르던 곳은 `--no-gate`를 주거나
  사전 점검을 실행해야 합니다.
- 원본과 동기화하지 않습니다. 원본의 이후 변경은 직접 읽고 옮겨야 합니다.

## 참고 자료
- `skills/aws-blog-skills/SKILL.md`(6단계와 7단계), `references/precheck.md`, `references/publishing.md`
- `skills/aws-blog-skills/scripts/redundancy_metrics.py`, `check_gate.py`, `md_to_wordpress.py`, `package_blog.sh`
- `tests/structure/test-aws-blog-skills.sh`, `tests/structure/test-aws-blog-skills-scripts.sh`
- [comeddy/blog-precheck-plugin](https://github.com/comeddy/blog-precheck-plugin), 커밋 `c3a09c9`

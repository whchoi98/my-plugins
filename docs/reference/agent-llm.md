# Agent · LLM / 에이전트 · LLM 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<a id="english"></a>
## English

### 1. Overview
The plugin's "model logic" is fourteen skills and three command prompts: Markdown instructions Claude follows
inside the user's Claude Code session. There is no SDK call, prompt template file, subagent or model
configuration. Claude Code loads every skill and command `description` in every session, the SKILL.md body when
one fires, and reference files only when a step asks for them. Skills chain through the Skill tool as
`my-plugins:<skill>`; deterministic checks are bundled scripts the model must run instead of judging by eye.

### 2. Components
| Skill | Entry | What the model does | Read on demand |
|---|---|---|---|
| aws-blog-skills | `skills/aws-blog-skills/SKILL.md` | Steps 0-7: scope, fact and URL check, skeleton and draft, style rules and 윤문, diagrams, structure check, packaging, rule registration | `references/` per step: structure, style, humanize-checklist, verification, diagrams, exemplars, collaboration |
| aws-diagram | `skills/aws-diagram/SKILL.md` | Map the system to AWS services, look up exact icons with `find_icon.py`, compose SVG, inline icons with `embed.py` | `references/diagram_guide.md` (read in full) |
| aws-diagram-design | `skills/aws-diagram-design/SKILL.md` | Pick a semantic pattern and one of 27 visual types, draw HTML/SVG on the 4px grid, pass the taste gate, export | `references/type-*.md` for the chosen type, `style-guide.md`, `semantic-patterns.md`, `animation.md`, export and import references |
| kor-deslop | `skills/kor-deslop/SKILL.md` | One pass: rule priority, meaning preservation, severity-based fixes, six self-checks, three output modes | `references/patterns.md` (81 patterns and principles, read once per run) |
| aws-ppt-skills | `skills/aws-ppt-skills/SKILL.md` | Confirm the output format (PPT, HTML or both), theme, audience, presenter and content; paste the pptxgenjs helpers; build, apply template, lint, render, inspect; for an HTML deck convert the checked `.pptx` and check the page in a browser | `references/diagrams.md`, `references/html-deck.md` |
| consulting-ppt-white-ppt | `skills/consulting-ppt-white-ppt/SKILL.md` | Confirm client, logo and chapters; derive the accent; compose with `consult_helpers.js`; fix and render | `examples/build_sample.js` |
| pptx-template-fill | `skills/pptx-template-fill/SKILL.md` | Inventory shapes, write a mapping table, fill runs, cells and chart caches in place, unify fonts, QA | `references/recipes.md` |
| aws-reports | `skills/aws-reports/SKILL.md` | Pick the report type (benchmark or PoC), gather data and the PoC success criteria, compute numbers and verdicts in Python, write one Markdown draft, build Word + HTML with `report.mjs`, run `check_report.py --profile`, look at the previews | `references/` per type: `benchmark-structure.md`, or `poc-structure.md` + `poc-verdict-rules.md`; always `markdown-spec.md`, `style-rules.md`; `assets/examples/<type>/` |
| html-report | `skills/html-report/SKILL.md` | Pick research or general, gather content, sources and the sharing scope, copy the template, fill Korean and English pairs, embed images, run `check_html.py` and `lint_prose.py` on the Korean text, look at the four previews | `references/design-spec.md` (read once), `assets/template.html` |
| techblogs | `skills/techblogs/SKILL.md` | Fix the material and scope (a new post, or a published AWS blog post brought in with `import_aws_post.py`), verify facts and links, write the Korean fragment, remove AI tells, write the English fragment, build with `build_post.py`, run `check_post.py`, `lint_prose.py` and `check_urls.py`, place into the blog repository with `place_post.py --build`, look at the previews | `references/design-spec.md` (before writing), `references/publish.md` (when placing); aws-blog-skills `references/style.md`, `humanize-checklist.md`, `verification.md` |
| aws-infographic | `skills/aws-infographic/SKILL.md` | Fix the scope in one round of questions (sizes, sources, AWS mapping, deck theme and audience), verify every number against primary sources, design sections around one visual each, write the page modules, build with `buildkit.py` until the QA report is empty, then rebuild the content as an editable deck through aws-ppt-skills and run `check_editable.py` | `references/ppt-deck.md` (before the deck) |
| ui-deslop | `skills/ui-deslop/SKILL.md` | Audit the screen against the signs, decide how much to change, write a five-line direction and wait for the user, fix in ordered passes (spacing, color, icons, copy, type, layout, details, visuals, motion), check and report; a story video on request | `references/signs.md`, `tokens.md`, `visuals.md`, `effects.md`, `rtl.md`, `refs.md` |
| eng-deslop | `skills/eng-deslop/SKILL.md` | Mark the tells, draft the rewrite, check that no fact changed, write the final text; pasted-text, file and embedded modes | none (the patterns are in the body) |
| setup | `skills/setup/SKILL.md` | Check, install user-level items, ask before the sudo step, re-check and report `missing:` | none |
| commands | `commands/*.md` | `export-diagram`, `import-drawio`, `import-mermaid` follow the aws-diagram-design references instead of restating them | `skills/aws-diagram-design/references/export.md`, `import-*.md`, `output-spec.md` |

**How skills chain.**

| Caller | Calls | When |
|---|---|---|
| aws-blog-skills | `my-plugins:aws-diagram` | AWS service architecture figures (step 4) |
| aws-blog-skills | `my-plugins:aws-diagram-design`, then `/my-plugins:export-diagram`; `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | Structure diagrams, and redrawing existing draw.io or Mermaid figures (step 4, `references/diagrams.md`) |
| aws-blog-skills | `my-plugins:kor-deslop` (check-only) | Self-check for remaining AI tells after the draft and before packaging (step 3, `references/humanize-checklist.md`) |
| aws-ppt-skills | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design` | Architecture and structure diagrams; graphs stay native pptxgenjs charts |
| aws-reports | `my-plugins:aws-diagram` | Architecture figure in the method section, converted with `svg2png.py` |
| html-report | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop` (check-only) | Figures; an optional AI-tell check on the Korean text |
| techblogs | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop` (check-only) | Figures (step 4); the AI-tell check after the Korean draft (step 3) |
| aws-infographic | `my-plugins:aws-ppt-skills` | The editable deck once the infographic passes QA (step 9) |
| aws-blog-skills, aws-ppt-skills, consulting-ppt-white-ppt, aws-reports, html-report, techblogs, aws-infographic | `my-plugins:setup` | A tool or font is missing |

Charts and comparison figures specific to the blog are drawn by aws-blog-skills itself with `diagram_lib.py`,
which reads icons and fonts from `../aws-diagram-design/assets` (see [architecture.md](../architecture.md)).

**Token cost** (`claude --plugin-dir . plugin details my-plugins`, 2026-11-21; estimates):

| Component | Always-on | On invoke |
|---|---|---|
| aws-blog-skills | ~530 | ~4.8k |
| aws-diagram | ~680 | ~3.5k |
| aws-diagram-design | ~630 | ~20.6k |
| kor-deslop | ~210 | ~1.4k |
| aws-ppt-skills | ~430 | ~33.2k |
| consulting-ppt-white-ppt | ~580 | ~7.2k |
| pptx-template-fill | ~570 | ~3.6k |
| aws-reports | ~540 | ~3.7k |
| html-report | ~360 | ~2.7k |
| techblogs | ~480 | ~5.6k |
| aws-infographic | ~390 | ~4.9k |
| ui-deslop | ~420 | ~15.5k |
| eng-deslop | ~380 | ~16.5k |
| setup | ~400 | ~1.4k |
| export-diagram, import-drawio, import-mermaid | ~70, ~70, ~70 | ~740, ~1.5k, ~1.4k |
| **Total always-on** | **~6.8k** | |

References come on top of the on-invoke figure. A chained run pays for each skill that fires: a blog post with
a structure diagram loads aws-blog-skills, aws-diagram-design and kor-deslop bodies in the same session.

### 3. Key Decisions
- Progressive disclosure: only descriptions are always loaded; bodies and references load on invoke, and
  references load per step, so a sentence fix does not pull in the diagram profile.
- aws-reports is one skill with two report types: one description (~430 always-on tokens; two skills cost ~980),
  and SKILL.md sends the model to the benchmark or PoC references after it picks the type
  ([ADR-003](../decisions/ADR-003-one-report-skill-global-npm.md)).
- Delegate, don't copy: aws-blog-skills and aws-ppt-skills call the diagram skills and kor-deslop through the
  Skill tool instead of copying their rules ([ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)).
- html-report fills a fixed template instead of rendering a draft: the model edits content only, and
  `check_html.py` verifies pairs, order, numbering and tokens ([ADR-004](../decisions/ADR-004-html-report-template-fill.md)).
- techblogs builds the page from fragments: the model writes `meta.json` and one body fragment per language,
  `build_post.py` copies the template's `<style>` and `<script>` unchanged, and `check_post.py` compares the two
  languages ([ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md)).
- aws-infographic keeps one source of content for two outputs: the page modules hold the text in a `T` dict,
  `buildkit.py` checks the drawing, and the deck is rebuilt from the same text with native PowerPoint objects
  instead of a pasted picture ([ADR-006](../decisions/ADR-006-infographic-editable-deck.md)).
- Descriptions route between neighbours: aws-diagram and aws-diagram-design each name the other "in this
  plugin" for the other kind of figure; consulting-ppt-white-ppt names aws-ppt-skills for seminar decks;
  aws-blog-skills states that it takes precedence over kor-deslop for blog drafts.
- ui-deslop and eng-deslop are other authors' prompts, copied at a pinned commit and never edited, so my-plugins
  controls only their `name` and `description`. The three deslop descriptions name each other: Korean text goes to
  kor-deslop, English text to eng-deslop, a screen to ui-deslop
  ([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).
- Mechanical rules are scripts with exit codes (`lint_prose.py`, `check_structure.py`, `check_urls.py`, geometry
  asserts in `diagram_lib.py`, `self_check.py`, `check_deck.py`, `qa_check.py`); SKILL.md keeps judgment and order.
- Paths: `${CLAUDE_SKILL_DIR}` is substituted in SKILL.md only (aws-blog-skills, setup); the diagram and deck
  skills define `SKILL_DIR` from "Base directory for this skill". Bash state does not persist between calls, so
  the model uses absolute paths ([ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md)).
- kor-deslop only subtracts: user request, then meaning preservation, then patterns; whole-sentence deletions are
  reported as candidates.
- aws-ppt-skills builds on empty masters and moves slides onto the bundled template with `apply_template.py`, so
  the template stays the only source of background, logo, footer and page numbers.
- aws-blog-skills appends confirmed rules with `(YYYY-MM-DD 확정)` so later sessions can tell rule age from the text.

### 4. Code Pointers
- `skills/aws-blog-skills/SKILL.md`
- `skills/aws-blog-skills/references/diagrams.md`
- `skills/aws-blog-skills/references/humanize-checklist.md`
- `skills/aws-diagram/SKILL.md`
- `skills/aws-diagram-design/SKILL.md`
- `skills/kor-deslop/SKILL.md`
- `skills/kor-deslop/references/patterns.md`
- `skills/ui-deslop/SKILL.md`
- `skills/eng-deslop/SKILL.md`
- `scripts/upstream-skills.json`
- `skills/aws-ppt-skills/SKILL.md`
- `skills/aws-ppt-skills/references/diagrams.md`
- `skills/aws-ppt-skills/references/html-deck.md`
- `skills/consulting-ppt-white-ppt/SKILL.md`
- `skills/pptx-template-fill/SKILL.md`
- `skills/aws-reports/SKILL.md`
- `skills/aws-reports/references/poc-verdict-rules.md`
- `skills/html-report/SKILL.md`
- `skills/html-report/references/design-spec.md`
- `skills/techblogs/SKILL.md`
- `skills/techblogs/references/design-spec.md`
- `skills/aws-infographic/SKILL.md`
- `skills/aws-infographic/references/ppt-deck.md`
- `skills/setup/SKILL.md`
- `commands/export-diagram.md`
- `skills/CLAUDE.md`

### 5. Cross-references
- Related modules: `skills/` (`skills/CLAUDE.md`)
- Related ADRs: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md),
  [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md),
  [ADR-003](../decisions/ADR-003-one-report-skill-global-npm.md),
  [ADR-004](../decisions/ADR-004-html-report-template-fill.md),
  [ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md),
  [ADR-006](../decisions/ADR-006-infographic-editable-deck.md)
- Related runbooks: [release-plugin.md](../runbooks/release-plugin.md),
  [setup-dependencies.md](../runbooks/setup-dependencies.md)

<a id="korean"></a>
## 한국어

### 1. 개요
이 플러그인의 "모델 로직"은 skill 14개와 command 프롬프트 3개입니다. 사용자의 Claude Code 세션 안에서 Claude가 따르는 Markdown 지침이며, SDK 호출, 프롬프트 템플릿 파일, 하위 에이전트, 모델 설정은 없습니다. Claude Code는 모든 skill과 command의 `description`을 매 세션 로드하고, skill이 실행될 때 SKILL.md 본문을, 단계가 요구할 때만 참조 파일을 읽습니다. skill끼리는 Skill 도구로 `my-plugins:<skill>`을 불러 이어지며, 결정적 검사는 모델이 눈으로 판단하는 대신 실행해야 하는 함께 배포되는 스크립트입니다.

### 2. 구성요소
| skill | 진입점 | 모델이 하는 일 | 필요할 때 읽는 것 |
|---|---|---|---|
| aws-blog-skills | `skills/aws-blog-skills/SKILL.md` | 0~7단계: 범위, 사실과 URL 검증, 골격과 초안, 문장 규칙과 윤문, 다이어그램, 구조 검사, 패키징, 규칙 등록 | 단계별 `references/`: structure, style, humanize-checklist, verification, diagrams, exemplars, collaboration |
| aws-diagram | `skills/aws-diagram/SKILL.md` | 시스템을 AWS 서비스로 대응시키고, `find_icon.py`로 정확한 아이콘을 찾아 SVG를 짜고, `embed.py`로 아이콘을 내장 | `references/diagram_guide.md`(전체를 읽음) |
| aws-diagram-design | `skills/aws-diagram-design/SKILL.md` | 의미 패턴과 시각 유형 27가지 중 하나를 골라 4px 그리드로 HTML/SVG를 그리고, taste gate를 통과시킨 뒤 내보내기 | 고른 유형의 `references/type-*.md`, `style-guide.md`, `semantic-patterns.md`, `animation.md`, 내보내기와 가져오기 참조 |
| kor-deslop | `skills/kor-deslop/SKILL.md` | 한 번에 처리: 규칙 우선순위, 의미 보존, 심각도별 수정, 자체 점검 6항목, 결과 전달 방식 3가지 | `references/patterns.md`(패턴과 원칙 81개, 실행마다 한 번) |
| aws-ppt-skills | `skills/aws-ppt-skills/SKILL.md` | 출력 형식(PPT, HTML, 둘 다), 테마, 청중, 발표자, 내용을 확인하고 pptxgenjs 헬퍼를 붙여 빌드, 템플릿 적용, lint, 렌더, 눈으로 확인. HTML 덱은 확인을 마친 `.pptx`를 변환한 뒤 브라우저에서 확인 | `references/diagrams.md`, `references/html-deck.md` |
| consulting-ppt-white-ppt | `skills/consulting-ppt-white-ppt/SKILL.md` | 고객 이름, 로고, 챕터를 확인하고 강조색을 뽑은 뒤 `consult_helpers.js`로 짜고, 고치고 렌더 | `examples/build_sample.js` |
| pptx-template-fill | `skills/pptx-template-fill/SKILL.md` | 도형 인벤토리, 매핑 표 작성, run, 표 셀, 차트 캐시를 제자리에서 채우고 폰트 통일, QA | `references/recipes.md` |
| aws-reports | `skills/aws-reports/SKILL.md` | 보고서 유형(벤치마크, PoC)을 고르고 데이터와 PoC 성공 기준을 모아 숫자와 판정을 Python으로 계산한 뒤, Markdown 원고 하나를 써서 `report.mjs`로 Word + HTML을 빌드하고 `check_report.py --profile`로 검사하고 미리보기를 확인 | 유형별 `references/`: `benchmark-structure.md` 또는 `poc-structure.md` + `poc-verdict-rules.md`, 항상 `markdown-spec.md`, `style-rules.md`, `assets/examples/<유형>/` |
| html-report | `skills/html-report/SKILL.md` | 조사 보고서인지 일반 보고서인지 정하고, 내용과 출처와 공유 범위를 모은 뒤, 템플릿을 복사해 한국어와 영어 짝을 채우고, 그림을 넣고, `check_html.py`와 한국어 글의 `lint_prose.py`를 실행하고, 미리보기 네 가지 화면을 확인 | `references/design-spec.md`(한 번), `assets/template.html` |
| techblogs | `skills/techblogs/SKILL.md` | 소재와 범위를 정하고(새 글, 또는 `import_aws_post.py`로 가져온 게시된 AWS 블로그 글) 사실과 링크를 검증한 뒤 한국어 조각을 쓰고 AI 티를 없앤 다음 영어 조각을 쓰고 `build_post.py`로 빌드해 `check_post.py`, `lint_prose.py`, `check_urls.py`를 실행하고 `place_post.py --build`로 블로그 저장소에 배치한 뒤 미리보기 화면을 확인 | `references/design-spec.md`(본문을 쓰기 전), `references/publish.md`(배치할 때), aws-blog-skills의 `references/style.md`, `humanize-checklist.md`, `verification.md` |
| aws-infographic | `skills/aws-infographic/SKILL.md` | 범위를 한 번에 확인하고(크기, 원본, AWS 연계, 덱 테마와 청중 규모) 모든 수치를 1차 출처로 검증한 뒤 섹션마다 시각 표현 하나를 정해 장 모듈을 쓰고 `buildkit.py`로 QA 이슈가 0건이 될 때까지 빌드. 이어서 같은 내용을 aws-ppt-skills로 편집 가능한 덱으로 다시 만들고 `check_editable.py` 실행 | `references/ppt-deck.md`(덱을 만들기 전) |
| ui-deslop | `skills/ui-deslop/SKILL.md` | 화면을 흔적 목록과 대조해 점검하고, 수정 범위를 정하고, 다섯 줄 방향을 써서 사용자 답을 기다린 뒤, 정해진 순서(간격, 색, 아이콘, 문구, 글꼴, 레이아웃, 세부, 그림, 모션)로 수정하고 확인해 보고. 요청하면 스토리 영상 | `references/signs.md`, `tokens.md`, `visuals.md`, `effects.md`, `rtl.md`, `refs.md` |
| eng-deslop | `skills/eng-deslop/SKILL.md` | 흔적 표시, 다시 쓴 초안, 사실이 바뀌지 않았는지 확인, 최종본 작성. 붙여 넣은 글, 파일, 다른 작업에 포함된 글의 세 방식 | 없음(패턴이 본문에 있음) |
| setup | `skills/setup/SKILL.md` | 점검, 사용자 영역 설치, sudo 단계 전에 허락받기, 재점검과 `missing:` 보고 | 없음 |
| command | `commands/*.md` | `export-diagram`, `import-drawio`, `import-mermaid`는 aws-diagram-design 참조를 다시 적지 않고 따름 | `skills/aws-diagram-design/references/export.md`, `import-*.md`, `output-spec.md` |

**skill이 이어지는 방식.**

| 호출하는 쪽 | 부르는 것 | 언제 |
|---|---|---|
| aws-blog-skills | `my-plugins:aws-diagram` | AWS 서비스 아키텍처 그림(4단계) |
| aws-blog-skills | `my-plugins:aws-diagram-design` 뒤 `/my-plugins:export-diagram`, `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | 구조 다이어그램, 기존 draw.io나 Mermaid 그림 다시 그리기(4단계, `references/diagrams.md`) |
| aws-blog-skills | `my-plugins:kor-deslop`(점검만) | 초안 완성 직후와 패키징 직전의 자가 점검에서 남은 AI 티 확인(3단계, `references/humanize-checklist.md`) |
| aws-ppt-skills | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design` | 아키텍처와 구조 다이어그램. 그래프는 pptxgenjs 기본 차트로 유지 |
| aws-reports | `my-plugins:aws-diagram` | 측정 환경 섹션의 구성도. `svg2png.py`로 PNG 변환 |
| html-report | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`(점검만) | 그림, 한국어 글의 AI 티 점검(선택) |
| techblogs | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`(점검만) | 그림(4단계), 한국어 초안을 쓴 뒤의 AI 티 점검(3단계) |
| aws-infographic | `my-plugins:aws-ppt-skills` | 인포그래픽 QA가 끝난 뒤의 편집 가능한 덱(9단계) |
| aws-blog-skills, aws-ppt-skills, consulting-ppt-white-ppt, aws-reports, html-report, techblogs, aws-infographic | `my-plugins:setup` | 도구나 폰트가 없을 때 |

블로그 고유의 차트와 비교 그림은 aws-blog-skills가 `diagram_lib.py`로 직접 그리며, 아이콘과 폰트는 `../aws-diagram-design/assets`에서 읽습니다([architecture.md](../architecture.md) 참고).

**토큰 비용**(`claude --plugin-dir . plugin details my-plugins`, 2026-11-21, 추정치):

| 구성 요소 | 항상 로드 | 호출할 때 |
|---|---|---|
| aws-blog-skills | ~530 | ~4.8k |
| aws-diagram | ~680 | ~3.5k |
| aws-diagram-design | ~630 | ~20.6k |
| kor-deslop | ~210 | ~1.4k |
| aws-ppt-skills | ~430 | ~33.2k |
| consulting-ppt-white-ppt | ~580 | ~7.2k |
| pptx-template-fill | ~570 | ~3.6k |
| aws-reports | ~540 | ~3.7k |
| html-report | ~360 | ~2.7k |
| techblogs | ~480 | ~5.6k |
| aws-infographic | ~390 | ~4.9k |
| ui-deslop | ~420 | ~15.5k |
| eng-deslop | ~380 | ~16.5k |
| setup | ~400 | ~1.4k |
| export-diagram, import-drawio, import-mermaid | ~70, ~70, ~70 | ~740, ~1.5k, ~1.4k |
| **항상 로드 합계** | **~6.8k** | |

참조 파일은 호출 비용에 더해집니다. 이어서 실행하면 실행된 skill마다 비용이 붙습니다. 구조 다이어그램이 있는 블로그 원고는 한 세션에서 aws-blog-skills, aws-diagram-design, kor-deslop 본문을 모두 로드합니다.

### 3. 주요 결정
- 점진적 공개: description만 항상 로드하고 본문과 참조 파일은 호출할 때 로드합니다. 참조 파일은 단계마다 읽으므로 문장 교정 때 다이어그램 프로필까지 불러오지 않습니다.
- aws-reports는 보고서 유형 둘을 담은 skill 하나입니다. description이 하나라 항상 로드 비용이 ~430토큰이고(skill 두 개면 ~980), SKILL.md가 유형을 고른 뒤 벤치마크나 PoC 참조 파일로 보냅니다([ADR-003](../decisions/ADR-003-one-report-skill-global-npm.md)).
- 복사하지 않고 위임: aws-blog-skills와 aws-ppt-skills는 다이어그램 skill과 kor-deslop의 규칙을 복사하지 않고 Skill 도구로 부릅니다([ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)).
- html-report는 원고를 변환하지 않고 고정 템플릿을 채웁니다. 모델은 내용만 고치고, `check_html.py`가 짝, 순서, 번호, 토큰을 확인합니다([ADR-004](../decisions/ADR-004-html-report-template-fill.md)).
- techblogs는 조각 파일로 페이지를 빌드합니다. 모델은 `meta.json`과 언어별 본문 조각을 쓰고 `build_post.py`가 템플릿의 `<style>`과 `<script>`를 그대로 옮기며 `check_post.py`가 두 언어를 비교합니다([ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md)).
- aws-infographic은 결과물 두 가지가 같은 내용을 씁니다. 장 모듈의 `T` dict가 문구를 갖고 `buildkit.py`가 그림을 검사하며, 덱은 그림을 붙이지 않고 같은 문구를 PowerPoint 기본 개체로 다시 만듭니다([ADR-006](../decisions/ADR-006-infographic-editable-deck.md)).
- description이 이웃 skill로 안내: aws-diagram과 aws-diagram-design은 다른 종류의 그림에는 "이 플러그인의" 상대 skill을 쓰라고 적고, consulting-ppt-white-ppt는 세미나 덱에 aws-ppt-skills를 안내하며, aws-blog-skills는 블로그 원고에서 kor-deslop보다 자신이 우선한다고 적습니다.
- ui-deslop과 eng-deslop은 다른 저작자의 프롬프트를 고정한 커밋에서 복사한 것이고 수정하지 않으므로, 이 플러그인이 정하는 것은 `name`과 `description`뿐입니다. 세 deslop skill의 description은 서로를 안내합니다. 한국어 글은 kor-deslop, 영어 글은 eng-deslop, 화면은 ui-deslop으로 갑니다([ADR-008](../decisions/ADR-008-vendored-skills-synced-by-pull-request.md)).
- 기계적 규칙은 종료 코드가 있는 스크립트로 둡니다(`lint_prose.py`, `check_structure.py`, `check_urls.py`, `diagram_lib.py`의 기하 assert, `self_check.py`, `check_deck.py`, `qa_check.py`). SKILL.md에는 판단과 작업 순서만 남깁니다.
- 경로: `${CLAUDE_SKILL_DIR}`는 SKILL.md에서만 치환됩니다(aws-blog-skills, setup). 다이어그램과 덱 skill은 "Base directory for this skill"에서 `SKILL_DIR`을 정합니다. Bash 호출 사이에 셸 상태가 남지 않으므로 모델은 절대 경로를 씁니다([ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md)).
- kor-deslop은 빼기만 합니다. 사용자 요청, 의미 보존, 패턴 순으로 우선하며, 문장 전체 삭제는 후보로만 알립니다.
- aws-ppt-skills는 빈 마스터 위에 빌드한 뒤 `apply_template.py`로 슬라이드를 포함된 템플릿으로 옮기므로, 배경, 로고, 바닥글, 쪽 번호의 출처는 템플릿 하나뿐입니다.
- aws-blog-skills는 확정한 규칙에 `(YYYY-MM-DD 확정)`을 붙여, 이후 세션이 본문만 보고도 규칙이 언제 생겼는지 알 수 있게 합니다.

### 4. 코드 포인터
- `skills/aws-blog-skills/SKILL.md`
- `skills/aws-blog-skills/references/diagrams.md`
- `skills/aws-blog-skills/references/humanize-checklist.md`
- `skills/aws-diagram/SKILL.md`
- `skills/aws-diagram-design/SKILL.md`
- `skills/kor-deslop/SKILL.md`
- `skills/kor-deslop/references/patterns.md`
- `skills/ui-deslop/SKILL.md`
- `skills/eng-deslop/SKILL.md`
- `scripts/upstream-skills.json`
- `skills/aws-ppt-skills/SKILL.md`
- `skills/aws-ppt-skills/references/diagrams.md`
- `skills/aws-ppt-skills/references/html-deck.md`
- `skills/consulting-ppt-white-ppt/SKILL.md`
- `skills/pptx-template-fill/SKILL.md`
- `skills/aws-reports/SKILL.md`
- `skills/aws-reports/references/poc-verdict-rules.md`
- `skills/html-report/SKILL.md`
- `skills/html-report/references/design-spec.md`
- `skills/techblogs/SKILL.md`
- `skills/techblogs/references/design-spec.md`
- `skills/aws-infographic/SKILL.md`
- `skills/aws-infographic/references/ppt-deck.md`
- `skills/setup/SKILL.md`
- `commands/export-diagram.md`
- `skills/CLAUDE.md`

### 5. 상호 참조
- 관련 모듈: `skills/`(`skills/CLAUDE.md`)
- 관련 ADR: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md), [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md), [ADR-003](../decisions/ADR-003-one-report-skill-global-npm.md), [ADR-004](../decisions/ADR-004-html-report-template-fill.md), [ADR-005](../decisions/ADR-005-techblogs-personal-blog-workflow.md), [ADR-006](../decisions/ADR-006-infographic-editable-deck.md)
- 관련 런북: [release-plugin.md](../runbooks/release-plugin.md), [setup-dependencies.md](../runbooks/setup-dependencies.md)

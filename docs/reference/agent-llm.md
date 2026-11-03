# Agent · LLM / 에이전트 · LLM 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<a id="english"></a>
## English

### 1. Overview
The plugin's "model logic" is eight skills and three command prompts: Markdown instructions Claude follows
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
| kor-deslop | `skills/kor-deslop/SKILL.md` | One pass: rule priority, meaning preservation, severity-based fixes, six self-checks, three output modes | `references/patterns.md` (79 patterns and principles, read once per run) |
| aws-ppt-skills | `skills/aws-ppt-skills/SKILL.md` | Confirm theme, audience, presenter and content; paste the pptxgenjs helpers; build, apply template, lint, render, inspect | `references/diagrams.md` |
| consulting-ppt-white-ppt | `skills/consulting-ppt-white-ppt/SKILL.md` | Confirm client, logo and chapters; derive the accent; compose with `consult_helpers.js`; fix and render | `examples/build_sample.js` |
| pptx-template-fill | `skills/pptx-template-fill/SKILL.md` | Inventory shapes, write a mapping table, fill runs, cells and chart caches in place, unify fonts, QA | `references/recipes.md` |
| setup | `skills/setup/SKILL.md` | Check, install user-level items, ask before the sudo step, re-check and report `missing:` | none |
| commands | `commands/*.md` | `export-diagram`, `import-drawio`, `import-mermaid` follow the aws-diagram-design references instead of restating them | `skills/aws-diagram-design/references/export.md`, `import-*.md`, `output-spec.md` |

**How skills chain.**

| Caller | Calls | When |
|---|---|---|
| aws-blog-skills | `my-plugins:aws-diagram` | AWS service architecture figures (step 4) |
| aws-blog-skills | `my-plugins:aws-diagram-design`, then `/my-plugins:export-diagram`; `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | Structure diagrams, and redrawing existing draw.io or Mermaid figures (step 4, `references/diagrams.md`) |
| aws-blog-skills | `my-plugins:kor-deslop` (check-only) | Self-check for remaining AI tells after the draft and before packaging (step 3, `references/humanize-checklist.md`) |
| aws-ppt-skills | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design` | Architecture and structure diagrams; graphs stay native pptxgenjs charts |
| aws-blog-skills, aws-ppt-skills, consulting-ppt-white-ppt | `my-plugins:setup` | A tool or font is missing |

Charts and comparison figures specific to the blog are drawn by aws-blog-skills itself with `diagram_lib.py`,
which reads icons and fonts from `../aws-diagram-design/assets` (see [architecture.md](../architecture.md)).

**Token cost** (`claude --plugin-dir . plugin details my-plugins`, 2026-11-03; estimates):

| Component | Always-on | On invoke |
|---|---|---|
| aws-blog-skills | ~380 | ~4.7k |
| aws-diagram | ~530 | ~3.2k |
| aws-diagram-design | ~490 | ~19.2k |
| kor-deslop | ~130 | ~1.2k |
| aws-ppt-skills | ~230 | ~29.6k |
| consulting-ppt-white-ppt | ~460 | ~6.9k |
| pptx-template-fill | ~450 | ~3.5k |
| setup | ~270 | ~1.2k |
| export-diagram, import-drawio, import-mermaid | ~60, ~60, ~50 | ~740, ~1.5k, ~1.4k |
| **Total always-on** | **~3.1k** | |

References come on top of the on-invoke figure. A chained run pays for each skill that fires: a blog post with
a structure diagram loads aws-blog-skills, aws-diagram-design and kor-deslop bodies in the same session.

### 3. Key Decisions
- Progressive disclosure: only descriptions are always loaded; bodies and references load on invoke, and
  references load per step, so a sentence fix does not pull in the diagram profile.
- Delegate, don't copy: aws-blog-skills and aws-ppt-skills call the diagram skills and kor-deslop through the
  Skill tool instead of copying their rules ([ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)).
- Descriptions route between neighbours: aws-diagram and aws-diagram-design each name the other "in this
  plugin" for the other kind of figure; consulting-ppt-white-ppt names aws-ppt-skills for seminar decks;
  aws-blog-skills states that it takes precedence over kor-deslop for blog drafts.
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
- `skills/aws-ppt-skills/SKILL.md`
- `skills/aws-ppt-skills/references/diagrams.md`
- `skills/consulting-ppt-white-ppt/SKILL.md`
- `skills/pptx-template-fill/SKILL.md`
- `skills/setup/SKILL.md`
- `commands/export-diagram.md`
- `skills/CLAUDE.md`

### 5. Cross-references
- Related modules: `skills/` (`skills/CLAUDE.md`)
- Related ADRs: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md),
  [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- Related runbooks: [release-plugin.md](../runbooks/release-plugin.md),
  [setup-dependencies.md](../runbooks/setup-dependencies.md)

<a id="korean"></a>
## 한국어

### 1. 개요
이 플러그인의 "모델 로직"은 skill 8개와 command 프롬프트 3개입니다. 사용자의 Claude Code 세션 안에서 Claude가 따르는 Markdown 지침이며, SDK 호출, 프롬프트 템플릿 파일, 하위 에이전트, 모델 설정은 없습니다. Claude Code는 모든 skill과 command의 `description`을 매 세션 로드하고, skill이 실행될 때 SKILL.md 본문을, 단계가 요구할 때만 참조 파일을 읽습니다. skill끼리는 Skill 도구로 `my-plugins:<skill>`을 불러 이어지며, 결정적 검사는 모델이 눈으로 판단하는 대신 실행해야 하는 함께 배포되는 스크립트입니다.

### 2. 구성요소
| skill | 진입점 | 모델이 하는 일 | 필요할 때 읽는 것 |
|---|---|---|---|
| aws-blog-skills | `skills/aws-blog-skills/SKILL.md` | 0~7단계: 범위, 사실과 URL 검증, 골격과 초안, 문장 규칙과 윤문, 다이어그램, 구조 검사, 패키징, 규칙 등록 | 단계별 `references/`: structure, style, humanize-checklist, verification, diagrams, exemplars, collaboration |
| aws-diagram | `skills/aws-diagram/SKILL.md` | 시스템을 AWS 서비스로 대응시키고, `find_icon.py`로 정확한 아이콘을 찾아 SVG를 짜고, `embed.py`로 아이콘을 내장 | `references/diagram_guide.md`(전체를 읽음) |
| aws-diagram-design | `skills/aws-diagram-design/SKILL.md` | 의미 패턴과 시각 유형 27가지 중 하나를 골라 4px 그리드로 HTML/SVG를 그리고, taste gate를 통과시킨 뒤 내보내기 | 고른 유형의 `references/type-*.md`, `style-guide.md`, `semantic-patterns.md`, `animation.md`, 내보내기와 가져오기 참조 |
| kor-deslop | `skills/kor-deslop/SKILL.md` | 한 번에 처리: 규칙 우선순위, 의미 보존, 심각도별 수정, 자체 점검 6항목, 결과 전달 방식 3가지 | `references/patterns.md`(패턴과 원칙 79개, 실행마다 한 번) |
| aws-ppt-skills | `skills/aws-ppt-skills/SKILL.md` | 테마, 청중, 발표자, 내용을 확인하고 pptxgenjs 헬퍼를 붙여 빌드, 템플릿 적용, lint, 렌더, 눈으로 확인 | `references/diagrams.md` |
| consulting-ppt-white-ppt | `skills/consulting-ppt-white-ppt/SKILL.md` | 고객 이름, 로고, 챕터를 확인하고 강조색을 뽑은 뒤 `consult_helpers.js`로 짜고, 고치고 렌더 | `examples/build_sample.js` |
| pptx-template-fill | `skills/pptx-template-fill/SKILL.md` | 도형 인벤토리, 매핑 표 작성, run, 표 셀, 차트 캐시를 제자리에서 채우고 폰트 통일, QA | `references/recipes.md` |
| setup | `skills/setup/SKILL.md` | 점검, 사용자 영역 설치, sudo 단계 전에 허락받기, 재점검과 `missing:` 보고 | 없음 |
| command | `commands/*.md` | `export-diagram`, `import-drawio`, `import-mermaid`는 aws-diagram-design 참조를 다시 적지 않고 따름 | `skills/aws-diagram-design/references/export.md`, `import-*.md`, `output-spec.md` |

**skill이 이어지는 방식.**

| 호출하는 쪽 | 부르는 것 | 언제 |
|---|---|---|
| aws-blog-skills | `my-plugins:aws-diagram` | AWS 서비스 아키텍처 그림(4단계) |
| aws-blog-skills | `my-plugins:aws-diagram-design` 뒤 `/my-plugins:export-diagram`, `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | 구조 다이어그램, 기존 draw.io나 Mermaid 그림 다시 그리기(4단계, `references/diagrams.md`) |
| aws-blog-skills | `my-plugins:kor-deslop`(점검만) | 초안 완성 직후와 패키징 직전의 자가 점검에서 남은 AI 티 확인(3단계, `references/humanize-checklist.md`) |
| aws-ppt-skills | `my-plugins:aws-diagram`, `my-plugins:aws-diagram-design` | 아키텍처와 구조 다이어그램. 그래프는 pptxgenjs 기본 차트로 유지 |
| aws-blog-skills, aws-ppt-skills, consulting-ppt-white-ppt | `my-plugins:setup` | 도구나 폰트가 없을 때 |

블로그 고유의 차트와 비교 그림은 aws-blog-skills가 `diagram_lib.py`로 직접 그리며, 아이콘과 폰트는 `../aws-diagram-design/assets`에서 읽습니다([architecture.md](../architecture.md) 참고).

**토큰 비용**(`claude --plugin-dir . plugin details my-plugins`, 2026-11-03, 추정치):

| 구성 요소 | 항상 로드 | 호출할 때 |
|---|---|---|
| aws-blog-skills | ~380 | ~4.7k |
| aws-diagram | ~530 | ~3.2k |
| aws-diagram-design | ~490 | ~19.2k |
| kor-deslop | ~130 | ~1.2k |
| aws-ppt-skills | ~230 | ~29.6k |
| consulting-ppt-white-ppt | ~460 | ~6.9k |
| pptx-template-fill | ~450 | ~3.5k |
| setup | ~270 | ~1.2k |
| export-diagram, import-drawio, import-mermaid | ~60, ~60, ~50 | ~740, ~1.5k, ~1.4k |
| **항상 로드 합계** | **~3.1k** | |

참조 파일은 호출 비용에 더해집니다. 이어서 실행하면 실행된 skill마다 비용이 붙습니다. 구조 다이어그램이 있는 블로그 원고는 한 세션에서 aws-blog-skills, aws-diagram-design, kor-deslop 본문을 모두 로드합니다.

### 3. 주요 결정
- 점진적 공개: description만 항상 로드하고 본문과 참조 파일은 호출할 때 로드합니다. 참조 파일은 단계마다 읽으므로 문장 교정 때 다이어그램 프로필까지 불러오지 않습니다.
- 복사하지 않고 위임: aws-blog-skills와 aws-ppt-skills는 다이어그램 skill과 kor-deslop의 규칙을 복사하지 않고 Skill 도구로 부릅니다([ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)).
- description이 이웃 skill로 안내: aws-diagram과 aws-diagram-design은 다른 종류의 그림에는 "이 플러그인의" 상대 skill을 쓰라고 적고, consulting-ppt-white-ppt는 세미나 덱에 aws-ppt-skills를 안내하며, aws-blog-skills는 블로그 원고에서 kor-deslop보다 자신이 우선한다고 적습니다.
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
- `skills/aws-ppt-skills/SKILL.md`
- `skills/aws-ppt-skills/references/diagrams.md`
- `skills/consulting-ppt-white-ppt/SKILL.md`
- `skills/pptx-template-fill/SKILL.md`
- `skills/setup/SKILL.md`
- `commands/export-diagram.md`
- `skills/CLAUDE.md`

### 5. 상호 참조
- 관련 모듈: `skills/`(`skills/CLAUDE.md`)
- 관련 ADR: [ADR-001](../decisions/ADR-001-claude-code-skill-conventions.md), [ADR-002](../decisions/ADR-002-merge-four-plugins-into-one.md)
- 관련 런북: [release-plugin.md](../runbooks/release-plugin.md), [setup-dependencies.md](../runbooks/setup-dependencies.md)

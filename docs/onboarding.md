# Onboarding

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Prerequisites
- git, Bash 4+, `jq`, Python 3, `zip`
- Claude Code CLI (for `claude plugin validate`, `claude plugin details` and `--plugin-dir`)
- Node.js and npm for the deck skills
- Everything else the skills need (uv, Playwright Chromium, fonts, pptxgenjs, python-pptx, LibreOffice,
  Poppler, rsvg-convert) is checked and installed by `bash skills/setup/scripts/setup.sh`
  ([setup-dependencies.md](runbooks/setup-dependencies.md))

## Setup
```bash
git clone https://github.com/whchoi98/my-plugins.git
cd my-plugins
bash scripts/setup.sh                      # dev: checks tools, chmod hooks and scripts, installs git hooks
bash skills/setup/scripts/setup.sh         # user deps: check only; add "install" or "install --sudo"
bash tests/run-all.sh                      # all harness tests
```

## Try a working-tree change
```bash
claude --plugin-dir .        # loads this checkout as a plugin for one session
```
Inside the session, call the skill explicitly, for example `/my-plugins:aws-blog-skills` or
`/my-plugins:aws-diagram-design`. If `my-plugins@my-plugins` is also installed, or any of the four standalone
plugins (`aws-blog-skills@aws-blog-skills`, `aws-diagrams@aws-diagrams`, `kor-writing@kor-writing`,
`aws-deck@whchoi`) or their claude.ai-synced copies, disable them for the test so the right copy fires.

## Where things live
| Need | File |
|---|---|
| Conventions and sync rules | `CLAUDE.md`, `skills/CLAUDE.md`, `tests/CLAUDE.md` |
| Blog workflow | `skills/aws-blog-skills/SKILL.md`; a writing rule in `references/style.md` is mirrored in `scripts/lint_prose.py` |
| Blog draft skeleton and author bio | `skills/aws-blog-skills/references/structure.md` and `assets/templates/blog-template.md` |
| AWS architecture diagrams | `skills/aws-diagram/SKILL.md`, `references/diagram_guide.md`, `scripts/find_icon.py` |
| Structure diagrams and shared assets | `skills/aws-diagram-design/SKILL.md`, `references/`, `assets/` |
| Export and import commands | `commands/*.md`, which follow `skills/aws-diagram-design/references/export.md` and `import-*.md` |
| Korean AI-tell rules | `skills/kor-deslop/SKILL.md` and its rulebook in `references/` |
| Deck skills | `skills/aws-ppt-skills/`, `skills/consulting-ppt-white-ppt/`, `skills/pptx-template-fill/` |
| External tools and fonts | `skills/setup/scripts/setup.sh`, `skills/setup/SKILL.md` |
| Diagram guides and samples | `docs/diagrams/` |

## First tasks
1. Read `CLAUDE.md` and [architecture.md](architecture.md)
2. Run `bash tests/run-all.sh structure` and read the suites under `tests/structure/`
3. Make a small rule change in one skill, run the tests, and follow [release-plugin.md](runbooks/release-plugin.md)
   to ship it

---

<a id="korean"></a>

# 한국어

## 사전 요구 사항
- git, Bash 4 이상, `jq`, Python 3, `zip`
- Claude Code CLI(`claude plugin validate`, `claude plugin details`, `--plugin-dir`용)
- 덱 skill용 Node.js와 npm
- 그 밖에 skill이 쓰는 것(uv, Playwright Chromium, 폰트, pptxgenjs, python-pptx, LibreOffice, Poppler, rsvg-convert)은 `bash skills/setup/scripts/setup.sh`가 점검하고 설치합니다([setup-dependencies.md](runbooks/setup-dependencies.md))

## 설정
```bash
git clone https://github.com/whchoi98/my-plugins.git
cd my-plugins
bash scripts/setup.sh                      # dev: checks tools, chmod hooks and scripts, installs git hooks
bash skills/setup/scripts/setup.sh         # user deps: check only; add "install" or "install --sudo"
bash tests/run-all.sh                      # all harness tests
```

## 작업 트리 변경 시험
```bash
claude --plugin-dir .        # loads this checkout as a plugin for one session
```
세션 안에서는 `/my-plugins:aws-blog-skills`나 `/my-plugins:aws-diagram-design`처럼 skill을 직접 호출합니다. `my-plugins@my-plugins`가 설치되어 있거나, 단독 플러그인 네 개(`aws-blog-skills@aws-blog-skills`, `aws-diagrams@aws-diagrams`, `kor-writing@kor-writing`, `aws-deck@whchoi`) 또는 claude.ai에서 동기화된 사본이 있으면, 원하는 사본이 실행되도록 시험하는 동안 비활성화합니다.

## 파일 위치
| 필요한 것 | 파일 |
|---|---|
| 규칙과 동기화 규칙 | `CLAUDE.md`, `skills/CLAUDE.md`, `tests/CLAUDE.md` |
| 블로그 워크플로 | `skills/aws-blog-skills/SKILL.md`. 문장 규칙은 `references/style.md`에 두고 `scripts/lint_prose.py`에도 반영 |
| 블로그 원고 골격과 저자 소개 | `skills/aws-blog-skills/references/structure.md`와 `assets/templates/blog-template.md` |
| AWS 아키텍처 다이어그램 | `skills/aws-diagram/SKILL.md`, `references/diagram_guide.md`, `scripts/find_icon.py` |
| 구조 다이어그램과 공용 assets | `skills/aws-diagram-design/SKILL.md`, `references/`, `assets/` |
| 내보내기와 가져오기 command | `commands/*.md`. `skills/aws-diagram-design/references/export.md`와 `import-*.md`를 따름 |
| 한국어 AI 티 규칙 | `skills/kor-deslop/SKILL.md`와 `references/`의 규칙집 |
| 덱 skill | `skills/aws-ppt-skills/`, `skills/consulting-ppt-white-ppt/`, `skills/pptx-template-fill/` |
| 외부 프로그램과 폰트 | `skills/setup/scripts/setup.sh`, `skills/setup/SKILL.md` |
| 다이어그램 가이드와 샘플 | `docs/diagrams/` |

## 첫 작업
1. `CLAUDE.md`와 [architecture.md](architecture.md)를 읽습니다
2. `bash tests/run-all.sh structure`를 실행하고 `tests/structure/`의 테스트를 읽습니다
3. skill 하나에서 작은 규칙을 고치고 테스트를 실행한 뒤, [release-plugin.md](runbooks/release-plugin.md)를 따라 배포합니다

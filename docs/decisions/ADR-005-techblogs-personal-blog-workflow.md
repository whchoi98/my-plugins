# ADR-005: techblogs lives in the plugin and builds blog posts from fragments with its own template

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Accepted (2026-11-15)

## Context
The author publishes posts on a personal tech blog, whchoi98.github.io (Jekyll on GitHub Pages). A post there is
three things in `docs/techblog/<category>/`: a front matter file (`<slug>.md`, `layout: report`), a bilingual report
page (`<slug>-report.html`) that the blog's report layout embeds in an iframe, and an image folder
(`<slug>-assets/`). A user-level skill of the same name existed before in `~/.claude/skills/techblogs`.

The work has the same steps as aws-blog-skills: fix the material and scope, verify facts and every URL, write the
Korean text, remove AI tells, draw figures, register confirmed rules. Only the destination differs. A post can
also be an AWS Korea Tech Blog post published again on the personal blog. A user-level skill has no sibling path
to the aws-blog-skills linter, URL checker and style references, is not covered by this repository's tests, and
is not installed with the plugin.

html-report (ADR-004) already ships a page with the same look: one column up to 1440px, NanumSquareOTF_ac and
D2Coding, light and dark themes, a language switch. Three decisions were open: where the blog skill lives, how a
page is produced, and whether it shares the html-report template.

## Options Considered

### Where the skill lives

#### Option 1: Keep it as a user-level skill
- **Pros**: a change needs no release; nobody else receives a skill made for one blog
- **Cons**: no sibling path to `../aws-blog-skills/scripts/lint_prose.py`, `check_urls.py` and the style references,
  so they are copied or found through a plugin cache glob; no tests and no version; each machine needs its own copy

#### Option 2: Add it to my-plugins
- **Pros**: reuses aws-blog-skills files by sibling paths and calls kor-deslop, aws-diagram, aws-diagram-design and
  setup in the same namespace; the same harness, mutation-checked tests and release procedure
- **Cons**: a skill for one blog ships to every installer; every change under `skills/techblogs/` is a release

### How a page is produced

#### Option 1: Copy the template and fill it by hand, as html-report does
- **Pros**: no build script; one file to edit
- **Cons**: a post is far longer than a report and exists twice, once per language; the front matter file, the
  section menu, the source table and the canonical link repeat values that then drift apart; nothing stops an edit
  to `<style>` or `<script>` except the checker

#### Option 2: A Markdown draft and a renderer
- **Pros**: the model writes Markdown
- **Cons**: figures with captions, captioned tables, code boxes with a copy button and status pills each need
  syntax first; two drafts per post; a renderer to maintain

#### Option 3: Fragment files filled into the template by a script, then checked
- **Pros**: the model writes `meta.json` and one body fragment per language; `build_post.py` generates the head, the
  section menu, the source table, the closing notes and the front matter file from `meta.json` in one place and
  copies `<style>` and `<script>` unchanged; an imported AWS blog post maps onto the fragment markup directly
- **Cons**: fragments are still HTML written by hand; a checker has to compare the two languages

### Whether the template is shared with html-report

#### Option 1: One template for both skills
- **Pros**: one set of design values
- **Cons**: the blog page needs what a shared report must not have, and the reverse (see Decision)

#### Option 2: A template of its own
- **Pros**: each page keeps the structure its reader needs
- **Cons**: colors, fonts and box styles exist in two templates and can drift

## Decision
The skill moves into the plugin as `skills/techblogs/` and replaces the user-level skill.

A post is built, not hand-filled. The work folder holds `meta.json`, `ko.body.html`, `en.body.html` and `images/`;
`scripts/build_post.py` fills `assets/template.html` and writes the report page, the front matter file and the
image folder into `out/`. Corrections go into the fragments and the post is built again; `out/` is never edited.
`scripts/check_post.py` verifies what the build cannot guarantee: the same sections and the same number of
figures, tables, code boxes and quote boxes in both languages, caption numbers, image files, banned symbols and the
front matter. It also fails a page whose `<style>` or `<script>` differs from the template, so a design change is
made in `references/design-spec.md`, `assets/template.html` and `scripts/check_post.py` together.
`scripts/import_aws_post.py` turns a published AWS blog post into the same work folder, and
`scripts/place_post.py` copies a built post into the blog repository and builds the site. It never runs git:
a push to that repository publishes the site, so staging, commit and push stay with the user.

The template keeps the names the blog's report layout depends on: `div.wrap.page`, `nav.top.theme-bar`, the
`data-theme` and `data-lang` attributes on `html` with the `themechange` and `langchange` events, and the storage
keys `techblogs-theme` and `techblogs-lang`. `tests/structure/test-techblogs.sh` fails when one of them is renamed.

The template is not shared with html-report, for three reasons:
- **Blog embedding**: the blog layout embeds the page in an iframe, hides its top bar and switches theme and
  language from outside through the names above. html-report pages are opened on their own and have no such contract.
- **Section menu**: a post has a sideways menu of its sections that stays at the top when the page is opened alone,
  and each language is a whole column (`div.col.l-ko`, `div.col.l-en`). html-report has a fixed page order with a
  source table and a method section, and pairs each Korean element with its English one.
- **Images as files**: a post keeps its images in `<slug>-assets/` beside the page, and the blog serves them as
  files. html-report embeds images as data URIs because the page is shared as one file.

## Consequences

### Positive
- The blog workflow reuses the aws-blog-skills linter, URL checker and references instead of copying them, and is
  covered by the repository's tests
- The report page, its menu, its source table and the front matter file come from one `meta.json`, so they cannot
  disagree
- A changed template reaches every post by rebuilding it; no page carries its own edited CSS

### Negative
- Every installer receives a skill that targets one blog: the site address in `build_post.py` and the
  `docs/techblog/<category>/` layout in `place_post.py` are that blog's
- Two templates (html-report, techblogs) hold similar colors, fonts and box styles and are kept in step by hand
- Posts already placed keep the old look until they are rebuilt and placed again
- `place_post.py --build` needs the blog repository's Bundler and Jekyll, which `setup` does not install

## References
- `skills/techblogs/SKILL.md`, `skills/techblogs/references/design-spec.md`, `skills/techblogs/references/publish.md`
- `tests/structure/test-techblogs.sh`
- [ADR-002](ADR-002-merge-four-plugins-into-one.md), [ADR-004](ADR-004-html-report-template-fill.md)

---

<a id="korean"></a>

# 한국어

## 상태
승인(2026-11-15)

## 배경
글쓴이는 개인 기술 블로그 whchoi98.github.io(GitHub Pages의 Jekyll)에 글을 올립니다. 이 블로그의 글 한 편은 `docs/techblog/<분류 폴더>/` 아래의 세 가지로 이루어집니다. front matter 파일(`<slug>.md`, `layout: report`), 블로그의 report 레이아웃이 iframe으로 넣는 한영 리포트 페이지(`<slug>-report.html`), 그림 폴더(`<slug>-assets/`)입니다. 이전에는 같은 이름의 사용자 개인 skill이 `~/.claude/skills/techblogs`에 있었습니다.

작업 절차는 aws-blog-skills와 같습니다. 소재와 범위 확정, 사실과 모든 URL 검증, 한국어 본문 작성, AI 티 제거, 그림 작성, 확정한 규칙 등록 순서로 진행합니다. 올리는 곳만 다릅니다. AWS Korea Tech Blog에 게시한 글을 개인 블로그에 다시 싣는 경우도 있습니다. 사용자 개인 skill은 aws-blog-skills의 문장 검사기, URL 검사기, 문체 참조 파일을 옆 skill 경로로 찾을 수 없고 이 저장소의 테스트를 받지 않으며 플러그인과 함께 설치되지 않습니다.

html-report(ADR-004)가 이미 같은 모양의 페이지를 배포합니다. 최대 1440px 한 컬럼, NanumSquareOTF_ac와 D2Coding, 라이트와 다크 테마, 언어 전환을 씁니다. 정할 것은 세 가지였습니다. 블로그 skill을 어디에 둘지, 페이지를 어떻게 만들지, html-report와 템플릿을 함께 쓸지입니다.

## 검토한 선택지

### skill을 두는 곳

#### 선택지 1: 사용자 개인 skill로 유지
- **장점**: 고칠 때 릴리스가 필요 없습니다. 블로그 하나를 위한 skill이 다른 사람에게 배포되지 않습니다
- **단점**: `../aws-blog-skills/scripts/lint_prose.py`, `check_urls.py`, 문체 참조 파일을 옆 skill 경로로 찾을 수 없어 복사하거나 플러그인 캐시 glob으로 찾아야 합니다. 테스트와 버전이 없고 머신마다 따로 복사해야 합니다

#### 선택지 2: my-plugins에 추가
- **장점**: aws-blog-skills의 파일을 옆 skill 경로로 다시 쓰고 kor-deslop, aws-diagram, aws-diagram-design, setup을 같은 이름 공간에서 부릅니다. 같은 하네스, 변이로 확인한 테스트, 같은 릴리스 절차를 씁니다
- **단점**: 블로그 하나를 위한 skill이 모든 설치자에게 배포됩니다. `skills/techblogs/` 아래의 변경은 모두 릴리스입니다

### 페이지를 만드는 방식

#### 선택지 1: html-report처럼 템플릿을 복사해 직접 채움
- **장점**: 빌드 스크립트가 없고 고칠 파일이 하나입니다
- **단점**: 글은 보고서보다 훨씬 길고 언어마다 한 번씩 두 번 들어갑니다. front matter 파일, 이동 메뉴, 참고 자료 표, canonical 링크에 같은 값이 반복되어 서로 어긋납니다. `<style>`이나 `<script>`를 고치는 일을 검사기 말고는 막지 못합니다

#### 선택지 2: Markdown 원고와 변환기
- **장점**: 모델이 Markdown을 씁니다
- **단점**: 캡션이 있는 그림과 표, 복사 버튼이 있는 코드 상자, 상태 알약마다 문법부터 정해야 합니다. 글마다 원고가 두 개이고 변환기를 관리해야 합니다

#### 선택지 3: 조각 파일을 스크립트가 템플릿에 채우고 검사
- **장점**: 모델은 `meta.json`과 언어별 본문 조각만 씁니다. `build_post.py`가 머리, 이동 메뉴, 참고 자료 표, 끝의 고지, front matter 파일을 `meta.json` 하나에서 만들고 `<style>`과 `<script>`를 그대로 옮깁니다. 가져온 AWS 블로그 글이 조각의 마크업에 바로 대응합니다
- **단점**: 조각은 여전히 손으로 쓰는 HTML입니다. 두 언어가 같은지는 검사기가 비교해야 합니다

### html-report와 템플릿을 함께 쓸지

#### 선택지 1: 두 skill이 템플릿 하나를 씀
- **장점**: 디자인 값이 한 벌입니다
- **단점**: 블로그 페이지에 필요한 것이 공유용 보고서에는 있으면 안 되고 그 반대도 같습니다(결정 참고)

#### 선택지 2: 자기 템플릿을 둠
- **장점**: 페이지마다 읽는 사람에게 필요한 구조를 유지합니다
- **단점**: 색, 글꼴, 상자 스타일이 템플릿 두 곳에 있어 어긋날 수 있습니다

## 결정
skill을 플러그인의 `skills/techblogs/`로 옮기고 사용자 개인 skill을 대체합니다.

글은 직접 채우지 않고 빌드합니다. 작업 폴더에 `meta.json`, `ko.body.html`, `en.body.html`, `images/`를 두고 `scripts/build_post.py`가 `assets/template.html`에 채워 리포트 페이지, front matter 파일, 그림 폴더를 `out/`에 씁니다. 고칠 때는 조각을 고치고 다시 빌드하며 `out/`은 직접 고치지 않습니다. `scripts/check_post.py`는 빌드가 보장하지 못하는 것을 확인합니다. 두 언어의 절이 같은지, 그림, 표, 코드 상자, 인용 상자의 수가 같은지, 캡션 번호, 그림 파일, 금지 기호, front matter를 봅니다. `<style>`이나 `<script>`가 템플릿과 다른 페이지도 실패로 처리하므로, 디자인을 바꿀 때는 `references/design-spec.md`, `assets/template.html`, `scripts/check_post.py`를 함께 고칩니다. `scripts/import_aws_post.py`는 게시된 AWS 블로그 글을 같은 작업 폴더로 옮기고 `scripts/place_post.py`는 빌드한 글을 블로그 저장소에 복사해 사이트를 빌드합니다. git은 실행하지 않습니다. 그 저장소는 push하면 사이트가 배포되므로 스테이징, 커밋, push는 사용자가 합니다.

템플릿은 블로그의 report 레이아웃이 의존하는 이름을 유지합니다. `div.wrap.page`, `nav.top.theme-bar`, `html`의 `data-theme`과 `data-lang` 속성 및 `themechange`와 `langchange` 이벤트, 저장 키 `techblogs-theme`과 `techblogs-lang`입니다. 이 이름을 바꾸면 `tests/structure/test-techblogs.sh`가 실패합니다.

html-report와 템플릿을 공유하지 않는 이유는 세 가지입니다.
- **블로그 임베드 연동**: 블로그 레이아웃이 페이지를 iframe으로 넣고 상단 막대를 숨기며 위 이름으로 테마와 언어를 바깥에서 바꿉니다. html-report 페이지는 단독으로 열며 이런 약속이 없습니다.
- **이동 메뉴**: 글에는 절로 가는 가로 메뉴가 있고 문서만 열면 화면 위쪽에 붙습니다. 언어마다 컬럼 하나(`div.col.l-ko`, `div.col.l-en`)를 통째로 씁니다. html-report는 출처 표와 조사 방법이 있는 고정된 페이지 순서를 쓰고 한국어 요소마다 영어 요소를 짝지어 둡니다.
- **그림을 파일로 둠**: 글의 그림은 페이지 옆 `<slug>-assets/`에 두고 블로그가 파일로 제공합니다. html-report는 파일 하나로 공유하는 페이지라서 그림을 data URI로 넣습니다.

## 결과

### 긍정적
- 블로그 워크플로가 aws-blog-skills의 문장 검사기, URL 검사기, 참조 파일을 복사하지 않고 다시 쓰며 저장소의 테스트를 받습니다
- 리포트 페이지, 이동 메뉴, 참고 자료 표, front matter 파일이 `meta.json` 하나에서 나오므로 서로 어긋나지 않습니다
- 템플릿을 바꾸면 글을 다시 빌드해 반영합니다. 페이지마다 따로 고친 CSS가 남지 않습니다

### 부정적
- 블로그 하나를 위한 skill이 모든 설치자에게 배포됩니다. `build_post.py`의 사이트 주소와 `place_post.py`의 `docs/techblog/<분류 폴더>/` 구조는 그 블로그의 것입니다
- 템플릿 두 개(html-report, techblogs)에 비슷한 색, 글꼴, 상자 스타일이 있고 사람이 맞춰야 합니다
- 이미 배치한 글은 다시 빌드해 배치하기 전까지 이전 모양으로 남습니다
- `place_post.py --build`에는 블로그 저장소의 Bundler와 Jekyll이 필요하고 `setup`은 이를 설치하지 않습니다

## 참고
- `skills/techblogs/SKILL.md`, `skills/techblogs/references/design-spec.md`, `skills/techblogs/references/publish.md`
- `tests/structure/test-techblogs.sh`
- [ADR-002](ADR-002-merge-four-plugins-into-one.md), [ADR-004](ADR-004-html-report-template-fill.md)

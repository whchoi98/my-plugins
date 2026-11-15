# techblogs 페이지 규격

`assets/template.html`이 디자인의 기준이다. 글을 쓸 때는 작업 폴더의 `meta.json`, `ko.body.html`, `en.body.html`만 만들고, 페이지는 `scripts/build_post.py`가 조립한다. `<style>`과 `<script>`는 템플릿에서만 고친다. `scripts/check_post.py`가 리포트의 두 블록이 템플릿과 같은지 비교한다.

## 디자인 요약

| 항목 | 값 |
|---|---|
| 폭 | 한 컬럼, `.wrap` 최대 1440px(좌우 여백 포함). 본문, 표, 그림이 같은 폭을 쓴다 |
| 글꼴 | 본문과 제목 NanumSquareOTF_ac(400, 700), 코드 D2Coding. 설치된 글꼴을 먼저 쓰고 없으면 블로그의 `/assets/fonts/`에서 받는다 |
| 색 | 바탕 `--bg`, 상자 `--surface`, 글자 `--ink`, 보조 글자 `--muted`, 선 `--line`, 강조 `--accent`. 다크 값은 `:root[data-theme="dark"]`와 시스템 설정 양쪽에 같은 값으로 있다 |
| 절 머리 | 위쪽 2px 선, 작은 번호(`p.eyebrow`), 26px 제목 |
| 상자 | 표, 그림, 코드 상자는 흰 바탕(`--surface`)에 1px 선, 모서리 10px |
| 언어 | `html[data-lang]`이 `.l-ko`와 `.l-en` 중 하나를 숨긴다. 저장 키 `techblogs-lang` |
| 테마 | `html[data-theme]`, 저장 키 `techblogs-theme`. 값이 없으면 시스템 설정을 따른다 |

## 블로그 레이아웃과 맞물리는 부분

블로그의 `_layouts/report.html`은 리포트를 iframe으로 넣고 다음에 의존한다. 템플릿에서 이 이름들을 바꾸지 않는다.

- `div.wrap.page`: 레이아웃이 `.page`를 찾아야 초기화한다.
- `nav.top.theme-bar`: 블로그 상단의 전환 버튼이 기준이므로 레이아웃이 `.theme-bar`를 숨긴다. 문서만 열면 보인다.
- `html`의 `data-theme`, `data-lang`: 레이아웃이 직접 바꾸고 `themechange`, `langchange` 이벤트를 보낸다.
- 저장 키 `techblogs-theme`, `techblogs-lang`: 레이아웃이 iframe을 띄우기 전에 써 둔다.
- 이동 메뉴(`nav.toc`)는 임베드 화면에서는 위에 붙지 않는다. iframe 높이가 본문 전체이기 때문이다. 문서만 열면 붙는다.

## meta.json

```json
{
  "slug": "eks-node-startup",
  "category": "Container",
  "category_dir": "container",
  "icon": "eks",
  "date": "2026-11-15",
  "minutes": 0,
  "tags": ["Amazon EKS", "Karpenter"],
  "title":   {"ko": "제목", "en": "Title"},
  "excerpt": {"ko": "목록 카드에 보일 한두 문장", "en": "One or two sentences for the list card"},
  "thesis":  {"ko": "이 글이 답하는 질문과 결론 두세 문장", "en": "The question and the answer in two or three sentences"},
  "facts":   [{"ko": "<b>요점</b> 한 줄", "en": "<b>Point</b> one line"}],
  "origin":  {"name": {"ko": "AWS 기술 블로그", "en": "AWS Tech Blog (Korean)"}, "url": "https://aws.amazon.com/ko/blogs/tech/...", "date": "2026-11-04"},
  "author":  {"ko": "글쓴이", "en": "Author"},
  "note":    {"ko": "측정 조건과 기준일 고지", "en": "Conditions and as-of date"},
  "sources": [{"title": "문서 제목", "url": "https://docs.aws.amazon.com/...", "kind": {"ko": "공식 문서", "en": "AWS docs"}, "accessed": "2026-11-15"}]
}
```

| 키 | 규칙 |
|---|---|
| `slug` | 영문 소문자, 숫자, 하이픈. 파일 이름과 주소가 된다 |
| `category`, `category_dir`, `icon` | 블로그 `_config.yml`의 `blog_categories` 이름과 그 폴더, `assets/icons`의 파일 이름 |
| `date` | 게시일. 옮겨 싣는 글은 원문 게시일을 쓴다(목록이 원문 순서대로 정렬된다) |
| `minutes` | 0이면 한국어 본문 글자 수에서 계산한다 |
| `thesis` | 머리의 요약 문단. 본문에 있는 내용만으로 쓴다 |
| `facts` | 선택. 요점 목록 3~5개. 값은 인라인 HTML(`<b>`, `<code>`)을 쓸 수 있다 |
| `origin` | 선택. 다른 곳에 먼저 게시한 글을 옮길 때만. 있으면 canonical이 원문 주소가 되고 머리와 끝에 원문 링크가 붙는다 |
| `author`, `note` | 선택. 끝의 "이 글에 대하여"에 들어간다 |
| `colophon` | 선택. "이 글에 대하여" 아래에 작은 글씨 한 줄(`p.colophon`)로 들어간다 |
| `site` | 선택. 상단 막대의 목록 링크. `{"url": "/", "ko": "기술 블로그 홈", "en": "Tech blog home"}`이 기본값이다 |
| `sources` | 참고 자료 표. 직접 열어 확인한 문서만 넣고 `accessed`에 확인한 날을 쓴다 |

`"TODO"`가 남아 있으면 빌드가 멈춘다.

## 본문 조각 (ko.body.html, en.body.html)

두 파일은 같은 순서로 같은 요소를 갖는다. 영어 파일은 절 id만 `en-sN`이다. 검사기는 절마다 h3, 그림, 표, 코드 상자, 인용 상자의 수와 그림 파일 순서가 같은지 본다.

### 절

```html
<section class="sec" id="ko-s1"><header class="sec-head"><p class="eyebrow">01</p><h2>절 제목</h2></header><div class="prose">
<p>문단</p>
<h3>작은 제목</h3>
</div></section>
```

- id는 `ko-s1`부터 순서대로 붙인다. 이동 메뉴는 `h2` 글자로 만들어진다.
- `p.eyebrow`는 절 번호(두 자리)나 짧은 꼬리표다. 번호가 없는 절(들어가며, 마치며)은 생략한다.
- 본문 요소는 `div.prose` 바로 아래에 둔다. 쓸 수 있는 인라인 태그는 `a`, `b`, `em`, `code`, `br`, `sup`, `sub`다.
- 바깥 링크는 `target="_blank" rel="noopener"`를 붙인다.
- 강조 문단은 `<blockquote><p>…</p></blockquote>`로 쓰고 절마다 하나를 넘기지 않는다.

### 표

```html
<div class="scroll"><table>
<thead>
<tr><th>항목</th><th>값</th></tr>
</thead>
<tbody>
<tr><td>이름</td><td class="num">12.5</td></tr>
</tbody>
</table></div>
<p class="cap"><b>표 1.</b> 캡션. 단위와 기준일을 적는다</p>
```

표는 항상 `div.scroll` 안에 둔다. 캡션은 표 아래 `p.cap`이고 `표 N.`(영어 `Table N.`)으로 시작하며 번호는 글 전체에서 이어진다. 상태 표시는 `<span class="pill good">`, `warn`, `bad`, `info`를 쓴다.

### 그림

```html
<figure class="fig"><div class="canvas wide"><img src="images/fig01-architecture.png" alt="그림을 보지 않아도 알 수 있는 설명" width="1280" height="720" loading="lazy"></div><figcaption><b>그림 1.</b> 캡션</figcaption></figure>
```

- 파일은 작업 폴더의 `images/`에 두고 `images/<파일>`로 가리킨다. 빌드가 `<slug>-assets/`로 옮긴다. 원격 주소와 data URI는 쓰지 않는다.
- `width`와 `height`에는 화면에 보일 크기(CSS px)를 쓴다. 파일의 실제 픽셀 폭은 그 크기 이상이어야 흐려지지 않는다. 화면 캡처처럼 좁은 그림은 이 폭으로 가운데에 놓인다.
- 구성도처럼 넓은 그림(보일 폭 900px 이상)은 `div.canvas`에 `wide`를 붙인다. 상자 폭을 채우고(최대 1280px), `width`와 `height`는 가로세로 비율로만 쓰인다. 휴대폰에서는 760px 폭으로 보이고 상자 안에서 옆으로 민다.
- 캔버스는 다크 테마에서도 흰색이다. 그림은 흰 바탕으로 그린다.
- 캡션은 `그림 N.`(영어 `Figure N.`)으로 시작한다.

### 코드 상자

```html
<div class="snippet"><div class="snippet-bar"><span class="lang">bash</span><button type="button" class="copy"><span class="i">복사</span><span class="ok">복사됨</span></button></div><pre><code>aws eks list-clusters --region ap-northeast-2</code></pre></div>
```

영어 페이지의 버튼 글자는 `Copy`, `Copied`다. 코드 안의 `<`, `>`, `&`는 `&lt;`, `&gt;`, `&amp;`로 쓴다. 코드와 명령은 두 언어에서 같고 주석만 옮긴다. 계정 ID, 내부 주소, 시크릿은 가린다.

## 글자 규칙 (검사기가 보는 것)

- 가운뎃점(·), 엠 대시(—), 엔 대시(–)는 두 언어 모두 쓰지 않는다(ERROR). 코드 안은 예외다.
- 문장 안의 화살표(→)는 말로 푼다(WARN). 표 안의 짧은 표기는 둔다.
- 영어 쪽에 한글이 남으면 WARN이다. 화면에 실제로 보이는 한국어 이름을 인용할 때만 둔다.
- 요소에 `style` 속성을 쓰지 않는다(ERROR).
- 금지 기호는 그림의 `alt`와 요약(`excerpt.ko`, meta description)에도 쓰지 않는다(ERROR).
- 영어 쪽 복사 버튼에 한글이 남으면 WARN이다.
- `--dump-ko`는 제목, 요약 문단, 요약(`excerpt.ko`), 요점, 본문, 끝의 글을 뽑는다. 표와 코드는 뺀다.

검사기가 보지 않는 규칙도 있다. 쓰는 사람이 지킨다.

- 강조 문단은 절마다 하나
- 인라인 태그는 `a`, `b`, `em`, `code`, `br`, `sup`, `sub`만
- 바깥 링크의 `rel="noopener"` (`target="_blank"`가 없을 때만 WARN)
- `excerpt.en`과 `title`의 금지 기호 (제목은 `h1`에서 걸린다)

## 템플릿에 있지만 빌드가 만들지 않는 요소

본문 조각에 직접 써도 되는 선택 요소다.

- `<p class="lede">`: `h2` 바로 아래 `header.sec-head` 안에 두는 한 줄 설명
- `<sup class="cite"><a href="#src-1">1</a></sup>`: 참고 자료 표의 행(`src-N`)을 가리키는 인용 번호
- `table.src-t` 안의 `div.meta`: 참고 자료 제목 아래의 작은 설명

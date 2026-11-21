# html-report 디자인 규격

모든 html-report 페이지가 따르는 규칙이다. 같은 값이 `assets/template.html`의 `<style>`과 `scripts/check_html.py`에 들어 있다. 보고서마다 CSS를 고치지 않는다. 규칙을 바꿀 때는 이 파일, 템플릿, 검사기를 함께 고친다.

## 토큰

| 항목 | 변수 | 라이트 | 다크 |
|---|---|---|---|
| 바탕 | `--bg` | #f3f5f8 | #0e1319 |
| 글자 | `--ink` | #15202b | #e4e9ef |
| 보조 글자 | `--muted` | #5a6774 | #9ba7b4 |
| 강조 | `--accent` | #1d5bb8 | #86abff |
| 표와 스니펫 상자 | `--surface` | #ffffff | #151c25 |
| 그림 상자 | `--fig` | #ffffff | #ffffff |
| 테두리 | `--line` | #d9dfe6 | #2a3441 |
| 챕터 구분선 | `--rule` | #c9d1db | #3a4655 |
| 강조 문단 바탕 | `--callout` | #e8f0fc | #17243a |
| 스니펫 바탕 | `--code` | #f6f8fa | #121922 |
| 상태 초록 글자 | `--ok` | #17703c | #7fd6a1 |
| 상태 초록 바탕 | `--ok-bg` | #e2f3e8 | #11301e |
| 상태 노랑 글자 | `--warn` | #8a5a00 | #f0c860 |
| 상태 노랑 바탕 | `--warn-bg` | #fdf1d2 | #382d0e |
| 상태 빨강 글자 | `--bad` | #b42318 | #ff9d94 |
| 상태 빨강 바탕 | `--bad-bg` | #fbe4e2 | #3c1a1a |

- 다크에서도 그림 상자는 흰색이다. 구성도와 차트는 흰 바탕을 기준으로 그리기 때문이다. 표와 스니펫 상자는 다크에서 어두운 면이 된다.
- 글꼴: 본문 `'NanumSquareOTF_ac', 'NanumSquareOTF', 'NanumSquare_ac', 'NanumSquare', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif`, 코드 `'D2Coding', ui-monospace, Menlo, Consolas, monospace`. NanumSquareOTF_ac가 없으면 `my-plugins:setup`이 설치하는 NanumSquareOTF를 먼저 찾고, 그다음 Apple SD Gothic Neo와 맑은 고딕으로 넘어간다. 글꼴은 파일에 넣지 않는다.
- 크기: 본문 15px, H1 `clamp(30px, 3.2vw, 44px)`, H2 26px, H3 17px, 요약 문단 17px, 캡션과 표 머리글 13px.
- 폭: 한 컬럼. `.wrap`이 최대 1440px로 가운데에 놓이고 좌우 여백은 40px이다. 본문, 그림, 표, 스니펫이 모두 이 폭을 함께 쓴다.

## 페이지 순서

`<html data-report="research">`는 자료를 찾아 정리한 조사 보고서, `<html data-report="general">`은 그 밖의 보고서다. `<main>` 바로 아래에는 다음 요소만 이 순서로 둔다.

| 순서 | 요소 | research | general |
|---|---|---|---|
| ① | 상단 막대 `header.topbar`(`main` 앞): 목록 링크 `a.list-link`, 언어 버튼 `[data-set-lang]` 두 개, 테마 버튼 `[data-set-theme]` 두 개 | 필수 | 필수 |
| ② | 머리 `header.doc-head`: 기준일 `.meta time`, 검색한 곳 `[data-meta="searched"]`, 제목 `h1`, 요약 문단 `.lead`, 태그 `.tags`, 출처 구성 목록 `.source-mix` | 모두 필수. 태그가 없으면 WARN | 기준일, 제목, 요약 문단 필수. 나머지는 해당할 때 |
| ③ | 챕터 `section.sec`: 2px 구분선(CSS), 출처 종류 `p.src-kind`, `h2` | 출처 종류 필수 | 출처 종류는 해당할 때 |
| ④ | 참조 원문 데이터 출처 표 `section.sources` | 필수 | 인용 번호가 있으면 필수 |
| ⑤ | 조사 방법 `section.method` | 필수 | 해당할 때 |
| ⑥ | 공유 범위 `p.share` 한 줄 | 필수 | 필수 |

## 두 언어를 한 파일에

한국어 요소 바로 뒤에 같은 태그의 영어 요소를 둔다. 화면에는 고른 언어 하나만 보인다.

```html
<p lang="ko">한국어 문단입니다.</p>
<p lang="en">The English paragraph.</p>
<h2><span lang="ko">1. 챕터 제목</span><span lang="en">1. Section title</span></h2>
<ul lang="ko"><li>항목</li></ul>
<ul lang="en"><li>Item</li></ul>
```

- 문단, 목록, 강조 문단 안의 문단은 요소째 짝을 만든다. 제목, 캡션, 표 칸, 단추처럼 짧은 글은 `span` 짝을 쓴다.
- `lang` 요소 안에서는 다시 짝을 만들지 않는다. 한국어 문단 안의 알약은 한국어로만 쓴다.
- 언어와 관계없는 글(제품 이름만 있는 태그, 출처의 원래 제목, 게시한 곳, 언어 버튼)은 `translate="no"`를 붙이고 한 번만 쓴다. 숫자와 코드는 짝 밖에 둬도 된다.
- `<title data-ko="…" data-en="…">`과 그림의 `alt`(한국어), `data-alt-en`(영어)은 스크립트가 언어에 맞춰 바꾼다.
- 처음에는 한국어와 시스템 테마로 열린다. 버튼으로 고른 값은 브라우저의 `html-report:lang`, `html-report:theme`에 기억되어 같은 곳에 둔 다른 보고서에서도 이어진다.

## 구성 요소

챕터:

```html
<section class="sec" id="s3">
  <p class="src-kind"><span lang="ko">공식 문서</span><span lang="en">Official docs</span></p>
  <h2><span lang="ko">3. 챕터 제목</span><span lang="en">3. Section title</span></h2>
  …
</section>
```

그림. 흰 상자 안에 넣고, 캡션은 상자 아래에 둔다. 그림 번호는 1부터 차례로 붙인다. 이미지는 작업 중에는 `images/x.png`처럼 상대 경로로 두고, `embed_images.py`가 data URI로 바꾼다. SVG는 `<svg>`째 넣어도 된다. 640px 이하에서 줄이면 읽기 어려운 작은 그림은 `class="fig fit"`으로 화면 폭에 맞춘다.

```html
<figure class="fig">
  <div class="box"><img src="images/arch.png" alt="구성도 설명" data-alt-en="Architecture description"></div>
  <figcaption><span lang="ko">그림 2. 캡션</span><span lang="en">Figure 2. Caption</span></figcaption>
</figure>
```

표. 상자 안에 넣는다. 캡션은 있으면 "표 N."으로 상자 아래에 둔다.

```html
<figure class="tbl">
  <div class="box"><table>…</table></div>
  <figcaption><span lang="ko">표 1. 캡션</span><span lang="en">Table 1. Caption</span></figcaption>
</figure>
```

강조 문단은 연한 파랑 바탕이고 왼쪽 막대가 없다. 챕터마다 하나를 넘기지 않는다.

```html
<div class="callout"><p lang="ko">…</p><p lang="en">…</p></div>
```

스니펫은 `<pre class="box"><code>…</code></pre>`로 쓴다. 인용 번호는 위 첨자로, 출처 표의 행을 가리킨다. 한 곳에 출처가 여럿이면 위 첨자 하나에 쉼표로 묶는다.

```html
<sup class="cite"><a href="#src-2">2</a></sup>
<sup class="cite"><a href="#src-1">1</a>,<a href="#src-3">3</a></sup>
```

상태는 둥근 알약이다. `ok`는 초록(확인됨, 지원, 충족), `warn`은 노랑(조건부, 부분, 확인 필요), `bad`는 빨강(지원 안 됨, 미충족), `info`는 파랑(참고)이다.

```html
<span class="pill ok"><span lang="ko">확인됨</span><span lang="en">Confirmed</span></span>
```

출처 표의 행. 번호는 `src-1`부터 차례로 붙이고, 첫 칸의 숫자와 `id`를 맞춘다. `data-kind`는 출처 구성 목록의 `data-kind`와 같은 값을 쓴다. 제목은 원문 그대로 두고 링크를 건다.

```html
<tr id="src-1" data-kind="docs"><td>1</td><td><span lang="ko">공식 문서</span><span lang="en">Official docs</span></td>
  <td><a href="https://…" translate="no">원래 제목</a></td><td translate="no">AWS</td><td>2026-11-11</td></tr>
```

출처 구성 목록은 종류마다 한 항목이다. `data-count`는 출처 표에서 그 종류의 행 수이고, 보이는 글의 숫자와 같다.

```html
<li data-kind="docs" data-count="4"><span lang="ko">공식 문서 4건</span><span lang="en">Official docs: 4</span></li>
```

조사 방법에는 검색한 기간과 검색어, 출처를 넣고 뺀 기준, 사실을 확인한 방법을 쓴다. 공유 범위는 `<p class="share">` 한 줄로, 누구에게까지 보여 줄 수 있는지 쓴다.

## 모바일

640px 이하에서는 좌우 여백이 16px로, 챕터 사이 간격이 줄어든다. 그림은 720px 폭을 유지하고 상자 안에서 가로로 밀어 본다. 표도 상자 안에서 가로로 민다. 페이지 자체는 가로로 밀리지 않아야 한다. `preview.py`가 확인한다.

## 문장

- 한국어는 AWS Korea Tech Blog 합쇼체로 쓰고 `../aws-blog-skills/references/style.md`의 금지어를 따른다.
- 가운뎃점(·), 대시(—, –), 화살표(→, ←, ⇒)를 두 언어 모두 쓰지 않는다. 나열은 쉼표나 "와", "과", "및"으로, 흐름은 문장으로 쓴다.
- 권고는 "~하는 것을 권고합니다"로 쓴다. "~하세요", "권장합니다"는 쓰지 않는다. 영어는 "We recommend …"로 쓴다.
- 영어는 한국어와 같은 내용, 같은 숫자를 담는다. 한쪽에만 문장을 더하거나 빼지 않는다.

## 검사기가 보는 것

`scripts/check_html.py`가 다음을 확인한다.

- ERROR: `data-report` 값, 기본 언어, CSS 토큰과 크기와 폭(이 파일의 값), 템플릿과 다른 `<style>`과 `<script>`, 인라인 `style` 속성과 외부 스타일시트, 왼쪽 막대(`border-left`), 페이지 순서, 상단 막대와 머리의 필수 요소, 챕터의 `h2`와 출처 종류, 두 언어 짝, 짝 밖이나 영어 쪽의 한국어, 본문과 속성 글(`<title data-ko data-en>`, `alt`, `data-alt-en`, `aria-label`)의 금지 기호, 그림과 표의 상자와 캡션 번호, 인용 번호와 출처 표 번호, 출처 구성 목록의 건수, 상대 경로 그림, 템플릿 자리 표시와 예시 문장(템플릿에서 직접 읽는다. 라벨, 태그, 검색한 곳, 출처 구성 목록, 공유 범위 줄은 빼고)
- WARN: 한다체나 해요체로 끝나는 문장(문단과 목록 항목은 마침표 없이 끝나도), "~하세요"와 "권장", 인용하지 않은 출처, 링크 없는 출처, 외부 그림, `alt`나 `data-alt-en` 없는 그림, 상자 없는 스니펫, 태그 없음
- 원래 제목처럼 `translate="no"`를 붙인 글은 원문 그대로 두므로 금지 기호를 검사하지 않는다

#!/usr/bin/env python3
"""Check an html-report page against ../references/design-spec.md.

usage: python3 check_html.py report/out/page.html [more.html ...]
       python3 check_html.py report/out/page.html --dump-ko report/out/page.ko.md

ERROR  breaks the design or the single-file rule: tokens, page order, language pairs, captions, source
       numbers, relative images, leftover template placeholders. Fix the page and check again. Exit code 1.
WARN   wording or completeness to review: a sentence not in 합쇼체, "~하세요", an uncited source, missing tags.
OK     printed when a file has neither.
--dump-ko writes the Korean text as plain Markdown lines so that ../aws-blog-skills/scripts/lint_prose.py
can sweep it. Standard library only.
"""
import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NOT_PROSE = {"head", "script", "style", "title", "code", "pre"}
HANGUL = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
FORBIDDEN = {"·": "가운뎃점", "—": "엠 대시", "–": "엔 대시", "→": "화살표", "←": "화살표", "⇒": "화살표"}
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
# Markup that exists only in the template; sample sentences are read from the template itself (template_samples).
PLACEHOLDERS = ["example.com/source-", "Source title as published", "Placeholder figure", 'data-ko="보고서 제목"',
                'data-en="Report title"', ">보고서 제목</title>"]
# Template text a finished report may keep word for word: interface labels, table heads, source kinds, status words.
LABELS = {"목록", "All reports", "라이트", "Light", "다크", "Dark", "기준일", "As of", "검색한 곳", "Searched",
          "출처 구성", "Sources", "참조 원문 데이터 출처", "Source data", "조사 방법", "Method", "번호", "No.", "종류",
          "Type", "제목", "Title", "게시한 곳", "Publisher", "확인한 날", "Checked", "공식 문서", "Official docs",
          "블로그", "Blog posts", "Blog post", "항목", "Item", "값", "Value", "상태", "Status", "확인됨", "Confirmed",
          "조건부", "Conditional", "지원 안 됨", "Not supported"}
# Parts whose template text can be right as it is (tags, searched sources, source mix, sharing line): not sample-checked.
SAMPLE_SKIP = ("topbar", "tags", "source-mix", "share")
# Attributes whose text a reader sees (tab title, image description, accessible names).
TEXT_ATTRS = ("data-ko", "data-en", "alt", "data-alt-en", "aria-label", "title")
# (pattern on whitespace-normalized CSS, what it guards). Same values as design-spec.md and the template.
CSS_RULES = [
    (r"--bg:#f3f5f8", "라이트 바탕 #f3f5f8"), (r"--ink:#15202b", "라이트 글자 #15202b"),
    (r"--muted:#5a6774", "라이트 보조 글자 #5a6774"), (r"--accent:#1d5bb8", "라이트 강조 #1d5bb8"),
    (r"--bg:#0e1319", "다크 바탕 #0e1319"), (r"--ink:#e4e9ef", "다크 글자 #e4e9ef"),
    (r"--accent:#86abff", "다크 강조 #86abff"),
    (r"@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)", "시스템 다크 설정을 따르는 규칙"),
    (r":root\[data-theme=\"dark\"\]\{", "다크 버튼 규칙"),
    (r":root\[data-lang=\"ko\"\] body \[lang=\"en\"\],:root\[data-lang=\"en\"\] body \[lang=\"ko\"\]\{display:none", "언어 전환 규칙"),
    (r"body\{[^}]*font-family:'NanumSquareOTF_ac'[^}]*'Apple SD Gothic Neo','Malgun Gothic'", "본문 글꼴 NanumSquareOTF_ac, Apple SD Gothic Neo, 맑은 고딕"),
    (r"code\{[^}]*font-family:'D2Coding'", "코드 글꼴 D2Coding"),
    (r"body\{[^}]*font-size:15px", "본문 15px"),
    (r"h1\{[^}]*font-size:clamp\(30px,[^)]*,44px\)", "H1 30~44px"),
    (r"h2\{[^}]*font-size:26px", "H2 26px"), (r"h3\{[^}]*font-size:17px", "H3 17px"),
    (r"\.lead\{[^}]*font-size:17px", "요약 문단 17px"),
    (r"\.wrap\{[^}]*max-width:1440px", "최대 폭 1440px"),
    (r"\.sec,\.sources,\.method\{[^}]*border-top:2px solid", "절마다 2px 구분선"),
    (r"\.box\{[^}]*border:1px solid[^}]*border-radius:10px", "상자 1px 테두리와 둥근 모서리 10px"),
    (r"\.callout\{[^}]*background:var\(--callout\)", "강조 문단 연한 파랑 바탕"),
    (r"\.pill\{[^}]*border-radius:999px", "상태 알약"),
    (r"@media \(max-width:640px\)\{", "640px 이하 모바일 규칙"),
]
ORDER = {"research": r"^HS+RMX$", "general": r"^HS+R?M?X$"}


class Node:
    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.parent, self.line, self.kids = tag, attrs, parent, line, []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def elements(self):
        return [k for k in self.kids if isinstance(k, Node)]

    def iter(self):
        for k in self.kids:
            if isinstance(k, Node):
                yield k
                yield from k.iter()

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def text(self, ticks=False, drop=()):
        """Text of the subtree; `drop` names classes whose elements are left out (e.g. cite numbers, pills)."""
        out = []
        for k in self.kids:
            if isinstance(k, str):
                out.append(k)
            elif k.tag in ("script", "style") or any(c in k.classes for c in drop):
                continue
            elif ticks and k.tag == "code":
                out.append("`" + k.text() + "`")
            else:
                out.append(k.text(ticks, drop))
        return "".join(out)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None, 0)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.cur, self.getpos()[0])
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, dict(attrs), self.cur, self.getpos()[0]))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def has(n, c):
    return c in n.classes


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def snip(s, n=40):
    s = norm(s)
    return s if len(s) <= n else s[:n] + "…"


def lang_of(n):
    for x in (n, *n.ancestors()):
        if x.tag == "html":
            return None
        if "lang" in x.attrs:
            return x.attrs["lang"]
    return None


def not_prose(n):
    return any(x.tag in NOT_PROSE or x.attrs.get("translate") == "no" for x in (n, *n.ancestors()))


def sibling(n, step):
    kids = n.parent.kids
    i = kids.index(n) + step
    while 0 <= i < len(kids):
        k = kids[i]
        if isinstance(k, Node):
            return k
        if k.strip():
            return None
        i += step
    return None


def top_ko(root):
    """Korean elements that are not inside another lang element, in document order."""
    for n in root.iter():
        if n.tag != "html" and n.attrs.get("lang") == "ko" and lang_of(n.parent) is None:
            yield n


def blocks(root, langs=("ko", "en"), skip=(), with_pre=False, drop=("cite",)):
    """(node, text) for each top-level language element and each <li> of a language list (and <pre> if asked).
    Elements inside a class in `skip` or inside [data-meta] (when `skip` is given) are left out; `drop` as in text()."""
    for n in root.iter():
        top = n.tag != "html" and n.attrs.get("lang") in langs and lang_of(n.parent) is None
        if not (top or (with_pre and n.tag == "pre")) or any(has(x, c) for x in (n, *n.ancestors()) for c in skip):
            continue
        if skip and any(x.attrs.get("data-meta") for x in (n, *n.ancestors())):
            continue
        if n.tag in ("ul", "ol"):
            for li in (k for k in n.elements() if k.tag == "li"):
                yield li, norm(li.text(drop=drop))
        else:
            yield n, norm(n.text(drop=drop))


def parse(text):
    t = Tree()
    t.feed(text)
    return t.root


_SAMPLES = None


def template_samples():
    """Sentences (8+ characters) and short texts of assets/template.html that a finished report must not keep."""
    global _SAMPLES
    if _SAMPLES is None:
        sentences, short = set(), set()
        if TEMPLATE.is_file():
            tpl = parse(TEMPLATE.read_text(encoding="utf-8"))
            for _, b in blocks(tpl, skip=SAMPLE_SKIP, with_pre=True, drop=("cite", "pill")):
                if not b or b in LABELS:
                    continue
                if len(b) < 8:
                    short.add(b)
                sentences.update(p for p in re.split(r"(?<=[.!?])\s+", b)
                                 if len(p) >= 8 and not re.fullmatch(r"(그림|표|Figure|Table) \d+\.", p))
        _SAMPLES = (sorted(sentences), short)
    return _SAMPLES


def assets(root):
    """Whitespace-normalized text of every <style> and <script>, in document order."""
    return ([norm(n.text()) for n in root.iter() if n.tag == "style"],
            [norm("".join(k for k in n.kids if isinstance(k, str))) for n in root.iter() if n.tag == "script"])


def check(path):
    src = Path(path).read_text(encoding="utf-8")
    t = Tree()
    t.feed(src)
    root = t.root
    errs, warns = [], []
    nodes = list(root.iter())
    html = next((n for n in nodes if n.tag == "html"), None)
    if html is None:
        return ["<html> 요소가 없다"], [], "?", root
    kind = html.attrs.get("data-report")
    if kind not in ORDER:
        errs.append(f'<html data-report>는 "research" 또는 "general"이다 (지금: {kind!r})')
        kind = "research"
    if html.attrs.get("data-lang") != "ko" or html.attrs.get("lang") != "ko":
        errs.append('<html lang="ko" data-lang="ko">로 연다. 처음 화면은 한국어다')

    for needle in PLACEHOLDERS:
        for m in re.finditer(re.escape(needle), src):
            errs.append(f"L{src.count(chr(10), 0, m.start()) + 1} 템플릿 자리 표시가 남았다: {needle}")
    sentences, short = template_samples()
    for n, b in blocks(root, skip=SAMPLE_SKIP, with_pre=True, drop=("cite", "pill")):
        left = [s for s in sentences if s in b] or ([b] if b in short else [])
        for s in left:
            errs.append(f"L{n.line} 템플릿 자리 표시가 남았다(예시 문장): {snip(s)}")

    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", "\n".join(n.text() for n in nodes if n.tag == "style"))
    for pat, what in CSS_RULES:
        if not re.search(pat, css):
            errs.append(f"CSS 규칙이 바뀌었거나 없다: {what}. 템플릿의 <style>을 그대로 쓴다")
    if re.search(r"border-left\s*:", css):
        errs.append("CSS에 border-left가 있다. 강조 문단과 상자에 왼쪽 막대를 쓰지 않는다")
    if TEMPLATE.is_file() and Path(path).resolve() != TEMPLATE:
        mine, theirs = assets(root), assets(parse(TEMPLATE.read_text(encoding="utf-8")))
        if mine[0] != theirs[0]:
            errs.append("<style>이 템플릿과 다르다. 보고서마다 CSS를 고치거나 덧붙이지 않고 템플릿의 <style>을 그대로 쓴다")
        if mine[1] != theirs[1]:
            errs.append("<script>가 템플릿과 다르다. 언어와 테마 전환이 깨지지 않게 템플릿의 <script>를 그대로 쓴다")
    for n in nodes:
        if "style" in n.attrs and not any(x.tag == "svg" for x in (n, *n.ancestors())):
            errs.append(f'L{n.line} <{n.tag} style="{snip(n.attrs["style"] or "", 30)}">: 인라인 style을 쓰지 않는다')
        if n.tag == "link" and "stylesheet" in (n.attrs.get("rel") or ""):
            errs.append(f"L{n.line} 외부 스타일시트를 쓰지 않는다: {n.attrs.get('href')}")
        for a in TEXT_ATTRS:
            v = n.attrs.get(a) or ""
            for ch, nm in FORBIDDEN.items():
                if ch in v:
                    errs.append(f'L{n.line} {a}="{snip(v, 30)}": {nm}({ch})를 쓰지 않는다')
            if a in ("data-en", "data-alt-en") and HANGUL.search(v):
                errs.append(f'L{n.line} {a}="{snip(v, 30)}": 영어 쪽에 한국어가 들어 있다')

    # ① top bar, before <main>
    main = next((n for n in nodes if n.tag == "main"), None)
    top = next((n for n in nodes if has(n, "topbar")), None)
    if top is None:
        errs.append("상단 막대(header.topbar)가 없다")
    else:
        if main is not None and nodes.index(top) > nodes.index(main):
            errs.append("상단 막대는 <main> 앞에 둔다")
        link = next((n for n in top.iter() if n.tag == "a" and has(n, "list-link")), None)
        if link is None or not (link.attrs.get("href") or "").strip():
            errs.append("상단 막대에 목록 링크(a.list-link href)가 없다")
        langs = {n.attrs.get("data-set-lang") for n in top.iter() if "data-set-lang" in n.attrs}
        themes = {n.attrs.get("data-set-theme") for n in top.iter() if "data-set-theme" in n.attrs}
        if langs != {"ko", "en"}:
            errs.append(f"언어 버튼은 data-set-lang ko와 en 두 개다 (지금: {sorted(x or '' for x in langs)})")
        if themes != {"light", "dark"}:
            errs.append(f"테마 버튼은 data-set-theme light와 dark 두 개다 (지금: {sorted(x or '' for x in themes)})")

    # page order inside <main>
    if main is None:
        errs.append("<main>이 없다")
        return errs, warns, kind, root
    codes = ""
    for n in main.elements():
        codes += ("H" if has(n, "doc-head") else "S" if has(n, "sec") else "R" if has(n, "sources")
                  else "M" if has(n, "method") else "X" if has(n, "share") else "?")
    if not re.match(ORDER[kind], codes):
        want = "머리, 절, 출처 표, 조사 방법, 공유 범위" if kind == "research" else "머리, 절, (출처 표), (조사 방법), 공유 범위"
        errs.append(f"<main> 바로 아래 순서가 규격과 다르다 ({kind}: {want}). 지금: {codes} "
                    "(H 머리, S 절, R 출처 표, M 조사 방법, X 공유 범위, ? 그 밖의 요소)")

    # ② head
    head = next((n for n in main.elements() if has(n, "doc-head")), None)
    if head is not None:
        meta = next((n for n in head.iter() if has(n, "meta")), None)
        if meta is None or not any(n.tag == "time" and n.attrs.get("datetime") for n in meta.iter()):
            errs.append("머리에 기준일(.meta 안의 <time datetime>)이 없다")
        if kind == "research" and not any(n.attrs.get("data-meta") == "searched" for n in head.iter()):
            errs.append('머리에 검색한 곳([data-meta="searched"])이 없다')
        if kind == "research" and not any(has(n, "source-mix") for n in head.iter()):
            errs.append("머리에 출처 구성 목록(.source-mix)이 없다")
        if not any(has(n, "tags") for n in head.iter()):
            warns.append("머리에 태그(.tags)가 없다")
        leads = [n for n in head.iter() if has(n, "lead")]
        if [n.attrs.get("lang") for n in leads] != ["ko", "en"]:
            errs.append('요약 문단은 <p class="lead" lang="ko">와 lang="en" 한 쌍이다')
    h1s = [n for n in nodes if n.tag == "h1"]
    if len(h1s) != 1 or (head is not None and h1s[0] not in head.iter()):
        errs.append(f"h1은 머리 안에 하나만 둔다 (지금 {len(h1s)}개)")

    # ③ sections, ④ ⑤
    for sec in main.elements():
        if not (has(sec, "sec") or has(sec, "sources") or has(sec, "method")):
            continue
        kids = sec.elements()
        h2 = next((k for k in kids if k.tag == "h2"), None)
        name = sec.attrs.get("id") or f"L{sec.line}"
        if h2 is None:
            errs.append(f"{name}: 절 바로 아래에 h2가 없다")
        elif has(sec, "sec") and kind == "research" and not any(has(k, "src-kind") for k in kids[:kids.index(h2)]):
            errs.append(f"{name}: h2 앞에 출처 종류(p.src-kind)가 없다")

    # language pairs
    for n in nodes:
        lg = n.attrs.get("lang")
        if n.tag == "html" or lg is None:
            continue
        if lg not in ("ko", "en"):
            errs.append(f'L{n.line} lang="{lg}": ko와 en만 쓴다')
            continue
        outer = lang_of(n.parent)
        if outer is not None:
            if outer != lg:
                errs.append(f'L{n.line} lang="{outer}" 글 안의 lang="{lg}" 요소는 어느 화면에도 보이지 않는다: {snip(n.text())}')
            continue
        mate, want = (sibling(n, 1), "en") if lg == "ko" else (sibling(n, -1), "ko")
        if not (mate is not None and mate.tag == n.tag and mate.attrs.get("lang") == want):
            where = "바로 뒤에" if lg == "ko" else "바로 앞에"
            errs.append(f'L{n.line} <{n.tag} lang="{lg}"> {where} 같은 태그의 lang="{want}" 짝이 없다: {snip(n.text())}')
        if not n.text().strip() and not any(k.tag in ("img", "svg") for k in n.iter()):
            errs.append(f'L{n.line} <{n.tag} lang="{lg}">가 비어 있다')

    # Korean outside its pair, forbidden symbols
    for n in [root, *nodes]:
        texts = [k for k in n.kids if isinstance(k, str) and k.strip()]
        if not texts or n is root or not_prose(n):
            continue
        lg = lang_of(n)
        for s in texts:
            if HANGUL.search(s) and lg != "ko":
                why = "짝 밖에 있어 영어 화면에도 보인다" if lg is None else "영어 쪽에 들어 있다"
                errs.append(f"L{n.line} 한국어 글이 {why}: {snip(s)}")
            for ch, nm in FORBIDDEN.items():
                if ch in s:
                    errs.append(f"L{n.line} {nm}({ch})를 쓰지 않는다: {snip(s)}")

    # figures and tables
    for n in nodes:
        if n.tag == "figure" and not (has(n, "fig") or has(n, "tbl")):
            errs.append(f'L{n.line} <figure>에는 class="fig"(그림) 또는 class="tbl"(표)을 붙인다')
        if n.tag == "table" and not any(has(a, "box") for a in n.ancestors()):
            errs.append(f"L{n.line} 표는 상자(.box) 안에 넣는다")
        if n.tag == "pre" and not has(n, "box"):
            warns.append(f'L{n.line} 스니펫은 <pre class="box">로 쓴다')
    for cls_, ko_w, en_w, label in (("fig", "그림", "Figure", "그림"), ("tbl", "표", "Table", "표")):
        figs = [n for n in nodes if n.tag == "figure" and has(n, cls_)]
        for i, f in enumerate(figs, 1):
            kids = f.elements()
            box = next((k for k in kids if has(k, "box")), None)
            cap = next((k for k in kids if k.tag == "figcaption"), None)
            if box is None:
                errs.append(f"L{f.line} {label} {i}: 상자(<div class=\"box\">) 안에 넣는다")
            if cap is None:
                if cls_ == "fig":
                    errs.append(f"L{f.line} 그림 {i}: 아래에 캡션(figcaption)이 없다")
                continue
            if box is not None and kids.index(cap) < kids.index(box):
                errs.append(f"L{cap.line} {label} {i}: 캡션은 상자 아래에 둔다")
            ko = next((k for k in cap.iter() if k.attrs.get("lang") == "ko"), None)
            en = next((k for k in cap.iter() if k.attrs.get("lang") == "en"), None)
            kt, et = (norm(ko.text()) if ko else ""), (norm(en.text()) if en else "")
            if not re.match(rf"{ko_w} {i}\. \S", kt):
                errs.append(f'L{cap.line} 캡션은 "{ko_w} {i}. "으로 시작한다: "{snip(kt, 24)}"')
            if not re.match(rf"{en_w} {i}\. \S", et):
                errs.append(f'L{cap.line} 영어 캡션은 "{en_w} {i}. "으로 시작한다: "{snip(et, 24)}"')

    # ④ sources, citations, source mix
    src_sec = next((n for n in main.elements() if has(n, "sources")), None)
    rows = [n for n in src_sec.iter() if n.tag == "tr" and (n.attrs.get("id") or "").startswith("src-")] if src_sec else []
    ids = [r.attrs["id"] for r in rows]
    if src_sec is not None and not rows:
        errs.append('출처 표에 <tr id="src-1"> 같은 행이 없다')
    for i, r in enumerate(rows, 1):
        rid = r.attrs["id"]
        if rid != f"src-{i}":
            errs.append(f"L{r.line} 출처 번호는 src-1부터 차례로 붙인다: {rid} (차례상 src-{i})")
        if not r.attrs.get("data-kind"):
            errs.append(f"L{r.line} {rid}: 출처 종류(data-kind)가 없다")
        tds = [k for k in r.elements() if k.tag == "td"]
        if tds and norm(tds[0].text()) != rid[4:]:
            errs.append(f"L{r.line} {rid}: 첫 칸의 번호가 {norm(tds[0].text())!r}이다")
        if not any(k.tag == "a" and (k.attrs.get("href") or "").startswith(("https://", "http://")) for k in r.iter()):
            warns.append(f"L{r.line} {rid}: 원문 링크가 없다")
    cites = [n for n in nodes if n.tag == "a" and any(x.tag == "sup" and has(x, "cite") for x in n.ancestors())]
    if any(n.tag == "sup" and has(n, "cite") for n in nodes) and src_sec is None:
        errs.append("인용 번호가 있는데 출처 표(section.sources)가 없다")
    cited = set()
    for a in cites:
        href = a.attrs.get("href") or ""
        if href[1:] not in ids:
            errs.append(f"L{a.line} 인용 번호 {norm(a.text())}가 출처 표에 없는 곳을 가리킨다: {href}")
            continue
        cited.add(href[1:])
        if norm(a.text()) != href[5:]:
            errs.append(f"L{a.line} 인용 번호 글자 {norm(a.text())}와 {href}가 다르다")
    for rid in ids:
        if rid not in cited:
            warns.append(f"{rid}: 본문에서 인용하지 않은 출처다")
    mix = next((n for n in nodes if has(n, "source-mix")), None)
    if mix is not None:
        declared = {}
        for li in (n for n in mix.iter() if n.tag == "li"):
            k, c = li.attrs.get("data-kind"), li.attrs.get("data-count") or ""
            if not k or not c.isdigit():
                errs.append(f"L{li.line} 출처 구성 항목에 data-kind와 숫자 data-count가 없다")
                continue
            declared[k] = int(c)
            for part in (x for x in li.iter() if x.attrs.get("lang") in ("ko", "en")):
                if not re.search(rf"(?<!\d){c}(?!\d)", part.text()):
                    errs.append(f"L{li.line} 출처 구성 {k}: 보이는 글({snip(part.text(), 20)})에 건수 {c}가 없다")
        actual = dict(Counter(r.attrs.get("data-kind") for r in rows))
        if declared != actual:
            errs.append(f"출처 구성 목록 {declared}이 출처 표의 종류별 행 수 {actual}와 다르다")

    # images
    for img in (n for n in nodes if n.tag == "img"):
        s = img.attrs.get("src") or ""
        if s.startswith(("https://", "http://")):
            warns.append(f"L{img.line} 외부 그림은 오프라인과 사내망에서 보이지 않는다: {snip(s, 50)}")
        elif not s.startswith("data:"):
            errs.append(f"L{img.line} 상대 경로 그림({s})은 파일을 공유하면 깨진다. embed_images.py로 파일 안에 넣는다")
        if not (img.attrs.get("alt") or "").strip():
            warns.append(f"L{img.line} 그림에 alt(한국어 설명)가 없다")
        elif "data-alt-en" not in img.attrs:
            warns.append(f"L{img.line} 그림에 data-alt-en(영어 설명)이 없다")

    # Korean wording, block by block: a 한다체 or 해요체 ending before . ! ? or, in a paragraph or list item, at the end
    for n, s in blocks(root, langs=("ko",)):
        if not_prose(n.parent):
            continue
        for m in re.finditer(r"([가-힣])(다|요)(?=[.!?]|$)", s):
            if m.group(2) == "다" and m.group(1) == "니":
                continue
            if m.end() == len(s) and n.tag not in ("p", "li"):
                continue
            warns.append(f"L{n.line} 합쇼체가 아닌 문장: …{s[max(0, m.start() - 20):m.end() + 1]}")
            break
        if "하세요" in s:
            warns.append(f'L{n.line} 권고는 "~하는 것을 권고합니다"로 쓴다: {snip(s)}')
        if "권장" in s:
            warns.append(f'L{n.line} "권장" 대신 "권고"로 쓴다: {snip(s)}')
    return errs, warns, kind, root


def ko_markdown(root):
    """Korean text as Markdown lines for lint_prose.py: headings keep their level, lists become '- ' lines.
    The tab title (<title data-ko>) and image descriptions (alt) come first, one line each."""
    out = []
    for n in root.iter():
        v = n.attrs.get("data-ko") if n.tag == "title" else n.attrs.get("alt") if n.tag == "img" else None
        if v and norm(v):
            out += [norm(v), ""]
    for n in top_ko(root):
        if any(has(x, "topbar") or has(x, "sources") for x in n.ancestors()) or not_prose(n.parent):
            continue
        level = next((int(x.tag[1]) for x in (n, *n.ancestors()) if re.fullmatch(r"h[1-6]", x.tag)), 0)
        if n.tag in ("ul", "ol"):
            out += ["- " + norm(li.text(True)) for li in n.elements() if li.tag == "li"]
        elif norm(n.text(True)):
            out.append(("#" * level + " " if level else "") + norm(n.text(True)))
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="+")
    ap.add_argument("--dump-ko", metavar="OUT.md", help="write the Korean text for lint_prose.py (one input file)")
    a = ap.parse_args()
    if a.dump_ko and len(a.html) != 1:
        ap.error("--dump-ko takes exactly one html file")
    failed = False
    for f in a.html:
        if not Path(f).is_file():
            print(f"== {f}\n   ERROR file not found")
            failed = True
            continue
        errs, warns, kind, root = check(f)
        print(f"== {f} ({kind})")
        for e in errs:
            print(f"   ERROR {e}")
        for w in warns:
            print(f"   WARN  {w}")
        if not errs and not warns:
            print("   OK")
        failed |= bool(errs)
        if a.dump_ko:
            Path(a.dump_ko).parent.mkdir(parents=True, exist_ok=True)
            Path(a.dump_ko).write_text(ko_markdown(root), encoding="utf-8")
            print(f"   Korean text -> {a.dump_ko}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

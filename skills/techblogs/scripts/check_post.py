#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check a techblogs report page (and its front matter file) against the template rules.

Usage: python3 check_post.py <slug>-report.html [--front <slug>.md] [--blog <blog-repo>] [--dump-ko FILE] [--urls FILE]
       python3 check_post.py ko.body.html --dump-ko FILE        (fragment: text dump only)

ERROR lines are rule violations and make the exit code 1. WARN lines need a human decision.
--front   front matter file to check (default: <slug>.md next to the report, when it exists)
--blog    blog repository; the category and icon are checked against its _config.yml and assets/icons
--dump-ko write the Korean text as Markdown for lint_prose.py (tables and code are left out)
--urls    write every outside link of the page (not the canonical link), one per line, for check_urls.py
"""
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")
VOID = {"br", "img", "hr", "col", "input", "meta", "link", "wbr"}
HANGUL = re.compile(r"[가-힣]")
BANNED = {"·": "가운뎃점", "—": "엠 대시", "–": "엔 대시"}


class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs or []), parent, []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def text(self, skip=()):
        return "".join(k if isinstance(k, str) else ("" if k.tag in skip else k.text(skip)) for k in self.kids)

    def walk(self):
        for k in self.kids:
            if isinstance(k, Node):
                yield k
                yield from k.walk()

    def find(self, tag=None, cls=None):
        return [n for n in self.walk() if (tag is None or n.tag == tag) and (cls is None or cls in n.cls())]

    def inside(self, tag=None, cls=None):
        n = self.parent
        while n is not None:
            if (tag is None or n.tag == tag) and (cls is None or cls in n.cls()):
                return True
            n = n.parent
        return False


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(s):
    t = Tree()
    t.feed(s)
    return t.root


def blocks(s, tag):
    return [m.group(1).strip() for m in re.finditer(r"<%s\b[^>]*>(.*?)</%s>" % (tag, tag), s, re.S)]


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def dump_ko(root, path):
    """Korean prose as Markdown. Tables become table rows (lint skips them); code is dropped."""
    col = [n for n in root.find("div", "col") if "l-ko" in n.cls()]
    scope = col[0] if col else root
    lines = []
    for h in root.find("h1"):
        ko = [s for s in h.find("span", "l-ko")]
        lines.append("# " + squash((ko[0] if ko else h).text()))
    for p in root.find("p", "thesis"):
        ko = p.find("span", "l-ko")
        if ko:
            lines.append(squash(ko[0].text()))
    # 목록 카드에 보이는 요약, 머리의 요점, 끝의 글도 문장 검사를 받는다.
    for m in root.find("meta"):
        if m.attrs.get("name") == "description" and m.attrs.get("content", "").strip():
            lines.append(squash(m.attrs["content"]))
    for box in root.find("ul", "facts") + root.find("footer", "foot"):
        for sp in box.find("span", "l-ko"):
            if squash(sp.text()):
                lines.append(squash(sp.text()))
    for n in scope.walk():
        if n.inside("pre") or n.inside("table") or n.tag in ("pre", "code"):
            continue
        t = squash(n.text(skip=("pre",)))
        if not t:
            continue
        if n.tag == "h2":
            lines.append("## " + t)
        elif n.tag == "h3":
            lines.append("### " + t)
        elif n.tag == "p" and not n.inside("li"):
            lines.append(t)
        elif n.tag == "li":
            own = squash("".join(k if isinstance(k, str) else ("" if k.tag in ("ul", "ol", "pre") else k.text()) for k in n.kids))
            if own:
                lines.append("- " + own)
        elif n.tag == "figcaption":
            lines.append(t)
        elif n.tag == "table":
            pass
    for table in scope.find("table"):
        for tr in table.find("tr"):
            cells = [squash(c.text()) for c in tr.kids if isinstance(c, Node) and c.tag in ("th", "td")]
            lines.append("| " + " | ".join(cells) + " |")
    open(path, "w", encoding="utf-8").write("\n\n".join(lines) + "\n")


def main():
    argv = sys.argv[1:]
    opts = {}
    for k in ("--front", "--blog", "--dump-ko", "--urls"):
        if k in argv:
            i = argv.index(k)
            opts[k] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1:
        raise SystemExit(__doc__)
    path = argv[0]
    src = open(path, encoding="utf-8").read()
    root = parse(src)
    if "--dump-ko" in opts:
        dump_ko(root, opts["--dump-ko"])
    if "--urls" in opts:
        seen = []
        for a in root.find("a"):
            h = a.attrs.get("href", "")
            if re.match(r"^https?://", h) and h not in seen:
                seen.append(h)
        open(opts["--urls"], "w", encoding="utf-8").write("".join("- %s\n" % u for u in seen))
    if "<html" not in src:
        print("fragment: 글만 뽑았습니다 (%s)" % opts.get("--dump-ko", "-"))
        return 0

    errors, warns = [], []
    E, W = errors.append, warns.append
    tpl = open(TEMPLATE, encoding="utf-8").read()

    # 1. 템플릿의 style과 script를 그대로 쓰는가
    if blocks(src, "style") != blocks(tpl, "style"):
        E("<style>이 템플릿과 다릅니다. 디자인은 템플릿에서만 고칩니다.")
    if blocks(src, "script") != blocks(tpl, "script"):
        E("<script>가 템플릿과 다릅니다.")
    if re.search(r"\[\[[a-z_]+\]\]", src):
        E("채우지 않은 템플릿 토큰이 남아 있습니다: %s" % ", ".join(sorted(set(re.findall(r"\[\[[a-z_]+\]\]", src)))))
    if re.search(r"\bTODO\b", re.sub(r"<pre>.*?</pre>", "", src, flags=re.S)):
        E("TODO 표시가 남아 있습니다.")
    for n in root.walk():
        if "style" in n.attrs:
            E("인라인 style 속성은 쓰지 않습니다: <%s style=\"%s\">" % (n.tag, n.attrs["style"][:40]))
            break

    # 2. 페이지 뼈대
    def need(desc, found, exactly=None):
        if (exactly is not None and len(found) != exactly) or (exactly is None and not found):
            E("%s: %d개 (필요: %s)" % (desc, len(found), exactly if exactly is not None else "1개 이상"))
        return found

    wrap = [n for n in root.find("div", "wrap") if "page" in n.cls()]
    need("div.wrap.page (블로그 레이아웃이 찾는 요소)", wrap, 1)
    need("nav.top.theme-bar (블로그 레이아웃이 숨기는 상단 막대)", [n for n in root.find("nav", "top") if "theme-bar" in n.cls()], 1)
    need("header.masthead", root.find("header", "masthead"), 1)
    need("h1", root.find("h1"), 1)
    need("p.thesis", root.find("p", "thesis"), 1)
    need("footer.foot", root.find("footer", "foot"), 1)
    if not re.search(r'<link rel="canonical" href="https?://[^"]+">', src):
        E("canonical 링크가 없습니다.")
    title = blocks(src, "title")
    if not title or not title[0]:
        E("<title>이 비어 있습니다.")
    if not re.search(r'<meta name="description" content="[^"]+">', src):
        E("meta description이 비어 있습니다.")

    ids = [n.attrs["id"] for n in root.walk() if "id" in n.attrs]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        E("id가 겹칩니다: %s" % d)

    # 3. 두 언어의 절과 구성 요소
    cols = {}
    for lang in ("ko", "en"):
        c = [n for n in root.find("div", "col") if "l-" + lang in n.cls()]
        need("div.col.l-%s" % lang, c, 1)
        cols[lang] = c[0] if c else Node("div")
    shape = {}
    for lang, col in cols.items():
        secs = [n for n in col.kids if isinstance(n, Node) and n.tag == "section"]
        for n, s in enumerate(secs, 1):
            if s.attrs.get("id") != "%s-s%d" % (lang, n):
                E("%s %d번째 절의 id가 %s-s%d 가 아닙니다: %s" % (lang, n, lang, n, s.attrs.get("id")))
            if len(s.find("h2")) != 1 or not s.find("header", "sec-head") or not s.find("div", "prose"):
                E("%s 절 %s: header.sec-head 안의 h2 하나와 div.prose가 필요합니다." % (lang, s.attrs.get("id")))
        shape[lang] = [(len(s.find("h3")), len(s.find("figure", "fig")), len(s.find("table")), len(s.find("div", "snippet")),
                        len(s.find("blockquote"))) for s in secs]
        nav = [n for n in root.find("nav", "toc") if "l-" + lang in n.cls()]
        need("nav.toc.l-%s" % lang, nav, 1)
        hrefs = [a.attrs.get("href", "") for a in (nav[0].find("a") if nav else [])]
        for h in hrefs:
            if not h.startswith("#") or h[1:] not in ids:
                E("%s 목차 링크가 가리키는 곳이 없습니다: %s" % (lang, h))
        for s in secs:
            if "#" + s.attrs.get("id", "") not in hrefs:
                E("%s 목차에 절이 빠졌습니다: %s" % (lang, s.attrs.get("id")))
    if len(shape["ko"]) != len(shape["en"]):
        E("절 수가 다릅니다: ko %d, en %d" % (len(shape["ko"]), len(shape["en"])))
    else:
        names = ("h3", "그림", "표", "코드 상자", "인용 상자")
        for n, (a, b) in enumerate(zip(shape["ko"], shape["en"]), 1):
            for name, x, y in zip(names, a, b):
                if x != y:
                    E("절 %d의 %s 수가 다릅니다: ko %d, en %d" % (n, name, x, y))
    imgs = {lang: [i.attrs.get("src", "") for i in col.find("img")] for lang, col in cols.items()}
    if imgs["ko"] != imgs["en"]:
        E("두 언어의 그림 파일 순서가 다릅니다.")

    # 4. 그림, 표, 코드 상자
    base = os.path.dirname(os.path.abspath(path))
    for img in root.find("img"):
        s = img.attrs.get("src", "")
        if not img.attrs.get("alt", "").strip():
            E("그림에 alt가 없습니다: %s" % s)
        if re.match(r"^(https?:)?//", s) or s.startswith("data:"):
            E("그림은 페이지 옆의 파일로 둡니다(원격 주소와 data URI는 쓰지 않음): %s" % s[:80])
        elif not os.path.isfile(os.path.join(base, s)):
            E("그림 파일이 없습니다: %s" % s)
        if not (img.attrs.get("width", "").isdigit() and img.attrs.get("height", "").isdigit()):
            W("그림에 width와 height가 없습니다: %s" % s)
        if not img.inside("figure", "fig") or not img.inside("div", "canvas"):
            E("그림은 figure.fig 안의 div.canvas에 둡니다: %s" % s)
    for lang, word, tword in (("ko", "그림", "표"), ("en", "Figure", "Table")):
        caps = [squash(f.text()) for f in cols[lang].find("figcaption")]
        for n, c in enumerate(caps, 1):
            if not c.startswith("%s %d." % (word, n)):
                E("%s 그림 캡션 번호가 순서대로가 아닙니다 (%s %d. 이어야 함): %s" % (lang, word, n, c[:50]))
        tcaps = [squash(p.text()) for p in cols[lang].find("p", "cap")]
        for n, c in enumerate(tcaps, 1):
            if not c.startswith("%s %d." % (tword, n)):
                E("%s 표 캡션 번호가 순서대로가 아닙니다 (%s %d. 이어야 함): %s" % (lang, tword, n, c[:50]))
        for f in cols[lang].find("figure", "fig"):
            if len(f.find("figcaption")) != 1:
                E("%s 그림에 캡션이 하나 있어야 합니다." % lang)
    for t in root.find("table"):
        if not t.inside("div", "scroll"):
            E("표는 div.scroll 안에 둡니다.")
    for s in root.find("div", "snippet"):
        if not s.find("span", "lang") or not s.find("button", "copy") or not [c for c in s.find("code") if c.inside("pre")]:
            E("코드 상자는 .snippet-bar(span.lang, button.copy)와 pre > code를 갖춥니다.")
    for p in root.find("pre"):
        if not p.inside("div", "snippet"):
            W("pre가 코드 상자(.snippet) 밖에 있습니다. 복사 버튼이 붙지 않습니다.")

    # 5. 글자: 금지 기호, 영어 페이지의 한글
    def prose_nodes(scope):
        for n in scope.walk():
            if n.tag in ("p", "li", "h1", "h2", "h3", "td", "th", "figcaption", "blockquote") and not n.inside("pre"):
                yield n

    wrapn = wrap[0] if wrap else root
    seen = set()
    for n in prose_nodes(wrapn):
        t = n.text(skip=("pre", "code"))
        for ch, name in BANNED.items():
            if ch in t and (ch, squash(t)[:30]) not in seen:
                seen.add((ch, squash(t)[:30]))
                E("%s(%s)은 쓰지 않습니다: %s" % (name, ch, squash(t)[:60]))
        if "→" in t and n.tag in ("p", "li") and not n.inside("table"):
            W("문장 안의 화살표(→)는 말로 풉니다: %s" % squash(t)[:60])
    for img in root.find("img"):
        for ch, name in BANNED.items():
            if ch in img.attrs.get("alt", ""):
                E("%s(%s)은 그림 alt에도 쓰지 않습니다: %s" % (name, ch, img.attrs["alt"][:60]))
    desc = re.search(r'<meta name="description" content="([^"]*)">', src)
    for ch, name in BANNED.items():
        if desc and ch in desc.group(1):
            E("%s(%s)은 요약(meta description, excerpt)에도 쓰지 않습니다: %s" % (name, ch, desc.group(1)[:60]))
    leaks = []
    for b in cols["en"].find("button", "copy"):
        if HANGUL.search(b.text()):
            leaks.append("복사 버튼: " + squash(b.text()))
    for n in prose_nodes(cols["en"]):
        t = n.text(skip=("pre", "code"))
        if HANGUL.search(t):
            leaks.append(squash(t)[:60])
    for n in wrapn.find("span", "l-en"):
        if not n.inside("div", "col") and HANGUL.search(n.text(skip=("code",))):
            leaks.append(squash(n.text())[:60])
    if leaks:
        W("영어 쪽에 한글이 있습니다 %d곳 (고유한 화면 이름이 아니면 번역): %s" % (len(leaks), " / ".join(leaks[:3])))
    for a in wrapn.find("a"):
        h = a.attrs.get("href", "")
        if h.startswith("http") and a.attrs.get("target") != "_blank":
            W("바깥 링크는 target=\"_blank\" rel=\"noopener\"로 엽니다: %s" % h[:70])
            break

    # 6. front matter
    front = opts.get("--front") or re.sub(r"-report\.html$", ".md", path)
    if os.path.isfile(front) and front != path:
        fm = open(front, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", fm, re.S)
        if not m:
            E("front matter 파일 형식이 아닙니다: %s" % front)
        else:
            kv = dict(re.findall(r"^([a-z_]+):\s*(.*)$", m.group(1), re.M))
            for k in ("title", "title_en", "layout", "report_src", "date", "category", "tags", "icon", "minutes", "excerpt", "excerpt_en"):
                if not kv.get(k, "").strip().strip('"'):
                    E("front matter에 %s 값이 없습니다." % k)
            if kv.get("layout") != "report":
                E("front matter의 layout은 report여야 합니다.")
            if not kv.get("report_src", "").endswith("/" + os.path.basename(path)):
                E("front matter의 report_src가 이 파일을 가리키지 않습니다: %s" % kv.get("report_src"))
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", kv.get("date", "")):
                E("front matter의 date는 YYYY-MM-DD 형식입니다.")
            if not kv.get("minutes", "").isdigit() or int(kv.get("minutes", "0")) <= 0:
                E("front matter의 minutes는 1 이상의 정수입니다.")
            if m.group(2).strip():
                E("front matter 파일에는 본문을 쓰지 않습니다. 본문은 리포트 HTML에 둡니다.")
            if "--blog" in opts:
                cfg = open(os.path.join(opts["--blog"], "_config.yml"), encoding="utf-8").read()
                cats = dict(re.findall(r"- name:\s*(.+?)\s*\n(?:\s+[a-z_]+:.*\n)*?\s+url:\s*(\S+)", cfg))
                if kv.get("category") not in cats:
                    E("category가 블로그 _config.yml의 blog_categories에 없습니다: %s" % kv.get("category"))
                elif not kv.get("report_src", "").startswith(cats[kv["category"]]):
                    E("report_src가 분류 폴더(%s) 아래가 아닙니다: %s" % (cats[kv["category"]], kv.get("report_src")))
                if not os.path.isfile(os.path.join(opts["--blog"], "assets", "icons", kv.get("icon", "") + ".svg")):
                    E("icon 파일이 블로그 assets/icons에 없습니다: %s" % kv.get("icon"))
    else:
        W("front matter 파일을 찾지 못해 검사하지 않았습니다: %s" % front)

    for e in errors:
        print("ERROR " + e)
    for w in warns:
        print("WARN  " + w)
    print("결과: ERROR %d / WARN %d" % (len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert an AWS Korea Tech Blog Markdown draft into HTML for the WordPress code editor (wordpress.md).

Usage: python3 md_to_wordpress.py <draft.md> --out <wordpress.md> [--slug <english-slug>] [--channel tech|korea]
Nothing is uploaded: image src stays a local path (images/<file>), and the reviewer uploads the images and
replaces the paths. The title, the suggested URL slug and the byline categories go into an HTML comment at the
top, the body starts at <h2>, horizontal rules are dropped, tables get inline borders, captions are centered and
code blocks become <pre><code class="lang-...">. Raw HTML in the draft is written as text, not passed through,
and a link may only use http, https, mailto or a relative path.
The slug comes from --slug, else from "slug:" in the frontmatter, else from the file name without its date.
Exit code 0: written (lines marked [!] need a look). Exit code 1: not written, a [FAIL] line says why.
Exit code 2: usage. The rules are in references/publishing.md and follow the WordPress structure checklist of
github.com/comeddy/blog-precheck-plugin (MIT, Copyright (c) 2026 Youngjin Kim).
"""
import argparse, collections, html, io, os, re, sys

TABLE_STYLE = "border-collapse: collapse; border: 1px solid #000; margin: 0 auto 8px auto;"
TH_STYLE = "border: 1px solid #000; padding: 8px; background-color: #f2f3f3;"
TD_STYLE = "border: 1px solid #000; padding: 8px;"
CAPTION_STYLE = "text-align: center; margin-top: 0;"
FIGURE_STYLE = "text-align: center;"

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SCHEMES = ("http", "https", "mailto")
ALT = r"((?:[^\[\]]|\[[^\[\]]*\])*)"          # alt text or link text: one level of brackets inside
DEST = r"((?:[^()\s]|\([^()\s]*\))+)"         # link URL: one level of parentheses inside
TITLE = r'(?:\s+"[^"]*")?'
IMAGE = r"!\[" + ALT + r"\]\(([^)]+?)" + TITLE + r"\)"   # the path may hold a space, so that it can be refused by name
IMAGE_LINE = re.compile("^" + IMAGE + r"\s*$")
LINK = r"\[" + ALT + r"\]\(" + DEST + TITLE + r"\)"
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})[ \t]*(.*)$")
LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
CAPTION = re.compile(r"^\*((?:표|그림) \d+\..*)\*\s*$")
BYLINE = re.compile(r"^by\s+(.+?)\s+on\s+.+?\s+in\s+(.*)$")


class Notes(object):
    """What the conversion changed (changed), what needs a look (warn) and what stops it (fail)."""

    def __init__(self, base):
        self.base = base
        self.changed, self.warn, self.fail = [], [], []
        self.count = collections.Counter()
        self.langs = []


def attr(text):
    return html.escape(text, quote=True)


def comment_text(text):
    """Text that cannot close the HTML comment it is written into."""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    while "--" in text:
        text = text.replace("--", "- -")
    return text


def fence_open(line):
    """The match of a line that opens a fenced code block, or None. A backtick fence has no backtick after it."""
    m = FENCE.match(line)
    return m if m and not (m.group(2)[0] == "`" and "`" in m.group(3)) else None


def fence_close(line, mark):
    s = line.strip()
    return len(s) >= len(mark) and set(s) == set(mark[0])


def scheme_ok(url, notes):
    m = re.match(r"^\s*([A-Za-z][A-Za-z0-9+.-]*):", url)
    if m and m.group(1).lower() not in SCHEMES:
        notes.fail.append("링크나 이미지 URL에 넣을 수 없는 스킴(%s): http, https, mailto, 상대 경로만 가능" % m.group(1))
        return False
    return True


def image(alt, src, notes):
    notes.count["img"] += 1
    if src.startswith("data:"):
        notes.fail.append("base64 데이터 URI 이미지: images/ 폴더의 파일로 바꾼다")
        src = "data:"
    elif re.match(r"https?://", src):
        if re.search(r"-\d+x\d+\.(?:png|jpe?g|gif|webp)$", src, flags=re.I):
            notes.warn.append("축소본 이미지 URL(-NNNxNNN): 원본 URL로 바꾼다: %s" % src)
    elif not scheme_ok(src, notes):
        src = ""
    elif not src.startswith("images/"):
        notes.fail.append("이미지 경로가 images/ 상대 경로가 아님: %s" % src)
    elif not IMAGE_NAME.match(src.rsplit("/", 1)[-1]):
        notes.fail.append("이미지 파일 이름에 공백이나 특수문자가 있음: %s" % ascii(src))
    elif not os.path.isfile(os.path.join(notes.base, src)):
        notes.fail.append("이미지 파일 없음: %s" % src)
    return '<img src="%s" alt="%s" />' % (attr(src), attr(alt))


def emphasis(text):
    """Bold and italic in text that is already escaped. A closing * may be followed by a Korean particle."""
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![*\\A-Za-z0-9])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![*A-Za-z0-9])", r"<em>\1</em>", text)


def inline(text, notes):
    """Markdown inside a block: code spans, links, images, bold, italic. Everything else is escaped.

    A piece that is finished (a code span, a link) is put aside as a mark and comes back at the end, so a later
    rule cannot change it. Each piece is kept in two forms: its markup, and the plain text it stands for. Where
    the result is an attribute value (href, src, alt) only the plain form is used, and it is escaped there.
    """
    held = []

    def hold(markup, plain):
        held.append((markup, plain))
        return "\x00%d\x00" % (len(held) - 1)

    def back(s, form):
        for _ in range(4):  # a held piece can sit inside another one (code inside a link text)
            s = re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))][form], s)
        return s

    def link(m):
        url = back(m.group(2), 1)
        if not scheme_ok(url, notes):
            url = ""
        return hold('<a href="%s">%s</a>' % (attr(url), emphasis(html.escape(m.group(1), quote=False))),
                    back(m.group(1), 1))

    def autolink(m):
        notes.count["autolink"] += 1
        return hold('<a href="%s">%s</a>' % (attr(m.group(1)), html.escape(m.group(1), quote=False)), m.group(1))

    text = re.sub(r"(`+)(.+?)\1",
                  lambda m: hold("<code>%s</code>" % html.escape(m.group(2).strip(), quote=False), m.group(2).strip()), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>])", lambda m: hold(html.escape(m.group(1), quote=False), m.group(1)), text)
    text = re.sub(r"<(https?://[^\s<>]+)>", autolink, text)
    text = re.sub(r"<br\s*/?>", lambda m: hold("<br />", " "), text, flags=re.I)
    if re.search(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>", text):
        notes.count["raw_html"] += 1
    text = re.sub(IMAGE, lambda m: hold(image(back(m.group(1), 1), back(m.group(2), 1), notes), back(m.group(1), 1)), text)
    text = re.sub(LINK, link, text)
    return back(emphasis(html.escape(text, quote=False)), 0)


def code_block(lines, i, notes):
    """(html, next index) of the fenced block that opens at lines[i]."""
    opening = fence_open(lines[i])
    indent, mark = len(opening.group(1)), opening.group(2)
    lang = re.sub(r"[^a-z0-9+#._-]", "", (opening.group(3).split() or [""])[0].lower())
    body, j = [], i + 1
    while j < len(lines):
        if fence_close(lines[j], mark):
            break
        body.append(lines[j][indent:] if not lines[j][:indent].strip() else lines[j])
        j += 1
    else:
        notes.fail.append("닫히지 않은 코드 블록 (%d행)" % (i + 1))
    if not lang:
        lang = "text"
        first = next((b.strip() for b in body if b.strip()), "")
        notes.warn.append("언어 라벨 없는 코드 블록 → lang-text: 원고의 펜스에 언어를 적고 다시 변환한다 (%s)" % first[:40])
    notes.langs.append(lang)
    return '<pre><code class="lang-%s">%s</code></pre>' % (lang, html.escape("\n".join(body), quote=False)), j + 1


def cells(row):
    row = row.strip()
    row = row[1:] if row.startswith("|") else row
    row = row[:-1] if row.endswith("|") and not row.endswith("\\|") else row
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def table(rows, notes):
    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    align = []
    for c in cells(rows[1]):
        align.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":")
                     else "left" if c.startswith(":") else "")

    def cell(tag, style, text, k):
        if k < len(align) and align[k]:
            style += " text-align: %s;" % align[k]
        return '<%s style="%s">%s</%s>' % (tag, style, inline(text, notes), tag)

    out = ['<table style="%s">' % TABLE_STYLE, "<thead>", "<tr>"]
    out += [cell("th", TH_STYLE, c, k) for k, c in enumerate(head)]
    out += ["</tr>", "</thead>", "<tbody>"]
    for row in body:
        if len(row) > len(head):
            notes.warn.append("머리 행보다 칸이 많은 표 행: 넘치는 칸을 뺐다 (%s)" % " | ".join(row)[:40])
        row = (row + [""] * len(head))[:len(head)]
        out += ["<tr>"] + [cell("td", TD_STYLE, c, k) for k, c in enumerate(row)] + ["</tr>"]
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def read_list(lines, i, notes):
    """(items, next index). An item is [level, ordered, text, first number, blocks nested in the item]."""
    items = []
    while i < len(lines):
        m = LIST.match(lines[i])
        if m:
            ordered = m.group(2)[0].isdigit()
            items.append([len(m.group(1).expandtabs(4)) // 2, ordered, m.group(3),
                          int(m.group(2)[:-1]) if ordered else 1, []])
            i += 1
            continue
        j = i
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j == len(lines):
            break
        indented = lines[j][:1] in (" ", "\t")
        if indented and fence_open(lines[j]):         # a code block that belongs to the item
            block, i = code_block(lines, j, notes)
            items[-1][4].append(block)
        elif j > i and LIST.match(lines[j]):          # a blank line between two items
            i = j
        elif j > i and indented:                      # a second paragraph of the item: its indented lines only
            k = j
            while (k < len(lines) and lines[k].strip() and lines[k][:1] in (" ", "\t")
                   and not LIST.match(lines[k]) and not fence_open(lines[k])):
                k += 1
            items[-1][4].append("<p>%s</p>" % inline(" ".join(s.strip() for s in lines[j:k]), notes))
            i = k
        elif j == i and indented:                     # the item's text goes on
            items[-1][2] += " " + lines[i].strip()
            i += 1
        else:
            break
    return items, i


def render_list(items, notes, pos=0):
    """(html, next position) of one list: the items from pos on that share its level and its kind."""
    level, ordered, start = items[pos][0], items[pos][1], items[pos][3]
    tag = "ol" if ordered else "ul"
    out = ['<ol start="%d">' % start if ordered and start != 1 else "<%s>" % tag]
    while pos < len(items) and items[pos][0] == level and items[pos][1] == ordered:
        item = items[pos]
        pos += 1
        body = inline(item[2], notes) + "".join("\n" + b for b in item[4])
        while pos < len(items) and items[pos][0] > level:
            nested, pos = render_list(items, notes, pos)
            body += "\n" + nested
        out.append("<li>%s%s</li>" % (body, "\n" if "\n" in body else ""))
    out.append("</%s>" % tag)
    return "\n".join(out), pos


def convert(md, notes, slug=None, channel="tech", name=""):
    """HTML for the code editor, or None when notes.fail has something."""
    md = md.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    meta = {}
    m = re.match(r"\A---\n(.*?)\n---\n", md, flags=re.S)
    if m:
        for line in m.group(1).split("\n"):
            kv = re.match(r"^(\w+):\s*(.*?)\s*$", line)
            if kv:
                meta[kv.group(1)] = kv.group(2).strip("\"'")
        md = md[m.end():]
    lines = md.split("\n")  # not splitlines(): a form feed or U+2028 inside a code block is not a line break
    out, para = [], []
    title, cats, seen_h1 = meta.get("title"), [], False

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(s.strip() for s in para), notes))
            notes.count["p"] += 1
            del para[:]

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
        elif fence_open(line):
            flush()
            block, i = code_block(lines, i, notes)
            out.append(block)
        elif re.match(r"^#{1,6}[ \t]", line):
            flush()
            h = re.match(r"^(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$", line)
            level, text = len(h.group(1)), h.group(2)
            i += 1
            if level == 1 and not seen_h1:
                seen_h1 = True
                title = title or text
                notes.changed.append("문서 제목(H1)은 본문에서 빼고 맨 위 주석에 적음 (WordPress 제목 필드에 넣는다)")
                continue
            if level == 1:
                notes.warn.append("H1이 두 개 이상: 두 번째부터 h2로 바꿈 (%s)" % text[:30])
                level = 2
            notes.count["h%d" % level] += 1
            out.append("<h%d>%s</h%d>" % (level, inline(text, notes), level))
        elif BYLINE.match(s) and not notes.count["h2"] and "](" in s:
            flush()
            cats = re.findall(r"\[([^\]]+)\]\(", BYLINE.match(s).group(2))
            notes.changed.append("바이라인은 본문에서 빼고 카테고리를 맨 위 주석에 적음 (WordPress가 저자, 날짜, 카테고리를 표시한다)")
            i += 1
        elif HR.match(line):
            flush()
            notes.count["hr"] += 1
            i += 1
        elif s.startswith("|") and i + 1 < len(lines) and "-" in lines[i + 1] and SEPARATOR.match(lines[i + 1]):
            flush()
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            out.append(table(lines[i:j], notes))
            notes.count["table"] += 1
            i = j
        elif IMAGE_LINE.match(s):
            flush()
            im = IMAGE_LINE.match(s)
            out.append('<p style="%s">%s</p>' % (FIGURE_STYLE, image(im.group(1), im.group(2), notes)))
            i += 1
        elif CAPTION.match(s):
            flush()
            out.append('<p style="%s"><em>%s</em></p>' % (CAPTION_STYLE, inline(CAPTION.match(s).group(1), notes)))
            notes.count["caption"] += 1
            i += 1
        elif s.startswith(">"):
            flush()
            groups = [[]]
            while i < len(lines) and lines[i].strip().startswith(">"):
                text = re.sub(r"^\s*>\s?", "", lines[i]).strip()
                if text:
                    groups[-1].append(text)
                elif groups[-1]:
                    groups.append([])
                i += 1
            out.append("<blockquote>\n%s\n</blockquote>" % "\n".join(
                "<p>%s</p>" % inline(" ".join(g), notes) for g in groups if g))
        elif LIST.match(line):
            flush()
            items, i = read_list(lines, i, notes)
            pos = 0
            while pos < len(items):  # a change of marker kind or a step back in indent starts another list
                rendered, pos = render_list(items, notes, pos)
                out.append(rendered)
                notes.count["list"] += 1
        else:
            para.append(line)
            i += 1
    flush()

    if notes.count["hr"]:
        notes.changed.append("구분선(hr) %d개 제거 (h2 제목이 섹션을 구분한다)" % notes.count["hr"])
    if notes.count["autolink"]:
        notes.warn.append("꺾쇠로 감싼 URL %d개를 링크로 바꿈: 협업 도구에 붙여넣다 생긴 것인지 확인한다" % notes.count["autolink"])
    if notes.count["raw_html"]:
        notes.warn.append("HTML 태그가 든 줄 %d개: 태그를 글자로 바꿔 넣었다. 필요한 태그는 wordpress.md에 직접 적는다"
                          % notes.count["raw_html"])
    if notes.count["h4"] or notes.count["h5"] or notes.count["h6"]:
        notes.warn.append("h4 이하 헤딩이 있음: 원고 구조는 h3까지다")

    if not title:
        notes.fail.append("제목 없음: 프론트매터 title 또는 H1")
    source = "--slug"
    if not slug:
        slug, source = meta.get("slug"), "프론트매터 slug"
    if not slug:
        slug, source = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", re.sub(r"\.md$", "", name)), "파일 이름에서 날짜를 뺀 값"
        notes.warn.append("프론트매터에 slug: 가 없어 파일 이름에서 만든 값을 썼다 (%s): 제목의 핵심어로 slug: 를 적고 다시 변환한다" % slug)
    if not SLUG.match(slug or ""):
        notes.fail.append("영어 URL slug를 정할 수 없음 (%s: %r): 프론트매터에 slug: <소문자와 하이픈>을 적는다" % (source, slug))

    html_body = "\n\n".join(out)
    recount(md, html_body, notes)
    if notes.fail:
        return None
    head = ["<!--", "제목: %s" % comment_text(title), "추천 URL slug: %s (%s)" % (slug, source),
            "예상 URL: https://aws.amazon.com/ko/blogs/%s/%s/" % (channel, slug)]
    if cats:
        head.append("카테고리: %s" % ", ".join(comment_text(c) for c in cats))
    head.append("-->")
    return "\n".join(head) + "\n\n" + html_body + "\n"


def outside_fences(md):
    """(number of fenced code blocks, the lines of the draft that are not inside one)."""
    count, mark, kept = 0, None, []
    for line in md.split("\n"):
        if mark:
            if fence_close(line, mark):
                mark = None
                count += 1
        elif fence_open(line):
            mark = fence_open(line).group(2)
        else:
            kept.append(line)
    return count, kept


def recount(md, body, notes):
    """Count the draft's blocks a second way and compare with what was written; a difference stops the conversion."""
    fences, lines = outside_fences(md)
    tables = sum(1 for k, l in enumerate(lines)
                 if l.lstrip().startswith("|") and (k == 0 or not lines[k - 1].lstrip().startswith("|")))
    images = len(re.findall(r"!\[" + ALT + r"\]\([^)]+\)", re.sub(r"`[^`\n]*`", "", "\n".join(lines))))
    captions = sum(1 for l in lines if CAPTION.match(l.strip()))
    for label, want, have in (("코드 블록", fences, body.count("<pre><code ")),
                              ("표", tables, body.count("<table ")),
                              ("이미지", images, body.count("<img ")),
                              ("캡션", captions, body.count('<p style="%s"><em>' % CAPTION_STYLE))):
        if want != have:
            notes.fail.append("변환 검산 불일치: %s 원고 %d개, 변환본 %d개 (변환기가 읽지 못한 문법이 있다)" % (label, want, have))
    first = re.search(r"<h(\d)>", body)
    if first and first.group(1) != "2":
        notes.fail.append("본문의 첫 헤딩이 h%s: h2로 시작해야 한다" % first.group(1))
    for tag in ("<h1", "<hr"):
        if tag in body:
            notes.fail.append("변환본에 %s 태그가 남음" % tag[1:])


def main(argv):
    ap = argparse.ArgumentParser(description="Markdown blog draft to HTML for the WordPress code editor.")
    ap.add_argument("draft")
    ap.add_argument("--out", required=True, help="file to write (wordpress.md)")
    ap.add_argument("--slug", help="English URL slug; default: frontmatter slug, then the file name without its date")
    ap.add_argument("--channel", default="tech", choices=("tech", "korea"), help="blog channel of the expected URL")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.draft):
        ap.error("draft not found: %s" % args.draft)
    if os.path.abspath(args.out) == os.path.abspath(args.draft):
        ap.error("--out is the draft itself")
    notes = Notes(os.path.dirname(os.path.abspath(args.draft)))
    md = io.open(args.draft, encoding="utf-8-sig", newline="").read()
    result = convert(md, notes, args.slug, args.channel, os.path.basename(args.draft))

    print("== %s -> %s" % (args.draft, args.out))
    c = notes.count
    print("  h2 %d, h3 %d, 문단 %d, 목록 %d, 표 %d, 이미지 %d, 캡션 %d, 코드 블록 %d%s" % (
        c["h2"], c["h3"], c["p"], c["list"], c["table"], c["img"], c["caption"], len(notes.langs),
        " (%s)" % ", ".join("lang-" + l for l in notes.langs) if notes.langs else ""))
    for line in notes.changed:
        print("  [변환] %s" % line)
    for line in notes.warn:
        print("  [!] %s" % line)
    for line in notes.fail:
        print("  [FAIL] %s" % line)
    if result is None:
        print("  not written: %d problem(s)" % len(notes.fail))
        return 1
    with io.open(args.out, "w", encoding="utf-8") as f:
        f.write(result)
    print("  OK: %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

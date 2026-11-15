#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn a published AWS blog post into a techblogs work folder.

Usage: python3 import_aws_post.py <post-url-or-saved.html> <work-dir> [--slug NAME]

Writes <work-dir>/meta.json (title, date, origin, sources, image list), <work-dir>/ko.body.html
(sections in the template markup of references/design-spec.md) and <work-dir>/images/.
The page is input data: only the article body is read, inline markup is reduced to an allowlist,
and images are fetched only from the AWS blog hosts. Fields the editor must fill in meta.json are
left as "TODO" and build_post.py refuses to build while one remains.

Pictures are taken wherever they sit: alone in a paragraph, at the end of a text paragraph, or inline as
base64. Editor placeholders (an address without an image file name) are dropped. The last lines report
how much of the article text was carried over ("coverage") and every block that was left out; read them
before editing, because the post must keep the content of the original.
"""
import base64
import struct
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

AWS_HOSTS = {"aws.amazon.com", "d2908q01vomqb2.cloudfront.net"}
VOID = {"br", "img", "hr", "col", "input", "meta", "link", "wbr"}
INLINE_KEEP = {"a", "b", "strong", "em", "i", "code", "br", "sup", "sub"}
UA = "techblogs-import"


class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs or []), parent, []

    def text(self):
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)

    def find(self, tag):
        out = []
        for k in self.kids:
            if isinstance(k, Node):
                if k.tag == tag:
                    out.append(k)
                out.extend(k.find(tag))
        return out


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


def esc(s):
    return html.escape(s, quote=False)


LOCALE = ""  # "/ko" when the post lives under aws.amazon.com/ko/; set in main()


def absolute(url):
    url = url.strip()
    # A root-relative link on a localized page is redirected to the localized address; write that one.
    if LOCALE and url.startswith("/") and not url.startswith("//") and not url.startswith(LOCALE + "/"):
        url = LOCALE + url
    return urllib.parse.urljoin("https://aws.amazon.com/", url)


def inline(node):
    """Inline HTML of a node's children, reduced to the allowlist."""
    out = []
    for k in node.kids:
        if isinstance(k, str):
            out.append(esc(k))
        elif k.tag == "br":
            out.append("<br>")
        elif k.tag == "a" and re.match(r"^https?://", absolute(k.attrs.get("href", ""))):
            out.append('<a href="%s" target="_blank" rel="noopener">%s</a>'
                       % (html.escape(absolute(k.attrs["href"]), quote=True), inline(k)))
        elif k.tag in ("b", "strong"):
            out.append("<b>%s</b>" % inline(k))
        elif k.tag in ("em", "i"):
            out.append("<em>%s</em>" % inline(k))
        elif k.tag in ("code", "sup", "sub"):
            out.append("<%s>%s</%s>" % (k.tag, inline(k), k.tag))
        elif k.tag == "img":
            continue
        else:
            out.append(inline(k))
    return re.sub(r"[ \t\r\n]+", " ", "".join(out)).strip()


def render_list(node):
    items = []
    for li in node.kids:
        if not isinstance(li, Node) or li.tag != "li":
            continue
        nested = "".join(render_list(k) for k in li.kids if isinstance(k, Node) and k.tag in ("ul", "ol"))
        flat = Node("li", parent=None)
        flat.kids = [k for k in li.kids if not (isinstance(k, Node) and k.tag in ("ul", "ol"))]
        items.append("<li>%s%s</li>" % (inline(flat), nested))
    return "<%s>\n%s\n</%s>" % (node.tag, "\n".join(items), node.tag)


def render_table(node):
    rows = []
    for tr in node.find("tr"):
        cells = [c for c in tr.kids if isinstance(c, Node) and c.tag in ("th", "td")]
        rows.append((any(c.tag == "th" for c in cells) and all(c.tag == "th" for c in cells),
                     "<tr>%s</tr>" % "".join("<%s>%s</%s>" % (c.tag, inline(c), c.tag) for c in cells)))
    head = [r for h, r in rows if h]
    body = [r for h, r in rows if not h]
    parts = ["<div class=\"scroll\"><table>"]
    if head:
        parts.append("<thead>\n%s\n</thead>" % "\n".join(head))
    parts.append("<tbody>\n%s\n</tbody>" % "\n".join(body))
    parts.append("</table></div>")
    return "\n".join(parts)


def render_pre(node):
    code = node.find("code")
    lang = "text"
    if code:
        m = re.search(r"lang(?:uage)?-([\w+-]+)", code[0].attrs.get("class", ""))
        if m:
            lang = m.group(1).lower()
    text = node.text().strip("\n")
    return ('<div class="snippet"><div class="snippet-bar"><span class="lang">%s</span>'
            '<button type="button" class="copy"><span class="i">복사</span><span class="ok">복사됨</span></button></div>'
            "<pre><code>%s</code></pre></div>") % (esc(lang), esc(text))


CAP = re.compile(r"^\s*(그림|표)\s*(\d+)\s*[.:]?\s*(.*)$", re.S)
REFS = re.compile(r"^(참고\s*자료|참고\s*문헌|참고\s*문서|참조|References?)$", re.I)
B64 = re.compile(r"^(?:data:)?image/(png|jpe?g|gif|webp);base64,", re.I)
IMG_EXT = re.compile(r"\.(png|jpe?g|gif|webp|svg)$", re.I)


def real_imgs(node):
    """img nodes worth keeping: an address that ends in an image file name, or an inline base64 picture."""
    out = []
    for im in ([node] if node.tag == "img" else node.find("img")):
        src = im.attrs.get("src", "").strip()
        if B64.match(src) or IMG_EXT.search(urllib.parse.urlparse(absolute(src)).path):
            out.append(im)
    return out


def image_first(node):
    """True when a picture comes before any text of the block."""
    for k in node.kids:
        if isinstance(k, str):
            if k.strip():
                return False
        elif k.tag == "img" or k.find("img"):
            return bool(real_imgs(k)) or image_first(k)
        elif k.text().strip():
            return False
    return True


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def convert(body, slug, images, dropped):
    """Return (sections, sources, trailing notes). A section is [number, title, [html blocks]].

    A figure is written as the token \\x00FIGn\\x00 and filled in after the pictures are saved.
    """
    sections = [["", "들어가며", []]]
    sources, notes = [], []
    in_refs = False
    flat = []
    for b in (k for k in body.kids if isinstance(k, Node)):
        # 감싸는 div(wp-caption 제외)는 안쪽 블록으로 푼다.
        if b.tag == "div" and "wp-caption" not in b.attrs.get("class", "") and any(isinstance(k, Node) and k.tag in (
                "p", "pre", "table", "ul", "ol", "h2", "h3", "h4", "blockquote", "div", "figure") for k in b.kids):
            flat.extend(k for k in b.kids if isinstance(k, Node))
        else:
            flat.append(b)
    i = 0
    tbl_no = 0
    while i < len(flat):
        b = flat[i]
        out = sections[-1][2]
        text = b.text().strip()
        pics = real_imgs(b) if b.tag in ("p", "div", "figure") else []
        if b.tag == "h2":
            title = re.sub(r"\s+", " ", text)
            in_refs = bool(REFS.match(title))
            if not in_refs:
                m = re.match(r"^(\d+)\s*[.)]\s*(.+)$", title)
                sections.append([m.group(1) if m else "", m.group(2) if m else title, []])
        elif in_refs:
            if b.tag in ("ul", "ol"):
                # 항목 전체 글자를 제목으로 둔다. 링크 뒤의 설명("- 게시처, 확인한 날")도 원문의 일부다.
                for li in b.find("li"):
                    links = [a for a in li.find("a") if re.match(r"^https?://", absolute(a.attrs.get("href", "")))]
                    full = re.sub(r"\s+[–—]\s+", " - ", re.sub(r"\s+", " ", li.text()).strip())
                    if links:
                        sources.append({"title": full, "url": absolute(links[0].attrs["href"])})
                    elif full:
                        notes.append(esc(full))
            elif b.tag == "p" and text:
                notes.append(inline(b))
            elif text:
                dropped.append("%s: %s" % (b.tag, text[:50]))
        elif b.tag in ("h3", "h4"):
            out.append("<h3>%s</h3>" % inline(b))
        elif pics:
            wp = [p for p in b.find("p") if "wp-caption-text" in p.attrs.get("class", "")]
            rest = inline(b) if not wp else ""
            rest_text = plain(rest).strip()
            same_cap = bool(rest_text and image_first(b) and CAP.match(rest_text) and CAP.match(rest_text).group(1) == "그림")
            if rest_text and not image_first(b):
                out.append("<p>%s</p>" % rest)
            for n, img in enumerate(pics):
                cap = ""
                last = n == len(pics) - 1
                if wp:
                    cap = inline(wp[0])
                elif same_cap and last:
                    cap = rest
                elif last:
                    j = i + 1
                    while j < len(flat) and not flat[j].text().strip() and not real_imgs(flat[j]):
                        j += 1
                    if j < len(flat) and flat[j].tag == "p" and not real_imgs(flat[j]):
                        m = CAP.match(flat[j].text())
                        if m and m.group(1) == "그림":
                            cap = inline(flat[j])
                            i = j
                alt = re.sub(r"\s+", " ", img.attrs.get("alt", "")).strip()
                m = CAP.match(plain(cap))
                cap_text = m.group(3).strip() if m and m.group(1) == "그림" else plain(cap).strip()
                images.append({"src": img.attrs.get("src", "").strip(), "alt": alt, "caption": cap_text or alt,
                               "w": img.attrs.get("width", ""), "h": img.attrs.get("height", "")})
                out.append("\x00FIG%d\x00" % len(images))
            if rest_text and image_first(b) and not same_cap and not wp:
                out.append("<p>%s</p>" % rest)
        elif b.tag == "p":
            m = CAP.match(text)
            if m and m.group(1) == "표" and out and out[-1].startswith('<div class="scroll">'):
                tbl_no += 1
                out.append('<p class="cap"><b>표 %d.</b> %s</p>' % (tbl_no, esc(m.group(3).strip())))
            elif text:
                out.append("<p>%s</p>" % inline(b))
        elif b.tag in ("ul", "ol"):
            out.append(render_list(b))
        elif b.tag == "table":
            out.append(render_table(b))
        elif b.tag == "pre":
            out.append(render_pre(b))
        elif b.tag == "blockquote":
            ps = [k for k in b.kids if isinstance(k, Node) and k.tag == "p"] or [b]
            out.append("<blockquote>%s</blockquote>" % "".join("<p>%s</p>" % inline(p) for p in ps))
        elif b.tag not in ("footer", "hr", "script", "style") and text:
            dropped.append("%s: %s" % (b.tag, text[:50]))
        i += 1
    return [s for s in sections if s[2]], sources, notes


def section_html(lang, n, number, title, blocks):
    eyebrow = '<p class="eyebrow">%02d</p>' % int(number) if number else ""
    return ('<section class="sec" id="%s-s%d"><header class="sec-head">%s<h2>%s</h2></header><div class="prose">\n%s\n</div></section>'
            % (lang, n, eyebrow, esc(title), "\n".join(blocks)))


def source_kind(url):
    host, path = urllib.parse.urlparse(url).netloc, urllib.parse.urlparse(url).path
    if host.startswith("docs.aws.amazon.com"):
        return {"ko": "공식 문서", "en": "AWS docs"}
    if host == "aws.amazon.com" and "/blogs/" in path:
        return {"ko": "AWS 블로그", "en": "AWS blog"}
    if host == "aws.amazon.com" and "/whats-new/" in path:
        return {"ko": "새 소식", "en": "What's New"}
    if host == "aws.amazon.com":
        return {"ko": "AWS 페이지", "en": "AWS page"}
    if host.endswith("github.com"):
        return {"ko": "GitHub", "en": "GitHub"}
    return {"ko": "웹 문서", "en": "Web"}


def fetch(url):
    if urllib.parse.urlparse(url).netloc not in AWS_HOSTS:
        raise SystemExit("AWS 블로그 호스트가 아닙니다: %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def pixel_size(data):
    """(width, height) of a PNG, GIF or JPEG, else (0, 0)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker, size = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + size
    return 0, 0


def save_image(im, n, work):
    """Save picture n, fill in im["file"] and the display size, and return its <figure>."""
    src = im["src"]
    m = B64.match(src)
    if m:
        data = base64.b64decode(src[m.end():])
        name = "fig%02d.%s" % (n, "jpg" if m.group(1).lower().startswith("jp") else m.group(1).lower())
    else:
        url = absolute(src)
        base = os.path.basename(urllib.parse.urlparse(url).path)
        full = re.sub(r"-\d+x\d+(\.[A-Za-z]+)$", r"\1", url)  # WordPress size variant -> the original file
        data = None
        for u in ([full, url] if full != url else [url]):
            try:
                data = fetch(u)
                base = os.path.basename(urllib.parse.urlparse(u).path)
                break
            except (Exception, SystemExit) as e:  # noqa: BLE001 - try the next address, then report
                err = e
        name = "fig%02d-%s" % (n, re.sub(r"[^A-Za-z0-9._-]", "-", base))
        if data is None:
            # 그림 자리는 본문에 남긴다. 파일이 없으면 build_post.py가 멈추므로 빠뜨린 채로 게시되지 않는다.
            print("WARN  그림을 받지 못했습니다: %s (%s). images/%s 파일을 직접 넣습니다." % (url, err, name))
    if data is not None:
        open(os.path.join(work, "images", name), "wb").write(data)
    fw, fh = pixel_size(data) if data is not None else (0, 0)
    aw = int(im["w"]) if im["w"].isdigit() else 0
    ah = int(im["h"]) if im["h"].isdigit() else 0
    wide = aw >= 900 if aw else fw >= 1200  # the width the author gave is the intended display width
    if fw and fh:
        w = fw if wide else min(aw or fw, fw)
        h = round(fh * w / fw)
    else:
        w, h = aw, ah
    size = ' width="%d" height="%d"' % (w, h) if w and h else ""
    im["file"] = name
    if not im["caption"]:
        print("WARN  그림 %d에 캡션과 alt가 없습니다. 앞 문단을 보고 캡션을 씁니다: %s" % (n, name))
    cap = (" " + esc(im["caption"])) if im["caption"] else ""
    return ('<figure class="fig"><div class="canvas%s"><img src="images/%s" alt="%s"%s loading="lazy"></div>'
            "<figcaption><b>그림 %d.</b>%s</figcaption></figure>"
            % (" wide" if wide else "", name, html.escape(im["alt"] or im["caption"] or "그림 %d" % n, quote=True), size, n, cap))


def main():
    global LOCALE
    argv = sys.argv[1:]
    slug = None
    if "--slug" in argv[:-1]:  # the value after --slug is not a positional argument
        i = argv.index("--slug")
        slug = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 2 or any(a.startswith("--") for a in argv):
        raise SystemExit(__doc__)
    src, work = argv
    if re.match(r"^https?://", src):
        page, url = fetch(src).decode("utf-8", "replace"), src
    else:
        page = open(src, encoding="utf-8", errors="replace").read()
        m = re.search(r'<link rel="canonical" href="([^"]+)"', page)
        url = m.group(1) if m else ""
    m = re.search(r'<section class="blog-post-content[^"]*"[^>]*>(.*?)</section>', page, re.S)
    if not m:
        raise SystemExit("본문(section.blog-post-content)을 찾지 못했습니다.")
    slug = slug or os.path.basename(urllib.parse.urlparse(url).path.rstrip("/")) or "post"
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise SystemExit("slug는 영문 소문자, 숫자, 하이픈만 씁니다: %s" % slug)
    lm = re.match(r"^/([a-z]{2})/", urllib.parse.urlparse(url).path)
    LOCALE = "/" + lm.group(1) if lm else ""
    tree = Tree()
    tree.feed(m.group(1))
    images, dropped = [], []
    sections, sources, notes = convert(tree.root, slug, images, dropped)

    def meta(prop):
        mm = re.search(r'<meta[^>]+property="%s"[^>]+content="([^"]*)"' % re.escape(prop), page)
        return html.unescape(mm.group(1)) if mm else ""

    title = re.sub(r"\s*\|\s*(Amazon Web Services|AWS 기술 블로그).*$", "", meta("og:title")).strip()
    cats = [html.unescape(c) for c in re.findall(r'<span property="articleSection">(.*?)</span>', page)]
    os.makedirs(os.path.join(work, "images"), exist_ok=True)
    figures = {}
    for n, im in enumerate(images, 1):
        figures["\x00FIG%d\x00" % n] = save_image(im, n, work)
    body = "\n".join(section_html("ko", n, num, t, [figures.get(b, b) for b in blocks if figures.get(b, b)])
                     for n, (num, t, blocks) in enumerate(sections, 1))
    open(os.path.join(work, "ko.body.html"), "w", encoding="utf-8").write(body + "\n")
    data = {
        "slug": slug,
        "category": "TODO", "category_dir": "TODO", "icon": "TODO", "minutes": 0,
        "date": meta("article:published_time")[:10],
        "tags": cats,
        "title": {"ko": title, "en": "TODO"},
        "excerpt": {"ko": "TODO", "en": "TODO"},
        "thesis": {"ko": "TODO", "en": "TODO"},
        "facts": [],
        "origin": {"name": {"ko": "AWS 기술 블로그", "en": "AWS Tech Blog (Korean)"}, "url": url, "date": meta("article:published_time")[:10]},
        "author": {"ko": "TODO", "en": "TODO"},
        "note": {"ko": " ".join(plain(n) for n in notes), "en": "TODO" if notes else ""},
        "sources": [dict(s, kind=source_kind(s["url"]), accessed="TODO") for s in sources],
    }
    open(os.path.join(work, "meta.json"), "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    # 원문 글자가 얼마나 옮겨졌는지: 본문(저자 상자 제외)의 글자 수와 옮긴 글자 수를 비교한다.
    def squeeze(s):
        return re.sub(r"\s+", "", s)
    src_body = re.sub(r"<footer\b.*?</footer>", "", m.group(1), flags=re.S)
    src_n = len(squeeze(plain(src_body)))
    kept = re.sub(r'<div class="snippet-bar">.*?</div>|<p class="eyebrow">.*?</p>|<b>(그림|표) \d+\.</b>', "", body)
    kept_n = len(squeeze(plain(kept))) + sum(len(squeeze(s["title"])) for s in sources) + sum(len(squeeze(plain(n))) for n in notes)
    ratio = kept_n / src_n if src_n else 1.0
    print("sections: %d, figures: %d, sources: %d, coverage: %.1f%% (%d of %d characters)"
          % (len(sections), len(images), len(sources), ratio * 100, kept_n, src_n))
    if ratio < 0.97:
        print("WARN  원문 글자의 %.1f%%만 옮겨졌습니다. 빠진 블록을 원문과 대조합니다." % (ratio * 100))
    for d in dropped:
        print("WARN  옮기지 않은 블록: %s" % d)
    print("wrote: %s" % os.path.join(work, "meta.json"))
    print("wrote: %s" % os.path.join(work, "ko.body.html"))


if __name__ == "__main__":
    main()

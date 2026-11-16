#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a techblogs post from a work folder.

Usage: python3 build_post.py <work-dir> [--out DIR]

Reads <work-dir>/meta.json, ko.body.html, en.body.html and images/, fills ../assets/template.html and
writes, under --out (default <work-dir>/out):
  <slug>-report.html   the bilingual report page (style and script copied from the template unchanged)
  <slug>.md            the front matter file of the blog's report layout
  <slug>-assets/       the images the page refers to
Nothing is written into the skill folder. Exit code 1 when a required value is missing.
"""
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")
SITE = "https://whchoi98.github.io"


# The storylines a new post can follow (references/storylines.md); design-spec.md lists the same keys
STORYLINES = ("qa", "troubleshoot", "measure", "compare", "build", "anatomy", "change", "retro")


def die(msg):
    print("ERROR " + msg)
    sys.exit(1)


def esc(s):
    return html.escape(str(s), quote=False)


def attr(s):
    return html.escape(str(s), quote=True)


def pair(ko, en):
    return '<span class="l-ko">%s</span><span class="l-en">%s</span>' % (ko, en)


def both(d, key):
    v = d.get(key) or {}
    if not isinstance(v, dict) or not str(v.get("ko", "")).strip() or not str(v.get("en", "")).strip():
        die("meta.json: %s 에 ko와 en 값이 모두 있어야 합니다." % key)
    return v["ko"], v["en"]


def walk_todo(v, path=""):
    if isinstance(v, dict):
        for k, x in v.items():
            walk_todo(x, path + "." + k if path else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            walk_todo(x, "%s[%d]" % (path, i))
    elif isinstance(v, str) and v.strip() == "TODO":
        die("meta.json: %s 가 TODO로 남아 있습니다." % path)


def sections(body, lang):
    """[(id, h2 text)] in order; ids must be <lang>-s1, <lang>-s2, ..."""
    found = re.findall(r'<section class="sec" id="([^"]+)">\s*<header class="sec-head">.*?<h2>(.*?)</h2>', body, re.S)
    for n, (sid, _) in enumerate(found, 1):
        if sid != "%s-s%d" % (lang, n):
            die("%s.body.html: %d번째 절의 id가 %s-s%d 가 아니라 %s 입니다." % (lang, n, lang, n, sid))
    if not found:
        die("%s.body.html: 절(section.sec)이 없습니다." % lang)
    return found


def main():
    argv = sys.argv[1:]
    out = None
    if "--out" in argv[:-1]:  # the value after --out is not the work folder
        i = argv.index("--out")
        out = os.path.abspath(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) != 1 or argv[0].startswith("--"):
        raise SystemExit(__doc__)
    work = os.path.abspath(argv[0])
    out = out or os.path.join(work, "out")
    if os.path.commonpath([out, os.path.abspath(os.path.join(HERE, ".."))]) == os.path.abspath(os.path.join(HERE, "..")):
        die("skill 폴더 안에는 쓰지 않습니다: %s" % out)
    try:
        meta = json.load(open(os.path.join(work, "meta.json"), encoding="utf-8"))
    except (OSError, ValueError) as e:
        die("meta.json을 읽지 못했습니다: %s" % e)
    walk_todo(meta)
    slug = meta.get("slug", "")
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        die("meta.json: slug는 영문 소문자, 숫자, 하이픈만 씁니다.")
    for k in ("category", "category_dir", "icon", "date"):
        if not str(meta.get(k, "")).strip():
            die("meta.json: %s 값이 없습니다." % k)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["date"]):
        die("meta.json: date는 YYYY-MM-DD 형식입니다.")
    if not re.match(r"^[a-z0-9-]+$", meta["category_dir"]):
        die("meta.json: category_dir는 블로그 docs/techblog 아래의 폴더 이름입니다.")
    storyline = str(meta.get("storyline") or "").strip()
    if storyline and storyline not in STORYLINES:
        die("meta.json: storyline은 %s 가운데 하나입니다: %s" % (", ".join(STORYLINES), storyline))
    title_ko, title_en = both(meta, "title")
    excerpt_ko, excerpt_en = both(meta, "excerpt")
    thesis_ko, thesis_en = both(meta, "thesis")
    bodies = {}
    for lang in ("ko", "en"):
        p = os.path.join(work, lang + ".body.html")
        if not os.path.isfile(p):
            die("%s 가 없습니다." % p)
        bodies[lang] = open(p, encoding="utf-8").read().strip()
    secs = {lang: sections(bodies[lang], lang) for lang in ("ko", "en")}
    if len(secs["ko"]) != len(secs["en"]):
        die("절 수가 다릅니다: ko %d, en %d" % (len(secs["ko"]), len(secs["en"])))

    assets = slug + "-assets"
    used = sorted(set(re.findall(r'src="images/([^"]+)"', bodies["ko"] + bodies["en"])))
    if os.path.isdir(os.path.join(out, assets)):
        shutil.rmtree(os.path.join(out, assets))  # a renamed picture must not leave its old file behind
    os.makedirs(os.path.join(out, assets), exist_ok=True)
    for name in used:
        src = os.path.join(work, "images", name)
        if os.path.basename(name) != name or not os.path.isfile(src):
            die("그림 파일이 없습니다: images/%s" % name)
        shutil.copyfile(src, os.path.join(out, assets, name))
    for lang in bodies:
        bodies[lang] = bodies[lang].replace('src="images/', 'src="%s/' % assets)

    origin = meta.get("origin") or {}
    report_src = "/docs/techblog/%s/%s-report.html" % (meta["category_dir"], slug)
    post_url = "%s/docs/techblog/%s/%s/" % (SITE, meta["category_dir"], slug)
    canonical = origin.get("url") or post_url
    minutes = int(meta.get("minutes") or 0)
    if minutes <= 0:
        text = re.sub(r"<[^>]+>", "", re.sub(r"<pre>.*?</pre>", "", bodies["ko"], flags=re.S))
        minutes = max(3, round(len(re.sub(r"\s+", "", text)) / 700))

    meta_top = ['<span class="mono">%s</span>' % pair("게시 " + esc(meta["date"]), "Published " + esc(meta["date"])),
                "<span>%s</span>" % esc(meta["category"]),
                "<span>%s</span>" % pair("읽는 시간 %d분" % minutes, "%d min read" % minutes)]
    if origin.get("url"):
        name_ko, name_en = both(origin, "name")
        link = '<a href="%s" target="_blank" rel="noopener">%%s</a>' % attr(origin["url"])
        meta_top.append('<span class="wide">%s</span>' % pair("원문 " + link % esc(name_ko), "First published on " + link % esc(name_en)))
    tags = "".join("<span>#%s</span>" % esc(t) for t in meta.get("tags") or [])
    facts = ""
    if meta.get("facts"):
        facts = '<ul class="facts">%s</ul>' % "".join("<li>%s</li>" % pair(f["ko"], f["en"]) for f in meta["facts"])

    srcs = meta.get("sources") or []
    toc = {}
    for lang, label in (("ko", "참고 자료"), ("en", "References")):
        links = ['<a href="#%s">%s</a>' % (sid, re.sub(r"<[^>]+>", "", t).strip()) for sid, t in secs[lang]]
        if srcs:
            links.append('<a href="#sources">%s</a>' % label)
        toc[lang] = "".join(links)
    sources = ""
    if srcs:
        rows = []
        for n, s in enumerate(srcs, 1):
            kind = s.get("kind") or {}
            rows.append('<tr id="src-%d"><td class="num"><b>%d</b></td><td class="t"><a href="%s" target="_blank" rel="noopener">%s</a></td>'
                        '<td class="nowrap">%s</td><td class="nowrap num">%s</td></tr>'
                        % (n, n, attr(s["url"]), esc(s["title"]), pair(esc(kind.get("ko", "")), esc(kind.get("en", ""))), esc(s.get("accessed", ""))))
        sources = ('<section class="sec" id="sources"><header class="sec-head"><h2>%s</h2></header><div class="prose">\n'
                   '<div class="scroll"><table class="src-t"><thead><tr><th>No.</th><th>%s</th><th>%s</th><th>%s</th></tr></thead>\n<tbody>\n%s\n</tbody></table></div>\n'
                   "</div></section>") % (pair("참고 자료", "References"), pair("출처", "Source"), pair("종류", "Kind"),
                                          pair("확인한 날", "Checked"), "\n".join(rows))

    foot = ["<h2>%s</h2>" % pair("이 글에 대하여", "About this post"), "<ul>"]
    if origin.get("url"):
        name_ko, name_en = both(origin, "name")
        link = '<a href="%s" target="_blank" rel="noopener">%%s</a>' % attr(origin["url"])
        foot.append("<li>%s</li>" % pair(
            "<b>원문</b> %s, %s 게시. 이 페이지는 같은 글을 옮겨 실으면서 문장을 다듬은 것입니다." % (link % esc(name_ko), esc(origin.get("date", ""))),
            "<b>Original</b> %s, published %s. This page republishes the same post with edited wording; the English text is a translation."
            % (link % esc(name_en), esc(origin.get("date", "")))))
    if meta.get("author"):
        a_ko, a_en = both(meta, "author")
        foot.append("<li>%s</li>" % pair("<b>글쓴이</b> " + esc(a_ko), "<b>Author</b> " + esc(a_en)))
    foot.append("</ul>")
    note = meta.get("note") or {}
    if str(note.get("ko", "")).strip():
        n_ko, n_en = both(meta, "note")
        foot.append("<p>%s</p>" % pair(esc(n_ko), esc(n_en)))
    colophon = ""
    if meta.get("colophon"):
        c_ko, c_en = both(meta, "colophon")
        colophon = '<p class="colophon">%s</p>' % pair(esc(c_ko), esc(c_en))
    site = meta.get("site") or {}

    fill = {
        "title_ko": esc(title_ko), "title_en": esc(title_en), "excerpt_ko": attr(excerpt_ko), "canonical": attr(canonical),
        "home_url": attr(site.get("url", "/")), "home_ko": esc(site.get("ko", "기술 블로그 홈")), "home_en": esc(site.get("en", "Tech blog home")),
        "meta_top": "".join(meta_top), "thesis_ko": esc(thesis_ko), "thesis_en": esc(thesis_en), "tags": tags, "facts": facts,
        "toc_ko": toc["ko"], "toc_en": toc["en"], "body_ko": bodies["ko"], "body_en": bodies["en"],
        "sources": sources, "foot": "\n".join(foot), "colophon": colophon,
    }
    page = open(TEMPLATE, encoding="utf-8").read()
    page = re.sub(r"\[\[([a-z_]+)\]\]", lambda m: fill[m.group(1)] if m.group(1) in fill else die("템플릿 토큰을 채우지 못했습니다: " + m.group(1)), page)
    report = os.path.join(out, slug + "-report.html")
    open(report, "w", encoding="utf-8").write(page)

    def q(s):
        return json.dumps(str(s), ensure_ascii=False)

    front = ["---", "title: " + q(title_ko), "title_en: " + q(title_en), "layout: report", "report_src: " + report_src,
             "date: " + meta["date"], "category: " + meta["category"], "tags: " + json.dumps(meta.get("tags") or [], ensure_ascii=False),
             "icon: " + meta["icon"], "minutes: %d" % minutes, "excerpt: " + q(excerpt_ko), "excerpt_en: " + q(excerpt_en), "---", ""]
    md = os.path.join(out, slug + ".md")
    open(md, "w", encoding="utf-8").write("\n".join(front))
    if storyline:
        print("storyline: " + storyline)
    elif not origin.get("url"):
        print("WARN  meta.json에 storyline이 없습니다. 새 글은 references/storylines.md에서 스토리라인을 골라 적습니다.")
    print("deliverables:")
    print("  " + report)
    print("  " + md)
    for name in used:
        print("  " + os.path.join(out, assets, name))


if __name__ == "__main__":
    main()

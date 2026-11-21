#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start a new techblogs post from the storyline template chosen for its topic and material.

Usage: python3 new_post.py --list
       python3 new_post.py <work-dir> --storyline KEY --slug NAME [--date YYYY-MM-DD]

--list prints every storyline with the material it fits and the signals to look for, so that one can
be chosen after reading the topic and the material (references/storylines.md has the full text).

The second form writes a work folder for a new post:
  meta.json       the storyline key, the slug and the date; every other field is "TODO"
  ko.body.html    one section per step of the storyline's section flow, each with a guide comment
  en.body.html    the same sections for the English body
  images/         empty
The section flow is read from ../references/storylines.md, so the templates and the document cannot
drift apart. Titles and paragraphs are "TODO", and build_post.py refuses to build while a "TODO" or a
guide comment remains. An existing meta.json or body file is never overwritten. Nothing is written
into the skill folder.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STORYLINES_MD = os.path.join(HERE, "..", "references", "storylines.md")
GUIDE = "안내:"   # build_post.py looks for "<!-- 안내:" in a body


def die(msg):
    print("ERROR " + msg)
    sys.exit(1)


def split_flow(text):
    """Split the section flow on commas that are not inside parentheses."""
    items, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip())
    return items


def load():
    """Read the storylines: key, name, the material it fits, the signals, flow, opening and closing."""
    try:
        text = open(STORYLINES_MD, encoding="utf-8").read()
    except OSError as e:
        die("storylines.md를 읽지 못했습니다: %s" % e)
    rows = {}
    for line in text.splitlines():
        m = re.match(r"^\| `([a-z]+)` \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", line)
        if m:
            rows[m.group(1)] = dict(name=m.group(2), fits=m.group(3), signals=m.group(4), gives=m.group(5))
    out = []
    for sec in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = sec.partition("\n")
        m = re.match(r"([a-z]+): (.+)$", head.strip())
        if not m or m.group(1) not in rows:
            continue
        item = dict(rows[m.group(1)], key=m.group(1))
        for label, field in (("챕터 흐름", "flow"), ("여는 방식", "opening"), ("닫는 방식", "closing")):
            lm = re.search(r"^- \*\*%s\*\*: (.+)$" % label, body, re.M)
            if not lm:
                die("storylines.md의 %s에 '%s' 줄이 없습니다." % (item["key"], label))
            item[field] = lm.group(1).strip()
        item["flow"] = split_flow(item["flow"])
        out.append(item)
    if not out:
        die("storylines.md에서 스토리라인을 찾지 못했습니다.")
    return out


def section(lang, n, total, step, extra):
    eyebrow = "" if n == 1 else '<p class="eyebrow">%02d</p>' % (n - 1)
    guide = "<!-- %s %d번째 챕터. %s%s -->" % (GUIDE, n, step, extra)
    return ('<section class="sec" id="%s-s%d"><header class="sec-head">%s<h2>TODO</h2></header><div class="prose">\n'
            "%s\n<p>TODO</p>\n</div></section>\n" % (lang, n, eyebrow, guide))


def body(lang, item):
    total = len(item["flow"])
    parts = []
    for n, step in enumerate(item["flow"], 1):
        extra = ""
        if n == 1:
            extra = " 여는 방식: " + item["opening"]
        elif n == total:
            extra = " 닫는 방식: " + item["closing"]
        parts.append(section(lang, n, total, step, extra))
    return "\n".join(parts)


def main():
    argv = sys.argv[1:]
    items = load()
    keys = [i["key"] for i in items]
    if argv == ["--list"]:
        for i in items:
            print("%s (%s)" % (i["key"], i["name"]))
            print("  맞는 소재: " + i["fits"])
            print("  보이는 신호: " + i["signals"])
            print("  챕터 흐름: " + ", ".join(i["flow"]))
        return
    opts = {}
    for name in ("--storyline", "--slug", "--date"):
        if name in argv[:-1]:  # the value after an option is not the work folder
            k = argv.index(name)
            opts[name] = argv[k + 1]
            del argv[k:k + 2]
    if len(argv) != 1 or argv[0].startswith("--") or "--storyline" not in opts or "--slug" not in opts:
        raise SystemExit(__doc__)
    work = os.path.abspath(argv[0])
    skill = os.path.abspath(os.path.join(HERE, ".."))
    if os.path.commonpath([work, skill]) == skill:
        die("skill 폴더 안에는 쓰지 않습니다: %s" % work)
    key = opts["--storyline"]
    if key not in keys:
        die("storyline은 %s 가운데 하나입니다: %s" % (", ".join(keys), key))
    slug = opts["--slug"]
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        die("slug는 영문 소문자, 숫자, 하이픈만 씁니다: %s" % slug)
    date = opts.get("--date") or datetime.date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        die("date는 YYYY-MM-DD 형식입니다: %s" % date)
    for name in ("meta.json", "ko.body.html", "en.body.html"):
        if os.path.exists(os.path.join(work, name)):
            die("이미 있는 파일은 덮어쓰지 않습니다: %s" % os.path.join(work, name))
    item = items[keys.index(key)]
    os.makedirs(os.path.join(work, "images"), exist_ok=True)
    pair = {"ko": "TODO", "en": "TODO"}
    meta = {
        "slug": slug, "category": "TODO", "category_dir": "TODO", "icon": "TODO", "date": date, "minutes": 0,
        "storyline": key, "tags": [],
        "title": dict(pair), "excerpt": dict(pair), "thesis": dict(pair), "facts": [],
        "author": dict(pair), "note": dict(pair), "sources": [],
    }
    open(os.path.join(work, "meta.json"), "w", encoding="utf-8").write(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    for lang in ("ko", "en"):
        open(os.path.join(work, lang + ".body.html"), "w", encoding="utf-8").write(body(lang, item))
    print("storyline: %s (%s), sections: %d" % (key, item["name"], len(item["flow"])))
    print("work folder: " + work)
    for n, step in enumerate(item["flow"], 1):
        print("  %d. %s" % (n, step))
    print("TODO와 안내 주석을 모두 채우고 지운 뒤 build_post.py를 실행합니다. 챕터는 소재에 맞게 더하거나 뺄 수 있습니다.")


if __name__ == "__main__":
    main()

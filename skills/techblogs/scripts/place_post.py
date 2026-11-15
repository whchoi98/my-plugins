#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy a built techblogs post into the blog repository and build the site.

Usage: python3 place_post.py <work-dir>/out <blog-repo> [--replace] [--build]

Copies <slug>.md, <slug>-report.html and <slug>-assets/ into <blog-repo>/docs/techblog/<category folder>/,
runs check_post.py on the placed files and, with --build, `bundle exec jekyll build`.
It never runs git: the last lines list the files to stage one by one. Commit and push are the user's call.
--replace  overwrite a post with the same slug (without it an existing post stops the script)
"""
import glob
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print("ERROR " + msg)
    sys.exit(1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        raise SystemExit(__doc__)
    out, blog = os.path.abspath(args[0]), os.path.abspath(args[1])
    if not os.path.isfile(os.path.join(blog, "_config.yml")) or not os.path.isdir(os.path.join(blog, "docs", "techblog")):
        die("블로그 저장소가 아닙니다(_config.yml, docs/techblog 없음): %s" % blog)
    # out 폴더에는 검사용으로 뽑은 ko.md, urls.md도 있을 수 있다. 리포트와 짝인 md만 front matter 파일이다.
    mds = [m for m in glob.glob(os.path.join(out, "*.md")) if os.path.isfile(m[:-3] + "-report.html")]
    if len(mds) != 1:
        die("out 폴더에 리포트(<slug>-report.html)와 짝인 front matter 파일(<slug>.md)이 하나 있어야 합니다: %d개" % len(mds))
    slug = os.path.basename(mds[0])[:-3]
    fm = open(mds[0], encoding="utf-8").read()
    kv = dict(re.findall(r"^([a-z_]+):\s*(.*)$", fm, re.M))
    cfg = open(os.path.join(blog, "_config.yml"), encoding="utf-8").read()
    cats = dict(re.findall(r"- name:\s*(.+?)\s*\n(?:\s+[a-z_]+:.*\n)*?\s+url:\s*(\S+)", cfg))
    if kv.get("category") not in cats:
        die("category가 _config.yml의 blog_categories에 없습니다: %s (있는 값: %s)" % (kv.get("category"), ", ".join(cats)))
    rel = cats[kv["category"]].strip("/")
    if not rel.startswith("docs/techblog/"):
        die("이 분류는 게시물 폴더가 아닙니다: %s" % cats[kv["category"]])
    dest = os.path.join(blog, rel)
    if not os.path.isdir(dest):
        die("분류 폴더가 없습니다: %s" % dest)
    report, assets = slug + "-report.html", slug + "-assets"
    if not os.path.isfile(os.path.join(out, report)):
        die("리포트 파일이 없습니다: %s" % os.path.join(out, report))
    if os.path.exists(os.path.join(dest, slug + ".md")) and "--replace" not in sys.argv:
        die("같은 slug의 글이 이미 있습니다: %s (덮어쓰려면 --replace)" % os.path.join(dest, slug + ".md"))
    placed = []
    for name in (slug + ".md", report):
        shutil.copyfile(os.path.join(out, name), os.path.join(dest, name))
        placed.append(os.path.join(rel, name))
    if os.path.isdir(os.path.join(out, assets)):
        if os.path.isdir(os.path.join(dest, assets)):
            shutil.rmtree(os.path.join(dest, assets))
        shutil.copytree(os.path.join(out, assets), os.path.join(dest, assets))
        placed.extend(os.path.join(rel, assets, f) for f in sorted(os.listdir(os.path.join(dest, assets))))
    rc = subprocess.call([sys.executable, os.path.join(HERE, "check_post.py"), os.path.join(dest, report), "--blog", blog])
    if rc != 0:
        die("배치한 글이 검사를 통과하지 못했습니다. 작업 폴더에서 고친 뒤 다시 빌드하고 배치합니다.")
    if "--build" in sys.argv:
        env = dict(os.environ)
        gems = sorted(glob.glob(os.path.expanduser("~/.local/share/gem/ruby/*/bin")))
        if gems:
            env["PATH"] = gems[-1] + os.pathsep + env.get("PATH", "")
        lab = os.path.join(blog, "scripts", "build-lab-zip.sh")
        if os.path.isfile(lab):
            subprocess.call(["bash", lab], cwd=blog, env=env, stdout=subprocess.DEVNULL)
        try:
            rc = subprocess.call(["bundle", "exec", "jekyll", "build", "-d", "_site"], cwd=blog, env=env)
        except FileNotFoundError:
            die("bundle 명령이 없습니다. 글은 배치했고 빌드만 하지 못했습니다. 블로그 저장소 README의 설치 절차(Ruby, Bundler)를 따른 뒤 --replace --build로 다시 실행합니다.")
        if rc != 0:
            die("jekyll build가 실패했습니다.")
        for built in (os.path.join("_site", rel, slug, "index.html"), os.path.join("_site", rel, report)):
            if not os.path.isfile(os.path.join(blog, built)):
                die("빌드 결과에 파일이 없습니다: %s" % built)
        print("built: %s" % os.path.join(blog, "_site", rel, slug, "index.html"))
    print("placed (stage these one by one, in %s):" % blog)
    for p in placed:
        print("  git add %s" % p)


if __name__ == "__main__":
    main()

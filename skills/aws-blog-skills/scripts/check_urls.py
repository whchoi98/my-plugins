#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check every http(s) URL in Markdown drafts: status 200 and no redirect to another page.

Usage: python3 check_urls.py <draft.md> [more.md ...]
Exit code 1 when any URL fails, so it can gate the reference list.

docs.aws.amazon.com answers a missing page by redirecting to the guide's first page with status 200
(checked 2026-11-01), so a final URL that differs from the requested one is reported as REDIRECT and
counts as a failure: replace the URL in the draft with the final one, or find the right page.
This only gates the link list. Reading the page itself (WebFetch) is still required for fact checks.
URLs on reserved example hosts (RFC 2606 / RFC 6761) and placeholders without a host are skipped.
"""
import io, re, sys, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

UA = "Mozilla/5.0 (X11; Linux x86_64) aws-blog-skills-check-urls"
URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'`]+")
RESERVED = ("example.com", "example.org", "example.net")
RESERVED_TLD = (".example", ".test", ".invalid", ".localhost")


def norm(u):
    p = urlsplit(u)
    path = p.path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


def skip(u):
    host = urlsplit(u).hostname or ""
    return not host or "." not in host or host in RESERVED or host.endswith(RESERVED) \
        or host.endswith(RESERVED_TLD) or host == "localhost"


def check(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            status, final = r.status, r.geturl()
    except urllib.error.HTTPError as e:
        status, final = e.code, e.geturl() or u
    except Exception as e:  # DNS, TLS, timeout
        return u, "ERROR", f"{type(e).__name__}: {e}"
    if status != 200:
        return u, "FAIL", f"HTTP {status}"
    if norm(final) != norm(u):
        return u, "REDIRECT", final
    return u, "OK", ""


def main(paths):
    urls, placeholders = [], set()
    for path in paths:
        text = io.open(path, encoding="utf-8").read()
        for m in URL_RE.finditer(text):
            u = m.group(0).rstrip(".,;:*_")
            if text[m.end():m.end() + 1] in ("<", "{"):  # e.g. .../category/<path>/ is a template, not a link
                placeholders.add(u)
            if u not in urls:
                urls.append(u)
    todo = [u for u in urls if not skip(u) and u not in placeholders]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(check, todo))
    bad = 0
    for u, verdict, note in results:
        if verdict != "OK":
            bad += 1
        print(f"  [{verdict}] {u}" + (f"  -> {note}" if note else ""))
    print(f"  urls={len(urls)} checked={len(todo)} skipped={len(urls) - len(todo)} failed={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))

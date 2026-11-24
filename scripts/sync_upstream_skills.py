#!/usr/bin/env python3
"""Keep the skills that come from other repositories in step with their sources.

scripts/upstream-skills.json names every vendored skill: the source repository, the folder inside it, the
files to take, the license, and the name and description my-plugins gives the skill. A vendored skill is
never edited by hand. Its SKILL.md body and every other file are the bytes of the source; only the `name`
and `description` of the frontmatter are replaced and three `metadata` lines are added.

  check    compare every source with what the manifest records; exit 10 when a skill has an update
  update   copy the changed skills in, write their frontmatter, the license copies, the manifest and
           the [Unreleased] section of CHANGELOG.md
  render   write the frontmatter again after `description` was edited in the manifest
  verify   offline: the vendored files are exactly what the manifest records

A source is other people's text that Claude will follow, so `update` refuses a source whose license
changed, a symbolic link, a file type the manifest does not allow and a file over the size limit, and it
writes a report of what changed for the person who reviews the pull request.

A skill with `"mode": "derived"` is not a copy. It is an edition of its source: `update` rebuilds it from
the source by the recipe the manifest names (literal replacements, anchored edits, files the edition keeps
as its own). The recipe fails when an anchor is gone or a token it forbids survives, so a change in the
source that the recipe does not cover stops the update before anything is written. No file of a source is
ever run, and a script of a source is copied byte for byte.

Standard library only. Exit codes: 0 done, 1 refused or failed, 10 an update is available (`check`).
"""
import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

MANIFEST = "scripts/upstream-skills.json"
DESC_MIN, DESC_MAX = 50, 1536          # Claude Code cuts the skill listing at 1,536 characters
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 8_000_000
SCRIPT_EXT = {".mjs", ".js", ".cjs", ".ts", ".py", ".sh"}
OUR_META = ("upstream", "upstream-commit", "modified")
KEY = re.compile(r"^([A-Za-z_][\w-]*):(.*)$")
URL = re.compile(r"https?://[^\s)>\"'`\]]+")
SAFE_PATH = re.compile(r"[A-Za-z0-9._/ -]+")   # a file name ends up in a report that GitHub renders
CHANGELOG_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
SCHEDULES = ("weekly", "biweekly")
TEXT_EXT = {".md", ".html"}            # the only file types a recipe may change
EXTRA = "extra:"                        # a recipe names a file outside the skill folder with this prefix
MARK = re.compile("(\x00[0-9]+\x00)")  # stands for a block of the edition while the source text is rewritten


class Refused(Exception):
    """The source or the manifest breaks a rule; nothing more is written for that skill."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def write(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    os.chmod(path, 0o644)


def git(*args, cwd=None):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    done = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if done.returncode != 0:
        raise Refused("git %s: %s" % (args[0], (done.stderr.strip().splitlines() or ["failed"])[-1]))
    return done.stdout.strip()


# ----------------------------------------------------------------------------------------------- manifest

def load_manifest(root):
    path = os.path.join(root, MANIFEST)
    try:
        data = json.loads(read(path).decode("utf-8"))
    except (OSError, ValueError) as err:
        raise Refused("%s: %s" % (MANIFEST, err))
    names = [e.get("name") for e in data.get("skills", [])]
    if not names or len(set(names)) != len(names):
        raise Refused("%s: `skills` is empty or holds a name twice" % MANIFEST)
    for entry in data["skills"]:
        check_entry(entry)
    return data


def save_manifest(root, data):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    write(os.path.join(root, MANIFEST), text.encode("utf-8"))


def check_entry(entry):
    name = entry.get("name", "")
    for field in ("name", "repo", "path", "license", "license_file", "description", "changes", "allow_ext"):
        if not entry.get(field):
            raise Refused("%s: `%s` is missing in the manifest" % (name or "?", field))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise Refused("%s: a skill name is lowercase letters, digits and hyphens" % name)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", entry["repo"]):
        raise Refused("%s: `repo` is owner/name on GitHub" % name)
    desc = entry["description"]
    if "\n" in desc or not DESC_MIN <= len(desc) <= DESC_MAX:
        raise Refused("%s: the description is one line of %d to %d characters (it has %d)"
                      % (name, DESC_MIN, DESC_MAX, len(desc)))
    if "\n" in entry["changes"] or ": " in entry["changes"]:
        raise Refused("%s: `changes` is one line without ': '" % name)
    if entry.get("mode", "vendored") not in ("vendored", "derived"):
        raise Refused("%s: `mode` is vendored or derived" % name)
    if entry.get("schedule", "weekly") not in SCHEDULES:
        raise Refused("%s: `schedule` is one of %s" % (name, ", ".join(SCHEDULES)))
    if is_derived(entry) and not entry.get("recipe"):
        raise Refused("%s: a derived skill names its `recipe` in the manifest" % name)


def is_derived(entry):
    return entry.get("mode") == "derived"


def source_url(entry):
    return "https://github.com/%s" % entry["repo"]


# ------------------------------------------------------------------------------------------- frontmatter

def split_frontmatter(text, where):
    """Return (frontmatter lines, body). The body starts right after the closing --- line."""
    lines = text.split("\n")
    if lines[0].rstrip("\r") != "---":
        raise Refused("%s: SKILL.md does not open with ---" % where)
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    raise Refused("%s: the SKILL.md frontmatter is not closed" % where)


def entries(fm_lines):
    """Top-level entries of the frontmatter in order: [key or None, [lines]]."""
    out = []
    for line in fm_lines:
        m = KEY.match(line)
        if m:
            out.append([m.group(1), [line]])
        elif out and (line[:1] in (" ", "\t") or not line.strip()):
            out[-1][1].append(line)
        else:
            out.append([None, [line]])
    return out


def scalar(lines):
    """The text of a one-key entry: a plain or quoted value, or a folded or literal block."""
    value = KEY.match(lines[0]).group(2).strip()
    if value[:1] in (">", "|") and len(value) <= 2:
        return ("\n" if value[0] == "|" else " ").join(l.strip() for l in lines[1:] if l.strip())
    rest = " ".join(l.strip() for l in lines[1:] if l.strip())
    value = (value + " " + rest).strip() if rest else value
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def field(fm_lines, key):
    for k, lines in entries(fm_lines):
        if k == key:
            return scalar(lines)
    return None


def yaml_scalar(text):
    """A YAML value on one line: plain when that is safe, double-quoted otherwise."""
    plain = (text == text.strip() and text[:1] not in "!&*-?|>'\"%@`#[]{},:"
             and ": " not in text and " #" not in text and not text.endswith(":"))
    if plain:
        return text
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


def render_frontmatter(entry, fm_lines, commit):
    """The source's frontmatter with our name and description and three more metadata lines."""
    ours = ["upstream: %s" % source_url(entry), "upstream-commit: %s" % commit,
            "modified: %s" % yaml_scalar(entry["changes"])]
    out, seen = [], set()
    for key, lines in entries(fm_lines):
        seen.add(key)
        if key == "name":
            out.append("name: %s" % entry["name"])
        elif key == "description":
            out.append("description: %s" % yaml_scalar(entry["description"]))
        elif key == "metadata":
            kids = [l for l in lines[1:] if l.strip()]
            if KEY.match(lines[0]).group(2).strip() or not kids:
                raise Refused("%s: the source's `metadata` is not a block of keys" % entry["name"])
            indent = kids[0][:len(kids[0]) - len(kids[0].lstrip())]
            taken = {l.strip().split(":")[0] for l in kids}
            if taken & set(OUR_META):
                raise Refused("%s: the source's metadata already has %s"
                              % (entry["name"], ", ".join(sorted(taken & set(OUR_META)))))
            out += [lines[0]] + kids + [indent + l for l in ours]
        else:
            out += lines
    for needed in ("name", "description"):
        if needed not in seen:
            raise Refused("%s: the source's frontmatter has no `%s`" % (entry["name"], needed))
    if "metadata" not in seen:
        out += ["metadata:"] + ["  " + l for l in ours]
    return out


def vendored_skill_md(entry, source_text, commit):
    fm, body = split_frontmatter(source_text, entry["name"])
    declared = field(fm, "license")
    if declared != entry["license"]:
        raise Refused("%s: the source's license is %r, the manifest says %r. Read the new terms before "
                      "syncing, then change `license` in the manifest" % (entry["name"], declared, entry["license"]))
    return "\n".join(["---"] + render_frontmatter(entry, fm, commit) + ["---", body]), field(fm, "description")


# ------------------------------------------------------------------------------------------------ source

def select_files(entry, src_root):
    """Files of the source that belong to the skill: {relative posix path: absolute path}."""
    base = os.path.normpath(os.path.join(src_root, entry["path"]))
    if not os.path.isdir(base):
        raise Refused("%s: the source has no folder %s" % (entry["name"], entry["path"]))
    include, exclude = entry.get("include") or ["*"], entry.get("exclude") or []
    allow = set(entry["allow_ext"])
    picked, total = {}, 0
    for folder, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in dirs:
            rel = os.path.relpath(os.path.join(folder, name), base).replace(os.sep, "/")
            wanted = any(p == "*" or p.startswith(rel + "/") for p in include)
            if os.path.islink(os.path.join(folder, name)) and wanted and not any(fnmatch.fnmatch(rel + "/x", p) for p in exclude):
                raise Refused("%s: the folder %s is a symbolic link in the source" % (entry["name"], rel))
        for name in sorted(files):
            full = os.path.join(folder, name)
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            if not any(fnmatch.fnmatch(rel, p) for p in include) or any(fnmatch.fnmatch(rel, p) for p in exclude):
                continue
            part = base
            for piece in rel.split("/"):
                part = os.path.join(part, piece)
                if os.path.islink(part):
                    raise Refused("%s: %s is a symbolic link in the source" % (entry["name"], rel))
            if not SAFE_PATH.fullmatch(rel):
                raise Refused("%s: %r is an unusual file name; review it" % (entry["name"], rel))
            if any(p.startswith(".") for p in rel.split("/")):
                raise Refused("%s: %s is a hidden file; name it in `exclude` or review it" % (entry["name"], rel))
            ext = os.path.splitext(name)[1].lower()
            if ext not in allow:
                raise Refused("%s: %s has a file type the manifest does not allow (%s). Review the file, then "
                              "add the type to `allow_ext`" % (entry["name"], rel, ext or "no extension"))
            size = os.path.getsize(full)
            if size > entry.get("max_file_bytes", MAX_FILE_BYTES):
                raise Refused("%s: %s is %d bytes, over the limit" % (entry["name"], rel, size))
            total += size
            picked[rel] = full
    if "SKILL.md" not in picked:
        raise Refused("%s: no SKILL.md in %s of the source" % (entry["name"], entry["path"]))
    if total > entry.get("max_total_bytes", MAX_TOTAL_BYTES):
        raise Refused("%s: the skill is %d bytes, over the limit" % (entry["name"], total))
    return picked


def fetch(entry, args, tmp):
    """Return (checkout folder, commit, commit date) of the source."""
    if args.source:
        if not os.path.isdir(args.source):
            raise Refused("--source %s is not a folder" % args.source)
        if os.path.isdir(os.path.join(args.source, ".git")) and not args.commit:
            return (args.source, git("rev-parse", "HEAD", cwd=args.source),
                    git("log", "-1", "--format=%cs", cwd=args.source))
        return args.source, args.commit or "local", args.date or datetime.date.today().isoformat()
    dest = os.path.join(tmp, entry["name"])
    if getattr(args, "pinned", False):
        if not entry.get("commit"):
            raise Refused("%s: --pinned needs a commit in the manifest" % entry["name"])
        git("init", "--quiet", dest)
        git("remote", "add", "origin", source_url(entry) + ".git", cwd=dest)
        git("fetch", "--depth", "1", "--quiet", "origin", entry["commit"], cwd=dest)
        git("checkout", "--quiet", "FETCH_HEAD", cwd=dest)
        return dest, git("rev-parse", "HEAD", cwd=dest), git("log", "-1", "--format=%cs", cwd=dest)
    cmd = ["clone", "--depth", "1", "--quiet"]
    if entry.get("ref", "HEAD") != "HEAD":
        cmd += ["--branch", entry["ref"]]
    git(*cmd, source_url(entry) + ".git", dest)
    return dest, git("rev-parse", "HEAD", cwd=dest), git("log", "-1", "--format=%cs", cwd=dest)


def remote_head(entry):
    ref = entry.get("ref", "HEAD")
    out = git("ls-remote", source_url(entry) + ".git", ref)
    if not out:
        raise Refused("%s: %s has no ref %s" % (entry["name"], entry["repo"], ref))
    return out.split()[0]


def source_state(entry, src_root):
    """Hashes of the source's files and of its license file."""
    picked = select_files(entry, src_root)
    lic = os.path.join(src_root, entry["license_file"])
    if not os.path.isfile(lic) or os.path.islink(lic):
        raise Refused("%s: the source has no %s" % (entry["name"], entry["license_file"]))
    return picked, {rel: sha256(read(full)) for rel, full in picked.items()}, sha256(read(lic))


def quoted(text, limit=600):
    """Text of a source for the report: one code span, so nothing in it is rendered or notifies anyone."""
    text = " ".join(text.split()).replace("`", "'")
    return "`%s`" % (text[:limit] + ("..." if len(text) > limit else ""))


def diff_files(old, new):
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(rel for rel in set(old) & set(new) if old[rel] != new[rel])
    return added, changed, removed


# ------------------------------------------------------------------------------------------------ update

def skill_dir(root, entry):
    return os.path.join(root, "skills", entry["name"])


def license_path(root, entry):
    return os.path.join(root, "third_party", "LICENSE-%s" % entry["name"])


def links_in(folder):
    found = set()
    for base, _dirs, files in os.walk(folder):
        for name in files:
            try:
                found |= {u.rstrip(".,;:") for u in URL.findall(read(os.path.join(base, name)).decode("utf-8"))}
            except (UnicodeDecodeError, OSError):
                pass
    return found


def apply(root, entry, src_root, commit, date):
    """Write the skill from the source. Returns the notes for the report."""
    picked, hashes, lic_hash = source_state(entry, src_root)
    try:
        source_text = read(picked["SKILL.md"]).decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("%s: the source's SKILL.md is not UTF-8" % entry["name"])
    skill_md, upstream_desc = vendored_skill_md(entry, source_text, commit)   # refuses before anything is written
    target = skill_dir(root, entry)
    links_before = links_in(target) if os.path.isdir(target) else set()
    added, changed, removed = diff_files(entry.get("files", {}), hashes)
    notes = []
    if entry.get("upstream_description_sha256") not in (None, sha256((upstream_desc or "").encode("utf-8"))):
        notes.append("The source changed its own description. Read it and see whether `description` in the "
                     "manifest still says what the skill does: %s" % quoted(upstream_desc or ""))
    if entry.get("license_sha256") not in (None, lic_hash):
        notes.append("The text of the source's %s changed (the license name did not)." % entry["license_file"])

    if os.path.isdir(target):
        shutil.rmtree(target)
    for rel, full in picked.items():
        data = skill_md.encode("utf-8") if rel == "SKILL.md" else read(full)
        write(os.path.join(target, *rel.split("/")), data)
    write(license_path(root, entry), read(os.path.join(src_root, entry["license_file"])))

    scripts = [rel for rel in added + changed if os.path.splitext(rel)[1].lower() in SCRIPT_EXT]
    if scripts:
        notes.append("Code that runs on a user's machine changed: %s" % ", ".join(scripts))
    new_links = sorted(links_in(target) - links_before)
    if new_links and links_before:
        notes.append("Links that were not in the skill before: %s" % ", ".join(quoted(u) for u in new_links))

    previous = entry.get("commit")
    entry.update(commit=commit, commit_date=date, files=dict(sorted(hashes.items())),
                 skill_md_sha256=sha256(skill_md.encode("utf-8")), license_sha256=lic_hash,
                 upstream_description_sha256=sha256((upstream_desc or "").encode("utf-8")))
    return {"name": entry["name"], "repo": entry["repo"], "previous": previous, "commit": commit, "date": date,
            "added": added, "changed": changed, "removed": removed, "notes": notes}


def report_text(results):
    out = ["# Upstream skill sync", "",
           "A skill is text that Claude follows on a user's machine. Read the diff of every file below before "
           "merging, the scripts and the links first.", ""]
    for r in results:
        out.append("## %s (%s)" % (r["name"], r["repo"]))
        if r["previous"] and r["previous"] != "local" and r["commit"] != "local":
            out.append("Source: `%s` to `%s` (%s), https://github.com/%s/compare/%s...%s"
                       % (r["previous"][:7], r["commit"][:7], r["date"], r["repo"], r["previous"], r["commit"]))
        else:
            out.append("Source: `%s` (%s)" % (r["commit"][:7], r["date"]))
        if r.get("version"):
            out.append("- version of the source: `%s`" % r["version"])
        for label in ("added", "changed", "removed"):
            if r[label]:
                out.append("- %s (%d): %s" % (label, len(r[label]), ", ".join("`%s`" % f for f in r[label][:150])
                                              + (" and %d more" % (len(r[label]) - 150) if len(r[label]) > 150 else "")))
        out += ["- note: %s" % n for n in r["notes"]]
        out.append("")
    out += ["Before a release: `bash tests/run-all.sh`, then `docs/runbooks/sync-upstream-skills.md`.", ""]
    return "\n".join(out)


def changelog_lines(result):
    count = len(result["added"]) + len(result["changed"]) + len(result["removed"])
    files = "1 file changed" if count == 1 else "%d files changed" % count
    return ("- `%s`: synced with upstream %s `%s` (%s), %s"
            % (result["name"], result["repo"], result["commit"][:7], result["date"], files),
            "- `%s`: upstream %s `%s`(%s)와 동기화, 파일 %d개 변경"
            % (result["name"], result["repo"], result["commit"][:7], result["date"], count))


def add_to_unreleased(lines, entry_line, prefix):
    """Put entry_line under `### Changed` of the first [Unreleased] section in lines (one language)."""
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## [Unreleased]"))
    except StopIteration:
        return False
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## [") or lines[i].startswith("[Unreleased]:")), len(lines))
    section = [l for l in lines[start + 1:end] if not l.startswith(prefix)]
    heads = {l[4:].strip(): i for i, l in enumerate(section) if l.startswith("### ")}
    if "Changed" in heads:
        at = heads["Changed"] + 1
        while at < len(section) and not section[at].startswith("### ") and section[at].strip():
            at += 1
        section.insert(at, entry_line)
    else:
        later = [heads[h] for h in CHANGELOG_ORDER[2:] if h in heads]
        while section and not section[-1].strip():
            section.pop()
        if later:
            section[min(later):min(later)] = ["### Changed", entry_line, ""]
        else:
            section += ["", "### Changed", entry_line]
    if section and section[0].strip():
        section.insert(0, "")
    if not section or section[-1].strip():
        section.append("")
    lines[start + 1:end] = section
    return True


def update_changelog(root, results):
    path = os.path.join(root, "CHANGELOG.md")
    if not os.path.isfile(path):
        return False
    lines = read(path).decode("utf-8").split("\n")
    marker = next((i for i, l in enumerate(lines) if l.strip() == '<a id="korean"></a>'), None)
    if marker is None:
        return False
    en, ko = lines[:marker], lines[marker:]
    ok = True
    for result in results:
        line_en, line_ko = changelog_lines(result)
        ok &= add_to_unreleased(en, line_en, "- `%s`: synced with upstream " % result["name"])
        ok &= add_to_unreleased(ko, line_ko, "- `%s`: upstream " % result["name"])
    write(path, "\n".join(en + ko).encode("utf-8"))
    return ok


# ----------------------------------------------------------------------------------------- derived skills

def matches(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) for p in patterns or [])


def no_middle_dot(text):
    """In the text of SVG <text> elements, write ', ' for ' \u00b7 ' and '/' for a bare middle dot."""
    def fix(found):
        pieces = re.split(r"(<[^>]*>)", found.group(2))
        for i in range(0, len(pieces), 2):
            pieces[i] = re.sub("[ \\t]+\u00b7[ \\t]+", ", ", pieces[i]).replace("\u00b7", "/")
        return found.group(1) + "".join(pieces) + found.group(3)
    return re.sub(r"(<text\b[^>]*>)(.*?)(</text>)", fix, text, flags=re.S | re.I)


TRANSFORMS = {"svg-text-separators": no_middle_dot}
EDIT_KINDS = (("keep",), ("find", "replace"), ("from", "to", "replace"), ("before", "insert"), ("after", "insert"))


def load_recipe(root, entry):
    """The recipe of a derived skill with its block files read in, and one hash over all of it."""
    name, rel = entry["name"], entry["recipe"]
    path = os.path.normpath(os.path.join(root, rel))
    folder = os.path.dirname(path)
    try:
        raw = read(path)
        recipe = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as err:
        raise Refused("%s: %s: %s" % (name, rel, err))
    unknown = set(recipe) - {"schema", "local", "replaced", "extra", "steps", "edits", "forbid"}
    if unknown:
        raise Refused("%s: the recipe has an unknown key: %s" % (name, ", ".join(sorted(unknown))))
    blocks = {}

    def block(file_name):
        if file_name not in blocks:
            full = os.path.normpath(os.path.join(folder, file_name))
            if not full.startswith(folder + os.sep) or os.path.islink(full) or not os.path.isfile(full):
                raise Refused("%s: the recipe names %s, which is not a file in its folder" % (name, file_name))
            blocks[file_name] = read(full).decode("utf-8")
        return blocks[file_name]

    ids = set()
    for edit in recipe.get("edits", []):
        for key in ("replace_file", "insert_file"):
            if key in edit:
                edit[key[:-5]] = block(edit.pop(key))
        eid, keys = edit.get("id"), set(edit) - {"id", "file", "count"}
        if not eid or eid in ids or not edit.get("file") or not any(keys == set(kind) for kind in EDIT_KINDS):
            raise Refused("%s: a recipe edit needs a unique `id`, a `file` and one of keep, find + replace, "
                          "from + to + replace, before + insert, after + insert (edit %r)" % (name, eid))
        ids.add(eid)
        if any("\x00" in edit[k] for k in keys) or not all(edit[k] for k in keys - {"replace", "insert"}):
            raise Refused("%s: recipe edit `%s` has an empty anchor or a NUL character" % (name, eid))
    for step in recipe.get("steps", []):
        kinds = [k for k in ("pairs", "regex", "transform") if k in step]
        if not step.get("files") or len(kinds) != 1 or (kinds == ["transform"] and step["transform"] not in TRANSFORMS):
            raise Refused("%s: a recipe step needs `files` and one of pairs, regex, transform" % name)
    for rule in recipe.get("forbid", []):
        if not rule.get("files") or not rule.get("tokens"):
            raise Refused("%s: a recipe `forbid` rule needs `files` and `tokens`" % name)
    for item in recipe.get("extra", []):
        to = item.get("to", "")
        if not item.get("from") or not SAFE_PATH.fullmatch(to) or to.startswith(("/", ".", "skills/")) or ".." in to.split("/"):
            raise Refused("%s: a recipe `extra` file needs `from` and a plain `to` path outside skills/" % name)
    if not set(recipe.get("replaced", [])) <= set(recipe.get("local", [])):
        raise Refused("%s: every `replaced` file of the recipe is also listed in `local`" % name)
    digest = hashlib.sha256(raw)
    for file_name in sorted(blocks):
        digest.update(b"\0" + file_name.encode("utf-8") + b"\0" + blocks[file_name].encode("utf-8"))
    recipe["_sha256"] = digest.hexdigest()
    return recipe


def run_step(name, step, text):
    if "pairs" in step:
        flags = re.I if step.get("ignore_case") else 0
        for old, new in step["pairs"]:
            text = re.sub(re.escape(old), lambda _found, new=new: new, text, flags=flags)
        return text
    if "regex" in step:
        for pattern, repl in step["regex"]:
            try:
                text = re.sub(pattern, repl, text, flags=re.M)
            except re.error as err:
                raise Refused("%s: recipe regex %r: %s" % (name, pattern, err))
        return text
    return TRANSFORMS[step["transform"]](text)


def derive_text(name, key, text, recipe):
    """One file of the source rewritten by the recipe. Returns (text, {edit id: hash of a replaced span}).

    Edits anchor on the source's own text. What an edit puts in stands apart as a mark while the steps and
    the forbid rules run, so they see the source's text only and never the edition's blocks.
    """
    if "\x00" in text:
        raise Refused("%s: %s holds a NUL character" % (name, key))
    held, spans = [], {}

    def hold(final):
        held.append(final)
        return "\x00%d\x00" % (len(held) - 1)

    for edit in recipe.get("edits", []):
        if edit["file"] != key:
            continue
        for anchor_key in ("keep", "find", "from", "to", "before", "after"):
            if anchor_key in edit:
                want = edit.get("count", 1) if anchor_key in ("keep", "find") else 1
                have = text.count(edit[anchor_key])
                if have != want:
                    raise Refused("%s: recipe edit `%s` no longer applies to %s: its `%s` text occurs %d time(s), "
                                  "not %d: %s" % (name, edit["id"], key, anchor_key, have, want, quoted(edit[anchor_key], 160)))
        if "keep" in edit:
            text = text.replace(edit["keep"], hold(edit["keep"]))
        elif "find" in edit:
            text = text.replace(edit["find"], hold(edit["replace"]))
        elif "from" in edit:
            start, end = text.index(edit["from"]), text.index(edit["to"])
            if start >= end:
                raise Refused("%s: recipe edit `%s`: `from` comes after `to` in %s" % (name, edit["id"], key))
            spans[edit["id"]] = sha256(text[start:end].encode("utf-8"))
            text = text[:start] + hold(edit["replace"]) + text[end:]
        elif "before" in edit:
            text = text.replace(edit["before"], hold(edit["insert"]) + edit["before"])
        else:
            text = text.replace(edit["after"], edit["after"] + hold(edit["insert"]))

    parts = MARK.split(text)
    for step in recipe.get("steps", []):
        if matches(key, step["files"]) and not matches(key, step.get("except")):
            for i in range(0, len(parts), 2):
                parts[i] = run_step(name, step, parts[i])
                if "\x00" in parts[i]:
                    raise Refused("%s: a recipe step wrote a NUL character into %s" % (name, key))
    for rule in recipe.get("forbid", []):
        if not matches(key, rule["files"]) or matches(key, rule.get("except")):
            continue
        for token in rule["tokens"]:
            for i in range(0, len(parts), 2):
                found = re.search(re.escape(token), parts[i], re.I if rule.get("ignore_case") else 0)
                if found:
                    line = parts[i][:found.start()].rsplit("\n", 1)[-1] + parts[i][found.start():].split("\n", 1)[0]
                    raise Refused("%s: `%s` survives in %s: %s. Add a replacement to the recipe, or `keep` the text "
                                  "when it belongs there" % (name, token, key, quoted(line.strip(), 200)))
    return "".join(held[int(p[1:-1])] if i % 2 else p for i, p in enumerate(parts)), spans


def extra_sources(entry, recipe, src_root):
    """{path in this repository: bytes of the source} for the files the recipe takes from outside the skill folder."""
    found = {}
    top = os.path.realpath(src_root)
    for item in recipe.get("extra", []):
        full = os.path.join(src_root, *item["from"].split("/"))
        if (os.path.islink(full) or not os.path.isfile(full)
                or not os.path.realpath(full).startswith(top + os.sep)):
            raise Refused("%s: the source has no file %s, which the recipe takes" % (entry["name"], item["from"]))
        if os.path.splitext(full)[1].lower() not in TEXT_EXT or os.path.getsize(full) > MAX_FILE_BYTES:
            raise Refused("%s: %s is not a .md or .html file under the size limit" % (entry["name"], item["from"]))
        found[item["to"]] = read(full)
    return found


def upstream_version(src_root):
    try:
        version = json.loads(read(os.path.join(src_root, ".claude-plugin", "plugin.json")).decode("utf-8")).get("version")
    except (OSError, ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and re.fullmatch(r"[0-9A-Za-z.+-]{1,40}", version) else None


def derive(root, entry, src_root):
    """Everything `update` writes for a derived skill, built in memory: nothing is written when it refuses."""
    name = entry["name"]
    recipe = load_recipe(root, entry)
    picked, hashes, lic_hash = source_state(entry, src_root)
    extra_raw = extra_sources(entry, recipe, src_root)
    replaced = set(recipe.get("replaced", []))
    for rel in sorted(replaced - set(picked)):
        raise Refused("%s: the source no longer has %s, which the recipe replaces" % (name, rel))
    for rel in sorted(picked):
        if rel not in replaced and matches(rel, recipe.get("local")):
            raise Refused("%s: the source now has %s, which the recipe lists as a file of the edition" % (name, rel))
    keys = (set(picked) - replaced) | {EXTRA + to for to in extra_raw}
    for edit in recipe.get("edits", []):
        if edit["file"] not in keys:
            raise Refused("%s: recipe edit `%s` names %s, which is not a file taken from the source" % (name, edit["id"], edit["file"]))
        if os.path.splitext(edit["file"])[1].lower() not in TEXT_EXT:
            raise Refused("%s: recipe edit `%s`: a recipe changes .md and .html files only" % (name, edit["id"]))

    def rewrite(key, raw):
        try:
            return derive_text(name, key, raw.decode("utf-8"), recipe)
        except UnicodeDecodeError:
            raise Refused("%s: %s is not UTF-8" % (name, key))

    out, extras, spans = {}, {}, {}
    for rel, full in picked.items():
        if rel in replaced:
            continue
        data = read(full)
        if os.path.splitext(rel)[1].lower() in TEXT_EXT:
            text, found = rewrite(rel, data)
            spans.update(found)
            data = text.encode("utf-8")
        out[rel] = data
    for to, raw in extra_raw.items():
        text, found = rewrite(EXTRA + to, raw)
        spans.update(found)
        extras[to] = text.encode("utf-8")
    return {"recipe": recipe, "picked": picked, "hashes": hashes, "license": lic_hash, "out": out, "spans": spans,
            "extras": extras, "extra_hashes": {to: sha256(raw) for to, raw in extra_raw.items()}}


def edition_files(root, entry, recipe):
    """{relative path: absolute path} of the files in the skill folder that belong to the edition, not the source."""
    target, kept = skill_dir(root, entry), {}
    for base, _dirs, files in os.walk(target):
        for fname in files:
            full = os.path.join(base, fname)
            rel = os.path.relpath(full, target).replace(os.sep, "/")
            if matches(rel, recipe.get("local")):
                if os.path.islink(full):
                    raise Refused("%s: %s is a symbolic link" % (entry["name"], rel))
                kept[rel] = full
    for pattern in recipe.get("local", []):
        if not any(fnmatch.fnmatch(rel, pattern) for rel in kept):
            raise Refused("%s: nothing in skills/%s matches `%s`, which the recipe lists as a file of the edition"
                          % (entry["name"], entry["name"], pattern))
    return kept


def apply_derived(root, entry, src_root, commit, date):
    """Rebuild a derived skill from the source by its recipe. Returns the notes for the report."""
    name = entry["name"]
    built = derive(root, entry, src_root)                      # refuses before anything is written
    recipe, hashes, out = built["recipe"], built["hashes"], built["out"]
    try:
        source_fm, _body = split_frontmatter(read(built["picked"]["SKILL.md"]).decode("utf-8"), name)
    except UnicodeDecodeError:
        raise Refused("%s: the source's SKILL.md is not UTF-8" % name)
    upstream_desc = field(source_fm, "description")
    skill_md, _desc = vendored_skill_md(entry, out["SKILL.md"].decode("utf-8"), commit)
    out["SKILL.md"] = skill_md.encode("utf-8")
    target = skill_dir(root, entry)
    kept = edition_files(root, entry, recipe)
    if not os.path.isfile(license_path(root, entry)):
        raise Refused("%s: third_party/LICENSE-%s is missing; a derived skill keeps its own license file" % (name, name))
    links_before = links_in(target)
    added, changed, removed = diff_files(entry.get("files", {}), hashes)
    more = diff_files(entry.get("extra_files", {}), built["extra_hashes"])
    added, changed, removed = added + more[0], changed + more[1], removed + more[2]
    notes = []
    version = upstream_version(src_root)
    if entry.get("upstream_description_sha256") not in (None, sha256((upstream_desc or "").encode("utf-8"))):
        notes.append("The source changed its own description. Read it and see whether `description` in the "
                     "manifest still says what the skill does: %s" % quoted(upstream_desc or ""))
    if entry.get("license_sha256") not in (None, built["license"]):
        notes.append("The text of the source's %s changed. third_party/LICENSE-%s is the edition's own file; "
                     "bring it in line by hand." % (entry["license_file"], name))
    for rel in sorted(recipe.get("replaced", [])):
        if entry.get("files", {}).get(rel) not in (None, hashes[rel]):
            notes.append("The source changed %s, which the edition replaces with its own file. Read the source's "
                         "diff of that file and port what applies by hand." % rel)
    for eid, digest in sorted(built["spans"].items()):
        if entry.get("spans", {}).get(eid) not in (None, digest):
            notes.append("The source changed the text that recipe edit `%s` replaces. Compare it with the block "
                         "the recipe puts there." % eid)

    fresh, old = target + ".new", target + ".old"
    for folder in (fresh, old):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    for rel, full in kept.items():
        dest = os.path.join(fresh, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(full, dest)
    for rel, data in out.items():
        write(os.path.join(fresh, *rel.split("/")), data)
    os.rename(target, old)
    os.rename(fresh, target)
    shutil.rmtree(old)
    for to, data in built["extras"].items():
        write(os.path.join(root, *to.split("/")), data)
    for to in set(entry.get("extra_files", {})) - set(built["extras"]):
        gone = os.path.join(root, *to.split("/"))
        if os.path.isfile(gone):
            os.remove(gone)

    scripts = [rel for rel in added + changed if os.path.splitext(rel)[1].lower() in SCRIPT_EXT]
    if scripts:
        notes.append("Code that runs on a user's machine changed: %s" % ", ".join(scripts))
    new_links = sorted(links_in(target) - links_before)
    if new_links and entry.get("commit"):
        notes.append("Links that were not in the skill before: %s" % ", ".join(quoted(u) for u in new_links[:40]))
    previous = entry.get("commit")
    entry.update(commit=commit, commit_date=date, files=dict(sorted(hashes.items())),
                 written={rel: sha256(data) for rel, data in sorted(out.items())
                          if rel != "SKILL.md" and sha256(data) != hashes[rel]},
                 extra_files=dict(sorted(built["extra_hashes"].items())),
                 extra_written={to: sha256(data) for to, data in sorted(built["extras"].items())},
                 spans=dict(sorted(built["spans"].items())), recipe_sha256=recipe["_sha256"],
                 skill_md_sha256=sha256(out["SKILL.md"]), license_sha256=built["license"],
                 upstream_description_sha256=sha256((upstream_desc or "").encode("utf-8")))
    if version:
        entry["upstream_version"] = version
    return {"name": name, "repo": entry["repo"], "previous": previous, "commit": commit, "date": date,
            "added": added, "changed": changed, "removed": removed, "notes": notes, "version": version}


def verify_derived(root, entry):
    """Problems of one derived skill: a file of the source that differs from what `update` wrote, a file that is
    neither the source's nor the edition's, a missing file of the edition, a recipe changed after the last update."""
    name, target, problems = entry["name"], skill_dir(root, entry), []
    recorded, written = entry.get("files"), entry.get("written", {})
    if not recorded or not entry.get("commit"):
        return ["%s: not derived yet (no commit or files in the manifest)" % name]
    if not os.path.isdir(target):
        return ["%s: skills/%s is missing" % (name, name)]
    try:
        recipe = load_recipe(root, entry)
    except Refused as err:
        return [str(err)]
    if recipe["_sha256"] != entry.get("recipe_sha256"):
        problems.append("%s: the recipe changed after the last update; run `update --skill %s --pinned`" % (name, name))
    replaced, local = set(recipe.get("replaced", [])), recipe.get("local", [])
    present = {}
    for base, _dirs, files in os.walk(target):
        for fname in files:
            full = os.path.join(base, fname)
            present[os.path.relpath(full, target).replace(os.sep, "/")] = full
    ours = {rel for rel in present if matches(rel, local)}
    theirs = set(recorded) - replaced
    for rel in sorted(set(present) - theirs - ours):
        problems.append("%s: %s is neither a file of the source nor listed in the recipe's `local`" % (name, rel))
    for rel in sorted(theirs - set(present)):
        problems.append("%s: %s is missing" % (name, rel))
    for pattern in local:
        if not any(fnmatch.fnmatch(rel, pattern) for rel in ours):
            problems.append("%s: no file matches `%s`, which the recipe lists as a file of the edition" % (name, pattern))
    for rel in sorted(present):
        if os.path.islink(present[rel]):
            problems.append("%s: %s is a symbolic link" % (name, rel))
    for rel in sorted(theirs & set(present)):
        if rel != "SKILL.md" and sha256(read(present[rel])) != written.get(rel, recorded[rel]):
            problems.append("%s: %s differs from what `update` wrote; a file of the source is changed by the recipe only"
                            % (name, rel))
        if os.path.splitext(rel)[1].lower() not in entry["allow_ext"]:
            problems.append("%s: %s has a file type the manifest does not allow" % (name, rel))
    for to, digest in sorted(entry.get("extra_written", {}).items()):
        full = os.path.join(root, *to.split("/"))
        if not os.path.isfile(full) or os.path.islink(full):
            problems.append("%s: %s is missing" % (name, to))
        elif sha256(read(full)) != digest:
            problems.append("%s: %s differs from what `update` wrote; change the recipe, not the file" % (name, to))
    problems += frontmatter_problems(entry, present)
    if not os.path.isfile(license_path(root, entry)):
        problems.append("%s: third_party/LICENSE-%s is missing" % (name, name))
    return problems


# ---------------------------------------------------------------------------------------------- commands

def chosen(data, args):
    picked = [e for e in data["skills"] if not args.skill or e["name"] == args.skill]
    if not picked:
        raise Refused("no skill named %s in the manifest" % args.skill)
    if getattr(args, "schedule", None):
        picked = [e for e in picked if e.get("schedule", "weekly") == args.schedule]
    if args.source and len(picked) != 1:
        raise Refused("--source needs --skill")
    return picked


def cmd_check(root, args):
    data = load_manifest(root)
    updates = 0
    with tempfile.TemporaryDirectory(prefix="upstream-skills.") as tmp:
        for entry in chosen(data, args):
            if not args.source and entry.get("commit") == remote_head(entry):
                print("OK %s: up to date with %s (%s)" % (entry["name"], entry["repo"], entry["commit"][:7]))
                continue
            src, commit, date = fetch(entry, args, tmp)
            _picked, hashes, lic_hash = source_state(entry, src)
            added, changed, removed = diff_files(entry.get("files", {}), hashes)
            if is_derived(entry):
                extra_now = {to: sha256(raw) for to, raw in extra_sources(entry, load_recipe(root, entry), src).items()}
                more = diff_files(entry.get("extra_files", {}), extra_now)
                added, changed, removed = added + more[0], changed + more[1], removed + more[2]
            if not (added or changed or removed) and lic_hash == entry.get("license_sha256"):
                print("OK %s: %s moved to %s, the skill's files are the same" % (entry["name"], entry["repo"], commit[:7]))
                continue
            updates += 1
            print("UPDATE %s: %s %s to %s (%s)" % (entry["name"], entry["repo"],
                                                    (entry.get("commit") or "none")[:7], commit[:7], date))
            for label, items in (("added", added), ("changed", changed), ("removed", removed)):
                if items:
                    print("  %s: %s" % (label, ", ".join(items)))
            if lic_hash != entry.get("license_sha256"):
                print("  the text of %s changed" % entry["license_file"])
            if is_derived(entry):
                try:
                    derive(root, entry, src)
                    print("  the recipe applies to the new source")
                except Refused as err:
                    print("  RECIPE %s" % err)
    return 10 if updates else 0


def cmd_update(root, args):
    data = load_manifest(root)
    results, failed = [], 0
    with tempfile.TemporaryDirectory(prefix="upstream-skills.") as tmp:
        for entry in chosen(data, args):
            try:
                src, commit, date = fetch(entry, args, tmp)
                _picked, hashes, lic_hash = source_state(entry, src)
                same = (hashes == entry.get("files") and lic_hash == entry.get("license_sha256")
                        and not verify_entry(root, entry))
                if same and is_derived(entry):
                    recipe = load_recipe(root, entry)
                    same = (recipe["_sha256"] == entry.get("recipe_sha256") and entry.get("extra_files", {})
                            == {to: sha256(raw) for to, raw in extra_sources(entry, recipe, src).items()})
                if same and not args.force:
                    print("OK %s: nothing to update (%s)" % (entry["name"], (entry.get("commit") or "")[:7]))
                    continue
                result = (apply_derived if is_derived(entry) else apply)(root, entry, src, commit, date)
            except Refused as err:
                failed += 1
                print("REFUSED %s" % err, file=sys.stderr)
                continue
            results.append(result)
            print("UPDATED %s: %s %s, %d added, %d changed, %d removed"
                  % (entry["name"], entry["repo"], commit[:7], len(result["added"]), len(result["changed"]),
                     len(result["removed"])))
            for note in result["notes"]:
                print("  NOTE %s" % note)
    if results:
        save_manifest(root, data)
        if not args.no_changelog and not update_changelog(root, results):
            print("WARN CHANGELOG.md has no [Unreleased] section in both languages; add the entries by hand")
    if args.report and (results or failed):
        write(args.report, report_text(results).encode("utf-8"))
    return 1 if failed else 0


def cmd_render(root, args):
    data = load_manifest(root)
    for entry in chosen(data, args):
        path = os.path.join(skill_dir(root, entry), "SKILL.md")
        if not os.path.isfile(path):
            raise Refused("%s: not vendored yet; run `update`" % entry["name"])
        fm, body = split_frontmatter(read(path).decode("utf-8"), entry["name"])
        out = []
        for key, lines in entries(fm):
            if key == "name":
                out.append("name: %s" % entry["name"])
            elif key == "description":
                out.append("description: %s" % yaml_scalar(entry["description"]))
            else:
                out += lines
        text = "\n".join(["---"] + out + ["---", body]).encode("utf-8")
        write(path, text)
        entry["skill_md_sha256"] = sha256(text)
        print("RENDERED %s" % entry["name"])
    save_manifest(root, data)
    return 0


def frontmatter_problems(entry, present):
    """Problems of the SKILL.md that `update` or `render` wrote: its hash and the frontmatter the manifest gives it."""
    name, problems = entry["name"], []
    if "SKILL.md" not in present:
        return problems
    data = read(present["SKILL.md"])
    if sha256(data) != entry.get("skill_md_sha256"):
        problems.append("%s: SKILL.md differs from what `update` or `render` wrote" % name)
    try:
        fm, _body = split_frontmatter(data.decode("utf-8"), name)
    except (Refused, UnicodeDecodeError) as err:
        return problems + ["%s: %s" % (name, err)]
    for key, want in (("name", name), ("description", entry["description"]), ("license", entry["license"])):
        if field(fm, key) != want:
            problems.append("%s: SKILL.md `%s` is not the manifest's; run `render`" % (name, key))
    meta = "\n".join(fm)
    for want in ("upstream: %s" % source_url(entry), "upstream-commit: %s" % entry["commit"]):
        if not re.search(r"^\s+%s$" % re.escape(want), meta, re.M):
            problems.append("%s: SKILL.md metadata has no `%s`" % (name, want))
    return problems


def verify_entry(root, entry):
    """Problems of one vendored skill, an empty list when it is what the manifest records."""
    if is_derived(entry):
        return verify_derived(root, entry)
    name, target, problems = entry["name"], skill_dir(root, entry), []
    recorded = entry.get("files")
    if not recorded or not entry.get("commit"):
        return ["%s: not vendored yet (no commit or files in the manifest)" % name]
    if not os.path.isdir(target):
        return ["%s: skills/%s is missing" % (name, name)]
    present = {}
    for base, _dirs, files in os.walk(target):
        for fname in files:
            full = os.path.join(base, fname)
            present[os.path.relpath(full, target).replace(os.sep, "/")] = full
    for rel in sorted(set(present) - set(recorded)):
        problems.append("%s: %s is not a file of the source" % (name, rel))
    for rel in sorted(set(recorded) - set(present)):
        problems.append("%s: %s is missing" % (name, rel))
    for rel in sorted(set(recorded) & set(present)):
        if os.path.islink(present[rel]):
            problems.append("%s: %s is a symbolic link" % (name, rel))
        elif rel != "SKILL.md" and sha256(read(present[rel])) != recorded[rel]:
            problems.append("%s: %s differs from the source; a vendored file is changed by `update` only" % (name, rel))
        if os.path.splitext(rel)[1].lower() not in entry["allow_ext"]:
            problems.append("%s: %s has a file type the manifest does not allow" % (name, rel))
    problems += frontmatter_problems(entry, present)
    lic = license_path(root, entry)
    if not os.path.isfile(lic):
        problems.append("%s: third_party/LICENSE-%s is missing" % (name, name))
    elif sha256(read(lic)) != entry.get("license_sha256"):
        problems.append("%s: third_party/LICENSE-%s differs from the source's license" % (name, name))
    return problems


def cmd_verify(root, args):
    data = load_manifest(root)
    bad = 0
    for entry in chosen(data, args):
        problems = verify_entry(root, entry)
        bad += len(problems)
        for problem in problems:
            print("FAIL %s" % problem)
        if not problems:
            print("OK %s: %d files, %s %s" % (entry["name"], len(entry["files"]), entry["repo"], entry["commit"][:7]))
    listed = {e["name"] for e in data["skills"]}
    for name in sorted(listed):
        if not args.skill and not os.path.isdir(os.path.join(root, "skills", name)):
            bad += 1
            print("FAIL %s: in the manifest, not under skills/" % name)
    return 1 if bad else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["check", "update", "render", "verify"])
    parser.add_argument("--skill", help="one skill of the manifest (default: all)")
    parser.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
                        help="repository root (default: the folder above this script)")
    parser.add_argument("--source", help="a local checkout of the source in place of a download (needs --skill)")
    parser.add_argument("--commit", help="commit id to record for --source when it is not a git checkout")
    parser.add_argument("--date", help="commit date (YYYY-MM-DD) to record for --source")
    parser.add_argument("--force", action="store_true", help="update: write the skill even when nothing changed")
    parser.add_argument("--pinned", action="store_true",
                        help="check, update: take the source at the commit the manifest records (after a recipe change)")
    parser.add_argument("--schedule", choices=SCHEDULES,
                        help="only the skills with this `schedule` in the manifest (default weekly)")
    parser.add_argument("--no-changelog", action="store_true", help="update: leave CHANGELOG.md alone")
    parser.add_argument("--report", help="update: write a Markdown report of what changed to this file")
    args = parser.parse_args(argv)
    root = os.path.normpath(args.root)
    try:
        return {"check": cmd_check, "update": cmd_update, "render": cmd_render, "verify": cmd_verify}[args.command](root, args)
    except Refused as err:
        print("REFUSED %s" % err, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

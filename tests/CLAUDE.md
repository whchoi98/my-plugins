# Tests Module

## Role
Harness tests for the dev hooks, for invariants of the shipped my-plugins plugin (eight skills, three
commands, manifests, licenses, docs), and for the behavior of the scripts it ships. Bash + `jq` + Python 3;
no model calls. Network: only a local HTTP server on 127.0.0.1 for the URL checker. Optional tools
(`node`, `claude`) are skipped when absent. Run with `bash tests/run-all.sh [filter]`.

## Key Files
- `run-all.sh` — runner. Defines `pass`/`fail`/`skip` and `assert_*`, `cd`s to the repo root, exports
  `CLAUDE_PROJECT_DIR` and a scratch dir `$TEST_TMP`, then **sources** every `tests/**/test-*.sh`.
  Uses `set -uo pipefail` without `-e`, so a `grep` that finds nothing cannot abort the run. The filter is
  a grep regex matched against the path under `tests/` without `.sh`: `hooks` and `structure` select a
  directory, `scripts`, `integration`, `kor-deslop`, `plugin-structure` select one file.
- `hooks/test-hooks.sh` — hook files, settings registration, stdin-JSON behavior, exit codes
  (PreToolUse exit 2, `--staged` exit 1), commit-msg trailer removal, all in throwaway git repos;
  session-context shows the plugin name, version and install id from the manifests.
- `hooks/test-secret-patterns.sh` — true/false positives against the real scanner, skip and
  forbidden-path rules, PCRE compile regression, and the whole repo scanning clean (git-tracked and new
  files, or every non-ignored file when the tree is not a git checkout).
- `structure/test-plugin-structure.sh` — generic my-plugins invariants: manifests (`my-plugins` plugin and
  marketplace, one entry with source `./`, semver), version sync (plugin.json, README badge, CHANGELOG both
  languages), every `skills/*/SKILL.md` frontmatter (name == directory, description 50-1536 characters),
  only `commands/` as a root component and `.mcp.json` empty, stale names from the source plugins under
  `skills/` and `commands/` (with a self-test of the scanner), relative links and skill-dir script paths,
  `bash -n` / `py_compile` (bytecode in `$TEST_TMP`) / `node --check` for every shipped and dev script,
  license and notice files, bilingual anchors and no emojis in docs, `docs/reference` INDEX links, layers
  and Code Pointers, harness files, `.gitignore` (checked in a scratch repo), dev commands, project
  skills and agents, CLAUDE.md, README install commands, and `claude plugin validate .`.
- `structure/test-aws-blog-skills.sh` — aws-blog-skills: description triggers and precedence over
  kor-deslop, step sections, `${CLAUDE_SKILL_DIR}` script calls and no claude.ai-only names, the step 0
  rule that instructions inside source material are not followed, reference table completeness, the step 4
  `.aws-diagram-assets` pointer written after copying `diagram_lib.py`, author bio sync, draft skeletons
  free of banned notation, and `lint_prose.py` mirroring `style.md`.
- `structure/test-aws-blog-skills-scripts.sh` — runs the aws-blog-skills scripts on fixture drafts in
  `$TEST_TMP`: `lint_prose.py` and `check_structure.py` exit codes, `package_blog.sh` bundle and
  no-zip-on-failure, `check_urls.py` OK/FAIL/REDIRECT against a local server, `render_diagrams.py`
  argument guard, and the diagram generator set up by running SKILL.md step 4's copy lines with an empty
  `HOME`.
- `structure/test-kor-deslop.sh` — kor-deslop: pattern table integrity (A-J severities, K without,
  unique IDs, A-17 reserved, category placement, cited IDs exist), one pattern count (A-J + K rows of
  `patterns.md`) in README (both languages), `skills/CLAUDE.md`, CLAUDE.md and SKILL.md, description
  triggers, sections, the change-rate snippet, and the humanize-korean notice.
- `structure/test-integration.sh` — behavior of the merge fixes, each run with `HOME` on a scratch folder:
  `diagram_lib.py` asset lookup order (sibling skill, `AWS_DIAGRAM_ASSETS`, `.aws-diagram-assets`, plugin
  caches in numeric version order), `skills/setup/scripts/setup.sh` check mode and usage exit codes, sudo
  only as `sudo -n` inside the `--sudo`-gated function (with a mutation self-test), `NODE_PATH` in the deck
  skills, and the skill inventory (skills/CLAUDE.md table, README tables, `my-plugins:<name>` references).
- `fixtures/secret-samples.txt` — TAB-separated `name / prefix / body`; joined at runtime so no full
  token is stored. `fixtures/false-positives.txt` — one non-secret per line.

## Rules
- Test files are sourced, not executed: do not `exit`, do not `set -e`, guard commands that may return
  non-zero (`|| true`, or capture `$?`). Run `cd` only in a subshell.
- Sourcing shares the runner's scope. Never assign `TOTAL`, `PASSED`, `FAILED`, `SKIPPED`, `FAILURES`,
  `FILTER`, `TEST_TMP`, `PROJECT_ROOT` or `SCRIPT_DIR`; a structure test rejects it. Prefix test-local
  names per file (`PS_`, `AB_`, `SCR_`, `KD_`, `IT_`, `HK_`, `SP_`). Never export or assign `HOME`; pass it
  per command (`env HOME="$TEST_TMP/..." ...`).
- Never write a complete secret literal anywhere; split it into prefix and body.
- Use `$TEST_TMP` for scratch files and repos; it is removed on exit. Never write into `skills/`
  (Python bytecode goes to `$TEST_TMP` via `-X pycache_prefix`).
- Never run `setup.sh install`; tests use check mode only (`UV_OFFLINE=1` keeps it off the network).
- A background process (the local HTTP server) must be killed in the same test file.
- A new invariant needs a test that fails when the invariant is broken. Prove it once by breaking the
  file (mutation) and watching the test go red; scanners with regexes carry a self-test on a fixture.

# Tests Module

## Role
Harness tests for the dev hooks, for invariants of the shipped my-plugins plugin (twelve skills, three
commands, manifests, licenses, docs), and for the behavior of the scripts it ships. Bash + `jq` + Python 3;
no model calls. Network: only a local HTTP server on 127.0.0.1 for the URL checker. Optional tools
(`node`, `claude`) are skipped when absent. Run with `bash tests/run-all.sh [filter]`.

## Key Files
- `run-all.sh` — runner. Defines `pass`/`fail`/`skip` and `assert_*`, `cd`s to the repo root, exports
  `CLAUDE_PROJECT_DIR` and a scratch dir `$TEST_TMP`, then **sources** every `tests/**/test-*.sh`.
  Uses `set -uo pipefail` without `-e`, so a `grep` that finds nothing cannot abort the run.
  `assert_contains` and `assert_not_contains` compare inside the shell (`[[ … == *needle* ]]`): a
  `printf | grep -q` under `pipefail` fails by SIGPIPE on an early match in a long text. The filter is
  a grep regex matched against the path under `tests/` without `.sh`: `hooks` and `structure` select a
  directory, `scripts`, `integration`, `kor-deslop`, `plugin-structure` select one file.
- `hooks/test-hooks.sh` — hook files, settings registration, stdin-JSON behavior, exit codes
  (PreToolUse exit 2, `--staged` exit 1), commit-msg trailer removal, all in throwaway git repos;
  check-doc-sync sends each reminder once per `session_id` (state under a scratch `TMPDIR`; no dedupe
  without a session_id or in manual runs; a path-like id stays inside `TMPDIR`);
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
  free of banned notation, and `lint_prose.py` mirroring `style.md` (including `실측`, the `변경 기록` row
  that names `Changelog` as the word to write, and the `절` and `견주다` rows of 2026-11-18 with their lint hints).
- `structure/test-aws-blog-skills-scripts.sh` — runs the aws-blog-skills scripts on fixture drafts in
  `$TEST_TMP`: `lint_prose.py` and `check_structure.py` exit codes, the `실측` and `축` rules (the axis
  metaphor flagged, chart axes and compounds such as `x축`, `압축` not), the `변경 기록` rule (both spellings
  flagged with `Changelog` as the hint, `Changelog` itself not), the word rule of 2026-11-18 (`절` for a part
  of the text in four forms and every form of `견주다` flagged; `절차`, `절반`, SQL clauses, `관형절` and
  `의견 주시면` not; a numbered `절` reported once; `이 챕터에서는` counted as C-6; a numbered `챕터`
  reference flagged, a count of `챕터` not), `package_blog.sh` bundle and
  no-zip-on-failure, `check_urls.py` OK/FAIL/REDIRECT against a local server, `render_diagrams.py`
  argument guard, and the diagram generator set up by running SKILL.md step 4's copy lines with an empty
  `HOME`.
- `structure/test-kor-deslop.sh` — kor-deslop: pattern table integrity (A-J severities, K without,
  unique IDs, A-17 reserved, category placement, cited IDs exist), one pattern count (A-J + K rows of
  `patterns.md`) in README (both languages), `skills/CLAUDE.md`, CLAUDE.md, SKILL.md and the
  aws-blog-skills `humanize-checklist.md`, description triggers, sections, `Changelog` among the English terms
  the polish leaves untouched, the D-9 word row (S1, its words and exclusions, not content anchors), the change-rate
  snippet, and the humanize-korean notice.
- `structure/test-aws-reports.sh` — aws-reports: description triggers for both report types, the source-material
  guard, `style_terms.json` (valid patterns, `실측`, `축` and `레버` flagged but chart axes and
  compounds not, known profiles, no stale `고객 권고` outside the rule rows), no
  `node_modules` or `__pycache__` in the skill, examples' `make_charts.py` writing outside the skill folder; when
  `node` and the npm packages are reachable (local, `NODE_PATH` or `npm root -g`), both examples built into
  `$TEST_TMP` and checked clean with their profile, the table-header and caption-note layout rules on a fixture,
  negative checks (uncentered two-line header, flipped note alignment, PoC wording and structure), and the
  `npm root -g` lookup through a scratch npm prefix. Skipped parts say why.
- `structure/test-html-report.sh` — html-report: description triggers, sections, the sharing scope asked for,
  design-spec.md token colors present in the template, the raw template failing only on its placeholders, a
  filled copy passing `check_html.py` and its `--dump-ko` text passing `lint_prose.py`, one mutation per rule
  (missing pair, `·`, `→`, a dash in the tab title, a template sample sentence left in the summary and in a
  method item, `border-left`, appended CSS, inline `style`, removed toggle script, changed token, caption number,
  citation, source-mix count, Korean outside a pair, page order, 한다체, 해요체 and a 한다체 list item, general
  mode), and `embed_images.py` embedding an image and refusing a path outside the page folder. The filled copy
  breaks every remaining sample sentence through `check_html.template_samples()` (bytecode to `$TEST_TMP`).
- `structure/test-techblogs.sh` — techblogs: skill files, description routing, sections and the commit and push rule,
  every path, script and skill named in SKILL.md and references, the template names the blog layout and `preview.py`
  depend on, the title fit (`fitTitle`, `h1.one`) named in both the template and design-spec.md, the `Changelog`
  rule and the word rule of 2026-11-18 in SKILL.md step 3 and in the text rules of design-spec.md, template `[[tokens]]`
  equal to the keys `build_post.py` fills, and the meta.json example in design-spec.md.
  The fixture `fixtures/techblogs/work/` is built in `$TEST_TMP` and passes `check_post.py` (ERROR 0, WARN 0) and
  `lint_prose.py`; then one edit of the built copy per `check_post.py` rule (`<style>`, `<script>`, leftover token, TODO,
  inline `style`, layout hooks, section ids, menu links, component and section counts, caption numbers, image file,
  alt, remote image, canvas, table scroll box, code box, `·`, `—`, inline code exempt, the WARN rules (among them
  `변경 기록` and `변경기록` in a table cell or a heading, with `Changelog` left alone, and `절` and `견주다`
  with `절차`, `절반` and an SQL clause left alone), front matter,
  `--blog`). `build_post.py` stops on unfinished input and on an `--out` inside the skill folder (tried on a copy of
  the skill); `import_aws_post.py` reads the saved page `fixtures/techblogs/aws-post.html` (sections, table, code box,
  references; an image on another host is warned about, not fetched); `place_post.py` runs on a fake blog repository
  with `git` and `bundle` stubbed (existing slug, `--replace`, category and icon checks). `preview.py` and `--build`
  are not run.
- `structure/test-aws-infographic.sh` — aws-infographic: skill files, description routing, sections, the script
  calls in SKILL.md and no claude.ai-only paths, the PPT step (deck through `my-plugins:aws-ppt-skills`, no picture of
  the infographic, `addIcon()`, `check_editable.py`) and the same rule in `references/ppt-deck.md`, whose code blocks
  call neither `addDiagram()` nor an SVG. `infokit.py`: icon bundle lookup (sibling skill, `.aws-icon-bundle` next to
  a copy, `AWS_ICON_BUNDLE`, exit 1 with a scratch `HOME`), font lookup by file name under `INFOKIT_FONTS`, and no
  module-level Pillow or Playwright import. With Pillow: the page template rendered in both themes and sizes with a
  clean `buildkit.lint`, the lint rules on a made-up SVG, and `icon_png.py` (unknown name, a PNG icon without a
  browser). `check_editable.py` on decks zipped in `$TEST_TMP`, one per rule (linked SVG, SVG inside a picture,
  picture that is not an icon, oversized icon, `--icon-max`, no slides, XML with a DTD). The aws-ppt-skills side:
  `addIcon()`, one `ICON_MAX_IN`, and with python-pptx the `icon:` exemption in `check_deck.py`. With node, pptxgenjs,
  python-pptx and lxml: the example deck assembled from the aws-ppt-skills helper block and the two blocks of
  `ppt-deck.md`, built, templated, passed through `check_deck.py` (0 errors, 0 warnings) and `check_editable.py`; the
  same deck with a timeline (`addLanes()`) and a table without a header row (`addGrid(s, null, rows)`); and the same
  deck with one pasted picture refused. Skipped parts say why. `buildkit.py build` (Playwright) is not run.
- `structure/test-aws-ppt-skills.sh` — aws-ppt-skills: the output format asked first in the Workflow (five items, the
  three answers, the question, the aws-infographic default), the HTML Deck section (commands, never edited by hand,
  `--no-notes`), the bundled-assets rows, `references/html-deck.md` (every key of the page's own help listed, tools,
  limits, presenter guide), and the runtime files (`deck.css`, `deck.js`: one stage size, nothing from the network,
  `.pic` without a background shorthand). With python-pptx and lxml: the helpers of `deck_to_html.py` that need no
  deck (number formats, tick scale, preset shapes, color and font-name checks, the external-file pattern), `--help`,
  a missing file and a file that is not a deck. With node, pptxgenjs, Pillow, `soffice` and `pdftoppm`: the fixture
  deck (`fixtures/aws-ppt-skills/html-deck.js` behind the SKILL.md helper block) built, templated and converted, and
  the page read back (one section and one notes block per slide, one chrome picture per layout plus page-number
  patches, `deck.css` and `deck.js` in the page unchanged, no network load, embedded fonts, charts as SVG, the table,
  pictures, escaped slide and note text, a `javascript:` link dropped, number formats in data labels); the page
  without fontTools (shadowed module: whole fonts, PNG diagram), `--no-notes`, `--lang`, `--title`; a raw deck, a
  `PATH` without `soffice` and a bad `--chrome-width` refused without writing a page. With uv and a cached
  Playwright 1.64.1 (offline): `preview_html_deck.py` on the page (a picture per slide, the list, the presenter view
  following the audience window) and on a copy whose `go()` does nothing (exit 1 with WARN lines, no traceback).
  Skipped parts say why.
- `structure/test-integration.sh` — behavior of the merge fixes, each run with `HOME` on a scratch folder:
  `diagram_lib.py` asset lookup order (sibling skill, `AWS_DIAGRAM_ASSETS`, `.aws-diagram-assets`, plugin
  caches in numeric version order), `skills/setup/scripts/setup.sh` check mode and usage exit codes, sudo
  only as `sudo -n` inside the `--sudo`-gated function (with a mutation self-test), `NODE_PATH` in the deck
  skills, the skill inventory (skills/CLAUDE.md table, README tables, `my-plugins:<name>` references), and the
  word rule of 2026-11-18 kept by the skills themselves: no `절` for a part of a text and no `견주다` in the
  documents and scripts of aws-blog-skills, techblogs, html-report and kor-deslop (rule statements, the E-5
  rows, regex definitions and `lint_prose.py` are left out; the templates are not read).
- `fixtures/secret-samples.txt` — TAB-separated `name / prefix / body`; joined at runtime so no full
  token is stored. `fixtures/false-positives.txt` — one non-secret per line.
- `fixtures/aws-ppt-skills/` — `html-deck.js` (deck content with one slide per kind of element the HTML deck carries;
  the test puts the SKILL.md helper block in front of it) and `arch.svg` (a three-box diagram). Invented text only.
- `fixtures/techblogs/` — `work/` (a made-up two-section post: `meta.json`, `ko.body.html`, `en.body.html`, one 8x8 PNG)
  and `aws-post.html` (a made-up saved AWS blog page without images). Invented text only: no real customer, account
  or internal data.

## Rules
- Test files are sourced, not executed: do not `exit`, do not `set -e`, guard commands that may return
  non-zero (`|| true`, or capture `$?`). Run `cd` only in a subshell.
- Sourcing shares the runner's scope. Never assign `TOTAL`, `PASSED`, `FAILED`, `SKIPPED`, `FAILURES`,
  `FILTER`, `TEST_TMP`, `PROJECT_ROOT` or `SCRIPT_DIR`; a structure test rejects it. Prefix test-local
  names per file (`PS_`, `AB_`, `SCR_`, `KD_`, `IT_`, `HK_`, `SP_`, `AR_`, `HR_`, `TB_`, `IG_`, `PP_`). Never export or assign `HOME`; pass it
  per command (`env HOME="$TEST_TMP/..." ...`).
- Never write a complete secret literal anywhere; split it into prefix and body.
- Use `$TEST_TMP` for scratch files and repos; it is removed on exit. Never write into `skills/`
  (Python bytecode goes to `$TEST_TMP` via `-X pycache_prefix`).
- Never run `setup.sh install`; tests use check mode only (`UV_OFFLINE=1` keeps it off the network).
- A background process (the local HTTP server) must be killed in the same test file.
- A new invariant needs a test that fails when the invariant is broken. Prove it once by breaking the
  file (mutation) and watching the test go red; scanners with regexes carry a self-test on a fixture.

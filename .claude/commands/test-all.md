---
description: Run the harness tests and plugin manifest validation, then report results
allowed-tools: Read, Glob, Bash(bash tests/run-all.sh:*), Bash(claude plugin validate:*), Bash(bash -n:*)
---

# Test All

Run every check for this repo. None of them call a model. The URL checker test uses a local HTTP server
on 127.0.0.1, so no external network is needed.

## Step 1: Run Tests

Run both and keep going if one fails, so the report covers all of them:

```bash
# Hooks, secret patterns, plugin structure, and the shipped scripts' behavior
bash tests/run-all.sh

# Claude Code's own manifest and skill validation
claude plugin validate .
```

If $ARGUMENTS is given, pass it to the runner as a filter (`hooks`, `secret`, `structure`, `scripts`,
`aws-blog-skills`, `kor-deslop`, `integration`, `plugin-structure`).

## Step 2: Report

Present:
- Total, passed, failed, skipped
- Failed test names with the expected and actual values
- The likely fix when the cause is apparent

`claude plugin validate .` reports one `ICON_MISSING` warning; it only matters for the public plugin
directory listing and does not fail validation.

## Error Recovery

### If the runner itself fails
```bash
bash -n tests/run-all.sh
ls -la tests/*/*.sh
```

### Common failure categories

| Failure Pattern | Likely Cause | Fix |
|---|---|---|
| claude.ai-only name found | `present_files`, `web_fetch` or `/mnt/user-data` pasted back into aws-blog-skills from a claude.ai copy | Use the Claude Code form from the SKILL.md 실행 환경 table |
| Stale namespace found | `aws-diagrams:`, `kor-writing:`, `aws-deck@`, `whchoi:`, `/aws-diagram-design:` or bare `/aws-diagram` under `skills/` or `commands/` | Use `my-plugins:<skill>` or `/my-plugins:<name>` |
| Skill-dir path missing | A SKILL.md or reference names a script or asset that is not in that skill | Fix the path, or the sibling-relative link (`../<skill>/...`) |
| Pattern count mismatch | kor-deslop rulebook changed without SKILL.md, README, `skills/CLAUDE.md` or CLAUDE.md | Write the same count everywhere |
| setup.sh check fails | Usage or exit codes changed, or sudo used outside the `--sudo` path | Keep check mode read-only and sudo as `sudo -n` behind `--sudo` |
| Reference not listed in SKILL.md | New `references/*.md` without a table row | Add a row to the SKILL.md reference table |
| Author bio mismatch | Bio edited in one of `structure.md`, `blog-template.md` | Copy the same text to both; update `BIO_HEAD` if the first sentence changed |
| Script behavior test fails | Exit code or output format changed | Fix the script or, if intended, the test and SKILL.md together |
| Version mismatch | `plugin.json` bumped without README badge or CHANGELOG | Follow `docs/runbooks/release-plugin.md` |
| `.mcp.json` not empty | Dev-only MCP server added | Move it to user scope (`claude mcp add -s user`) |
| "invalid JSON" | Malformed manifest or settings | `python3 -m json.tool <file>` |
| "not executable" | Permission lost | `chmod +x` on the file |

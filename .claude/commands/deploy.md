---
description: Release the plugin to users (version bump, CHANGELOG, tag, push, refresh) per docs/runbooks/release-plugin.md
allowed-tools: Read, Glob, Bash(git status:*), Bash(git branch:*), Bash(git log:*), Bash(git describe:*), Bash(bash tests/run-all.sh:*), Bash(claude plugin validate:*), Bash(claude plugin list:*)
---

# Deploy (Release)

For this repo, deploying means publishing a new version of `my-plugins` (all nine skills and three commands
share one version). The repo is installed from GitHub, so `git push` reaches every user. Commit, tag and push commands are intentionally NOT
pre-allowed: each one is approved by the user when prompted.

## Step 1: Pre-Deploy Checks

1. Working tree is clean: `git status`
2. Current branch is `main` (warn otherwise)
3. `bash tests/run-all.sh` and `claude plugin validate .` pass
4. Ask the user for the new version (semver rules in `.claude/skills/release/SKILL.md`) if $ARGUMENTS
   does not give one

## Step 2: Follow the Runbook

Follow `docs/runbooks/release-plugin.md`:
- Bump `.claude-plugin/plugin.json`, README badge, CHANGELOG (both languages)
- Re-run the tests
- Commit with a Conventional Commits message and no `Co-Authored-By` (`chore: release vX.Y.Z`), tag `vX.Y.Z`,
  push `main` with the tag (user approval)

## Step 3: Verify

- `git ls-remote --tags origin vX.Y.Z` returns the tag
- `claude plugin marketplace update my-plugins`
- `claude plugin update my-plugins@my-plugins` (the marketplace update alone does not move the install)
- `claude plugin list` shows `my-plugins@my-plugins` at the new version, then `/reload-plugins`

## Step 4: Summary

Display the version, the CHANGELOG section, the pushed commit and tag, and the installed version.

## Error Recovery

### If pre-deploy checks fail (Step 1)
Stop and report. Do not stash, reset, or switch branches without the user's approval.

### If the push is rejected
Someone else pushed first. `git pull --rebase origin main`, re-run the tests, and ask again.
Never force-push `main`.

### If a bad version was published
Revert with `git revert <sha>`, release it as the next PATCH version, and push. Do not reuse or delete
a published version number; installed copies are keyed by version.

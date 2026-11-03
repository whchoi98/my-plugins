---
name: release
description: Cut a semver release of the my-plugins plugin - bump .claude-plugin/plugin.json, update the bilingual CHANGELOG.md and README badge, commit with a Conventional Commits message, tag vX.Y.Z, and refresh the installed copy. Use when asked to release, bump the version, or publish skill or command changes to users.
---

# Release Skill

Installed copies of this plugin update only when `plugin.json` `version` changes, so every change
under `skills/` or `commands/` needs a release. All eight skills and three commands share one version.
Full procedure: `docs/runbooks/release-plugin.md`.

## Procedure

### 1. Pre-release Checks
- Working tree is clean: `git status`
- On `main`: `git branch --show-current`
- Tests pass: `bash tests/run-all.sh` and `claude plugin validate .`

### 2. Determine Version
- Review changes since the last tag:
  `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`
- Apply semver for a multi-skill plugin:
  - MAJOR: invocation changes (a skill or command renamed or removed, `/my-plugins:<name>` changed),
    work-folder layout or deliverable set changed, a script's arguments changed incompatibly
  - MINOR: new skill, command, workflow step, reference file, script, confirmed rule, or `setup` dependency
  - PATCH: wording fixes, lint term tweaks, bug fixes in scripts, doc-only changes that ship

### 3. Update Files
- `.claude-plugin/plugin.json` `version`
- README version badge (`Version-X.Y.Z-green`)
- `CHANGELOG.md`: move `## [Unreleased]` items to `## [X.Y.Z] - YYYY-MM-DD` in BOTH the English and
  Korean sections; categories stay in English; English entries imperative, Korean entries 명사형 종결;
  update the reference links at the bottom of both sections

### 4. Commit and Tag
- `git commit -m "chore: release vX.Y.Z"` (Conventional Commits; no `Co-Authored-By` trailer, the
  `commit-msg` hook strips it)
- `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- Pushing `main` and the tag is outward-facing (public repo): ask the user before
  `git push origin main --follow-tags`. Before the first public push, the aws-deck license has to be settled
  (`docs/decisions/ADR-002-merge-four-plugins-into-one.md`)

### 5. Refresh and Summarize
- `claude plugin marketplace update my-plugins`
- `claude plugin update my-plugins@my-plugins` (the marketplace update alone does not move the
  installed version), then `/reload-plugins` or restart
- Display the version bump, key changes, and anything not yet pushed

#!/bin/bash
# True/false positive tests for .claude/hooks/secret-scan.sh, run against the real scanner
# (sourced by tests/run-all.sh). Samples are assembled at runtime from tests/fixtures/.

SCANNER=".claude/hooks/secret-scan.sh"

# --- True positives: each sample must be detected, in .txt and in .md ---
while IFS=$'\t' read -r name prefix body; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    for ext in txt md; do
        sample="$TEST_TMP/tp-sample.$ext"
        printf '%s%s\n' "$prefix" "$body" > "$sample"
        if bash "$SCANNER" --files "$sample" >/dev/null 2>&1; then
            fail "TP ($ext): $name" "scanner did not detect the sample"
        else
            pass "TP ($ext): $name"
        fi
    done
done < tests/fixtures/secret-samples.txt

# --- False positives: none of these lines may trigger ---
while IFS= read -r line; do
    [ -z "$line" ] && continue
    sample="$TEST_TMP/fp-sample.md"
    printf '%s\n' "$line" > "$sample"
    if bash "$SCANNER" --files "$sample" >/dev/null 2>&1; then
        pass "FP: ${line:0:40}"
    else
        fail "FP: ${line:0:40}" "scanner flagged a non-secret"
    fi
done < tests/fixtures/false-positives.txt

# --- The shipped content itself must scan clean ---
# In a git checkout: tracked and new (not ignored) files. Outside one (a fresh copy before `git init`):
# every file, minus what .gitignore keeps out (local .env files, caches, archives, blog work folders).
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    mapfile -t TRACKED < <(git ls-files 2>/dev/null; git ls-files -o --exclude-standard 2>/dev/null)
    SP_SCOPE="tracked and new files"
else
    mapfile -t TRACKED < <(find . -type f -not -path './.git/*' -not -name '.env' -not -name '.env.*' \
        -not -path './.claude/settings.local.json' -not -path '*/__pycache__/*' -not -name '*.pyc' \
        -not -name '*.zip' -not -name '*.tar.gz' -not -regex '\./[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-[^/]*/.*' \
        -printf '%P\n' | sort; [ -f .env.example ] && echo .env.example)
    SP_SCOPE="all files (no git checkout)"
fi
if [ "${#TRACKED[@]}" -gt 0 ] && bash "$SCANNER" --files "${TRACKED[@]}" >/dev/null 2>&1; then
    pass "repo: $SP_SCOPE scan clean (${#TRACKED[@]} files)"
else
    fail "repo: $SP_SCOPE scan clean" "$(bash "$SCANNER" --files "${TRACKED[@]}" 2>&1 | head -3)"
fi

# --- Skip and forbidden-path rules ---
bash "$SCANNER" --files .env.example >/dev/null 2>&1 \
    && pass "skip: .env.example is not scanned" || fail "skip: .env.example is not scanned" "flagged"
bash "$SCANNER" --files tests/fixtures/secret-samples.txt >/dev/null 2>&1 \
    && pass "skip: fixture files are not scanned" || fail "skip: fixture files are not scanned" "flagged"
bash "$SCANNER" --files .env >/dev/null 2>&1 \
    && fail "forbidden: .env is always blocked" "allowed" \
    || pass "forbidden: .env is always blocked"
bash "$SCANNER" --files .claude/settings.local.json >/dev/null 2>&1 \
    && fail "forbidden: .claude/settings.local.json is always blocked" "allowed" \
    || pass "forbidden: .claude/settings.local.json is always blocked"
SKIP_LINE=$(grep -m1 '^SKIP_PATTERNS=' "$SCANNER" || true)
assert_not_contains "scanner: Markdown is not skipped" "$SKIP_LINE" "'*.md'"

# --- Regression: the AWS secret pattern must compile in PCRE (no variable-length lookbehind) ---
# grep exits 1 for "no match" and 2 for a pattern error
AWS_SECRET_REGEX=$(grep -oP "^\s+'\Kaws_secret_access_key[^']*" "$SCANNER" | head -1 || true)
REGEX_STATUS=0
echo "x" | grep -P -- "$AWS_SECRET_REGEX" >/dev/null 2>&1 || REGEX_STATUS=$?
if [ -n "$AWS_SECRET_REGEX" ] && [ "$REGEX_STATUS" -le 1 ]; then
    pass "AWS secret regex compiles"
else
    fail "AWS secret regex compiles" "pattern missing or grep -P error (status $REGEX_STATUS)"
fi

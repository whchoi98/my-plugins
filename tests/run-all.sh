#!/bin/bash
# Test runner for harness engineering tests.
# Usage: bash tests/run-all.sh [test-file-pattern]
# The pattern is a grep regex matched against each test file's path under tests/, without .sh.
# Example: bash tests/run-all.sh             # run all tests
#          bash tests/run-all.sh hooks        # tests/hooks/*
#          bash tests/run-all.sh structure    # tests/structure/* (structure and shipped-script tests)
#          bash tests/run-all.sh scripts      # structure/test-aws-blog-skills-scripts only
#          bash tests/run-all.sh integration  # structure/test-integration only
#
# Test files are sourced. -e is deliberately off: a grep that finds nothing must not abort the
# run; every check reports through pass/fail instead.

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0
FAILURES=()

export TEST_RUNNER_ACTIVE=1

pass() {
    TOTAL=$((TOTAL + 1))
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}✓${NC} $1"
}

fail() {
    TOTAL=$((TOTAL + 1))
    FAILED=$((FAILED + 1))
    FAILURES+=("$1: $2")
    echo -e "  ${RED}✗${NC} $1"
    echo -e "    ${RED}→ $2${NC}"
}

skip() {
    TOTAL=$((TOTAL + 1))
    SKIPPED=$((SKIPPED + 1))
    echo -e "  ${YELLOW}○${NC} $1 (skipped: $2)"
}

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    [ "$expected" = "$actual" ] && pass "$desc" || fail "$desc" "expected '$expected', got '$actual'"
}

assert_contains() {
    local desc="$1" haystack="$2" needle="$3"
    printf '%s\n' "$haystack" | grep -qF -- "$needle" && pass "$desc" || fail "$desc" "output does not contain '$needle'"
}

assert_not_contains() {
    local desc="$1" haystack="$2" needle="$3"
    printf '%s\n' "$haystack" | grep -qF -- "$needle" && fail "$desc" "output unexpectedly contains '$needle'" || pass "$desc"
}

assert_file_exists() {
    local desc="$1" filepath="$2"
    [ -f "$filepath" ] && pass "$desc" || fail "$desc" "file not found: $filepath"
}

assert_file_executable() {
    local desc="$1" filepath="$2"
    [ -x "$filepath" ] && pass "$desc" || fail "$desc" "file not executable: $filepath"
}

assert_json_valid() {
    local desc="$1" filepath="$2"
    python3 -m json.tool "$filepath" > /dev/null 2>&1 && pass "$desc" || fail "$desc" "invalid JSON: $filepath"
}

assert_bash_syntax() {
    local desc="$1" filepath="$2"
    bash -n "$filepath" 2>/dev/null && pass "$desc" || fail "$desc" "bash syntax error in: $filepath"
}

FILTER="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
export CLAUDE_PROJECT_DIR="$PROJECT_ROOT"

# Scratch space for tests that need temporary files or git repositories
TEST_TMP="$(mktemp -d "${TMPDIR:-/tmp}/harness-tests.XXXXXX")"
trap 'case "$TEST_TMP" in */harness-tests.*) rm -rf -- "$TEST_TMP" ;; esac' EXIT

echo -e "${CYAN}=== Harness Test Suite ===${NC}"
echo ""

TEST_FILES=$(find "$SCRIPT_DIR" -name "test-*.sh" | sort)

for test_file in $TEST_FILES; do
    test_name=$(basename "$test_file" .sh)
    # Match the filter against the path under tests/ (e.g. structure/test-aws-blog-skills-scripts),
    # so "structure" selects the whole directory and "scripts" or "kor-deslop" a single file.
    test_path="${test_file#"$SCRIPT_DIR"/}"
    if [ -n "$FILTER" ] && ! printf '%s\n' "${test_path%.sh}" | grep -q -- "$FILTER"; then
        continue
    fi
    echo -e "${CYAN}▸ $test_name${NC}"
    # shellcheck source=/dev/null
    source "$test_file"
    echo ""
done

echo -e "${CYAN}=== Results ===${NC}"
echo -e "  Total:   $TOTAL"
echo -e "  ${GREEN}Passed:  $PASSED${NC}"
[ "$FAILED" -gt 0 ] && echo -e "  ${RED}Failed:  $FAILED${NC}" || echo -e "  Failed:  0"
[ "$SKIPPED" -gt 0 ] && echo -e "  ${YELLOW}Skipped: $SKIPPED${NC}" || echo -e "  Skipped: 0"

if [ "${#FAILURES[@]}" -gt 0 ]; then
    echo ""
    echo -e "${RED}=== Failures ===${NC}"
    for f in "${FAILURES[@]}"; do
        echo -e "  ${RED}✗${NC} $f"
    done
    exit 1
fi

if [ "$TOTAL" -eq 0 ] || [ "$TOTAL" -ne $((PASSED + FAILED + SKIPPED)) ]; then
    echo -e "${RED}Counters are inconsistent or no tests ran (filter: '$FILTER'); a test file may have overwritten them.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All tests passed.${NC}"

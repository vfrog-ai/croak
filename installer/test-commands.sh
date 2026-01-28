#!/bin/bash

# CROAK Command Test Script
# Tests all CLI commands to ensure they work correctly

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test header
print_test() {
  echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}Testing: $1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to run a test
run_test() {
  local test_name="$1"
  local command="$2"
  
  print_test "$test_name"
  echo -e "${YELLOW}Command: ${command}${NC}\n"
  
  if eval "$command" > /tmp/croak-test-output.log 2>&1; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "${RED}Output:${NC}"
    cat /tmp/croak-test-output.log
    ((TESTS_FAILED++))
    return 1
  fi
}

# Function to run a test that should fail (negative test)
run_test_should_fail() {
  local test_name="$1"
  local command="$2"
  
  print_test "$test_name (should fail)"
  echo -e "${YELLOW}Command: ${command}${NC}\n"
  
  if ! eval "$command" > /tmp/croak-test-output.log 2>&1; then
    echo -e "${GREEN}✓ PASSED (correctly failed)${NC}"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}✗ FAILED (should have failed but didn't)${NC}"
    echo -e "${RED}Output:${NC}"
    cat /tmp/croak-test-output.log
    ((TESTS_FAILED++))
    return 1
  fi
}

# Get the path to the croak binary
CROAK_BIN="./bin/croak.js"
if [ ! -f "$CROAK_BIN" ]; then
  echo -e "${RED}Error: croak.js not found at $CROAK_BIN${NC}"
  echo -e "${YELLOW}Make sure you're running this from the installer directory${NC}"
  exit 1
fi

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    CROAK Command Test Suite                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Test 1: Version command
run_test "Version command" "node $CROAK_BIN --version"

# Test 2: Version command (short)
run_test "Version command (short)" "node $CROAK_BIN -v"

# Test 3: Help command
run_test "Help command" "node $CROAK_BIN --help"

# Test 4: Help command (short)
run_test "Help command (short)" "node $CROAK_BIN -h"

# Test 5: Help subcommand
run_test "Help subcommand" "node $CROAK_BIN help"

# Test 6: Init command (dry run - should show help or prompt)
run_test "Init command help" "node $CROAK_BIN init --help"

# Test 7: Doctor command (should work even without initialization, but may exit with 1)
print_test "Doctor command"
echo -e "${YELLOW}Command: node $CROAK_BIN doctor${NC}\n"
if node $CROAK_BIN doctor > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}"
  ((TESTS_PASSED++))
else
  # Doctor exits with 1 when there are issues, which is expected behavior
  if grep -q "CROAK Doctor" /tmp/croak-test-output.log; then
    echo -e "${GREEN}✓ PASSED (doctor ran correctly, found expected issues)${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}✗ FAILED${NC}"
    cat /tmp/croak-test-output.log
    ((TESTS_FAILED++))
  fi
fi

# Test 8: Doctor command with help
run_test "Doctor command help" "node $CROAK_BIN doctor --help"

# Test 9: Upgrade command (check only)
run_test "Upgrade command (check)" "node $CROAK_BIN upgrade --check"

# Test 10: Upgrade command help
run_test "Upgrade command help" "node $CROAK_BIN upgrade --help"

# Test 11: Invalid command (should fail gracefully)
run_test_should_fail "Invalid command" "node $CROAK_BIN invalid-command-that-does-not-exist"

# Test 12: No arguments (should show help)
print_test "No arguments (shows help)"
echo -e "${YELLOW}Command: node $CROAK_BIN${NC}\n"
if node $CROAK_BIN > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}"
  ((TESTS_PASSED++))
else
  # Check if it at least showed the banner/help
  if grep -q "CROAK\|Usage:" /tmp/croak-test-output.log; then
    echo -e "${GREEN}✓ PASSED (showed help/banner)${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}✗ FAILED${NC}"
    cat /tmp/croak-test-output.log
    ((TESTS_FAILED++))
  fi
fi

# Test 13: Linting
print_test "Linting"
echo -e "${YELLOW}Command: npm run lint${NC}\n"
if npm run lint > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⚠ Linting has issues (check output)${NC}"
  cat /tmp/croak-test-output.log
  ((TESTS_FAILED++))
fi

# Test 14: Formatting check
print_test "Formatting"
echo -e "${YELLOW}Command: npm run format${NC}\n"
if npm run format > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⚠ Formatting has issues (check output)${NC}"
  cat /tmp/croak-test-output.log
  ((TESTS_FAILED++))
fi

# Test 15: Package publish dry-run
print_test "Package publish dry-run"
echo -e "${YELLOW}Command: npm publish --dry-run${NC}\n"
if npm publish --dry-run > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}"
  echo -e "${CYAN}Package contents:${NC}"
  grep -A 20 "Tarball Contents" /tmp/croak-test-output.log || true
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ FAILED${NC}"
  cat /tmp/croak-test-output.log
  ((TESTS_FAILED++))
fi

# Test 16: Package.json validation
print_test "Package.json validation"
if node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8'))" > /tmp/croak-test-output.log 2>&1; then
  echo -e "${GREEN}✓ PASSED (valid JSON)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ FAILED (invalid JSON)${NC}"
  cat /tmp/croak-test-output.log
  ((TESTS_FAILED++))
fi

# Test 17: Check required files exist
print_test "Required files check"
MISSING_FILES=0
REQUIRED_FILES=(
  "package.json"
  "bin/croak.js"
  "src/index.js"
  "README.md"
  "LICENSE"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "${GREEN}✓ $file exists${NC}"
  else
    echo -e "${RED}✗ $file missing${NC}"
    ((MISSING_FILES++))
  fi
done

if [ $MISSING_FILES -eq 0 ]; then
  echo -e "${GREEN}✓ All required files present${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ Missing $MISSING_FILES required file(s)${NC}"
  ((TESTS_FAILED++))
fi

# Summary
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Test Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
  echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
else
  echo -e "${GREEN}Tests Failed: $TESTS_FAILED${NC}"
fi

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo -e "${CYAN}Total Tests: $TOTAL${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "\n${GREEN}✨ All tests passed!${NC}\n"
  exit 0
else
  echo -e "\n${RED}❌ Some tests failed. Please review the output above.${NC}\n"
  exit 1
fi

#!/usr/bin/env bash
set -e

# Colors
RED="\033[31m"
YELLOW="\033[33m"
GREEN="\033[32m"
BLUE="\033[34m"
CYAN="\033[36m"
RESET="\033[0m"
BOLD="\033[1m"

# Usage
FRONTEND_DIR="${1:-saUI}"
LABEL_AWAITING_AUDIT="awaiting-audit"
LABEL_AUDITED="audited"

BEADS_INTERVAL=30
FULL_INTERVAL=60
LAST_FULL=0

# Initialize variables for first display
TOTAL_TSC_ERRORS="--"
TEST_TSC_ERRORS="--"
NON_TEST_TSC_ERRORS="--"
BUN_STATUS="${YELLOW}pending${RESET}"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo -e "${RED}Error:${RESET} frontend directory '$FRONTEND_DIR' not found!"
  exit 1
fi

while true; do
  NOW=$(date +%s)
  ELAPSED_FULL=$((NOW - LAST_FULL))

  # Clear screen
  clear

  echo -e "${BLUE}${BOLD}==================== DASHBOARD ====================${RESET}"
  echo -e "${CYAN}Updated:${RESET} $(date)"
  echo -e "${CYAN}Frontend Dir:${RESET} $FRONTEND_DIR"
  echo -e "${CYAN}Refresh:${RESET} Issues every ${BEADS_INTERVAL}s, Full check every ${FULL_INTERVAL}s"
  echo

  # ——————————————————————————————————————————————
  # Beads issue snapshot
  # ——————————————————————————————————————————————
  TOTAL_ISSUES=$(bd list --json 2>/dev/null | jq 'length')
  OPEN_ISSUES=$(bd list --status open --json 2>/dev/null | jq 'length')
  CLOSED_NO_LABELS=$(bd list --status closed --no-labels --json 2>/dev/null | jq 'length')
  CLOSED_AWAITING_AUDIT=$(bd list --status closed --label "$LABEL_AWAITING_AUDIT" --json 2>/dev/null | jq 'length')
  CLOSED_AUDITED=$(bd list --status closed --label "$LABEL_AUDITED" --json 2>/dev/null | jq 'length')

  echo -e "${BLUE}Beads Issues:${RESET}"
  printf "  Total                 : %s%s%s\n" \
    "$( [ "$TOTAL_ISSUES" -gt 0 ] && echo -e "$YELLOW" || echo -e "$GREEN" )" "$TOTAL_ISSUES" "$RESET"
  printf "  Open                  : %s%s%s\n" \
    "$( [ "$OPEN_ISSUES" -gt 0 ] && echo -e "$RED" || echo -e "$GREEN" )" "$OPEN_ISSUES" "$RESET"
  printf "  Closed (no labels)    : %s%s%s\n" \
    "$( [ "$CLOSED_NO_LABELS" -gt 0 ] && echo -e "$YELLOW" || echo -e "$GREEN" )" "$CLOSED_NO_LABELS" "$RESET"
  printf "  Closed (awaiting-audit): %s%s%s\n" \
    "$( [ "$CLOSED_AWAITING_AUDIT" -gt 0 ] && echo -e "$YELLOW" || echo -e "$GREEN" )" "$CLOSED_AWAITING_AUDIT" "$RESET"
  printf "  Closed (audited)       : %s%s%s\n" \
    "$( [ "$CLOSED_AUDITED" -gt 0 ] && echo -e "$GREEN" || echo -e "$GREEN" )" "$CLOSED_AUDITED" "$RESET"
  echo

  # ——————————————————————————————————————————————
  # Full check (TS + Bun)
  # ——————————————————————————————————————————————
  if [ $ELAPSED_FULL -ge $FULL_INTERVAL ]; then
    cd "$FRONTEND_DIR"

    # TypeScript errors (use node_modules/.bin/tsc or npx)
    TMP_OUT=$(mktemp)
    if [ -f node_modules/.bin/tsc ]; then
      node_modules/.bin/tsc --noEmit 2>&1 > "$TMP_OUT" || true
    elif [ -f ../node_modules/.bin/tsc ]; then
      ../node_modules/.bin/tsc --noEmit 2>&1 > "$TMP_OUT" || true
    else
      echo "tsc not found in node_modules" > "$TMP_OUT"
    fi

    TOTAL_TSC_ERRORS=$(grep -E "error TS[0-9]+" "$TMP_OUT" | wc -l | tr -d " ")
    TEST_TSC_ERRORS=$(grep -E "error TS[0-9]+" "$TMP_OUT" \
      | grep -E "\.test\.ts|\.spec\.ts|__tests__" \
      | wc -l | tr -d " ")
    NON_TEST_TSC_ERRORS=$((TOTAL_TSC_ERRORS - TEST_TSC_ERRORS))

    rm "$TMP_OUT"

    # Build check (npm run build)
    if [ -f package.json ]; then
      BUILD_OUT=$(mktemp)
      npm run build 2>&1 > "$BUILD_OUT" || true
      BUILD_EXIT=$?
      if [ $BUILD_EXIT -eq 0 ]; then
        BUN_STATUS="${GREEN}Succeeded${RESET}"
      else
        BUN_STATUS="${RED}Failed${RESET}"
      fi
      rm "$BUILD_OUT"
    else
      BUN_STATUS="${YELLOW}no package.json${RESET}"
    fi

    cd - >/dev/null
    LAST_FULL=$NOW
  fi

  echo -e "${BLUE}TypeScript Errors (tsc):${RESET}"
  printf "  Total Errors        : %s%s%s\n" \
    "$( [[ "$TOTAL_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$TOTAL_TSC_ERRORS" -gt 0 ] && echo -e "$RED" || echo -e "$YELLOW" )" "$TOTAL_TSC_ERRORS" "$RESET"
  printf "  Test File Errors    : %s%s%s\n" \
    "$( [[ "$TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$TEST_TSC_ERRORS" -gt 0 ] && echo -e "$YELLOW" || echo -e "$GREEN" )" "$TEST_TSC_ERRORS" "$RESET"
  printf "  Non-Test File Errors: %s%s%s\n" \
    "$( [[ "$NON_TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$NON_TEST_TSC_ERRORS" -gt 0 ] && echo -e "$YELLOW" || echo -e "$GREEN" )" "$NON_TEST_TSC_ERRORS" "$RESET"
  echo
  echo -e "${BLUE}Build Status:${RESET} $BUN_STATUS"
  echo
  echo -e "${CYAN}===================================================${RESET}"

  sleep $BEADS_INTERVAL
done


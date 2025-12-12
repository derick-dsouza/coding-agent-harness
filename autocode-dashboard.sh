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
LAST_BUILD_CHECK="never"

# Previous run values for comparison
PREV_TOTAL_TSC_ERRORS=""
PREV_TEST_TSC_ERRORS=""
PREV_NON_TEST_TSC_ERRORS=""

if [ ! -d "$FRONTEND_DIR" ]; then
  echo -e "${RED}Error:${RESET} frontend directory '$FRONTEND_DIR' not found!"
  exit 1
fi

# Clean shutdown handler
cleanup() {
  echo -e "\n${CYAN}Dashboard shutting down...${RESET}"
  exit 0
}

trap cleanup SIGINT SIGTERM

while true; do
  NOW=$(date +%s)
  ELAPSED_FULL=$((NOW - LAST_FULL))

  # Clear screen
  clear

  echo -e "${BLUE}${BOLD}================ AUTOCODE DASHBOARD ================${RESET}"
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
  COLOR=$( [ "$TOTAL_ISSUES" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  echo -e "  Total                 : ${COLOR}${TOTAL_ISSUES}${RESET}"
  COLOR=$( [ "$OPEN_ISSUES" -gt 0 ] && echo "$RED" || echo "$GREEN" )
  echo -e "  Open                  : ${COLOR}${OPEN_ISSUES}${RESET}"
  COLOR=$( [ "$CLOSED_NO_LABELS" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  echo -e "  Closed (no labels)    : ${COLOR}${CLOSED_NO_LABELS}${RESET}"
  COLOR=$( [ "$CLOSED_AWAITING_AUDIT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  echo -e "  Closed (awaiting-audit): ${COLOR}${CLOSED_AWAITING_AUDIT}${RESET}"
  echo -e "  Closed (audited)       : ${GREEN}${CLOSED_AUDITED}${RESET}"
  
  # In-progress issues from BEADS
  IN_PROGRESS_ISSUES=$(bd list --status in_progress --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
  COLOR=$( [ "$IN_PROGRESS_ISSUES" -gt 0 ] && echo "$CYAN" || echo "$GREEN" )
  echo -e "  In Progress           : ${COLOR}${IN_PROGRESS_ISSUES}${RESET}"
  echo

  # ——————————————————————————————————————————————
  # Worker Coordination Status
  # ——————————————————————————————————————————————
  WORKERS_DIR=".autocode-workers"
  if [ -d "$WORKERS_DIR" ]; then
    # Count active workers (lock files with recent heartbeats)
    ACTIVE_WORKERS=0
    NOW_TS=$(date +%s)
    HEARTBEAT_TIMEOUT=90
    
    shopt -s nullglob
    for lock_file in "$WORKERS_DIR"/worker-*.lock; do
      if [ -f "$lock_file" ]; then
        HEARTBEAT=$(jq -r '.heartbeat // 0' "$lock_file" 2>/dev/null | cut -d. -f1)
        if [ -n "$HEARTBEAT" ] && [ "$HEARTBEAT" -gt 0 ]; then
          AGE=$((NOW_TS - HEARTBEAT))
          if [ "$AGE" -lt "$HEARTBEAT_TIMEOUT" ]; then
            ACTIVE_WORKERS=$((ACTIVE_WORKERS + 1))
          fi
        fi
      fi
    done
    shopt -u nullglob
    
    # Count claims
    CLAIM_COUNT=0
    if [ -d "$WORKERS_DIR/claims" ]; then
      CLAIM_COUNT=$(ls -1 "$WORKERS_DIR/claims/"*.claim 2>/dev/null | wc -l | tr -d " " || echo "0")
      [ -z "$CLAIM_COUNT" ] && CLAIM_COUNT=0
    fi
    
    # Count file locks
    FILE_LOCK_COUNT=0
    if [ -d "$WORKERS_DIR/files" ]; then
      FILE_LOCK_COUNT=$(ls -1 "$WORKERS_DIR/files/"*.lock 2>/dev/null | wc -l | tr -d " " || echo "0")
      [ -z "$FILE_LOCK_COUNT" ] && FILE_LOCK_COUNT=0
    fi
    
    echo -e "${BLUE}Worker Coordination:${RESET}"
    COLOR=$( [ "$ACTIVE_WORKERS" -gt 1 ] && echo "$CYAN" || echo "$GREEN" )
    echo -e "  Active Workers      : ${COLOR}${ACTIVE_WORKERS}${RESET}"
    COLOR=$( [ "$CLAIM_COUNT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
    echo -e "  Issue Claims        : ${COLOR}${CLAIM_COUNT}${RESET}"
    COLOR=$( [ "$FILE_LOCK_COUNT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
    echo -e "  File Locks          : ${COLOR}${FILE_LOCK_COUNT}${RESET}"
    
    # Show claimed issues if any
    if [ "$CLAIM_COUNT" -gt 0 ]; then
      echo -e "  ${CYAN}Claimed Issues:${RESET}"
      shopt -s nullglob
      for claim_file in "$WORKERS_DIR/claims/"*.claim; do
        if [ -f "$claim_file" ]; then
          ISSUE_ID=$(jq -r '.issue_id // "unknown"' "$claim_file" 2>/dev/null)
          WORKER_ID=$(jq -r '.worker_id // "unknown"' "$claim_file" 2>/dev/null)
          echo -e "    - $ISSUE_ID (worker: ${WORKER_ID:0:8})"
        fi
      done
      shopt -u nullglob
    fi
  else
    echo -e "${BLUE}Worker Coordination:${RESET}"
    echo -e "  ${YELLOW}No .autocode-workers directory${RESET}"
  fi
  echo

  # ——————————————————————————————————————————————
  # Full check (TS + Build)
  # ——————————————————————————————————————————————
  if [ $ELAPSED_FULL -ge $FULL_INTERVAL ]; then
    cd "$FRONTEND_DIR"

    # Save previous values for comparison
    if [[ "$TOTAL_TSC_ERRORS" =~ ^[0-9]+$ ]]; then
      PREV_TOTAL_TSC_ERRORS="$TOTAL_TSC_ERRORS"
      PREV_TEST_TSC_ERRORS="$TEST_TSC_ERRORS"
      PREV_NON_TEST_TSC_ERRORS="$NON_TEST_TSC_ERRORS"
    fi

    # TypeScript errors (use node_modules/.bin/tsc or npx)
    TMP_OUT=$(mktemp)
    if [ -f node_modules/.bin/tsc ]; then
      node_modules/.bin/tsc --noEmit > "$TMP_OUT" 2>&1 || true
    elif [ -f ../node_modules/.bin/tsc ]; then
      ../node_modules/.bin/tsc --noEmit > "$TMP_OUT" 2>&1 || true
    else
      echo "tsc not found in node_modules" > "$TMP_OUT"
    fi

    TOTAL_TSC_ERRORS=$(grep -E "error TS[0-9]+" "$TMP_OUT" 2>/dev/null | wc -l | tr -d " " || echo "0")
    TEST_TSC_ERRORS=$(grep -E "error TS[0-9]+" "$TMP_OUT" 2>/dev/null \
      | grep -E "\.test\.ts|\.spec\.ts|__tests__" 2>/dev/null \
      | wc -l | tr -d " " || echo "0")
    [ -z "$TOTAL_TSC_ERRORS" ] && TOTAL_TSC_ERRORS=0
    [ -z "$TEST_TSC_ERRORS" ] && TEST_TSC_ERRORS=0
    NON_TEST_TSC_ERRORS=$((TOTAL_TSC_ERRORS - TEST_TSC_ERRORS))

    rm "$TMP_OUT"

    # Build check (bun run build) - suppress all output
    if [ -f package.json ]; then
      BUILD_OUT=$(mktemp)
      set +e  # Temporarily disable exit on error
      bun run build > "$BUILD_OUT" 2>&1
      BUILD_EXIT=$?
      set -e  # Re-enable exit on error
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
    LAST_BUILD_CHECK=$(date +"%H:%M:%S")
  fi

  # Calculate time until next full check
  TIME_UNTIL_NEXT=$((FULL_INTERVAL - ELAPSED_FULL))
  [ $TIME_UNTIL_NEXT -lt 0 ] && TIME_UNTIL_NEXT=0

  echo -e "${BLUE}TypeScript Errors (tsc):${RESET} ${CYAN}(last check: ${LAST_BUILD_CHECK}, next in ${TIME_UNTIL_NEXT}s)${RESET}"
  
  # Helper function to format delta
  format_delta() {
    local curr="$1"
    local prev="$2"
    if [ -n "$prev" ] && [[ "$curr" =~ ^[0-9]+$ ]] && [[ "$prev" =~ ^[0-9]+$ ]]; then
      local diff=$((curr - prev))
      if [ $diff -lt 0 ]; then
        echo "${GREEN}(was $prev, ${diff})${RESET}"
      elif [ $diff -gt 0 ]; then
        echo "${RED}(was $prev, +${diff})${RESET}"
      else
        echo "${CYAN}(was $prev, no change)${RESET}"
      fi
    else
      echo ""
    fi
  }
  
  if [[ "$TOTAL_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$TOTAL_TSC_ERRORS" -gt 0 ]; then
    COLOR="$RED"
  else
    COLOR="$YELLOW"
  fi
  DELTA=$(format_delta "$TOTAL_TSC_ERRORS" "$PREV_TOTAL_TSC_ERRORS")
  echo -e "  Total Errors        : ${COLOR}${TOTAL_TSC_ERRORS}${RESET} $DELTA"
  
  if [[ "$TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$TEST_TSC_ERRORS" -gt 0 ]; then
    COLOR="$YELLOW"
  else
    COLOR="$GREEN"
  fi
  DELTA=$(format_delta "$TEST_TSC_ERRORS" "$PREV_TEST_TSC_ERRORS")
  echo -e "  Test File Errors    : ${COLOR}${TEST_TSC_ERRORS}${RESET} $DELTA"
  
  if [[ "$NON_TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$NON_TEST_TSC_ERRORS" -gt 0 ]; then
    COLOR="$YELLOW"
  else
    COLOR="$GREEN"
  fi
  DELTA=$(format_delta "$NON_TEST_TSC_ERRORS" "$PREV_NON_TEST_TSC_ERRORS")
  echo -e "  Non-Test File Errors: ${COLOR}${NON_TEST_TSC_ERRORS}${RESET} $DELTA"
  echo
  echo -e "${BLUE}Build Status:${RESET} $BUN_STATUS"
  echo
  echo -e "${CYAN}===================================================${RESET}"
  echo -e "${CYAN}Press 'q' to quit${RESET}"

  # Wait for BEADS_INTERVAL seconds, but check for 'q' keypress
  for ((i=0; i<BEADS_INTERVAL; i++)); do
    read -t 1 -n 1 key 2>/dev/null || true
    if [[ "$key" == "q" || "$key" == "Q" ]]; then
      cleanup
    fi
  done
done


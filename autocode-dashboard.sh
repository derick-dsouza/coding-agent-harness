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

# Previous run values for comparison (TypeScript)
PREV_TOTAL_TSC_ERRORS=""
PREV_TEST_TSC_ERRORS=""
PREV_NON_TEST_TSC_ERRORS=""

# Initial TypeScript counts (captured at first tsc run)
INIT_TOTAL_TSC_ERRORS=""
INIT_TEST_TSC_ERRORS=""
INIT_NON_TEST_TSC_ERRORS=""

# Initial BEADS counts (captured at startup)
INIT_TOTAL_ISSUES=""
INIT_OPEN_ISSUES=""
INIT_CLOSED_NO_LABELS=""
INIT_CLOSED_AWAITING_AUDIT=""
INIT_CLOSED_AUDITED=""
INIT_IN_PROGRESS_ISSUES=""

if [ ! -d "$FRONTEND_DIR" ]; then
  echo -e "${RED}Error:${RESET} frontend directory '$FRONTEND_DIR' not found!"
  exit 1
fi

# Clean shutdown handler
cleanup() {
  echo -e "\n${CYAN}Dashboard shutting down...${RESET}"
  
  # Clean up stale worker locks (heartbeat > 90s old)
  WORKERS_DIR=".autocode-workers"
  if [ -d "$WORKERS_DIR" ]; then
    NOW_TS=$(date +%s)
    HEARTBEAT_TIMEOUT=90
    CLEANED=0
    
    shopt -s nullglob
    for lock_file in "$WORKERS_DIR"/worker-*.lock; do
      if [ -f "$lock_file" ]; then
        HEARTBEAT=$(jq -r '.heartbeat // 0' "$lock_file" 2>/dev/null | cut -d. -f1)
        if [ -n "$HEARTBEAT" ] && [ "$HEARTBEAT" -gt 0 ]; then
          AGE=$((NOW_TS - HEARTBEAT))
          if [ "$AGE" -ge "$HEARTBEAT_TIMEOUT" ]; then
            WORKER_ID=$(jq -r '.worker_id // "unknown"' "$lock_file" 2>/dev/null)
            rm -f "$lock_file"
            
            # Also clean up claims and file locks from this dead worker
            if [ -d "$WORKERS_DIR/claims" ]; then
              for claim_file in "$WORKERS_DIR/claims/"*.claim; do
                if [ -f "$claim_file" ]; then
                  CLAIM_WORKER=$(jq -r '.worker_id // ""' "$claim_file" 2>/dev/null)
                  if [ "$CLAIM_WORKER" = "$WORKER_ID" ]; then
                    rm -f "$claim_file"
                    CLEANED=$((CLEANED + 1))
                  fi
                fi
              done
            fi
            
            if [ -d "$WORKERS_DIR/files" ]; then
              for file_lock in "$WORKERS_DIR/files/"*.lock; do
                if [ -f "$file_lock" ]; then
                  LOCK_WORKER=$(jq -r '.worker_id // ""' "$file_lock" 2>/dev/null)
                  if [ "$LOCK_WORKER" = "$WORKER_ID" ]; then
                    rm -f "$file_lock"
                    CLEANED=$((CLEANED + 1))
                  fi
                fi
              done
            fi
            
            echo -e "  ${YELLOW}Cleaned up stale worker: ${WORKER_ID:0:8}${RESET}"
          fi
        fi
      fi
    done
    shopt -u nullglob
    
    # Clean up stale init lock (> 300s old)
    if [ -f "$WORKERS_DIR/init.lock" ]; then
      INIT_TIME=$(jq -r '.locked_at // 0' "$WORKERS_DIR/init.lock" 2>/dev/null | cut -d. -f1)
      if [ -n "$INIT_TIME" ] && [ "$INIT_TIME" -gt 0 ]; then
        INIT_AGE=$((NOW_TS - INIT_TIME))
        if [ "$INIT_AGE" -ge 300 ]; then
          INIT_WORKER=$(jq -r '.worker_id // "unknown"' "$WORKERS_DIR/init.lock" 2>/dev/null)
          rm -f "$WORKERS_DIR/init.lock"
          echo -e "  ${YELLOW}Cleaned up stale init lock: ${INIT_WORKER:0:8} (${INIT_AGE}s old)${RESET}"
          CLEANED=$((CLEANED + 1))
        fi
      fi
    fi
    
    # Clean up stale audit lock (> 1800s / 30min old)
    if [ -f "$WORKERS_DIR/audit.lock" ]; then
      AUDIT_TIME=$(jq -r '.locked_at // 0' "$WORKERS_DIR/audit.lock" 2>/dev/null | cut -d. -f1)
      if [ -n "$AUDIT_TIME" ] && [ "$AUDIT_TIME" -gt 0 ]; then
        AUDIT_AGE=$((NOW_TS - AUDIT_TIME))
        if [ "$AUDIT_AGE" -ge 1800 ]; then
          AUDIT_WORKER=$(jq -r '.worker_id // "unknown"' "$WORKERS_DIR/audit.lock" 2>/dev/null)
          rm -f "$WORKERS_DIR/audit.lock"
          echo -e "  ${YELLOW}Cleaned up stale audit lock: ${AUDIT_WORKER:0:8} (${AUDIT_AGE}s old)${RESET}"
          CLEANED=$((CLEANED + 1))
        fi
      fi
    fi
    
    if [ "$CLEANED" -gt 0 ]; then
      echo -e "  ${GREEN}Cleaned $CLEANED stale claims/locks${RESET}"
    fi
  fi
  
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
  IN_PROGRESS_ISSUES=$(bd list --status in_progress --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")

  # Capture initial values on first run
  if [ -z "$INIT_TOTAL_ISSUES" ]; then
    INIT_TOTAL_ISSUES="$TOTAL_ISSUES"
    INIT_OPEN_ISSUES="$OPEN_ISSUES"
    INIT_CLOSED_NO_LABELS="$CLOSED_NO_LABELS"
    INIT_CLOSED_AWAITING_AUDIT="$CLOSED_AWAITING_AUDIT"
    INIT_CLOSED_AUDITED="$CLOSED_AUDITED"
    INIT_IN_PROGRESS_ISSUES="$IN_PROGRESS_ISSUES"
  fi

  # Helper function to format BEADS delta
  format_beads_delta() {
    local curr="$1"
    local init="$2"
    if [ -n "$init" ] && [[ "$curr" =~ ^[0-9]+$ ]] && [[ "$init" =~ ^[0-9]+$ ]]; then
      local diff=$((curr - init))
      if [ $diff -lt 0 ]; then
        echo "${GREEN}(was $init, ${diff})${RESET}"
      elif [ $diff -gt 0 ]; then
        echo "${CYAN}(was $init, +${diff})${RESET}"
      else
        echo ""
      fi
    else
      echo ""
    fi
  }

  echo -e "${BLUE}Beads Issues:${RESET}"
  COLOR=$( [ "$TOTAL_ISSUES" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  DELTA=$(format_beads_delta "$TOTAL_ISSUES" "$INIT_TOTAL_ISSUES")
  echo -e "  Total                 : ${COLOR}${TOTAL_ISSUES}${RESET} $DELTA"
  
  COLOR=$( [ "$OPEN_ISSUES" -gt 0 ] && echo "$RED" || echo "$GREEN" )
  DELTA=$(format_beads_delta "$OPEN_ISSUES" "$INIT_OPEN_ISSUES")
  echo -e "  Open                  : ${COLOR}${OPEN_ISSUES}${RESET} $DELTA"
  
  COLOR=$( [ "$CLOSED_NO_LABELS" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  DELTA=$(format_beads_delta "$CLOSED_NO_LABELS" "$INIT_CLOSED_NO_LABELS")
  echo -e "  Closed (no labels)    : ${COLOR}${CLOSED_NO_LABELS}${RESET} $DELTA"
  
  COLOR=$( [ "$CLOSED_AWAITING_AUDIT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
  DELTA=$(format_beads_delta "$CLOSED_AWAITING_AUDIT" "$INIT_CLOSED_AWAITING_AUDIT")
  echo -e "  Closed (awaiting-audit): ${COLOR}${CLOSED_AWAITING_AUDIT}${RESET} $DELTA"
  
  DELTA=$(format_beads_delta "$CLOSED_AUDITED" "$INIT_CLOSED_AUDITED")
  echo -e "  Closed (audited)       : ${GREEN}${CLOSED_AUDITED}${RESET} $DELTA"
  
  COLOR=$( [ "$IN_PROGRESS_ISSUES" -gt 0 ] && echo "$CYAN" || echo "$GREEN" )
  DELTA=$(format_beads_delta "$IN_PROGRESS_ISSUES" "$INIT_IN_PROGRESS_ISSUES")
  echo -e "  In Progress           : ${COLOR}${IN_PROGRESS_ISSUES}${RESET} $DELTA"
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
    
    # Check initialization lock
    INIT_LOCK_STATUS="${GREEN}Free${RESET}"
    INIT_LOCK_HOLDER=""
    if [ -f "$WORKERS_DIR/init.lock" ]; then
      INIT_WORKER=$(jq -r '.worker_id // ""' "$WORKERS_DIR/init.lock" 2>/dev/null)
      INIT_TIME=$(jq -r '.locked_at // 0' "$WORKERS_DIR/init.lock" 2>/dev/null | cut -d. -f1)
      if [ -n "$INIT_WORKER" ] && [ -n "$INIT_TIME" ] && [ "$INIT_TIME" -gt 0 ]; then
        INIT_AGE=$((NOW_TS - INIT_TIME))
        if [ "$INIT_AGE" -lt 300 ]; then
          INIT_LOCK_STATUS="${YELLOW}Locked${RESET}"
          INIT_LOCK_HOLDER=" (worker: ${INIT_WORKER:0:8}, ${INIT_AGE}s ago)"
        else
          INIT_LOCK_STATUS="${RED}Stale${RESET}"
          INIT_LOCK_HOLDER=" (${INIT_AGE}s old, will auto-cleanup)"
        fi
      fi
    fi
    
    # Check audit lock
    AUDIT_LOCK_STATUS="${GREEN}Free${RESET}"
    AUDIT_LOCK_HOLDER=""
    if [ -f "$WORKERS_DIR/audit.lock" ]; then
      AUDIT_WORKER=$(jq -r '.worker_id // ""' "$WORKERS_DIR/audit.lock" 2>/dev/null)
      AUDIT_TIME=$(jq -r '.locked_at // 0' "$WORKERS_DIR/audit.lock" 2>/dev/null | cut -d. -f1)
      if [ -n "$AUDIT_WORKER" ] && [ -n "$AUDIT_TIME" ] && [ "$AUDIT_TIME" -gt 0 ]; then
        AUDIT_AGE=$((NOW_TS - AUDIT_TIME))
        if [ "$AUDIT_AGE" -lt 1800 ]; then  # 30 min timeout for audit
          AUDIT_LOCK_STATUS="${CYAN}Running${RESET}"
          AUDIT_LOCK_HOLDER=" (worker: ${AUDIT_WORKER:0:8}, ${AUDIT_AGE}s ago)"
        else
          AUDIT_LOCK_STATUS="${RED}Stale${RESET}"
          AUDIT_LOCK_HOLDER=" (${AUDIT_AGE}s old, will auto-cleanup)"
        fi
      fi
    fi
    
    # Count decomposition requests
    DECOMP_COUNT=0
    DECOMP_PENDING=0
    if [ -d "$WORKERS_DIR/decomposition_requests" ]; then
      shopt -s nullglob
      for req_file in "$WORKERS_DIR/decomposition_requests/"*.request; do
        if [ -f "$req_file" ]; then
          DECOMP_COUNT=$((DECOMP_COUNT + 1))
          STATUS=$(jq -r '.status // ""' "$req_file" 2>/dev/null)
          if [ "$STATUS" = "pending" ]; then
            DECOMP_PENDING=$((DECOMP_PENDING + 1))
          fi
        fi
      done
      shopt -u nullglob
    fi
    
    echo -e "${BLUE}Worker Coordination:${RESET}"
    COLOR=$( [ "$ACTIVE_WORKERS" -gt 1 ] && echo "$CYAN" || echo "$GREEN" )
    echo -e "  Active Workers      : ${COLOR}${ACTIVE_WORKERS}${RESET}"
    echo -e "  Init Lock           : ${INIT_LOCK_STATUS}${INIT_LOCK_HOLDER}"
    echo -e "  Audit Lock          : ${AUDIT_LOCK_STATUS}${AUDIT_LOCK_HOLDER}"
    COLOR=$( [ "$CLAIM_COUNT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
    echo -e "  Issue Claims        : ${COLOR}${CLAIM_COUNT}${RESET}"
    COLOR=$( [ "$FILE_LOCK_COUNT" -gt 0 ] && echo "$YELLOW" || echo "$GREEN" )
    echo -e "  File Locks          : ${COLOR}${FILE_LOCK_COUNT}${RESET}"
    
    # Show decomposition requests
    if [ "$DECOMP_PENDING" -gt 0 ]; then
      echo -e "  Decomp Requests     : ${RED}${DECOMP_PENDING} pending${RESET} (of ${DECOMP_COUNT} total)"
    elif [ "$DECOMP_COUNT" -gt 0 ]; then
      echo -e "  Decomp Requests     : ${GREEN}0 pending${RESET} (${DECOMP_COUNT} processed)"
    else
      echo -e "  Decomp Requests     : ${GREEN}None${RESET}"
    fi
    
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
    
    # Show pending decomposition requests if any
    if [ "$DECOMP_PENDING" -gt 0 ]; then
      echo -e "  ${YELLOW}Pending Decomposition:${RESET}"
      shopt -s nullglob
      for req_file in "$WORKERS_DIR/decomposition_requests/"*.request; do
        if [ -f "$req_file" ]; then
          STATUS=$(jq -r '.status // ""' "$req_file" 2>/dev/null)
          if [ "$STATUS" = "pending" ]; then
            ISSUE_ID=$(jq -r '.issue_id // "unknown"' "$req_file" 2>/dev/null)
            REASON=$(jq -r '.reason // ""' "$req_file" 2>/dev/null | head -c 40)
            echo -e "    - $ISSUE_ID: ${REASON}..."
          fi
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

    # Capture initial TSC values on first successful run
    if [ -z "$INIT_TOTAL_TSC_ERRORS" ] && [[ "$TOTAL_TSC_ERRORS" =~ ^[0-9]+$ ]]; then
      INIT_TOTAL_TSC_ERRORS="$TOTAL_TSC_ERRORS"
      INIT_TEST_TSC_ERRORS="$TEST_TSC_ERRORS"
      INIT_NON_TEST_TSC_ERRORS="$NON_TEST_TSC_ERRORS"
    fi

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
  
  # Helper function to format delta from last run
  format_tsc_delta_last() {
    local curr="$1"
    local prev="$2"
    if [ -n "$prev" ] && [[ "$curr" =~ ^[0-9]+$ ]] && [[ "$prev" =~ ^[0-9]+$ ]]; then
      local diff=$((curr - prev))
      if [ $diff -lt 0 ]; then
        echo "${GREEN}(${diff})${RESET}"
      elif [ $diff -gt 0 ]; then
        echo "${RED}(+${diff})${RESET}"
      else
        echo "${CYAN}(0)${RESET}"
      fi
    else
      echo ""
    fi
  }
  
  # Helper function to format delta from session start
  format_tsc_delta_start() {
    local curr="$1"
    local init="$2"
    if [ -n "$init" ] && [[ "$curr" =~ ^[0-9]+$ ]] && [[ "$init" =~ ^[0-9]+$ ]]; then
      local diff=$((curr - init))
      if [ $diff -lt 0 ]; then
        echo "${GREEN}[start: $init, ${diff}]${RESET}"
      elif [ $diff -gt 0 ]; then
        echo "${RED}[start: $init, +${diff}]${RESET}"
      else
        echo "${CYAN}[start: $init, 0]${RESET}"
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
  DELTA_LAST=$(format_tsc_delta_last "$TOTAL_TSC_ERRORS" "$PREV_TOTAL_TSC_ERRORS")
  DELTA_START=$(format_tsc_delta_start "$TOTAL_TSC_ERRORS" "$INIT_TOTAL_TSC_ERRORS")
  echo -e "  Total Errors        : ${COLOR}${TOTAL_TSC_ERRORS}${RESET} $DELTA_LAST $DELTA_START"
  
  if [[ "$TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$TEST_TSC_ERRORS" -gt 0 ]; then
    COLOR="$YELLOW"
  else
    COLOR="$GREEN"
  fi
  DELTA_LAST=$(format_tsc_delta_last "$TEST_TSC_ERRORS" "$PREV_TEST_TSC_ERRORS")
  DELTA_START=$(format_tsc_delta_start "$TEST_TSC_ERRORS" "$INIT_TEST_TSC_ERRORS")
  echo -e "  Test File Errors    : ${COLOR}${TEST_TSC_ERRORS}${RESET} $DELTA_LAST $DELTA_START"
  
  if [[ "$NON_TEST_TSC_ERRORS" =~ ^[0-9]+$ ]] && [ "$NON_TEST_TSC_ERRORS" -gt 0 ]; then
    COLOR="$YELLOW"
  else
    COLOR="$GREEN"
  fi
  DELTA_LAST=$(format_tsc_delta_last "$NON_TEST_TSC_ERRORS" "$PREV_NON_TEST_TSC_ERRORS")
  DELTA_START=$(format_tsc_delta_start "$NON_TEST_TSC_ERRORS" "$INIT_NON_TEST_TSC_ERRORS")
  echo -e "  Non-Test File Errors: ${COLOR}${NON_TEST_TSC_ERRORS}${RESET} $DELTA_LAST $DELTA_START"
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


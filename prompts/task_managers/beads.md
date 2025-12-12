## BEADS TASK MANAGEMENT

BEADS is a git-backed, local task management system. Use the `bd` CLI command directly via bash.

---

## 🚨 CRITICAL: MULTI-WORKER COORDINATION (READ FIRST!) 🚨

**STOP! Before picking up ANY issue, you MUST check and claim it first!**

Multiple workers may be running in parallel. To prevent conflicts:

```bash
# SET THIS FIRST (required for claim commands)
export HARNESS_DIR="/Users/derickdsouza/Projects/development/coding-agent-harness"

# 1. BEFORE picking an issue - check if available
python3 $HARNESS_DIR/claim_issue.py check ISSUE_ID

# 2. CLAIM the issue WITH the files you'll modify
python3 $HARNESS_DIR/claim_issue.py claim ISSUE_ID src/path/to/file1.vue src/path/to/file2.ts

# 3. ONLY THEN start work
bd update ISSUE_ID --status in_progress

# 4. When DONE - release the claim
bd update ISSUE_ID --status closed
bd label add ISSUE_ID awaiting-audit  
python3 $HARNESS_DIR/claim_issue.py release ISSUE_ID
```

**⚠️ If claim fails → Pick a DIFFERENT issue! Do NOT work on claimed issues!**

See "MULTI-WORKER BEADS COORDINATION" section below for full details.

---

**Benefits:**
- **No rate limits** - BEADS is local
- **Git-backed** - All changes tracked in .beads/ directory
- **Fast** - No network calls
- **Simple** - Direct bash commands

---

### BEADS COMMANDS REFERENCE

```bash
# List issues by status
bd list --status open --json
bd list --status open --limit 100 --json
bd list --status in_progress --json
bd list --status closed --json

# Get specific issue (NOTE: returns array, use .[0] with jq)
bd show ISSUE_ID --json
bd show ISSUE_ID --json | jq -r '.[0].description'

# Create new issue
bd create "Issue Title" \
  --description "Issue description" \
  --priority 2 \
  --type task \
  --labels label1,label2

# Update issue status
bd update ISSUE_ID --status in_progress
bd update ISSUE_ID --status open
bd update ISSUE_ID --status closed

# Update issue description (append comment)
bd update ISSUE_ID --description "$(bd show ISSUE_ID --json | jq -r '.[0].description')\n\n---\nNew comment here"

# Manage labels
bd label add ISSUE_ID label-name
bd label remove ISSUE_ID label-name

# Add comment
bd comment ISSUE_ID "Your comment here"

# Count issues
bd list --status open --json | jq 'length'
bd list --status closed --json | jq 'length'
```

---

### BEADS WORKFLOW

**For Coding Agents:**
1. **List issues:** `bd list --status open --limit 100 --json`
2. **Pick next issue:** Select from `open` status issues
3. **🚨 CLAIM FIRST:** `python3 $HARNESS_DIR/claim_issue.py claim ISSUE_ID files...` (REQUIRED!)
4. **Start work:** `bd update ISSUE_ID --status in_progress`
5. **Implement the feature**
6. **Mark done:** `bd update ISSUE_ID --status closed` and `bd label add ISSUE_ID awaiting-audit`
7. **Release claim:** `python3 $HARNESS_DIR/claim_issue.py release ISSUE_ID`

**For Initializer Agents:**
1. **Check for existing issues:** `bd list --status open --json`
2. **Create issues directly:** Use `bd create` for each feature from app_spec.txt
3. **Save state:** Create `.task_project.json`

---

### BEADS TASK DECOMPOSITION (IMPORTANT - FOR CODING AGENTS)

**🚨 CRITICAL: Coding agents NEVER create issues directly!**

If you discover during implementation that a task is too large:
- **Too Large** - Will take more than one focused session to complete properly
- **Has Hidden Complexity** - Reveals multiple distinct pieces of work
- **Blocked by Prerequisites** - Needs foundational work done first
- **Affects Multiple Files/Areas** - Should be split by area of concern

**You MUST create a DECOMPOSITION REQUEST instead of creating issues yourself.**

This ensures proper coordination - the initializer agent will create the sub-issues.

```bash
# SET THIS FIRST
export HARNESS_DIR="/Users/derickdsouza/Projects/development/coding-agent-harness"

# Request decomposition instead of creating issues
python3 $HARNESS_DIR/claim_issue.py request-decomposition ISSUE_ID \
  "Task too large - 76 errors across 8 files with different root causes" \
  "Fix useAcceptRejectDealForm return type,Fix useBankDealFormatting implicit any,Fix useClipboard generic constraints"

# Then update the issue to note decomposition was requested
bd comment ISSUE_ID "Decomposition requested - task too large for single session. See decomposition_requests/ for details."

# Release your claim and move to another issue
python3 $HARNESS_DIR/claim_issue.py release ISSUE_ID
```

**Decomposition Request Guidelines:**

| Scenario | Action |
|----------|--------|
| Issue has 5+ files to modify | Request decomposition by file/group |
| Issue has multiple unrelated changes | Request separate issues for each |
| Found prerequisite work needed | Request blocking issue, pick different work |
| Scope expanded during analysis | Request new issues for expanded scope |
| Error count higher than expected | Request split by error category or file |

**What Happens After Request:**
1. Your request is saved to `.autocode-workers/decomposition_requests/`
2. The initializer agent will pick it up and create proper sub-issues
3. You can move on to work on a different issue
4. Don't wait for decomposition - pick another task

**Why Coding Agents Don't Create Issues:**
- Prevents duplicate issues from multiple workers
- Ensures consistent issue quality (initializer's job)
- Proper dependency tracking
- Clean separation of concerns

**Remember:** Requesting decomposition is NOT failure - it's proper engineering. The initializer agent is better equipped to create well-structured sub-issues.

---

### HANDLING INCOMPLETE CLOSED ISSUES

If you discover a closed issue that was NOT actually complete (still has errors, missing functionality, etc.):

```bash
# 1. Re-open the issue
bd update ISSUE_ID --status open

# 2. Remove misleading labels
bd label remove ISSUE_ID awaiting-audit
bd label remove ISSUE_ID audited

# 3. Add context about what's still needed
bd update ISSUE_ID --description "$(bd show ISSUE_ID --json | jq -r '.[0].description')\n\n---\n**REOPENED:** Previous implementation was incomplete.\n\n## Remaining Work\n- [specific items still needed]\n\n## Current Error Count
[X] errors in [files]"

# 4. If the remaining work is substantial, decompose it
bd label add ISSUE_ID needs-decomposition
```

**Signs an Issue Should Be Reopened:**
- Running type-check/lint still shows errors in files the issue claimed to fix
- Tests fail for functionality the issue claimed to implement
- Code contains TODOs, stubs, or placeholders
- Partial implementation that only handles happy path

---

### MULTI-WORKER BEADS COORDINATION

When multiple workers are running in the same project, you MUST coordinate to avoid conflicts:

**BEFORE starting work on any issue, ALWAYS claim it first:**

The claim script is at `$AUTOCODE_HARNESS_DIR/claim_issue.py` (or find it with `which autocode` and look in the same directory).

```bash
# Find harness directory (if not set)
HARNESS_DIR=$(dirname $(which autocode 2>/dev/null || echo "$HOME/coding-agent-harness"))

# Check if issue is available
python3 $HARNESS_DIR/claim_issue.py check ISSUE_ID

# Claim the issue (with files you'll modify)
python3 $HARNESS_DIR/claim_issue.py claim ISSUE_ID src/file1.vue src/file2.ts

# List all claimed issues
python3 $HARNESS_DIR/claim_issue.py list

# Check for file conflicts before editing
python3 $HARNESS_DIR/claim_issue.py files src/file1.vue src/file2.ts

# Release claim when done (or if you abandon the issue)
python3 $HARNESS_DIR/claim_issue.py release ISSUE_ID
```

**Coordination Rules:**

1. **Always Claim First**: Before `bd update ISSUE_ID --status in_progress`, run `python3 claim_issue.py claim ISSUE_ID`
2. **Include Files**: When claiming, list the files you plan to modify to prevent edit conflicts
3. **Check Before Editing**: If claim fails, another worker is on it - pick a different issue
4. **Release When Done**: After marking issue closed, release your claim
5. **Handle Conflicts**: If you see "File has been modified" errors, another worker edited it - re-read and merge

**Workflow with Claims:**

```bash
# 1. Find an issue to work on
bd list --status open --json

# 2. Check if it's available and claim it
python3 $HARNESS_DIR/claim_issue.py check smartaffirm-xyz
python3 $HARNESS_DIR/claim_issue.py claim smartaffirm-xyz src/components/MyComponent.vue

# 3. Mark as in-progress in BEADS
bd update smartaffirm-xyz --status in_progress

# 4. Do your work...

# 5. Mark done and release
bd update smartaffirm-xyz --status closed
bd label add smartaffirm-xyz awaiting-audit
python3 $HARNESS_DIR/claim_issue.py release smartaffirm-xyz
```

**If Claim Fails:**
- The issue or files are claimed by another worker
- Pick a DIFFERENT issue - don't try to work on claimed issues
- Use `python3 claim_issue.py list` to see what's taken

---

### BEADS STATE TRACKING

All BEADS project data is stored in `.task_project.json`:
```json
{
  "adapter": "beads",
  "workspace": "default",
  "initialized": true,
  "issues_created": 50,
  "issues_closed": 45,
  "features_awaiting_audit": 40,
  "features_audited": 5,
  "legacy_done_without_audit": 0,
  "verification_status": {
    "project_marked_complete": "FALSE - 40 issues still awaiting audit",
    "audit_status": "IN PROGRESS - 5/45 features audited"
  }
}
```

**🚨 CRITICAL: Audit Tracking Fields (MUST UPDATE!):**

| Field | Description | Update When |
|-------|-------------|-------------|
| `features_awaiting_audit` | Count of issues with "awaiting-audit" label | After closing any issue |
| `features_audited` | Count of issues with "audited" label | After audit session |
| `verification_status.project_marked_complete` | TRUE only when ALL audits pass | Never set TRUE if awaiting_audit > 0 |

**To sync counts with actual BEADS data:**
```bash
# Get actual counts from BEADS
AWAITING=$(bd list --status closed --label awaiting-audit --json | jq 'length')
AUDITED=$(bd list --status closed --label audited --json | jq 'length')
NO_LABELS=$(bd list --status closed --no-labels --json | jq 'length')

# Update .task_project.json
jq --argjson await "$AWAITING" --argjson audit "$AUDITED" --argjson legacy "$NO_LABELS" \
  '.features_awaiting_audit = $await | .features_audited = $audit | .legacy_done_without_audit = $legacy' \
  .task_project.json > tmp.$$.json && mv tmp.$$.json .task_project.json
```

**Notes:**
- BEADS data is stored in `.beads/` directory (git-tracked)
- All operations are local (no API rate limits)
- Use `--json` flag for programmatic parsing
- Parse JSON with `jq` for filtering/counting
- `bd show` returns an **array** - always use `.[0]` when accessing single issue properties
- **Closed ≠ Complete!** A project is only complete when features_awaiting_audit = 0

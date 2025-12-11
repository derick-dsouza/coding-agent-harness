## BEADS TASK MANAGEMENT

BEADS is a git-backed, local task management system. Use the `bd` CLI command directly via bash.

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
3. **Start work:** `bd update ISSUE_ID --status in_progress`
4. **Implement the feature**
5. **Mark done:** `bd update ISSUE_ID --status closed` and `bd label add ISSUE_ID awaiting-audit`

**For Initializer Agents:**
1. **Check for existing issues:** `bd list --status open --json`
2. **Create issues directly:** Use `bd create` for each feature from app_spec.txt
3. **Save state:** Create `.task_project.json`

---

### BEADS TASK DECOMPOSITION (IMPORTANT)

**When to Create Sub-Issues:**

If you discover during implementation that a task is:
- **Too Large** - Will take more than one focused session to complete properly
- **Has Hidden Complexity** - Reveals multiple distinct pieces of work
- **Blocked by Prerequisites** - Needs foundational work done first
- **Affects Multiple Files/Areas** - Should be split by area of concern

**DO NOT** try to rush through or cut corners. Instead, decompose into atomic tasks:

```bash
# Create sub-issue for discovered work
bd create "Sub-task: [Specific piece of work]" \
  --description "## Context
Discovered while working on PARENT_ISSUE_ID.

## Specific Work Required
[Detailed description of this atomic task]

## Files to Modify
- path/to/file1.ts
- path/to/file2.ts

## Acceptance Criteria
- [ ] Specific testable criterion 1
- [ ] Specific testable criterion 2

## Parent Issue
PARENT_ISSUE_ID" \
  --priority 2 \
  --type task \
  --labels sub-task,RELEVANT_PHASE_LABEL

# Update parent issue to note the decomposition
bd update PARENT_ISSUE_ID --description "$(bd show PARENT_ISSUE_ID --json | jq -r '.[0].description')\n\n---\n**Decomposed:** This issue was split into sub-tasks:\n- SUB_ISSUE_ID_1: [description]\n- SUB_ISSUE_ID_2: [description]"
```

**Decomposition Guidelines:**

| Scenario | Action |
|----------|--------|
| Issue has 5+ files to modify | Split by file or logical group |
| Issue has multiple unrelated changes | Create separate issues for each |
| Found prerequisite work needed | Create blocking issue, do it first |
| Scope expanded during analysis | Create new issues for expanded scope |
| Error count higher than expected | Split by error category or file |

**Example - TypeScript Fix Decomposition:**
```bash
# Original issue: "Fix TypeScript errors in composables"
# Discovery: 76 errors across 8 files with different root causes

# Create atomic sub-issues:
bd create "Fix useAcceptRejectDealForm return type interface" \
  --description "Add missing properties to UseAcceptRejectDealFormReturn interface..." \
  --priority 2 --type task --labels sub-task,typescript-foundation

bd create "Fix useBankDealFormatting implicit any types" \
  --description "Add explicit type annotations to all function parameters..." \
  --priority 2 --type task --labels sub-task,typescript-foundation

# Mark original as decomposed (not closed, as work isn't done)
bd update ORIGINAL_ID --status open
bd label add ORIGINAL_ID decomposed
```

**Remember:** Creating sub-issues is NOT failure - it's proper engineering. A well-decomposed task list is better than a rushed, incomplete implementation.

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

When multiple workers are running in the same project, BEADS updates require coordination:

1. **Issue Claiming**: Before starting work, check `.autocode-workers/claims/` to ensure no other worker has claimed the issue
2. **Status Updates**: Only update status for issues YOU have claimed
3. **Atomic Operations**: Complete your BEADS update immediately after making changes - don't leave partial state
4. **Conflict Resolution**: If you see `.beads/` changes from another worker in git status, pull/merge before your updates

```bash
# Check if another worker is working on an issue
ls .autocode-workers/claims/ 2>/dev/null | grep -q "ISSUE_ID" && echo "CLAIMED" || echo "AVAILABLE"

# Always check git status before BEADS updates
git status .beads/
```

---

### BEADS STATE TRACKING

All BEADS project data is stored in `.task_project.json`:
```json
{
  "adapter": "beads",
  "workspace": "default",
  "initialized": true,
  "issues_created": 50,
  "features_awaiting_audit": 0,
  "legacy_done_without_audit": 0
}
```

**Notes:**
- BEADS data is stored in `.beads/` directory (git-tracked)
- All operations are local (no API rate limits)
- Use `--json` flag for programmatic parsing
- Parse JSON with `jq` for filtering/counting
- `bd show` returns an **array** - always use `.[0]` when accessing single issue properties

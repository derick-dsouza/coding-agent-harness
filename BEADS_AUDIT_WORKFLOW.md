# BEADS Audit Workflow

## Overview

BEADS manages the audit workflow through a combination of **labels**, **counters in state files**, and **periodic audit triggers**. Unlike Linear or GitHub which have built-in project management features, BEADS relies on local CLI commands and file-based tracking.

## How BEADS Audit Works

### 1. **Audit Labels**

BEADS uses labels to track audit status:

- **`awaiting-audit`** - Feature completed, needs quality review
- **`audited`** - Feature passed audit review
- **`fix`** - Issue found during audit that needs fixing

### 2. **Audit Counter Tracking**

The `.task_project.json` file tracks audit-related metrics:

```json
{
  "adapter": "beads",
  "features_awaiting_audit": 3,
  "audits_completed": 2,
  "total_issues": 124,
  "issues_closed": 101
}
```

**Key Fields:**
- `features_awaiting_audit` - Number of completed features pending review
- `audits_completed` - Number of audit sessions completed

### 3. **Automatic Audit Tracking**

When a coding agent closes an issue using `close_issue_with_audit_tracking()`:

1. **Issue is closed** via `bd close ISSUE_ID`
2. **Label is added** via `bd label add ISSUE_ID awaiting-audit`
3. **Counter is incremented** in `.task_project.json`
4. **Optional comment** is added via `bd comment ISSUE_ID "comment text"`

**BEADS-specific commands used:**
```bash
# Close issue
bd close smartaffirm-abc

# Add audit label
bd label add smartaffirm-abc awaiting-audit

# Add comment
bd comment smartaffirm-abc "Feature completed, awaiting audit review"
```

### 4. **Audit Trigger Conditions**

An audit session is triggered when:

```
features_awaiting_audit >= AUDIT_INTERVAL (default: 5)
```

**Logic in `should_run_audit()`:**
```python
def should_run_audit(project_dir: Path) -> bool:
    state = load_task_project_state(project_dir)
    awaiting_count = state.get("features_awaiting_audit", 0)
    legacy_done_count = state.get("legacy_done_without_audit", 0)
    total_awaiting = awaiting_count + legacy_done_count
    
    return total_awaiting >= AUDIT_INTERVAL  # Default: 5
```

### 5. **Audit Session Workflow**

When an audit session runs:

1. **Query issues with audit label**
   ```bash
   bd list --label awaiting-audit --status closed --json
   ```

2. **Audit agent reviews** each feature
   - Checks code quality
   - Verifies requirements met
   - Tests functionality

3. **For each reviewed feature:**
   - **If PASS**: 
     - Remove `awaiting-audit` label
     - Add `audited` label
     - Decrement `features_awaiting_audit` counter
   - **If FAIL**:
     - Create new FIX issue with `fix` label
     - Link to original issue
     - Keep `awaiting-audit` label

4. **Update state file**
   ```json
   {
     "features_awaiting_audit": 0,
     "audits_completed": 3
   }
   ```

### 6. **BEADS-Specific Commands for Audit**

**List issues awaiting audit:**
```bash
bd list --label awaiting-audit --json
```

**Count audit-pending issues:**
```bash
bd count --label awaiting-audit
```

**Review an issue (pass):**
```bash
bd label remove ISSUE_ID awaiting-audit
bd label add ISSUE_ID audited
bd comment ISSUE_ID "✅ Audit PASSED - Feature verified and working correctly"
```

**Review an issue (fail):**
```bash
bd create --title "FIX: Issue found in ISSUE_ID" --label fix --priority 1
bd label add NEW_ISSUE_ID fix
bd comment ISSUE_ID "❌ Audit FAILED - Created fix issue: NEW_ISSUE_ID"
```

## Comparison with Other Adapters

### Linear
- Uses **Linear-native states** (Done, In Progress, etc.)
- Uses **Linear API** for all operations
- Audit labels managed via Linear UI

### GitHub Issues  
- Uses **GitHub labels** and **milestones**
- Uses **GitHub API** or `gh` CLI
- Integrates with GitHub Projects

### BEADS
- Uses **local SQLite database** + JSONL files
- Uses **`bd` CLI** for all operations
- **File-based state tracking** in `.task_project.json`
- **Git-friendly** - issues stored in `.beads/` directory

## Key Differences in BEADS Audit

### 1. **No Native "Status" Field**
BEADS uses `open`/`closed` status, not `todo`/`in_progress`/`done`

**Mapping:**
```python
STATUS_TO_BEADS = {
    IssueStatus.TODO: "open",
    IssueStatus.IN_PROGRESS: "open",  # Same as TODO
    IssueStatus.DONE: "closed",
    IssueStatus.CANCELED: "closed"
}
```

### 2. **Label-Based Workflow**
BEADS relies heavily on labels for workflow state:
- `typescript-foundation` - Phase 1 tasks
- `typescript-critical` - Phase 2 tasks
- `awaiting-audit` - Completed but not reviewed
- `audited` - Passed quality review
- `fix` - Bug found during audit

### 3. **Local Storage**
All audit data is stored locally:
- `.beads/*.db` - SQLite database
- `.beads/*.jsonl` - Git-trackable issue history
- `.task_project.json` - Counter tracking

### 4. **CLI-Based Operations**
All operations use `bd` commands:
```bash
bd list --label awaiting-audit --json | jq '.[] | select(.status=="closed")'
```

vs Linear API:
```graphql
query {
  issues(filter: { labels: { name: { eq: "awaiting-audit" } } }) {
    nodes { id, title, state }
  }
}
```

## Implementation Example

### Closing an Issue with Audit Tracking (BEADS)

```python
def close_issue_with_audit_tracking(issue_id: str) -> Issue:
    # 1. Close the issue
    result = subprocess.run(
        ["bd", "close", issue_id, "--json"],
        capture_output=True, text=True
    )
    
    # 2. Add awaiting-audit label
    subprocess.run(
        ["bd", "label", "add", issue_id, "awaiting-audit"],
        capture_output=True, text=True
    )
    
    # 3. Update counter in .task_project.json
    with open(".task_project.json", "r+") as f:
        data = json.load(f)
        data["features_awaiting_audit"] = data.get("features_awaiting_audit", 0) + 1
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    
    # 4. Add comment
    subprocess.run(
        ["bd", "comment", issue_id, 
         "Feature completed. Awaiting audit review."],
        capture_output=True, text=True
    )
    
    return parse_issue(result.stdout)
```

## Audit Session Example

```python
# Check if audit needed
if should_run_audit(project_dir):
    # Get issues awaiting audit
    result = subprocess.run(
        ["bd", "list", "--label", "awaiting-audit", 
         "--status", "closed", "--json"],
        capture_output=True, text=True
    )
    
    issues = json.loads(result.stdout)
    
    for issue in issues:
        # Audit agent reviews the feature
        verdict = audit_feature(issue)
        
        if verdict == "PASS":
            # Remove awaiting-audit, add audited
            subprocess.run(["bd", "label", "remove", issue["id"], "awaiting-audit"])
            subprocess.run(["bd", "label", "add", issue["id"], "audited"])
            
            # Update counter
            decrement_audit_counter()
        else:
            # Create FIX issue
            fix_issue = subprocess.run([
                "bd", "create",
                "--title", f"FIX: {issue['title']}",
                "--label", "fix",
                "--priority", "1",
                "--json"
            ], capture_output=True, text=True)
```

## Benefits of BEADS Audit Approach

1. **Git-Friendly** - All audit history in `.beads/` tracked in git
2. **Offline-First** - Works without internet connection
3. **Simple** - Just CLI commands, no complex API
4. **Transparent** - All state visible in files
5. **Portable** - Move between machines with git

## Limitations

1. **No Web UI** - Must use CLI or text editor
2. **Manual State File Updates** - Requires script coordination
3. **No Built-in Dashboards** - Need custom tooling for metrics
4. **Label Dependency** - Workflow relies on correct label usage

## Best Practices

1. **Always use `close_issue_with_audit_tracking()`** - Don't close issues manually
2. **Check `features_awaiting_audit` counter** - Verify it matches actual label count
3. **Use consistent labels** - `awaiting-audit`, `audited`, `fix`
4. **Comment on audit results** - Document pass/fail reasons
5. **Track audit metrics** - Monitor pass rate over time

## Troubleshooting

### Counter Mismatch
```bash
# Count actual issues with label
bd count --label awaiting-audit

# Compare with .task_project.json
cat .task_project.json | jq '.features_awaiting_audit'

# Fix mismatch
python scripts/sync_audit_counter.py
```

### Missing Audit Labels
```bash
# Find closed issues without audit labels
bd list --status closed --json | jq '.[] | select(.labels | map(.name) | contains(["awaiting-audit", "audited"]) | not)'
```

### Audit Not Triggering
```bash
# Check counter
cat .task_project.json | jq '.features_awaiting_audit'

# Check AUDIT_INTERVAL in agent.py
grep AUDIT_INTERVAL agent.py
```

## See Also

- [BEADS Adapter Documentation](task_management/BEADS_ADAPTER.md)
- [Audit System Overview](AUDIT_SYSTEM.md)
- [Task Management Interface](task_management/interface.py)

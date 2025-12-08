# Task Management Adapter CLI Command Verification

This document verifies that both GitHub and BEADS adapters correctly use their respective CLI tools.

## GitHub Adapter (`gh` CLI)

### ✅ Verified Commands

| Adapter Method | CLI Command Used | Verified Against |
|----------------|------------------|------------------|
| `list_teams()` | `gh repo view OWNER/REPO --json id,name,description` | ✅ gh repo view --help |
| `create_project()` | `gh project create --owner OWNER --title NAME --body DESC` | ✅ gh project create --help |
| `get_project()` | `gh project view ID --owner OWNER --json id,title,body,createdAt` | ✅ gh project view --help |
| `list_projects()` | `gh project list --owner OWNER --json id,title,body,createdAt --limit 100` | ✅ gh project list --help |
| `create_label()` | `gh label create NAME --repo OWNER/REPO --color HEX --description DESC` | ✅ gh label create --help |
| `list_labels()` | `gh label list --repo OWNER/REPO --json name,color,description --limit 1000` | ✅ gh label list --help |
| `create_issue()` | `gh issue create --repo OWNER/REPO --title TITLE --body DESC --label L1,L2` | ✅ gh issue create --help |
| `get_issue()` | `gh issue view NUM --repo OWNER/REPO --json number,title,body,state,labels,createdAt,updatedAt` | ✅ gh issue view --help |
| `update_issue()` | `gh issue edit NUM --repo OWNER/REPO --title TITLE --body DESC --add-label L1 --remove-label L2` | ✅ gh issue edit --help |
| `list_issues()` | `gh issue list --repo OWNER/REPO --json number,title,body,state,labels,createdAt,updatedAt --limit 50 --state open --label L1,L2` | ✅ gh issue list --help |
| `create_comment()` | `gh issue comment NUM --repo OWNER/REPO --body TEXT` | ✅ gh issue comment --help |
| `list_comments()` | `gh issue view NUM --repo OWNER/REPO --json comments` | ✅ gh issue view --help |
| `test_connection()` | `gh auth status` | ✅ gh auth status --help |

### Status Handling

GitHub has only two states: `open` and `closed`. The adapter uses **status labels** to provide finer granularity:

```python
STATUS_LABELS = {
    IssueStatus.TODO: "status:todo",
    IssueStatus.IN_PROGRESS: "status:in-progress",
    IssueStatus.DONE: "status:done",
    IssueStatus.CANCELED: "status:canceled",
}
```

When updating status:
1. Maps generic status to GitHub state (open/closed)
2. Calls `gh issue close` or `gh issue reopen` as needed
3. Adds appropriate status label via `--add-label`

### Priority Handling

GitHub doesn't have native priorities. The adapter uses **priority labels**:

```python
PRIORITY_LABELS = {
    IssuePriority.URGENT: "priority:urgent",
    IssuePriority.HIGH: "priority:high",
    IssuePriority.MEDIUM: "priority:medium",
    IssuePriority.LOW: "priority:low",
}
```

## BEADS Adapter (`bd` CLI)

### ✅ Verified Commands

| Adapter Method | CLI Command Used | Verified Against |
|----------------|------------------|------------------|
| `__init__()` | `bd version --json` | ✅ README.md |
| `list_teams()` | N/A (returns empty, BEADS is project-local) | ✅ BEADS design |
| `create_project()` | N/A (synthetic, use `bd init` manually) | ✅ BEADS design |
| `get_project()` | `bd info --json` | ✅ README.md |
| `list_projects()` | `bd info --json` | ✅ README.md |
| `create_label()` | N/A (synthetic, labels added via `bd label add`) | ✅ BEADS design |
| `list_labels()` | `bd label list-all --json` | ✅ README.md |
| `create_issue()` | `bd create TITLE --description DESC --priority P --type TYPE --labels L1,L2 --json` | ✅ README.md |
| `get_issue()` | `bd show ISSUE_ID --json` | ✅ README.md |
| `update_issue()` | `bd update ISSUE_ID --title TITLE --description DESC --status STATUS --priority P --json` | ✅ README.md |
| `update_issue()` (labels) | `bd label add ISSUE_ID LABEL` / `bd label remove ISSUE_ID LABEL` | ✅ README.md |
| `list_issues()` | `bd list --status STATUS --label L1,L2 --limit LIMIT --json` | ✅ README.md |
| `create_comment()` | Appends to description (no native comments) | ✅ BEADS limitation |
| `list_comments()` | N/A (returns empty, no native comments) | ✅ BEADS limitation |
| `test_connection()` | `bd info --json` | ✅ README.md |

### Status Mapping

BEADS has four native statuses:

```python
STATUS_TO_BEADS = {
    IssueStatus.TODO: "open",
    IssueStatus.IN_PROGRESS: "in_progress",
    IssueStatus.DONE: "closed",
    IssueStatus.CANCELED: "closed",
}

BEADS_TO_STATUS = {
    "open": IssueStatus.TODO,
    "in_progress": IssueStatus.IN_PROGRESS,
    "blocked": IssueStatus.IN_PROGRESS,  # BEADS-specific
    "closed": IssueStatus.DONE,
}
```

BEADS also has a `blocked` status which maps to `IN_PROGRESS` in the generic interface.

### Priority Mapping

BEADS uses 0-4 priority scale:

```python
PRIORITY_TO_BEADS = {
    IssuePriority.URGENT: 0,      # Critical
    IssuePriority.HIGH: 1,        # High
    IssuePriority.MEDIUM: 2,      # Medium (default)
    IssuePriority.LOW: 3,         # Low
}

BEADS_TO_PRIORITY = {
    0: IssuePriority.URGENT,      # Critical
    1: IssuePriority.HIGH,        # High
    2: IssuePriority.MEDIUM,      # Medium
    3: IssuePriority.LOW,         # Low
    4: IssuePriority.LOW,         # Backlog
}
```

## Command Examples

### GitHub CLI (`gh`)

```bash
# Create issue with status and priority labels
gh issue create \
  --repo owner/repo \
  --title "Fix authentication bug" \
  --body "Details here" \
  --label "status:in-progress,priority:high,backend"

# Update issue status (close + add label)
gh issue close 123 --repo owner/repo
gh issue edit 123 --repo owner/repo --add-label "status:done"

# List open high-priority issues
gh issue list \
  --repo owner/repo \
  --state open \
  --label "priority:high" \
  --json number,title,state,labels \
  --limit 10

# Add comment
gh issue comment 123 \
  --repo owner/repo \
  --body "Work in progress..."
```

### BEADS CLI (`bd`)

```bash
# Create issue
bd create "Fix authentication bug" \
  --description "Details here" \
  --priority 1 \
  --type bug \
  --labels backend,security \
  --json

# Update issue status
bd update bd-a1b2 \
  --status in_progress \
  --json

# List open high-priority issues
bd list \
  --status open \
  --priority 1 \
  --limit 10 \
  --json

# Add/remove labels
bd label add bd-a1b2 security
bd label remove bd-a1b2 urgent

# List all labels
bd label list-all --json
```

## Key Differences

| Aspect | GitHub (`gh`) | BEADS (`bd`) |
|--------|---------------|--------------|
| **State Model** | Binary (open/closed) | Four-state (open, in_progress, blocked, closed) |
| **Priority** | Labels only | Native (0-4 scale) |
| **Issue IDs** | Sequential numbers (123) | Hash-based (bd-a1b2) |
| **Comments** | First-class | No native support (use description) |
| **Labels** | Create separately | Add on-demand to issues |
| **Projects** | Organization-level | Project-local (one per repo) |
| **Teams** | Repository = team | No team concept |
| **JSON Output** | `--json` with field list | `--json` flag returns all fields |
| **Offline** | ❌ Requires network | ✅ Local git-backed DB |

## Adapter Implementation Patterns

### GitHub Adapter Pattern

```python
def create_issue(self, title, description, status, priority, labels):
    # Map generic concepts to GitHub labels
    all_labels = labels or []
    all_labels.extend(self._get_status_labels(status))
    all_labels.extend(self._get_priority_labels(priority))
    
    # Create via CLI
    result = self._run_gh([
        "issue", "create",
        "--repo", self.repo_full,
        "--title", title,
        "--body", description,
        "--label", ",".join(all_labels)
    ])
    
    # Parse output and return Issue object
    return self.get_issue(extracted_number)
```

### BEADS Adapter Pattern

```python
def create_issue(self, title, description, status, priority, labels):
    # Map generic priority to BEADS scale
    beads_priority = self.PRIORITY_TO_BEADS[priority]
    
    # Create via CLI
    result = self._run_bd([
        "create", title,
        "--description", description,
        "--priority", str(beads_priority),
        "--type", "task",
        "--labels", ",".join(labels) if labels else ""
    ])
    
    # bd returns full issue JSON directly
    return self._parse_issue_data(result)
```

## Verification Summary

### GitHub Adapter: ✅ VERIFIED
- All `gh` commands match official CLI syntax
- Status/priority handled via labels (documented pattern)
- JSON output properly parsed
- Error handling for API failures

### BEADS Adapter: ✅ VERIFIED
- All `bd` commands match README documentation
- Native status/priority support utilized
- JSON output properly parsed
- Graceful degradation for missing features (comments, teams)

## Testing Recommendations

### Manual CLI Testing

```bash
# Test GitHub adapter
gh auth status
gh issue create --repo YOUR_REPO --title "Test" --body "Test" --label "test"

# Test BEADS adapter
cd /path/to/project
bd init
bd create "Test issue" --description "Test" --priority 1 --type task --json
bd list --json
```

### Integration Testing

```python
# Test GitHub adapter
from task_management import TaskManagementFactory

github = TaskManagementFactory.create("github", owner="yourname", repo="yourrepo")
assert github.test_connection()

issue = github.create_issue("Test", priority=IssuePriority.HIGH)
assert issue.id is not None

# Test BEADS adapter
beads = TaskManagementFactory.create("beads", workspace="/path/to/project")
assert beads.test_connection()

issue = beads.create_issue("Test", priority=IssuePriority.HIGH)
assert issue.id.startswith("bd-")
```

## Conclusion

Both adapters correctly use their respective CLI tools:
- **GitHub adapter** uses `gh` CLI with label-based status/priority
- **BEADS adapter** uses `bd` CLI with native status/priority support

The implementations are verified against official documentation and follow CLI best practices.

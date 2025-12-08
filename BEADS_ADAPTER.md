# BEADS Adapter Documentation

## Overview

The BEADS adapter integrates the BEADS git-backed issue tracker with the coding agent harness.

BEADS (https://github.com/steveyegge/beads) is a lightweight memory system for coding agents using a graph-based issue tracker backed by git.

## Installation

```bash
# Quick install (macOS/Linux)
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Or via Homebrew
brew tap steveyegge/beads
brew install bd

# Or via npm
npm install -g @beads/bd
```

## Configuration

### In project root (one-time setup):

```bash
cd /path/to/your/project
bd init
```

### In `autocode.py` config:

```python
TASK_ADAPTER = "beads"  # or "linear" or "github"

# BEADS-specific configuration
BEADS_WORKSPACE = "/path/to/your/project"  # Optional, defaults to current directory
```

## Architecture

### BEADS Concepts → Generic Task Management Mapping

| BEADS Concept | Generic Interface | Notes |
|---------------|------------------|-------|
| Project database | Project | BEADS is project-local, one database per repo |
| Issue | Issue | Full mapping with hash-based IDs (bd-a1b2) |
| Status (open, in_progress, blocked, closed) | IssueStatus | Maps to TODO, IN_PROGRESS, DONE, CANCELED |
| Priority (0-4) | IssuePriority | 0=URGENT, 1=HIGH, 2=MEDIUM, 3=LOW, 4=LOW |
| Labels | Label | String labels with usage counts |
| Notes/Description updates | Comment | Appended to description (no first-class comments) |
| Type (bug, feature, task, epic, chore) | Stored in metadata | Preserved in Issue.metadata |

### Status Mapping

| Generic Status | BEADS Status |
|----------------|--------------|
| TODO | open |
| IN_PROGRESS | in_progress |
| DONE | closed |
| CANCELED | closed |

**Note:** BEADS also has a "blocked" status which maps to IN_PROGRESS in the generic interface.

### Priority Mapping

| Generic Priority | BEADS Priority (0-4 scale) |
|-----------------|----------------------------|
| URGENT | 0 (critical) |
| HIGH | 1 (high) |
| MEDIUM | 2 (medium, default) |
| LOW | 3 (low) or 4 (backlog) |

## CLI Command Reference

### Issue Operations

```bash
# Create issue
bd create "Title" -d "Description" -p 1 -t task -l "backend,urgent" --json

# Get issue
bd show bd-a1b2 --json

# Update issue
bd update bd-a1b2 --status in_progress --priority 2 --json

# List issues
bd list --status open --priority 1 --label backend --limit 50 --json

# Delete issue
bd delete bd-a1b2 --force
```

### Label Operations

```bash
# Add label to issue
bd label add bd-a1b2 security

# Remove label from issue
bd label remove bd-a1b2 urgent

# List labels on an issue
bd label list bd-a1b2 --json

# List all labels with counts
bd label list-all --json
```

### Project Information

```bash
# Check if database is initialized
bd info --json

# Get version
bd version --json
```

## Adapter Implementation Details

### Key Features

1. **Hash-based IDs**: BEADS uses collision-resistant hash IDs (bd-a1b2) instead of sequential numbers
2. **Git-backed**: All issues stored in `.beads/beads.jsonl` and synced via git
3. **Project-local**: Each repository has its own BEADS database
4. **Dependency tracking**: Supports blocks, related, parent-child, discovered-from relationships
5. **Multi-worker**: Multiple agents/machines can work simultaneously without conflicts

### Limitations

1. **No Teams**: BEADS is project-local, so `list_teams()` returns empty list
2. **No Projects**: Returns synthetic project for current workspace
3. **No First-class Comments**: Comments are appended to issue description with timestamps
4. **No Label Colors**: BEADS labels don't have colors (color field is None)

### JSON Output Format

All commands support `--json` flag for programmatic access.

Example issue JSON:
```json
{
  "id": "bd-a1b2",
  "title": "Fix authentication bug",
  "description": "Details here",
  "status": "open",
  "priority": 1,
  "type": "bug",
  "labels": ["backend", "security"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "assignee": "alice"
}
```

## Usage Examples

### Initialize BEADS for a project:

```python
from task_management import TaskManagementFactory

# Create adapter
adapter = TaskManagementFactory.create(
    adapter_type="beads",
    workspace="/path/to/project"
)

# Test connection
if adapter.test_connection():
    print("BEADS database ready!")
```

### Create and manage issues:

```python
# Create issue
issue = adapter.create_issue(
    title="Implement user authentication",
    description="Add OAuth 2.0 support",
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
    labels=["backend", "security"]
)

# Update status
adapter.update_issue(
    issue.id,
    status=IssueStatus.IN_PROGRESS,
    add_labels=["in-development"]
)

# List ready work
open_issues = adapter.list_issues(
    status=IssueStatus.TODO,
    limit=10
)
```

### Agent workflow:

```python
# Agent checks for work
ready_issues = adapter.list_issues(
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
    limit=5
)

for issue in ready_issues:
    print(f"Ready to work on: {issue.title} ({issue.id})")
    
    # Agent starts work
    adapter.update_issue(issue.id, status=IssueStatus.IN_PROGRESS)
    
    # ... agent performs work ...
    
    # Agent completes work
    adapter.update_issue(issue.id, status=IssueStatus.DONE)
    adapter.create_comment(issue.id, "Completed successfully!")
```

## Integration with Coding Agent Harness

The harness automatically:

1. **Initializes BEADS** on first run (if `TASK_ADAPTER = "beads"`)
2. **Creates project structure** in the workspace
3. **Syncs issues** before/after each agent session
4. **Tracks progress** via issue status updates
5. **Maintains audit trail** through BEADS's built-in versioning

## File Structure

When using BEADS adapter, your project will have:

```
your-project/
├── .beads/
│   ├── beads.jsonl          # Issue data (committed to git)
│   ├── beads.db             # SQLite cache (local only)
│   ├── config.yaml          # BEADS configuration
│   └── README.md            # BEADS documentation
├── .gitattributes           # Git merge driver config
└── your project files...
```

## Best Practices

### 1. **Commit JSONL files to git**
   - `.beads/beads.jsonl` and `.beads/deletions.jsonl` should be tracked
   - `.beads/beads.db` should be in `.gitignore` (local cache only)

### 2. **Use meaningful labels**
   - `backend`, `frontend`, `security`, `performance`, etc.
   - Labels are free-form and help filter issues

### 3. **Set appropriate priorities**
   - 0 (URGENT): Critical bugs, blockers
   - 1 (HIGH): Important features, major bugs
   - 2 (MEDIUM): Normal work (default)
   - 3-4 (LOW): Nice-to-haves, backlog

### 4. **Leverage dependency tracking**
   - Use BEADS's native dependency system for complex workflows
   - Access via `bd link` commands (not yet exposed in adapter)

### 5. **Use types for organization**
   - bug, feature, task, epic, chore
   - Stored in `Issue.metadata['type']`

## Troubleshooting

### "bd: command not found"
```bash
# Verify installation
which bd

# Reinstall if needed
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

### "Database not initialized"
```bash
# Initialize in project root
cd /path/to/project
bd init
```

### "Failed to parse JSON"
- Ensure you're using BEADS v0.20.1+ (hash-based IDs)
- Run `bd version --json` to check

### Git conflicts in beads.jsonl
- BEADS uses custom git merge driver to prevent conflicts
- Ensure merge driver is configured: `git config merge.beads.driver "bd merge %A %O %A %B"`
- Ensure `.gitattributes` has: `.beads/beads.jsonl merge=beads`

## Comparison with Other Adapters

| Feature | BEADS | Linear | GitHub Issues |
|---------|-------|--------|---------------|
| Setup Complexity | Very Low (bd init) | Medium (API key) | Low (gh CLI) |
| Cost | Free | Paid | Free |
| Offline Support | ✅ Yes | ❌ No | ❌ No |
| Multi-agent | ✅ Excellent | ⚠️ API limits | ⚠️ API limits |
| Dependency Tracking | ✅ Built-in | ✅ Built-in | ⚠️ Via labels |
| Git Integration | ✅ Native | ❌ Separate | ⚠️ Via API |
| Query Performance | ✅ Local DB | ⚠️ Network | ⚠️ Network |
| Audit Trail | ✅ Git history | ✅ API logs | ✅ API logs |

## When to Use BEADS

**✅ Good fit when:**
- Working on open source or personal projects
- Need offline capability
- Want git-native issue tracking
- Running multiple agents simultaneously
- Local-first workflow preferred

**❌ Not ideal when:**
- Team already using Linear/GitHub Issues
- Need web UI for human access
- Want tight integration with project management tools
- Require sophisticated reporting/analytics

## References

- **BEADS Repository**: https://github.com/steveyegge/beads
- **BEADS Documentation**: See repo docs/ folder
- **Installation Guide**: https://github.com/steveyegge/beads/blob/main/docs/INSTALLING.md
- **Protected Branches**: https://github.com/steveyegge/beads/blob/main/docs/PROTECTED_BRANCHES.md

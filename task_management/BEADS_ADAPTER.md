# BEADS Adapter Guide

## Overview

The BEADS Adapter provides integration with BEADS task management system using the BEADS CLI (`bd`).

**Note:** This is a template implementation. Actual CLI commands and API structure should be verified against BEADS documentation.

## Prerequisites

1. **Install BEADS CLI:**
   ```bash
   # Installation method depends on BEADS distribution
   # Example (adjust based on actual BEADS CLI):
   npm install -g beads-cli
   # or
   pip install beads-cli
   # or download binary from BEADS website
   ```

2. **Authenticate:**
   ```bash
   bd auth login
   # or
   bd config set-token YOUR_API_TOKEN
   ```

## Configuration

### Environment Variables

```bash
export TASK_ADAPTER_TYPE="beads"
export BEADS_WORKSPACE="my-workspace"  # Optional
```

### Programmatic Usage

```python
from task_management import create_adapter

# Create BEADS adapter
adapter = create_adapter(
    adapter_type="beads",
    workspace="my-workspace"  # Optional
)

# Test connection
if adapter.test_connection():
    print("Connected to BEADS!")
```

## Terminology Mapping

| Generic Term | BEADS Term | CLI Command |
|-------------|------------|-------------|
| Team | Team/Workspace | `bd team list` |
| Project | Project | `bd project list` |
| Issue | Issue/Task | `bd issue list` |
| Label | Label/Tag | `bd label list` |
| Status | Status | `bd issue update --status` |
| Priority | Priority | `bd issue update --priority` |

## Status Values

The adapter assumes BEADS supports these status values:

| Generic Status | BEADS Status |
|---------------|--------------|
| TODO | TODO |
| IN_PROGRESS | IN_PROGRESS |
| DONE | DONE |
| CANCELED | CANCELED |

**Note:** Adjust `STATUS_TO_BEADS` and `BEADS_TO_STATUS` mappings in `beads_adapter.py` based on actual BEADS status values.

## Priority Values

| Generic Priority | BEADS Priority |
|-----------------|----------------|
| URGENT | URGENT |
| HIGH | HIGH |
| MEDIUM | MEDIUM |
| LOW | LOW |

## Adapter Implementation Notes

This adapter is a **template** and makes assumptions about BEADS CLI structure:

### Assumed CLI Commands

```bash
# Teams
bd team list --json

# Projects
bd project create --name "Project Name" --teams "team1,team2" --json
bd project get PROJECT_ID --json
bd project list [--team TEAM_ID] --json

# Labels
bd label create --name "bug" --color "#ff0000" --json
bd label list --json

# Issues
bd issue create --title "Title" --description "Desc" --status TODO --priority HIGH --json
bd issue get ISSUE_ID --json
bd issue update ISSUE_ID --title "New Title" --status DONE --json
bd issue list [--project PROJECT_ID] [--status STATUS] [--labels LABELS] --json

# Comments
bd comment create ISSUE_ID --body "Comment text" --json
bd comment list ISSUE_ID --json

# Auth
bd auth status
```

### Expected JSON Response Structure

The adapter assumes responses like:

```json
{
  "issue": {
    "id": "ISS-123",
    "title": "Issue title",
    "description": "Issue description",
    "status": "IN_PROGRESS",
    "priority": "HIGH",
    "projectId": "PROJ-1",
    "labels": [
      {"id": "LAB-1", "name": "bug", "color": "#ff0000"}
    ],
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-02T00:00:00Z"
  }
}
```

## Customization Required

Before using this adapter in production:

1. **Verify CLI commands:**
   ```bash
   bd --help
   bd issue --help
   ```

2. **Update status mappings** in `beads_adapter.py`:
   ```python
   STATUS_TO_BEADS = {
       IssueStatus.TODO: "YOUR_BEADS_TODO_STATUS",
       IssueStatus.IN_PROGRESS: "YOUR_BEADS_IN_PROGRESS_STATUS",
       # ...
   }
   ```

3. **Update priority mappings:**
   ```python
   PRIORITY_TO_BEADS = {
       IssuePriority.URGENT: "YOUR_BEADS_URGENT_PRIORITY",
       # ...
   }
   ```

4. **Adjust CLI command structure** in methods like `_run_bd()`.

5. **Update JSON parsing** in `_parse_issue_data()` based on actual response structure.

## Common Operations

### Create an Issue

```python
issue = adapter.create_issue(
    title="Implement new feature",
    description="Feature requirements...",
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
    labels=["enhancement"]
)
print(f"Created issue: {issue.id}")
```

### Update Issue Status

```python
adapter.update_issue(
    issue_id="ISS-123",
    status=IssueStatus.IN_PROGRESS
)
```

### List Issues

```python
# All issues in a project
issues = adapter.list_issues(project_id="PROJ-1")

# Filter by status
in_progress = adapter.list_issues(
    status=IssueStatus.IN_PROGRESS,
    limit=50
)

# Filter by labels
bugs = adapter.list_issues(
    labels=["bug"],
    limit=20
)
```

### Add Comments

```python
comment = adapter.create_comment(
    issue_id="ISS-123",
    body="Updated implementation approach based on review."
)
```

## Workspace Support

If BEADS supports workspaces:

```python
# Create adapter for specific workspace
adapter = create_adapter(
    adapter_type="beads",
    workspace="engineering-team"
)
```

The adapter passes `--workspace` flag to all CLI commands.

## Troubleshooting

### CLI Not Found

```bash
# Check if bd is installed
which bd
bd --version

# Install if missing (adjust based on BEADS distribution)
npm install -g beads-cli
```

### Authentication Issues

```bash
# Check auth status
bd auth status

# Re-authenticate
bd auth login
```

### Debugging CLI Calls

Enable debug logging to see actual CLI commands:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# The adapter will log subprocess calls
adapter.create_issue(...)
```

## Development & Testing

### Testing the Adapter

```python
# Test basic connectivity
assert adapter.test_connection()

# Test team listing
teams = adapter.list_teams()
print(f"Found {len(teams)} teams")

# Test issue creation
issue = adapter.create_issue(
    title="Test Issue",
    description="Testing BEADS adapter"
)
assert issue.id is not None
```

### Mocking for Unit Tests

```python
from unittest.mock import patch, MagicMock

def test_create_issue():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout='{"issue": {"id": "ISS-1", "title": "Test"}}',
            returncode=0
        )
        
        adapter = BeadsAdapter()
        issue = adapter.create_issue(title="Test")
        
        assert issue.id == "ISS-1"
        mock_run.assert_called_once()
```

## Next Steps

1. **Verify BEADS CLI documentation** for accurate command structure
2. **Update adapter code** with correct CLI commands and response formats
3. **Test thoroughly** with actual BEADS instance
4. **Configure status/priority mappings** to match your BEADS setup
5. **Report issues** or contribute improvements to the adapter

## Contributing

If you customize this adapter for your BEADS deployment:

1. Document actual CLI commands used
2. Share status/priority mappings
3. Provide example JSON responses
4. Submit improvements via PR

## References

- [Task Management Interface](interface.py) - Generic adapter contract
- [TERMINOLOGY_MAPPING.md](TERMINOLOGY_MAPPING.md) - Cross-platform concepts
- BEADS CLI Documentation - (provide link when available)

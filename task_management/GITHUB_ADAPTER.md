# GitHub Adapter Guide

## Overview

The GitHub Adapter maps GitHub Issues and Projects to the generic task management interface using the GitHub CLI (`gh`).

## Prerequisites

1. **Install GitHub CLI:**
   ```bash
   # macOS
   brew install gh
   
   # Linux
   # See: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
   
   # Windows
   # See: https://github.com/cli/cli#installation
   ```

2. **Authenticate:**
   ```bash
   gh auth login
   ```

## Configuration

### Environment Variables

Set these environment variables to use GitHub adapter:

```bash
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="your-org-or-username"
export GITHUB_REPO="your-repo-name"
```

### Programmatic Usage

```python
from task_management import create_adapter

# Create GitHub adapter
adapter = create_adapter(
    adapter_type="github",
    owner="myorg",
    repo="myrepo"
)

# Test connection
if adapter.test_connection():
    print("Connected to GitHub!")
```

## Terminology Mapping

GitHub's structure is mapped to generic task management concepts:

| Generic Term | GitHub Term | Notes |
|-------------|-------------|-------|
| Team | Repository | A repository represents a "team" context |
| Project | GitHub Project | Uses Projects (v2) for organization |
| Issue | Issue | Direct mapping |
| Label | Label | Direct mapping |
| Status | Issue State + Labels | `open`/`closed` + status labels |
| Priority | Priority Labels | Uses `priority:*` labels |

## Status Management

GitHub only has `open` and `closed` states. The adapter uses labels for precise status tracking:

| Generic Status | GitHub State | Status Label |
|---------------|--------------|--------------|
| TODO | open | `status:todo` |
| IN_PROGRESS | open | `status:in-progress` |
| DONE | closed | `status:done` |
| CANCELED | closed | `status:canceled` |

**Example: Creating an issue in "In Progress" state:**
```python
issue = adapter.create_issue(
    title="Implement feature X",
    description="Details here...",
    status=IssueStatus.IN_PROGRESS,  # Sets state=open + label=status:in-progress
)
```

## Priority Management

The adapter uses standardized priority labels:

| Generic Priority | GitHub Label |
|-----------------|--------------|
| URGENT | `priority:urgent` |
| HIGH | `priority:high` |
| MEDIUM | `priority:medium` |
| LOW | `priority:low` |

**Setup: Create priority labels:**
```bash
gh label create "priority:urgent" --color "d73a4a" --repo yourorg/yourrepo
gh label create "priority:high" --color "ff9800" --repo yourorg/yourrepo
gh label create "priority:medium" --color "ffc107" --repo yourorg/yourrepo
gh label create "priority:low" --color "4caf50" --repo yourorg/yourrepo

gh label create "status:todo" --color "e4e669" --repo yourorg/yourrepo
gh label create "status:in-progress" --color "0366d6" --repo yourorg/yourrepo
gh label create "status:done" --color "28a745" --repo yourorg/yourrepo
gh label create "status:canceled" --color "6c757d" --repo yourorg/yourrepo
```

## Label Management

GitHub labels are used for both built-in (status, priority) and custom categorization:

```python
# Create a custom label
label = adapter.create_label(
    name="bug",
    color="#d73a4a",
    description="Something isn't working"
)

# Create issue with labels
issue = adapter.create_issue(
    title="Fix login bug",
    labels=[label.id]  # Add custom labels
)
```

## Project Management

GitHub Projects (v2) are supported:

```python
# Create a project
project = adapter.create_project(
    name="Q1 Roadmap",
    team_ids=[],  # Not used for GitHub
    description="Q1 2025 feature roadmap"
)

# Note: Linking issues to projects requires additional gh project item-add command
```

## Common Operations

### Create and Track an Issue

```python
# Create issue
issue = adapter.create_issue(
    title="Implement user authentication",
    description="Add OAuth2 support for Google and GitHub",
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
    labels=["enhancement"]
)

# Start work
adapter.update_issue(
    issue.id,
    status=IssueStatus.IN_PROGRESS
)

# Add progress comment
adapter.create_comment(
    issue.id,
    "Completed OAuth2 integration. Testing in progress."
)

# Complete
adapter.update_issue(
    issue.id,
    status=IssueStatus.DONE
)
```

### List Issues by Status

```python
# Get all in-progress issues
in_progress = adapter.list_issues(
    status=IssueStatus.IN_PROGRESS,
    limit=50
)

for issue in in_progress:
    print(f"#{issue.id}: {issue.title}")
```

### Filter by Labels

```python
# Get all high-priority bugs
bugs = adapter.list_issues(
    labels=["bug", "priority:high"],
    limit=20
)
```

## Limitations

1. **No native project linking in issue creation:** GitHub CLI doesn't support adding issues to projects during creation. Use `gh project item-add` separately.

2. **Comment IDs:** The adapter may not return precise comment IDs immediately after creation due to CLI limitations.

3. **Rate Limits:** GitHub API has rate limits. For authenticated requests: 5,000 requests/hour.

## Troubleshooting

### `gh: command not found`
```bash
# Install GitHub CLI first
brew install gh  # macOS
```

### Authentication errors
```bash
# Re-authenticate
gh auth login

# Check status
gh auth status
```

### Permission errors
Ensure your GitHub token has these scopes:
- `repo` (full repository access)
- `project` (project access)

## Advanced: Direct CLI Usage

The adapter wraps these `gh` commands:

```bash
# List issues
gh issue list --repo OWNER/REPO --json number,title,state,labels

# Create issue
gh issue create --repo OWNER/REPO --title "Title" --body "Description"

# Update issue
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --add-label "status:in-progress"

# Close issue
gh issue close ISSUE_NUMBER --repo OWNER/REPO
```

## Next Steps

- See [TERMINOLOGY_MAPPING.md](TERMINOLOGY_MAPPING.md) for cross-platform concepts
- See [GitHub CLI docs](https://cli.github.com/manual/) for advanced usage

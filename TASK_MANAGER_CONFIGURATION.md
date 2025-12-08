# Task Manager Configuration Guide

This guide explains how to configure different task management adapters in the autonomous coding agent harness.

## Overview

The harness supports multiple task management systems through an adapter pattern:

- **Linear** - Via Linear API (MCP server)
- **GitHub Issues** - Via `gh` CLI
- **BEADS** - Via `bd` CLI

## Configuration Methods

Task manager configuration can be specified in three ways (priority order):

1. **CLI argument**: `--task-adapter <type>`
2. **Config file**: `.autocode-config.json`
3. **Environment variable**: `TASK_ADAPTER_TYPE`
4. **Default**: `linear`

## Linear Adapter

### Requirements

- Linear API key from: https://linear.app/YOUR-TEAM/settings/api
- Environment variable: `LINEAR_API_KEY`

### Configuration

**.autocode-config.json:**
```json
{
  "task_manager": "linear",
  "task_manager_config": {
    "linear": {
      "team_name": "YOUR_TEAM_NAME",
      "project_name": "YOUR_PROJECT_NAME"
    }
  }
}
```

**Environment:**
```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

**CLI:**
```bash
python autocode.py --task-adapter linear
```

### Features

- Full API integration via MCP server
- Rich metadata support (labels, priorities, estimates)
- Sub-issue support
- Custom workflows

## GitHub Adapter

### Requirements

- GitHub CLI (`gh`) installed and authenticated
- Repository owner and name

### Configuration

**.autocode-config.json:**
```json
{
  "task_manager": "github",
  "task_manager_config": {
    "github": {
      "owner": "myorg",
      "repo": "myrepo"
    }
  }
}
```

**Environment:**
```bash
# Authenticate gh CLI first
gh auth login

# Optional: Set via environment variables
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
export TASK_ADAPTER_TYPE="github"
```

**CLI:**
```bash
python autocode.py --task-adapter github
```

### Features

- Uses GitHub Issues for task management
- CLI-based (no API key needed if gh is authenticated)
- Labels map to task states
- Supports comments and assignees

### State Mapping

| Generic State | GitHub Implementation |
|--------------|----------------------|
| Backlog | Open issue with label: `status: backlog` |
| Todo | Open issue with label: `status: todo` |
| In Progress | Open issue with label: `status: in-progress` |
| Awaiting Audit | Open issue with label: `status: awaiting-audit` |
| Done | Closed issue with label: `status: done` |
| Audited | Closed issue with label: `status: audited` |

## BEADS Adapter

### Requirements

- BEADS CLI (`bd`) installed and configured
- Optional: workspace ID

### Configuration

**.autocode-config.json:**
```json
{
  "task_manager": "beads",
  "task_manager_config": {
    "beads": {
      "workspace": "my-workspace"
    }
  }
}
```

**Environment:**
```bash
# Authenticate bd CLI first
bd auth login

# Optional: Set workspace via environment
export BEADS_WORKSPACE="my-workspace"
export TASK_ADAPTER_TYPE="beads"
```

**CLI:**
```bash
python autocode.py --task-adapter beads
```

### Features

- Uses BEADS CLI for task management
- File-based task tracking
- Git integration
- Lightweight and local-first

### State Mapping

| Generic State | BEADS Implementation |
|--------------|---------------------|
| Backlog | `bd list --status backlog` |
| Todo | `bd list --status todo` |
| In Progress | `bd list --status doing` |
| Awaiting Audit | `bd list --status review` |
| Done | `bd list --status done` |

## Complete Configuration Example

**.autocode-config.json:**
```json
{
  "spec_file": "prompts/app_spec.txt",
  
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  
  "max_iterations": null,
  
  "task_manager": "linear",
  
  "task_manager_config": {
    "linear": {
      "team_name": "Engineering",
      "project_name": "Mobile App Rewrite"
    },
    "github": {
      "owner": "mycompany",
      "repo": "mobile-app"
    },
    "beads": {
      "workspace": "mobile-rewrite"
    }
  }
}
```

## Switching Between Adapters

You can switch adapters without changing the config file:

```bash
# Use Linear (from config file)
python autocode.py

# Override to use GitHub
python autocode.py --task-adapter github

# Override to use BEADS
python autocode.py --task-adapter beads
```

## Generic Task States

All adapters implement the same generic state machine:

```
Backlog → Todo → In Progress → Awaiting Audit → Audited
                      ↓
                   Done (if no audit needed)
```

Additional states:
- **Has Bugs** - Features with audit findings
- **Fix** - Bug fix tasks created by auditor

## Troubleshooting

### Linear Issues

**Problem**: `LINEAR_API_KEY environment variable not set`

**Solution**:
```bash
# Get API key from Linear
open "https://linear.app/YOUR-TEAM/settings/api"

# Set environment variable
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

### GitHub Issues

**Problem**: `GitHub adapter requires 'owner' and 'repo' in task_manager_config`

**Solution**: Add to `.autocode-config.json`:
```json
{
  "task_manager_config": {
    "github": {
      "owner": "your-org",
      "repo": "your-repo"
    }
  }
}
```

**Problem**: `gh: command not found`

**Solution**:
```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login
```

### BEADS Issues

**Problem**: `bd: command not found`

**Solution**:
```bash
# Install BEADS CLI
# See: https://github.com/steveyegge/beads

# Authenticate
bd auth login
```

## Adapter Comparison

| Feature | Linear | GitHub | BEADS |
|---------|--------|--------|-------|
| Authentication | API Key | gh CLI | bd CLI |
| API Integration | Yes (MCP) | No (CLI) | No (CLI) |
| Rich Metadata | ✅ Full | ⚠️ Limited | ⚠️ Basic |
| Sub-tasks | ✅ Yes | ❌ No | ⚠️ Via hierarchy |
| Offline Support | ❌ No | ❌ No | ✅ Yes |
| Cost | Free/Paid | Free | Free |
| Setup Complexity | Medium | Low | Low |

## Future Adapters

Planned support:
- **Jira** - Via Jira API
- **Asana** - Via Asana API
- **Trello** - Via Trello API
- **ClickUp** - Via ClickUp API

## Creating Custom Adapters

To add a new adapter:

1. Implement `TaskManagementAdapter` interface in `task_management/`
2. Add to `factory.py`
3. Update this documentation
4. Create adapter-specific docs (see `BEADS_ADAPTER.md`, `GITHUB_ADAPTER.md`)

See `task_management/README.md` for detailed adapter development guide.

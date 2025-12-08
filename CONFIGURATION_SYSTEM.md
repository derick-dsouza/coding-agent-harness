# Configuration System Documentation

## Overview

The autonomous coding agent harness uses a flexible configuration system that supports:

1. **Multiple models** - Different Claude models for initialization, coding, and audit
2. **Multiple task managers** - Linear, GitHub, BEADS adapters
3. **Multiple configuration sources** - CLI, config file, environment variables

## Configuration Priority

```
CLI Arguments > Config File (.autocode-config.json) > Environment Variables > Defaults
```

## Configuration File Format

### Minimal Configuration

```json
{
  "spec_file": "prompts/app_spec.txt",
  "model": "claude-opus-4-5-20251101"
}
```

### Multi-Model Configuration

```json
{
  "spec_file": "prompts/app_spec.txt",
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101"
}
```

### Full Configuration with Task Manager

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
      "project_name": "Mobile App"
    },
    "github": {
      "owner": "myorg",
      "repo": "myrepo"
    },
    "beads": {
      "workspace": "my-workspace"
    }
  }
}
```

## Configuration Options

### Model Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `claude-opus-4-5-20251101` | Single model for all sessions (overrides all below) |
| `initializer_model` | string | `claude-opus-4-5-20251101` | Model for initialization session |
| `coding_model` | string | `claude-sonnet-4-5-20250929` | Model for coding sessions |
| `audit_model` | string | `claude-opus-4-5-20251101` | Model for audit sessions |

**Model Options:**
- `claude-opus-4-5-20251101` - Highest quality, slowest, most expensive
- `claude-sonnet-4-5-20250929` - Balanced quality/speed/cost
- `claude-haiku-4-20250514` - Fastest, cheapest, lighter tasks only

**Recommended Configurations:**

| Strategy | Init | Code | Audit | Cost Savings | Quality |
|----------|------|------|-------|--------------|---------|
| Premium | Opus | Opus | Opus | 0% | ⭐⭐⭐⭐⭐ |
| Recommended | Opus | Sonnet | Opus | ~65% | ⭐⭐⭐⭐⭐ |
| Balanced | Opus | Sonnet | Sonnet | ~75% | ⭐⭐⭐⭐ |
| Maximum Savings | Opus | Haiku | Sonnet | ~85% | ⭐⭐⭐⭐ |

### Task Manager Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `task_manager` | string | `linear` | Task management adapter to use |
| `task_manager_config` | object | `{}` | Adapter-specific configuration |

**Supported Adapters:**
- `linear` - Linear.app via MCP server
- `github` - GitHub Issues via `gh` CLI
- `beads` - BEADS via `bd` CLI

### General Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `spec_file` | string | `app_spec.txt` | Path to specification file (relative to project dir) |
| `max_iterations` | int/null | `null` | Maximum agent iterations (null = unlimited) |

## CLI Arguments

All configuration options can be overridden via CLI:

```bash
# Model configuration
python autocode.py --model claude-opus-4-5-20251101
python autocode.py \
  --initializer-model claude-opus-4-5-20251101 \
  --coding-model claude-sonnet-4-5-20250929 \
  --audit-model claude-opus-4-5-20251101

# Task manager
python autocode.py --task-adapter linear
python autocode.py --task-adapter github
python autocode.py --task-adapter beads

# General options
python autocode.py --spec-file my_spec.txt
python autocode.py --max-iterations 10
python autocode.py --project-dir /path/to/project
```

## Environment Variables

### Required

```bash
# Claude Code authentication
export CLAUDE_CODE_OAUTH_TOKEN="your-token-here"
```

### Task Manager Specific

**Linear:**
```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

**GitHub:**
```bash
# Authenticate gh CLI (one-time setup)
gh auth login

# Optional: Set via environment variables
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
```

**BEADS:**
```bash
# Authenticate bd CLI (one-time setup)
bd auth login

# Optional: Set workspace
export BEADS_WORKSPACE="my-workspace"
```

### Optional

```bash
# Override task manager selection
export TASK_ADAPTER_TYPE="linear"  # or "github" or "beads"
```

## Configuration Resolution Logic

### Model Selection

1. If `--model` CLI arg → use for all sessions
2. Else if `model` in config → use for all sessions
3. Else resolve each individually:
   - Check `--{type}-model` CLI arg
   - Check `{type}_model` in config
   - Check `model` in config (fallback)
   - Use default for that type

### Task Manager Selection

1. Check `--task-adapter` CLI arg
2. Check `task_manager` in config file
3. Check `TASK_ADAPTER_TYPE` environment variable
4. Use default: `linear`

### Task Manager Config

- Always loaded from config file's `task_manager_config` section
- Can be overridden by environment variables (e.g., `GITHUB_OWNER`)
- Required fields validated on startup

## Examples

### Example 1: Development Environment

**Goal**: Fast iteration with Linear tasks

**.autocode-config.json:**
```json
{
  "spec_file": "dev_spec.txt",
  "model": "claude-sonnet-4-5-20250929",
  "max_iterations": 5,
  "task_manager": "linear",
  "task_manager_config": {
    "linear": {
      "team_name": "Dev",
      "project_name": "Prototype"
    }
  }
}
```

**Environment:**
```bash
export CLAUDE_CODE_OAUTH_TOKEN="..."
export LINEAR_API_KEY="lin_api_..."
```

**Run:**
```bash
python autocode.py
```

### Example 2: Production with Quality Audit

**Goal**: High quality with cost optimization

**.autocode-config.json:**
```json
{
  "spec_file": "production_spec.yaml",
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  "task_manager": "github",
  "task_manager_config": {
    "github": {
      "owner": "mycompany",
      "repo": "production-app"
    }
  }
}
```

**Environment:**
```bash
export CLAUDE_CODE_OAUTH_TOKEN="..."
gh auth login  # One-time setup
```

**Run:**
```bash
python autocode.py
```

### Example 3: Open Source Project with BEADS

**Goal**: Local-first task tracking

**.autocode-config.json:**
```json
{
  "spec_file": "README.md",
  "coding_model": "claude-sonnet-4-5-20250929",
  "task_manager": "beads"
}
```

**Environment:**
```bash
export CLAUDE_CODE_OAUTH_TOKEN="..."
bd auth login  # One-time setup
```

**Run:**
```bash
python autocode.py
```

### Example 4: Multi-Project Workspace

**Goal**: Same config, different task managers per project

**.autocode-config.json (shared):**
```json
{
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "task_manager_config": {
    "linear": {
      "team_name": "Engineering",
      "project_name": "Various"
    },
    "github": {
      "owner": "myorg",
      "repo": "current-project"
    }
  }
}
```

**Usage:**
```bash
# Project A uses Linear
cd project-a
python autocode.py --task-adapter linear --spec-file spec_a.txt

# Project B uses GitHub
cd project-b
python autocode.py --task-adapter github --spec-file spec_b.txt
```

## Validation and Debugging

### Check Configuration

```bash
# Dry run to see resolved configuration
python autocode.py --help

# Python validation
python -c "
import json
with open('.autocode-config.json') as f:
    config = json.load(f)
print('Valid JSON:', list(config.keys()))
"
```

### Common Issues

**Problem**: Model not found

```
Error: Model 'claude-opus-3' not recognized
```

**Solution**: Use full model IDs:
- `claude-opus-4-5-20251101`
- `claude-sonnet-4-5-20250929`
- `claude-haiku-4-20250514`

**Problem**: Task manager config missing

```
Error: GitHub adapter requires 'owner' and 'repo' in task_manager_config
```

**Solution**: Add to config file:
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

**Problem**: Spec file not found

```
Error: Spec file not found: /path/to/app_spec.txt
```

**Solution**: 
1. Create the spec file in project directory
2. Update `spec_file` in config
3. Use `--spec-file` to override

## Best Practices

### 1. Use Multi-Model Strategy

✅ **Recommended:**
```json
{
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101"
}
```

Saves ~65% cost while maintaining quality.

### 2. Keep Sensitive Data in Environment

❌ **Don't:**
```json
{
  "linear_api_key": "lin_api_secret123"
}
```

✅ **Do:**
```bash
export LINEAR_API_KEY="lin_api_secret123"
```

### 3. Version Control Config File

✅ **Commit:**
```
.autocode-config.json (with placeholder values)
.autocode-config.example.json
```

❌ **Don't commit:**
```
.autocode-config.json (with real API keys)
```

### 4. Document Team Configuration

Create `SETUP.md` in your repo:
```markdown
# Agent Setup

1. Copy example config:
   cp .autocode-config.example.json .autocode-config.json

2. Update task_manager_config:
   - Linear: team_name, project_name
   - GitHub: owner, repo

3. Set environment:
   export CLAUDE_CODE_OAUTH_TOKEN="..."
   export LINEAR_API_KEY="..."

4. Run:
   python autocode.py
```

## Related Documentation

- [Task Manager Configuration](TASK_MANAGER_CONFIGURATION.md) - Detailed adapter setup
- [Audit System](AUDIT_SYSTEM.md) - Audit model configuration
- [Task Adapter Architecture](TASK_ADAPTER_ARCHITECTURE.md) - Adapter implementation details
- [README](README.md) - General usage

## See Also

- `.autocode-config.example.json` - Full example configuration
- `autocode.py` - Implementation of config loading
- `task_management/` - Adapter implementations

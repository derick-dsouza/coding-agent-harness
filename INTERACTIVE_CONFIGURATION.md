# Interactive Configuration System

## Overview

The `autocode.py` harness includes an interactive first-time setup wizard that makes it easy to configure your coding agent environment. When you run `autocode.py` for the first time in a directory without a `.autocode-config.json` file and without CLI arguments, the wizard automatically launches.

## Features

### Automatic Detection
- Detects first-time setup (no `.autocode-config.json` exists)
- Only launches if no CLI arguments are provided
- Skips wizard if configuration already exists

### Interactive Prompts
1. **Task Adapter Selection**: Choose between Linear, GitHub Issues, or BEADS
2. **Adapter Configuration**: Provide adapter-specific settings (team name, repo, etc.)
3. **Model Selection**: Choose Claude models for three different roles:
   - **Initializer**: High-quality planning and task breakdown (default: Opus)
   - **Coding**: Implementation work (default: Sonnet)
   - **Audit**: Quality review and verification (default: Opus)

### Smart Defaults
- Reads from `autocode-defaults.json` for sensible defaults
- Recommends best practices (Opus for planning/audit, Sonnet for coding)
- Shows availability status for CLI tools (gh, bd)
- Warns about missing API keys

### Validation
- Checks if CLI tools are available in PATH
- Validates adapter-specific requirements
- Confirms configuration before saving

## Usage

### First-Time Setup

Simply run autocode in a new project directory:

```bash
cd /path/to/my-new-project
python /path/to/autocode.py
```

The wizard will guide you through:

```
======================================================================
AUTOCODE FIRST-TIME SETUP
======================================================================

Project directory: /path/to/my-new-project

This wizard will help you configure autocode for this project.

======================================================================
TASK MANAGEMENT ADAPTER SELECTION
======================================================================

Select task management adapter:
  1. Linear - Linear project management (requires Linear API key) [✓ Available (⚠ LINEAR_API_KEY not set)]
  2. GitHub Issues - GitHub Issues for task management (requires gh CLI) [✓ Available]
  3. BEADS - BEADS local task management (requires bd CLI) [✗ Not available ('bd' not found in PATH)]

Enter choice [1-3] (default: 1): 2

GitHub Issues Configuration:
----------------------------------------------------------------------
Enter GitHub organization/owner: my-org
Enter repository name: my-repo

✓ GitHub CLI (gh) is installed.
  Make sure you're authenticated: gh auth login

======================================================================
MODEL SELECTION
======================================================================

Claude models available:
  • Opus: claude-opus-4-5-20251101
  • Sonnet: claude-sonnet-4-5-20250929
  • Haiku: claude-haiku-4-5-20250929

Recommended configuration:
  • Initializer: Opus (high-quality planning and task breakdown)
  • Coding: Sonnet (balanced quality and speed for implementation)
  • Audit: Opus (thorough review and quality assurance)

Select initializer model (task planning and breakdown):
  1. opus (default)
  2. sonnet
  3. haiku

Enter choice [1-3] (default: 1): 

Select coding model (implementation):
  1. opus
  2. sonnet (default)
  3. haiku

Enter choice [1-3] (default: 2): 

Select audit model (quality review):
  1. opus (default)
  2. sonnet
  3. haiku

Enter choice [1-3] (default: 1): 

======================================================================
CONFIGURATION SUMMARY
======================================================================
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "github",
  "task_adapter_config": {
    "github": {
      "owner": "my-org",
      "repo": "my-repo"
    }
  },
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}

Save this configuration? [Y/n]: y

✓ Configuration saved to /path/to/my-new-project/.autocode-config.json

You can edit this file directly or re-run the wizard anytime.

Next steps:
  1. Create your app_spec.txt file (or use --spec-file to specify another)
  2. Run: python autocode.py
```

### Re-running the Wizard

To re-run the wizard on an existing project, simply delete `.autocode-config.json`:

```bash
rm .autocode-config.json
python /path/to/autocode.py
```

Or run the wizard directly:

```bash
python /path/to/config_wizard.py
```

### Skipping the Wizard

If you want to skip the wizard and use defaults or CLI arguments:

```bash
# Provide any CLI argument to skip wizard
python autocode.py --spec-file my_spec.txt

# Or provide model selection
python autocode.py --model claude-opus-4-5-20251101

# Or provide task adapter
python autocode.py --task-adapter linear
```

## Configuration File Structure

The wizard creates a `.autocode-config.json` file:

```json
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "github",
  "task_adapter_config": {
    "github": {
      "owner": "my-org",
      "repo": "my-repo"
    }
  },
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}
```

### Key Fields

- **agent_sdk**: The agent SDK to use (currently only `claude-agent-sdk`)
- **task_adapter**: Which task management system to use (`linear`, `github`, `beads`)
- **task_adapter_config**: Adapter-specific configuration
- **initializer_model**: Model for planning and task breakdown
- **coding_model**: Model for implementation work
- **audit_model**: Model for quality review
- **spec_file**: Path to specification file (relative to project directory)
- **max_iterations**: Optional limit on iterations (null = unlimited)

## Defaults File

The `autocode-defaults.json` file contains system-wide defaults:

```json
{
  "agent_sdk": "claude-agent-sdk",
  "models": {
    "claude": {
      "opus": "claude-opus-4-5-20251101",
      "sonnet": "claude-sonnet-4-5-20250929",
      "haiku": "claude-haiku-4-5-20250929"
    }
  },
  "task_adapters": {
    "linear": {
      "name": "Linear",
      "description": "Linear project management (requires Linear API key)",
      "cli_command": null,
      "requires_api_key": true
    },
    "github": {
      "name": "GitHub Issues",
      "description": "GitHub Issues for task management (requires gh CLI)",
      "cli_command": "gh",
      "requires_api_key": false
    },
    "beads": {
      "name": "BEADS",
      "description": "BEADS local task management (requires bd CLI)",
      "cli_command": "bd",
      "requires_api_key": false
    }
  },
  "defaults": {
    "initializer_model": "opus",
    "coding_model": "sonnet",
    "audit_model": "opus",
    "task_adapter": "linear",
    "max_iterations": null
  }
}
```

This file:
- Maps friendly model names (`opus`, `sonnet`, `haiku`) to actual model IDs
- Defines available task adapters with metadata
- Sets recommended defaults
- **Should not be modified by users** (lives alongside autocode.py)

## Model Name Mapping

The wizard uses friendly names that map to actual Claude model IDs:

| Friendly Name | Actual Model ID |
|--------------|----------------|
| `opus` | `claude-opus-4-5-20251101` |
| `sonnet` | `claude-sonnet-4-5-20250929` |
| `haiku` | `claude-haiku-4-5-20250929` |

This abstraction:
- Makes configuration easier to read and write
- Allows updating model versions without changing configs
- Provides room for future model provider expansion (OpenAI, Google, etc.)

## Task Adapter Detection

The wizard intelligently detects available task adapters:

### Linear
- **Detection**: Checks for `LINEAR_API_KEY` environment variable
- **Warning**: Shows warning if API key is not set
- **Configuration**: Prompts for team name and project name

### GitHub
- **Detection**: Checks if `gh` CLI is in PATH
- **Validation**: Reminds user to authenticate (`gh auth login`)
- **Configuration**: Prompts for owner and repo

### BEADS
- **Detection**: Checks if `bd` CLI is in PATH
- **Status**: Shows "Not available" if CLI not found
- **Configuration**: Prompts for workspace ID (defaults to "default")

## Configuration Priority

The system follows this priority (highest to lowest):

1. **CLI arguments** (e.g., `--model`, `--task-adapter`)
2. **`.autocode-config.json`** (per-project configuration)
3. **Defaults from wizard** (saved to `.autocode-config.json`)
4. **Hardcoded defaults** (in `autocode.py`)

## Examples

### Example 1: Linear with Recommended Models

```bash
$ cd my-project
$ python /path/to/autocode.py

# Select Linear, provide team/project
# Select opus, sonnet, opus for models
# Creates:
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "linear",
  "task_adapter_config": {
    "linear": {
      "team_name": "engineering",
      "project_name": "web-app"
    }
  },
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}
```

### Example 2: GitHub with Cost-Optimized Models

```bash
$ cd my-project
$ python /path/to/autocode.py

# Select GitHub, provide owner/repo
# Select opus, sonnet, sonnet for models
# Creates:
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "github",
  "task_adapter_config": {
    "github": {
      "owner": "acme-corp",
      "repo": "api-server"
    }
  },
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-sonnet-4-5-20250929",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}
```

### Example 3: BEADS with Maximum Savings

```bash
$ cd my-project
$ python /path/to/autocode.py

# Select BEADS, provide workspace
# Select opus, haiku, sonnet for models
# Creates:
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "beads",
  "task_adapter_config": {
    "beads": {
      "workspace": "default"
    }
  },
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-haiku-4-5-20250929",
  "audit_model": "claude-sonnet-4-5-20250929",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}
```

## Future Extensions

The system is designed to support:

### Additional Model Providers
```json
{
  "models": {
    "claude": { ... },
    "openai": {
      "gpt4": "gpt-4-turbo-preview",
      "gpt35": "gpt-3.5-turbo"
    },
    "google": {
      "gemini-pro": "gemini-pro-1.5",
      "gemini-flash": "gemini-flash-1.5"
    }
  }
}
```

### Additional Task Adapters
```json
{
  "task_adapters": {
    "jira": { ... },
    "asana": { ... },
    "trello": { ... }
  }
}
```

### Per-Adapter Model Preferences
```json
{
  "task_adapter": "github",
  "github_model_override": {
    "coding_model": "claude-haiku-4-5-20250929"
  }
}
```

## Troubleshooting

### Wizard doesn't launch
- Check that `.autocode-config.json` doesn't already exist
- Ensure you're not passing any CLI arguments
- Verify you're running from the correct directory

### CLI tool not detected
- Ensure the tool is installed and in your PATH
- For `gh`: `brew install gh` or https://cli.github.com/
- For `bd`: https://github.com/steveyegge/beads

### API key warnings
- Linear: Set `LINEAR_API_KEY` environment variable
- GitHub: Run `gh auth login` to authenticate
- BEADS: No API key required

### Configuration not taking effect
- Check configuration priority (CLI > config > defaults)
- Verify JSON syntax in `.autocode-config.json`
- Check for typos in model names or adapter types

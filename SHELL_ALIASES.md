# Shell Aliases for Coding Agent Harness

The following aliases have been added to your `~/.zshrc`:

## Quick Commands

### `autocode` or `code-agent-update`
**Detect spec changes AND run the coding agent**

```bash
autocode
# or
code-agent-update
```

Both commands do the same thing - your main command! Use this after editing `prompts/app_spec.txt`.

**What it does:**
- Activates the virtual environment
- Navigates to the harness directory
- Copies spec to project directory
- Detects spec changes
- Creates Linear issues for gaps
- Runs coding agent to implement

Equivalent to:
```bash
source /Users/derickdsouza/Projects/development/coding-agent-harness/.venv/bin/activate
cd /Users/derickdsouza/Projects/development/coding-agent-harness
./work-on-project.sh both
```

### `code-agent-detect`
**Only detect spec changes** (don't run agent)

```bash
code-agent-detect
```

Use this to see what issues will be created without running the agent.

**What it does:**
- Activates venv
- Navigates to harness
- Runs spec change detector only

### `code-agent-run`
**Only run the coding agent** (no detection)

```bash
code-agent-run
```

Use this when you've manually created Linear issues or just want to continue work.

**What it does:**
- Activates venv
- Navigates to harness
- Runs coding agent only

### `code-agent-cd`
**Navigate to the harness directory**

```bash
code-agent-cd
```

Equivalent to:
```bash
cd /Users/derickdsouza/Projects/development/coding-agent-harness
```

### `autospec [path]`
**Copy app_spec.txt to specified directory**

```bash
# Copy to current directory
autospec

# Copy to specific directory
autospec /path/to/project
autospec ./my-new-project
```

**What it does:**
- Copies `prompts/app_spec.txt` to target directory
- Defaults to current directory (`.`) if no path specified
- Useful for starting new projects with same spec

## Your Complete Workflow

### Adding New Features (Claude Agent SDK Example)

```bash
# 1. Edit spec (from anywhere)
vim ~/Projects/development/coding-agent-harness/prompts/app_spec.txt

# 2. Run update (from anywhere - venv activation automatic!)
autocode

# That's it! Watch Linear for progress:
# https://linear.app/derickdsouza/project/claudeai-clone-ai-chat-interface-ff80cbd668d0
```

### Just Want to Continue Working

```bash
# If you already have TODO issues in Linear, just run:
code-agent-run
```

### Preview What Will Change

```bash
# See what issues will be created without running agent:
code-agent-detect
```

## Activation

The aliases are now in `~/.zshrc`. To activate them:

**Option 1: Reload your shell**
```bash
source ~/.zshrc
```

**Option 2: Open a new terminal tab/window**
(Aliases will be available automatically)

## Quick Test

```bash
# Test that the alias works
code-agent-cd && pwd
# Should output: /Users/derickdsouza/Projects/development/coding-agent-harness
```

## Summary

| Alias | What It Does |
|-------|--------------|
| `autocode` | 🎯 **Main command** - Points to code-agent-update |
| `code-agent-update` | 🎯 **Detect + Run** (venv activated automatically) |
| `code-agent-detect` | 🔍 Detect changes only (venv activated) |
| `code-agent-run` | 🤖 Run agent only (venv activated) |
| `code-agent-cd` | 📂 Navigate to harness |
| `autospec [path]` | 📋 Copy spec to directory (defaults to `.`) |

**Most common usage:** `autocode` or `code-agent-update` after editing `prompts/app_spec.txt`

**Key benefit:** No need to manually activate venv or navigate to directories!

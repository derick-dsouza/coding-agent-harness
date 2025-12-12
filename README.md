# Autonomous Coding Agent Demo (Task Management Integrated)

A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a two-agent pattern (initializer + coding agent) with **pluggable task management** (Linear, GitHub Issues, BEADS) for tracking all work.

## Key Features

- **Multi-Platform Task Management**: Support for Linear, GitHub Issues, BEADS (adapter pattern)
- **Agent SDK Adapter Layer**: Mix and match Factory Droid, Aider, OpenCode, OpenAI Codex CLI, Gemini CLI, Mistral, and Claude per session type
- **Real-time Visibility**: Watch agent progress in your task management system
- **Session Handoff**: Agents communicate via issue comments, not text files
- **Two-Agent Pattern**: Initializer creates project & issues, coding agents implement them
- **Browser Testing**: Puppeteer MCP for UI verification
- **Configurable Models**: Use different Claude models for initialization, coding, and auditing
- **CLI-First**: GitHub and BEADS adapters use CLI tools (no API keys needed)

## Prerequisites

### 1. Install Claude Code CLI and Python SDK

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Authentication

You need authentication for Claude Code and your chosen task management platform:

**Claude Code OAuth Token:**
```bash
# Generate the token using Claude Code CLI
claude setup-token

# Set the environment variable
export CLAUDE_CODE_OAUTH_TOKEN='your-oauth-token-here'
```

**Task Management Platform (choose one):**

**Option 1: Linear (API-based)**
```bash
# Get your API key from: https://linear.app/YOUR-TEAM/settings/api
export TASK_ADAPTER_TYPE="linear"
export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'
```

**Option 2: GitHub Issues (CLI-based, no API key needed)**
```bash
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="your-org"
export GITHUB_REPO="your-repo"

# Authenticate GitHub CLI
brew install gh  # macOS
gh auth login
```

**Option 3: BEADS (CLI-based, no API key needed)**
```bash
export TASK_ADAPTER_TYPE="beads"
export BEADS_WORKSPACE="your-workspace"  # Optional

# Install and authenticate BEADS CLI
# (Installation method depends on BEADS distribution)
bd auth login
```

### 3. Verify Installation

```bash
claude --version  # Should be latest version
pip show claude-code-sdk  # Check SDK is installed
```

## Quick Start

```bash
python autonomous_agent_demo.py --project-dir ./my_project
```

For testing with limited iterations:
```bash
python autonomous_agent_demo.py --project-dir ./my_project --max-iterations 3
```

### Agent SDK Selection (Mix & Match)

- Default SDK comes from `autocode-defaults.json` (`claude-agent-sdk`), override with `--agent-sdk`
- Use `--initializer-sdk`, `--coding-sdk`, `--audit-sdk` to pick different providers per session
- Supported keys (in registry order): `claude-agent-sdk`, `factory-droid`, `aider`, `opencode`, `openai-codex-cli`, `gemini-cli`, `mistral`
- CLI-based SDKs can run in dry-run mode with `--simulate-agent-sdk` or `AGENT_SDK_SIMULATE=1` (no external CLI needed)

## How It Works

### Task Management Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│              TASK MANAGEMENT INTEGRATED WORKFLOW                 │
├──────────────────────────────────────────────────────────────────┤
│  app_spec.* ──► Initializer Agent ──► Issues (50) in System     │
│                    (txt/md/yaml)           │                     │
│                                            │                     │
│                    ┌───────────────────────▼──────────────┐     │
│                    │    TASK MANAGEMENT SYSTEM            │     │
│                    │    (Linear / GitHub / BEADS)         │     │
│                    │  ┌──────────────────────────────┐    │     │
│                    │  │ Issue: Auth - Login flow     │    │     │
│                    │  │ Status: TODO → IN_PROGRESS   │    │     │
│                    │  │ Priority: HIGH               │    │     │
│                    │  │ Comments: [session notes]    │    │     │
│                    │  └──────────────────────────────┘    │     │
│                    └──────────────────────────────────────┘     │
│                                            │                     │
│                    Coding Agent queries system                   │
│                    ├── Search for TODO issues                    │
│                    ├── Update status to IN_PROGRESS              │
│                    ├── Implement & test with Puppeteer           │
│                    ├── Add comment with implementation notes     │
│                    └── Update status to DONE                     │
└──────────────────────────────────────────────────────────────────┘
```

### Two-Agent Pattern

1. **Initializer Agent (Session 1):**
   - Reads `app_spec.*` (txt, md, yaml)
   - Lists teams and creates a new project
   - Creates 50 issues with detailed test steps
   - Creates a META issue for session tracking
   - Sets up project structure, `init.sh`, and git

2. **Coding Agent (Sessions 2+):**
   - Queries task system for highest-priority TODO issue
   - Runs verification tests on previously completed features
   - Claims issue (status → IN_PROGRESS)
   - Implements the feature
   - Tests via Puppeteer browser automation
   - Marks complete (status → DONE)
   - Updates META issue with session summary

### Session Handoff via Task Management

Instead of local text files, agents communicate through:
- **Issue Comments**: Implementation details, blockers, context
- **META Issue**: Session summaries and handoff notes
- **Issue Status**: TODO / IN_PROGRESS / DONE workflow
- **Labels**: Priority, categorization, and custom tags

## Task Management System

The harness uses a **pluggable adapter pattern** to support multiple task management platforms:

| Platform | Type | Authentication | Documentation |
|----------|------|----------------|---------------|
| **Linear** | MCP/API | API Key | Production-ready |
| **GitHub Issues** | CLI (`gh`) | OAuth | [Guide](task_management/GITHUB_ADAPTER.md) |
| **BEADS** | CLI (`bd`) | Token | [Template](task_management/BEADS_ADAPTER.md) |

### Switching Platforms

Change task management system via environment variable:

```bash
# Use Linear
export TASK_ADAPTER_TYPE="linear"
export LINEAR_API_KEY="lin_api_xxxxx"

# Use GitHub Issues
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"

# Use BEADS
export TASK_ADAPTER_TYPE="beads"
export BEADS_WORKSPACE="workspace-id"
```

See [task_management/README.md](task_management/README.md) for complete documentation.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (from `claude setup-token`) | Yes |
| `TASK_ADAPTER_TYPE` | Task management platform: `linear`, `github`, or `beads` | Yes |
| **Linear-specific** |||
| `LINEAR_API_KEY` | Linear API key for MCP access | If using Linear |
| **GitHub-specific** |||
| `GITHUB_OWNER` | Repository owner (org or user) | If using GitHub |
| `GITHUB_REPO` | Repository name | If using GitHub |
| **BEADS-specific** |||
| `BEADS_WORKSPACE` | Workspace identifier (optional) | If using BEADS |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-opus-4-5-20251101` |

## Project Structure

```
coding-agent-harness/
├── autonomous_agent_demo.py  # Main entry point
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK + MCP client configuration
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── linear_config.py          # Linear configuration constants (legacy)
├── task_management/          # Task management adapter system
│   ├── __init__.py           # Public API
│   ├── interface.py          # Generic interface (TaskManagementAdapter)
│   ├── linear_adapter.py     # Linear implementation (MCP-based)
│   ├── github_adapter.py     # GitHub Issues implementation (CLI-based)
│   ├── beads_adapter.py      # BEADS implementation (CLI-based)
│   ├── factory.py            # Adapter factory
│   ├── README.md             # Full documentation
│   ├── GITHUB_ADAPTER.md     # GitHub-specific guide
│   ├── BEADS_ADAPTER.md      # BEADS-specific guide
│   ├── TERMINOLOGY_MAPPING.md # Cross-platform terminology
│   ├── PROMPT_GUIDELINES.md  # Writing adapter-agnostic prompts
│   └── MIGRATION_PLAN.md     # Migration checklist
├── prompts/
│   ├── app_spec.txt          # Application specification
│   ├── initializer_prompt.md # First session prompt (creates issues)
│   ├── coding_prompt.md      # Continuation session prompt (works issues)
│   └── audit_prompt.md       # Audit session prompt (reviews work)
└── requirements.txt          # Python dependencies
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── .task_project.json        # Task management project state (marker file)
├── app_spec.*                # Copied specification (txt, md, or yaml)
├── init.sh                   # Environment setup script
├── .claude_settings.json     # Security settings
└── [application files]       # Generated application code
```

## MCP Servers Used

| Server | Transport | Purpose | Used By |
|--------|-----------|---------|---------|
| **Linear** | HTTP (Streamable HTTP) | Project management - issues, status, comments | Linear adapter |
| **Puppeteer** | stdio | Browser automation for UI testing | All adapters |

**Note:** GitHub and BEADS adapters use CLI tools (`gh`, `bd`) instead of MCP servers.

## Security Model

This demo uses defense-in-depth security (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to project directory
3. **Bash Allowlist:** Only specific commands permitted (npm, node, git, etc.)
4. **MCP Permissions:** Tools explicitly allowed in security settings

## Linear Setup

Before running, ensure you have:

1. A Linear workspace with at least one team
2. An API key with read/write permissions (from Settings > API)
3. The agent will automatically detect your team and create a project

The initializer agent will create:
- A new Linear project named after your app
- 50 feature issues based on `app_spec.txt`
- 1 META issue for session tracking and handoff

All subsequent coding agents will work from this Linear project.

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adding Features to Existing Project

If you've already completed the initial 50 issues and want to add new features:

**Option 1: Manually create issues in your task management system**
- Go to Linear/GitHub/BEADS and create new issues
- Mark them as TODO with appropriate priority
- The coding agent will pick them up automatically

**Option 2: Use the spec change detector (recommended)**
```bash
# Edit app_spec.txt with your changes
vim prompts/app_spec.txt

# Run the spec change detector
python detect_spec_changes.py --project-dir ./your_project

# The detector will:
# 1. Compare app_spec.txt against existing issues
# 2. Create new issues for any gaps found
# 3. Label them as "spec-change"
# 4. Update the project state

# Then run the coding agent normally
python autonomous_agent_demo.py --project-dir ./your_project
```

### Adjusting Issue Count

Edit `prompts/initializer_prompt.md` and change "50 issues" to your desired count.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"CLAUDE_CODE_OAUTH_TOKEN not set"**
Run `claude setup-token` to generate a token, then export it.

**"LINEAR_API_KEY not set"**
Get your API key from `https://linear.app/YOUR-TEAM/settings/api`

**"Appears to hang on first run"**
Normal behavior. The initializer is creating a Linear project and 50 issues with detailed descriptions. Watch for `[Tool: mcp__linear__create_issue]` output.

**"Command blocked by security hook"**
The agent tried to run a disallowed command. Add it to `ALLOWED_COMMANDS` in `security.py` if needed.

**"MCP server connection failed"**
Verify your `LINEAR_API_KEY` is valid and has appropriate permissions. The Linear MCP server uses HTTP transport at `https://mcp.linear.app/mcp`.

## Viewing Progress

Open your Linear workspace to see:
- The project created by the initializer agent
- All 50 issues organized under the project
- Real-time status changes (Todo → In Progress → Done)
- Implementation comments on each issue
- Session summaries on the META issue

## License

MIT License - see [LICENSE](LICENSE) for details.

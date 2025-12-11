# 🚀 AUTOCODE WORKFLOW DOCUMENTATION

## System Overview

**Autocode** is an autonomous coding agent harness that uses Claude to build complete applications from specifications. It integrates with task management systems (Linear, GitHub, BEADS) and includes automated testing and auditing.

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: INITIALIZATION                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. First-Time Setup (if no .autocode-config.json)             │
│     • Run config_wizard.py                                      │
│     • Select task adapter (Linear/GitHub/BEADS)                 │
│     • Configure API keys                                        │
│     • Select Claude models (initializer/coding/audit)           │
│     • Set project directory and spec file                       │
│     • Create .autocode-config.json                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Load Configuration                                          │
│     • Read .autocode-config.json                                │
│     • Load spec_file (app_spec.txt)                             │
│     • Initialize task adapter                                   │
│     • Set security restrictions                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Check for Existing Project                                  │
│     • Look for .task_project.json                               │
│     • If exists → Continue existing project                     │
│     • If not → Run Initializer Session                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
         ┌─────────────────┐   ┌──────────────────┐
         │   NEW PROJECT   │   │ EXISTING PROJECT │
         └─────────────────┘   └──────────────────┘
                    │                   │
                    │                   └──────────┐
                    ▼                              │
┌─────────────────────────────────────────────────│────────────────┐
│            PHASE 2: INITIALIZER SESSION         │                │
└─────────────────────────────────────────────────│────────────────┘
                    │                              │
                    ▼                              │
┌─────────────────────────────────────────────────│────────────────┐
│  4. Initializer Agent (High-Quality Model)      │                │
│     • Analyze app_spec.txt                      │                │
│     • Break down into features/issues           │                │
│     • Create detailed task descriptions         │                │
│     • Determine dependencies                    │                │
│     • Create issues in task system              │                │
│     • Save to .task_project.json                │                │
└─────────────────────────────────────────────────│────────────────┘
                    │                              │
                    └──────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 3: MAIN CODING LOOP                      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Spec Change Detection (detect_spec_changes.py)              │
│     • Compare current app_spec.txt with previous hash            │
│     • If changed → Trigger initializer to create new issues     │
│     • Update spec_hash in .task_project.json                    │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Query Task System (with Caching)                            │
│     • Check linear_cache.db for recent data                     │
│     • If cache valid (TTL) → Use cached data                    │
│     • If cache expired → Query Linear API                       │
│     • Update cache with new data                                │
│     • Get Todo/In Progress/Done counts                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌────────┴────────┐
                          │   Has Issues?   │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌─────────────┐              ┌──────────────┐
            │     YES     │              │      NO      │
            └─────────────┘              └──────────────┘
                    │                             │
                    │                             ▼
                    │              ┌─────────────────────────┐
                    │              │  Skip to Phase 5: Audit │
                    │              └─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Coding Agent Session (Cost-Effective Model)                 │
│     • Create restricted environment (.claude_settings.json)     │
│     • Filesystem restricted to project directory                │
│     • Bash commands restricted to allowlist                     │
│     • Load MCP servers (puppeteer, linear)                      │
│     • Send prompt with:                                         │
│       - app_spec.txt content                                    │
│       - Current task status                                     │
│       - Previous session notes                                  │
│       - Available tools/MCPs                                    │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. Agent Execution Loop                                        │
│     Agent can:                                                  │
│     • Read/Write files (restricted to project dir)              │
│     • Run bash commands (allowlist only)                        │
│     • Query Linear (via MCP with caching)                       │
│     • Control browser (via Puppeteer MCP)                       │
│     • Update issue status (Todo→In Progress→Done)               │
│     • Add comments to META issue                                │
│                                                                 │
│     Each iteration:                                             │
│     1. Agent receives tool results                              │
│     2. Agent thinks and decides next action                     │
│     3. Agent calls tools (Read, Write, Bash, MCP)               │
│     4. Tools execute and return results                         │
│     5. Repeat until agent says "AUTOMODE_COMPLETE"              │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. Session Completion                                          │
│     • Agent marks issues as Done                                │
│     • Adds summary comment to META issue                        │
│     • Updates .task_project.json with notes                     │
│     • Increments coding_sessions count                          │
│     • Saves features_completed list                             │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌────────┴────────┐
                          │ Max Iterations? │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌─────────────┐              ┌──────────────┐
            │  Reached    │              │  Not Yet     │
            └─────────────┘              └──────────────┘
                    │                             │
                    │                             │
                    │                 ┌───────────┘
                    │                 │
                    ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 4: AUDIT SESSION                        │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  10. Check if Audit Needed                                      │
│      • Count features marked Done but not audited               │
│      • If count >= 10 → Trigger audit                           │
│      • If audit_mode: "always" → Always audit                   │
│      • If audit_mode: "never" → Skip audit                      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌────────┴────────┐
                          │  Audit Needed?  │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌─────────────┐              ┌──────────────┐
            │     YES     │              │      NO      │
            └─────────────┘              └──────────────┘
                    │                             │
                    │                             ▼
                    │                     ┌──────────────┐
                    │                     │     EXIT     │
                    │                     └──────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  11. Audit Agent Session (High-Quality Model)                   │
│      • Read app_spec.txt                                        │
│      • Query all Done issues                                    │
│      • For each feature:                                        │
│        - Test functionality via Puppeteer                       │
│        - Verify code quality                                    │
│        - Check against spec requirements                        │
│        - Assign grade: PASS/FAIL                                │
│      • Generate audit report                                    │
│      • Update .task_project.json                                │
│      • Add audit summary to META issue                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  12. Audit Results                                              │
│      • Display pass/fail counts                                 │
│      • Show overall grade                                       │
│      • If failures → Issues reopened for fixing                 │
│      • If all pass → Mark features as audited                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌────────┴────────┐
                          │  All Features   │
                          │    Complete?    │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌─────────────┐              ┌──────────────┐
            │     YES     │              │      NO      │
            └─────────────┘              └──────────────┘
                    │                             │
                    │                             │
                    │                 ┌───────────┘
                    │                 │
                    ▼                 ▼
            ┌─────────────┐    ┌──────────────────┐
            │   SUCCESS   │    │ Loop Back to     │
            │   COMPLETE  │    │ Phase 3: Coding  │
            └─────────────┘    └──────────────────┘
```

---

## 📁 Key Files and Their Roles

### Configuration Files
```
.autocode-config.json        → Main configuration (models, adapter, paths)
.task_project.json           → Project state (issues created, sessions run)
.claude_settings.json        → Security restrictions for Claude Agent SDK
linear_cache.db              → SQLite cache for Linear API responses
```

### Core Scripts
```
autocode.py                  → Main orchestrator
config_wizard.py             → Interactive setup
detect_spec_changes.py       → Detect spec changes and trigger initializer
agent.py                     → Claude Agent SDK integration
security.py                  → Security and allowlist management
prompts.py                   → Prompt templates for agents
```

### Task Management
```
task_management/
  ├── adapters/
  │   ├── linear_adapter.py     → Linear API integration
  │   ├── github_adapter.py     → GitHub Issues integration
  │   └── beads_adapter.py      → BEADS local task management
  └── base_adapter.py           → Abstract base for all adapters
```

### Linear Optimization
```
linear_cache.py              → Cache management for Linear API
linear_cache_helpers.py      → Cache query helpers
linear_batch_helper.py       → Batch operations for Linear
linear_tracker.py            → API call tracking and rate limiting
```

### Spec File
```
app_spec.txt                 → Application specification
                               (or prompts/app_spec.txt)
```

---

## 🔧 Usage Workflows

### 1️⃣ Starting a New Project

```bash
# Navigate to your project directory
cd /path/to/your/project

# Copy spec file
autospec

# Or manually:
cp /path/to/coding-agent-harness/prompts/app_spec.txt .

# Edit app_spec.txt with your requirements
vim app_spec.txt

# Run autocode (will trigger setup wizard on first run)
cd /path/to/coding-agent-harness
source .venv/bin/activate
python autocode.py
```

**What happens:**
1. Config wizard asks for task adapter, API keys, models
2. Creates `.autocode-config.json`
3. Initializer agent analyzes spec and creates issues
4. Coding agent starts implementing features
5. Audit agent validates completed features

### 2️⃣ Continuing Existing Project

```bash
# Using alias (if configured)
code-agent-update

# Or manually:
cd /path/to/coding-agent-harness
source .venv/bin/activate
python autocode.py
```

**What happens:**
1. Loads existing `.task_project.json`
2. Checks for spec changes
3. Queries task system (cached)
4. Resumes coding where it left off

### 3️⃣ Adding New Features (Spec Change)

```bash
# Edit spec file in your project
vim app_spec.txt

# Add new features to the spec
# Example:
# """
# NEW FEATURE: User authentication
# - JWT-based login
# - Password reset
# - OAuth integration
# """

# Run autocode
code-agent-update
```

**What happens:**
1. `detect_spec_changes.py` detects file hash changed
2. Triggers initializer agent
3. Initializer creates new issues for new features
4. Coding agent implements new features
5. Audit validates everything

### 4️⃣ Debugging/Manual Intervention

```bash
# Check Linear project status
cd generations/autonomous_demo_project
python -c "from task_management.adapters.linear_adapter import LinearAdapter; \
           adapter = LinearAdapter(); \
           status = adapter.get_project_status(); \
           print(status)"

# Clear cache if stale
rm linear_cache.db

# View cached data
sqlite3 linear_cache.db "SELECT * FROM linear_cache;"

# Check API call count
python linear_tracker.py --stats
```

---

## 🎯 Key Features

### 1. **Spec Change Detection**
- Automatically detects when `app_spec.txt` changes
- Triggers initializer to create new issues
- Allows iterative development

### 2. **Linear API Caching**
- 5-minute TTL for issue queries
- Reduces API calls by ~80%
- Prevents rate limiting

### 3. **Multi-Model Strategy**
- Initializer: High-quality model (Opus) for planning
- Coding: Cost-effective model (Sonnet) for implementation
- Audit: High-quality model (Opus) for validation

### 4. **Security Sandbox**
- Filesystem restricted to project directory
- Bash commands restricted to allowlist
- No network access except MCP servers

### 5. **Task Adapters**
- **Linear**: Full-featured project management
- **GitHub Issues**: Simple, integrated with GitHub
- **BEADS**: Local, offline task management

### 6. **Automated Testing**
- Puppeteer MCP for browser automation
- End-to-end testing of features
- Audit agent validates all functionality

---

## 🚨 Common Issues and Solutions

### Issue: Rate Limited by Linear API
**Solution:** Cache is working. Wait or increase TTL in `linear_cache.py`

### Issue: Agent not detecting spec changes
**Solution:** Check `spec_hash` in `.task_project.json`. Delete if corrupted.

### Issue: Agent keeps testing even when no issues
**Solution:** Check skip logic in `autocode.py`. Should skip if `todo_count == 0`

### Issue: Verbose output cluttering terminal
**Solution:** Use `--verbose` flag to control output level

### Issue: Can't find spec file
**Solution:** Use `autospec` alias or copy manually to project directory

---

## 📊 Progress Tracking

### Check Linear Project
Visit: https://linear.app/your-workspace/your-project

### Check Local Status
```bash
cat .task_project.json | jq
```

### View META Issue
All session notes are added as comments to the META issue in Linear.

---

## 🎓 Best Practices

1. **Write Clear Specs**: Detailed specs → better issues → faster implementation
2. **Use Aliases**: Set up shell aliases for common workflows
3. **Monitor Cache**: Check `linear_cache.db` if data seems stale
4. **Audit Regularly**: Don't skip audits; catch bugs early
5. **Commit Often**: Agent should commit after each feature
6. **Review META Issue**: Read agent's notes to understand decisions

---


# Coding Agent Harness - Session Improvements

## Overview
This document summarizes all improvements made to the coding agent harness system during the December 11-12, 2025 session.

---

## 1. Verbose Flag for Output Control

**Problem**: JSON dumps and tool output cluttered the terminal, making it difficult to read.

**Solution**: Added `--verbose` flag to control output verbosity.

**Files Modified**:
- `agent.py`: Added verbose parameter to agent functions
- `autocode.py`: Added `--verbose` CLI flag

**Impact**: Cleaner console output by default, detailed debugging available when needed.

---

## 2. Command Restrictions Documentation

**Problem**: Agent repeatedly attempted blocked commands (cd, npx, find, sed, etc.), wasting API calls.

**Solution**: Created upfront documentation of blocked commands injected into all prompts.

**Files Created**:
- `prompts/task_adapters/command_restrictions.txt`: Comprehensive list of allowed/blocked commands with workarounds

**Files Modified**:
- `prompts.py`: Updated to inject command restrictions into all prompts

**Benefits**:
- Agent knows restrictions upfront
- Reduces wasted API calls
- Provides workaround guidance
- Improves agent efficiency

**Blocked Commands**:
- Navigation: `cd`
- Package managers: `npx`, `bun`, `yarn`, `pip`
- File search: `find`, `locate`, `which`
- Text processing: `sed`, `awk`, `cut`, `tr`, `sort`, `uniq`
- File operations: `mv`, `rm`, `touch`
- Network: `curl`, `wget`
- Shell: `bash`, `sh`, `exec`
- And many more...

**Workarounds Provided**:
- `cd path && cmd` → `git -C path cmd` or use absolute paths
- `npx tsc` → `npm run <script>` or `node_modules/.bin/tsc`
- `find` → `ls -R` or `grep -r`
- `sed`/`awk` → Use Read/Edit SDK tools
- `curl` → Use MCP web_search or file operations

---

## 3. Task Manager Display Fixes

**Problem**: Console showed "Linear" even when BEADS was configured.

**Solution**: Updated display logic to show correct task manager name.

**Files Modified**:
- `autocode.py`: Fixed task manager status display

**Impact**: Accurate console output reflecting actual configuration.

---

## 4. Project Type Detection

**Problem**: Agent assumed all projects were greenfield, creating init.sh for existing projects.

**Solution**: Added detection logic in initializer prompt.

**Implementation**: Initializer checks app_spec for indicators like:
- "existing project"
- "fix TypeScript errors"
- "refactor"
- Absence of "create new" or "build from scratch"

**Default**: Assumes existing project if unclear (safer assumption).

**Impact**: Agent behaves appropriately for existing vs. new projects.

---

## 5. BEADS Adapter Improvements

**Problem**: BEADS adapter had jq parsing errors and didn't properly handle CLI output.

**Solution**: Fixed JSON parsing and command construction.

**Files Modified**:
- `task_management/beads_adapter.py`: Fixed jq commands and error handling

**Impact**: Reliable BEADS integration for local task management.

---

## 6. Spec Change Detector Independence

**Problem**: Spec detector hardcoded paths to `prompts/` subdirectory.

**Solution**: Made detector work with spec file from working directory.

**Files Modified**:
- `detect_spec_changes.py`: Removed hardcoded prompt paths

**Impact**: Works correctly regardless of directory structure.

---

## 7. Shell Alias Improvements

**Problem**: Aliases didn't activate venv or use correct paths.

**Solution**: Updated aliases to include venv activation and use current directory.

**Aliases Created/Updated**:
- `autocode`: Activates venv, runs autocode.py from current directory
- `autorun` →  `code-agent-update`: Same as autocode (semantic naming)
- `autospec [path]`: Copies app_spec.txt template to target (default: current dir)

**Files Modified**:
- `~/.zshrc`: Updated alias definitions

**Impact**: Easier workflow, works from any project directory.

---

## 8. Demo Project Organization

**Problem**: Config files scattered in main directory mixed with harness code.

**Solution**: Moved demo-specific files to `generations/autonomous_demo_project/`.

**Files Moved**:
- `.autocode-config.json`
- `.task_project.json`
- `prompts/app_spec.txt`

**Impact**: Cleaner separation between harness and demo project.

---

## 9. Improved Completion Detection

**Problem**: Agent thought work was done when open BEADS issues existed.

**Solution**: Fixed completion logic to properly count open BEADS issues.

**Files Modified**:
- `autocode.py`: Updated completion check logic

**Impact**: Agent continues working until truly complete.

---

## 10. Output Formatting Improvements

**Problem**: Tool output ran together without line breaks, difficult to read.

**Solution**: Added line breaks after tool outputs and agent commentary.

**Files Modified**:
- `agent.py`: Added newlines after tool outputs

**Impact**: More readable console output during agent execution.

---

## 11. Workflow Documentation

**Problem**: Users didn't understand the end-to-end workflow.

**Solution**: Created visual workflow diagram.

**Files Created**:
- `WORKFLOW_DIAGRAM.txt`: ASCII art workflow showing all steps

**Sections**:
1. Configuration (wizard)
2. Spec Writing (app_spec.txt)
3. Initialization (issue creation)
4. Coding (implementation loop)
5. Auditing (quality review)
6. Completion

**Impact**: Clear understanding of system workflow.

---

## 12. Adapter Flexibility Documentation

**Problem**: Unclear if workflow works with all task managers.

**Solution**: Documented adapter architecture.

**Key Points**:
- Workflow is task-manager agnostic
- Adapters translate generic calls to specific APIs
- Linear, BEADS, GitHub Issues all supported
- Same workflow regardless of backend

---

## 13. BEADS Auto-Detection

**Problem**: User had to manually select BEADS even when `.beads` directory existed.

**Solution**: Added auto-detection in config wizard.

**Files Modified**:
- `config_wizard.py`: Check for `.beads` directory on startup
- Defaults to BEADS if detected

**Impact**: Seamless experience for BEADS users.

---

## 14. Spec Template System

**Problem**: No template for creating new app_spec.txt files.

**Solution**: Analyzed demo spec and created XML template.

**Files Created**:
- `templates/app_spec_template.xml`: Structured template with all sections

**Template Sections**:
- Project overview
- Core requirements
- Technical stack
- Architecture
- Features (phases with priorities)
- Security requirements
- Testing requirements
- Quality standards

**Rationale for XML**:
- Better structure than plain text
- Hierarchical organization
- AI-friendly (Claude excels at XML)
- Clear section boundaries
- Easier validation

**Impact**: Consistent, high-quality spec files for new projects.

---

## Architecture Insights

### Task Manager Abstraction
The system uses an adapter pattern for task management:
```
Generic API (autocode.py)
    ↓
Task Adapter Interface
    ↓
├── Linear Adapter (API + MCP)
├── BEADS Adapter (CLI + local DB)
└── GitHub Adapter (gh CLI + API)
```

### Prompt Modularization
Prompts are now modular:
```
Base Prompt (coding_prompt.md, initializer_prompt.md)
    +
Task Manager Guide (prompts/task_managers/{adapter}.md)
    +
Command Restrictions (prompts/task_adapters/command_restrictions.txt)
    ↓
Final Prompt (injected at runtime)
```

### Security Model
- Allowlist-based command filtering
- MCP server restrictions per adapter
- Filesystem sandboxing to project directory
- No external network access (except MCP tools)

---

## Key Takeaways

1. **Upfront Information Matters**: Telling agent about restrictions upfront saves many wasted API calls

2. **Adapter Pattern is Powerful**: Single workflow, multiple backends - users choose what works for them

3. **Templates Improve Quality**: Structured templates (XML) lead to better, more consistent specs

4. **Verbosity Control is Essential**: Different users need different output levels

5. **Auto-Detection Improves UX**: System should detect and suggest optimal configuration

6. **Separation of Concerns**: Keep harness code separate from generated projects

---

## Future Improvements

### Potential Enhancements:
1. **Verification System**: Automated testing after each feature implementation
2. **Audit Triggers**: Automatic audit after N features completed
3. **Progress Dashboard**: Web UI showing real-time project status
4. **Multi-Repository Support**: Handle monorepo scenarios
5. **Rollback Capability**: Undo last N issues if audit fails
6. **Performance Metrics**: Track tokens used, time per issue, error rates
7. **Smart Retries**: Exponential backoff for rate limits
8. **Caching**: Cache task manager queries to reduce API calls
9. **Batch Operations**: Group multiple task updates into single API calls

---

## Statistics

### Files Modified: 15+
- Core system files: 8
- Prompt files: 3
- Documentation files: 4

### New Features: 14
- Verbose flag
- Command restrictions
- Task manager display fix
- Project type detection
- BEADS improvements
- Spec detector independence
- Alias improvements
- Demo organization
- Completion detection
- Output formatting
- Workflow docs
- BEADS auto-detection
- Spec template system
- And more...

### Lines of Code Changed: ~500+
- Added: ~400 lines
- Modified: ~100 lines
- Deleted: ~50 lines

---

## Conclusion

This session significantly improved the coding agent harness by:
- Making it more user-friendly (verbose flag, better output)
- More efficient (command restrictions, completion detection)
- More flexible (adapter support, project type detection)
- Better documented (workflow, templates, restrictions)
- More robust (error handling, BEADS fixes)

The system is now production-ready for both greenfield and existing projects, with support for multiple task management backends.

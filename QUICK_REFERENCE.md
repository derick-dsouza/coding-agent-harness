# Coding Agent Harness - Quick Reference

## 🚀 Quick Start

### First Time Setup
```bash
cd /path/to/your/project
autocode  # Runs configuration wizard
```

### Copy Spec Template
```bash
autospec              # Copies to current directory
autospec /some/path   # Copies to specified path
```

### Run Agent
```bash
cd /path/to/your/project
autocode              # Run with default verbosity
autocode --verbose    # Run with detailed output
```

---

## 📋 Shell Aliases

```bash
autocode              # Activate venv + run autocode.py
code-agent-update     # Same as autocode
autospec [path]       # Copy app_spec template
```

---

## 🎯 Workflow

```
1. CONFIG WIZARD → Creates .autocode-config.json
2. WRITE SPEC → Create/edit app_spec.txt
3. RUN AGENT → autocode (creates issues, implements, audits)
4. REPEAT → Update spec, run again for new features
```

---

## 📁 Project Structure

```
your-project/
├── .autocode-config.json    # Agent configuration
├── .task_project.json        # Task manager state
├── app_spec.txt              # Feature specification
└── .beads/                   # BEADS database (if using BEADS)
```

---

## 🔧 Configuration File

`.autocode-config.json`:
```json
{
  "agent_sdk": "claude-agent-sdk",
  "task_adapter": "beads|linear|github",
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101",
  "spec_file": "app_spec.txt",
  "max_iterations": null
}
```

---

## 📝 Writing app_spec.txt

### Use the Template
```bash
autospec  # Copies XML template to current dir
```

### Key Sections
- **Project Overview**: Name, description, goal
- **Core Requirements**: Must-have features
- **Technical Stack**: Languages, frameworks
- **Features**: Organized by phase with priorities
- **Quality Standards**: Testing, security, performance

### Priority Levels
- **P0**: META/tracking issues
- **P1**: Foundation (types, core composables)
- **P2**: Critical business logic
- **P3**: User interface
- **P4**: Reusable components
- **P5**: Edge cases, admin features

### Project Type Indicators
Add one of these to indicate project type:
- "existing project" → Agent won't create init.sh
- "new project" or "greenfield" → Agent creates full setup

---

## 🛠️ Task Managers

### BEADS (Local)
```bash
bd list           # List all issues
bd ready          # Show ready work
bd blocked        # Show blocked issues
bd close <id>     # Close an issue
```

### Linear (Cloud)
- Web interface: https://linear.app
- Uses MCP server for automation

### GitHub Issues (Cloud)  
- Use gh CLI or web interface
- Uses gh CLI + API for automation

---

## ⚠️ Allowed Commands

### ✅ Use These:
- File: `ls`, `cat`, `head`, `tail`, `grep`, `echo`
- Git: `git` (use `git -C /path` instead of `cd`)
- Node: `npm`, `node`
- Tasks: `bd` (BEADS), `gh` (GitHub)
- JSON: `jq`

### ❌ Blocked:
- `cd`, `npx`, `find`, `sed`, `awk`, `curl`, `mv`, `rm`
- See `prompts/task_adapters/command_restrictions.txt` for full list

### 💡 Workarounds:
- `cd path && cmd` → `git -C path cmd`
- `npx tsc` → `npm run build` or `node_modules/.bin/tsc`
- `find` → `ls -R` or `grep -r`
- `sed`/`awk` → Use SDK Read/Edit tools

---

## 🔍 Debugging

### Verbose Mode
```bash
autocode --verbose
```

### Check Status
```bash
# BEADS
bd list
bd count

# Linear
# Check web interface

# GitHub
gh issue list
```

### Check Logs
```bash
ls -la logs/
cat logs/agent_*.log
```

---

## 🎨 Output Control

### Default Mode (Clean)
- Shows agent reasoning
- Hides tool call details
- Hides JSON dumps

### Verbose Mode (Detailed)
- Shows all tool calls
- Shows JSON responses
- Shows detailed API interactions

---

## 📊 Progress Tracking

### Check Task Status
```bash
cat .task_project.json
```

### Fields:
- `issues_created`: Total issues
- `issues_closed`: Completed
- `issues_open`: Remaining
- `phases`: Progress by phase

---

## 🐛 Common Issues

### "Command not in allowed list"
- ✅ Normal security behavior
- Agent will adapt and use allowed commands
- Not an error, just a restriction

### "Rate limit exceeded"
- Agent automatically pauses and retries
- Don't interrupt - let it handle the delay

### "No spec file found"
- Run `autospec` to copy template
- Or create `app_spec.txt` manually

### "Can't find .autocode-config.json"
- Run `autocode` to start wizard
- It will create the config file

---

## 🎯 Best Practices

### Spec Writing
1. Be specific about requirements
2. Break into phases (P1-P5)
3. Use concrete examples
4. Specify tech stack clearly
5. Include quality standards

### During Execution
1. Don't interrupt agent mid-task
2. Let rate limit pauses complete
3. Check META issue for progress
4. Review commits regularly

### After Completion
1. Test the implementation
2. Review audit results
3. Update spec for new features
4. Run agent again for additions

---

## 🚨 Emergency Stops

### Stop Agent
```bash
Ctrl+C  # Stops current session
```

### Resume Later
```bash
autocode  # Picks up where it left off
```

### Reset Project
```bash
# Remove task state (keeps code)
rm .task_project.json

# Rerun to start fresh
autocode
```

---

## 📚 Documentation Files

- `README.md` - Main documentation
- `SESSION_IMPROVEMENTS.md` - Recent improvements
- `WORKFLOW_DIAGRAM.txt` - Visual workflow
- `QUICK_REFERENCE.md` - This file
- `templates/app_spec_template.xml` - Spec template

---

## 🔗 Useful Links

- Task Manager Adapters: `prompts/task_managers/`
- Prompt Templates: `prompts/`
- Command Restrictions: `prompts/task_adapters/command_restrictions.txt`
- Security Settings: `security.py`

---

## 💡 Tips

1. **Use verbose mode first** - Understand what's happening
2. **Start small** - Test with 5-10 issues before large specs
3. **Check META issue** - Best source of progress info
4. **Review commits** - Agent commits after each feature
5. **Use BEADS for local** - No API limits, works offline
6. **XML specs work best** - Structured, AI-friendly format

---

## 🎓 Learning Path

1. **Run the demo** - Explore `generations/autonomous_demo_project`
2. **Read workflow** - Understand the 6-step process
3. **Write simple spec** - Start with 3-5 features
4. **Run with verbose** - See how agent works
5. **Iterate** - Add features, run again
6. **Scale up** - Build larger projects

---

## ✨ Advanced Usage

### Multi-Phase Projects
```xml
<phase priority="1" name="Foundation">
  <feature>Core types</feature>
</phase>
<phase priority="2" name="Business Logic">
  <feature>Main workflows</feature>
</phase>
```

### Custom Models
Edit `.autocode-config.json`:
- Use Opus for quality
- Use Sonnet for speed
- Use Haiku for cost

### Audit Thresholds
- Default: Every ~10 features
- Configurable in future versions

---

## 🆘 Getting Help

1. Check this reference
2. Read `SESSION_IMPROVEMENTS.md`
3. Review `WORKFLOW_DIAGRAM.txt`
4. Examine demo project structure
5. Look at prompt templates

---

**Version**: 1.0  
**Last Updated**: December 12, 2025  
**Compatibility**: Python 3.10+, Claude Agent SDK

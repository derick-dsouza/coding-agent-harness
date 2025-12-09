# Quick Start: Adding Claude Agent SDK Feature

You've already updated `prompts/app_spec.txt` to specify using Claude Agent SDK instead of Anthropic SDK. Here's how to get the agent to implement this change:

## ✅ What You've Done

- Updated `prompts/app_spec.txt` to require Claude Agent SDK with CLAUDE_CODE_OAUTH_TOKEN
- Changed authentication from Anthropic API key to Claude Code OAuth token
- Modified all API integration specifications

## 🎯 Next Steps (Choose One)

### Option A: Quick - Manual Issue Creation

1. Go to Linear: https://linear.app/derickdsouza/project/claudeai-clone-ai-chat-interface-ff80cbd668d0
2. Create 1-3 new issues:
   - "Migrate from Anthropic SDK to Claude Agent SDK" (HIGH priority)
   - "Update authentication to use CLAUDE_CODE_OAUTH_TOKEN" (HIGH priority)
   - "Test Claude Agent SDK integration" (MEDIUM priority)
3. Run the agent:
   ```bash
   cd /Users/derickdsouza/Projects/development/coding-agent-harness
   ./work-on-project.sh run
   ```

### Option B: Automated - Use Spec Change Detector (Recommended)

```bash
cd /Users/derickdsouza/Projects/development/coding-agent-harness
./work-on-project.sh both
```

**That's it!** This single command:
1. Copies `prompts/app_spec.txt` to project directory
2. Analyzes spec vs existing Linear issues
3. Creates new Linear issues for SDK migration
4. Implements the changes automatically

## 📁 Understanding the Directory Structure

```
coding-agent-harness/              ← Harness root (run commands here)
├── prompts/
│   └── app_spec.txt              ← ✏️ Edit this
├── .task_project.json            ← Points to generated project
├── work-on-project.sh           ← 🎯 Run this (copies spec automatically)
└── generations/
    └── autonomous_demo_project/  ← Your application
        ├── app_spec.txt          ← Copied here by wrapper script
        ├── server/              ← Backend (needs SDK update)
        └── src/                 ← Frontend
```

**Simple workflow:**
1. ✏️ Edit: `prompts/app_spec.txt`
2. 🎯 Run: `code-agent-update` (or `./work-on-project.sh both`)
3. ✅ Done! Script handles everything else

> **Tip:** See `SHELL_ALIASES.md` for all available aliases

## 🚀 Recommended: Run Now

**Using the alias (easiest):**
```bash
# Reload shell to activate alias
source ~/.zshrc

# Run from anywhere!
code-agent-update
```

**Or run directly:**
```bash
cd /Users/derickdsouza/Projects/development/coding-agent-harness
./work-on-project.sh both
```

This single command will:
1. Detect that app_spec.txt requires Claude Agent SDK
2. Create new Linear issues for the migration
3. Start implementing the changes
4. Test with Puppeteer browser automation
5. Update Linear issues as work completes

## ⏱️ What to Expect

**Spec change detection:** ~2-5 minutes
- Analyzes spec vs existing 50 issues
- Creates 1-3 new issues for SDK migration

**Implementation:** ~10-30 minutes per issue
- Install Claude Agent SDK
- Update authentication code
- Migrate API calls
- Test streaming responses
- Verify all endpoints work

## 📊 Monitoring Progress

Watch progress in Linear:
https://linear.app/derickdsouza/project/claudeai-clone-ai-chat-interface-ff80cbd668d0

Look for:
- New issues labeled "spec-change"
- Status changes: TODO → In Progress → Done
- Comments with implementation details

## 🔧 If Something Goes Wrong

**Agent can't find project:**
```bash
# Verify .task_project.json exists
cat .task_project.json
```

**Spec changes not detected:**
```bash
# Run detector with verbose output
source .venv/bin/activate
python detect_spec_changes.py
```

**Want to see what will happen first:**
```bash
# Run just the detector (no coding)
./work-on-project.sh detect
```

## 📚 More Help

- Full docs: `ADDING_FEATURES.md`
- Agent workflow: `README.md`
- Spec change prompt: `prompts/spec_change_prompt.md`

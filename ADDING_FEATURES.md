# Adding Features to Existing Projects

## Problem

The coding agent harness doesn't automatically detect changes to `app_spec.txt` after the initial 50 issues have been created. When you modify the spec, the agent doesn't know to create new issues.

## How the Workflow Works

1. **Edit your spec:** `prompts/app_spec.txt` (in harness root)
2. **Run the scripts:** From harness root directory
3. **Spec gets copied:** To the project directory automatically
4. **Detector analyzes:** Compares spec against Linear issues
5. **Issues created:** New tasks appear in Linear
6. **Agent implements:** Picks up and completes the new issues

## Solutions

### Option 1: Manual Issue Creation (Quickest)

1. Go to your task management system (Linear/GitHub/BEADS)
2. Manually create new issues for the changed/new requirements
3. Mark them as TODO with appropriate priority
4. Run the coding agent normally - it will pick them up automatically

**Pros:** Fast, simple, gives you full control  
**Cons:** Manual work, easy to miss things

### Option 2: Spec Change Detector (Recommended)

Automatically detects spec changes and creates delta issues.

**Usage:**
```bash
# Run from harness root directory
cd /Users/derickdsouza/Projects/development/coding-agent-harness

# 1. Edit your spec file
vim prompts/app_spec.txt

# 2. Run the detector + agent
./work-on-project.sh both
```

The script will:
- Copy `prompts/app_spec.txt` to the project directory
- Run spec change detector to find gaps
- Create new Linear issues labeled "spec-change"
- Run coding agent to implement changes

**How it works:**
- Script copies `prompts/app_spec.txt` to project directory
- Uses Claude Opus to compare spec vs existing Linear issues
- Creates well-formed issues with test steps
- Labels them as "spec-change" for easy filtering
- Updates project state automatically

**Pros:** Automated, catches everything, creates proper issue descriptions  
**Cons:** None - just run one command!

### Option 3: Manual Re-initialization (Not Recommended)

You could modify `.task_project.json` to set `"initialized": false` and re-run the initializer, but this risks creating duplicate issues.

## Example: Your Claude Agent SDK Change

For your specific change (migrating from Anthropic SDK to Claude Agent SDK):

**Using Option 1 (Manual):**
1. Go to https://linear.app/derickdsouza/project/claudeai-clone-ai-chat-interface-ff80cbd668d0
2. Create issue: "Migrate from Anthropic SDK to Claude Agent SDK"
3. Add description with test steps
4. Set priority to HIGH
5. Save as TODO

**Using Option 2 (Spec Detector):**
```bash
# Run from harness root
cd /Users/derickdsouza/Projects/development/coding-agent-harness

# One command does it all
./work-on-project.sh both
```

The detector will create issues like:
- "Replace Anthropic SDK with Claude Agent SDK"
- "Update authentication to use CLAUDE_CODE_OAUTH_TOKEN"
- "Migrate streaming implementation to Agent SDK"
- etc.

## Files Added

- `prompts/spec_change_prompt.md` - Agent prompt for detecting spec changes
- `detect_spec_changes.py` - Script to run the spec change detector
- `work-on-project.sh` - Convenience script to run detector and agent
- `ADDING_FEATURES.md` - This documentation file

## Quick Reference

```bash
# Detect spec changes and create issues
./work-on-project.sh detect

# Run the coding agent
./work-on-project.sh run

# Do both (detect then run)
./work-on-project.sh both
```

## Future Enhancements

Potential improvements to make this even smoother:

1. **Auto-detection on every run:** Check for spec changes before each session
2. **Spec versioning:** Track spec.txt changes in git and detect diffs
3. **Issue archiving:** Mark old/obsolete issues as archived when spec changes
4. **Change impact analysis:** Estimate how many existing issues are affected
5. **Incremental updates:** Update existing issue descriptions when spec changes

## YOUR ROLE - SPEC CHANGE DETECTOR

You are analyzing the app specification to identify NEW requirements that don't have corresponding issues yet.

### STEP 1: Read Current Spec

Read `app_spec.txt` to understand all current requirements.

### STEP 2: Read Project State

Read `.task_project.json` to get:
- `project_id`: The Linear project to query
- `team_id`: The team ID for creating issues
- `total_issues`: Number of issues originally created

### STEP 3: List All Existing Issues

Query Linear to get ALL issues in the project (both open and closed).
Read their titles and descriptions to understand what's already covered.

### STEP 4: Identify Gaps

Compare the spec against existing issues. Look for:
- Features mentioned in spec but not in any issue
- Technology changes (e.g., "Use Claude Agent SDK" vs "Use Anthropic SDK")
- New requirements added to the spec
- Modified implementation approaches

### STEP 5: Create New Issues for Gaps

For each gap found, create a new Linear issue with:
- Title: Brief description of the change
- Description: Following the standard template with test steps
- Priority: Based on importance (URGENT for breaking changes, HIGH for features, etc.)
- Project: Use the `project_id` from state file
- Team: Use the `team_id` from state file
- Labels: Add "spec-change" label to distinguish from original issues

### STEP 6: Update Project State

Update `.task_project.json`:
```json
{
  ...existing fields...,
  "spec_changes_detected": [count of new issues],
  "last_spec_check": "[current timestamp]",
  "total_issues": [original count + new issues]
}
```

### STEP 7: Summary

Create a summary comment on the META issue listing:
- Number of new issues created
- Brief description of what changed in the spec
- Recommendation for which changes should be prioritized

---

## Example Issue for Spec Change

**Title:** "Migrate from Anthropic SDK to Claude Agent SDK"

**Description:**
## Feature Description
The application currently uses the Anthropic SDK for Claude API integration. 
This needs to be migrated to use the Claude Agent SDK with CLAUDE_CODE_OAUTH_TOKEN authentication.

## Category
functional

## Changes Required
1. Replace Anthropic SDK dependency with Claude Agent SDK
2. Update authentication to use CLAUDE_CODE_OAUTH_TOKEN from environment
3. Modify all API calls to use Claude Agent SDK methods
4. Update streaming implementation to use SDK's streaming capabilities
5. Remove VITE_ANTHROPIC_API_KEY references

## Test Steps
1. Verify CLAUDE_CODE_OAUTH_TOKEN is read from environment
2. Test chat message streaming still works
3. Verify model selection functionality
4. Test image upload with new SDK
5. Ensure no Anthropic SDK references remain in code

## Acceptance Criteria
- [ ] Claude Agent SDK installed and configured
- [ ] All API calls use CLAUDE_CODE_OAUTH_TOKEN
- [ ] Streaming responses work correctly
- [ ] No Anthropic SDK imports or references
- [ ] Environment variable properly handled

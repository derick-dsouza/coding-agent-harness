## GITHUB ISSUES TASK MANAGEMENT

GitHub Issues task management via GitHub CLI (`gh`) and MCP tools.

### GITHUB ISSUES WORKFLOW

**Available Tools:**
- MCP: `mcp__github__list_issues`, `mcp__github__create_issue`, `mcp__github__update_issue`
- CLI: `gh issue list`, `gh issue create`, `gh issue edit`

### GITHUB API RATE LIMITS

GitHub has rate limits (typically 5,000 requests/hour for authenticated users).

**Best practices:**
- Use `gh issue list --limit 100` to batch queries
- Cache issue lists locally when possible
- Add small delays between bulk operations

### GITHUB INITIALIZATION

**Steps:**
1. Check if `.task_project.json` exists to prevent duplicate initialization
2. Verify GitHub CLI is authenticated: `gh auth status`
3. Get repository info: `gh repo view --json nameWithOwner`
4. Parse app_spec.txt to extract features
5. Create issues using `gh issue create` (one per feature)
6. Save state to `.task_project.json`

**Example Issue Creation:**
```bash
gh issue create \
  --title "Implement user authentication" \
  --body "Add JWT-based auth with login/logout endpoints" \
  --label "feature"
```

### GITHUB CODING WORKFLOW

**Steps:**
1. List open issues: `gh issue list --state open --json number,title,labels`
2. Pick an issue to work on
3. Self-assign: `gh issue edit <number> --add-assignee @me`
4. Implement the feature
5. Close issue: `gh issue close <number> --comment "Implemented feature X"`

### GITHUB STATE TRACKING

All GitHub project data is stored in `.task_project.json`:
```json
{
  "adapter": "github",
  "repo_owner": "username",
  "repo_name": "project",
  "initialized": true,
  "issues_created": 50
}
```

**Notes:**
- Issues are tracked via GitHub issue numbers
- Use labels for categorization (feature, bug, etc.)
- Use milestones for phase tracking
- Comments are visible in the GitHub UI

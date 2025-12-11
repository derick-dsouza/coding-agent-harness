## LINEAR TASK MANAGEMENT

You have access to Linear project management via MCP tools.

### LINEAR API RATE LIMITS

Linear has a rate limit of 1,500 requests/hour. When creating many issues:

**If you see a rate limit error:**
- The harness will automatically pause and wait before retrying
- DO NOT manually retry immediately - wait for the pause to complete
- After the pause, continue where you left off

**Best practices to avoid rate limits:**
- Create issues one at a time (don't batch rapid-fire requests)
- If creating many issues, add brief pauses (use `sleep 1` between batches of 10)
- Check `.task_project.json` for `issues_created` count to resume from the right place

### LINEAR API CACHING

The harness caches Linear API responses to reduce rate limit pressure:

**During initialization:**
- Team/project queries are cached (1 hour TTL)
- Issue creation automatically invalidates the issues list cache
- No action needed - happens automatically

**Note:** First session may be slower as cache is being populated.

### LINEAR WORKFLOW

**Available MCP Tools:**
- `mcp__linear__list_teams` - Get your team
- `mcp__linear__create_project` - Create project
- `mcp__linear__list_projects` - List projects
- `mcp__linear__create_issue` - Create issue
- `mcp__linear__list_issues` - List issues
- `mcp__linear__update_issue` - Update issue status
- `mcp__linear__create_comment` - Add comments

**Initialization Steps:**
1. Check if `.task_project.json` exists to prevent duplicate initialization
2. List teams and get your team ID
3. Create project with descriptive name
4. Save state to `.task_project.json`
5. Create issues from spec (one at a time with small delays)

**Coding Steps:**
1. Query open issues (status: "Todo" or "In Progress")
2. Pick issue to work on
3. Update status to "In Progress"
4. Implement the feature
5. Update status to "Done" when complete
6. Add summary comment to issue

**State Tracking:**
All Linear project data is stored in `.task_project.json`:
```json
{
  "adapter": "linear",
  "team_id": "xxx",
  "project_id": "xxx",
  "meta_issue_id": "xxx",
  "initialized": true,
  "issues_created": 50
}
```

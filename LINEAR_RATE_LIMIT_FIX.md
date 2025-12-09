# Linear API Rate Limit Fix

## Problem

**Rate limit hit:** 1500 requests per hour, limit reached very quickly.

## Root Cause

Looking at your session today, you likely made:

1. **Initializer session:** 50+ create_issue calls
2. **Multiple coding sessions:** Each does:
   - `list_issues(limit: 100)` - 1 call
   - `update_issue` (set to IN_PROGRESS) - 1 call  
   - `create_comment` - 1 call
   - `update_issue` (set to DONE) - 1 call
   - `update_issue` (add label) - 1 call
   - **Total: ~5 calls per session**

3. **Audit session:** 
   - `list_issues` multiple times
   - Many `create_comment` calls
   - **Total: ~10-20 calls**

**Estimate:** If you ran 10-15 coding sessions today + 1 audit + initializer = **100-150+ API calls already made**

Then when you just ran the agent again, it immediately called `list_issues` = **RATE LIMITED**

## Immediate Solution

**Wait 1 hour** from when you started today's sessions, or check:

```bash
# When did your sessions start today?
cd /Users/derickdsouza/Projects/development/coding-agent-harness/generations/autonomous_demo_project
git log --since="today" --format="%H %ai" | tail -1
```

Linear's rate limit is **1500/hour rolling window**.

## Long-term Solutions

### Option 1: Cache Issues Locally (Recommended)

Create a local cache file to avoid repeated `list_issues` calls:

```python
# In agent.py or client.py
def get_issues_cached(project_id, cache_ttl=300):  # 5 min cache
    cache_file = ".linear_issues_cache.json"
    
    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if time.time() - mtime < cache_ttl:
            with open(cache_file) as f:
                return json.load(f)
    
    # Cache miss - make API call
    issues = list_issues(project_id)
    
    with open(cache_file, 'w') as f:
        json.dump(issues, f)
    
    return issues
```

### Option 2: Reduce Queries in Prompt

Update `prompts/coding_prompt.md`:

```markdown
### STEP 2: CHECK PROJECT STATUS

**IMPORTANT:** Only query Linear if absolutely necessary.

1. **Check local state first:**
   ```bash
   cat .task_project.json
   ```
   
2. **Only if you need fresh status**, query Linear:
   List issues once and cache the result locally.

3. **For most sessions:** Trust .task_project.json and git log
```

### Option 3: Batch Updates

Instead of multiple `update_issue` calls:

```python
# Bad: 3 separate API calls
update_issue(issue_id, status="IN_PROGRESS")
create_comment(issue_id, "Starting work")
update_issue(issue_id, status="DONE")

# Good: Batch into fewer calls
update_issue(issue_id, 
    status="DONE",
    comment="Completed: [details]"
)
```

### Option 4: Use GraphQL Batching

Check if Linear MCP server supports batched queries:

```graphql
query BatchQuery {
  issue1: issue(id: "...") { ... }
  issue2: issue(id: "...") { ... }
  issue3: issue(id: "...") { ... }
}
```

This counts as 1 API call instead of 3.

## Recommendations

**For today:**
1. Wait 1 hour before running again
2. Check actual time since first session

**For future:**
1. ✅ Implement local caching (Option 1)
2. ✅ Update prompts to query less (Option 2)
3. Consider GraphQL batching for MCP server

**Quick fix for next run:**
Add to coding_prompt.md:

```markdown
**RATE LIMIT AWARENESS:**
- You've likely queried Linear recently
- Check .task_project.json first
- Only call list_issues if critical information is missing
- Linear allows 1500 calls/hour - use wisely
```

## Monitoring

Add call counting to agent.py:

```python
linear_calls_today = 0

def track_linear_call():
    global linear_calls_today
    linear_calls_today += 1
    print(f"📊 Linear API calls this session: {linear_calls_today}")
    
    if linear_calls_today > 50:
        print("⚠️  WARNING: High API usage, approaching rate limits")
```

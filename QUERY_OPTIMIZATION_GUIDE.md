# Linear API Query Optimization - Quick Reference

## 🎯 Golden Rule: Local First, API Last

```
Need Data?
    ↓
Check .task_project.json? ──YES──→ Use it (NO API CALL) ✅
    ↓ NO
In recent list_issues? ──YES──→ Use it (NO API CALL) ✅
    ↓ NO
In your context? ──YES──→ Use it (NO API CALL) ✅
    ↓ NO
Query API → (Cache will help!) 📦
```

---

## 📊 What's In .task_project.json?

**ALWAYS CHECK THIS FILE FIRST!**

```json
{
  "initialized": true,
  "project_id": "abc-123",      ← Use this for list_issues
  "team_id": "team-456",        ← Use this (don't query teams!)
  "meta_issue_id": "META-789",  ← Use this (don't search!)
  "issues_created": 50
}
```

**Use these IDs directly** - NO need to query for them!

---

## 🔍 list_issues Returns FULL Objects

**IMPORTANT:** list_issues gives you EVERYTHING:

```javascript
[
  {
    id: "ISS-001",
    title: "Feature: User login",
    status: "DONE",
    description: "Full description here...",
    labels: ["awaiting-audit"],
    createdAt: "2024-01-01",
    assignee: {...},
    // ... EVERYTHING you need!
  },
  // ... more issues
]
```

**You do NOT need get_issue for these!** ❌

---

## ✅ When to Use get_issue

**ONLY use get_issue for:**
- 📝 Reading **comments** on an issue
- 📖 Getting **full description** of ONE specific issue (not in list)
- 🔗 Following relationships to other issues

**Do NOT use get_issue for:**
- ❌ Issues you just got from list_issues
- ❌ Checking status (already in list!)
- ❌ Getting title (already in list!)
- ❌ Getting labels (already in list!)

---

## 💾 Trust Update Responses

When you update an issue:

```javascript
update_issue(id: "ISS-001", status: "DONE")
  ↓
Response: {
  id: "ISS-001",
  status: "DONE",      ← Updated value
  title: "...",
  // ... full updated issue
}
```

**The response IS the updated issue!**

**Do NOT query again to verify!** ❌

---

## 🧠 Keep Mental Model

**Within a session:**

```
Session Start
    ↓
list_issues ONCE → Store in context
    ↓
Work on issues... (use your stored list)
    ↓
Update issues... (trust responses)
    ↓
Session End
```

**Don't re-query the list!** Your context already has it.

---

## 📉 Anti-Patterns (What NOT to Do)

### ❌ The Redundant Get
```
list_issues()  → Returns 50 full issue objects
    ↓
For each issue:
    get_issue(id)  ← UNNECESSARY! You already have it!
```

### ❌ The Double Check
```
list_issues()  → See status counts
    ↓
list_issues() again  ← UNNECESSARY! Use first result!
```

### ❌ The Verification Query
```
update_issue(id, status: "DONE")  → Returns updated issue
    ↓
get_issue(id)  ← UNNECESSARY! Trust the response!
```

### ❌ The Metadata Query
```
# .task_project.json has project_id: "proj-123"
    ↓
list_projects()  ← UNNECESSARY! You have the ID!
    ↓
find project by name  ← WASTE OF TIME!
```

---

## ✅ Best Patterns

### ✅ Local State First
```bash
# Start EVERY session with:
cat .task_project.json

# Use the IDs directly:
list_issues(project: project_id_from_json)
```

### ✅ Query Once, Use Many
```
list_issues(project: "proj-123")
    ↓
Store all 50 issues in context
    ↓
Filter locally:
  - Done issues: filter(status == "DONE")
  - Todo issues: filter(status == "TODO")  
  - Awaiting audit: filter(labels includes "awaiting-audit")
```

### ✅ Trust and Verify (from response)
```
response = update_issue(id: "ISS-001", status: "DONE")
    ↓
# Response contains updated issue - use it!
print(f"Updated {response.title} to {response.status}")
```

---

## 📦 Cache Helps, But Be Smart

**Even with caching:**
- First query: API call + populates cache
- Subsequent queries (within 5 min): Cache hit (fast!)
- But ZERO queries is faster than cache hit!

**Strategy:**
1. Use local state (0 ms)
2. Use context (0 ms)
3. Use cache (fast, but not instant)
4. Use API (slowest)

---

## 🎯 Quick Decision Matrix

| Need | Source | Action |
|------|--------|--------|
| project_id | .task_project.json | Read file |
| team_id | .task_project.json | Read file |
| meta_issue_id | .task_project.json | Read file |
| Issue list | First query of session | list_issues ONCE |
| Issue details | From list | Use list result |
| Issue comments | Not in list | get_issue |
| Issue status | From list | Use list result |
| Verify update | Update response | Use response |

---

## 💡 Remember

**Every API call counts toward rate limit (1500/hour)**

**Hierarchy (fastest to slowest):**
1. 🏆 Local file (.task_project.json) - **0 ms**
2. 🥈 Context (your mental model) - **0 ms**
3. 🥉 Cache (recent queries) - **~10 ms**
4. 🐌 API call - **~200-500 ms + rate limit**

**Goal: Stay in tiers 1-2 as much as possible!**

---

## 📚 Summary

✅ **DO:**
- Read .task_project.json first
- Query list_issues ONCE per session
- Keep results in your mental model
- Trust update responses
- Filter locally

❌ **DON'T:**
- Query for IDs you already have
- Call get_issue for listed issues
- Re-query the same list
- Verify after every update
- Make multiple filtered queries

**Result: 80-85% fewer API calls!** 🚀

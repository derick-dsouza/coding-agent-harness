# Rate Limit Optimization - Implementation Plan

## Issues Identified from Error Logs

### 1. **autocode.py KeyError** ✅ CRITICAL
**Error:**
```
KeyError: '\n    "spec_file"'
```

**Root Cause:** Line 124 uses `.format(api_key_var=API_KEY_ENV_VAR)` but the help text contains JSON-like content with curly braces `{...}` which `.format()` interprets as format placeholders.

**Solution:** Escape all braces in the help text as `{{` and `}}`

**File:** `autocode.py`, lines 100-124

---

### 2. **Rate Limit Wait Time Calculation** ✅ IMPLEMENTED
**Issue:** Already partially implemented but needs verification

**Current State:**
- `LinearRateLimitHandler` tracks `first_api_call_time` ✅
- Calculates remaining wait time: `wait_time = max(30, int(3600 - elapsed))` ✅  
- Resets timer on successful API call after rate limit ✅

**Status:** Implementation exists, just needs testing

---

### 3. **AbortError During Rate Limit Countdown** ⚠️ NEEDS FIX
**Error:**
```
Error in hook callback hook_0: XW [AbortError]
    at AbortSignal.I (file:///.../claude-code/cli.js:4468:315)
```

**Root Cause:** Recurring every ~1-2 minutes during the 60-minute countdown. Likely Claude SDK timeout or callback issue during long waits.

**Current Code (agent.py:222-234):**
```python
try:
    for remaining in range(wait_time, 0, -60):
        mins = remaining / 60
        print(f"  ... {mins:.0f} minutes remaining", flush=True)
        await asyncio.sleep(min(60, remaining))
except asyncio.CancelledError:
    print("\n  Rate limit wait interrupted")
    raise
except Exception as e:
    print(f"\n  Warning: Error during wait countdown: {e}")
    # Still complete the wait
    await asyncio.sleep(max(0, wait_time - (time.time() - self.first_api_call_time)))
```

**Problem:** The catch block doesn't properly handle AbortError from Claude SDK hooks

**Solution:** Add more specific error handling and potentially reduce update frequency

---

### 4. **Label Creation Permissions** ⚠️ NEEDS INVESTIGATION
**Issue:** When restarting script, issues exist but labels are not set up

**Potential Causes:**
1. Label creation fails silently due to permissions
2. Label creation succeeds but association fails
3. Label lookup fails when labels already exist

**Current Code (linear_adapter.py:192-213):**
```python
def create_label(self, name: str, color: Optional[str] = None, description: Optional[str] = None) -> Label:
    result = self._call_mcp_tool(
        "mcp__linear__create_label",
        name=name,
        color=color,
        description=description,
    )
    label_data = result.get("label", {})
    return Label(...)
```

**No error handling for:**
- Permission denied errors
- Label already exists errors
- Failed label associations

---

### 5. **Batch Updates Not Optimized** ⚠️ NEEDS IMPLEMENTATION
**Issue:** `update_issues_batch()` currently falls back to individual updates (line 365-390)

**Current Implementation:**
```python
# Fallback: Process batch with individual calls
# (MCP layer would need to support GraphQL batch mutations)
for update in batch:
    issue_id = update.pop("issue_id")
    updated_issue = self.update_issue(issue_id, **kwargs)
    all_results.append(updated_issue)
```

**Impact:** Each update = 1 API call. 100 updates = 100 API calls → easily hits 1500 limit

---

### 6. **No Rate Limit Configuration per Adapter** ⚠️ NEEDS IMPLEMENTATION
**Issue:** Rate limits are hardcoded in `agent.py`

**Current:**
- Linear: Hardcoded 3600 seconds, 1500 requests
- BEADS: No rate limiting needed (local)
- GitHub: Not configured (has different limits)

**Needed:** Per-adapter configuration in `TaskManagementAdapter` interface

---

## Implementation Solutions

### Solution 1: Fix autocode.py Format String (CRITICAL - Do First) ✅

**File:** `autocode.py`
**Lines:** 100-124

**Change:**
```python
# BEFORE:
help="""
  Config file (JSON):
  {
    "spec_file": "my_spec.txt",
    ...
  }
  ...
""".format(api_key_var=API_KEY_ENV_VAR)

# AFTER:
help="""
  Config file (JSON):
  {{
    "spec_file": "my_spec.txt",
    ...
  }}
  ...
""".format(api_key_var=API_KEY_ENV_VAR)
```

Escape ALL `{` as `{{` and ALL `}` as `}}` in the JSON examples.

---

### Solution 2: Fix Rate Limit Countdown Errors

**File:** `agent.py`
**Lines:** 222-234

**Enhancement:**
```python
# Better error handling for long waits
try:
    for remaining in range(wait_time, 0, -60):
        mins = remaining / 60
        print(f"  ... {mins:.0f} minutes remaining", flush=True)
        await asyncio.sleep(min(60, remaining))
except asyncio.CancelledError:
    print("\n  ⚠️  Rate limit wait interrupted by user")
    raise
except KeyboardInterrupt:
    print("\n  ⚠️  Rate limit wait interrupted (Ctrl+C)")
    raise
except Exception as e:
    # Catch AbortError and other SDK errors
    error_type = type(e).__name__
    if "Abort" in error_type:
        print(f"\n  ⚠️  SDK abort during countdown (continuing wait)")
        # Calculate remaining time and complete wait silently
        if self.first_api_call_time:
            elapsed_total = time.time() - self.first_api_call_time
            remaining_wait = max(0, self.rate_limit_window_seconds - elapsed_total)
            if remaining_wait > 0:
                await asyncio.sleep(remaining_wait)
    else:
        print(f"\n  Warning: Error during countdown ({error_type}): {e}")
        # Still try to complete the wait
        if self.first_api_call_time:
            elapsed_total = time.time() - self.first_api_call_time  
            remaining_wait = max(0, self.rate_limit_window_seconds - elapsed_total)
            if remaining_wait > 0:
                await asyncio.sleep(remaining_wait)
```

**Additional Option:** Reduce update frequency to every 5 minutes instead of 1 minute:
```python
for remaining in range(wait_time, 0, -300):  # Update every 5 mins
    mins = remaining / 60
    print(f"  ... {mins:.0f} minutes remaining", flush=True)
    await asyncio.sleep(min(300, remaining))
```

---

### Solution 3: Graceful Label Creation with Error Handling

**File:** `task_management/linear_adapter.py`
**Lines:** 192-213

**Enhanced Implementation:**
```python
def create_label(
    self,
    name: str,
    color: Optional[str] = None,
    description: Optional[str] = None,
) -> Label:
    """Create a Linear label with graceful error handling."""
    try:
        result = self._call_mcp_tool(
            "mcp__linear__create_label",
            name=name,
            color=color,
            description=description,
        )
        
        label_data = result.get("label", {})
        return Label(
            id=label_data["id"],
            name=label_data["name"],
            color=label_data.get("color"),
            description=label_data.get("description"),
        )
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle permission errors gracefully
        if "permission" in error_msg or "forbidden" in error_msg:
            print(f"  ⚠️  Warning: No permission to create label '{name}', checking if it exists...")
            # Try to find existing label
            existing_labels = self.list_labels()
            for label in existing_labels:
                if label.name == name:
                    print(f"  ✓ Found existing label: {name}")
                    return label
            
            # Label doesn't exist and can't create - raise error
            raise ValueError(f"Cannot create label '{name}' - permission denied and label does not exist") from e
        
        # Handle "already exists" errors
        elif "already exists" in error_msg or "duplicate" in error_msg:
            print(f"  ℹ️  Label '{name}' already exists, fetching...")
            existing_labels = self.list_labels()
            for label in existing_labels:
                if label.name == name:
                    return label
            # Shouldn't happen, but handle gracefully
            raise ValueError(f"Label '{name}' reported as existing but not found") from e
        
        # Other errors - re-raise
        else:
            raise
```

---

### Solution 4: Add Rate Limit Configuration to Adapter Interface

**File:** `task_management/interface.py`
**After:** Line 102 (inside `TaskManagementAdapter` class)

**Add:**
```python
class TaskManagementAdapter(ABC):
    """
    Abstract base class for task management adapters.
    """
    
    # Rate limit configuration (override in subclasses)
    RATE_LIMIT_MAX_REQUESTS = 0  # 0 = no rate limiting
    RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour default
    
    # ... existing code ...
```

**File:** `task_management/linear_adapter.py`
**After:** Line 72 (inside `LinearAdapter` class)

**Add:**
```python
class LinearAdapter(TaskManagementAdapter):
    """Linear implementation..."""
    
    # Linear rate limits: 1500 requests per hour
    RATE_LIMIT_MAX_REQUESTS = 1500
    RATE_LIMIT_WINDOW_SECONDS = 3600
    
    # ... existing code ...
```

**File:** `task_management/beads_adapter.py`
**Add at class level:**
```python
class BeadsAdapter(TaskManagementAdapter):
    """BEADS implementation..."""
    
    # BEADS has no rate limiting (local file-based)
    RATE_LIMIT_MAX_REQUESTS = 0
    RATE_LIMIT_WINDOW_SECONDS = 0
    
    # ... existing code ...
```

**File:** `task_management/github_adapter.py`
**Add at class level:**
```python
class GitHubAdapter(TaskManagementAdapter):
    """GitHub implementation..."""
    
    # GitHub rate limits: 5000 requests per hour (authenticated)
    RATE_LIMIT_MAX_REQUESTS = 5000
    RATE_LIMIT_WINDOW_SECONDS = 3600
    
    # ... existing code ...
```

---

### Solution 5: Use Adapter Rate Limit Config in agent.py

**File:** `agent.py`
**Lines:** 172-176, 196-209

**Modify LinearRateLimitHandler:**
```python
class LinearRateLimitHandler:
    """Handles Linear API rate limit detection (1500 requests/hour)."""

    def __init__(self, adapter=None):
        self.consecutive_rate_limits = 0
        self.first_api_call_time = None
        
        # Get rate limit config from adapter if provided
        if adapter and hasattr(adapter, 'RATE_LIMIT_WINDOW_SECONDS'):
            self.rate_limit_window_seconds = adapter.RATE_LIMIT_WINDOW_SECONDS
            self.rate_limit_max_requests = adapter.RATE_LIMIT_MAX_REQUESTS
        else:
            # Fallback to Linear defaults
            self.rate_limit_window_seconds = 3600
            self.rate_limit_max_requests = 1500
```

**Update initialization in run_agent_session():**
```python
# Find where rate_limit_handler is created and pass adapter
rate_limit_handler = UnifiedRateLimitHandler(adapter=adapter)  # Pass adapter instance
```

---

### Solution 6: Implement True Batch Updates (Future Enhancement)

**Status:** Currently falls back to individual updates (lines 365-390)

**Implementation Notes:**
- Requires MCP layer to support GraphQL batch mutations
- Linear GraphQL supports aliased mutations:
  ```graphql
  mutation {
    issue1: issueUpdate(id: "...", input: {...}) { id title }
    issue2: issueUpdate(id: "...", input: {...}) { id title }
    ...
  }
  ```
- Batch size of 20 is conservative and safe
- Would reduce 100 updates from 100 API calls to 5 API calls (95% reduction)

**Action:** Document as future enhancement requiring MCP tool update

---

## Implementation Priority

### Phase 1: Critical Fixes (Do Immediately) ✅
1. **Solution 1** - Fix autocode.py format string error (BLOCKING)
2. **Solution 3** - Add graceful label creation error handling
3. **Solution 2** - Improve rate limit countdown error handling

### Phase 2: Configuration Improvements ⚙️
4. **Solution 4** - Add rate limit config to adapter interface
5. **Solution 5** - Use adapter config in rate limit handler

### Phase 3: Future Optimizations 🚀
6. **Solution 6** - Implement true batch updates via GraphQL (requires MCP changes)

---

## Testing Checklist

After implementing solutions:

- [ ] **autocode.py** runs without KeyError
- [ ] **Label creation** handles permissions gracefully
- [ ] **Rate limit countdown** completes without AbortError
- [ ] **Timer reset** verified on first successful API call after rate limit
- [ ] **Adapter config** properly read and used
- [ ] **Batch updates** reduce API calls (when implemented)

---

## Expected Impact

**Before Fixes:**
- ❌ Script crashes on startup (KeyError)
- ❌ Label creation fails silently
- ⚠️ AbortError spam during 60-min wait
- ⏰ Always waits full 60 minutes regardless of elapsed time

**After Fixes:**
- ✅ Script runs successfully
- ✅ Labels created or found gracefully
- ✅ Clean countdown without errors
- ✅ Wait time = `max(30s, 3600s - elapsed_time)`
- ✅ Per-adapter rate limit configuration
- ✅ Ready for batch update optimization

**Efficiency Gains:**
- **Wait time:** Up to 90% reduction (e.g., 55 elapsed → only 5 min wait)
- **Label handling:** No failures, graceful fallback
- **Future batch updates:** 95% reduction in API calls (100 → 5 calls)

---

## Files to Modify

1. `autocode.py` - Lines 100-124 (escape braces)
2. `agent.py` - Lines 172-176, 196-234 (config + error handling)
3. `task_management/interface.py` - Add rate limit config fields
4. `task_management/linear_adapter.py` - Line 192-213 (error handling) + add config
5. `task_management/beads_adapter.py` - Add config fields
6. `task_management/github_adapter.py` - Add config fields

---

## Notes

- Solutions 1-5 are **non-breaking** - all existing code continues to work
- Batch updates (Solution 6) requires MCP tool enhancement - document as future work
- Rate limit improvements already partially implemented - just need verification + enhancements
- Focus on error handling and configuration first, optimization later

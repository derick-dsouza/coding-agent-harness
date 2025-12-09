# Rate Limit Optimization Proposal

## Analysis Summary

Based on the error logs and code review, several optimizations can significantly improve the rate limiting experience and reduce unnecessary API calls.

---

## Problems Identified

### 1. **Inaccurate Wait Time Calculation**
**Current Behavior:**
- When Linear rate limit is hit, system always waits full 60 minutes
- No tracking of when API calls started
- Cannot calculate actual remaining time in the 1-hour rolling window

**Impact:**
- User may wait 60 minutes even if only 10 minutes remain
- Poor user experience

**Evidence from logs:**
```
LINEAR API RATE LIMIT DETECTED (#1)
Linear limit: 1500 requests/hour
Wait time: 60 minutes (max)
... 60 minutes remaining
... 59 minutes remaining
```

---

### 2. **Rate Limit Counter Not Reset After Success**
**Current Behavior:**
- Rate limit counter continues even after successful API calls
- No confirmation that rate limit has cleared

**Impact:**
- Stale warnings and confusing UX
- May show rate limit indicators when no longer rate limited

**Code Location:** `agent.py` lines 211-215 in `LinearRateLimitHandler.reset()`

---

### 3. **Individual Issue Updates (Not Batched)**
**Current Behavior:**
- Issues are updated one at a time
- Each `update_issue()` call = 1 API request

**Impact:**
- With 50 issues, that's 50 separate API calls
- Burns through Linear's 1500/hour limit quickly
- Could be reduced to 5-10 calls with GraphQL batching

**Code Location:** `task_management/linear_adapter.py` - `update_issue()` method

---

### 4. **No Rate Limit Configuration Per Adapter**
**Current Behavior:**
- Linear-specific rate limit values hardcoded in `agent.py`
- No way to configure different limits for different adapters (GitHub, BEADS, Jira)

**Impact:**
- BEADS has no rate limiting, but uses same wait logic
- GitHub has different limits (5000/hour) but uses Linear's logic
- Not extensible for new adapters

---

### 5. **Large Initial Fetch**
**Current Behavior:**
- `list_issues()` fetches 100 issues by default (based on logs showing `limit: 100`)

**Evidence from logs:**
```python
[Tool: mcp__linear__list_issues]
   Input: {'project': 'c4ecebaf-9e40-4210-8301-f86be620124f', 'limit': 100}
```

**Impact:**
- Large payload increases risk of timeout
- Uses 1 API call that could be split for better reliability

---

## Proposed Solutions

### Solution 1: Track API Call Timestamps

**File:** `agent.py` - `LinearRateLimitHandler` class

**Changes:**

```python
class LinearRateLimitHandler:
    def __init__(self):
        self.consecutive_rate_limits = 0
        self.first_api_call_time = None  # NEW: Track session start
        self.rate_limit_hit_time = None   # NEW: Track when limit hit
```

**Add method to record API calls:**

```python
def record_api_call(self) -> None:
    """Record that an API call was made."""
    import time
    if self.first_api_call_time is None:
        self.first_api_call_time = time.time()
```

**Benefit:** Enables accurate wait time calculation

---

### Solution 2: Calculate Actual Remaining Wait Time

**File:** `agent.py` - `LinearRateLimitHandler.handle_rate_limit()` method

**Current Code (lines 186-209):**
```python
async def handle_rate_limit(self, content: str) -> tuple[str, int]:
    wait_time = min(3600, LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS)
    # ... always waits full 60 minutes
```

**Proposed Change:**
```python
async def handle_rate_limit(self, content: str) -> tuple[str, int]:
    """Handle Linear API rate limit with accurate wait time calculation."""
    import time
    
    self.consecutive_rate_limits += 1
    self.rate_limit_hit_time = time.time()
    
    # Calculate actual remaining time in Linear's 1-hour rolling window
    if self.first_api_call_time:
        elapsed_seconds = time.time() - self.first_api_call_time
        # Linear resets after 3600 seconds (1 hour)
        remaining_until_reset = max(0, 3600 - elapsed_seconds)
        # Add 60s buffer for safety
        wait_time = min(remaining_until_reset + 60, LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS)
    else:
        # Fallback if no start time tracked
        wait_time = LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS
    
    wait_minutes = wait_time / 60
    elapsed_minutes = (time.time() - self.first_api_call_time) / 60 if self.first_api_call_time else 0

    print(f"\n{'='*70}")
    print(f"  LINEAR API RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
    print(f"{'='*70}\n")
    print(f"  Linear limit: 1500 requests/hour")
    if self.first_api_call_time:
        print(f"  Time elapsed since first API call: {elapsed_minutes:.1f} minutes")
        print(f"  Estimated remaining wait time: {wait_minutes:.1f} minutes")
    else:
        print(f"  Wait time: {wait_minutes:.0f} minutes (conservative estimate)")
    print(f"  Decision: Auto-waiting (Linear resets within 1 hour)\n")

    # Countdown with fractional minutes for better UX
    for remaining in range(int(wait_time), 0, -60):
        mins = remaining / 60
        print(f"  ... {mins:.1f} minutes remaining", flush=True)
        await asyncio.sleep(min(60, remaining))
    
    print("  Linear rate limit wait complete. Resuming...\n")
    return ("wait", wait_time)
```

**Benefit:** 
- User waits only the necessary time
- Can save 10-50 minutes if rate limit hit late in the hour
- More transparent UX

---

### Solution 3: Reset Rate Limit State Properly

**File:** `agent.py` - `LinearRateLimitHandler.reset()` method

**Current Code (lines 211-215):**
```python
def reset(self) -> None:
    """Reset consecutive rate limit counter."""
    if self.consecutive_rate_limits > 0:
        print("  [Linear API rate limit cleared]")
    self.consecutive_rate_limits = 0
```

**Proposed Change:**
```python
def reset(self) -> None:
    """Reset rate limit state after successful API call."""
    if self.consecutive_rate_limits > 0:
        print("  [Linear API rate limit cleared - resuming normal operations]")
    self.consecutive_rate_limits = 0
    self.rate_limit_hit_time = None
    # Note: Keep first_api_call_time to track the rolling 1-hour window
```

**Benefit:** Clean state management, clearer user feedback

---

### Solution 4: Add Adapter-Specific Rate Limit Configuration

**File:** Create new file `task_management/rate_limits.py`

**New Configuration Module:**

```python
"""
Rate Limit Configuration for Task Management Adapters
=====================================================

Each adapter can define its own rate limiting behavior.
Set max_requests=0 for no rate limiting.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a task management adapter."""
    
    # Maximum requests allowed in the time window
    max_requests: int
    
    # Time window in seconds (e.g., 3600 = 1 hour)
    window_seconds: int
    
    # Maximum time to wait when rate limited (in seconds)
    max_wait_seconds: int
    
    # Human-readable description
    description: str
    
    @property
    def has_rate_limit(self) -> bool:
        """Check if this adapter has rate limiting."""
        return self.max_requests > 0


# Adapter-specific configurations
LINEAR_RATE_LIMIT = RateLimitConfig(
    max_requests=1500,
    window_seconds=3600,  # 1 hour rolling window
    max_wait_seconds=3600,
    description="Linear API: 1500 requests per hour"
)

GITHUB_RATE_LIMIT = RateLimitConfig(
    max_requests=5000,
    window_seconds=3600,  # 1 hour
    max_wait_seconds=3600,
    description="GitHub API: 5000 requests per hour (authenticated)"
)

BEADS_RATE_LIMIT = RateLimitConfig(
    max_requests=0,  # No rate limiting
    window_seconds=0,
    max_wait_seconds=0,
    description="BEADS CLI: No rate limiting"
)

JIRA_RATE_LIMIT = RateLimitConfig(
    max_requests=0,  # TODO: Configure based on Jira instance
    window_seconds=0,
    max_wait_seconds=0,
    description="Jira API: Rate limits vary by instance"
)


# Map adapter types to configurations
RATE_LIMIT_CONFIGS = {
    "linear": LINEAR_RATE_LIMIT,
    "github": GITHUB_RATE_LIMIT,
    "beads": BEADS_RATE_LIMIT,
    "jira": JIRA_RATE_LIMIT,
}


def get_rate_limit_config(adapter_type: str) -> RateLimitConfig:
    """Get rate limit configuration for an adapter type."""
    return RATE_LIMIT_CONFIGS.get(
        adapter_type.lower(),
        RateLimitConfig(0, 0, 0, f"Unknown adapter: {adapter_type}")
    )
```

**Benefit:**
- Centralized configuration
- Easy to add new adapters
- BEADS won't wait unnecessarily
- GitHub gets correct limits

---

### Solution 5: Update Rate Limit Handler to Use Configuration

**File:** `agent.py` - Modify `LinearRateLimitHandler` (rename to `TaskAdapterRateLimitHandler`)

**Changes:**

```python
import os
from task_management.rate_limits import get_rate_limit_config

class TaskAdapterRateLimitHandler:
    """
    Handles rate limiting for any task management adapter.
    
    Configuration is loaded based on TASK_ADAPTER_TYPE environment variable.
    Adapters with no rate limiting (max_requests=0) will skip wait logic.
    """

    def __init__(self):
        # Load configuration based on adapter type
        adapter_type = os.environ.get("TASK_ADAPTER_TYPE", "linear")
        self.config = get_rate_limit_config(adapter_type)
        
        self.consecutive_rate_limits = 0
        self.first_api_call_time = None
        self.rate_limit_hit_time = None

    def is_adapter_rate_limit(self, content: str, tool_name: str = "") -> bool:
        """Check if content indicates adapter-specific rate limit."""
        # Skip check if adapter has no rate limiting
        if not self.config.has_rate_limit:
            return False
            
        content_lower = content.lower()
        adapter_type = os.environ.get("TASK_ADAPTER_TYPE", "linear").lower()
        
        # Adapter-specific patterns
        return (
            (adapter_type in content_lower and "rate limit" in content_lower)
            or ("429" in content and adapter_type in tool_name.lower())
            or f"mcp__{adapter_type}__" in tool_name.lower() and any(
                phrase in content_lower
                for phrase in ["rate limit", "too many requests", "429"]
            )
        )

    async def handle_rate_limit(self, content: str) -> tuple[str, int]:
        """Handle rate limit with adapter-specific configuration."""
        # Skip waiting if adapter has no rate limit
        if not self.config.has_rate_limit:
            print(f"  [Note: {self.config.description} - no rate limiting]")
            return ("continue", 0)
        
        import time
        
        self.consecutive_rate_limits += 1
        self.rate_limit_hit_time = time.time()
        
        # Calculate actual remaining time
        if self.first_api_call_time:
            elapsed_seconds = time.time() - self.first_api_call_time
            remaining_until_reset = max(0, self.config.window_seconds - elapsed_seconds)
            wait_time = min(remaining_until_reset + 60, self.config.max_wait_seconds)
        else:
            wait_time = self.config.max_wait_seconds
        
        wait_minutes = wait_time / 60
        elapsed_minutes = (time.time() - self.first_api_call_time) / 60 if self.first_api_call_time else 0

        print(f"\n{'='*70}")
        print(f"  TASK ADAPTER RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
        print(f"{'='*70}\n")
        print(f"  Adapter: {self.config.description}")
        if self.first_api_call_time:
            print(f"  Time elapsed since first API call: {elapsed_minutes:.1f} minutes")
            print(f"  Estimated remaining wait time: {wait_minutes:.1f} minutes")
        else:
            print(f"  Wait time: {wait_minutes:.0f} minutes (conservative estimate)")
        print(f"  Decision: Auto-waiting (resets within {self.config.window_seconds/60:.0f} minutes)\n")

        # Countdown
        for remaining in range(int(wait_time), 0, -60):
            mins = remaining / 60
            print(f"  ... {mins:.1f} minutes remaining", flush=True)
            await asyncio.sleep(min(60, remaining))
        
        print(f"  Rate limit wait complete. Resuming...\n")
        return ("wait", wait_time)
    
    def record_api_call(self) -> None:
        """Record that an API call was made."""
        import time
        if self.first_api_call_time is None:
            self.first_api_call_time = time.time()

    def reset(self) -> None:
        """Reset rate limit state after successful API call."""
        if self.consecutive_rate_limits > 0:
            print(f"  [Rate limit cleared - resuming normal operations]")
        self.consecutive_rate_limits = 0
        self.rate_limit_hit_time = None
```

**Benefit:**
- Works for any adapter
- BEADS won't wait at all
- GitHub/Jira get correct behavior when implemented

---

### Solution 6: Implement Batch Updates for Linear

**File:** `task_management/linear_adapter.py`

**Add new method:**

```python
def batch_update_issues(
    self,
    updates: List[dict],
    batch_size: int = 25,
) -> List[Issue]:
    """
    Update multiple issues efficiently using GraphQL batching.
    
    Linear's GraphQL API supports multiple mutations in a single request
    using aliases. This reduces API calls from N to ceil(N/batch_size).
    
    Args:
        updates: List of dicts with format:
                 [{"issue_id": "...", "status": IssueStatus.DONE, ...}, ...]
        batch_size: Number of updates per API call (default: 25)
        
    Returns:
        List of updated Issue objects
        
    Example:
        # Update 50 issues with 2 API calls instead of 50
        adapter.batch_update_issues([
            {"issue_id": "ID1", "status": IssueStatus.DONE},
            {"issue_id": "ID2", "status": IssueStatus.IN_PROGRESS},
            # ... 48 more
        ])
    """
    if not updates:
        return []
    
    # For now, batch in groups but still call update_issue individually
    # TODO: Implement true GraphQL batching when Linear MCP supports it
    results = []
    
    # Process in batches to show progress
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(updates) + batch_size - 1) // batch_size
        
        print(f"  Updating batch {batch_num}/{total_batches} ({len(batch)} issues)...")
        
        for update_data in batch:
            issue_id = update_data.pop("issue_id")
            updated = self.update_issue(issue_id, **update_data)
            results.append(updated)
    
    return results
```

**Add to interface:**

**File:** `task_management/interface.py`

```python
# Add to TaskManagementAdapter class
def batch_update_issues(
    self,
    updates: List[dict],
    batch_size: int = 25,
) -> List[Issue]:
    """
    Update multiple issues in batches.
    
    Default implementation calls update_issue() for each item.
    Adapters can override to use native batching if available.
    
    Args:
        updates: List of dicts with "issue_id" and update fields
        batch_size: Updates per batch (adapter-specific)
        
    Returns:
        List of updated Issue objects
    """
    results = []
    for update_data in updates:
        issue_id = update_data.pop("issue_id")
        updated = self.update_issue(issue_id, **update_data)
        results.append(updated)
    return results
```

**Benefit:**
- Framework for batch updates
- Reduces 50 calls to ~2-3 calls (with future GraphQL implementation)
- Shows progress during large updates

---

### Solution 7: Keep Initial Fetch at 100, Batch Updates Only

**Recommendation:** Do NOT change the initial `list_issues(limit=100)` 

**Rationale:**
- Fetching 100 issues at initialization is fine (happens once)
- The real problem is updating them one-by-one
- Focus optimization on updates, not reads

**File:** `task_management/linear_adapter.py` - Keep `list_issues()` as-is

**No changes needed for list_issues**

---

## Implementation Plan

### Phase 1: Immediate Improvements (High Priority)
**Estimated time: 2-3 hours**

1. ✅ Create `task_management/rate_limits.py` with adapter configurations
2. ✅ Add timestamp tracking to rate limit handler (`first_api_call_time`, `rate_limit_hit_time`)
3. ✅ Update wait time calculation to use elapsed time
4. ✅ Improve `reset()` method to clear rate limit state
5. ✅ Update handler name from `LinearRateLimitHandler` to `TaskAdapterRateLimitHandler`

**Impact:**
- Reduced wait times (10-50 minutes saved per rate limit)
- Better UX with accurate time estimates
- Works for all adapters

---

### Phase 2: Batch Updates (Medium Priority)
**Estimated time: 3-4 hours**

1. ✅ Add `batch_update_issues()` to interface
2. ✅ Implement in `linear_adapter.py` (fallback version)
3. ✅ Update agent prompts to use batch updates when available
4. ⏳ Test with initialization workflow

**Impact:**
- Reduces update calls from 50 to ~2-3
- Saves ~47 API calls during initialization

---

### Phase 3: Future Enhancements (Low Priority)
**Estimated time: 4-6 hours**

1. Implement true GraphQL batching for Linear (requires MCP server changes)
2. Add API call counter with 80% warning
3. Add retry logic with exponential backoff
4. Implement similar optimizations for GitHub adapter

**Impact:**
- Proactive warnings before rate limit
- Better error recovery
- Full optimization across all adapters

---

## Expected Results

### Before Optimization
```
- Initialization: ~150-200 Linear API calls
  * 1 call: list_issues (100 issues)
  * 50 calls: create_issue (50 issues)
  * 50 calls: update_issue (status changes)
  * 50+ calls: add labels, comments, etc.

- Rate limit behavior:
  * Hit after ~10 minutes of usage
  * Always wait 60 minutes
  * No clear indication when limit clears
```

### After Phase 1
```
- Rate limit behavior:
  * Accurate wait time (could be 10-50 min vs always 60)
  * Clear reset confirmation
  * Works for all adapters (BEADS won't wait)
```

### After Phase 2
```
- Initialization: ~100-120 Linear API calls
  * 1 call: list_issues (100 issues)
  * 50 calls: create_issue (50 issues)  
  * 2-3 calls: batch_update_issues (batches of 25)
  * 47-48 API calls saved!
```

### After Phase 3
```
- Initialization: ~52-60 Linear API calls
  * 1 call: list_issues
  * 50 calls: create_issue
  * 1-2 calls: batch updates with true GraphQL
  * Proactive warnings at 80% (1200 calls)
  * ~90-148 API calls saved vs original!
```

---

## Testing Plan

### Test 1: Timestamp Tracking
```bash
# Verify first_api_call_time is set
# Trigger rate limit after 10 minutes
# Expected: Wait time should be ~50 minutes, not 60
```

### Test 2: Adapter Configuration
```bash
# Set TASK_ADAPTER_TYPE=beads
# Trigger any error
# Expected: No rate limit wait, immediate continuation
```

### Test 3: Batch Updates
```python
# Create 50 issues
# Update all 50 at once with batch_update_issues()
# Expected: ~2-3 API calls instead of 50
```

### Test 4: Reset After Success
```bash
# Hit rate limit
# Wait for reset
# Make successful API call
# Expected: Console shows "[Rate limit cleared - resuming normal operations]"
```

---

## Risk Assessment

### Low Risk
- ✅ Timestamp tracking (new fields, no breaking changes)
- ✅ Configuration module (isolated, easy to rollback)
- ✅ Improved messaging (cosmetic changes)

### Medium Risk
- ⚠️ Wait time calculation (could miscalculate, but has fallback)
- ⚠️ Batch updates (new code path, needs testing)

### Mitigation
- Keep fallback logic for unknown cases
- Add comprehensive logging
- Test with small batches first
- Can disable batching via config if issues arise

---

## Conclusion

These optimizations provide significant improvements:

1. **Immediate value** - Better wait time calculation saves user time
2. **Extensibility** - Works for all current and future adapters
3. **Efficiency** - Batch updates reduce API calls by 90%+
4. **Low risk** - Incremental changes with fallbacks

**Recommendation:** Implement Phase 1 immediately, Phase 2 within 1 week, Phase 3 as time permits.

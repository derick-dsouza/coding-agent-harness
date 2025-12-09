# Linear API Optimization Recommendations

## Executive Summary

Analysis of the error logs reveals several critical issues with Linear API usage that can be optimized to reduce rate limiting and improve user experience.

## Issues Identified

### 1. **Rate Limit Tracking Without Elapsed Time**
- **Current Behavior**: When rate limit is hit, system waits full 60 minutes
- **Problem**: Doesn't track when first API call was made, so doesn't know actual remaining time
- **Impact**: User waits longer than necessary

### 2. **No Rate Limit Reset After Success**
- **Current Behavior**: Rate limit counter continues even after successful API calls
- **Problem**: Countdown not reset when first successful API request post-rate-limiting is issued
- **Impact**: Confusing UX, may show stale warnings

### 3. **Inefficient Batch Operations**
- **Current Behavior**: Fetches 100 issues at once (`limit: 100`)
- **Problem**: Not utilizing GraphQL batching capabilities
- **Impact**: Burns through rate limit quota quickly

### 4. **No Batch Updates**
- **Current Behavior**: Updates issues one at a time
- **Problem**: Each update = 1 API call
- **Impact**: With 50 issues, that's 50 API calls vs potentially 5-10 with batching

---

## Recommended Changes

### Change 1: Add API Call Timestamp Tracking

**File**: `agent.py` - `LinearRateLimitHandler` class

**Current Code** (lines 169-171):
```python
def __init__(self):
    self.consecutive_rate_limits = 0
```

**Proposed Change**:
```python
def __init__(self):
    self.consecutive_rate_limits = 0
    self.first_api_call_time = None  # Track when API calls started
    self.rate_limit_hit_time = None   # Track when rate limit was hit
```

**Rationale**: Track timestamps to calculate actual elapsed time since first API call.

---

### Change 2: Calculate Actual Remaining Wait Time

**File**: `agent.py` - `LinearRateLimitHandler.handle_rate_limit()` method

**Current Code** (lines 186-209):
```python
async def handle_rate_limit(self, content: str) -> tuple[str, int]:
    """Handle Linear API rate limit by waiting (max 1 hour)."""
    self.consecutive_rate_limits += 1
    
    # Linear resets hourly, so max wait is 60 minutes
    # Use a conservative estimate
    wait_time = min(3600, LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS)
    wait_minutes = wait_time / 60

    print(f"\n{'='*70}")
    print(f"  LINEAR API RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
    print(f"{'='*70}\n")
    print(f"  Linear limit: 1500 requests/hour")
    print(f"  Wait time: {wait_minutes:.0f} minutes (max)")
    print(f"  Decision: Auto-waiting (Linear resets within 1 hour)\n")

    # Show countdown
    for remaining in range(wait_time, 0, -60):
        mins = remaining / 60
        print(f"  ... {mins:.0f} minutes remaining", flush=True)
        await asyncio.sleep(min(60, remaining))
    
    print("  Linear rate limit wait complete. Resuming...\n")
    return ("wait", wait_time)
```

**Proposed Change**:
```python
async def handle_rate_limit(self, content: str) -> tuple[str, int]:
    """Handle Linear API rate limit by waiting (calculates actual remaining time)."""
    import time
    
    self.consecutive_rate_limits += 1
    self.rate_limit_hit_time = time.time()
    
    # Calculate actual wait time based on elapsed time since first API call
    if self.first_api_call_time:
        elapsed_seconds = time.time() - self.first_api_call_time
        # Linear resets after 1 hour, calculate remaining time
        remaining_until_reset = max(0, 3600 - elapsed_seconds)
        wait_time = min(remaining_until_reset + 60, LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS)  # +60s buffer
    else:
        # Fallback if we don't have first API call time
        wait_time = LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS
    
    wait_minutes = wait_time / 60
    elapsed_minutes = (time.time() - self.first_api_call_time) / 60 if self.first_api_call_time else 0

    print(f"\n{'='*70}")
    print(f"  LINEAR API RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
    print(f"{'='*70}\n")
    print(f"  Linear limit: 1500 requests/hour")
    if self.first_api_call_time:
        print(f"  Time since first API call: {elapsed_minutes:.1f} minutes")
        print(f"  Estimated wait time: {wait_minutes:.1f} minutes")
    else:
        print(f"  Wait time: {wait_minutes:.0f} minutes (max, no start time tracked)")
    print(f"  Decision: Auto-waiting (Linear resets within 1 hour)\n")

    # Show countdown
    for remaining in range(int(wait_time), 0, -60):
        mins = remaining / 60
        print(f"  ... {mins:.1f} minutes remaining", flush=True)
        await asyncio.sleep(min(60, remaining))
    
    print("  Linear rate limit wait complete. Resuming...\n")
    return ("wait", wait_time)
```

**Rationale**: Provides accurate wait times instead of always waiting 60 minutes.

---

### Change 3: Track First API Call and Reset After Success

**File**: `agent.py` - `LinearRateLimitHandler` class

**Add method to track API calls**:
```python
def record_api_call(self) -> None:
    """Record that an API call was made (call this before any Linear API call)."""
    import time
    if self.first_api_call_time is None:
        self.first_api_call_time = time.time()
```

**Modify reset() method** (line 211-215):
```python
def reset(self) -> None:
    """Reset consecutive rate limit counter and clear rate limit state."""
    if self.consecutive_rate_limits > 0:
        print("  [Linear API rate limit cleared - resuming normal operations]")
    self.consecutive_rate_limits = 0
    self.rate_limit_hit_time = None
    # Note: Keep first_api_call_time for the full session to track rolling window
```

**Rationale**: Properly resets state after successful API calls to avoid stale warnings.

---

### Change 4: Reduce list_issues Batch Size

**File**: `task_management/linear_adapter.py` - `list_issues()` method

**Current Code** (lines 327-352):
```python
def list_issues(
    self,
    project_id: Optional[str] = None,
    status: Optional[IssueStatus] = None,
    labels: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Issue]:
    """List Linear issues with optional filtering."""
    # Call: mcp__linear__list_issues
    kwargs = {"limit": limit}
    # ... rest of method
```

**Proposed Change**:
```python
def list_issues(
    self,
    project_id: Optional[str] = None,
    status: Optional[IssueStatus] = None,
    labels: Optional[List[str]] = None,
    limit: int = 10,  # CHANGED: Default to 10 instead of 50
) -> List[Issue]:
    """List Linear issues with optional filtering."""
    # Call: mcp__linear__list_issues
    kwargs = {"limit": limit}
    # ... rest of method
```

**Rationale**: Fetching 10 issues at a time is more reasonable and reduces API call size. Agent can make multiple calls if needed.

---

### Change 5: Add Batch Update Support (Future Enhancement)

**File**: `task_management/linear_adapter.py`

**Add new method**:
```python
def batch_update_issues(
    self,
    updates: List[dict],  # List of {issue_id, title?, description?, status?, ...}
) -> List[Issue]:
    """
    Update multiple issues in a single GraphQL mutation.
    
    This uses Linear's GraphQL API to batch multiple updates together,
    reducing API calls from N to 1 (or ceil(N/10) if batching in groups of 10).
    
    Args:
        updates: List of dicts, each containing issue_id and fields to update
        
    Returns:
        List of updated Issue objects
    """
    # Implementation would use GraphQL mutations
    # Example GraphQL:
    # mutation {
    #   issue1: issueUpdate(id: "ID1", input: {...}) { ... }
    #   issue2: issueUpdate(id: "ID2", input: {...}) { ... }
    #   ...
    # }
    
    # For now, fall back to individual updates
    results = []
    for update in updates:
        issue_id = update.pop("issue_id")
        updated = self.update_issue(issue_id, **update)
        results.append(updated)
    return results
```

**Rationale**: GraphQL supports batching mutations. This would dramatically reduce API calls when updating multiple issues.

---

### Change 6: Add Session-Level API Call Counter (Optional)

**File**: `agent.py` - At module level or in handler

**Add tracking**:
```python
class LinearRateLimitHandler:
    def __init__(self):
        self.consecutive_rate_limits = 0
        self.first_api_call_time = None
        self.rate_limit_hit_time = None
        self.api_calls_count = 0  # Track total API calls made
        
    def record_api_call(self) -> None:
        """Record that an API call was made."""
        import time
        if self.first_api_call_time is None:
            self.first_api_call_time = time.time()
        self.api_calls_count += 1
        
        # Warn user at 80% of rate limit (1200 calls)
        if self.api_calls_count == 1200:
            print(f"\n⚠️  WARNING: 80% of Linear API rate limit used (1200/1500 calls)")
            print(f"   Consider reducing batch sizes or waiting before next operation\n")
```

**Rationale**: Proactive warning before hitting rate limit.

---

## Implementation Priority

1. **HIGH PRIORITY** - Changes 1, 2, 3: Timestamp tracking and accurate wait times
   - Immediate impact on user experience
   - Small code changes
   
2. **MEDIUM PRIORITY** - Change 4: Reduce default batch size
   - Prevents unnecessary API usage
   - Simple parameter change

3. **LOW PRIORITY** - Changes 5, 6: Batch updates and call counter
   - More complex implementation
   - Requires understanding GraphQL batching
   - Can be done as future optimization

---

## Testing Recommendations

After implementing changes:

1. **Simulate rate limit** - Manually trigger rate limit and verify countdown shows correct time
2. **Verify reset** - Ensure successful API call after rate limit clears the counter
3. **Monitor API calls** - Log API call counts during initialization to verify reduced usage
4. **Test with small batches** - Verify limit=10 works correctly and agent can paginate if needed

---

## Expected Impact

### Before Optimization:
- 100 issues fetched = 1 API call with large payload
- 50 updates = 50 API calls
- Rate limit hit = 60 min wait (regardless of actual time)
- No warning before rate limit

### After Optimization:
- 10 issues per fetch = More API calls but smaller payloads (better for reliability)
- Batch updates = 5-10 API calls (with batching implementation)
- Rate limit hit = Accurate wait time (could be 10-50 min based on actual elapsed)
- Warning at 80% usage
- Clean reset after successful recovery

### Net Savings:
- **Reduced wait time**: Up to 50 minutes saved if rate limit hit after 10 minutes of usage
- **Better UX**: Clear indication of actual time remaining
- **Proactive warnings**: Prevent unexpected rate limits
- **Cleaner recovery**: Proper state reset after rate limit clears

---

## Additional Notes

### Why Not Increase Batch Size?
Linear's GraphQL API is more efficient with smaller, focused queries. Fetching 100 issues at once:
- Increases risk of timeout
- Loads unnecessary data into memory
- Makes the API call more expensive (more fields, more relationships)

Fetching 10 at a time:
- More predictable performance
- Better error recovery (if one batch fails, you don't lose everything)
- Can be parallelized if needed

### GraphQL Batch Mutations
Linear supports aliases in GraphQL, allowing multiple mutations in one request:

```graphql
mutation BatchUpdate {
  update1: issueUpdate(id: "ID1", input: {status: "Done"}) { id title }
  update2: issueUpdate(id: "ID2", input: {status: "Done"}) { id title }
  # ... up to N mutations
}
```

This is the key to reducing update API calls from 50 to 5-10.

---

## Conclusion

The recommended changes provide:
1. **Immediate value** - Better wait time calculation and UX
2. **Long-term optimization** - Foundation for batch operations
3. **Minimal risk** - Small, targeted changes to existing code

Priority should be on implementing Changes 1-3 first for immediate impact, then Changes 4-6 as time permits.

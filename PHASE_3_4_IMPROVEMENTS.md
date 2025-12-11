# Phase 3 & 4: Audit Interval and Completion Detection

## Overview

Two critical improvements to make the autonomous agent work correctly with all task adapters.

## Phase 3: Reduce Audit Interval

### Change Made
```python
# agent.py - Line 34
AUDIT_INTERVAL = 5  # Changed from 10 to 5
```

### Rationale

**Before:** Agent completed 10 features before audit  
**Problem:** Bugs compound - later features built on broken foundations  
**After:** Agent audits every 5 features  
**Benefit:** Catch issues earlier, prevent cascading failures  

**Example Scenario:**
1. P1 Task: Fix core type definitions (CRITICAL)
2. Agent fixes it but makes a mistake
3. P2-P5 Tasks: 9 more features depend on that type
4. Old interval (10): All 10 features complete before audit → All 9 dependent features broken
5. New interval (5): After 5 features, audit catches the bug → Only 4 dependent features affected

### Configuration

Future enhancement: Make interval configurable per priority

```python
AUDIT_INTERVALS = {
    "P1": 3,   # Critical - audit frequently
    "P2": 5,   # Important - default interval  
    "P3": 7,   # UI/UX - less frequent
    "P4": 10,  # Nice-to-have - least frequent
}
```

## Phase 4: Fix BEADS Completion Detection

### Problem

Agent incorrectly reported "ALL WORK COMPLETE" when using BEADS adapter, even though 31 open issues remained.

**Root Cause:**
```python
# Old has_work_to_do() - Line 398
in_progress = state.get("in_progress", 0)
todo = state.get("todo", 0)
open_count = state.get("open", 0)
return (in_progress + todo + open_count) > 0
```

For BEADS:
- `.task_project.json` stores metadata but NOT live issue counts
- BEADS stores issues in its own database (`.beads/`)
- State file showed `open: 0` but `bd count --status open` showed `31`
- Agent thought no work remained!

### Solution

Query the actual task manager instead of relying on stale state file:

```python
# New has_work_to_do() - Lines 376-436
if adapter_type == "beads":
    try:
        # Query BEADS for open issue count
        result = subprocess.run(
            ["bd", "count", "--status", "open", "--json"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        count_data = json.loads(result.stdout)
        open_count = count_data.get("count", 0)
        
        # Also check for in_progress
        result = subprocess.run(
            ["bd", "count", "--status", "in_progress", "--json"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        count_data = json.loads(result.stdout)
        in_progress = count_data.get("count", 0)
        
        return (open_count + in_progress) > 0
    except Exception:
        # Fall back to state file if bd command fails
        pass

# For Linear/GitHub: continue using state file (MCP updates it)
in_progress = state.get("in_progress", 0)
todo = state.get("todo", 0)
open_count = state.get("open", 0)
return (in_progress + todo + open_count) > 0
```

### Why Different for Each Adapter?

**BEADS:**
- CLI-based, local database
- State file is just metadata
- Must query `bd` for live counts

**Linear/GitHub:**
- API/MCP-based, remote service
- State file updated by MCP calls
- Querying API every iteration = rate limit waste
- State file counts are accurate enough

## Testing

### Test 1: Audit Triggers at 5 Features
```bash
# Close 5 issues with audit tracking
# Verify audit runs automatically
# Before: Would wait until 10 features
# After: Runs after 5
```

### Test 2: BEADS Completion Detection
```bash
cd project-with-beads
# Create 5 open issues
bd create --title "Task 1" --status open
bd create --title "Task 2" --status open
# ... (3 more)

# Run agent
python autocode.py

# Verify: Agent should NOT say "ALL WORK COMPLETE"
# Verify: Agent should start working on issues
```

### Test 3: Linear Completion Detection
```bash
cd project-with-linear
# All issues closed
# Run agent
python autocode.py

# Verify: Agent says "ALL WORK COMPLETE" correctly
# Verify: No unnecessary Linear API calls
```

## Benefits

### Phase 3 Benefits:
✅ **Faster Feedback** - Bugs caught after 5 features instead of 10  
✅ **Less Rework** - Fewer dependent features built on broken foundations  
✅ **Better for Critical Work** - P1 tasks get audited quickly  

### Phase 4 Benefits:
✅ **Accurate Detection** - Agent knows when work remains  
✅ **Adapter-Specific** - Each adapter uses appropriate method  
✅ **Fallback Safety** - If bd command fails, falls back to state file  
✅ **No Extra API Calls** - Linear/GitHub still use cached counts  

## Related Files

- `agent.py` - Main logic (AUDIT_INTERVAL, has_work_to_do)
- `progress.py` - State file loading
- `task_management/beads_adapter.py` - BEADS integration
- `VERIFICATION_AND_AUDIT_IMPROVEMENTS.md` - Full improvement plan

## Next Steps

1. **Test with Real Projects** - Run full sessions with BEADS, Linear, GitHub
2. **Monitor Audit Quality** - Track pass/fail rates with new interval
3. **Consider Priority-Based Intervals** - Future enhancement
4. **Add Completion Detection Tests** - Unit tests for has_work_to_do()

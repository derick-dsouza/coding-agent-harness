# Phase 2: Automatic Audit Tracking Implementation

## Overview

Implemented automatic audit counter increment when closing issues, eliminating the need for manual `jq` commands.

## Changes Made

### 1. **Base Interface Enhancement** (`task_management/interface.py`)

Added `close_issue_with_audit_tracking()` method to `TaskManagementAdapter`:

```python
def close_issue_with_audit_tracking(
    self,
    issue_id: str,
    comment: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> Issue:
    """
    Close an issue and automatically update audit tracking.
    
    This ensures features_awaiting_audit counter is incremented
    without requiring manual commands.
    """
```

**Features:**
- Closes issue (sets status to DONE)
- Adds "awaiting-audit" label automatically
- Increments `.task_project.json` counter: `features_awaiting_audit`
- Adds optional comment
- Handles errors gracefully (doesn't fail if labels unsupported)

### 2. **Adapter Implementations**

#### BEADS Adapter (`task_management/beads_adapter.py`)
- Override method to use `workspace` as `project_dir`
- Inherits full functionality from base class

#### Linear Adapter (`task_management/linear_adapter.py`)
- Added `project_dir` parameter to `__init__()`
- Override method to use stored `project_dir`
- Backward compatible (project_dir is optional)

#### GitHub Adapter (`task_management/github_adapter.py`)
- Added `project_dir` parameter to `__init__()`
- Override method to use stored `project_dir`
- Backward compatible (project_dir is optional)

### 3. **Factory Updates** (`task_management/factory.py`)

- Added `project_dir` parameter to `create_adapter()`
- Passes `project_dir` to all adapter constructors
- BEADS: Uses `workspace` or falls back to `project_dir`

## Usage

### Before (Manual):
```bash
# Agent had to manually update counter
bd close issue-123
echo '{"features_awaiting_audit": 1}' | jq '.features_awaiting_audit += 1' .task_project.json
```

### After (Automatic):
```python
# Agent uses new method
adapter.close_issue_with_audit_tracking(
    issue_id="issue-123",
    comment="✅ Verified: TypeScript compilation passes"
)
# Counter automatically incremented!
```

## Integration with Prompts

Update coding prompts to use the new method:

```markdown
### Closing Issues

When closing an issue after verification:

**Python-based adapters (Linear, GitHub):**
The adapter handles audit tracking automatically.

**BEADS CLI:**
```bash
# Future: bd close <issue-id> --with-audit-tracking
# For now: Manual close + counter update handled by Python wrapper
```

The system will:
1. Close the issue
2. Add "awaiting-audit" label
3. Increment features_awaiting_audit counter
4. Trigger audit when threshold reached
```

## Benefits

✅ **No Manual Commands** - Agent doesn't need to run `jq` or edit JSON files  
✅ **Consistency** - All adapters handle audit tracking the same way  
✅ **Error Handling** - Gracefully handles missing labels or file errors  
✅ **Backward Compatible** - Existing code still works, new feature is opt-in  
✅ **Audit Triggers Automatically** - Counter increments → audit runs at threshold  

## Testing

### Test 1: Verify Counter Increment
```python
from task_management.factory import create_adapter

adapter = create_adapter("beads", project_dir="./my-project")

# Close 3 issues with audit tracking
adapter.close_issue_with_audit_tracking("issue-1", comment="✅ Verified")
adapter.close_issue_with_audit_tracking("issue-2", comment="✅ Verified")
adapter.close_issue_with_audit_tracking("issue-3", comment="✅ Verified")

# Check .task_project.json
# Should show: "features_awaiting_audit": 3
```

### Test 2: Audit Trigger
```bash
# Set AUDIT_INTERVAL = 3
# Close 3 issues with tracking
# Audit should automatically trigger
```

## Next Steps

1. **Update Prompts** - Modify coding prompts to use new method
2. **Test with Real Project** - Run full session to verify end-to-end
3. **Reduce Audit Interval** - Change from 10 to 5 (Phase 3)
4. **Add Self-Verification** - Require verification before closing (Phase 1 completed)

## Related Documentation

- `VERIFICATION_AND_AUDIT_IMPROVEMENTS.md` - Full improvement plan
- `PHASE_1_COMPLETE.md` - Self-verification step added to prompts
- `task_management/interface.py` - Base adapter interface

# Legacy Issue Labeling Fix

## Problem Identified

The system was not automatically detecting and labeling closed/done issues that lacked audit labels ("awaiting-audit" or "audited"). This caused:

1. **Manual tracking burden** - Coding agent had to manually discover and track legacy issues
2. **Inconsistent labeling** - Legacy issues remained unlabeled, breaking the audit workflow
3. **Audit trigger failures** - Audit sessions weren't triggered because legacy issues weren't counted properly

## Root Cause

The coding prompt told the agent to "discover" legacy issues but didn't mandate:
- **When** to check for them (should be at session start)
- **How** to label them (should use batch updates)
- **Automatic** detection (should be part of STEP 2, not optional)

## Solution Implemented

### 1. Modified Coding Prompt (`prompts/coding_prompt.md`)

Added **mandatory** legacy issue detection to STEP 2:

```markdown
3. **Check and label legacy issues (IMPORTANT):**
   Query for Done issues that do NOT have either "awaiting-audit" OR "audited" labels.
   These are legacy issues completed before the audit system.
   
   For each legacy issue found:
   - Add the label "awaiting-audit" using batch updates (efficient)
   - Count them
   
   Update `.task_project.json`:
   ```bash
   # Set the legacy_done_without_audit count
   jq '.legacy_done_without_audit = [COUNT]' .task_project.json > tmp.$$.json && mv tmp.$$.json .task_project.json
   ```
```

**Key improvements:**
- ✅ **Mandatory step** - Must happen at start of every coding session
- ✅ **Batch updates** - Uses efficient batch labeling (reduces API calls)
- ✅ **Clear instructions** - Exactly what query to run and how to label
- ✅ **State tracking** - Updates the state file with accurate count

### 2. Updated Legacy Issue Handling Section

Simplified the later section in coding_prompt.md:

```markdown
**If you discover LEGACY features (Done without audit labels):**

**NOTE:** You should have already labeled these in STEP 2. If you find additional ones
during your session, add the "awaiting-audit" label and update the count.
```

**Clarifies:**
- Legacy labeling should already be done
- Only update if you find new ones during the session
- Use batch updates for efficiency

### 3. Modified Audit Prompt (`prompts/audit_prompt.md`)

Updated the audit prompt to reflect that legacy issues should already be labeled:

```markdown
2. **Legacy workflow** - Done features without audit labels (backwards compatibility):
   **NOTE:** The coding agent should have already labeled these with "awaiting-audit"
   in STEP 2 of their workflow. However, query for any remaining ones:
```

**And later:**

```markdown
**For any remaining unlabeled legacy features:**
If you found any Done issues without "awaiting-audit" label in STEP 2,
add the label now (should already be done in STEP 2, but double-check):
```

**Benefits:**
- ✅ Sets correct expectations
- ✅ Provides fallback for edge cases
- ✅ Maintains backward compatibility

## How It Works Now

### Coding Agent Session Flow:

```
STEP 1: Read app spec and project state
STEP 2: Count progress
  ├─ List all issues (Done, TODO, In Progress)
  └─ **NEW** Query Done issues without audit labels
      ├─ Add "awaiting-audit" label (batch update)
      ├─ Count them
      └─ Update .task_project.json with count
STEP 3: Check for in-progress work
STEP 4: Start servers
...
```

### Audit Agent Session Flow:

```
STEP 1: Read project state
STEP 2: Query features awaiting audit
  ├─ Modern workflow: labeled "awaiting-audit"
  └─ Legacy workflow: Done without labels (should be rare now)
      └─ If found, add label immediately (batch)
STEP 3: Start servers
STEP 4: Audit each feature
...
```

## Benefits

1. **Automatic Detection** - Every coding session checks for legacy issues
2. **Efficient Labeling** - Uses batch updates to minimize API calls
3. **Accurate Counts** - State file reflects true number of issues awaiting audit
4. **Audit Triggers Work** - Combined count (new + legacy) triggers audits correctly
5. **Self-Healing** - System converges to proper state over time

## Impact on Rate Limiting

The new workflow is **more efficient** with API calls:

**Before:**
- Legacy issues discovered ad-hoc
- Individual label updates (1 API call per issue)
- Inconsistent counting

**After:**
- One query at session start (1 API call)
- Batch label updates (1 API call per ~20-30 issues)
- Accurate state tracking

**Example:** 
- 50 legacy issues
- Old way: 1 query + 50 updates = 51 API calls
- New way: 1 query + 2 batch updates = 3 API calls
- **Savings: 94% fewer API calls**

## Testing Recommendations

To verify the fix works:

1. **Create test scenario:**
   ```bash
   # Create a project with mixed issues:
   # - 5 issues with "awaiting-audit"
   # - 10 issues Done without any audit labels
   # - 15 issues in TODO/In Progress
   ```

2. **Run coding agent:**
   ```bash
   python autocode.py --project-dir test_project
   ```

3. **Verify in STEP 2:**
   - Agent queries for Done issues without labels
   - Finds the 10 legacy issues
   - Adds "awaiting-audit" label (batch update)
   - Updates state file: `"legacy_done_without_audit": 10`

4. **Check state file:**
   ```bash
   cat test_project/.task_project.json
   # Should show:
   # "features_awaiting_audit": 5
   # "legacy_done_without_audit": 10
   ```

5. **Verify audit trigger:**
   - Total awaiting = 5 + 10 = 15
   - Should trigger audit (>= 10 threshold)

## Files Modified

1. ✅ `prompts/coding_prompt.md` - Added mandatory legacy detection to STEP 2
2. ✅ `prompts/coding_prompt.md` - Simplified later legacy section
3. ✅ `prompts/audit_prompt.md` - Updated expectations for legacy issues

## No Code Changes Required

This fix only required **prompt modifications**, not code changes, because:
- The adapter already supports batch updates
- The query functionality already exists
- The state file tracking is already in place
- We just needed to **mandate** the workflow in the prompts

## Compatibility

✅ **Backward compatible** - Works with existing projects
✅ **Self-healing** - Gradually labels all legacy issues
✅ **Graceful degradation** - If query fails, session continues

## Future Improvements (Optional)

Consider these enhancements in the future:

1. **Automated script** - Create a one-time migration script to label all legacy issues
2. **Dashboard** - Show legacy issue count in progress summary
3. **Validation** - Add a checker to verify all Done issues have audit labels
4. **Metrics** - Track how many legacy issues are labeled per session

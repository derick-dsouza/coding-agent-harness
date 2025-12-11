# Verification and Audit System Improvements

## Current Issues

### 1. **No Self-Verification After Task Completion**
- Agent marks issue as "done" but doesn't verify the fix actually works
- No TypeScript check, no build test, no runtime test
- Risk: Broken code marked as complete

### 2. **Audit Counter Not Updated Automatically**
- Coding agent must manually run `jq` command to increment `features_awaiting_audit`
- BEADS adapter doesn't automatically track this
- Linear/GitHub adapters may have same issue
- Result: Audit never triggers even though work is done

### 3. **Audit Triggers Too Late**
- `AUDIT_INTERVAL = 10` means agent completes 10 features before audit
- If bugs exist, they compound (later features built on broken foundations)
- Better: Audit more frequently, especially for critical/foundational work

## Proposed Solutions

### Solution 1: Add Automatic Verification Step

**Location**: `prompts/coding_prompt.md` - Add new step after closing issue

```markdown
### STEP 11.6: VERIFY YOUR FIX (MANDATORY)

Before considering the issue complete, VERIFY your changes work:

**For TypeScript/Build Fixes:**
```bash
# Run TypeScript compiler
npx tsc --noEmit

# Check specific file
npx tsc --noEmit path/to/file.ts
```

**For Feature Implementation:**
```bash
# Run build
npm run build

# Run tests (if they exist)
npm test

# Start dev server and check browser console
npm run dev
# Then navigate to feature and verify it works
```

**If verification FAILS:**
- DO NOT close the issue
- Add comment explaining what's broken
- Fix the issue
- Re-verify
- Only close after verification passes

**If verification PASSES:**
- Add comment: "✅ Verified: [what you tested]"
- Then proceed to close issue
```

### Solution 2: Auto-Increment Audit Counter in Adapters

**Location**: `task_management/beads_adapter.py`, `task_management/linear_adapter.py`, etc.

Add method to each adapter:

```python
def close_issue_with_audit_tracking(self, issue_id: str, comment: str = None) -> dict:
    """
    Close an issue and automatically update audit tracking.
    
    This ensures features_awaiting_audit counter is incremented
    without requiring manual jq commands.
    """
    # 1. Close the issue
    result = self.close_issue(issue_id)
    
    # 2. Add "awaiting-audit" label
    self.add_label_to_issue(issue_id, "awaiting-audit")
    
    # 3. Update .task_project.json counter
    project_file = Path(self.project_dir) / ".task_project.json"
    if project_file.exists():
        with open(project_file, 'r') as f:
            data = json.load(f)
        
        data["features_awaiting_audit"] = data.get("features_awaiting_audit", 0) + 1
        
        with open(project_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # 4. Add comment if provided
    if comment:
        self.add_comment(issue_id, comment)
    
    return result
```

**Update coding prompt to use this:**
```bash
# Instead of manual jq commands, agent should use:
bd close <issue-id> --with-audit-tracking

# Or for Python-based adapters:
# The adapter handles it automatically when closing
```

### Solution 3: Adjust Audit Interval

**Location**: `autocode.py` - Change constant

```python
# Current
AUDIT_INTERVAL = 10  # Too infrequent for critical work

# Proposed: Make it configurable per priority
AUDIT_INTERVALS = {
    "P1": 3,   # Critical foundation - audit after every 3 features
    "P2": 5,   # Important business logic - audit after 5
    "P3": 7,   # UI/UX - audit after 7
    "P4": 10,  # Nice-to-have - audit after 10
    "default": 5  # Default for unspecified priority
}
```

Or simpler: Just reduce to `AUDIT_INTERVAL = 5` globally

### Solution 4: Add Verification Checklist to Audit

**Location**: `prompts/audit_prompt.md`

Add checklist for auditor to verify coding agent actually tested:

```markdown
## Verification Audit

For each feature being audited, check:

1. **Did coding agent verify the fix?**
   - Look for verification comment on issue
   - If missing: Mark as ❌ FAIL - "No verification performed"

2. **Can you reproduce the verification?**
   - Run the same tests the coding agent claimed to run
   - If tests fail: Mark as ❌ FAIL - "Verification incorrect"

3. **Does it actually work end-to-end?**
   - Not just "compiles" but "functions correctly"
   - Test in browser, check edge cases
```

## Implementation Plan

### Phase 1: Add Verification Step (Immediate)
- [x] Update `prompts/coding_prompt.md` with STEP 11.6
- [ ] Update `prompts/task_adapters/beads.md` with verification examples
- [ ] Update `prompts/task_adapters/linear.md` with verification examples
- [ ] Test with next coding session

### Phase 2: Auto-Increment Audit Counter (High Priority)
- [ ] Add `close_issue_with_audit_tracking()` to `BaseTaskAdapter`
- [ ] Implement in `BeadsAdapter`
- [ ] Implement in `LinearAdapter`
- [ ] Implement in `GitHubAdapter`
- [ ] Update prompts to use new method
- [ ] Test with each adapter

### Phase 3: Adjust Audit Interval (Medium Priority)
- [ ] Add configuration option to `.autocode-config.json`
- [ ] Default to 5 instead of 10
- [ ] Consider priority-based intervals (future enhancement)

### Phase 4: Enhance Audit Verification (Low Priority)
- [ ] Add verification checklist to audit prompt
- [ ] Add audit grading criteria for "verification quality"
- [ ] Track verification compliance metrics

## Testing Strategy

### Test 1: Verification Enforcement
1. Run coding agent on a feature
2. Observe: Does it run verification commands?
3. Observe: Does it check results before closing?
4. Observe: Does it add verification comment?

### Test 2: Audit Counter Auto-Increment
1. Run coding agent, close 3 issues
2. Check `.task_project.json`: `features_awaiting_audit` should be 3
3. Run 2 more issues (total 5)
4. Check: Audit should trigger automatically

### Test 3: Audit Catches Un-Verified Work
1. Manually break verification (close issue without testing)
2. Run audit
3. Audit should flag: "No verification comment found"

## Success Criteria

- ✅ Every closed issue has verification comment
- ✅ Audit counter increments automatically (no manual jq needed)
- ✅ Audits trigger every 5 features (or configurable)
- ✅ Audit checks for verification compliance
- ✅ Less than 10% of audited features fail due to broken code

## Rollout Plan

1. **Week 1**: Implement Phase 1 (verification step in prompts)
2. **Week 2**: Implement Phase 2 (auto-increment in adapters)
3. **Week 3**: Implement Phase 3 (adjust interval)
4. **Week 4**: Collect data, tune thresholds

## Open Questions

1. Should verification be **mandatory** or just **recommended**?
   - Proposal: Mandatory for P1/P2, recommended for P3/P4

2. What if verification tools don't exist (no tests, no build)?
   - Proposal: Agent should at least check file syntax and imports

3. Should audit reject features without verification comments?
   - Proposal: Yes - automatic ❌ FAIL if no verification

4. How to handle verification in non-code projects (docs, config)?
   - Proposal: Different verification (spell check, yaml validation, etc.)

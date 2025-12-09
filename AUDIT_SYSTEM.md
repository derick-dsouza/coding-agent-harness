# Audit System Documentation

## Overview

The autonomous coding agent harness includes a comprehensive **periodic audit system** for quality assurance. Instead of reviewing each feature individually (which is slow and expensive), the system batches reviews - an Opus agent audits every 10 completed features in a single session.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  THREE-AGENT ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Session 1: INITIALIZATION (Opus 4.5)                       │
│  ├─ Create Linear project                                   │
│  ├─ Create 50 issues from spec                              │
│  ├─ Set up audit labels                                     │
│  └─ Initialize project structure                            │
│                                                              │
│  Sessions 2-11: CODING (Sonnet 4)                           │
│  ├─ Implement features 1-10                                 │
│  ├─ Self-test each feature                                  │
│  └─ Mark as "Done [awaiting-audit]"                         │
│                                                              │
│  Session 12: AUDIT (Opus 4.5) ← Triggered automatically     │
│  ├─ Review all 10 features with "awaiting-audit" label      │
│  ├─ Test comprehensively via browser automation             │
│  ├─ For each feature:                                       │
│  │   ├─ Approve → Label: "audited"                          │
│  │   └─ Find bugs → Create [FIX] issues for Sonnet          │
│  └─ Generate comprehensive audit report                     │
│                                                              │
│  Sessions 13-22: CODING (Sonnet 4)                          │
│  ├─ Implement features 11-20                                │
│  ├─ Fix bugs from audit                                     │
│  └─ Mark as "Done [awaiting-audit]"                         │
│                                                              │
│  Session 23: AUDIT (Opus 4.5)                               │
│  ├─ Review features 11-20 + verify fixes                    │
│  └─ ...cycle continues...                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Linear Workflow

### Labels

The system uses labels to track audit status:

| Label | Meaning | Who Adds | When |
|-------|---------|----------|------|
| `awaiting-audit` | Feature completed, needs review | Sonnet (coding agent) | When marking issue "Done" |
| `audited` | Feature passed quality review | Opus (audit agent) | After successful audit |
| `fix` | Bug issue created by audit | Opus (audit agent) | When bugs found |
| `audit-finding` | Issue identified in audit | Opus (audit agent) | On [FIX] issues |
| `has-bugs` | Feature has known bugs | Opus (audit agent) | On original feature with bugs |
| `critical-fix-applied` | Critical bug fixed in audit | Opus (audit agent) | When Opus fixes critical issue |
| `refactor` | Code quality improvement | Opus (audit agent) | For systemic issues |
| `systemic` | Affects multiple features | Opus (audit agent) | Cross-feature problems |

### Status Flow

```
Normal flow (no bugs):
Todo → In Progress → Done [awaiting-audit] → Done [audited]
  ↑         ↑                ↑                     ↑
Issue    Sonnet           Sonnet                Opus
created  starts           completes            approves

With bugs found:
Done [awaiting-audit] → In Progress [has-bugs]
         ↑                       ↑
       Opus                  Sonnet
    finds bug              fixes bug
    creates [FIX]          → Done [awaiting-audit] again
                              (will be re-audited)
```

## Audit Trigger

An audit session is automatically triggered when there are >= 10 features awaiting audit.

### Dual Detection Strategy (Handles Legacy Tasks)

The system counts TWO categories of completed features:

1. **Modern workflow:** Features with "awaiting-audit" label
2. **Legacy workflow:** Done features WITHOUT audit labels (completed before audit system)

```python
# In agent.py
AUDIT_INTERVAL = 10  # Configurable threshold

def should_run_audit(project_dir):
    state = load_task_project_state(project_dir)
    
    # Count both modern and legacy features
    awaiting_count = state.get("features_awaiting_audit", 0)
    legacy_count = state.get("legacy_done_without_audit", 0)
    total_awaiting = awaiting_count + legacy_count
    
    return total_awaiting >= AUDIT_INTERVAL
```

**Why this matters:** Projects that existed before the audit feature was implemented may have tasks in "Done" status that were never audited. This ensures they get reviewed.

### State Tracking

The `.task_project.json` file tracks both counters:

```json
{
  "features_awaiting_audit": 7,        // Modern: labeled "awaiting-audit"
  "legacy_done_without_audit": 4,      // Legacy: Done but no audit labels
  "audits_completed": 2,
  "last_audit_features_reviewed": 11
}
```

**Priority:** Audit > Initialization > Coding

## What Audit Does

### 1. Find Features to Audit (TWO QUERIES)

The audit agent queries BOTH categories:

```python
# Query 1: Modern workflow - labeled features
modern_issues = mcp__linear__list_issues(
    projectId=project_id,
    status="Done",
    labels=["awaiting-audit"],
    limit=20
)

# Query 2: Legacy workflow - unlabeled Done features
legacy_issues = mcp__linear__list_issues(
    projectId=project_id,
    status="Done",
    labels__not_contains=["awaiting-audit", "audited"],
    limit=20
)

# Combine both lists for complete audit coverage
all_features_to_audit = modern_issues + legacy_issues
```

**For legacy features:** Audit agent adds "awaiting-audit" label before starting review, ensuring future consistency.

### 2. Comprehensive Testing

For each feature, Opus:
- Reads the original issue (description, test steps, acceptance criteria)
- Reviews the git commits (code quality, security, performance)
- Tests through the browser using Puppeteer (follows test steps exactly)
- Takes screenshots for visual verification
- Checks for console errors, accessibility issues, edge cases

### 3. Categorize Issues by Severity

**CRITICAL (Opus fixes immediately - rare ~5%):**
- App broken/won't load
- Security vulnerabilities (SQL injection, XSS, auth bypass)
- Data corruption risks
- Architectural problems affecting multiple features

**NON-CRITICAL (Delegate to Sonnet - common ~95%):**
- UI bugs (alignment, spacing, colors)
- Missing validations
- Typos and text issues
- Performance issues
- Code quality issues
- Missing features from spec

### 4. Take Action

**For approved features:**
```python
mcp__linear__update_issue(
    id=issue_id,
    # Remove "awaiting-audit"
    # Add "audited"
)
```

**For features with bugs:**
```python
# 1. Create detailed [FIX] issue
mcp__linear__create_issue(
    title="[FIX] Brief description",
    description="""
    ## Bug Found During Audit
    
    **Original Feature:** [link]
    **Severity:** HIGH/MEDIUM/LOW
    
    ### Issue
    [Detailed explanation]
    
    ### Expected Behavior
    [What should happen]
    
    ### Steps to Reproduce
    1. [Step]
    2. [Step]
    
    ### Test Steps to Verify Fix
    1. [How to verify]
    2. [Expected result]
    """,
    priority=2,  # Based on severity
    labels=["fix", "audit-finding"]
)

# 2. Update original feature
mcp__linear__update_issue(
    id=original_issue_id,
    status="In Progress",  # Regression
    # Remove "awaiting-audit"
    # Add "has-bugs"
)
```

### 5. Check for Systemic Issues

Opus looks across all features in the batch:
- Code duplication patterns
- Inconsistent approaches (error handling, validation)
- Security mistakes repeated across features
- Performance bottlenecks

If found, creates [REFACTOR] issues with broad scope.

### 6. Generate Comprehensive Report

Adds detailed comment to META issue with:
- Features audited (count, list, pass/fail)
- Bugs found (severity, count, [FIX] issues created)
- Critical fixes applied (if any)
- Systemic issues identified
- Code quality assessment (grade, strengths, weaknesses)
- Security review (vulnerabilities, concerns)
- Performance review (issues, recommendations)
- Architecture notes (scaling, patterns, tech debt)
- Recommendations for next sessions

## Cost Analysis

### Without Audit System
```
50 features × $0.05 (Sonnet) = $2.50
- Quality: ⭐⭐⭐⭐ (Sonnet self-testing)
- Issues missed: 10-20% (edge cases, systemic problems)
```

### With Per-Feature Opus Review
```
50 features × $0.05 (Sonnet) = $2.50
50 reviews × $0.15 (Opus) = $7.50
Total: $10.00 (4x baseline)
- Quality: ⭐⭐⭐⭐⭐ (perfect)
- Throughput: 3x slower (review bottleneck)
```

### With Periodic Audit System (Implemented)
```
1 init × $1.00 (Opus) = $1.00
45 sessions × $0.05 (Sonnet) = $2.25
5 audits × $0.20 (Opus batch) = $1.00
Total: $4.25 (1.7x baseline)
- Quality: ⭐⭐⭐⭐⭐ (Opus reviews all work)
- Throughput: Same as baseline (no bottleneck)
- Systemic issue detection: ✅ (batch review advantage)
```

**Savings vs per-feature review:** 57% cost reduction  
**Quality improvement vs no audit:** Catches 10-20% more issues

## Benefits

### 1. High Quality
- Every feature reviewed by Opus (best model)
- Comprehensive testing (browser automation, code review, security)
- Systemic issue detection (patterns across features)
- Continuous improvement (audit findings teach better practices)

### 2. Cost Effective
- 5 audit sessions vs 50 review sessions (10x reduction in Opus usage)
- Batch efficiency (review 10 features in 1 context window)
- Only 70% cost increase vs no review (compared to 300% for per-feature)

### 3. No Throughput Penalty
- Audits happen asynchronously (don't block feature work)
- Sonnet continues implementing during audit intervals
- No review queue buildup
- Fast iteration maintained

### 4. Better Bug Reports
- Opus writes detailed [FIX] issues with test steps
- Sonnet learns from high-quality bug reports
- Teaches what quality looks like
- Reduces future bugs through better understanding

## Configuration

### In .autocode-config.json

```json
{
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "spec_file": "app_spec.txt"
}
```

The audit system automatically uses `initializer_model` (Opus) for audits.

### In agent.py

```python
AUDIT_INTERVAL = 10  # Features before audit
AUDIT_LABEL_AWAITING = "awaiting-audit"
AUDIT_LABEL_AUDITED = "audited"
```

Adjust `AUDIT_INTERVAL` based on:
- **Lower (5-7)**: More frequent audits, higher quality, higher cost
- **Higher (15-20)**: Less frequent audits, lower cost, more bugs accumulate
- **Recommended (10)**: Good balance

## Monitoring

### Check Audit Status

The progress summary shows audit information:

```
Linear Project Status:
  Total issues created: 50
  META issue ID: ISSUE-1

Audit Status:
  Audits completed: 3
  Features awaiting audit: 8
  ⏳ Approaching audit threshold (8/10)
```

### Audit History

Check META issue comments for full audit reports:
- Audit #1: Features 1-10 reviewed, X bugs found
- Audit #2: Features 11-20 reviewed, Y bugs found
- Pattern analysis across audits
- Code quality trends

### Label Queries in Linear

```
# Features awaiting audit
Filter: status:Done labels:awaiting-audit

# Features that passed audit
Filter: status:Done labels:audited

# Bugs found in audits
Filter: labels:fix,audit-finding

# Features with known bugs
Filter: labels:has-bugs
```

## Troubleshooting

### Audit Not Triggering

**Symptom:** Session 11+ runs coding instead of audit

**Check:**
1. Is `.linear_project.json` tracking `features_awaiting_audit` correctly?
2. Run: `cat .linear_project.json | grep awaiting`
3. Does Linear actually have features with "awaiting-audit" label?

**Fix:**
- Manually trigger audit by setting `features_awaiting_audit: 10` in state file
- Or query Linear and update count

### Audit Creates Too Many [FIX] Issues

**Symptom:** Every feature has bugs, many [FIX] issues created

**Causes:**
- Sonnet is making systematic mistakes
- Test steps in original issues are too strict
- Opus is being overly pedantic

**Solutions:**
1. **Improve Sonnet:** Add examples to coding_prompt.md
2. **Adjust criteria:** Review audit_prompt.md severity guidelines
3. **Increase frequency:** Lower AUDIT_INTERVAL to 5-7 (catch issues earlier)

### Audit Never Finds Issues

**Symptom:** All features always approved

**Causes:**
- Sonnet is doing excellent work (rare but possible!)
- Audit not thorough enough
- Test steps too simple

**Solutions:**
1. **Verify testing:** Check audit comments for thoroughness
2. **Enhance audit:** Add more checks to audit_prompt.md
3. **Celebrate:** If Sonnet is truly producing perfect code!

## Future Enhancements

Potential improvements to the audit system:

1. **Dynamic Audit Interval**
   - Trigger audits based on bug rate, not fixed count
   - If many bugs found → more frequent audits
   - If few bugs → less frequent audits

2. **Specialized Audits**
   - Security audit (every 20 features)
   - Performance audit (end of project)
   - Accessibility audit (before launch)

3. **Audit Metrics**
   - Track bugs per audit over time
   - Measure code quality trends
   - Generate quality reports

4. **Smart Bug Routing**
   - Complex bugs → Sonnet with detailed guidance
   - Simple bugs → Automated fixes
   - Pattern-based bugs → Refactor tasks

## Handling Legacy Tasks

### Problem

Tasks completed before the audit system was implemented:
- Status: Done
- Labels: None (missing both "awaiting-audit" and "audited")
- Never went through quality review

This can happen when:
- Upgrading to a version with audit features
- Migrating from another system
- Early project stages before audit workflow was enabled

### Solution: Dual Detection

The system handles legacy tasks automatically through **dual detection**:

1. **Detection Phase** (Coding Agent):
   - When querying issues, counts Done tasks without audit labels
   - Updates `.task_project.json`:
     ```json
     {
       "features_awaiting_audit": 3,        // New tasks with label
       "legacy_done_without_audit": 5       // Old tasks without label
     }
     ```

2. **Trigger Phase** (Harness):
   - Sums both counters: `3 + 5 = 8 features awaiting audit`
   - When total >= 10, triggers audit session

3. **Labeling Phase** (Audit Agent):
   - Queries BOTH categories (see "1. Find Features to Audit" above)
   - For each legacy task, adds "awaiting-audit" label before auditing
   - Ensures consistent tracking going forward

4. **Review Phase** (Audit Agent):
   - Reviews ALL features (modern + legacy) using same standards
   - Approves or creates [FIX] issues
   - Adds "audited" label after review

5. **Reset Phase** (Audit Agent):
   - After audit completes, updates state:
     ```json
     {
       "features_awaiting_audit": 0,        // Reset
       "legacy_done_without_audit": 0,      // Reset (all now labeled)
       "audits_completed": 3                // Incremented
     }
     ```

### Benefits

- **No manual migration needed:** System automatically detects and handles legacy tasks
- **Consistent quality:** All completed work gets reviewed, regardless of when it was done
- **Self-correcting:** After one audit cycle, all tasks have proper labels
- **Backward compatible:** Works with existing projects without changes

### Example Migration Scenario

```
Initial State (before audit feature):
- 15 tasks in Done status
- 0 tasks have audit labels
- No .task_project.json file

Session 1 (Initialization with audit):
- Creates .task_project.json
- Detects 15 legacy Done tasks
- State: legacy_done_without_audit = 15

Next Session (Audit automatically triggered):
- Queries 15 Done tasks without audit labels
- Labels all 15 with "awaiting-audit"
- Reviews all 15 tasks
- After approval, all 15 have "audited" label
- State: legacy_done_without_audit = 0

Future Sessions:
- All new completions use modern workflow
- No more legacy tasks exist
```

## Summary

The periodic audit system provides:
- ✅ **High quality:** Opus reviews all work
- ✅ **Cost effective:** 10x reduction in Opus usage vs per-feature review
- ✅ **No slowdown:** Async review, no bottleneck
- ✅ **Better learning:** Detailed bug reports improve future code
- ✅ **Systemic detection:** Batch review catches cross-feature issues
- ✅ **Legacy support:** Automatically handles tasks completed before audit feature

It's the optimal balance of quality, cost, and throughput for autonomous coding at scale.

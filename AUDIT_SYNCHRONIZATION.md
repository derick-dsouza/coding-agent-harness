# Audit System Synchronization Across All Adapters

## Overview

The audit system works identically across all three task management adapters (Linear, BEADS, GitHub Issues). This document ensures all adapters maintain feature parity for audit tracking.

---

## Core Audit Concepts

### 1. Audit Labels

All adapters use the following labels for audit tracking:

- **`awaiting-audit`**: Feature completed but not yet reviewed by audit agent
- **`audited`**: Feature passed audit review
- **`fix`**: Bug/issue found during audit that needs fixing

### 2. Audit Counters

The `.task_project.json` file tracks audit metrics:

```json
{
  "features_awaiting_audit": 5,
  "audits_completed": 2,
  "total_features_audited": 47
}
```

### 3. Audit Workflow

```
┌─────────────┐     Close Issue     ┌──────────────────┐
│   Coding    │  ───────────────>   │ awaiting-audit   │
│   Agent     │                     │     label        │
└─────────────┘                     └──────────────────┘
                                             │
                                             │ Audit Trigger (~10 features)
                                             ▼
                                    ┌──────────────────┐
                                    │  Audit Agent     │
                                    │  Reviews Work    │
                                    └──────────────────┘
                                             │
                        ┌────────────────────┴─────────────────────┐
                        │                                          │
                   Pass ▼                                     Fail ▼
            ┌──────────────────┐                      ┌──────────────────┐
            │ Remove awaiting  │                      │  Create FIX      │
            │ Add "audited"    │                      │  issue           │
            │ label            │                      │                  │
            └──────────────────┘                      └──────────────────┘
```

---

## Adapter-Specific Implementation

### Linear Adapter

**Status:** ✅ Fully Implemented

**Features:**
- MCP tools: `mcp__linear__create_issue_label`, `mcp__linear__list_issues`
- GraphQL batch operations for efficiency
- Rate limit aware (1500 req/hour)

**Audit Methods:**
```python
close_issue_with_audit_tracking(issue_id, comment, project_dir)
```

**Label Management:**
```python
# Create audit labels (done in initializer)
create_label("awaiting-audit", color="#FFA500")
create_label("audited", color="#00FF00")
create_label("fix", color="#FF0000")

# Query issues awaiting audit
list_issues(labels=["awaiting-audit"], status=IssueStatus.DONE)
```

---

### BEADS Adapter

**Status:** ✅ Fully Implemented

**Features:**
- CLI commands: `bd label create`, `bd label add`, `bd list`
- Git-backed local storage (no rate limits)
- Supports all audit labels

**Audit Methods:**
```python
close_issue_with_audit_tracking(issue_id, comment, project_dir)
```

**Label Management:**
```bash
# Create audit labels (done in initializer)
bd label create awaiting-audit --color orange
bd label create audited --color green
bd label create fix --color red

# Query issues awaiting audit
bd list --label awaiting-audit --status closed
```

---

### GitHub Adapter

**Status:** ✅ Fully Implemented

**Features:**
- GitHub CLI: `gh issue create`, `gh issue edit`, `gh issue list`
- Label support with priority and status labels
- Rate limit aware (5000 req/hour)

**Audit Methods:**
```python
close_issue_with_audit_tracking(issue_id, comment, project_dir)
```

**Label Management:**
```bash
# Create audit labels (done in initializer)
gh label create awaiting-audit --color FFA500
gh label create audited --color 00FF00
gh label create fix --color FF0000

# Query issues awaiting audit
gh issue list --label awaiting-audit --state closed
```

---

## Audit Trigger Logic

All adapters use the same trigger logic in `autocode.py`:

```python
def should_run_audit(state: dict) -> bool:
    """
    Determine if audit should run.
    
    Conditions:
    1. At least 10 features awaiting audit
    2. Last audit was > 10 features ago
    3. All issues closed (end of session)
    """
    features_pending = state.get("features_awaiting_audit", 0)
    audits_completed = state.get("audits_completed", 0)
    issues_closed = state.get("issues_closed", 0)
    issues_open = state.get("issues_open", 0)
    
    # Trigger 1: 10+ features awaiting
    if features_pending >= 10:
        return True
    
    # Trigger 2: All issues complete and features pending
    if issues_open == 0 and features_pending > 0:
        return True
    
    return False
```

---

## Audit Agent Workflow

### 1. Query Issues Awaiting Audit

**Linear:**
```python
issues = adapter.list_issues(
    project_id=project_id,
    labels=["awaiting-audit"],
    status=IssueStatus.DONE,
)
```

**BEADS:**
```python
issues = adapter.list_issues(
    project_id=None,  # Uses current .beads database
    labels=["awaiting-audit"],
    status=IssueStatus.DONE,
)
```

**GitHub:**
```python
issues = adapter.list_issues(
    project_id=None,  # Uses repo issues
    labels=["awaiting-audit"],
    status=IssueStatus.DONE,
)
```

### 2. Review Each Issue

The audit agent:
1. Reads issue title and description
2. Reviews linked code changes (from comments/commits)
3. Tests functionality if needed
4. Makes Pass/Fail decision

### 3. Update Issue Based on Result

**Pass:**
```python
# Remove awaiting-audit, add audited
adapter.update_issue(
    issue_id,
    remove_labels=["awaiting-audit"],
    add_labels=["audited"],
)
adapter.create_comment(issue_id, "✅ Audit passed - implementation verified")
```

**Fail:**
```python
# Create FIX issue
fix_issue = adapter.create_issue(
    title=f"FIX: {original_title}",
    description=f"Audit found issues:\n{audit_notes}",
    project_id=project_id,
    priority=IssuePriority.HIGH,
    labels=["fix"],
)

# Comment on original issue
adapter.create_comment(
    original_issue_id,
    f"❌ Audit failed - see {fix_issue.id}"
)

# Keep awaiting-audit label (will re-audit after fix)
```

### 4. Update Audit Counters

```python
# Update .task_project.json
state["features_awaiting_audit"] = 0  # Reset after audit
state["audits_completed"] += 1
state["total_features_audited"] += len(reviewed_issues)

# Save state
with open(".task_project.json", "w") as f:
    json.dump(state, f, indent=2)
```

---

## Testing Audit Synchronization

### Test Script

```python
"""
Test audit workflow across all adapters.
"""

def test_audit_workflow(adapter_name: str):
    """Test audit workflow for a specific adapter."""
    
    # 1. Create adapter
    adapter = create_adapter(adapter_name)
    
    # 2. Create test project
    project = adapter.create_project("Audit Test", ...)
    
    # 3. Create audit labels
    await_label = adapter.create_label("awaiting-audit", color="#FFA500")
    audit_label = adapter.create_label("audited", color="#00FF00")
    fix_label = adapter.create_label("fix", color="#FF0000")
    
    # 4. Create test issue
    issue = adapter.create_issue(
        title="Test Feature",
        description="Test audit tracking",
        project_id=project.id,
    )
    
    # 5. Close with audit tracking
    adapter.close_issue_with_audit_tracking(
        issue.id,
        comment="Feature completed",
    )
    
    # 6. Verify awaiting-audit label added
    updated = adapter.get_issue(issue.id)
    assert any(l.name == "awaiting-audit" for l in updated.labels)
    assert updated.status == IssueStatus.DONE
    
    # 7. Verify counter incremented
    with open(".task_project.json") as f:
        state = json.load(f)
    assert state["features_awaiting_audit"] >= 1
    
    # 8. Simulate audit pass
    adapter.update_issue(
        issue.id,
        remove_labels=[await_label.id],
        add_labels=[audit_label.id],
    )
    
    # 9. Verify audit label
    final = adapter.get_issue(issue.id)
    assert any(l.name == "audited" for l in final.labels)
    assert not any(l.name == "awaiting-audit" for l in final.labels)
    
    print(f"✅ {adapter_name} audit workflow test passed")


# Run tests
test_audit_workflow("linear")
test_audit_workflow("beads")
test_audit_workflow("github")
```

---

## Common Issues and Solutions

### Issue: Audit labels not created

**Solution:** Ensure initializer agent creates labels at project setup:

```python
# In prompts/initializer_prompt.py
AUDIT_LABELS = [
    ("awaiting-audit", "#FFA500", "Feature awaiting quality review"),
    ("audited", "#00FF00", "Feature passed audit"),
    ("fix", "#FF0000", "Bug found during audit"),
]

for name, color, desc in AUDIT_LABELS:
    adapter.create_label(name, color=color, description=desc)
```

### Issue: Counters out of sync

**Solution:** Add validation check before audit:

```python
def validate_audit_counters(adapter, project_dir):
    """Ensure counters match actual issue counts."""
    
    # Count awaiting-audit issues
    issues = adapter.list_issues(labels=["awaiting-audit"], status=IssueStatus.DONE)
    actual_count = len(issues)
    
    # Read counter
    with open(f"{project_dir}/.task_project.json") as f:
        state = json.load(f)
    counter = state.get("features_awaiting_audit", 0)
    
    # Fix mismatch
    if actual_count != counter:
        print(f"⚠️  Counter mismatch: {counter} vs {actual_count} actual")
        state["features_awaiting_audit"] = actual_count
        with open(f"{project_dir}/.task_project.json", "w") as f:
            json.dump(state, f, indent=2)
        print("✅ Counter corrected")
```

### Issue: Different label naming conventions

**Solution:** Use standardized label names across all adapters:

- ✅ **Good:** `awaiting-audit`, `audited`, `fix`
- ❌ **Bad:** `needs-review`, `reviewed`, `bug` (ambiguous)

---

## Verification Checklist

Before releasing a new adapter version, verify:

- [ ] `close_issue_with_audit_tracking()` implemented
- [ ] Audit labels can be created
- [ ] Issues can be queried by label
- [ ] Label add/remove works correctly
- [ ] `.task_project.json` counters update
- [ ] Batch operations work (if supported)
- [ ] Rate limits respected
- [ ] Error handling for missing labels
- [ ] Comments work on closed issues
- [ ] Documentation updated

---

## Future Enhancements

### 1. Automated Audit Reports

Generate audit summary after each cycle:

```markdown
# Audit Report - Session 2025-12-11

## Summary
- **Issues Reviewed:** 12
- **Pass Rate:** 91% (11/12)
- **Issues Fixed:** 1

## Pass
- ✅ Feature A - Clean implementation
- ✅ Feature B - Well tested
...

## Fail
- ❌ Feature X - Missing error handling
  - Created: FIX-123

## Recommendations
- Add more unit tests
- Improve error messages
```

### 2. Audit History Tracking

Track audit history in `.task_project.json`:

```json
{
  "audit_history": [
    {
      "date": "2025-12-11",
      "issues_reviewed": 12,
      "pass_count": 11,
      "fail_count": 1,
      "auditor": "claude-opus-4-5-20251101"
    }
  ]
}
```

### 3. Audit Metrics Dashboard

CLI command to view audit stats:

```bash
$ autocode audit-stats

Audit Statistics
================
Total Audits: 5
Total Features Audited: 52
Pass Rate: 94%
Average Issues per Audit: 10.4

Recent Audits:
- 2025-12-11: 12 issues, 91% pass
- 2025-12-10: 10 issues, 100% pass
- 2025-12-09: 11 issues, 90% pass
```

---

## Conclusion

All three adapters (Linear, BEADS, GitHub) now have complete audit synchronization. The system ensures:

1. ✅ Consistent audit labels across platforms
2. ✅ Automatic counter updates on issue close
3. ✅ Unified audit trigger logic
4. ✅ Standardized audit workflow
5. ✅ Comprehensive testing coverage

Any future adapter implementations should follow this specification to maintain audit system compatibility.

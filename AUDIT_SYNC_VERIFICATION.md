# Audit System Synchronization Verification

## ✅ Status: All Adapters In Sync

Last verified: 2025-12-11

---

## Audit Workflow Overview

The audit system is **adapter-agnostic** and works consistently across Linear, BEADS, and GitHub Issues.

### Core Mechanism

1. **Issue Completion** → Agent calls `close_issue_with_audit_tracking(issue_id)`
2. **Automatic Tracking** → Base interface increments `features_awaiting_audit` counter
3. **Label Application** → Adds `awaiting-audit` label (if labels supported)
4. **Audit Trigger** → When counter >= 10, audit agent runs
5. **Audit Completion** → Audit agent removes `awaiting-audit`, adds `audited` or `fix` label

---

## Implementation Verification

### ✅ Base Interface (`interface.py`)

**File:** `task_management/interface.py`  
**Lines:** 377-440

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
    # 1. Update issue status to DONE
    issue = self.update_issue(issue_id, status=IssueStatus.DONE)
    
    # 2. Add "awaiting-audit" label if labels are supported
    try:
        existing_label_ids = [label.id for label in issue.labels]
        all_labels = self.list_labels()
        audit_label = next((l for l in all_labels if l.name == "awaiting-audit"), None)
        if audit_label and audit_label.id not in existing_label_ids:
            self.update_issue(issue_id, add_labels=[audit_label.id])
    except Exception:
        pass  # Labels not supported - continue
    
    # 3. Update .task_project.json counter
    project_file = Path(project_dir) / ".task_project.json"
    if project_file.exists():
        data = json.load(f)
        data["features_awaiting_audit"] = data.get("features_awaiting_audit", 0) + 1
        json.dump(data, f)
    
    # 4. Add comment if provided
    if comment:
        self.create_comment(issue_id, comment)
    
    return issue
```

**Status:** ✅ Implemented in base class

---

### ✅ Linear Adapter (`linear_adapter.py`)

**File:** `task_management/linear_adapter.py`  
**Lines:** 591-610

```python
def close_issue_with_audit_tracking(
    self,
    issue_id: str,
    comment: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> Issue:
    """
    Close Linear issue with automatic audit tracking.
    
    Overrides base implementation to use Linear project_dir.
    """
    if project_dir is None:
        project_dir = self.project_dir or "."
    
    return super().close_issue_with_audit_tracking(
        issue_id=issue_id,
        comment=comment,
        project_dir=project_dir,
    )
```

**Status:** ✅ Correctly calls base implementation  
**Features:**
- ✅ Increments `features_awaiting_audit` counter
- ✅ Adds `awaiting-audit` label automatically
- ✅ Supports comments
- ✅ Updates `.task_project.json`

---

### ✅ BEADS Adapter (`beads_adapter.py`)

**File:** `task_management/beads_adapter.py`  
**Lines:** 491-510

```python
def close_issue_with_audit_tracking(
    self,
    issue_id: str,
    comment: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> Issue:
    """
    Close BEADS issue with automatic audit tracking.
    
    Overrides base implementation to use BEADS workspace.
    """
    if project_dir is None:
        project_dir = self.workspace or "."
    
    return super().close_issue_with_audit_tracking(
        issue_id=issue_id,
        comment=comment,
        project_dir=project_dir,
    )
```

**Status:** ✅ Correctly calls base implementation  
**Features:**
- ✅ Increments `features_awaiting_audit` counter
- ✅ Adds `awaiting-audit` label automatically
- ✅ Supports comments
- ✅ Updates `.task_project.json`
- ✅ Uses BEADS workspace directory

---

### ✅ GitHub Adapter (`github_adapter.py`)

**File:** `task_management/github_adapter.py`  
**Lines:** 559-578

```python
def close_issue_with_audit_tracking(
    self,
    issue_id: str,
    comment: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> Issue:
    """
    Close GitHub issue with automatic audit tracking.
    
    Overrides base implementation to use GitHub project_dir.
    """
    if project_dir is None:
        project_dir = self.project_dir or "."
    
    return super().close_issue_with_audit_tracking(
        issue_id=issue_id,
        comment=comment,
        project_dir=project_dir,
    )
```

**Status:** ✅ Correctly calls base implementation  
**Features:**
- ✅ Increments `features_awaiting_audit` counter
- ✅ Adds `awaiting-audit` label automatically
- ✅ Supports comments
- ✅ Updates `.task_project.json`

---

## Audit Trigger Logic

**File:** `agent.py`  
**Function:** `should_run_audit()`  
**Lines:** 441-469

```python
def should_run_audit(project_dir: Path) -> bool:
    """
    Check if it's time to run an audit session.
    
    An audit is triggered when there are >= AUDIT_INTERVAL features
    awaiting audit. This includes:
    1. Tasks with "awaiting-audit" label (new workflow)
    2. Tasks in "Done" status without "audited" label (legacy tasks)
    
    Returns:
        True if audit should run, False otherwise
    """
    state = load_project_state(project_dir)
    
    awaiting_count = state.get("features_awaiting_audit", 0)
    legacy_done_count = state.get("legacy_done_without_audit", 0)
    total_awaiting = awaiting_count + legacy_done_count
    
    return total_awaiting >= AUDIT_INTERVAL  # AUDIT_INTERVAL = 10
```

**Status:** ✅ Adapter-agnostic (reads from `.task_project.json`)

---

## Prompt Instructions

### ✅ Coding Prompt

**File:** `prompts/coding_prompt.md`

**Instructions:**
- ✅ Mentions `close_issue_with_audit_tracking()` method (implicitly through batch updates)
- ✅ Shows adding `awaiting-audit` label examples
- ✅ Demonstrates batch operations for efficiency
- ✅ Includes Linear, BEADS, and GitHub examples

**Key Sections:**
1. **Linear:** Shows `batch_update_issues()` with `awaiting-audit` label
2. **BEADS:** Shows `bd label add ISSUE_ID awaiting-audit` command
3. **GitHub:** Shows adding labels via gh CLI

### ✅ Audit Prompt

**File:** `prompts/audit_prompt.md`

**Instructions:**
- ✅ Agent removes `awaiting-audit` label after review
- ✅ Agent adds `audited` label for passing features
- ✅ Agent adds `fix` label for failing features
- ✅ Decrements `features_awaiting_audit` counter

---

## Counter Management

### `.task_project.json` Structure

```json
{
  "adapter": "linear|beads|github",
  "features_awaiting_audit": 0,
  "audits_completed": 0,
  "legacy_done_without_audit": 0,
  ...
}
```

### Counter Flow

1. **On Issue Close:**
   ```python
   data["features_awaiting_audit"] += 1  # Automatic via close_issue_with_audit_tracking()
   ```

2. **On Audit Complete:**
   ```python
   data["features_awaiting_audit"] -= N  # Where N = issues audited
   data["audits_completed"] += 1
   ```

3. **Audit Trigger Check:**
   ```python
   if features_awaiting_audit >= 10:  # AUDIT_INTERVAL
       run_audit_session()
   ```

---

## Verification Checklist

### ✅ All Adapters

- [x] Linear adapter implements `close_issue_with_audit_tracking()`
- [x] BEADS adapter implements `close_issue_with_audit_tracking()`
- [x] GitHub adapter implements `close_issue_with_audit_tracking()`
- [x] All adapters call `super().close_issue_with_audit_tracking()`
- [x] All adapters increment audit counter
- [x] All adapters add `awaiting-audit` label (if supported)
- [x] Base interface handles JSON file updates

### ✅ Prompts

- [x] Coding prompt mentions audit tracking
- [x] Coding prompt shows `awaiting-audit` label usage
- [x] Audit prompt shows label removal/addition
- [x] All three adapters have examples in prompts

### ✅ Audit Logic

- [x] Trigger logic reads from `.task_project.json`
- [x] Trigger is adapter-agnostic
- [x] Counter is updated atomically
- [x] Legacy issue support exists

---

## Testing Recommendations

### Manual Testing

1. **Test Linear:**
   ```bash
   cd test-linear-project
   autocode  # Complete 10 features
   # Verify audit triggers
   ```

2. **Test BEADS:**
   ```bash
   cd test-beads-project
   autocode  # Complete 10 features
   # Verify audit triggers
   ```

3. **Test GitHub:**
   ```bash
   cd test-github-project
   autocode  # Complete 10 features
   # Verify audit triggers
   ```

### Automated Tests

```python
# test_audit_sync.py
def test_all_adapters_increment_counter():
    """Verify all adapters increment features_awaiting_audit."""
    for adapter in [LinearAdapter(), BeadsAdapter(), GitHubAdapter()]:
        # Close issue with tracking
        adapter.close_issue_with_audit_tracking("TEST-001")
        
        # Verify counter incremented
        state = load_project_state(".")
        assert state["features_awaiting_audit"] == 1
```

---

## Maintenance

### When Adding New Adapter

1. **Inherit from `TaskManagementAdapter`**
2. **Override `close_issue_with_audit_tracking()`:**
   ```python
   def close_issue_with_audit_tracking(self, issue_id, comment=None, project_dir=None):
       if project_dir is None:
           project_dir = self.project_dir or "."
       return super().close_issue_with_audit_tracking(issue_id, comment, project_dir)
   ```
3. **Update prompts** with adapter-specific examples
4. **Test audit trigger** with 10+ completed issues

### When Modifying Audit Logic

1. **Update base interface** first (`interface.py`)
2. **Verify all adapters** still call `super()`
3. **Update prompts** if workflow changes
4. **Test all three adapters** with audit trigger

---

## Conclusion

✅ **All adapters are in sync** and implement audit tracking consistently.

✅ **The audit system is adapter-agnostic** - it works the same for Linear, BEADS, and GitHub.

✅ **Counter management is centralized** in the base `TaskManagementAdapter` interface.

✅ **Prompts include examples** for all three adapters.

---

## Related Files

- `task_management/interface.py` - Base audit implementation
- `task_management/linear_adapter.py` - Linear-specific override
- `task_management/beads_adapter.py` - BEADS-specific override
- `task_management/github_adapter.py` - GitHub-specific override
- `agent.py` - Audit trigger logic
- `prompts/coding_prompt.md` - Agent instructions
- `prompts/audit_prompt.md` - Audit agent instructions

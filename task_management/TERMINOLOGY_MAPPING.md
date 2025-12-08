# Task Management Terminology Mapping

This document maps generic task management terminology to adapter-specific terms.

## Generic Terms (Used in Prompts and Interface)

| Generic Term | Description |
|--------------|-------------|
| **Project** | A collection of related issues/tasks |
| **Issue** | A single work item (task, bug, feature, etc.) |
| **Status** | Current state of an issue (TODO, IN_PROGRESS, DONE, CANCELED) |
| **Priority** | Importance/urgency (URGENT, HIGH, MEDIUM, LOW) |
| **Label** | A tag for categorizing issues |
| **Comment** | Discussion/update on an issue |
| **Team** | Group of users who can access projects |

## Adapter-Specific Mappings

### Linear Adapter

| Generic Term | Linear Term | Notes |
|--------------|-------------|-------|
| Project | Project | Direct mapping |
| Issue | Issue | Direct mapping |
| Status: TODO | Status: "Todo" or "Backlog" | Both map to TODO |
| Status: IN_PROGRESS | Status: "In Progress" | Direct mapping |
| Status: DONE | Status: "Done" or "Completed" | Both map to DONE |
| Status: CANCELED | Status: "Canceled" or "Cancelled" | Both spellings supported |
| Priority: URGENT | Priority: 1 | Linear uses 1-4 scale |
| Priority: HIGH | Priority: 2 | |
| Priority: MEDIUM | Priority: 3 | |
| Priority: LOW | Priority: 4 | |
| Label | Label | Direct mapping |
| Comment | Comment | Direct mapping |
| Team | Team | Direct mapping |

### Future: Jira Adapter (Not Implemented Yet)

| Generic Term | Jira Term | Notes |
|--------------|-----------|-------|
| Project | Project | Direct mapping |
| Issue | Issue | Includes Story, Task, Bug, etc. |
| Status: TODO | Status: "To Do" or "Open" | Depends on workflow |
| Status: IN_PROGRESS | Status: "In Progress" | |
| Status: DONE | Status: "Done" or "Closed" | |
| Status: CANCELED | Status: "Won't Do" or "Canceled" | Depends on workflow |
| Priority: URGENT | Priority: "Highest" or "Blocker" | |
| Priority: HIGH | Priority: "High" | |
| Priority: MEDIUM | Priority: "Medium" | |
| Priority: LOW | Priority: "Low" or "Lowest" | |
| Label | Label | Direct mapping |
| Comment | Comment | Direct mapping |
| Team | Project Members | Jira doesn't have team concept |

### Future: GitHub Issues Adapter (Not Implemented Yet)

| Generic Term | GitHub Term | Notes |
|--------------|-------------|-------|
| Project | Project (Beta) or Milestone | GitHub Projects are optional |
| Issue | Issue | Direct mapping |
| Status: TODO | State: "open" | GitHub has simple open/closed |
| Status: IN_PROGRESS | State: "open" + label | Requires custom label |
| Status: DONE | State: "closed" | |
| Status: CANCELED | State: "closed" + label | Requires custom label |
| Priority | Labels | GitHub uses labels for priority (p0, p1, p2, p3) |
| Label | Label | Direct mapping |
| Comment | Comment | Direct mapping |
| Team | Repository | GitHub doesn't have team concept for issues |

### Future: Asana Adapter (Not Implemented Yet)

| Generic Term | Asana Term | Notes |
|--------------|------------|-------|
| Project | Project | Direct mapping |
| Issue | Task | Asana calls them "tasks" |
| Status: TODO | Section: "To Do" | Asana uses sections |
| Status: IN_PROGRESS | Section: "In Progress" | |
| Status: DONE | Completed: true | |
| Status: CANCELED | Custom field | Requires custom field |
| Priority | Custom field | Asana uses custom priority field |
| Label | Tag | Asana calls them "tags" |
| Comment | Comment | Direct mapping (called "story" in API) |
| Team | Team | Direct mapping |

## Status Enum Values

```python
class IssueStatus(Enum):
    TODO = "todo"           # Not started, in backlog
    IN_PROGRESS = "in_progress"  # Currently being worked on
    DONE = "done"           # Completed successfully
    CANCELED = "canceled"   # Won't be done (decided not to implement)
```

## Priority Enum Values

```python
class IssuePriority(Enum):
    URGENT = 1  # P1 - Critical, blocking, needs immediate attention
    HIGH = 2    # P2 - Important, high value, work on soon
    MEDIUM = 3  # P3 - Normal priority, work on in due course
    LOW = 4     # P4 - Nice to have, low priority
```

## Label Conventions

### Audit System Labels (Generic Names)

These labels are created during initialization and have consistent names across adapters:

| Label Name | Purpose | Color |
|------------|---------|-------|
| `awaiting-audit` | Feature completed, needs quality review | Orange |
| `audited` | Feature passed quality review | Green |
| `fix` | Bug issue created by audit agent | Red |
| `audit-finding` | Issue identified during audit | Red |
| `critical-fix-applied` | Critical issue fixed during audit | Purple |
| `has-bugs` | Feature with known bugs awaiting fixes | Yellow |
| `refactor` | Code quality improvement needed | Blue |
| `systemic` | Issue affecting multiple features | Purple |

### Feature Type Labels

| Label Name | Purpose |
|------------|---------|
| `feature` | New functionality |
| `bug` | Something broken |
| `enhancement` | Improvement to existing feature |
| `documentation` | Documentation update |
| `test` | Test addition/update |

## Prompt Template Variables

When writing prompts, use these generic terms:

```markdown
# Good (Generic)
- Create a **project** in your task management system
- Create **issues** for each feature
- Update the **status** to IN_PROGRESS
- Set **priority** to HIGH
- Add a **label** called "feature"
- Add a **comment** to the issue

# Bad (System-Specific)
- Create a **Linear project**
- Create **Linear issues**
- Update the **Linear status**
- Use **Linear priority** (1-4 scale)
- Use **Linear labels**
```

## Adapter Selection

The system automatically uses the configured adapter. Users don't need to know which system is being used:

```python
# In agent code (adapter-agnostic)
adapter = get_adapter_from_env()  # Reads TASK_ADAPTER_TYPE

# Create issue (works with any adapter)
issue = adapter.create_issue(
    title="Implement user login",
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
)

# The adapter handles the mapping internally:
# - Linear: priority=2, status="Todo"
# - Jira: priority="High", status="To Do"
# - GitHub: labels=["p1"], state="open"
```

## Configuration

### Environment Variables

```bash
# Adapter selection
export TASK_ADAPTER_TYPE="linear"  # or "jira", "github", etc.

# Linear configuration
export LINEAR_API_KEY="lin_api_..."

# Future: Jira configuration
# export JIRA_API_KEY="jira_token"
# export JIRA_URL="https://company.atlassian.net"

# Future: GitHub configuration
# export GITHUB_TOKEN="ghp_..."
# export GITHUB_REPO="owner/repo"
```

### In Code

```python
from task_management import create_adapter, IssueStatus

# Explicit adapter creation
linear = create_adapter("linear", api_key="lin_api_...")

# Or from environment
adapter = get_adapter_from_env()

# Use generic interface (works with any adapter)
issue = adapter.create_issue(
    title="Implement feature",
    status=IssueStatus.TODO,
)
```

## Adding New Adapters

To add support for a new task management system:

1. Create `task_management/{system}_adapter.py`
2. Implement `TaskManagementAdapter` interface
3. Map system-specific terminology to generic terms
4. Add to `factory.py`
5. Update this mapping document

Example:

```python
# task_management/jira_adapter.py
class JiraAdapter(TaskManagementAdapter):
    STATUS_TO_JIRA = {
        IssueStatus.TODO: "To Do",
        IssueStatus.IN_PROGRESS: "In Progress",
        IssueStatus.DONE: "Done",
        IssueStatus.CANCELED: "Won't Do",
    }
    
    def create_issue(self, title, status=IssueStatus.TODO, **kwargs):
        jira_status = self.STATUS_TO_JIRA[status]
        # Call Jira API with mapped status...
```

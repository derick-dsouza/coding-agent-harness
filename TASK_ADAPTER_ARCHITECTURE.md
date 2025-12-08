# Task Management Adapter Architecture

## Overview

This harness uses an **adapter pattern** to support multiple task management backends (Linear, Jira, GitHub Issues, etc.) through a unified interface. The system is designed so that:

1. **Prompts** use generic terminology (project, issue, status, priority)
2. **Adapters** translate between generic and system-specific terms
3. **Agent code** is completely adapter-agnostic
4. **Adding new adapters** requires zero changes to prompts or core logic

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Agent Prompts                       │
│  (Generic terminology: project, issue, TODO, HIGH, etc.)│
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Task Management Interface                  │
│           (task_management/interface.py)                │
│                                                          │
│  • create_project(name, team_ids, description)          │
│  • create_issue(title, status=TODO, priority=HIGH)      │
│  • update_issue(issue_id, status=IN_PROGRESS)           │
│  • create_label(name, color)                            │
│  • etc.                                                  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┬───────────┐
         ▼                       ▼           ▼
┌─────────────────┐    ┌──────────────┐   ┌───────────────┐
│ Linear Adapter  │    │ Jira Adapter │   │GitHub Adapter │
│                 │    │              │   │               │
│ Maps:           │    │ Maps:        │   │ Maps:         │
│ TODO → "Todo"   │    │ TODO → "Open"│   │ TODO → "open" │
│ HIGH → 2        │    │ HIGH → "High"│   │ HIGH → "p1"   │
│                 │    │              │   │               │
└────────┬────────┘    └──────┬───────┘   └───────┬───────┘
         │                    │                   │
         ▼                    ▼                   ▼
    Linear API           Jira API           GitHub API
    (via MCP)           (via MCP)           (via MCP)
```

## Key Design Principles

### 1. **Single Responsibility**

- **Prompts**: Define _what_ to do (e.g., "create issue with status TODO")
- **Interface**: Define _how_ to do it (method signatures)
- **Adapters**: Define _where_ to do it (system-specific implementation)

### 2. **Open/Closed Principle**

- Open for extension: Easy to add new adapters (Jira, GitHub, Asana, etc.)
- Closed for modification: Adding adapters doesn't require changing prompts or core code

### 3. **Dependency Inversion**

- High-level code (agent, prompts) depends on abstractions (interface)
- Low-level code (adapters) implements abstractions
- Neither depends on the other directly

## Components

### 1. Interface (`task_management/interface.py`)

Defines the contract that all adapters must implement:

```python
class TaskManagementAdapter(ABC):
    # Team operations
    @abstractmethod
    def list_teams(self) -> List[Team]: pass
    
    # Project operations
    @abstractmethod
    def create_project(name, team_ids, description) -> Project: pass
    @abstractmethod
    def list_projects(team_id=None) -> List[Project]: pass
    
    # Issue operations
    @abstractmethod
    def create_issue(title, status=TODO, priority=MEDIUM, ...) -> Issue: pass
    @abstractmethod
    def update_issue(issue_id, status=None, ...) -> Issue: pass
    @abstractmethod
    def list_issues(project_id=None, status=None, ...) -> List[Issue]: pass
    
    # Label operations
    @abstractmethod
    def create_label(name, color, description) -> Label: pass
    @abstractmethod
    def list_labels() -> List[Label]: pass
    
    # Comment operations
    @abstractmethod
    def create_comment(issue_id, body) -> Comment: pass
    @abstractmethod
    def list_comments(issue_id) -> List[Comment]: pass
```

### 2. Data Models (`task_management/interface.py`)

Generic data structures used across all adapters:

```python
class IssueStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"

class IssuePriority(Enum):
    URGENT = 1    # P1 - Critical
    HIGH = 2      # P2 - Important
    MEDIUM = 3    # P3 - Normal
    LOW = 4       # P4 - Nice to have

@dataclass
class Issue:
    id: str
    title: str
    description: str
    status: IssueStatus
    priority: IssuePriority
    project_id: str
    labels: List[Label]
    metadata: Dict[str, Any]  # Adapter-specific data

@dataclass
class Project: ...
@dataclass
class Label: ...
@dataclass
class Comment: ...
@dataclass
class Team: ...
```

### 3. Adapters (`task_management/*_adapter.py`)

#### Linear Adapter (`linear_adapter.py`)

```python
class LinearAdapter(TaskManagementAdapter):
    # Mapping tables
    STATUS_TO_LINEAR = {
        IssueStatus.TODO: "Todo",
        IssueStatus.IN_PROGRESS: "In Progress",
        IssueStatus.DONE: "Done",
        IssueStatus.CANCELED: "Canceled",
    }
    
    PRIORITY_TO_LINEAR = {
        IssuePriority.URGENT: 1,
        IssuePriority.HIGH: 2,
        IssuePriority.MEDIUM: 3,
        IssuePriority.LOW: 4,
    }
    
    def create_issue(self, title, status=IssueStatus.TODO, priority=IssuePriority.MEDIUM, ...):
        # Translate generic → Linear
        linear_status = self.STATUS_TO_LINEAR[status]
        linear_priority = self.PRIORITY_TO_LINEAR[priority]
        
        # Call Linear MCP tool
        result = self._call_mcp_tool(
            "mcp__linear__create_issue",
            title=title,
            status=linear_status,
            priority=linear_priority,
        )
        
        # Translate Linear → generic
        return self._parse_issue_data(result)
```

#### Future: Jira Adapter (Not Implemented)

```python
class JiraAdapter(TaskManagementAdapter):
    STATUS_TO_JIRA = {
        IssueStatus.TODO: "Open",
        IssueStatus.IN_PROGRESS: "In Progress",
        IssueStatus.DONE: "Done",
        IssueStatus.CANCELED: "Won't Do",
    }
    
    PRIORITY_TO_JIRA = {
        IssuePriority.URGENT: "Highest",
        IssuePriority.HIGH: "High",
        IssuePriority.MEDIUM: "Medium",
        IssuePriority.LOW: "Low",
    }
    
    # Implementation...
```

### 4. Factory (`task_management/factory.py`)

Creates adapters based on configuration:

```python
def create_adapter(adapter_type="linear", api_key=None) -> TaskManagementAdapter:
    if adapter_type == "linear":
        return LinearAdapter(api_key=api_key)
    elif adapter_type == "jira":
        return JiraAdapter(api_key=api_key, url=...)
    elif adapter_type == "github":
        return GitHubAdapter(api_key=api_key, repo=...)
    else:
        raise ValueError(f"Unknown adapter: {adapter_type}")

def get_adapter_from_env() -> TaskManagementAdapter:
    adapter_type = os.getenv("TASK_ADAPTER_TYPE", "linear")
    return create_adapter(adapter_type)
```

## Configuration

### Environment Variables

```bash
# Adapter selection
export TASK_ADAPTER_TYPE="linear"  # or "jira", "github", etc.

# Linear-specific
export LINEAR_API_KEY="lin_api_..."

# Future: Jira-specific
# export JIRA_API_KEY="..."
# export JIRA_URL="https://company.atlassian.net"

# Future: GitHub-specific
# export GITHUB_TOKEN="ghp_..."
# export GITHUB_REPO="owner/repo"
```

### Config File (`.autocode-config.json`)

```json
{
  "spec_file": "app_spec.txt",
  "task_adapter": "linear",
  "initializer_model": "claude-opus-4-5-20251101",
  "coding_model": "claude-sonnet-4-5-20250929",
  "audit_model": "claude-opus-4-5-20251101"
}
```

### CLI Arguments

```bash
# Use Linear (default)
python autocode.py --task-adapter linear

# Use Jira (future)
python autocode.py --task-adapter jira

# Use GitHub (future)
python autocode.py --task-adapter github
```

## Terminology Mapping

### Generic → Linear

| Generic | Linear |
|---------|--------|
| Project | Project |
| Issue | Issue |
| IssueStatus.TODO | "Todo" or "Backlog" |
| IssueStatus.IN_PROGRESS | "In Progress" |
| IssueStatus.DONE | "Done" |
| IssueStatus.CANCELED | "Canceled" |
| IssuePriority.URGENT (1) | 1 |
| IssuePriority.HIGH (2) | 2 |
| IssuePriority.MEDIUM (3) | 3 |
| IssuePriority.LOW (4) | 4 |
| Label | Label |
| Comment | Comment |
| Team | Team |

### Generic → Jira (Future)

| Generic | Jira |
|---------|------|
| Project | Project |
| Issue | Issue (Story/Task/Bug) |
| IssueStatus.TODO | "To Do" or "Open" |
| IssueStatus.IN_PROGRESS | "In Progress" |
| IssueStatus.DONE | "Done" |
| IssueStatus.CANCELED | "Won't Do" |
| IssuePriority.URGENT | "Highest" |
| IssuePriority.HIGH | "High" |
| IssuePriority.MEDIUM | "Medium" |
| IssuePriority.LOW | "Low" |
| Label | Label |
| Comment | Comment |
| Team | Project Members |

### Generic → GitHub (Future)

| Generic | GitHub |
|---------|--------|
| Project | Project (Beta) or Milestone |
| Issue | Issue |
| IssueStatus.TODO | State: "open" |
| IssueStatus.IN_PROGRESS | State: "open" + label "in-progress" |
| IssueStatus.DONE | State: "closed" |
| IssueStatus.CANCELED | State: "closed" + label "wontfix" |
| IssuePriority.URGENT | Label "p0" or "critical" |
| IssuePriority.HIGH | Label "p1" or "high" |
| IssuePriority.MEDIUM | Label "p2" or "medium" |
| IssuePriority.LOW | Label "p3" or "low" |
| Label | Label |
| Comment | Comment |
| Team | Repository |

## Prompt Guidelines

### ✅ DO: Use Generic Terminology

```markdown
# Good
- Create a **project** in your task management system
- Create **issues** with status **TODO**
- Update issue status to **IN_PROGRESS**
- Set priority to **HIGH**
- Add label **"awaiting-audit"**
- Add a **comment** to the issue

# The adapter handles the translation:
# - Linear: status="Todo", priority=2
# - Jira: status="Open", priority="High"
# - GitHub: state="open", labels=["p1"]
```

### ❌ DON'T: Use System-Specific Terminology

```markdown
# Bad
- Create a **Linear project**
- Use **Linear's status values** ("Todo", "In Progress")
- Set **Linear priority** (1-4 scale)
- Call **mcp__linear__create_issue**

# This breaks when using Jira or GitHub adapters!
```

### Status Values in Prompts

```markdown
# Use generic enum names
- TODO (not "Todo" or "Open" or "To Do")
- IN_PROGRESS (not "In Progress" or "in-progress")
- DONE (not "Done" or "Closed" or "completed")
- CANCELED (not "Canceled" or "Won't Do" or "wontfix")
```

### Priority Values in Prompts

```markdown
# Use generic enum names
- URGENT (not 1 or "Highest" or "p0")
- HIGH (not 2 or "High" or "p1")
- MEDIUM (not 3 or "Medium" or "p2")
- LOW (not 4 or "Low" or "p3")
```

## Rate Limiting

### Dual Rate Limit Architecture

The system handles two types of rate limits independently:

#### 1. **Task Management API Rate Limits**

- **Linear**: 1500 requests/hour (rolling window)
- **Jira**: Varies by plan (typically 1000-5000/hour)
- **GitHub**: 5000/hour (authenticated)

**Handler**: `LinearRateLimitHandler` (or adapter-specific)

**Strategy**:
- Always auto-wait (max 1 hour for Linear)
- Show countdown timer
- Never exit (wait is bounded)

#### 2. **Claude API Rate Limits**

- **Hourly limit**: e.g., 50 requests/hour
- **Weekly limit**: e.g., 1000 requests/week
- **Monthly limit**: e.g., 10000 requests/month

**Handler**: `ClaudeRateLimitHandler`

**Strategy**:
- **≤30 minutes**: Auto-wait with countdown
- **30min - 2 hours**: Wait but allow Ctrl+C to exit
- **>2 hours**: Auto-exit with resume instructions

### Unified Rate Limit Handler

```python
class UnifiedRateLimitHandler:
    """Dispatches to appropriate handler based on error source."""
    
    def __init__(self):
        self.claude_handler = ClaudeRateLimitHandler()
        self.linear_handler = LinearRateLimitHandler()  # or adapter-specific
    
    async def handle_rate_limit(self, content: str, tool_name: str = ""):
        # Detect source of rate limit
        if self.linear_handler.is_linear_rate_limit(content, tool_name):
            return await self.linear_handler.handle_rate_limit(content)
        elif self.claude_handler.is_claude_rate_limit(content):
            return await self.claude_handler.handle_rate_limit(content)
        else:
            # Fallback to Claude handler
            return await self.claude_handler.handle_rate_limit(content)
```

## Adding a New Adapter

### Step 1: Create Adapter File

```python
# task_management/jira_adapter.py
from .interface import TaskManagementAdapter, Issue, IssueStatus, IssuePriority

class JiraAdapter(TaskManagementAdapter):
    # 1. Define mapping tables
    STATUS_TO_JIRA = {
        IssueStatus.TODO: "To Do",
        IssueStatus.IN_PROGRESS: "In Progress",
        IssueStatus.DONE: "Done",
        IssueStatus.CANCELED: "Won't Do",
    }
    
    PRIORITY_TO_JIRA = {
        IssuePriority.URGENT: "Highest",
        IssuePriority.HIGH: "High",
        IssuePriority.MEDIUM: "Medium",
        IssuePriority.LOW: "Low",
    }
    
    # 2. Implement all abstract methods
    def create_issue(self, title, status=IssueStatus.TODO, ...):
        jira_status = self.STATUS_TO_JIRA[status]
        jira_priority = self.PRIORITY_TO_JIRA[priority]
        
        # Call Jira MCP tool
        result = self._call_mcp_tool(
            "mcp__jira__create_issue",
            summary=title,  # Jira calls it "summary"
            status=jira_status,
            priority=jira_priority,
        )
        
        # Parse response
        return self._parse_issue_data(result)
    
    # ... implement other methods
```

### Step 2: Register in Factory

```python
# task_management/factory.py
from .jira_adapter import JiraAdapter

def create_adapter(adapter_type="linear", api_key=None, **kwargs):
    if adapter_type == "linear":
        return LinearAdapter(api_key=api_key)
    elif adapter_type == "jira":
        return JiraAdapter(api_key=api_key, url=kwargs.get("url"))
    # ...
```

### Step 3: Update Documentation

- Add mapping to `TERMINOLOGY_MAPPING.md`
- Add example to this file
- Update `README.md` with new adapter

### Step 4: Test

```python
# test_jira_adapter.py
def test_jira_adapter():
    adapter = create_adapter("jira", api_key="...", url="...")
    
    # Test with generic interface
    issue = adapter.create_issue(
        title="Test issue",
        status=IssueStatus.TODO,
        priority=IssuePriority.HIGH,
    )
    
    assert issue.status == IssueStatus.TODO
    assert issue.priority == IssuePriority.HIGH
```

**That's it!** No changes needed to prompts or agent code.

## Benefits

### 1. **Flexibility**

Switch between task management systems without changing prompts:

```bash
# Use Linear
export TASK_ADAPTER_TYPE=linear
python autocode.py

# Use Jira
export TASK_ADAPTER_TYPE=jira
python autocode.py
```

### 2. **Maintainability**

- Prompts are system-agnostic (never need updating)
- Business logic in one place (interface)
- System-specific code isolated (adapters)

### 3. **Testability**

- Mock the interface for testing
- Test adapters independently
- No need to change prompts for testing

### 4. **Extensibility**

Adding Jira support:
- ✅ Create `jira_adapter.py` (1 file)
- ✅ Register in `factory.py` (2 lines)
- ❌ No prompt changes needed
- ❌ No agent code changes needed

### 5. **Clarity**

- Prompts use domain language (TODO, HIGH, etc.)
- No confusion about Linear vs Jira vs GitHub terminology
- Self-documenting code

## Migration Checklist

- [x] Create task_management module
- [x] Implement generic interface
- [x] Implement Linear adapter
- [x] Create factory pattern
- [ ] Update prompts to use generic terminology (minimal Linear refs remain)
- [ ] Update agent.py to use adapter
- [ ] Update progress.py to use adapter
- [ ] Update autocode.py with adapter config
- [ ] Test with Linear adapter
- [ ] Document architecture (this file)
- [ ] Update README

## Future Adapters

### Priority Order

1. **Linear** ✅ (Implemented)
2. **Jira** ⏳ (High demand, enterprise use)
3. **GitHub Issues** ⏳ (Open source projects)
4. **Asana** ⏳ (Project management focus)
5. **Trello** ⏳ (Kanban boards)
6. **Monday.com** ⏳ (Work OS)

### Adapter Complexity

| Adapter | Complexity | Notes |
|---------|------------|-------|
| Linear | Low | Clean API, 1:1 mapping |
| GitHub | Low | Simple API, some label hacks for priority/status |
| Jira | Medium | Complex API, workflow customization |
| Asana | Medium | Different data model (tasks in sections) |
| Trello | Medium | Board/list/card model vs project/issue |
| Monday | High | Very different data model, highly customizable |

## Summary

The task management adapter architecture provides:

- ✅ **Unified interface** for all task management systems
- ✅ **Generic terminology** in prompts (never mention "Linear")
- ✅ **Easy extensibility** for new adapters
- ✅ **Zero coupling** between prompts and backends
- ✅ **Flexible configuration** (env vars, config file, CLI)
- ✅ **Backward compatibility** with existing Linear setup

**Result**: Add Jira/GitHub/Asana support without touching prompts or agent code.

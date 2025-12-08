# Task Management Adapter System

A unified, adapter-based system for integrating with multiple task management platforms (Linear, GitHub Issues, BEADS, etc.) through a common interface.

## Features

- **Adapter Pattern**: Single interface, multiple backends
- **CLI-First**: GitHub and BEADS adapters use CLI tools (no API keys needed for these)
- **Generic Terminology**: Platform-agnostic naming (Issue, Project, Status, Priority)
- **Type-Safe**: Full type hints and dataclasses
- **Extensible**: Easy to add new adapters

## Supported Adapters

| Adapter | Status | Backend | Authentication |
|---------|--------|---------|----------------|
| **Linear** | ✅ Production | MCP/API | API Key (env: `LINEAR_API_KEY`) |
| **GitHub** | ✅ Production | CLI (`gh`) | `gh auth login` |
| **BEADS** | ⚠️ Template | CLI (`bd`) | `bd auth login` |
| Jira | 📋 Planned | API | API Token |
| Asana | 📋 Planned | API | API Key |

## Quick Start

### Installation

```python
# The task_management module is part of the coding-agent-harness
# No separate installation needed
from task_management import create_adapter, IssueStatus, IssuePriority
```

### Basic Usage

```python
from task_management import create_adapter, IssueStatus, IssuePriority

# Create adapter (reads from environment)
adapter = create_adapter("linear")  # or "github" or "beads"

# Create an issue
issue = adapter.create_issue(
    title="Implement user authentication",
    description="Add OAuth2 support",
    status=IssueStatus.TODO,
    priority=IssuePriority.HIGH,
    labels=["enhancement"]
)

# Update issue
adapter.update_issue(
    issue.id,
    status=IssueStatus.IN_PROGRESS
)

# Add comment
adapter.create_comment(
    issue.id,
    "Started implementation. OAuth2 library selected."
)

# Complete issue
adapter.update_issue(
    issue.id,
    status=IssueStatus.DONE
)
```

## Configuration

### Environment Variables

#### Linear Adapter
```bash
export TASK_ADAPTER_TYPE="linear"
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

#### GitHub Adapter
```bash
export TASK_ADAPTER_TYPE="github"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
```

#### BEADS Adapter
```bash
export TASK_ADAPTER_TYPE="beads"
export BEADS_WORKSPACE="my-workspace"  # Optional
```

### Programmatic Configuration

```python
from task_management import create_adapter

# Linear (API-based)
linear_adapter = create_adapter(
    adapter_type="linear",
    api_key="lin_api_xxxxxxxxxxxxx"
)

# GitHub (CLI-based)
github_adapter = create_adapter(
    adapter_type="github",
    owner="myorg",
    repo="myrepo"
)

# BEADS (CLI-based)
beads_adapter = create_adapter(
    adapter_type="beads",
    workspace="my-workspace"
)
```

## Architecture

### Interface-First Design

All adapters implement the `TaskManagementAdapter` interface:

```python
class TaskManagementAdapter(ABC):
    # Team operations
    def list_teams() -> List[Team]
    
    # Project operations
    def create_project(...) -> Project
    def get_project(project_id) -> Project
    def list_projects(...) -> List[Project]
    
    # Issue operations
    def create_issue(...) -> Issue
    def get_issue(issue_id) -> Issue
    def update_issue(...) -> Issue
    def list_issues(...) -> List[Issue]
    
    # Label operations
    def create_label(...) -> Label
    def list_labels() -> List[Label]
    
    # Comment operations
    def create_comment(...) -> Comment
    def list_comments(issue_id) -> List[Comment]
    
    # Health check
    def test_connection() -> bool
```

### Generic Data Models

```python
@dataclass
class Issue:
    id: str
    title: str
    description: Optional[str]
    status: IssueStatus  # TODO, IN_PROGRESS, DONE, CANCELED
    priority: IssuePriority  # URGENT, HIGH, MEDIUM, LOW
    project_id: Optional[str]
    labels: List[Label]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    metadata: Dict[str, Any]  # Adapter-specific data
```

### Terminology Mapping

Generic terminology is mapped to platform-specific terms:

| Generic | Linear | GitHub | BEADS |
|---------|--------|--------|-------|
| Issue | Issue | Issue | Issue/Task |
| Project | Project | Project (v2) | Project |
| Team | Team | Repository | Team/Workspace |
| Status: TODO | Todo | open + label | TODO |
| Status: IN_PROGRESS | In Progress | open + label | IN_PROGRESS |
| Status: DONE | Done | closed + label | DONE |
| Priority: URGENT | 1 | priority:urgent | URGENT |
| Priority: HIGH | 2 | priority:high | HIGH |

See [TERMINOLOGY_MAPPING.md](TERMINOLOGY_MAPPING.md) for complete reference.

## Adapter-Specific Guides

- **[Linear Adapter](linear_adapter.py)** - MCP/API-based, production-ready
- **[GitHub Adapter](GITHUB_ADAPTER.md)** - CLI-based (`gh`), uses labels for status/priority
- **[BEADS Adapter](BEADS_ADAPTER.md)** - CLI-based (`bd`), template implementation

## Advanced Usage

### Working with Labels

```python
# Create labels
bug_label = adapter.create_label(
    name="bug",
    color="#d73a4a",
    description="Something isn't working"
)

feature_label = adapter.create_label(
    name="feature",
    color="#0366d6"
)

# Create issue with labels
issue = adapter.create_issue(
    title="Fix login redirect",
    labels=[bug_label.id, "priority:high"]
)

# Add/remove labels
adapter.update_issue(
    issue.id,
    add_labels=["security"],
    remove_labels=["bug"]
)
```

### Filtering Issues

```python
# Get all high-priority issues
high_priority = adapter.list_issues(
    priority=IssuePriority.HIGH,
    limit=50
)

# Get in-progress issues in a project
active_issues = adapter.list_issues(
    project_id="PROJ-123",
    status=IssueStatus.IN_PROGRESS
)

# Get issues with specific labels
bugs = adapter.list_issues(
    labels=["bug", "critical"]
)
```

### Project Management

```python
# Create project
project = adapter.create_project(
    name="Q1 2025 Roadmap",
    team_ids=["TEAM-1"],
    description="Feature roadmap for Q1"
)

# Create issues in project
adapter.create_issue(
    title="Feature 1",
    project_id=project.id,
    priority=IssuePriority.HIGH
)
```

## Creating New Adapters

To add support for a new platform:

1. **Create adapter class** implementing `TaskManagementAdapter`:
   ```python
   class JiraAdapter(TaskManagementAdapter):
       def create_issue(self, ...):
           # Jira-specific implementation
           pass
   ```

2. **Map terminology** to platform-specific terms:
   ```python
   STATUS_TO_JIRA = {
       IssueStatus.TODO: "To Do",
       IssueStatus.IN_PROGRESS: "In Progress",
       # ...
   }
   ```

3. **Register in factory**:
   ```python
   # In factory.py
   elif adapter_type == "jira":
       return JiraAdapter(api_key=api_key, url=kwargs.get("url"))
   ```

4. **Document** CLI commands, API calls, and configuration

See existing adapters for implementation patterns.

## Testing

```python
# Test connection
assert adapter.test_connection(), "Failed to connect"

# Create and verify issue
issue = adapter.create_issue(title="Test Issue")
fetched = adapter.get_issue(issue.id)
assert fetched.title == "Test Issue"

# Test status transitions
adapter.update_issue(issue.id, status=IssueStatus.IN_PROGRESS)
updated = adapter.get_issue(issue.id)
assert updated.status == IssueStatus.IN_PROGRESS
```

## Prompt Integration

The adapter system integrates with agent prompts through generic terminology:

```markdown
<!-- In agent prompts -->
1. Create issues using IssueStatus.TODO, IssueStatus.IN_PROGRESS, IssueStatus.DONE
2. Set priority using IssuePriority.URGENT, IssuePriority.HIGH, etc.
3. Never use platform-specific terms (e.g., "Linear", "GitHub")
4. Use generic labels for categorization
```

See [PROMPT_GUIDELINES.md](PROMPT_GUIDELINES.md) for writing adapter-agnostic prompts.

## Migration from Linear-Only Code

If you have existing Linear-specific code:

1. **Replace imports**:
   ```python
   # Before
   from linear import Client
   
   # After
   from task_management import create_adapter
   adapter = create_adapter("linear")
   ```

2. **Update terminology**:
   - "Todo" → `IssueStatus.TODO`
   - Priority 1 → `IssuePriority.URGENT`
   - "mcp__linear__create_issue" → `adapter.create_issue(...)`

3. **See [MIGRATION_PLAN.md](MIGRATION_PLAN.md)** for complete checklist

## Troubleshooting

### Linear: "LINEAR_API_KEY not found"
```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"
```

### GitHub: "gh: command not found"
```bash
brew install gh  # macOS
gh auth login
```

### BEADS: CLI structure mismatch
BEADS adapter is a template. Adjust CLI commands in `beads_adapter.py` based on actual BEADS CLI documentation.

### Connection tests failing
```python
if not adapter.test_connection():
    print("Check authentication and network connectivity")
```

## Contributing

To contribute a new adapter:

1. Fork and create feature branch
2. Implement `TaskManagementAdapter` interface
3. Add comprehensive documentation
4. Include example usage and configuration
5. Write tests
6. Submit PR

## License

Part of the coding-agent-harness project. See [LICENSE](../LICENSE) for details.

## References

- [Interface Definition](interface.py)
- [Terminology Mapping](TERMINOLOGY_MAPPING.md)
- [Prompt Guidelines](PROMPT_GUIDELINES.md)
- [Linear Adapter](linear_adapter.py)
- [GitHub Adapter Guide](GITHUB_ADAPTER.md)
- [BEADS Adapter Guide](BEADS_ADAPTER.md)
- [Migration Plan](MIGRATION_PLAN.md)

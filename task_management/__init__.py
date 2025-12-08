"""
Task Management Abstraction Layer
==================================

Provides a generic interface for project and task management systems.
Supports multiple backends (Linear, Jira, GitHub Issues, etc.) through adapters.

Usage:
    from task_management import create_adapter, IssueStatus, IssuePriority
    
    # Create adapter (reads LINEAR_API_KEY from environment)
    adapter = create_adapter("linear")
    
    # List teams
    teams = adapter.list_teams()
    
    # Create project
    project = adapter.create_project(
        name="My Project",
        team_ids=[teams[0].id],
        description="Project description"
    )
    
    # Create label
    label = adapter.create_label(
        name="feature",
        color="#0000FF",
        description="New feature"
    )
    
    # Create issue
    issue = adapter.create_issue(
        title="Implement user authentication",
        description="Add login/signup functionality",
        project_id=project.id,
        priority=IssuePriority.HIGH,
        status=IssueStatus.TODO,
        labels=[label.id]
    )
    
    # Update issue
    adapter.update_issue(
        issue.id,
        status=IssueStatus.IN_PROGRESS
    )
    
    # List issues
    issues = adapter.list_issues(
        project_id=project.id,
        status=IssueStatus.TODO
    )
    
    # Add comment
    adapter.create_comment(
        issue.id,
        "Started working on this"
    )
"""

from .interface import (
    TaskManagementAdapter,
    Project,
    Issue,
    IssueStatus,
    IssuePriority,
    Label,
    Comment,
    Team,
)
from .linear_adapter import LinearAdapter
from .factory import create_adapter, get_adapter_from_env

__all__ = [
    # Core interface
    "TaskManagementAdapter",
    
    # Data models
    "Project",
    "Issue",
    "IssueStatus",
    "IssuePriority",
    "Label",
    "Comment",
    "Team",
    
    # Adapters
    "LinearAdapter",
    
    # Factory
    "create_adapter",
    "get_adapter_from_env",
]

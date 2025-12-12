"""
Task Management Interface
=========================

Generic interface for project and task management systems.
All adapters (Linear, Jira, GitHub, etc.) must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class IssueStatus(Enum):
    """Generic issue status values."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


class IssuePriority(Enum):
    """Generic issue priority levels."""
    URGENT = 1  # P1 - Critical, blocking
    HIGH = 2    # P2 - Important, high value
    MEDIUM = 3  # P3 - Normal priority
    LOW = 4     # P4 - Nice to have


@dataclass
class Team:
    """Represents a team in the task management system."""
    id: str
    name: str
    description: Optional[str] = None


@dataclass
class Project:
    """Represents a project containing issues."""
    id: str
    name: str
    description: Optional[str] = None
    team_ids: List[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.team_ids is None:
            self.team_ids = []


@dataclass
class Label:
    """Represents a label/tag for categorizing issues."""
    id: str
    name: str
    color: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Comment:
    """Represents a comment on an issue."""
    id: str
    issue_id: str
    body: str
    created_at: datetime
    author: Optional[str] = None


@dataclass
class Issue:
    """Represents a task/issue in the system."""
    id: str
    title: str
    description: Optional[str] = None
    status: IssueStatus = IssueStatus.TODO
    priority: IssuePriority = IssuePriority.MEDIUM
    project_id: Optional[str] = None
    labels: List[Label] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Custom fields (adapter-specific data can go here)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.metadata is None:
            self.metadata = {}


class TaskManagementAdapter(ABC):
    """
    Abstract base class for task management adapters.
    
    All methods use generic terminology (project, issue, label, etc.)
    rather than system-specific terms (Linear's "project", Jira's "epic", etc.)
    """
    
    # Rate limit configuration (override in subclasses)
    RATE_LIMIT_DURATION_MINUTES = 0  # 0 = no rate limit
    RATE_LIMIT_MAX_REQUESTS = 0      # 0 = no rate limit
    
    # ==================== Team Operations ====================
    
    @abstractmethod
    def list_teams(self) -> List[Team]:
        """
        List all teams available to the current user.
        
        Returns:
            List of Team objects
        """
        pass
    
    # ==================== Project Operations ====================
    
    @abstractmethod
    def create_project(
        self,
        name: str,
        team_ids: List[str],
        description: Optional[str] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name
            team_ids: List of team IDs to associate with project
            description: Optional project description
            
        Returns:
            Created Project object
        """
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project object or None if not found
        """
        pass
    
    @abstractmethod
    def list_projects(self, team_id: Optional[str] = None) -> List[Project]:
        """
        List all projects, optionally filtered by team.
        
        Args:
            team_id: Optional team ID to filter by
            
        Returns:
            List of Project objects
        """
        pass
    
    # ==================== Label Operations ====================
    
    @abstractmethod
    def create_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Label:
        """
        Create a label for categorizing issues.
        
        Args:
            name: Label name
            color: Optional color (hex format like "#FF0000")
            description: Optional description
            
        Returns:
            Created Label object
        """
        pass
    
    @abstractmethod
    def list_labels(self) -> List[Label]:
        """
        List all labels.
        
        Returns:
            List of Label objects
        """
        pass
    
    # ==================== Issue Operations ====================
    
    @abstractmethod
    def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        status: IssueStatus = IssueStatus.TODO,
        priority: IssuePriority = IssuePriority.MEDIUM,
        labels: Optional[List[str]] = None,  # Label IDs
    ) -> Issue:
        """
        Create a new issue.
        
        Args:
            title: Issue title
            description: Optional description
            project_id: Optional project to add issue to
            status: Issue status (default: TODO)
            priority: Issue priority (default: MEDIUM)
            labels: Optional list of label IDs to apply
            
        Returns:
            Created Issue object
        """
        pass
    
    @abstractmethod
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get an issue by ID.
        
        Args:
            issue_id: Issue identifier
            
        Returns:
            Issue object or None if not found
        """
        pass
    
    @abstractmethod
    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        labels: Optional[List[str]] = None,  # Label IDs (replaces existing)
        add_labels: Optional[List[str]] = None,  # Label IDs to add
        remove_labels: Optional[List[str]] = None,  # Label IDs to remove
    ) -> Issue:
        """
        Update an existing issue.
        
        Args:
            issue_id: Issue identifier
            title: Optional new title
            description: Optional new description
            status: Optional new status
            priority: Optional new priority
            labels: Optional list of label IDs (replaces all labels)
            add_labels: Optional list of label IDs to add
            remove_labels: Optional list of label IDs to remove
            
        Returns:
            Updated Issue object
        """
        pass
    
    def update_issues_batch(
        self,
        updates: List[Dict[str, Any]],
    ) -> List[Issue]:
        """
        Update multiple issues in a single batch request (if supported).
        
        This method provides a more efficient way to update multiple issues
        by combining them into a single API request, reducing the number of
        API calls and avoiding rate limits.
        
        Args:
            updates: List of update dictionaries, each containing:
                - issue_id (str): Required - Issue identifier
                - title (str): Optional - New title
                - description (str): Optional - New description
                - status (IssueStatus): Optional - New status
                - priority (IssuePriority): Optional - New priority
                - labels (List[str]): Optional - Label IDs (replaces all)
                - add_labels (List[str]): Optional - Label IDs to add
                - remove_labels (List[str]): Optional - Label IDs to remove
            
        Returns:
            List of updated Issue objects
            
        Note:
            Default implementation falls back to individual updates.
            Adapters that support batch operations (e.g., GraphQL-based)
            should override this for better performance.
        """
        results = []
        for update in updates:
            issue_id = update.pop("issue_id")
            updated_issue = self.update_issue(issue_id, **update)
            results.append(updated_issue)
        return results
    
    @abstractmethod
    def list_issues(
        self,
        project_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        labels: Optional[List[str]] = None,  # Label IDs
        limit: int = 50,
    ) -> List[Issue]:
        """
        List issues with optional filtering.
        
        Args:
            project_id: Optional project ID to filter by
            status: Optional status to filter by
            labels: Optional list of label IDs (issues must have ALL labels)
            limit: Maximum number of issues to return
            
        Returns:
            List of Issue objects
        """
        pass
    
    # ==================== Comment Operations ====================
    
    @abstractmethod
    def create_comment(
        self,
        issue_id: str,
        body: str,
    ) -> Comment:
        """
        Add a comment to an issue.
        
        Args:
            issue_id: Issue identifier
            body: Comment text (may support Markdown)
            
        Returns:
            Created Comment object
        """
        pass
    
    @abstractmethod
    def list_comments(self, issue_id: str) -> List[Comment]:
        """
        List all comments on an issue.
        
        Args:
            issue_id: Issue identifier
            
        Returns:
            List of Comment objects
        """
        pass
    
    # ==================== Health Check ====================
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the adapter can connect to the backend.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    # ==================== Audit Tracking ====================
    
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
        
        Args:
            issue_id: Issue identifier
            comment: Optional comment to add when closing
            project_dir: Optional project directory (defaults to current dir)
            
        Returns:
            Updated Issue object
        """
        import json
        from pathlib import Path
        
        # 1. Update issue status to DONE
        issue = self.update_issue(issue_id, status=IssueStatus.DONE)
        
        # 2. Add "awaiting-audit" label if labels are supported
        try:
            existing_label_ids = [label.id for label in issue.labels]
            # Try to find awaiting-audit label
            all_labels = self.list_labels()
            audit_label = next((l for l in all_labels if l.name == "awaiting-audit"), None)
            if audit_label and audit_label.id not in existing_label_ids:
                self.update_issue(issue_id, add_labels=[audit_label.id])
        except Exception:
            # Labels not supported or error - continue anyway
            pass
        
        # 3. Update .task_project.json counter
        if project_dir is None:
            project_dir = "."
        project_file = Path(project_dir) / ".task_project.json"
        
        if project_file.exists():
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Increment audit counter
                data["features_awaiting_audit"] = data.get("features_awaiting_audit", 0) + 1
                
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not update audit counter: {e}")
        
        # 4. Add comment if provided
        if comment:
            try:
                self.create_comment(issue_id, comment)
            except Exception as e:
                print(f"Warning: Could not add comment: {e}")
        
        return issue

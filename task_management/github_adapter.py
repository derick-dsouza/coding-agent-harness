"""
GitHub Adapter Implementation
==============================

Maps GitHub Issues and Projects to the generic TaskManagementAdapter interface.
Uses the GitHub CLI (gh) for all operations.
"""

import json
import subprocess
from typing import Optional, List
from datetime import datetime

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


class GitHubAdapter(TaskManagementAdapter):
    """
    GitHub implementation of the TaskManagementAdapter.
    
    Uses GitHub CLI (gh) to interact with GitHub API.
    Maps GitHub's terminology to generic task management concepts:
    - GitHub Repository → Team
    - GitHub Project → Project
    - GitHub Issue → Issue
    - GitHub Label → Label
    - GitHub Issue States (open, closed) → IssueStatus
    - Custom labels for priority → IssuePriority
    """
    
    # Rate limit configuration for GitHub API
    RATE_LIMIT_DURATION_MINUTES = 60  # 1 hour
    RATE_LIMIT_MAX_REQUESTS = 5000    # 5000 requests per hour for authenticated users
    
    # Status mapping: Generic → GitHub
    STATUS_TO_GITHUB = {
        IssueStatus.TODO: "open",
        IssueStatus.IN_PROGRESS: "open",
        IssueStatus.DONE: "closed",
        IssueStatus.CANCELED: "closed",
    }
    
    # Status mapping: GitHub → Generic (with label hints)
    # GitHub only has open/closed, so we use labels to determine precise status
    GITHUB_TO_STATUS = {
        "open": IssueStatus.TODO,  # Default, refined by labels
        "closed": IssueStatus.DONE,
    }
    
    # Priority label mapping
    PRIORITY_LABELS = {
        IssuePriority.URGENT: "priority:urgent",
        IssuePriority.HIGH: "priority:high",
        IssuePriority.MEDIUM: "priority:medium",
        IssuePriority.LOW: "priority:low",
    }
    
    # Status label mapping (to refine open/closed)
    STATUS_LABELS = {
        IssueStatus.TODO: "status:todo",
        IssueStatus.IN_PROGRESS: "status:in-progress",
        IssueStatus.DONE: "status:done",
        IssueStatus.CANCELED: "status:canceled",
    }
    
    def __init__(self, owner: str, repo: str, project_dir: Optional[str] = None):
        """
        Initialize GitHub adapter.
        
        Args:
            owner: GitHub repository owner (user or organization)
            repo: GitHub repository name
            project_dir: Project directory for audit tracking
        """
        self.owner = owner
        self.repo = repo
        self.repo_full = f"{owner}/{repo}"
        self.project_dir = project_dir
        
        # Verify gh CLI is available
        try:
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("GitHub CLI (gh) not found or not authenticated")
    
    # ==================== Helper Methods ====================
    
    def _run_gh(self, args: List[str], capture_json=True) -> dict:
        """
        Run a gh CLI command and return parsed JSON output.
        
        Args:
            args: Command arguments (excluding 'gh')
            capture_json: If True, expect JSON output and parse it
            
        Returns:
            Parsed JSON dict or None
        """
        cmd = ["gh"] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        if capture_json and result.stdout:
            return json.loads(result.stdout)
        
        return {"output": result.stdout}
    
    def _parse_github_status(self, state: str, labels: List[str]) -> IssueStatus:
        """
        Convert GitHub issue state + labels to generic IssueStatus.
        
        GitHub only has open/closed, so we use status labels for precision.
        """
        # Check for status labels first
        for label in labels:
            if label == "status:in-progress":
                return IssueStatus.IN_PROGRESS
            elif label == "status:canceled":
                return IssueStatus.CANCELED
            elif label == "status:done":
                return IssueStatus.DONE
            elif label == "status:todo":
                return IssueStatus.TODO
        
        # Fall back to state mapping
        if state == "closed":
            return IssueStatus.DONE
        return IssueStatus.TODO
    
    def _parse_github_priority(self, labels: List[str]) -> IssuePriority:
        """Extract priority from GitHub labels."""
        for label in labels:
            if label == "priority:urgent":
                return IssuePriority.URGENT
            elif label == "priority:high":
                return IssuePriority.HIGH
            elif label == "priority:low":
                return IssuePriority.LOW
            elif label == "priority:medium":
                return IssuePriority.MEDIUM
        
        return IssuePriority.MEDIUM  # Default
    
    def _get_status_labels(self, status: IssueStatus) -> List[str]:
        """Get labels needed to represent a status."""
        return [self.STATUS_LABELS.get(status, "status:todo")]
    
    def _get_priority_labels(self, priority: IssuePriority) -> List[str]:
        """Get labels needed to represent a priority."""
        return [self.PRIORITY_LABELS.get(priority, "priority:medium")]
    
    # ==================== Team Operations ====================
    
    def list_teams(self) -> List[Team]:
        """
        List teams (GitHub repos in this context).
        
        For GitHub adapter, a "team" is the repository itself.
        """
        # Get repo info
        result = self._run_gh([
            "repo", "view", self.repo_full,
            "--json", "id,name,description"
        ])
        
        return [Team(
            id=result.get("id", self.repo_full),
            name=result.get("name", self.repo),
            description=result.get("description"),
        )]
    
    # ==================== Project Operations ====================
    
    def create_project(
        self,
        name: str,
        team_ids: List[str],
        description: Optional[str] = None,
    ) -> Project:
        """
        Create a GitHub Project (v2).
        
        Note: GitHub Projects are now organization/repo-level boards.
        """
        # gh project create --owner OWNER --name NAME [--body BODY]
        cmd = [
            "project", "create",
            "--owner", self.owner,
            "--title", name,
        ]
        
        if description:
            cmd.extend(["--body", description])
        
        result = self._run_gh(cmd, capture_json=False)
        
        # Extract project number from output
        # Output format: "https://github.com/orgs/OWNER/projects/NUMBER"
        project_url = result.get("output", "").strip()
        project_id = project_url.split("/")[-1] if project_url else name
        
        return Project(
            id=project_id,
            name=name,
            description=description,
            team_ids=team_ids,
            created_at=datetime.now(),
        )
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a GitHub Project by ID/number.
        """
        try:
            result = self._run_gh([
                "project", "view", project_id,
                "--owner", self.owner,
                "--json", "id,title,body,createdAt"
            ])
            
            return Project(
                id=result.get("id", project_id),
                name=result.get("title", ""),
                description=result.get("body"),
                team_ids=[self.repo_full],
                created_at=self._parse_datetime(result.get("createdAt")),
            )
        except subprocess.CalledProcessError:
            return None
    
    def list_projects(self, team_id: Optional[str] = None) -> List[Project]:
        """
        List GitHub Projects for the organization/user.
        """
        result = self._run_gh([
            "project", "list",
            "--owner", self.owner,
            "--json", "id,title,body,createdAt",
            "--limit", "100"
        ])
        
        projects = []
        for project_data in result:
            projects.append(Project(
                id=project_data.get("id", ""),
                name=project_data.get("title", ""),
                description=project_data.get("body"),
                team_ids=[self.repo_full],
                created_at=self._parse_datetime(project_data.get("createdAt")),
            ))
        
        return projects
    
    # ==================== Label Operations ====================
    
    def create_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Label:
        """
        Create a GitHub label.
        """
        cmd = [
            "label", "create", name,
            "--repo", self.repo_full,
        ]
        
        if color:
            # Remove # if present
            color_code = color.lstrip("#")
            cmd.extend(["--color", color_code])
        
        if description:
            cmd.extend(["--description", description])
        
        self._run_gh(cmd, capture_json=False)
        
        return Label(
            id=name,  # GitHub uses name as ID
            name=name,
            color=color,
            description=description,
        )
    
    def list_labels(self) -> List[Label]:
        """
        List all GitHub labels in the repository.
        """
        result = self._run_gh([
            "label", "list",
            "--repo", self.repo_full,
            "--json", "name,color,description",
            "--limit", "1000"
        ])
        
        labels = []
        for label_data in result:
            labels.append(Label(
                id=label_data.get("name", ""),
                name=label_data.get("name", ""),
                color=f"#{label_data.get('color', '')}",
                description=label_data.get("description"),
            ))
        
        return labels
    
    # ==================== Issue Operations ====================
    
    def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        status: IssueStatus = IssueStatus.TODO,
        priority: IssuePriority = IssuePriority.MEDIUM,
        labels: Optional[List[str]] = None,
    ) -> Issue:
        """
        Create a GitHub issue.
        """
        cmd = [
            "issue", "create",
            "--repo", self.repo_full,
            "--title", title,
        ]
        
        if description:
            cmd.extend(["--body", description])
        
        # Combine user labels with status/priority labels
        all_labels = labels or []
        all_labels.extend(self._get_status_labels(status))
        all_labels.extend(self._get_priority_labels(priority))
        
        if all_labels:
            # gh issue create accepts multiple --label flags or comma-separated
            cmd.extend(["--label", ",".join(all_labels)])
        
        result = self._run_gh(cmd, capture_json=False)
        
        # Extract issue number from output
        # Output format: "https://github.com/OWNER/REPO/issues/NUMBER"
        issue_url = result.get("output", "").strip()
        issue_number = issue_url.split("/")[-1] if issue_url else "1"
        
        # Fetch the created issue
        return self.get_issue(issue_number)
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get a GitHub issue by number.
        """
        try:
            result = self._run_gh([
                "issue", "view", issue_id,
                "--repo", self.repo_full,
                "--json", "number,title,body,state,labels,createdAt,updatedAt"
            ])
            
            return self._parse_issue_data(result)
        except subprocess.CalledProcessError:
            return None
    
    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        labels: Optional[List[str]] = None,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> Issue:
        """
        Update a GitHub issue.
        """
        cmd = [
            "issue", "edit", issue_id,
            "--repo", self.repo_full,
        ]
        
        if title is not None:
            cmd.extend(["--title", title])
        
        if description is not None:
            cmd.extend(["--body", description])
        
        # Handle status change
        if status is not None:
            github_state = self.STATUS_TO_GITHUB[status]
            if github_state == "closed":
                # Close the issue
                subprocess.run(
                    ["gh", "issue", "close", issue_id, "--repo", self.repo_full],
                    check=True,
                )
            else:
                # Reopen if needed
                subprocess.run(
                    ["gh", "issue", "reopen", issue_id, "--repo", self.repo_full],
                    check=True,
                )
            
            # Add status label
            add_labels = add_labels or []
            add_labels.extend(self._get_status_labels(status))
        
        if priority is not None:
            add_labels = add_labels or []
            add_labels.extend(self._get_priority_labels(priority))
        
        # Handle label operations
        if labels is not None:
            # gh issue edit doesn't have --label, need to fetch current and replace
            # Get current issue to determine what to remove
            current_issue = self.get_issue(issue_id)
            current_labels = [label.name for label in current_issue.labels]
            
            # Remove all current labels, then add new ones
            if current_labels:
                cmd.extend(["--remove-label", ",".join(current_labels)])
            if labels:
                cmd.extend(["--add-label", ",".join(labels)])
        else:
            # Add/remove specific labels
            if add_labels:
                cmd.extend(["--add-label", ",".join(add_labels)])
            
            if remove_labels:
                cmd.extend(["--remove-label", ",".join(remove_labels)])
        
        self._run_gh(cmd, capture_json=False)
        
        # Fetch updated issue
        return self.get_issue(issue_id)
    
    def list_issues(
        self,
        project_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        labels: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Issue]:
        """
        List GitHub issues with optional filtering.
        """
        cmd = [
            "issue", "list",
            "--repo", self.repo_full,
            "--json", "number,title,body,state,labels,createdAt,updatedAt",
            "--limit", str(limit),
        ]
        
        # GitHub state filter (open/closed/all)
        if status in [IssueStatus.TODO, IssueStatus.IN_PROGRESS]:
            cmd.extend(["--state", "open"])
        elif status in [IssueStatus.DONE, IssueStatus.CANCELED]:
            cmd.extend(["--state", "closed"])
        else:
            cmd.extend(["--state", "all"])
        
        # Label filter
        if labels:
            label_str = ",".join(labels)
            cmd.extend(["--label", label_str])
        
        result = self._run_gh(cmd)
        
        issues = []
        for issue_data in result:
            parsed_issue = self._parse_issue_data(issue_data)
            
            # Additional status filtering (refine beyond open/closed)
            if status and parsed_issue.status != status:
                continue
            
            issues.append(parsed_issue)
        
        return issues
    
    # ==================== Comment Operations ====================
    
    def create_comment(self, issue_id: str, body: str) -> Comment:
        """
        Add a comment to a GitHub issue.
        """
        self._run_gh([
            "issue", "comment", issue_id,
            "--repo", self.repo_full,
            "--body", body
        ], capture_json=False)
        
        # GitHub CLI doesn't return comment ID easily, so we fetch latest
        comments = self.list_comments(issue_id)
        return comments[-1] if comments else Comment(
            id="unknown",
            issue_id=issue_id,
            body=body,
            created_at=datetime.now(),
        )
    
    def list_comments(self, issue_id: str) -> List[Comment]:
        """
        List all comments on a GitHub issue.
        """
        result = self._run_gh([
            "issue", "view", issue_id,
            "--repo", self.repo_full,
            "--json", "comments"
        ])
        
        comments = []
        for comment_data in result.get("comments", []):
            comments.append(Comment(
                id=comment_data.get("id", ""),
                issue_id=issue_id,
                body=comment_data.get("body", ""),
                created_at=self._parse_datetime(comment_data.get("createdAt")),
                author=comment_data.get("author", {}).get("login"),
            ))
        
        return comments
    
    # ==================== Health Check ====================
    
    def test_connection(self) -> bool:
        """
        Test connection to GitHub.
        """
        try:
            self._run_gh(["auth", "status"], capture_json=False)
            return True
        except subprocess.CalledProcessError:
            return False
    
    # ==================== Audit Tracking ====================
    
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
        # Use stored project_dir if not specified
        if project_dir is None:
            project_dir = self.project_dir or "."
        
        return super().close_issue_with_audit_tracking(
            issue_id=issue_id,
            comment=comment,
            project_dir=project_dir,
        )
    
    # ==================== Helper Methods ====================
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        except Exception:
            return None
    
    def _parse_issue_data(self, issue_data: dict) -> Issue:
        """Parse GitHub issue data into generic Issue object."""
        # Parse labels
        label_names = [label["name"] for label in issue_data.get("labels", [])]
        
        labels = []
        for label_data in issue_data.get("labels", []):
            labels.append(Label(
                id=label_data.get("name", ""),
                name=label_data.get("name", ""),
                color=f"#{label_data.get('color', '')}",
                description=label_data.get("description"),
            ))
        
        # Determine status and priority from labels
        status = self._parse_github_status(issue_data.get("state", "open"), label_names)
        priority = self._parse_github_priority(label_names)
        
        return Issue(
            id=str(issue_data.get("number", "")),
            title=issue_data.get("title", ""),
            description=issue_data.get("body"),
            status=status,
            priority=priority,
            project_id=None,  # GitHub doesn't store this in issue data
            labels=labels,
            created_at=self._parse_datetime(issue_data.get("createdAt")),
            updated_at=self._parse_datetime(issue_data.get("updatedAt")),
            metadata={
                "github_number": issue_data.get("number"),
                "github_url": f"https://github.com/{self.repo_full}/issues/{issue_data.get('number')}",
            },
        )

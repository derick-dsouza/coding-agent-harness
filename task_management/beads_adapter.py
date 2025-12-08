"""
BEADS Adapter Implementation
=============================

Maps BEADS task management to the generic TaskManagementAdapter interface.
Uses the BEADS CLI (bd) for all operations.

Note: This is a template implementation. Actual BEADS CLI commands and
JSON structure need to be updated based on real BEADS CLI documentation.
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


class BeadsAdapter(TaskManagementAdapter):
    """
    BEADS implementation of the TaskManagementAdapter.
    
    Uses BEADS CLI (bd) to interact with BEADS API.
    Maps BEADS terminology to generic task management concepts.
    
    Note: Command structure is based on typical task management CLIs.
    Adjust based on actual BEADS CLI documentation.
    """
    
    # Status mapping: Generic → BEADS
    # Adjust these based on actual BEADS status values
    STATUS_TO_BEADS = {
        IssueStatus.TODO: "TODO",
        IssueStatus.IN_PROGRESS: "IN_PROGRESS",
        IssueStatus.DONE: "DONE",
        IssueStatus.CANCELED: "CANCELED",
    }
    
    # Status mapping: BEADS → Generic
    BEADS_TO_STATUS = {
        "TODO": IssueStatus.TODO,
        "BACKLOG": IssueStatus.TODO,
        "IN_PROGRESS": IssueStatus.IN_PROGRESS,
        "DOING": IssueStatus.IN_PROGRESS,
        "DONE": IssueStatus.DONE,
        "COMPLETED": IssueStatus.DONE,
        "CANCELED": IssueStatus.CANCELED,
        "CANCELLED": IssueStatus.CANCELED,
    }
    
    # Priority mapping: Generic → BEADS
    PRIORITY_TO_BEADS = {
        IssuePriority.URGENT: "URGENT",
        IssuePriority.HIGH: "HIGH",
        IssuePriority.MEDIUM: "MEDIUM",
        IssuePriority.LOW: "LOW",
    }
    
    # Priority mapping: BEADS → Generic
    BEADS_TO_PRIORITY = {
        "URGENT": IssuePriority.URGENT,
        "CRITICAL": IssuePriority.URGENT,
        "HIGH": IssuePriority.HIGH,
        "MEDIUM": IssuePriority.MEDIUM,
        "NORMAL": IssuePriority.MEDIUM,
        "LOW": IssuePriority.LOW,
    }
    
    def __init__(self, workspace: Optional[str] = None):
        """
        Initialize BEADS adapter.
        
        Args:
            workspace: BEADS workspace ID or name (if applicable)
        """
        self.workspace = workspace
        
        # Verify bd CLI is available
        try:
            subprocess.run(
                ["bd", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("BEADS CLI (bd) not found or not authenticated")
    
    # ==================== Helper Methods ====================
    
    def _run_bd(self, args: List[str], input_data: Optional[dict] = None) -> dict:
        """
        Run a bd CLI command and return parsed JSON output.
        
        Args:
            args: Command arguments (excluding 'bd')
            input_data: Optional JSON data to pass as stdin
            
        Returns:
            Parsed JSON dict
        """
        cmd = ["bd"] + args
        
        # Add workspace context if configured
        if self.workspace:
            cmd.extend(["--workspace", self.workspace])
        
        # Assume bd outputs JSON by default or with --json flag
        if "--json" not in args:
            cmd.append("--json")
        
        stdin_input = None
        if input_data:
            stdin_input = json.dumps(input_data)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=stdin_input,
            check=True,
        )
        
        if result.stdout:
            return json.loads(result.stdout)
        
        return {}
    
    def _parse_beads_status(self, beads_status: str) -> IssueStatus:
        """Convert BEADS status to generic IssueStatus."""
        return self.BEADS_TO_STATUS.get(beads_status.upper(), IssueStatus.TODO)
    
    def _parse_beads_priority(self, beads_priority: str) -> IssuePriority:
        """Convert BEADS priority to generic IssuePriority."""
        return self.BEADS_TO_PRIORITY.get(beads_priority.upper(), IssuePriority.MEDIUM)
    
    # ==================== Team Operations ====================
    
    def list_teams(self) -> List[Team]:
        """
        List all BEADS teams/workspaces.
        
        Assumes: bd team list --json
        """
        result = self._run_bd(["team", "list"])
        
        teams = []
        for team_data in result.get("teams", []):
            teams.append(Team(
                id=team_data.get("id", ""),
                name=team_data.get("name", ""),
                description=team_data.get("description"),
            ))
        return teams
    
    # ==================== Project Operations ====================
    
    def create_project(
        self,
        name: str,
        team_ids: List[str],
        description: Optional[str] = None,
    ) -> Project:
        """
        Create a BEADS project.
        
        Assumes: bd project create --name NAME --teams TEAMS [--description DESC]
        """
        cmd = ["project", "create", "--name", name]
        
        if team_ids:
            cmd.extend(["--teams", ",".join(team_ids)])
        
        if description:
            cmd.extend(["--description", description])
        
        result = self._run_bd(cmd)
        
        project_data = result.get("project", {})
        return Project(
            id=project_data.get("id", ""),
            name=project_data.get("name", name),
            description=project_data.get("description", description),
            team_ids=team_ids,
            created_at=self._parse_datetime(project_data.get("createdAt")),
        )
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a BEADS project by ID.
        
        Assumes: bd project get PROJECT_ID --json
        """
        try:
            result = self._run_bd(["project", "get", project_id])
            
            project_data = result.get("project", {})
            return Project(
                id=project_data.get("id", project_id),
                name=project_data.get("name", ""),
                description=project_data.get("description"),
                team_ids=project_data.get("teamIds", []),
                created_at=self._parse_datetime(project_data.get("createdAt")),
            )
        except subprocess.CalledProcessError:
            return None
    
    def list_projects(self, team_id: Optional[str] = None) -> List[Project]:
        """
        List BEADS projects.
        
        Assumes: bd project list [--team TEAM_ID] --json
        """
        cmd = ["project", "list"]
        
        if team_id:
            cmd.extend(["--team", team_id])
        
        result = self._run_bd(cmd)
        
        projects = []
        for project_data in result.get("projects", []):
            projects.append(Project(
                id=project_data.get("id", ""),
                name=project_data.get("name", ""),
                description=project_data.get("description"),
                team_ids=project_data.get("teamIds", []),
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
        Create a BEADS label.
        
        Assumes: bd label create --name NAME [--color COLOR] [--description DESC]
        """
        cmd = ["label", "create", "--name", name]
        
        if color:
            cmd.extend(["--color", color])
        
        if description:
            cmd.extend(["--description", description])
        
        result = self._run_bd(cmd)
        
        label_data = result.get("label", {})
        return Label(
            id=label_data.get("id", ""),
            name=label_data.get("name", name),
            color=label_data.get("color", color),
            description=label_data.get("description", description),
        )
    
    def list_labels(self) -> List[Label]:
        """
        List all BEADS labels.
        
        Assumes: bd label list --json
        """
        result = self._run_bd(["label", "list"])
        
        labels = []
        for label_data in result.get("labels", []):
            labels.append(Label(
                id=label_data.get("id", ""),
                name=label_data.get("name", ""),
                color=label_data.get("color"),
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
        Create a BEADS issue.
        
        Assumes: bd issue create --title TITLE [--description DESC] [--project PROJECT_ID]
                 [--status STATUS] [--priority PRIORITY] [--labels LABEL_IDS]
        """
        cmd = ["issue", "create", "--title", title]
        
        if description:
            cmd.extend(["--description", description])
        
        if project_id:
            cmd.extend(["--project", project_id])
        
        cmd.extend(["--status", self.STATUS_TO_BEADS[status]])
        cmd.extend(["--priority", self.PRIORITY_TO_BEADS[priority]])
        
        if labels:
            cmd.extend(["--labels", ",".join(labels)])
        
        result = self._run_bd(cmd)
        
        issue_data = result.get("issue", {})
        return self._parse_issue_data(issue_data)
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get a BEADS issue by ID.
        
        Assumes: bd issue get ISSUE_ID --json
        """
        try:
            result = self._run_bd(["issue", "get", issue_id])
            
            issue_data = result.get("issue", {})
            return self._parse_issue_data(issue_data)
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
        Update a BEADS issue.
        
        Assumes: bd issue update ISSUE_ID [--title TITLE] [--description DESC]
                 [--status STATUS] [--priority PRIORITY] [--labels LABELS]
                 [--add-labels LABELS] [--remove-labels LABELS]
        """
        cmd = ["issue", "update", issue_id]
        
        if title is not None:
            cmd.extend(["--title", title])
        
        if description is not None:
            cmd.extend(["--description", description])
        
        if status is not None:
            cmd.extend(["--status", self.STATUS_TO_BEADS[status]])
        
        if priority is not None:
            cmd.extend(["--priority", self.PRIORITY_TO_BEADS[priority]])
        
        if labels is not None:
            cmd.extend(["--labels", ",".join(labels)])
        
        if add_labels:
            cmd.extend(["--add-labels", ",".join(add_labels)])
        
        if remove_labels:
            cmd.extend(["--remove-labels", ",".join(remove_labels)])
        
        result = self._run_bd(cmd)
        
        issue_data = result.get("issue", {})
        return self._parse_issue_data(issue_data)
    
    def list_issues(
        self,
        project_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        labels: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Issue]:
        """
        List BEADS issues with optional filtering.
        
        Assumes: bd issue list [--project PROJECT_ID] [--status STATUS]
                 [--labels LABELS] [--limit LIMIT] --json
        """
        cmd = ["issue", "list"]
        
        if project_id:
            cmd.extend(["--project", project_id])
        
        if status:
            cmd.extend(["--status", self.STATUS_TO_BEADS[status]])
        
        if labels:
            cmd.extend(["--labels", ",".join(labels)])
        
        cmd.extend(["--limit", str(limit)])
        
        result = self._run_bd(cmd)
        
        issues = []
        for issue_data in result.get("issues", []):
            issues.append(self._parse_issue_data(issue_data))
        
        return issues
    
    # ==================== Comment Operations ====================
    
    def create_comment(self, issue_id: str, body: str) -> Comment:
        """
        Create a comment on a BEADS issue.
        
        Assumes: bd comment create ISSUE_ID --body BODY --json
        """
        result = self._run_bd([
            "comment", "create", issue_id,
            "--body", body
        ])
        
        comment_data = result.get("comment", {})
        return Comment(
            id=comment_data.get("id", ""),
            issue_id=issue_id,
            body=comment_data.get("body", body),
            created_at=self._parse_datetime(comment_data.get("createdAt")),
            author=comment_data.get("author", {}).get("name"),
        )
    
    def list_comments(self, issue_id: str) -> List[Comment]:
        """
        List all comments on a BEADS issue.
        
        Assumes: bd comment list ISSUE_ID --json
        """
        result = self._run_bd(["comment", "list", issue_id])
        
        comments = []
        for comment_data in result.get("comments", []):
            comments.append(Comment(
                id=comment_data.get("id", ""),
                issue_id=issue_id,
                body=comment_data.get("body", ""),
                created_at=self._parse_datetime(comment_data.get("createdAt")),
                author=comment_data.get("author", {}).get("name"),
            ))
        
        return comments
    
    # ==================== Health Check ====================
    
    def test_connection(self) -> bool:
        """
        Test connection to BEADS.
        
        Assumes: bd auth status
        """
        try:
            subprocess.run(
                ["bd", "auth", "status"],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
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
        """Parse BEADS issue data into generic Issue object."""
        # Parse labels
        labels = []
        for label_data in issue_data.get("labels", []):
            labels.append(Label(
                id=label_data.get("id", ""),
                name=label_data.get("name", ""),
                color=label_data.get("color"),
                description=label_data.get("description"),
            ))
        
        return Issue(
            id=issue_data.get("id", ""),
            title=issue_data.get("title", ""),
            description=issue_data.get("description"),
            status=self._parse_beads_status(issue_data.get("status", "TODO")),
            priority=self._parse_beads_priority(issue_data.get("priority", "MEDIUM")),
            project_id=issue_data.get("projectId"),
            labels=labels,
            created_at=self._parse_datetime(issue_data.get("createdAt")),
            updated_at=self._parse_datetime(issue_data.get("updatedAt")),
            metadata=issue_data.get("metadata", {}),
        )

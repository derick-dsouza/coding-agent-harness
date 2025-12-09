"""
BEADS Adapter Implementation
=============================

Maps BEADS task management to the generic TaskManagementAdapter interface.
Uses the BEADS CLI (bd) for all operations.

BEADS-specific concepts:
- Issues have statuses: open, in_progress, blocked, closed
- Priorities: 0 (critical) to 4 (backlog)
- Types: bug, feature, task, epic, chore
- Hash-based IDs (bd-a1b2, bd-f14c) for collision-free multi-worker support
- Dependency tracking: blocks, related, parent-child, discovered-from
- Git-backed database with JSONL storage
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
    
    Uses BEADS CLI (bd) to interact with the git-backed issue tracker.
    Maps BEADS concepts to generic task management interface.
    
    BEADS Status Values: open, in_progress, blocked, closed
    BEADS Priority Values: 0-4 (0=critical, 1=high, 2=medium, 3=low, 4=backlog)
    BEADS Types: bug, feature, task, epic, chore
    """
    
    # Rate limit configuration for BEADS (no rate limit)
    RATE_LIMIT_DURATION_MINUTES = 0
    RATE_LIMIT_MAX_REQUESTS = 0
    
    # Status mapping: Generic → BEADS
    STATUS_TO_BEADS = {
        IssueStatus.TODO: "open",
        IssueStatus.IN_PROGRESS: "in_progress",
        IssueStatus.DONE: "closed",
        IssueStatus.CANCELED: "closed",
    }
    
    # Status mapping: BEADS → Generic
    BEADS_TO_STATUS = {
        "open": IssueStatus.TODO,
        "in_progress": IssueStatus.IN_PROGRESS,
        "blocked": IssueStatus.IN_PROGRESS,
        "closed": IssueStatus.DONE,
    }
    
    # Priority mapping: Generic → BEADS (0-4 scale)
    PRIORITY_TO_BEADS = {
        IssuePriority.URGENT: 0,      # Critical
        IssuePriority.HIGH: 1,        # High
        IssuePriority.MEDIUM: 2,      # Medium (default)
        IssuePriority.LOW: 3,         # Low
    }
    
    # Priority mapping: BEADS → Generic
    BEADS_TO_PRIORITY = {
        0: IssuePriority.URGENT,      # Critical
        1: IssuePriority.HIGH,        # High
        2: IssuePriority.MEDIUM,      # Medium
        3: IssuePriority.LOW,         # Low
        4: IssuePriority.LOW,         # Backlog
    }
    
    def __init__(self, workspace: Optional[str] = None):
        """
        Initialize BEADS adapter.
        
        Args:
            workspace: Project directory (BEADS uses project-local databases)
        """
        self.workspace = workspace
        
        # Verify bd CLI is available
        try:
            result = subprocess.run(
                ["bd", "version", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            version_info = json.loads(result.stdout)
            self.bd_version = version_info.get("version", "unknown")
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            raise RuntimeError("BEADS CLI (bd) not found. Install from: https://github.com/steveyegge/beads")
    
    # ==================== Helper Methods ====================
    
    def _run_bd(self, args: List[str], cwd: Optional[str] = None) -> dict:
        """
        Run a bd CLI command and return parsed JSON output.
        
        Args:
            args: Command arguments (excluding 'bd')
            cwd: Working directory (defaults to self.workspace)
            
        Returns:
            Parsed JSON dict
        """
        cmd = ["bd"] + args
        
        # Add --json flag if not present
        if "--json" not in args:
            cmd.append("--json")
        
        work_dir = cwd or self.workspace
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=work_dir,
            check=True,
        )
        
        if result.stdout:
            return json.loads(result.stdout)
        
        return {}
    
    def _parse_beads_status(self, beads_status: str) -> IssueStatus:
        """Convert BEADS status to generic IssueStatus."""
        return self.BEADS_TO_STATUS.get(beads_status.lower(), IssueStatus.TODO)
    
    def _parse_beads_priority(self, beads_priority: int) -> IssuePriority:
        """Convert BEADS priority (0-4) to generic IssuePriority."""
        return self.BEADS_TO_PRIORITY.get(beads_priority, IssuePriority.MEDIUM)
    
    # ==================== Team Operations ====================
    
    def list_teams(self) -> List[Team]:
        """
        List teams.
        
        Note: BEADS is project-local and doesn't have teams.
        Returns empty list for interface compatibility.
        """
        return []
    
    # ==================== Project Operations ====================
    
    def create_project(
        self,
        name: str,
        team_ids: List[str],
        description: Optional[str] = None,
    ) -> Project:
        """
        Create a project.
        
        Note: BEADS uses `bd init` to create project-local databases.
        This method creates a synthetic Project object for interface compatibility.
        Real initialization should be done via `bd init` in the project directory.
        """
        # Return synthetic project (BEADS doesn't have central project management)
        return Project(
            id=name,
            name=name,
            description=description,
            team_ids=[],
            created_at=datetime.now(),
        )
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.
        
        Note: BEADS is project-local. Returns current project info if initialized.
        """
        try:
            # Check if bd is initialized in workspace
            result = self._run_bd(["info"])
            
            db_path = result.get("database_path", "")
            if db_path:
                return Project(
                    id=project_id,
                    name=project_id,
                    description="BEADS project",
                    team_ids=[],
                    created_at=None,
                )
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def list_projects(self, team_id: Optional[str] = None) -> List[Project]:
        """
        List projects.
        
        Note: BEADS is project-local. Returns current project if initialized.
        """
        project = self.get_project("current")
        return [project] if project else []
    
    # ==================== Label Operations ====================
    
    def create_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Label:
        """
        Create a label.
        
        Note: BEADS labels are added directly to issues via `bd label add`.
        This returns a synthetic Label object for interface compatibility.
        """
        return Label(
            id=name,
            name=name,
            color=color,
            description=description,
        )
    
    def list_labels(self) -> List[Label]:
        """
        List all labels used in issues.
        
        Uses: bd label list-all --json
        """
        try:
            result = self._run_bd(["label", "list-all"])
            
            labels = []
            # Output format: {"labels": [{"name": "backend", "count": 5}, ...]}
            for label_data in result.get("labels", []):
                labels.append(Label(
                    id=label_data.get("name", ""),
                    name=label_data.get("name", ""),
                    color=None,  # BEADS doesn't store label colors
                    description=f"Used {label_data.get('count', 0)} times",
                ))
            
            return labels
        except subprocess.CalledProcessError:
            return []
    
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
        
        Uses: bd create TITLE --description DESC --priority P --type TYPE --labels L1,L2
        
        Note: BEADS creates issues with status=open by default.
        Status can be updated separately if needed.
        """
        cmd = ["create", title]
        
        if description:
            cmd.extend(["--description", description])
        
        # Map priority
        beads_priority = self.PRIORITY_TO_BEADS[priority]
        cmd.extend(["--priority", str(beads_priority)])
        
        # Default type is 'task'
        cmd.extend(["--type", "task"])
        
        if labels:
            cmd.extend(["--labels", ",".join(labels)])
        
        result = self._run_bd(cmd)
        
        # bd create returns the created issue
        return self._parse_issue_data(result)
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get a BEADS issue by ID.
        
        Uses: bd show ISSUE_ID --json
        """
        try:
            result = self._run_bd(["show", issue_id])
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
        Update a BEADS issue.
        
        Uses: bd update ISSUE_ID --status STATUS --priority P
              bd label add ISSUE_ID LABEL
              bd label remove ISSUE_ID LABEL
        """
        # Update basic fields
        if title is not None or description is not None or status is not None or priority is not None:
            cmd = ["update", issue_id]
            
            if title is not None:
                cmd.extend(["--title", title])
            
            if description is not None:
                cmd.extend(["--description", description])
            
            if status is not None:
                beads_status = self.STATUS_TO_BEADS[status]
                cmd.extend(["--status", beads_status])
            
            if priority is not None:
                beads_priority = self.PRIORITY_TO_BEADS[priority]
                cmd.extend(["--priority", str(beads_priority)])
            
            self._run_bd(cmd)
        
        # Handle labels separately
        if add_labels:
            for label in add_labels:
                try:
                    self._run_bd(["label", "add", issue_id, label])
                except subprocess.CalledProcessError:
                    pass  # Label might already exist
        
        if remove_labels:
            for label in remove_labels:
                try:
                    self._run_bd(["label", "remove", issue_id, label])
                except subprocess.CalledProcessError:
                    pass  # Label might not exist
        
        # Replace all labels if labels param is provided
        if labels is not None:
            # Get current labels
            current_issue = self.get_issue(issue_id)
            if current_issue:
                current_labels = {label.name for label in current_issue.labels}
                new_labels = set(labels)
                
                # Remove labels not in new set
                for label in current_labels - new_labels:
                    try:
                        self._run_bd(["label", "remove", issue_id, label])
                    except subprocess.CalledProcessError:
                        pass
                
                # Add labels not in current set
                for label in new_labels - current_labels:
                    try:
                        self._run_bd(["label", "add", issue_id, label])
                    except subprocess.CalledProcessError:
                        pass
        
        # Return updated issue
        updated = self.get_issue(issue_id)
        if not updated:
            raise RuntimeError(f"Failed to retrieve updated issue {issue_id}")
        
        return updated
    
    def list_issues(
        self,
        project_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        labels: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Issue]:
        """
        List BEADS issues with optional filtering.
        
        Uses: bd list --status STATUS --label LABELS --limit LIMIT --json
        """
        cmd = ["list"]
        
        # Note: BEADS is project-local, so project_id is ignored
        
        if status:
            beads_status = self.STATUS_TO_BEADS[status]
            cmd.extend(["--status", beads_status])
        
        if labels:
            # BEADS --label flag uses AND semantics (must have all labels)
            cmd.extend(["--label", ",".join(labels)])
        
        cmd.extend(["--limit", str(limit)])
        
        result = self._run_bd(cmd)
        
        issues = []
        # bd list returns array of issues directly
        issue_list = result if isinstance(result, list) else result.get("issues", [])
        
        for issue_data in issue_list:
            issues.append(self._parse_issue_data(issue_data))
        
        return issues
    
    # ==================== Comment Operations ====================
    
    def create_comment(self, issue_id: str, body: str) -> Comment:
        """
        Create a comment on a BEADS issue.
        
        Note: BEADS doesn't have first-class comments in the CLI.
        This adds a note to the issue's notes field instead.
        
        Workaround: Appends to issue description or uses notes field.
        """
        # Get current issue
        issue = self.get_issue(issue_id)
        if not issue:
            raise RuntimeError(f"Issue {issue_id} not found")
        
        # Append comment to description
        timestamp = datetime.now().isoformat()
        comment_text = f"\n\n---\n**Comment ({timestamp}):**\n{body}"
        
        new_description = (issue.description or "") + comment_text
        
        self._run_bd([
            "update", issue_id,
            "--description", new_description
        ])
        
        # Return synthetic comment
        return Comment(
            id=f"{issue_id}-{timestamp}",
            issue_id=issue_id,
            body=body,
            created_at=datetime.now(),
            author="system",
        )
    
    def list_comments(self, issue_id: str) -> List[Comment]:
        """
        List all comments on a BEADS issue.
        
        Note: BEADS doesn't have first-class comments.
        Returns empty list for interface compatibility.
        """
        return []
    
    # ==================== Health Check ====================
    
    def test_connection(self) -> bool:
        """
        Test connection to BEADS.
        
        Uses: bd info --json to check if database is initialized.
        """
        try:
            result = self._run_bd(["info"])
            # Check if database path exists in output
            return bool(result.get("database_path"))
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
        """
        Parse BEADS issue data into generic Issue object.
        
        BEADS JSON structure:
        {
            "id": "bd-a1b2",
            "title": "Fix bug",
            "description": "Details here",
            "status": "open",
            "priority": 1,
            "type": "bug",
            "labels": ["backend", "urgent"],
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T11:00:00Z",
            "assignee": "alice",
            ...
        }
        """
        # Parse labels (BEADS stores labels as strings, not objects)
        labels = []
        for label_name in issue_data.get("labels", []):
            labels.append(Label(
                id=label_name,
                name=label_name,
                color=None,
                description=None,
            ))
        
        # Extract priority and status
        raw_priority = issue_data.get("priority", 2)
        raw_status = issue_data.get("status", "open")
        
        return Issue(
            id=issue_data.get("id", ""),
            title=issue_data.get("title", ""),
            description=issue_data.get("description"),
            status=self._parse_beads_status(raw_status),
            priority=self._parse_beads_priority(raw_priority),
            project_id=None,  # BEADS is project-local
            labels=labels,
            created_at=self._parse_datetime(issue_data.get("created_at")),
            updated_at=self._parse_datetime(issue_data.get("updated_at")),
            metadata={
                "type": issue_data.get("type", "task"),
                "assignee": issue_data.get("assignee"),
                "beads_version": self.bd_version,
            },
        )

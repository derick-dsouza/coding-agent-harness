"""
Linear Adapter Implementation
==============================

Maps Linear's API to the generic TaskManagementAdapter interface.
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any
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


class LinearAdapter(TaskManagementAdapter):
    """
    Linear implementation of the TaskManagementAdapter.
    
    Uses MCP (Model Context Protocol) tools to interact with Linear API.
    Maps Linear's terminology to generic task management concepts:
    - Linear Project → Project
    - Linear Issue → Issue
    - Linear Label → Label
    - Linear Status (Todo, In Progress, Done, Canceled) → IssueStatus
    - Linear Priority (1-4) → IssuePriority
    """
    
    # Rate limit configuration for Linear API
    RATE_LIMIT_DURATION_MINUTES = 60  # 1 hour rolling window
    RATE_LIMIT_MAX_REQUESTS = 1500    # 1500 requests per hour
    
    # Status mapping: Generic → Linear
    STATUS_TO_LINEAR = {
        IssueStatus.TODO: "Todo",
        IssueStatus.IN_PROGRESS: "In Progress",
        IssueStatus.DONE: "Done",
        IssueStatus.CANCELED: "Canceled",
    }
    
    # Status mapping: Linear → Generic
    LINEAR_TO_STATUS = {
        "Todo": IssueStatus.TODO,
        "Backlog": IssueStatus.TODO,
        "In Progress": IssueStatus.IN_PROGRESS,
        "Done": IssueStatus.DONE,
        "Completed": IssueStatus.DONE,
        "Canceled": IssueStatus.CANCELED,
        "Cancelled": IssueStatus.CANCELED,
    }
    
    # Priority mapping: Generic → Linear (1-4)
    PRIORITY_TO_LINEAR = {
        IssuePriority.URGENT: 1,
        IssuePriority.HIGH: 2,
        IssuePriority.MEDIUM: 3,
        IssuePriority.LOW: 4,
    }
    
    # Priority mapping: Linear → Generic
    LINEAR_TO_PRIORITY = {
        0: IssuePriority.URGENT,  # Sometimes 0 is used
        1: IssuePriority.URGENT,
        2: IssuePriority.HIGH,
        3: IssuePriority.MEDIUM,
        4: IssuePriority.LOW,
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Linear adapter.
        
        Args:
            api_key: Linear API key (if None, reads from LINEAR_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError("LINEAR_API_KEY not provided and not in environment")
    
    # ==================== Helper Methods ====================
    
    def _call_mcp_tool(self, tool_name: str, **kwargs):
        """
        Call an MCP tool (placeholder - actual implementation uses Claude SDK).
        
        In real usage, this would be called through the Claude Agent SDK's
        tool execution mechanism.
        """
        # This is a placeholder - in actual usage, MCP tools are called
        # through the agent's execution context, not directly
        raise NotImplementedError(
            f"MCP tool '{tool_name}' must be called through agent context"
        )
    
    def _parse_linear_status(self, linear_status: str) -> IssueStatus:
        """Convert Linear status string to generic IssueStatus."""
        return self.LINEAR_TO_STATUS.get(linear_status, IssueStatus.TODO)
    
    def _parse_linear_priority(self, linear_priority: int) -> IssuePriority:
        """Convert Linear priority (1-4) to generic IssuePriority."""
        return self.LINEAR_TO_PRIORITY.get(linear_priority, IssuePriority.MEDIUM)
    
    # ==================== Team Operations ====================
    
    def list_teams(self) -> List[Team]:
        """List all Linear teams."""
        # Call: mcp__linear__list_teams
        # Returns: List of teams with id, name, description
        result = self._call_mcp_tool("mcp__linear__list_teams")
        
        teams = []
        for team_data in result.get("teams", []):
            teams.append(Team(
                id=team_data["id"],
                name=team_data["name"],
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
        """Create a Linear project."""
        # Call: mcp__linear__create_project
        result = self._call_mcp_tool(
            "mcp__linear__create_project",
            name=name,
            teamIds=team_ids,
            description=description,
        )
        
        project_data = result.get("project", {})
        return Project(
            id=project_data["id"],
            name=project_data["name"],
            description=project_data.get("description"),
            team_ids=team_ids,
            created_at=self._parse_datetime(project_data.get("createdAt")),
        )
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a Linear project by ID."""
        # Call: mcp__linear__get_project
        try:
            result = self._call_mcp_tool(
                "mcp__linear__get_project",
                projectId=project_id,
            )
            
            project_data = result.get("project", {})
            return Project(
                id=project_data["id"],
                name=project_data["name"],
                description=project_data.get("description"),
                team_ids=project_data.get("teamIds", []),
                created_at=self._parse_datetime(project_data.get("createdAt")),
            )
        except Exception:
            return None
    
    def list_projects(self, team_id: Optional[str] = None) -> List[Project]:
        """List Linear projects, optionally filtered by team."""
        # Call: mcp__linear__list_projects
        kwargs = {}
        if team_id:
            kwargs["teamId"] = team_id
        
        result = self._call_mcp_tool("mcp__linear__list_projects", **kwargs)
        
        projects = []
        for project_data in result.get("projects", []):
            projects.append(Project(
                id=project_data["id"],
                name=project_data["name"],
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
        """Create a Linear label."""
        try:
            # Call: mcp__linear__create_label
            result = self._call_mcp_tool(
                "mcp__linear__create_label",
                name=name,
                color=color,
                description=description,
            )
            
            label_data = result.get("label", {})
            return Label(
                id=label_data["id"],
                name=label_data["name"],
                color=label_data.get("color"),
                description=label_data.get("description"),
            )
        except Exception as e:
            # Handle permission errors gracefully
            error_msg = str(e).lower()
            if "permission" in error_msg or "forbidden" in error_msg or "unauthorized" in error_msg:
                # Try to find existing label instead
                existing_labels = self.list_labels()
                matching = [l for l in existing_labels if l.name.lower() == name.lower()]
                if matching:
                    print(f"  [Warning] Cannot create label '{name}' (insufficient permissions). Using existing label.")
                    return matching[0]
                else:
                    print(f"  [Warning] Cannot create label '{name}' (insufficient permissions) and no existing label found.")
                    # Return a dummy label for compatibility
                    return Label(id=f"dummy-{name}", name=name, color=color, description=description)
            raise
    
    def list_labels(self) -> List[Label]:
        """List all Linear labels."""
        # Call: mcp__linear__list_labels
        result = self._call_mcp_tool("mcp__linear__list_labels")
        
        labels = []
        for label_data in result.get("labels", []):
            labels.append(Label(
                id=label_data["id"],
                name=label_data["name"],
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
        """Create a Linear issue."""
        # Call: mcp__linear__create_issue
        kwargs = {
            "title": title,
            "description": description or "",
            "priority": self.PRIORITY_TO_LINEAR[priority],
        }
        
        if project_id:
            kwargs["projectId"] = project_id
        
        if labels:
            kwargs["labelIds"] = labels
        
        # Note: Linear typically starts issues in "Todo" status
        # Status changes happen via update_issue
        
        result = self._call_mcp_tool("mcp__linear__create_issue", **kwargs)
        
        issue_data = result.get("issue", {})
        return self._parse_issue_data(issue_data)
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """Get a Linear issue by ID."""
        # Call: mcp__linear__get_issue
        try:
            result = self._call_mcp_tool(
                "mcp__linear__get_issue",
                issueId=issue_id,
            )
            
            issue_data = result.get("issue", {})
            return self._parse_issue_data(issue_data)
        except Exception:
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
        """Update a Linear issue."""
        # Call: mcp__linear__update_issue
        kwargs = {"issueId": issue_id}
        
        if title is not None:
            kwargs["title"] = title
        
        if description is not None:
            kwargs["description"] = description
        
        if status is not None:
            kwargs["status"] = self.STATUS_TO_LINEAR[status]
        
        if priority is not None:
            kwargs["priority"] = self.PRIORITY_TO_LINEAR[priority]
        
        # Handle labels
        if labels is not None:
            kwargs["labelIds"] = labels
        elif add_labels or remove_labels:
            # Need to fetch current labels and merge
            current_issue = self.get_issue(issue_id)
            current_label_ids = [label.id for label in current_issue.labels]
            
            if add_labels:
                current_label_ids.extend(add_labels)
            
            if remove_labels:
                current_label_ids = [
                    lid for lid in current_label_ids if lid not in remove_labels
                ]
            
            kwargs["labelIds"] = list(set(current_label_ids))  # Remove duplicates
        
        result = self._call_mcp_tool("mcp__linear__update_issue", **kwargs)
        
        issue_data = result.get("issue", {})
        return self._parse_issue_data(issue_data)
    
    def update_issues_batch(
        self,
        updates: List[Dict[str, Any]],
        batch_size: int = 20,
    ) -> List[Issue]:
        """
        Update multiple Linear issues in batches using GraphQL mutations.
        
        Linear's GraphQL API supports batching multiple mutations in a single request.
        This significantly reduces API calls and helps avoid rate limits.
        
        Args:
            updates: List of update dictionaries (see parent class for format)
            batch_size: Number of updates per API call (default: 20, max: ~30)
            
        Returns:
            List of updated Issue objects
            
        Note:
            Linear GraphQL supports aliased mutations like:
            mutation {
              issue1: issueUpdate(id: "...", input: {...}) { id title }
              issue2: issueUpdate(id: "...", input: {...}) { id title }
              ...
            }
            
            A batch size of 20 is conservative and safe. Linear typically
            allows 20-30 mutations per request.
        """
        import requests
        import json
        
        all_results = []
        
        # Process in batches
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # Build GraphQL batch mutation with aliased mutations
            mutations = []
            for idx, update in enumerate(batch):
                issue_id = update.get("issue_id")
                if not issue_id:
                    continue
                
                # Build input object for GraphQL
                input_parts = []
                
                if "title" in update:
                    escaped_title = json.dumps(update["title"])
                    input_parts.append(f'title: {escaped_title}')
                
                if "description" in update:
                    escaped_desc = json.dumps(update["description"])
                    input_parts.append(f'description: {escaped_desc}')
                
                if "status" in update:
                    status_value = self.STATUS_TO_LINEAR.get(update["status"], update["status"])
                    input_parts.append(f'stateId: "{status_value}"')
                
                if "priority" in update:
                    priority_value = self.PRIORITY_TO_LINEAR.get(update["priority"], update["priority"])
                    input_parts.append(f'priority: {priority_value}')
                
                if "labels" in update:
                    label_ids = json.dumps(update["labels"])
                    input_parts.append(f'labelIds: {label_ids}')
                
                # Build the mutation for this issue
                if input_parts:
                    input_str = ', '.join(input_parts)
                    mutation = f'''
                      issue{idx}: issueUpdate(
                        id: "{issue_id}",
                        input: {{ {input_str} }}
                      ) {{
                        id
                        title
                        description
                        state {{ name }}
                        priority
                        labels {{ nodes {{ id name color }} }}
                        createdAt
                        updatedAt
                      }}
                    '''
                    mutations.append(mutation)
            
            if not mutations:
                continue
            
            # Build complete GraphQL mutation
            query = f'''
              mutation BatchUpdateIssues {{
                {' '.join(mutations)}
              }}
            '''
            
            # Send GraphQL request directly to Linear API
            try:
                response = requests.post(
                    'https://api.linear.app/graphql',
                    headers={
                        'Authorization': self.api_key,
                        'Content-Type': 'application/json',
                    },
                    json={'query': query},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse results
                if 'data' in data:
                    for idx in range(len(batch)):
                        result_key = f'issue{idx}'
                        if result_key in data['data']:
                            issue_data = data['data'][result_key]
                            all_results.append(self._parse_issue_data(issue_data))
                
                # Handle GraphQL errors
                if 'errors' in data:
                    print(f"⚠️  GraphQL batch update had errors: {data['errors']}")
                    # Fall back to individual updates for failed items
                    # (error handling could be more sophisticated)
                    
            except Exception as e:
                print(f"⚠️  GraphQL batch update failed: {e}")
                print(f"   Falling back to individual updates for this batch...")
                
                # Fallback: Process batch with individual calls
                for update in batch:
                    issue_id = update.get("issue_id")
                    if not issue_id:
                        continue
                    
                    # Convert Dict[str, Any] to typed parameters
                    kwargs = {}
                    if "title" in update:
                        kwargs["title"] = update["title"]
                    if "description" in update:
                        kwargs["description"] = update["description"]
                    if "status" in update:
                        kwargs["status"] = update["status"]
                    if "priority" in update:
                        kwargs["priority"] = update["priority"]
                    if "labels" in update:
                        kwargs["labels"] = update["labels"]
                    if "add_labels" in update:
                        kwargs["add_labels"] = update["add_labels"]
                    if "remove_labels" in update:
                        kwargs["remove_labels"] = update["remove_labels"]
                    
                    try:
                        updated_issue = self.update_issue(issue_id, **kwargs)
                        all_results.append(updated_issue)
                    except Exception as inner_e:
                        print(f"   Failed to update issue {issue_id}: {inner_e}")
        
        return all_results
    
    def list_issues(
        self,
        project_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        labels: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Issue]:
        """List Linear issues with optional filtering."""
        # Call: mcp__linear__list_issues
        kwargs = {"limit": limit}
        
        if project_id:
            kwargs["projectId"] = project_id
        
        if status:
            kwargs["status"] = self.STATUS_TO_LINEAR[status]
        
        if labels:
            kwargs["labels"] = labels
        
        result = self._call_mcp_tool("mcp__linear__list_issues", **kwargs)
        
        issues = []
        for issue_data in result.get("issues", []):
            issues.append(self._parse_issue_data(issue_data))
        return issues
    
    # ==================== Comment Operations ====================
    
    def create_comment(self, issue_id: str, body: str) -> Comment:
        """Create a comment on a Linear issue."""
        # Call: mcp__linear__create_comment
        result = self._call_mcp_tool(
            "mcp__linear__create_comment",
            issueId=issue_id,
            body=body,
        )
        
        comment_data = result.get("comment", {})
        return Comment(
            id=comment_data["id"],
            issue_id=issue_id,
            body=comment_data["body"],
            created_at=self._parse_datetime(comment_data.get("createdAt")),
            author=comment_data.get("author", {}).get("name"),
        )
    
    def list_comments(self, issue_id: str) -> List[Comment]:
        """List all comments on a Linear issue."""
        # Call: mcp__linear__list_comments
        result = self._call_mcp_tool(
            "mcp__linear__list_comments",
            issueId=issue_id,
        )
        
        comments = []
        for comment_data in result.get("comments", []):
            comments.append(Comment(
                id=comment_data["id"],
                issue_id=issue_id,
                body=comment_data["body"],
                created_at=self._parse_datetime(comment_data.get("createdAt")),
                author=comment_data.get("author", {}).get("name"),
            ))
        return comments
    
    # ==================== Health Check ====================
    
    def test_connection(self) -> bool:
        """Test connection to Linear API."""
        try:
            # Try to list teams as a health check
            self.list_teams()
            return True
        except Exception:
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
        """Parse Linear issue data into generic Issue object."""
        # Parse labels
        labels = []
        for label_data in issue_data.get("labels", []):
            labels.append(Label(
                id=label_data["id"],
                name=label_data["name"],
                color=label_data.get("color"),
                description=label_data.get("description"),
            ))
        
        return Issue(
            id=issue_data["id"],
            title=issue_data["title"],
            description=issue_data.get("description"),
            status=self._parse_linear_status(issue_data.get("status", "Todo")),
            priority=self._parse_linear_priority(issue_data.get("priority", 3)),
            project_id=issue_data.get("projectId"),
            labels=labels,
            created_at=self._parse_datetime(issue_data.get("createdAt")),
            updated_at=self._parse_datetime(issue_data.get("updatedAt")),
            metadata={"linear_url": issue_data.get("url")},  # Store Linear-specific data
        )

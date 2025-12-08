"""
Task Management Adapter Factory
================================

Factory for creating task management adapters based on configuration.
"""

import os
from typing import Optional

from .interface import TaskManagementAdapter
from .linear_adapter import LinearAdapter
from .github_adapter import GitHubAdapter
from .beads_adapter import BeadsAdapter


class AdapterType:
    """Supported adapter types."""
    LINEAR = "linear"
    GITHUB = "github"
    BEADS = "beads"
    # Future adapters:
    # JIRA = "jira"
    # ASANA = "asana"


def create_adapter(
    adapter_type: str = "linear",
    api_key: Optional[str] = None,
    **kwargs
) -> TaskManagementAdapter:
    """
    Create a task management adapter.
    
    Args:
        adapter_type: Type of adapter ("linear", "github", "beads", etc.)
        api_key: API key for the service (if None, reads from environment)
        **kwargs: Additional adapter-specific configuration
            - For GitHub: owner (str), repo (str)
            - For BEADS: workspace (str, optional)
        
    Returns:
        TaskManagementAdapter instance
        
    Raises:
        ValueError: If adapter_type is not supported or required kwargs missing
        
    Examples:
        # Create Linear adapter (reads LINEAR_API_KEY from env)
        adapter = create_adapter("linear")
        
        # Create Linear adapter with explicit API key
        adapter = create_adapter("linear", api_key="lin_api_...")
        
        # Create GitHub adapter (uses gh CLI, no API key needed)
        adapter = create_adapter("github", owner="myorg", repo="myrepo")
        
        # Create BEADS adapter (uses bd CLI, optional workspace)
        adapter = create_adapter("beads", workspace="my-workspace")
    """
    adapter_type = adapter_type.lower()
    
    if adapter_type == AdapterType.LINEAR:
        return LinearAdapter(api_key=api_key)
    
    elif adapter_type == AdapterType.GITHUB:
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        if not owner or not repo:
            raise ValueError("GitHub adapter requires 'owner' and 'repo' kwargs")
        return GitHubAdapter(owner=owner, repo=repo)
    
    elif adapter_type == AdapterType.BEADS:
        workspace = kwargs.get("workspace")
        return BeadsAdapter(workspace=workspace)
    
    # Future adapter types:
    # elif adapter_type == "jira":
    #     return JiraAdapter(api_key=api_key, url=kwargs.get("url"))
    
    else:
        raise ValueError(
            f"Unsupported adapter type: {adapter_type}. "
            f"Supported types: {AdapterType.LINEAR}, {AdapterType.GITHUB}, {AdapterType.BEADS}"
        )


def get_adapter_from_env() -> TaskManagementAdapter:
    """
    Create adapter based on environment variables.
    
    Environment Variables:
    - TASK_ADAPTER_TYPE: "linear", "github", or "beads" (default: "linear")
    
    Linear:
    - LINEAR_API_KEY: Linear API key
    
    GitHub:
    - GITHUB_OWNER: Repository owner
    - GITHUB_REPO: Repository name
    
    BEADS:
    - BEADS_WORKSPACE: Workspace ID (optional)
    
    Returns:
        TaskManagementAdapter instance
    """
    adapter_type = os.getenv("TASK_ADAPTER_TYPE", "linear")
    
    if adapter_type == AdapterType.LINEAR:
        api_key = os.getenv("LINEAR_API_KEY")
        if not api_key:
            raise ValueError("LINEAR_API_KEY environment variable not set")
        return LinearAdapter(api_key=api_key)
    
    elif adapter_type == AdapterType.GITHUB:
        owner = os.getenv("GITHUB_OWNER")
        repo = os.getenv("GITHUB_REPO")
        if not owner or not repo:
            raise ValueError("GITHUB_OWNER and GITHUB_REPO environment variables must be set")
        return GitHubAdapter(owner=owner, repo=repo)
    
    elif adapter_type == AdapterType.BEADS:
        workspace = os.getenv("BEADS_WORKSPACE")
        return BeadsAdapter(workspace=workspace)
    
    # Future adapters:
    # elif adapter_type == "jira":
    #     api_key = os.getenv("JIRA_API_KEY")
    #     url = os.getenv("JIRA_URL")
    #     if not api_key or not url:
    #         raise ValueError("JIRA_API_KEY and JIRA_URL must be set")
    #     return JiraAdapter(api_key=api_key, url=url)
    
    else:
        raise ValueError(f"Unsupported TASK_ADAPTER_TYPE: {adapter_type}")

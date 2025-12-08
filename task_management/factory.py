"""
Task Management Adapter Factory
================================

Factory for creating task management adapters based on configuration.
"""

import os
from typing import Optional

from .interface import TaskManagementAdapter
from .linear_adapter import LinearAdapter


class AdapterType:
    """Supported adapter types."""
    LINEAR = "linear"
    # Future adapters:
    # JIRA = "jira"
    # GITHUB = "github"
    # ASANA = "asana"


def create_adapter(
    adapter_type: str = "linear",
    api_key: Optional[str] = None,
    **kwargs
) -> TaskManagementAdapter:
    """
    Create a task management adapter.
    
    Args:
        adapter_type: Type of adapter ("linear", "jira", "github", etc.)
        api_key: API key for the service (if None, reads from environment)
        **kwargs: Additional adapter-specific configuration
        
    Returns:
        TaskManagementAdapter instance
        
    Raises:
        ValueError: If adapter_type is not supported
        
    Examples:
        # Create Linear adapter (reads LINEAR_API_KEY from env)
        adapter = create_adapter("linear")
        
        # Create Linear adapter with explicit API key
        adapter = create_adapter("linear", api_key="lin_api_...")
        
        # Future: Create Jira adapter
        # adapter = create_adapter("jira", api_key="jira_token", url="https://company.atlassian.net")
    """
    adapter_type = adapter_type.lower()
    
    if adapter_type == AdapterType.LINEAR:
        return LinearAdapter(api_key=api_key)
    
    # Future adapter types:
    # elif adapter_type == AdapterType.JIRA:
    #     return JiraAdapter(api_key=api_key, url=kwargs.get("url"))
    # elif adapter_type == AdapterType.GITHUB:
    #     return GitHubAdapter(api_key=api_key, repo=kwargs.get("repo"))
    
    else:
        raise ValueError(
            f"Unsupported adapter type: {adapter_type}. "
            f"Supported types: {AdapterType.LINEAR}"
        )


def get_adapter_from_env() -> TaskManagementAdapter:
    """
    Create adapter based on environment variables.
    
    Checks for:
    - TASK_ADAPTER_TYPE (default: "linear")
    - LINEAR_API_KEY (for Linear adapter)
    - JIRA_API_KEY + JIRA_URL (for Jira adapter)
    - GITHUB_TOKEN (for GitHub adapter)
    
    Returns:
        TaskManagementAdapter instance
    """
    adapter_type = os.getenv("TASK_ADAPTER_TYPE", "linear")
    
    if adapter_type == AdapterType.LINEAR:
        api_key = os.getenv("LINEAR_API_KEY")
        if not api_key:
            raise ValueError("LINEAR_API_KEY environment variable not set")
        return LinearAdapter(api_key=api_key)
    
    # Future adapters:
    # elif adapter_type == "jira":
    #     api_key = os.getenv("JIRA_API_KEY")
    #     url = os.getenv("JIRA_URL")
    #     if not api_key or not url:
    #         raise ValueError("JIRA_API_KEY and JIRA_URL must be set")
    #     return JiraAdapter(api_key=api_key, url=url)
    
    else:
        raise ValueError(f"Unsupported TASK_ADAPTER_TYPE: {adapter_type}")

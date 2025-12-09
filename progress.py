"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
Progress is tracked via task management system (Linear, Jira, GitHub, etc.),
with local state cached in .task_project.json.
"""

import json
from pathlib import Path

# Generic task project marker
TASK_PROJECT_MARKER = ".task_project.json"

# Legacy marker names for backward compatibility
LEGACY_LINEAR_MARKER = ".linear_project.json"


def load_task_project_state(project_dir: Path) -> dict | None:
    """
    Load the task project state from the marker file.
    
    Supports both new (.task_project.json) and legacy (.linear_project.json) formats.

    Args:
        project_dir: Directory containing task project state file

    Returns:
        Project state dict or None if not initialized
    """
    # Try new format first
    marker_file = project_dir / TASK_PROJECT_MARKER
    
    # Fallback to legacy format for backward compatibility
    if not marker_file.exists():
        marker_file = project_dir / LEGACY_LINEAR_MARKER

    if not marker_file.exists():
        return None

    try:
        with open(marker_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_linear_project_state(project_dir: Path) -> dict | None:
    """
    Legacy function - redirects to load_task_project_state.
    Kept for backward compatibility.

    Args:
        project_dir: Directory containing project state

    Returns:
        Project state dict or None if not initialized
    """
    return load_task_project_state(project_dir)


def is_task_initialized(project_dir: Path) -> bool:
    """
    Check if task project has been initialized.

    Args:
        project_dir: Directory to check

    Returns:
        True if task project state file exists and is valid
    """
    state = load_task_project_state(project_dir)
    return state is not None and state.get("initialized", False)


def is_linear_initialized(project_dir: Path) -> bool:
    """
    Legacy function - redirects to is_task_initialized.
    Kept for backward compatibility.

    Args:
        project_dir: Directory to check

    Returns:
        True if task project is initialized
    """
    return is_task_initialized(project_dir)


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type = "INITIALIZER" if is_initializer else "CODING AGENT"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """
    Print a summary of current progress.

    Since actual progress is tracked in the task management system,
    this reads the local state file for cached information. The agent
    updates the task system directly and reports progress in session comments.
    """
    state = load_task_project_state(project_dir)

    if state is None:
        print("\nProgress: Task management project not yet initialized")
        return

    total = state.get("total_issues", 0)
    meta_issue = state.get("meta_issue_id", "unknown")
    audits_completed = state.get("audits_completed", 0)
    features_awaiting = state.get("features_awaiting_audit", 0)
    adapter_type = state.get("adapter_type", "linear")  # Default to linear for backward compat

    print(f"\nTask Management Project Status ({adapter_type}):")
    print(f"  Total issues created: {total}")
    print(f"  META issue ID: {meta_issue}")
    print(f"  (Check {adapter_type.title()} for current Done/In Progress/Todo counts)")
    
    if audits_completed > 0:
        print(f"\nAudit Status:")
        print(f"  Audits completed: {audits_completed}")
        print(f"  Features awaiting audit: {features_awaiting}")
        if features_awaiting >= 10:
            print(f"  ⚠️  Audit threshold reached - next session will be an audit")
        elif features_awaiting > 5:
            print(f"  ⏳ Approaching audit threshold ({features_awaiting}/10)")


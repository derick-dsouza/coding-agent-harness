"""
Linear Configuration
====================

Configuration constants for Linear integration.
These values are used in prompts and for project state management.
"""

import os
import json
from pathlib import Path

def _get_linear_api_key_name():
    """Get the LINEAR API key environment variable name from defaults."""
    defaults_path = Path(__file__).parent / "autocode-defaults.json"
    try:
        with open(defaults_path, 'r') as f:
            defaults = json.load(f)
            return defaults.get("task_adapters", {}).get("linear", {}).get("api_key_env", "LINEAR_API_KEY")
    except:
        return "LINEAR_API_KEY"  # Fallback to default

# Environment variables (must be set before running)
LINEAR_API_KEY = os.environ.get(_get_linear_api_key_name())

# Default number of issues to create (can be overridden via command line)
DEFAULT_ISSUE_COUNT = 50

# Issue status workflow (Linear default states)
STATUS_TODO = "Todo"
STATUS_IN_PROGRESS = "In Progress"
STATUS_DONE = "Done"

# Label categories (map to feature types)
LABEL_FUNCTIONAL = "functional"
LABEL_STYLE = "style"
LABEL_INFRASTRUCTURE = "infrastructure"

# Priority mapping (Linear uses 0-4 where 1=Urgent, 4=Low, 0=No priority)
PRIORITY_URGENT = 1
PRIORITY_HIGH = 2
PRIORITY_MEDIUM = 3
PRIORITY_LOW = 4

# Local marker file to track Linear project initialization
LINEAR_PROJECT_MARKER = ".linear_project.json"

# Meta issue title for project tracking and session handoff
META_ISSUE_TITLE = "[META] Project Progress Tracker"

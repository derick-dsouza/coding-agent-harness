"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"
TASK_MANAGERS_DIR = PROMPTS_DIR / "task_managers"
TASK_ADAPTERS_DIR = PROMPTS_DIR / "task_adapters"

# Default spec file name used in prompt templates
DEFAULT_SPEC_FILE = "app_spec.txt"


def load_prompt(name: str, spec_file: Path | None = None, task_adapter: str | None = None) -> str:
    """Load a prompt template from the prompts directory.

    Args:
        name: Name of the prompt template (without .md extension)
        spec_file: Optional spec file path to substitute in the template
        task_adapter: Task management adapter (linear, beads, github)

    Returns:
        The prompt template with spec file name substituted and task manager guide included
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"
    content = prompt_path.read_text()

    # Replace default spec file name with custom one if provided
    if spec_file is not None:
        content = content.replace(DEFAULT_SPEC_FILE, str(spec_file))

    # Include command restrictions (always included)
    cmd_restrictions_path = TASK_ADAPTERS_DIR / "command_restrictions.txt"
    if cmd_restrictions_path.exists():
        cmd_restrictions_content = cmd_restrictions_path.read_text()
        # Insert at the very beginning before role section
        content = f"{cmd_restrictions_content}\n\n{content}"
    
    # Include task manager-specific guidance if adapter specified
    if task_adapter:
        task_manager_path = TASK_MANAGERS_DIR / f"{task_adapter}.md"
        if task_manager_path.exists():
            task_manager_content = task_manager_path.read_text()
            # Insert task manager guide at the beginning (after role section)
            content = content.replace(
                "### TASK MANAGEMENT API RATE LIMITS",
                f"{task_manager_content}\n\n### LEGACY CONTENT (Ignore if using {task_adapter.upper()})\n\n### TASK MANAGEMENT API RATE LIMITS",
                1
            )
    
    return content


def get_initializer_prompt(spec_file: Path | None = None, task_adapter: str | None = None) -> str:
    """Load the initializer prompt.

    Args:
        spec_file: Path to the spec file (relative to project dir)
        task_adapter: Task management adapter (linear, beads, github)
    """
    return load_prompt("initializer_prompt", spec_file, task_adapter)


def get_coding_prompt(spec_file: Path | None = None, task_adapter: str | None = None) -> str:
    """Load the coding agent prompt.

    Args:
        spec_file: Path to the spec file (relative to project dir)
        task_adapter: Task management adapter (linear, beads, github)
    """
    return load_prompt("coding_prompt", spec_file, task_adapter)


def get_audit_prompt(spec_file: Path | None = None, task_adapter: str | None = None) -> str:
    """Load the audit agent prompt.

    Args:
        spec_file: Path to the spec file (relative to project dir)
        task_adapter: Task management adapter (linear, beads, github)
    """
    return load_prompt("audit_prompt", spec_file, task_adapter)

"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"

# Default spec file name used in prompt templates
DEFAULT_SPEC_FILE = "app_spec.txt"


def load_prompt(name: str, spec_file: Path | None = None) -> str:
    """Load a prompt template from the prompts directory.

    Args:
        name: Name of the prompt template (without .md extension)
        spec_file: Optional spec file path to substitute in the template

    Returns:
        The prompt template with spec file name substituted
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"
    content = prompt_path.read_text()

    # Replace default spec file name with custom one if provided
    if spec_file is not None:
        content = content.replace(DEFAULT_SPEC_FILE, str(spec_file))

    return content


def get_initializer_prompt(spec_file: Path | None = None) -> str:
    """Load the initializer prompt.

    Args:
        spec_file: Path to the spec file (relative to project dir)
    """
    return load_prompt("initializer_prompt", spec_file)


def get_coding_prompt(spec_file: Path | None = None) -> str:
    """Load the coding agent prompt.

    Args:
        spec_file: Path to the spec file (relative to project dir)
    """
    return load_prompt("coding_prompt", spec_file)

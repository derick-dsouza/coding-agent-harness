#!/usr/bin/env python3
"""
Autonomous Coding Agent Demo
============================

A minimal harness demonstrating long-running autonomous coding with Claude.
This script implements the two-agent pattern (initializer + coding agent) and
incorporates all the strategies from the long-running agents guide.

Example Usage:
    python autonomous_agent_demo.py --project-dir ./claude_clone_demo
    python autonomous_agent_demo.py --project-dir ./claude_clone_demo --max-iterations 5
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from agent import run_autonomous_agent


# Configuration
# Model defaults - three separate models for different session types
# This balances quality (Opus for planning/audit) with cost/speed (Sonnet for implementation)
DEFAULT_INITIALIZER_MODEL = "claude-opus-4-5-20251101"
DEFAULT_CODING_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_AUDIT_MODEL = "claude-opus-4-5-20251101"  # Default: same as initializer
CONFIG_FILE = ".autocode-config.json"
DEFAULT_SPEC_FILE = "app_spec.txt"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent Demo - Long-running agent harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from project directory (uses app_spec.txt or .autocode-config.json)
  cd /path/to/my-project && python /path/to/autocode.py

  # Specify project directory explicitly
  python autocode.py --project-dir /path/to/my-project

  # Use a custom spec file - supports .txt, .md, .yaml, .yml, etc.
  python autocode.py --spec-file requirements.md
  python autocode.py --spec-file spec.yaml
  python autocode.py --spec-file PROJECT_SPEC.txt

  # Use separate models for initialization, coding, and audit (recommended)
  python autocode.py \\
    --initializer-model claude-opus-4-5-20251101 \\
    --coding-model claude-sonnet-4-5-20250929 \\
    --audit-model claude-opus-4-5-20251101

  # Use Sonnet for coding but cheaper Haiku for audits (if tasks are simple)
  python autocode.py \\
    --initializer-model claude-opus-4-5-20251101 \\
    --coding-model claude-sonnet-4-5-20250929 \\
    --audit-model claude-sonnet-4-5-20250929

  # Use a specific model for all sessions (init, coding, and audit)
  python autocode.py --model claude-opus-4-5-20251101

  # Limit iterations for testing
  python autocode.py --max-iterations 5

Config File (.autocode-config.json):
  {
    "spec_file": "my_spec.txt",
    "initializer_model": "claude-opus-4-5-20251101",
    "coding_model": "claude-sonnet-4-5-20250929",
    "audit_model": "claude-opus-4-5-20251101",
    "max_iterations": 10,
    "task_manager": "linear",
    "task_manager_config": {
      "linear": {
        "team_name": "YOUR_TEAM_NAME",
        "project_name": "YOUR_PROJECT_NAME"
      },
      "github": {
        "owner": "YOUR_GITHUB_ORG",
        "repo": "YOUR_REPO_NAME"
      },
      "beads": {
        "workspace": "YOUR_WORKSPACE_ID"
      }
    }
  }

  Or use single model for all sessions:
  {
    "spec_file": "my_spec.txt",
    "model": "claude-opus-4-5-20251101",
    "task_manager": "linear"
  }

  Priority: CLI arguments > config file > defaults

Environment Variables:
  CLAUDE_CODE_OAUTH_TOKEN    Claude Code OAuth token (required)
  LINEAR_API_KEY             Linear API key (required for Linear adapter)
  TASK_ADAPTER_TYPE          Task management adapter to use (default: linear)
                             Options: linear, github, beads
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory for the project (default: current directory). Must exist and contain the spec file.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--initializer-model",
        type=str,
        default=None,
        help=f"Claude model for initialization (default: {DEFAULT_INITIALIZER_MODEL})",
    )

    parser.add_argument(
        "--coding-model",
        type=str,
        default=None,
        help=f"Claude model for coding sessions (default: {DEFAULT_CODING_MODEL})",
    )

    parser.add_argument(
        "--audit-model",
        type=str,
        default=None,
        help=f"Claude model for audit sessions (default: {DEFAULT_AUDIT_MODEL})",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Claude model for all sessions (overrides --initializer-model, --coding-model, and --audit-model)",
    )

    parser.add_argument(
        "--spec-file",
        type=Path,
        default=None,
        help="Path to spec file relative to project directory - supports .txt, .md, .yaml, .yml, etc. (default: app_spec.txt)",
    )

    parser.add_argument(
        "--task-adapter",
        type=str,
        default=None,
        help="Task management adapter (default: linear). Options: linear, github, beads.",
    )

    return parser.parse_args()


def load_config(project_dir: Path) -> dict:
    """
    Load configuration from .autocode-config.json if it exists.

    Returns:
        Config dict (empty if file doesn't exist or is invalid)
    """
    config_path = project_dir / CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                print(f"Loaded config from {CONFIG_FILE}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read {CONFIG_FILE}: {e}")
    return {}


def resolve_config(
    args: argparse.Namespace,
    project_dir: Path,
    config: dict,
) -> dict | None:
    """
    Resolve final configuration with priority: CLI > config file > defaults.

    Returns:
        Dict with resolved values, or None if validation fails.
    """
    resolved = {}

    # Resolve models: CLI > config > defaults
    # If --model is specified, use it for all three (initializer, coding, audit)
    if args.model is not None:
        resolved["initializer_model"] = args.model
        resolved["coding_model"] = args.model
        resolved["audit_model"] = args.model
        print(f"Using single model for all sessions: {args.model}")
    else:
        # Resolve initializer model
        if args.initializer_model is not None:
            resolved["initializer_model"] = args.initializer_model
            print(f"Using initializer model from CLI: {args.initializer_model}")
        elif "initializer_model" in config:
            resolved["initializer_model"] = config["initializer_model"]
            print(f"Using initializer model from {CONFIG_FILE}: {config['initializer_model']}")
        elif "model" in config:
            # Fallback to single model from config
            resolved["initializer_model"] = config["model"]
            print(f"Using model from {CONFIG_FILE} for initializer: {config['model']}")
        else:
            resolved["initializer_model"] = DEFAULT_INITIALIZER_MODEL
            print(f"Using default initializer model: {DEFAULT_INITIALIZER_MODEL}")

        # Resolve coding model
        if args.coding_model is not None:
            resolved["coding_model"] = args.coding_model
            print(f"Using coding model from CLI: {args.coding_model}")
        elif "coding_model" in config:
            resolved["coding_model"] = config["coding_model"]
            print(f"Using coding model from {CONFIG_FILE}: {config['coding_model']}")
        elif "model" in config:
            # Fallback to single model from config
            resolved["coding_model"] = config["model"]
            print(f"Using model from {CONFIG_FILE} for coding: {config['model']}")
        else:
            resolved["coding_model"] = DEFAULT_CODING_MODEL
            print(f"Using default coding model: {DEFAULT_CODING_MODEL}")

        # Resolve audit model
        if args.audit_model is not None:
            resolved["audit_model"] = args.audit_model
            print(f"Using audit model from CLI: {args.audit_model}")
        elif "audit_model" in config:
            resolved["audit_model"] = config["audit_model"]
            print(f"Using audit model from {CONFIG_FILE}: {config['audit_model']}")
        elif "model" in config:
            # Fallback to single model from config
            resolved["audit_model"] = config["model"]
            print(f"Using model from {CONFIG_FILE} for audit: {config['model']}")
        else:
            resolved["audit_model"] = DEFAULT_AUDIT_MODEL
            print(f"Using default audit model: {DEFAULT_AUDIT_MODEL}")

    # Print model summary
    all_same = (
        resolved["initializer_model"] == resolved["coding_model"] == resolved["audit_model"]
    )
    
    if all_same:
        print(f"\n📊 Model Strategy: Single model for all sessions")
        print(f"   Model: {resolved['initializer_model']}")
    else:
        print(f"\n📊 Model Strategy: Multi-model optimization")
        print(f"   Initializer: {resolved['initializer_model']} (high-quality planning)")
        print(f"   Coding: {resolved['coding_model']} (cost-effective implementation)")
        print(f"   Audit: {resolved['audit_model']} (quality assurance)")

    # Resolve max_iterations: CLI > config > default (None = unlimited)
    if args.max_iterations is not None:
        resolved["max_iterations"] = args.max_iterations
        print(f"\nUsing max_iterations from CLI: {args.max_iterations}")
    elif "max_iterations" in config:
        resolved["max_iterations"] = config["max_iterations"]
        print(f"\nUsing max_iterations from {CONFIG_FILE}: {config['max_iterations']}")
    else:
        resolved["max_iterations"] = None
        print("\nUsing default max_iterations: unlimited")

    # Resolve spec_file: CLI > config > default (app_spec.txt)
    spec_file = None
    spec_source = None

    if args.spec_file is not None:
        spec_file = args.spec_file
        spec_source = "CLI"
    elif "spec_file" in config:
        spec_file = Path(config["spec_file"])
        spec_source = CONFIG_FILE
    else:
        spec_file = Path(DEFAULT_SPEC_FILE)
        spec_source = "default"

    # Validate spec file exists
    spec_path = project_dir / spec_file
    if spec_path.exists() and spec_path.is_file():
        resolved["spec_file"] = spec_file
        print(f"Using spec_file from {spec_source}: {spec_file}")
    else:
        print(f"Error: Spec file not found: {spec_path}")
        if spec_source == "CLI":
            print("  (specified via --spec-file)")
        elif spec_source == CONFIG_FILE:
            print(f"  (specified in {CONFIG_FILE})")
        else:
            print(f"\nNo spec file found. Create one of:")
            print(f"  1. {project_dir / DEFAULT_SPEC_FILE}")
            print(f"  2. {CONFIG_FILE} with 'spec_file' key")
            print(f"  3. Use --spec-file argument")
        return None

    # Resolve task_manager: CLI > config > env > default
    if args.task_adapter is not None:
        resolved["task_manager"] = args.task_adapter
        print(f"Using task_manager from CLI: {args.task_adapter}")
    elif "task_manager" in config:
        resolved["task_manager"] = config["task_manager"]
        print(f"Using task_manager from {CONFIG_FILE}: {config['task_manager']}")
    elif os.environ.get("TASK_ADAPTER_TYPE"):
        resolved["task_manager"] = os.environ["TASK_ADAPTER_TYPE"]
        print(f"Using task_manager from TASK_ADAPTER_TYPE env: {os.environ['TASK_ADAPTER_TYPE']}")
    else:
        resolved["task_manager"] = "linear"
        print(f"Using default task_manager: linear")

    # Resolve task_manager_config: config file only (not from CLI/env)
    resolved["task_manager_config"] = config.get("task_manager_config", {})

    return resolved


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Check for Claude Code OAuth token
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        print("Error: CLAUDE_CODE_OAUTH_TOKEN environment variable not set")
        print("\nRun 'claude setup-token' after installing the Claude Code CLI.")
        print("\nThen set it:")
        print("  export CLAUDE_CODE_OAUTH_TOKEN='your-token-here'")
        return

    # Resolve project directory
    project_dir = args.project_dir
    if not project_dir.is_absolute():
        # Use current working directory as base for relative paths
        project_dir = Path.cwd() / project_dir

    # FAIL FAST: Validate project directory exists
    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}")
        print("\nCreate the directory first:")
        print(f"  mkdir -p {project_dir}")
        return

    if not project_dir.is_dir():
        print(f"Error: Project path is not a directory: {project_dir}")
        return

    # Load config file
    config = load_config(project_dir)
    
    # First-time setup: Run interactive wizard if no config exists and no CLI args provided
    config_path = project_dir / CONFIG_FILE
    if not config_path.exists() and not any([
        args.spec_file,
        args.model,
        args.initializer_model,
        args.coding_model,
        args.audit_model,
        args.task_adapter,
        args.max_iterations
    ]):
        print("\n" + "="*70)
        print("🚀 FIRST-TIME SETUP DETECTED")
        print("="*70)
        print(f"\nNo configuration found in {project_dir}")
        print("Running interactive setup wizard...\n")
        
        # Import and run wizard
        from config_wizard import run_wizard
        run_wizard(project_dir)
        
        # Reload config after wizard
        config = load_config(project_dir)
        print("\n" + "="*70)
    
    # Resolve all settings
    resolved = resolve_config(args, project_dir, config)
    if resolved is None:
        return

    # Check for task manager-specific requirements
    task_manager = resolved.get("task_manager", "linear")
    task_manager_config = resolved.get("task_manager_config", {})
    
    if task_manager == "linear":
        # Check for Linear API key
        if not os.environ.get("LINEAR_API_KEY"):
            print("Error: LINEAR_API_KEY environment variable not set")
            print("\nLinear adapter requires an API key.")
            print("Get your API key from: https://linear.app/YOUR-TEAM/settings/api")
            print("\nThen set it:")
            print("  export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'")
            return
    elif task_manager == "github":
        # GitHub uses gh CLI, validate config has owner/repo
        github_config = task_manager_config.get("github", {})
        if not github_config.get("owner") or not github_config.get("repo"):
            print("Error: GitHub adapter requires 'owner' and 'repo' in task_manager_config")
            print(f"\nAdd to {CONFIG_FILE}:")
            print('  "task_manager_config": {')
            print('    "github": {')
            print('      "owner": "your-github-org",')
            print('      "repo": "your-repo-name"')
            print('    }')
            print('  }')
            return
        # Set environment variables for factory
        os.environ["GITHUB_OWNER"] = github_config["owner"]
        os.environ["GITHUB_REPO"] = github_config["repo"]
    elif task_manager == "beads":
        # BEADS uses bd CLI, workspace is optional
        beads_config = task_manager_config.get("beads", {})
        if beads_config.get("workspace"):
            os.environ["BEADS_WORKSPACE"] = beads_config["workspace"]
    else:
        print(f"Error: Unknown task manager: {task_manager}")
        print("Currently supported task managers: linear, github, beads")
        return

    # Set environment variable for task adapter (used by agent)
    os.environ["TASK_ADAPTER_TYPE"] = task_manager

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                spec_file=resolved["spec_file"],
                initializer_model=resolved["initializer_model"],
                coding_model=resolved["coding_model"],
                audit_model=resolved["audit_model"],
                max_iterations=resolved["max_iterations"],
            )
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run the same command again")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()

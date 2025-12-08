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
# Model defaults - using Opus for initialization, Sonnet for coding
# This balances quality (Opus for planning) with cost/speed (Sonnet for implementation)
DEFAULT_INITIALIZER_MODEL = "claude-opus-4-5-20251101"
DEFAULT_CODING_MODEL = "claude-sonnet-4-5-20250929"
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

  # Use a custom spec file (overrides .autocode-config.json)
  python autocode.py --spec-file requirements.txt

  # Use separate models for initialization and coding (recommended for cost savings)
  python autocode.py --initializer-model claude-opus-4-5-20251101 --coding-model claude-sonnet-4-5-20250929

  # Use a specific model for both initialization and coding
  python autocode.py --model claude-opus-4-5-20251101

  # Limit iterations for testing
  python autocode.py --max-iterations 5

Config File (.autocode-config.json):
  {
    "spec_file": "my_spec.txt",
    "initializer_model": "claude-opus-4-5-20251101",
    "coding_model": "claude-sonnet-4-5-20250929",
    "max_iterations": 10
  }

  Or use single model for both:
  {
    "spec_file": "my_spec.txt",
    "model": "claude-opus-4-5-20251101"
  }

  Priority: CLI arguments > config file > defaults

Environment Variables:
  CLAUDE_CODE_OAUTH_TOKEN    Claude Code OAuth token (required)
  LINEAR_API_KEY             Linear API key (required)
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
        "--model",
        type=str,
        default=None,
        help="Claude model for both initialization and coding (overrides --initializer-model and --coding-model)",
    )

    parser.add_argument(
        "--spec-file",
        type=Path,
        default=None,
        help="Path to spec file relative to project directory (default: from .autocode-config.json or app_spec.txt)",
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
    # If --model is specified, use it for both initializer and coding
    if args.model is not None:
        resolved["initializer_model"] = args.model
        resolved["coding_model"] = args.model
        print(f"Using single model for both: {args.model}")
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

    # Print model summary
    if resolved["initializer_model"] == resolved["coding_model"]:
        print(f"\n📊 Model Strategy: Single model for all sessions")
    else:
        print(f"\n📊 Model Strategy: Multi-model optimization")
        print(f"   Initializer: {resolved['initializer_model']} (high-quality planning)")
        print(f"   Coding: {resolved['coding_model']} (cost-effective implementation)")

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

    # Check for Linear API key
    if not os.environ.get("LINEAR_API_KEY"):
        print("Error: LINEAR_API_KEY environment variable not set")
        print("\nGet your API key from: https://linear.app/YOUR-TEAM/settings/api")
        print("\nThen set it:")
        print("  export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'")
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

    # Load config file and resolve all settings
    config = load_config(project_dir)
    resolved = resolve_config(args, project_dir, config)
    if resolved is None:
        return

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                spec_file=resolved["spec_file"],
                initializer_model=resolved["initializer_model"],
                coding_model=resolved["coding_model"],
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

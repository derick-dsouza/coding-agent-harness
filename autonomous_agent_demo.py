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
import os
from pathlib import Path

from agent import run_autonomous_agent


# Configuration
# Using Claude Opus 4.5 as default for best coding and agentic performance
# See: https://www.anthropic.com/news/claude-opus-4-5
DEFAULT_MODEL = "claude-opus-4-5-20251101"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent Demo - Long-running agent harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on a project with app_spec.txt in it
  python autonomous_agent_demo.py --project-dir /path/to/my-project

  # Use a custom spec file name
  python autonomous_agent_demo.py --project-dir /path/to/my-project --spec-file requirements.txt

  # Use a specific model
  python autonomous_agent_demo.py --project-dir /path/to/my-project --model claude-sonnet-4-5-20250929

  # Limit iterations for testing
  python autonomous_agent_demo.py --project-dir /path/to/my-project --max-iterations 5

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
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--spec-file",
        type=Path,
        default=Path("app_spec.txt"),
        help="Path to spec file relative to project directory (default: app_spec.txt)",
    )

    return parser.parse_args()


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

    # FAIL FAST: Validate spec file exists
    spec_file = project_dir / args.spec_file
    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        print("\nCreate a spec file with your project requirements.")
        print("See prompts/app_spec.txt for an example format.")
        return

    if not spec_file.is_file():
        print(f"Error: Spec path is not a file: {spec_file}")
        return

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                spec_file=args.spec_file,
                model=args.model,
                max_iterations=args.max_iterations,
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

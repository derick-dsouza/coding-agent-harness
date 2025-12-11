#!/usr/bin/env python3
"""
Spec Change Detection Script
==============================

Runs the spec change detector agent to identify new requirements
in app_spec.txt and create corresponding issues in the task management system.

Usage:
    python detect_spec_changes.py --project-dir ./my_project
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from client import create_client


async def run_spec_change_detection(
    project_dir: Path,
    model: str = "claude-opus-4-20250514",
    task_adapter: str = "linear",
) -> None:
    """
    Run the spec change detector agent.
    
    Args:
        project_dir: Directory containing the project (can be harness root or generated project)
        model: Claude model to use
        task_adapter: Task management adapter (linear, beads, github)
        model: Claude model to use (default: Opus for analysis quality)
    """
    print("\n" + "=" * 70)
    print("  SPEC CHANGE DETECTION")
    print("=" * 70)
    print(f"\nWorking directory: {project_dir}")
    print(f"Model: {model}\n")
    
    # Find the project state file
    task_state_file = project_dir / ".task_project.json"
    linear_state_file = project_dir / ".linear_project.json"
    
    if task_state_file.exists():
        state_file = task_state_file
    elif linear_state_file.exists():
        state_file = linear_state_file
    else:
        print("❌ Error: Project not initialized")
        print("   Expected .task_project.json or .linear_project.json in project directory")
        sys.exit(1)
    
    print(f"   State file: {state_file.name}")
    
    # Find the spec file in the working directory
    spec_file = None
    for filename in ["app_spec.txt", "app_spec.md", "app_spec.yaml", "app_spec.yml"]:
        candidate = project_dir / filename
        if candidate.exists():
            spec_file = candidate
            break
    
    if not spec_file:
        print(f"❌ Error: No app_spec file found in {project_dir}")
        print("   Looking for: app_spec.txt, app_spec.md, app_spec.yaml, app_spec.yml")
        sys.exit(1)
    
    print(f"   Spec file: {spec_file.name}\n")
    
    # Load the spec change prompt template
    prompt_file = Path(__file__).parent / "prompts" / "spec_change_prompt.md"
    
    try:
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Spec change prompt not found at {prompt_file}")
        sys.exit(1)
    
    # Read the spec content
    with open(spec_file, "r") as f:
        spec_content = f.read()
    
    # Create the full prompt
    prompt = f"{prompt_template}\n\n---\n\n## APP SPECIFICATION\n\n{spec_content}"
    
    # Create client
    client = create_client(project_dir, model, task_adapter)
    
    print("Analyzing spec for changes...\n")
    print("-" * 70)
    
    # Run the agent
    async with client:
        await client.query(prompt)
        
        # Collect and display response
        async for msg in client.receive_response():
            msg_type = type(msg).__name__
            
            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    
                    if block_type == "TextBlock" and hasattr(block, "text"):
                        print(block.text, end="", flush=True)
                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        print(f"\n[Tool: {block.name}]", flush=True)
            
            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    
                    if block_type == "ToolResultBlock":
                        is_error = getattr(block, "is_error", False)
                        if is_error:
                            result_str = str(getattr(block, "content", ""))[:500]
                            print(f"   [Error] {result_str}", flush=True)
                        else:
                            print("   [Done]", flush=True)
    
    print("\n" + "-" * 70)
    print("\n✅ Spec change detection complete!")
    print("\nNext steps:")
    print("  1. Check Linear for newly created issues labeled 'spec-change'")
    print("  2. Run the coding agent to implement the changes")
    print("  3. Or manually adjust issue priorities in Linear\n")


def main():
    """Parse arguments and run spec change detection."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Detect changes in app_spec.txt and create new issues"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./autonomous_demo_project"),
        help="Project directory (default: ./autonomous_demo_project)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-opus-4-20250514",
        help="Claude model to use (default: claude-opus-4-20250514)",
    )
    parser.add_argument(
        "--task-adapter",
        type=str,
        default="linear",
        help="Task adapter to use (linear, beads, github) (default: linear)",
    )
    
    args = parser.parse_args()
    
    # Verify project directory exists
    if not args.project_dir.exists():
        print(f"❌ Error: Project directory does not exist: {args.project_dir}")
        sys.exit(1)
    
    # Run async detection
    asyncio.run(run_spec_change_detection(args.project_dir, args.model, args.task_adapter))


if __name__ == "__main__":
    main()

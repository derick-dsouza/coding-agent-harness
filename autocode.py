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
from typing import Any

from agent import run_autonomous_agent
from client import (
    DEFAULTS,
    DEFAULT_AGENT_SDK_KEY,
    get_api_key_env_for_sdk,
    get_default_model_for_sdk,
)


# Configuration defaults pulled from autocode-defaults.json
DEFAULT_INITIALIZER_MODEL = get_default_model_for_sdk(DEFAULT_AGENT_SDK_KEY, "initializer") or "claude-opus-4-5-20251101"
DEFAULT_CODING_MODEL = get_default_model_for_sdk(DEFAULT_AGENT_SDK_KEY, "coding") or "claude-sonnet-4-5-20250929"
DEFAULT_AUDIT_MODEL = get_default_model_for_sdk(DEFAULT_AGENT_SDK_KEY, "audit") or "claude-opus-4-5-20251101"
CONFIG_FILE = ".autocode-config.json"
DEFAULT_SPEC_FILE = "app_spec.txt"

# Get API key environment variable name from defaults
API_KEY_ENV_VAR = get_api_key_env_for_sdk(DEFAULT_AGENT_SDK_KEY) or "CLAUDE_CODE_OAUTH_TOKEN"


def resolve_model_for_sdk(raw_model: str | None, sdk_key: str, role: str, default_fallback: str) -> str:
    """
    Normalize a model name for a given SDK and role.

    Supports aliases defined in autocode-defaults.json, falls back to SDK defaults,
    then to the provided default_fallback.
    """
    model_map = DEFAULTS.get("agent_sdks", {}).get(sdk_key, {}).get("models", {}) or {}
    if raw_model in model_map:
        return model_map[raw_model]
    if raw_model:
        return raw_model

    sdk_default = get_default_model_for_sdk(sdk_key, role)
    if sdk_default:
        return sdk_default

    return default_fallback


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
  {{{{
    "spec_file": "my_spec.txt",
    "initializer_model": "claude-opus-4-5-20251101",
    "coding_model": "claude-sonnet-4-5-20250929",
    "audit_model": "claude-opus-4-5-20251101",
    "max_iterations": 10,
    "task_manager": "linear",
    "task_manager_config": {{{{
      "linear": {{{{
        "team_name": "YOUR_TEAM_NAME",
        "project_name": "YOUR_PROJECT_NAME"
      }}}},
      "github": {{{{
        "owner": "YOUR_GITHUB_ORG",
        "repo": "YOUR_REPO_NAME"
      }}}},
      "beads": {{{{
        "workspace": "YOUR_WORKSPACE_ID"
      }}}}
    }}}}
  }}}}

  Or use single model for all sessions:
  {{{{
    "spec_file": "my_spec.txt",
    "model": "claude-opus-4-5-20251101",
    "task_manager": "linear"
  }}}}

  Priority: CLI arguments > config file > defaults

Environment Variables:
  {api_key_var}    Default agent SDK token (for {default_agent_sdk}; override per SDK as needed)
  AGENT_SDK_SIMULATE        Force simulation for CLI SDKs (optional)
  LINEAR_API_KEY            Linear API key (required for Linear adapter)
  TASK_ADAPTER_TYPE         Task management adapter to use (default: linear)
                            Options: linear, github, beads
        """.format(api_key_var=API_KEY_ENV_VAR, default_agent_sdk=DEFAULT_AGENT_SDK_KEY),
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
        "--agent-sdk",
        type=str,
        default=None,
        help="Agent SDK to use for all sessions (default from autocode-defaults.json).",
    )
    parser.add_argument(
        "--initializer-sdk",
        type=str,
        default=None,
        help="Agent SDK override for initializer session (defaults to --agent-sdk).",
    )
    parser.add_argument(
        "--coding-sdk",
        type=str,
        default=None,
        help="Agent SDK override for coding sessions (defaults to --agent-sdk).",
    )
    parser.add_argument(
        "--audit-sdk",
        type=str,
        default=None,
        help="Agent SDK override for audit sessions (defaults to --agent-sdk).",
    )
    parser.add_argument(
        "--simulate-agent-sdk",
        action="store_true",
        help="Force simulation mode for CLI-based SDKs (useful for local testing).",
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

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output including JSON dumps and detailed debug information",
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
    resolved: dict[str, Any] = {}

    # Resolve agent SDK selection
    default_sdk = DEFAULTS.get("defaults", {}).get("agent_sdk", DEFAULT_AGENT_SDK_KEY)
    base_sdk = args.agent_sdk or config.get("agent_sdk") or default_sdk
    initializer_sdk = args.initializer_sdk or config.get("initializer_agent_sdk") or base_sdk
    coding_sdk = args.coding_sdk or config.get("coding_agent_sdk") or base_sdk
    audit_sdk = args.audit_sdk or config.get("audit_agent_sdk") or base_sdk

    resolved["agent_sdks"] = {
        "default": base_sdk,
        "initializer": initializer_sdk,
        "coding": coding_sdk,
        "audit": audit_sdk,
    }
    resolved["simulate_agent_sdk"] = bool(args.simulate_agent_sdk or config.get("simulate_agent_sdk"))

    # Resolve models: CLI > config > defaults (per SDK)
    unified_model = args.model or config.get("model")
    initializer_model_raw = args.initializer_model or config.get("initializer_model") or unified_model
    coding_model_raw = args.coding_model or config.get("coding_model") or unified_model
    audit_model_raw = args.audit_model or config.get("audit_model") or unified_model

    resolved["initializer_model"] = resolve_model_for_sdk(
        initializer_model_raw, initializer_sdk, "initializer", DEFAULT_INITIALIZER_MODEL
    )
    resolved["coding_model"] = resolve_model_for_sdk(
        coding_model_raw, coding_sdk, "coding", DEFAULT_CODING_MODEL
    )
    resolved["audit_model"] = resolve_model_for_sdk(
        audit_model_raw, audit_sdk, "audit", DEFAULT_AUDIT_MODEL
    )

    print(f"\n📊 Agent SDK Strategy")
    print(f"   Initializer: {initializer_sdk} (model: {resolved['initializer_model']})")
    print(f"   Coding:      {coding_sdk} (model: {resolved['coding_model']})")
    print(f"   Audit:       {audit_sdk} (model: {resolved['audit_model']})")
    if resolved["simulate_agent_sdk"]:
        print("   Simulation:  Enabled for CLI agents (AGENT_SDK_SIMULATE or --simulate-agent-sdk)")

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

    # Validate spec file exists and is not empty
    spec_path = project_dir / spec_file
    if spec_path.exists() and spec_path.is_file():
        # Check if spec file is empty or only whitespace
        spec_content = spec_path.read_text().strip()
        if not spec_content:
            print(f"\n⚠️  WARNING: Spec file is empty: {spec_path}")
            print("\nThe spec file contains no requirements. Options:")
            print("  1. Add requirements to the spec file and run again")
            print("  2. Continue anyway (agent will only work on existing open issues)")

            # Check if there are existing open issues
            task_project_path = project_dir / ".task_project.json"
            if task_project_path.exists():
                with open(task_project_path, encoding='utf-8') as f:
                    task_data = json.load(f)
                    total_issues = task_data.get("total_issues_created", 0)
                    if total_issues > 0:
                        print(f"\n  📋 Found {total_issues} existing issues in task manager")
                        print("     Agent can work on open issues without a spec file")

            response = input("\nContinue with empty spec file? (y/n): ").strip().lower()
            if response != 'y':
                print("\nExiting. Please add requirements to the spec file.")
                return None

            print(f"\n✅ Continuing with empty spec file")

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
    elif "task_adapter" in config or "task_manager" in config:
        # Support both 'task_adapter' (new) and 'task_manager' (legacy) keys
        task_adapter = config.get("task_adapter") or config.get("task_manager")
        resolved["task_manager"] = task_adapter
        print(f"Using task_manager from {CONFIG_FILE}: {task_adapter}")
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
    
    # First-time setup: Check if this is a fresh project
    config_path = project_dir / CONFIG_FILE
    task_project_path = project_dir / ".task_project.json"
    
    # Check for task manager mismatch
    if config_path.exists() and task_project_path.exists():
        try:
            with open(task_project_path, encoding='utf-8') as f:
                task_data = json.load(f)
            
            config_adapter = config.get("task_adapter", "linear")
            
            # Detect mismatch: Linear IDs in file but BEADS/GitHub configured
            has_linear_ids = "team_id" in task_data or "project_id" in task_data
            
            if config_adapter == "beads" and has_linear_ids:
                print("\n" + "="*70)
                print("  ⚠️  TASK MANAGER MISMATCH DETECTED")
                print("="*70)
                print(f"\nConfigured adapter: BEADS")
                print(f"Found Linear project data in .task_project.json")
                print("\nThe .task_project.json file contains Linear project data,")
                print("but your config specifies BEADS as the task manager.")
                print("\nRecommended action:")
                print(f"  rm {task_project_path}")
                print(f"  # Then run autocode again to initialize with BEADS")
                return
        except Exception:
            # Ignore JSON parsing errors
            pass
    
    is_first_run = not config_path.exists() and not task_project_path.exists()
    
    # Run interactive wizard if first run and no CLI args provided
    if is_first_run and not any([
        args.spec_file,
        args.model,
        args.initializer_model,
        args.coding_model,
        args.audit_model,
        args.agent_sdk,
        args.initializer_sdk,
        args.coding_sdk,
        args.audit_sdk,
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
    
    # If first run and spec file not specified, prompt for it
    elif is_first_run and args.spec_file is None and "spec_file" not in config:
        print("\n" + "="*70)
        print("📄 SPEC FILE REQUIRED")
        print("="*70)
        print(f"\nNo spec file specified for first-time setup.")
        print("\nSupported formats: .txt, .md, .yaml, .yml")
        print(f"Default: {DEFAULT_SPEC_FILE}")
        
        while True:
            spec_input = input(f"\nEnter spec file name (or press Enter for '{DEFAULT_SPEC_FILE}'): ").strip()
            
            if not spec_input:
                spec_input = DEFAULT_SPEC_FILE
            
            spec_path = project_dir / spec_input
            if spec_path.exists() and spec_path.is_file():
                # Save to config for future runs
                config["spec_file"] = spec_input
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"\n✅ Using spec file: {spec_input}")
                print(f"   Saved to {CONFIG_FILE}")
                break
            else:
                print(f"\n❌ File not found: {spec_path}")
                print("   Please create the file or enter a different name.")
                retry = input("   Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("\nExiting. Please create a spec file and run again.")
                    return
        
        print("="*70 + "\n")
    
    # Resolve all settings
    resolved = resolve_config(args, project_dir, config)
    if resolved is None:
        return

    # Validate agent SDK credentials (skip CLI agents when simulation is enabled)
    selected_sdks = {
        resolved["agent_sdks"]["initializer"],
        resolved["agent_sdks"]["coding"],
        resolved["agent_sdks"]["audit"],
    }
    missing_envs = []
    for sdk_key in selected_sdks:
        env_var = get_api_key_env_for_sdk(sdk_key)
        if not env_var:
            continue
        if sdk_key != "claude-agent-sdk" and resolved.get("simulate_agent_sdk"):
            continue
        if not os.environ.get(env_var):
            missing_envs.append((sdk_key, env_var))

    if missing_envs:
        print("Error: Missing environment variables for selected agent SDKs:")
        for sdk_key, env_var in missing_envs:
            print(f"  - {sdk_key}: {env_var}")
        print("\nSet the required variables or enable --simulate-agent-sdk for CLI agents.")
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
                agent_sdks=resolved["agent_sdks"],
                simulate_agent_sdk=resolved["simulate_agent_sdk"],
                task_adapter=task_manager,
                max_iterations=resolved["max_iterations"],
                verbose=args.verbose,
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

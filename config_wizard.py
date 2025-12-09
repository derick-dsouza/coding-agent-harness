#!/usr/bin/env python3
"""
Interactive configuration wizard for first-time setup.
Prompts user for task adapter and model preferences.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def load_defaults() -> dict[str, Any]:
    """Load defaults from autocode-defaults.json"""
    defaults_path = Path(__file__).parent / "autocode-defaults.json"
    with open(defaults_path) as f:
        return json.load(f)


def prompt_choice(prompt: str, choices: list[str], default: str | None = None) -> str:
    """Prompt user to select from a list of choices"""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " (default)" if default and choice == default else ""
        print(f"  {i}. {choice}{marker}")
    
    while True:
        response = input(f"\nEnter choice [1-{len(choices)}]" + (f" (default: {choices.index(default) + 1}): " if default else ": "))
        
        # Handle default
        if not response.strip() and default:
            return default
        
        # Validate input
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        
        print(f"Invalid choice. Please enter a number between 1 and {len(choices)}")


def check_cli_available(command: str) -> bool:
    """Check if a CLI command is available"""
    return shutil.which(command) is not None


def prompt_task_adapter(defaults: dict) -> tuple[str, dict]:
    """Prompt user to select task adapter and configure it"""
    adapters = defaults["task_adapters"]
    default_adapter = defaults["defaults"]["task_adapter"]
    
    # Build choices with availability info
    choices = []
    choice_keys = []
    
    print("\n" + "="*70)
    print("TASK MANAGEMENT ADAPTER SELECTION")
    print("="*70)
    
    for key, adapter in adapters.items():
        name = adapter["name"]
        desc = adapter["description"]
        
        # Check availability
        available = True
        status = "✓ Available"
        
        if adapter["cli_command"]:
            if not check_cli_available(adapter["cli_command"]):
                available = False
                status = f"✗ Not available ('{adapter['cli_command']}' not found in PATH)"
        
        if adapter["requires_api_key"]:
            # Check for API key in environment
            key_var = f"{key.upper()}_API_KEY"
            if not os.getenv(key_var):
                status += f" (⚠ {key_var} not set)"
        
        choice_label = f"{name} - {desc} [{status}]"
        choices.append(choice_label)
        choice_keys.append(key)
    
    # Prompt for selection
    selected_idx = choices.index([c for c in choices if choice_keys[choices.index(c)] == default_adapter][0]) if default_adapter in choice_keys else 0
    selected_choice = prompt_choice(
        "Select task management adapter:",
        choices,
        choices[selected_idx]
    )
    
    selected_key = choice_keys[choices.index(selected_choice)]
    adapter_config = {}
    
    # Prompt for adapter-specific configuration
    print(f"\n{adapters[selected_key]['name']} Configuration:")
    print("-" * 70)
    
    if selected_key == "linear":
        team_name = input("Enter Linear team name: ").strip()
        project_name = input("Enter Linear project name: ").strip()
        adapter_config = {
            "team_name": team_name,
            "project_name": project_name
        }
        
        # Remind about API key
        if not os.getenv("LINEAR_API_KEY"):
            print("\n⚠ Warning: LINEAR_API_KEY environment variable is not set.")
            print("  You'll need to set it before running autocode.")
    
    elif selected_key == "github":
        owner = input("Enter GitHub organization/owner: ").strip()
        repo = input("Enter repository name: ").strip()
        adapter_config = {
            "owner": owner,
            "repo": repo
        }
        
        # Check gh CLI is authenticated
        if check_cli_available("gh"):
            print("\n✓ GitHub CLI (gh) is installed.")
            print("  Make sure you're authenticated: gh auth login")
    
    elif selected_key == "beads":
        workspace = input("Enter BEADS workspace ID (default: default): ").strip() or "default"
        adapter_config = {
            "workspace": workspace
        }
        
        # Check bd CLI
        if check_cli_available("bd"):
            print("\n✓ BEADS CLI (bd) is installed.")
    
    return selected_key, adapter_config


def prompt_models(defaults: dict) -> tuple[str, str, str]:
    """Prompt user to select models for initializer, coding, and audit"""
    models = defaults["models"]["claude"]
    model_choices = list(models.keys())
    
    print("\n" + "="*70)
    print("MODEL SELECTION")
    print("="*70)
    print("\nClaude models available:")
    for name, model_id in models.items():
        print(f"  • {name.capitalize()}: {model_id}")
    
    print("\nRecommended configuration:")
    print("  • Initializer: Opus (high-quality planning and task breakdown)")
    print("  • Coding: Sonnet (balanced quality and speed for implementation)")
    print("  • Audit: Opus (thorough review and quality assurance)")
    
    # Prompt for each model type
    default_init = defaults["defaults"]["initializer_model"]
    default_coding = defaults["defaults"]["coding_model"]
    default_audit = defaults["defaults"]["audit_model"]
    
    initializer = prompt_choice(
        "\nSelect initializer model (task planning and breakdown):",
        model_choices,
        default_init
    )
    
    coding = prompt_choice(
        "\nSelect coding model (implementation):",
        model_choices,
        default_coding
    )
    
    audit = prompt_choice(
        "\nSelect audit model (quality review):",
        model_choices,
        default_audit
    )
    
    return initializer, coding, audit


def create_config(project_dir: Path) -> dict:
    """Run interactive configuration wizard"""
    print("\n" + "="*70)
    print("AUTOCODE FIRST-TIME SETUP")
    print("="*70)
    print(f"\nProject directory: {project_dir.absolute()}")
    print("\nThis wizard will help you configure autocode for this project.")
    
    # Load defaults
    defaults = load_defaults()
    
    # Prompt for task adapter
    task_adapter, adapter_config = prompt_task_adapter(defaults)
    
    # Prompt for models
    initializer, coding, audit = prompt_models(defaults)
    
    # Map model names to actual model IDs
    model_map = defaults["models"]["claude"]
    
    # Build configuration
    config = {
        "agent_sdk": defaults["agent_sdk"],
        "task_adapter": task_adapter,
        "task_adapter_config": {
            task_adapter: adapter_config
        },
        "initializer_model": model_map[initializer],
        "coding_model": model_map[coding],
        "audit_model": model_map[audit],
        "spec_file": "app_spec.txt",
        "max_iterations": defaults["defaults"]["max_iterations"]
    }
    
    # Show summary
    print("\n" + "="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(json.dumps(config, indent=2))
    
    # Confirm
    confirm = input("\nSave this configuration? [Y/n]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes']:
        print("Configuration cancelled.")
        sys.exit(0)
    
    return config


def save_config(config: dict, project_dir: Path) -> None:
    """Save configuration to .autocode-config.json"""
    config_path = project_dir / ".autocode-config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, indent=2, fp=f)
        f.write('\n')  # Add trailing newline
    
    print(f"\n✓ Configuration saved to {config_path}")
    print("\nYou can edit this file directly or re-run the wizard anytime.")
    print("\nNext steps:")
    print("  1. Create your app_spec.txt file (or use --spec-file to specify another)")
    print("  2. Run: python autocode.py")


def run_wizard(project_dir: Path) -> None:
    """Run the interactive configuration wizard"""
    config = create_config(project_dir)
    save_config(config, project_dir)


if __name__ == "__main__":
    # For testing
    run_wizard(Path("."))

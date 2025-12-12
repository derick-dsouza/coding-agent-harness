#!/usr/bin/env python3
"""
Issue Claim Helper for Multi-Worker Coordination
================================================

Simple CLI tool for agents to claim/release issues and check conflicts.
Works with the WorkerCoordinator system.

Usage (from project directory):
    python3 /path/to/harness/claim_issue.py claim ISSUE_ID [FILE1 FILE2 ...]
    python3 /path/to/harness/claim_issue.py release ISSUE_ID
    python3 /path/to/harness/claim_issue.py check ISSUE_ID
    python3 /path/to/harness/claim_issue.py list
    python3 /path/to/harness/claim_issue.py files FILE1 [FILE2 ...]

The script automatically finds the project directory by looking for
.autocode-workers, .beads, .task_project.json, or .git markers.
"""

import sys
import json
from pathlib import Path

# Add the directory containing this script to the path so we can import worker_coordinator
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from worker_coordinator import (
    WorkerCoordinator,
    check_issue_available,
    list_claimed_issues,
    check_file_conflicts,
    get_files_locked_by_issue,
)


def get_project_dir() -> Path:
    """Find the project directory (where .autocode-workers is or should be)."""
    # Start from current directory and look for markers
    cwd = Path.cwd()
    
    # Check for .autocode-workers, .beads, or .task_project.json
    markers = ['.autocode-workers', '.beads', '.task_project.json', '.git']
    
    current = cwd
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    # Default to cwd if no marker found
    return cwd


def cmd_claim(issue_id: str, files: list[str] = None):
    """Claim an issue and optionally its files."""
    project_dir = get_project_dir()
    
    # Check availability first
    if not check_issue_available(project_dir, issue_id):
        print(f"ERROR: Issue {issue_id} is already claimed by another worker")
        sys.exit(1)
    
    # Check file conflicts
    if files:
        conflicts = check_file_conflicts(project_dir, files)
        if conflicts:
            print(f"ERROR: File conflicts detected:")
            for f in conflicts:
                print(f"  - {f}")
            sys.exit(1)
    
    # Create coordinator and claim
    coord = WorkerCoordinator(project_dir)
    coord.register()
    
    if files:
        success, conflicts = coord.try_claim_issue_with_files(issue_id, files)
        if not success:
            print(f"ERROR: Failed to claim issue {issue_id}")
            if conflicts:
                print(f"Conflicting files: {conflicts}")
            coord.cleanup()
            sys.exit(1)
    else:
        if not coord.try_claim_issue(issue_id):
            print(f"ERROR: Failed to claim issue {issue_id}")
            coord.cleanup()
            sys.exit(1)
    
    print(f"OK: Claimed issue {issue_id}")
    if files:
        print(f"    Files: {', '.join(files)}")
    
    # Don't cleanup - keep the claim active
    # The heartbeat loop should be running in the main agent process


def cmd_release(issue_id: str):
    """Release a claim on an issue."""
    project_dir = get_project_dir()
    coord = WorkerCoordinator(project_dir)
    coord.register()
    coord.release_claim(issue_id)
    coord.cleanup()
    print(f"OK: Released claim on {issue_id}")


def cmd_check(issue_id: str):
    """Check if an issue is available."""
    project_dir = get_project_dir()
    
    if check_issue_available(project_dir, issue_id):
        print(f"AVAILABLE: Issue {issue_id} can be claimed")
        sys.exit(0)
    else:
        print(f"CLAIMED: Issue {issue_id} is claimed by another worker")
        # Show who has it
        files = get_files_locked_by_issue(project_dir, issue_id)
        if files:
            print(f"  Files locked: {', '.join(files)}")
        sys.exit(1)


def cmd_list():
    """List all currently claimed issues."""
    project_dir = get_project_dir()
    claimed = list_claimed_issues(project_dir)
    
    if not claimed:
        print("No issues currently claimed")
    else:
        print(f"Claimed issues ({len(claimed)}):")
        for issue_id in claimed:
            files = get_files_locked_by_issue(project_dir, issue_id)
            if files:
                print(f"  {issue_id}: {', '.join(files)}")
            else:
                print(f"  {issue_id}")


def cmd_files(files: list[str]):
    """Check if files have conflicts."""
    project_dir = get_project_dir()
    conflicts = check_file_conflicts(project_dir, files)
    
    if not conflicts:
        print("OK: No file conflicts")
        sys.exit(0)
    else:
        print(f"CONFLICTS: {len(conflicts)} file(s) locked by other workers:")
        for f in conflicts:
            print(f"  - {f}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'claim':
        if len(sys.argv) < 3:
            print("Usage: claim_issue.py claim ISSUE_ID [FILE1 FILE2 ...]")
            sys.exit(1)
        issue_id = sys.argv[2]
        files = sys.argv[3:] if len(sys.argv) > 3 else None
        cmd_claim(issue_id, files)
    
    elif cmd == 'release':
        if len(sys.argv) < 3:
            print("Usage: claim_issue.py release ISSUE_ID")
            sys.exit(1)
        cmd_release(sys.argv[2])
    
    elif cmd == 'check':
        if len(sys.argv) < 3:
            print("Usage: claim_issue.py check ISSUE_ID")
            sys.exit(1)
        cmd_check(sys.argv[2])
    
    elif cmd == 'list':
        cmd_list()
    
    elif cmd == 'files':
        if len(sys.argv) < 3:
            print("Usage: claim_issue.py files FILE1 [FILE2 ...]")
            sys.exit(1)
        cmd_files(sys.argv[2:])
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
Supports multiple task management backends (Linear, Jira, GitHub) via adapter pattern.
"""

import asyncio
import os
import re
import signal
import sys
import select
import termios
import tty
import time
from pathlib import Path
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient

# Global shutdown flag
_shutdown_requested = False
# Global worker coordinator reference for signal handler cleanup
_worker_coordinator = None

from client import create_client
from progress import print_session_header, print_progress_summary, is_task_initialized
from prompts import get_initializer_prompt, get_coding_prompt, get_audit_prompt
from linear_tracker import init_tracker, track_linear_call
from linear_cache import init_cache
from linear_cache_helpers import (
    invalidate_cache_for_operations,
    print_combined_stats,
    get_project_id_from_state
)
from worker_coordinator import WorkerCoordinator


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3

# Audit system configuration
AUDIT_INTERVAL = 5  # Trigger audit every 5 completed features (was 10)
AUDIT_LABEL_AWAITING = "awaiting-audit"
AUDIT_LABEL_AUDITED = "audited"


def _signal_handler(signum, frame):
    """
    Handle Ctrl+C (SIGINT) for graceful shutdown.
    Cleans up worker coordinator claims/locks before exiting.
    """
    global _shutdown_requested, _worker_coordinator
    
    print("\n\n🛑 Ctrl+C received. Shutting down gracefully...")
    _shutdown_requested = True
    
    # Clean up worker coordinator if it exists
    if _worker_coordinator is not None:
        try:
            print("   Cleaning up worker claims and locks...")
            _worker_coordinator.cleanup()
            print("   ✅ Cleanup complete")
        except Exception as e:
            print(f"   ⚠️  Cleanup error: {e}")
    
    sys.exit(0)


def check_for_quit_key() -> bool:
    """
    Non-blocking check if 'q' or 'Q' was pressed.
    Returns True if quit was requested.
    """
    global _shutdown_requested
    if _shutdown_requested:
        return True
    
    try:
        # Check if stdin has data available (non-blocking)
        if sys.stdin.isatty():
            # Save terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                # Set terminal to raw mode for single char input
                tty.setcbreak(sys.stdin.fileno())
                # Check if input is available
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == 'q':
                        _shutdown_requested = True
                        return True
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except Exception:
        # If terminal operations fail, just continue
        pass
    
    return False


async def interruptible_sleep(seconds: float, message: str = "") -> bool:
    """
    Sleep for the specified duration, but check for 'q' keypress every 0.5s.
    
    Args:
        seconds: Total seconds to sleep
        message: Optional message to display (e.g., "Press 'q' to quit")
    
    Returns:
        True if sleep completed normally, False if interrupted by 'q'
    """
    global _shutdown_requested
    
    if message:
        print(message, flush=True)
    
    intervals = int(seconds / 0.5)
    remainder = seconds - (intervals * 0.5)
    
    for _ in range(intervals):
        if check_for_quit_key():
            return False
        await asyncio.sleep(0.5)
    
    if remainder > 0:
        if check_for_quit_key():
            return False
        await asyncio.sleep(remainder)
    
    return not _shutdown_requested

# Claude API rate limiting configuration
CLAUDE_RATE_LIMIT_BASE_WAIT_SECONDS = 60
CLAUDE_RATE_LIMIT_MAX_WAIT_SECONDS = 900
CLAUDE_RATE_LIMIT_BACKOFF_MULTIPLIER = 2

# Claude API smart wait thresholds (in minutes)
CLAUDE_WAIT_THRESHOLD_AUTO = 30  # ≤30 min: auto-wait with countdown
CLAUDE_WAIT_THRESHOLD_OPTIONAL = 120  # ≤2 hours: wait but allow Ctrl+C exit
# >2 hours: auto-exit with resume instructions

# Linear API rate limiting configuration
LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS = 3600  # Max 1 hour (Linear's limit)
LINEAR_WAIT_THRESHOLD_AUTO = 60  # ≤60 min: auto-wait (Linear max is 1 hour)


class ClaudeRateLimitHandler:
    """
    Handles Claude API rate limit detection with smart wait/exit decisions.
    
    Claude has hourly, weekly, and monthly limits that can require waiting
    from minutes to days. This handler intelligently decides when to wait
    vs. when to exit and resume later.
    """

    def __init__(self):
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = 0

    def is_claude_rate_limit(self, content: str) -> bool:
        """Check if content indicates a Claude API rate limit."""
        content_lower = content.lower()
        # Claude-specific patterns
        return (
            "limit reached" in content_lower
            or ("resets" in content_lower and ("am" in content_lower or "pm" in content_lower))
        )

    def extract_reset_time(self, content: str) -> Optional[int]:
        """Try to extract reset time from error message (in seconds)."""
        patterns = [
            r"retry.{0,10}after.{0,5}(\d+)\s*(?:second|sec|s)",
            r"reset.{0,10}in.{0,5}(\d+)\s*(?:second|sec|s)",
            r"wait.{0,10}(\d+)\s*(?:second|sec|s)",
            r"resets.{0,10}(\d+)\s*(?:minute|min)",
            r"resets.{0,10}(\d+)\s*(?:hour|hr|h)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                seconds = int(match.group(1))
                if 'hour' in pattern or ' h)' in pattern:
                    seconds *= 3600
                elif 'minute' in pattern:
                    seconds *= 60
                return seconds
        return None

    def get_wait_time(self, content: str) -> int:
        """Calculate wait time with exponential backoff."""
        extracted = self.extract_reset_time(content)
        if extracted:
            return min(extracted + 5, CLAUDE_RATE_LIMIT_MAX_WAIT_SECONDS)
        
        wait = CLAUDE_RATE_LIMIT_BASE_WAIT_SECONDS * (
            CLAUDE_RATE_LIMIT_BACKOFF_MULTIPLIER ** self.consecutive_rate_limits
        )
        return min(wait, CLAUDE_RATE_LIMIT_MAX_WAIT_SECONDS)

    async def handle_rate_limit(self, content: str) -> tuple[str, int]:
        """Handle Claude API rate limit with smart wait/exit decision."""
        self.consecutive_rate_limits += 1
        wait_time = self.get_wait_time(content)
        wait_minutes = wait_time / 60
        wait_hours = wait_minutes / 60

        print(f"\n{'='*70}")
        print(f"  CLAUDE API RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
        print(f"{'='*70}\n")

        if wait_minutes <= CLAUDE_WAIT_THRESHOLD_AUTO:
            print(f"  Wait time: {wait_minutes:.1f} minutes ({wait_time}s)")
            print(f"  Decision: Auto-waiting (short duration)\n")
            
            if wait_time > 30:
                for remaining in range(wait_time, 0, -30):
                    mins = remaining / 60
                    print(f"  ... {mins:.1f} minutes ({remaining}s) remaining", flush=True)
                    await asyncio.sleep(min(30, remaining))
            else:
                await asyncio.sleep(wait_time)
            
            print("  Rate limit wait complete. Resuming...\n")
            return ("wait", wait_time)

        elif wait_minutes <= CLAUDE_WAIT_THRESHOLD_OPTIONAL:
            print(f"  Wait time: {wait_minutes:.1f} minutes ({wait_hours:.2f} hours)")
            print(f"  Decision: Waiting, but you can press Ctrl+C to exit\n")
            print(f"  To resume later, run the same command again.")
            print(f"  Progress is saved in Linear.\n")

            try:
                for remaining in range(wait_time, 0, -60):
                    mins = remaining / 60
                    print(f"  ... {mins:.1f} minutes remaining (Ctrl+C to exit)", flush=True)
                    await asyncio.sleep(min(60, remaining))
                
                print("  Rate limit wait complete. Resuming...\n")
                return ("wait", wait_time)
            except KeyboardInterrupt:
                print("\n\n  User interrupted. Exiting gracefully...")
                return ("exit", wait_time)

        else:
            print(f"  Wait time: {wait_hours:.1f} hours ({wait_minutes:.0f} minutes)")
            print(f"  Decision: Wait too long, exiting gracefully\n")
            print(f"  {'='*70}")
            print(f"  TO RESUME LATER:")
            print(f"  {'='*70}")
            print(f"  Run the same command after the rate limit resets.")
            print(f"  All progress is saved in Linear and will continue from where it left off.\n")
            print(f"  Estimated reset: ~{wait_hours:.1f} hours from now\n")
            
            return ("exit", wait_time)

    def reset(self) -> None:
        """Reset consecutive rate limit counter."""
        if self.consecutive_rate_limits > 0:
            print("  [Claude API rate limit cleared]")
        self.consecutive_rate_limits = 0


class LinearRateLimitHandler:
    """
    Handles Linear API rate limit detection (1500 requests/hour).
    
    Linear has a fixed 1-hour rolling window, so waits are always manageable.
    This handler always waits rather than exiting.
    
    Tracks elapsed time from first API call to optimize wait duration.
    """

    def __init__(self):
        self.consecutive_rate_limits = 0
        self.first_api_call_time = None  # Track when Linear API usage started in this window
        self.rate_limit_window_seconds = 3600  # Linear's 1-hour window
        self.was_rate_limited = False  # Track if we were rate limited

    def track_api_call(self) -> None:
        """Track successful Linear API call to measure elapsed time in rate limit window."""
        if self.first_api_call_time is None:
            self.first_api_call_time = time.time()
    
    def is_linear_rate_limit(self, content: str, tool_name: str = "") -> bool:
        """Check if content indicates a Linear API rate limit."""
        content_lower = content.lower()
        # Linear-specific patterns
        return (
            ("linear" in content_lower and "rate limit" in content_lower)
            or ("429" in content and "linear" in tool_name.lower())
            or ("1500" in content and "per hour" in content_lower)
            or "mcp__linear__" in tool_name.lower() and any(
                phrase in content_lower
                for phrase in ["rate limit", "too many requests", "429"]
            )
        )

    async def handle_rate_limit(self, content: str) -> tuple[str, int]:
        """Handle Linear API rate limit by waiting only the remaining time in the window."""
        self.consecutive_rate_limits += 1
        self.was_rate_limited = True  # Mark that we hit rate limit
        
        # Calculate actual wait time based on elapsed time since first API call
        if self.first_api_call_time:
            elapsed = time.time() - self.first_api_call_time
            # Only wait the remaining time in the 1-hour window
            wait_time = max(30, int(self.rate_limit_window_seconds - elapsed))  # Min 30s buffer
        else:
            # Fallback: conservative estimate (full hour)
            wait_time = self.rate_limit_window_seconds
        
        wait_time = min(wait_time, LINEAR_RATE_LIMIT_MAX_WAIT_SECONDS)
        wait_minutes = wait_time / 60
        elapsed_minutes = (time.time() - self.first_api_call_time) / 60 if self.first_api_call_time else 0

        print(f"\n{'='*70}")
        print(f"  LINEAR API RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
        print(f"{'='*70}\n")
        print(f"  Linear limit: 1500 requests/hour")
        if self.first_api_call_time:
            print(f"  Time elapsed in current window: {elapsed_minutes:.1f} minutes")
        print(f"  Wait time: {wait_minutes:.1f} minutes ({wait_time}s)")
        print(f"  Decision: Auto-waiting (Linear resets within 1 hour)\n")

        # Show countdown with error handling
        try:
            for remaining in range(wait_time, 0, -60):
                mins = remaining / 60
                print(f"  ... {mins:.0f} minutes remaining", flush=True)
                await asyncio.sleep(min(60, remaining))
        except asyncio.CancelledError:
            print("\n  Rate limit wait interrupted")
            raise
        except Exception as e:
            print(f"\n  Warning: Error during wait countdown: {e}")
            # Still complete the wait
            await asyncio.sleep(max(0, wait_time - (time.time() - self.first_api_call_time) if self.first_api_call_time else wait_time))
        
        print("  Linear rate limit wait complete. Resuming...\n")
        return ("wait", wait_time)

    def reset(self) -> None:
        """Reset consecutive rate limit counter and timer after successful API call post rate-limit."""
        if self.consecutive_rate_limits > 0:
            print("  [Linear API rate limit cleared]")
        self.consecutive_rate_limits = 0
        
        # Only reset timer if we were rate limited (indicating new window has started)
        if self.was_rate_limited:
            self.first_api_call_time = None  # Reset timer for next rate limit window
            self.was_rate_limited = False
            print("  [Linear API rate limit window reset]")


class UnifiedRateLimitHandler:
    """
    Unified rate limit handler that dispatches to appropriate sub-handler.
    
    Automatically detects whether the rate limit is from:
    - Claude API (hourly/weekly/monthly limits, can be hours to days)
    - Linear API (1500 requests/hour, max 1-hour wait)
    
    And applies the appropriate wait/exit strategy for each.
    """

    def __init__(self):
        self.claude_handler = ClaudeRateLimitHandler()
        self.rate_limit_handler = LinearRateLimitHandler()

    def is_rate_limit_error(self, content: str, tool_name: str = "") -> bool:
        """Check if content indicates any rate limit error."""
        return (
            self.claude_handler.is_claude_rate_limit(content)
            or self.rate_limit_handler.is_linear_rate_limit(content, tool_name)
        )

    async def handle_rate_limit(self, content: str, tool_name: str = "") -> tuple[str, int]:
        """
        Handle rate limit by dispatching to appropriate handler.
        
        Args:
            content: Error message content
            tool_name: Name of the tool that generated the error (if applicable)
        
        Returns:
            (action, wait_time) where action is "wait" or "exit"
        """
        # Check Linear first (more specific pattern)
        if self.rate_limit_handler.is_linear_rate_limit(content, tool_name):
            return await self.rate_limit_handler.handle_rate_limit(content)
        
        # Otherwise assume Claude API rate limit
        elif self.claude_handler.is_claude_rate_limit(content):
            return await self.claude_handler.handle_rate_limit(content)
        
        # Fallback: treat as generic rate limit (use Claude handler)
        else:
            print("  [Unknown rate limit source, using Claude handler]")
            return await self.claude_handler.handle_rate_limit(content)
    
    def track_linear_api_call(self) -> None:
        """Track successful Linear API call for rate limit timing."""
        self.rate_limit_handler.track_api_call()

    def reset(self) -> None:
        """Reset both handlers."""
        self.claude_handler.reset()
        self.rate_limit_handler.reset()


class TaskInitializationHandler:
    """Handles task management system initialization checks and guidance."""

    def __init__(self):
        self.initialization_attempts = 0
        self.max_init_attempts = 1

    def is_task_uninitialized(self, project_dir: Path) -> bool:
        """Check if task management project needs initialization."""
        return not is_task_initialized(project_dir)

    def print_initialization_warning(self, project_dir: Path) -> None:
        """Print guidance for task management initialization."""
        self.initialization_attempts += 1

        print(f"\n{'='*70}")
        print(f"  TASK MANAGEMENT PROJECT INITIALIZATION REQUIRED")
        print(f"{'='*70}\n")

        print("The task management project has not been initialized yet.")
        print("\nTo initialize, run the appropriate script for your adapter:")
        print("  Linear:  python query_linear.py --init")
        print("  Jira:    (not yet implemented)")
        print("  GitHub:  (not yet implemented)\n")

        print("This will:")
        print("  1. Connect to your task management workspace")
        print("  2. Create a new project for this task")
        print("  3. Generate initial issues from the specification")
        print("  4. Save the project state locally\n")

        print("Once initialized, the agent will:")
        print("  - Track progress in your task system")
        print("  - Update issue statuses automatically")
        print("  - Create session summaries as comments\n")

        # Determine which env var is needed based on TASK_ADAPTER_TYPE
        adapter_type = os.environ.get("TASK_ADAPTER_TYPE", "linear")
        if adapter_type == "linear":
            env_var = "LINEAR_API_KEY"
        elif adapter_type == "jira":
            env_var = "JIRA_API_KEY"
        elif adapter_type == "github":
            env_var = "GITHUB_TOKEN"
        else:
            env_var = "TASK_API_KEY"
        
        print(f"Environment requirement: {env_var} must be set\n")

    def should_wait_for_init(self) -> bool:
        """Check if we should continue waiting for initialization."""
        return self.initialization_attempts < self.max_init_attempts


# Global handlers for the session
rate_limit_handler = UnifiedRateLimitHandler()
task_init_handler = TaskInitializationHandler()
worker_coordinator: Optional[WorkerCoordinator] = None


def has_work_to_do(project_dir: Path, is_first_run: bool) -> bool:
    """
    Check if there's any work for the agent to do.
    
    Returns:
        True if there's work to do, False if project is complete
    """
    from progress import load_task_project_state
    import subprocess
    import json
    
    # First run always has work (initialization)
    if is_first_run:
        return True
    
    state = load_task_project_state(project_dir)
    if not state or not state.get("initialized"):
        return True  # Needs initialization
    
    # Check if there's an audit to run
    if should_run_audit(project_dir):
        return True
    
    # For BEADS adapter, query actual issue counts from bd CLI
    adapter_type = state.get("adapter", "linear")
    
    if adapter_type == "beads":
        try:
            # Query BEADS for open issue count
            result = subprocess.run(
                ["bd", "count", "--status", "open", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            count_data = json.loads(result.stdout)
            open_count = count_data.get("count", 0)
            
            # Also check for in_progress
            result = subprocess.run(
                ["bd", "count", "--status", "in_progress", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            count_data = json.loads(result.stdout)
            in_progress = count_data.get("count", 0)
            
            return (open_count + in_progress) > 0
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # Fall back to state file counts if bd command fails
            pass
    
    # For Linear/GitHub or fallback: use state file counts
    in_progress = state.get("in_progress", 0)
    todo = state.get("todo", 0)
    open_count = state.get("open", 0)  # BEADS uses 'open' instead of 'todo'
    
    return (in_progress + todo + open_count) > 0


def should_run_audit(project_dir: Path) -> bool:
    """
    Check if it's time to run an audit session.
    
    An audit is triggered when there are >= AUDIT_INTERVAL features
    awaiting audit. This includes:
    1. Tasks with "awaiting-audit" label (new workflow)
    2. Tasks in "Done" status without "audited" label (legacy tasks)
    
    Returns:
        True if audit should run, False otherwise
    """
    from progress import load_task_project_state
    
    state = load_task_project_state(project_dir)
    if not state or not state.get("initialized"):
        return False
    
    # Get count from state file (updated by coding agent)
    # This count includes both:
    # - Explicitly labeled "awaiting-audit" tasks
    # - Done tasks without audit labels (legacy)
    awaiting_count = state.get("features_awaiting_audit", 0)
    
    # Also check for legacy done tasks without audit labels
    # This ensures we catch old tasks that were completed before audit feature
    legacy_done_count = state.get("legacy_done_without_audit", 0)
    
    total_awaiting = awaiting_count + legacy_done_count
    
    return total_awaiting >= AUDIT_INTERVAL


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
    verbose: bool = False,
) -> tuple[str, str]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path
        verbose: Enable verbose output including JSON dumps

    Returns:
        (status, response_text) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
    """
    print("Sending prompt to Claude Agent SDK...\n")

    try:
        # Send the query
        await client.query(message)

        # Collect response text and show tool use
        response_text = ""
        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            # Handle AssistantMessage (text and tool use)
            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        response_text += block.text
                        # Add spacing around agent text blocks
                        if block.text.strip():
                            print(f"\n{block.text}", flush=True)
                        else:
                            print(block.text, end="", flush=True)
                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        tool_name = block.name
                        if verbose:
                            print(f"\n\n[Tool: {tool_name}]", flush=True)
                        
                        # Track Linear API calls when tool is invoked
                        if "mcp__linear__" in tool_name:
                            from linear_tracker import get_tracker
                            tracker = get_tracker()
                            if tracker:
                                # Parse operation and endpoint from tool name
                                # Format: mcp__linear__<operation>_<endpoint>
                                # Examples: mcp__linear__list_issues, mcp__linear__create_issue
                                parts = tool_name.replace("mcp__linear__", "").split("_")
                                if len(parts) >= 2:
                                    operation = parts[0]  # list, create, update, get
                                    endpoint = "_".join(parts[1:])  # issues, projects, etc.
                                else:
                                    operation = parts[0] if parts else "unknown"
                                    endpoint = "unknown"
                                
                                # Extract metadata from input if available
                                metadata = {}
                                if hasattr(block, "input"):
                                    try:
                                        metadata = dict(block.input) if hasattr(block.input, "__dict__") else {}
                                    except:
                                        pass
                                
                                tracker.track_call(operation, endpoint, metadata)
                        
                        if verbose and hasattr(block, "input"):
                            input_str = str(block.input)
                            if len(input_str) > 200:
                                print(f"   Input: {input_str[:200]}...", flush=True)
                            else:
                                print(f"   Input: {input_str}", flush=True)

            # Handle UserMessage (tool results)
            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "ToolResultBlock":
                        result_content = getattr(block, "content", "")
                        is_error = getattr(block, "is_error", False)
                        result_str = str(result_content)

                        # Check if command was blocked by security hook
                        if "blocked" in result_str.lower():
                            print(f"\n   [BLOCKED] {result_content}\n", flush=True)
                        elif is_error:
                            # Check for rate limit errors
                            if rate_limit_handler.is_rate_limit_error(result_str, tool_name=getattr(block, "name", "")):
                                print(f"\n   [Rate Limited] {result_str[:200]}\n", flush=True)
                                action, wait_time = await rate_limit_handler.handle_rate_limit(result_str, tool_name=getattr(block, "name", ""))
                                
                                if action == "exit":
                                    print("\nExiting due to long rate limit wait...")
                                    return "rate_limit_exit", result_str
                            else:
                                # Show other errors (truncated)
                                error_str = result_str[:500]
                                print(f"\n   [Error] {error_str}\n", flush=True)
                        else:
                            # Tool succeeded - reset rate limit counter and track Linear API calls
                            tool_name = getattr(block, "name", "")
                            if "mcp__linear__" in tool_name:
                                rate_limit_handler.rate_limit_handler.track_api_call()
                            rate_limit_handler.reset()
                            if verbose:
                                print("\n   [Done]\n", flush=True)

        print("\n" + "-" * 70 + "\n")
        return "continue", response_text

    except Exception as e:
        print(f"Error during agent session: {e}")
        return "error", str(e)


async def run_autonomous_agent(
    project_dir: Path,
    spec_file: Path,
    initializer_model: str,
    coding_model: str,
    audit_model: str,
    task_adapter: str = "linear",
    max_iterations: Optional[int] = None,
    verbose: bool = False,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        spec_file: Path to spec file relative to project_dir
        initializer_model: Claude model for initialization
        coding_model: Claude model for coding sessions
        audit_model: Claude model for audit sessions
        task_adapter: Task management adapter (linear, beads, github)
        max_iterations: Maximum number of iterations (None for unlimited)
        verbose: Enable verbose output including JSON dumps
    """
    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT DEMO")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Spec file: {spec_file}")
    print(f"Task adapter: {task_adapter}")
    print(f"Initializer model: {initializer_model}")
    print(f"Coding model: {coding_model}")
    print(f"Audit model: {audit_model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Initialize worker coordinator for multi-instance support
    global worker_coordinator, _worker_coordinator
    worker_coordinator = WorkerCoordinator(project_dir)
    worker_coordinator.register()
    _worker_coordinator = worker_coordinator  # Set global for signal handler
    
    # Register signal handler for graceful Ctrl+C shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    
    # Start heartbeat background task
    heartbeat_task = asyncio.create_task(worker_coordinator.heartbeat_loop())

    # Check if this is a fresh start or continuation
    # We use .task_project.json as the marker for initialization
    is_first_run = not is_task_initialized(project_dir)

    # Initialize Linear API call tracker (only for Linear adapter)
    if task_adapter == "linear":
        tracker = init_tracker(project_dir)
        
        # Initialize Linear API cache
        cache = init_cache(project_dir)
        
        # Clean up old data
        tracker.cleanup_old_calls(days=7)
        expired = cache.clear_expired()
        if expired > 0:
            print(f"🧹 Cleared {expired} expired cache entries")
        
        # Check current rate limit status
        calls_last_hour = tracker.get_call_count_in_window()
        if calls_last_hour > 0:
            cache_stats = cache.get_stats()
            remaining = 1500 - calls_last_hour
            percent_used = (calls_last_hour / 1500) * 100
        
        print(f"📊 Linear API Status:")
        print(f"   Calls in last hour: {calls_last_hour}/1500 ({percent_used:.1f}% used)")
        print(f"   Remaining capacity: {remaining} calls")
        
        if cache_stats['total_hits'] > 0:
            print(f"📦 Cache:")
            print(f"   Hits: {cache_stats['total_hits']} | Hit rate: {cache_stats['hit_rate']*100:.1f}%")
            estimated_saved = cache_stats['total_hits']
            print(f"   Estimated API calls saved: {estimated_saved}")
        
        if not tracker.is_safe_to_call():
            print(f"\n⚠️  WARNING: Approaching rate limit!")
            print(f"   Consider waiting {tracker._time_until_safe()}")
            print(f"   💡 Tip: Review QUERY_OPTIMIZATION_GUIDE.md for reducing API calls")
        elif calls_last_hour > 1000:
            print(f"\n⚡ Moderate usage detected ({calls_last_hour} calls)")
            print(f"   💡 Tip: Use .task_project.json IDs directly to avoid metadata queries")
        
        print()

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is creating 50 issues and setting up the project.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
    else:
        print("Continuing existing project (task management initialized)")
        print_progress_summary(project_dir)

    # Main loop
    iteration = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Check if there's work to do (skip on first run to allow initialization)
        if iteration > 1 and not has_work_to_do(project_dir, is_first_run):
            print("\n" + "=" * 70)
            print("  ✅ ALL WORK COMPLETE")
            print("=" * 70)
            print("\nNo pending tasks or audits found.")
            print("All features have been implemented and audited.")
            print("\nTo add new features:")
            print("  1. Update your app_spec.txt file")
            print("  2. Run the script again - it will detect changes and create new issues")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Choose model and prompt based on session type
        # Priority: Audit > Initialization > Coding
        
        if should_run_audit(project_dir):
            # Audit session: Review completed work with audit model
            model = audit_model
            prompt = get_audit_prompt(spec_file, task_adapter)
            session_type = "AUDIT"
            print("=" * 70)
            print("  🔍 AUDIT SESSION - Quality Assurance Review")
            print("=" * 70)
            print(f"Reviewing features with '{AUDIT_LABEL_AWAITING}' label")
            print(f"Using audit model: {model}\n")
            
        elif is_first_run:
            # Initialization session: Set up project and create issues
            model = initializer_model
            prompt = get_initializer_prompt(spec_file, task_adapter)
            session_type = "INITIALIZATION"
            print(f"Using initializer model: {model}\n")
            is_first_run = False  # Only use initializer once
            
        else:
            # Coding session: Implement features
            model = coding_model
            prompt = get_coding_prompt(spec_file, task_adapter)
            session_type = "CODING"
            print(f"Using coding model: {model}\n")

        # Create client (fresh context)
        client = create_client(project_dir, model, task_adapter)

        # Run session with async context manager
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir, verbose)
        
        # Invalidate cache based on operations performed
        from linear_cache import get_cache
        from linear_tracker import get_tracker
        cache = get_cache()
        tracker = get_tracker()
        
        if cache and tracker:
            project_id = get_project_id_from_state(project_dir)
            invalidate_cache_for_operations(cache, tracker, project_id)
        
        # Print Linear API usage summary after session
        if tracker and tracker.session_calls:
            if cache:
                print_combined_stats(cache, tracker)
            else:
                tracker.print_session_summary()

        # Check for quit request
        if _shutdown_requested:
            print("\n\n🛑 Quit requested. Shutting down gracefully...")
            break

        # Handle status
        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s... (press 'q' to quit, or Ctrl+C anytime)")
            
            # Check if task management needs initialization
            if task_init_handler.is_task_uninitialized(project_dir):
                task_init_handler.print_initialization_warning(project_dir)
                if not task_init_handler.should_wait_for_init():
                    print("\nTo proceed, initialize task management using the command above.")
                    break
                if not await interruptible_sleep(AUTO_CONTINUE_DELAY_SECONDS):
                    print("\n\n🛑 Quit requested. Shutting down gracefully...")
                    break
            else:
                print_progress_summary(project_dir)
                if not await interruptible_sleep(AUTO_CONTINUE_DELAY_SECONDS):
                    print("\n\n🛑 Quit requested. Shutting down gracefully...")
                    break

        elif status == "error":
            print("\nSession encountered an error")
            print("Will retry with a fresh session... (press 'q' to quit, or Ctrl+C anytime)")
            if not await interruptible_sleep(AUTO_CONTINUE_DELAY_SECONDS):
                print("\n\n🛑 Quit requested. Shutting down gracefully...")
                break

        elif status == "rate_limit_exit":
            print("\nSession terminated due to long rate limit wait.")
            print("Run the same command again when the rate limit resets.")
            break

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session... (press 'q' to quit, or Ctrl+C anytime)\n")
            if not await interruptible_sleep(1):
                print("\n\n🛑 Quit requested. Shutting down gracefully...")
                break

    # Clean up worker coordinator
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    worker_coordinator.cleanup()

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)
    
    # Print final Linear API usage breakdown with cache stats
    from linear_tracker import get_tracker
    from linear_cache import get_cache
    tracker = get_tracker()
    cache = get_cache()
    
    if tracker and cache:
        print_combined_stats(cache, tracker)
        cache.print_stats()
    elif tracker:
        tracker.print_breakdown()

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("  # Or manually:")
    print("  npm install && npm run dev")
    print("\n  Then open http://localhost:3000 (or check init.sh for the URL)")
    print("-" * 70)

    print("\nDone!")

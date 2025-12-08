"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
"""

import asyncio
import re
from pathlib import Path
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient

from client import create_client
from progress import print_session_header, print_progress_summary, is_linear_initialized
from prompts import get_initializer_prompt, get_coding_prompt


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3

# Rate limiting configuration
RATE_LIMIT_BASE_WAIT_SECONDS = 60  # Start with 1 minute
RATE_LIMIT_MAX_WAIT_SECONDS = 900  # Cap at 15 minutes
RATE_LIMIT_BACKOFF_MULTIPLIER = 2  # Double wait time on consecutive limits


class RateLimitHandler:
    """Handles rate limit detection and exponential backoff."""

    def __init__(self):
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = 0

    def is_rate_limit_error(self, content: str) -> bool:
        """Check if content indicates a rate limit error."""
        content_lower = content.lower()
        return (
            "rate limit" in content_lower
            or "ratelimit" in content_lower
            or "too many requests" in content_lower
            or "429" in content
        )

    def extract_reset_time(self, content: str) -> Optional[int]:
        """Try to extract reset time from error message (in seconds)."""
        # Look for patterns like "retry after X seconds" or "reset in X"
        patterns = [
            r"retry.{0,10}after.{0,5}(\d+)\s*(?:second|sec|s)",
            r"reset.{0,10}in.{0,5}(\d+)\s*(?:second|sec|s)",
            r"wait.{0,10}(\d+)\s*(?:second|sec|s)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                return int(match.group(1))
        return None

    def get_wait_time(self, content: str) -> int:
        """Calculate wait time with exponential backoff."""
        # Try to extract reset time from error
        extracted = self.extract_reset_time(content)
        if extracted:
            return min(extracted + 5, RATE_LIMIT_MAX_WAIT_SECONDS)  # Add 5s buffer

        # Use exponential backoff
        wait = RATE_LIMIT_BASE_WAIT_SECONDS * (
            RATE_LIMIT_BACKOFF_MULTIPLIER ** self.consecutive_rate_limits
        )
        return min(wait, RATE_LIMIT_MAX_WAIT_SECONDS)

    async def handle_rate_limit(self, content: str) -> None:
        """Handle a rate limit by waiting appropriately."""
        self.consecutive_rate_limits += 1
        wait_time = self.get_wait_time(content)

        print(f"\n{'='*50}")
        print(f"  RATE LIMIT DETECTED (#{self.consecutive_rate_limits})")
        print(f"  Waiting {wait_time} seconds before continuing...")
        print(f"{'='*50}\n")

        # Show countdown for long waits
        if wait_time > 30:
            for remaining in range(wait_time, 0, -30):
                print(f"  ... {remaining}s remaining", flush=True)
                await asyncio.sleep(min(30, remaining))
        else:
            await asyncio.sleep(wait_time)

        print("  Rate limit wait complete. Resuming...\n")

    def reset(self) -> None:
        """Reset consecutive rate limit counter (call after successful request)."""
        if self.consecutive_rate_limits > 0:
            print("  [Rate limit cleared - requests succeeding]")
        self.consecutive_rate_limits = 0


# Global rate limit handler for the session
rate_limit_handler = RateLimitHandler()


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
) -> tuple[str, str]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path

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
                        print(block.text, end="", flush=True)
                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        print(f"\n[Tool: {block.name}]", flush=True)
                        if hasattr(block, "input"):
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
                            print(f"   [BLOCKED] {result_content}", flush=True)
                        elif is_error:
                            # Check for rate limit errors
                            if rate_limit_handler.is_rate_limit_error(result_str):
                                print(f"   [Rate Limited] {result_str[:200]}", flush=True)
                                await rate_limit_handler.handle_rate_limit(result_str)
                            else:
                                # Show other errors (truncated)
                                error_str = result_str[:500]
                                print(f"   [Error] {error_str}", flush=True)
                        else:
                            # Tool succeeded - reset rate limit counter
                            rate_limit_handler.reset()
                            print("   [Done]", flush=True)

        print("\n" + "-" * 70 + "\n")
        return "continue", response_text

    except Exception as e:
        print(f"Error during agent session: {e}")
        return "error", str(e)


async def run_autonomous_agent(
    project_dir: Path,
    spec_file: Path,
    model: str,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        spec_file: Path to spec file relative to project_dir
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
    """
    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT DEMO")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Spec file: {spec_file}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Check if this is a fresh start or continuation
    # We use .linear_project.json as the marker for initialization
    is_first_run = not is_linear_initialized(project_dir)

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is creating 50 Linear issues and setting up the project.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
    else:
        print("Continuing existing project (Linear initialized)")
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

        # Print session header
        print_session_header(iteration, is_first_run)

        # Create client (fresh context)
        client = create_client(project_dir, model)

        # Choose prompt based on session type
        if is_first_run:
            prompt = get_initializer_prompt(spec_file)
            is_first_run = False  # Only use initializer once
        else:
            prompt = get_coding_prompt(spec_file)

        # Run session with async context manager
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir)

        # Handle status
        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "error":
            print("\nSession encountered an error")
            print("Will retry with a fresh session...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

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

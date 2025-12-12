"""
Agent SDK Client Configuration
===============================

Adapter-based factory for creating and configuring agent SDK clients.
Supports multiple agent SDKs (Claude, Factory Droid, Aider, OpenCode,
OpenAI Codex CLI, Gemini CLI, Mistral) with a common interface so
sessions can mix and match providers per configuration.
"""

import asyncio
import asyncio.subprocess
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Protocol

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher

from security import bash_security_hook


# Load defaults configuration
def load_defaults() -> dict:
    """Load autocode-defaults.json from script directory."""
    script_dir = Path(__file__).parent
    defaults_path = script_dir / "autocode-defaults.json"

    if defaults_path.exists():
        with open(defaults_path) as f:
            return json.load(f)
    return {}


DEFAULTS = load_defaults()
DEFAULT_AGENT_SDK_KEY = DEFAULTS.get("defaults", {}).get("agent_sdk", "claude-agent-sdk")


def _get_agent_sdk_config(key: str) -> dict:
    """Return SDK config block for a given key from defaults."""
    return DEFAULTS.get("agent_sdks", {}).get(key, {})


def _extract_default_models(config: dict) -> Dict[str, Optional[str]]:
    """Normalize default model settings from the defaults file."""
    defaults = config.get("defaults", {})
    models = config.get("models", {})
    return {
        "initializer": defaults.get("initializer_model") or defaults.get("initializer") or models.get("initializer"),
        "coding": defaults.get("coding_model") or defaults.get("coding") or models.get("coding"),
        "audit": defaults.get("audit_model") or defaults.get("audit") or models.get("audit"),
        "default": defaults.get("default_model") or models.get("default"),
    }


def get_api_key_env_for_sdk(key: str) -> Optional[str]:
    """Lookup the environment variable name for an SDK."""
    return _get_agent_sdk_config(key).get("api_key_env")


def get_default_model_for_sdk(key: str, role: str) -> Optional[str]:
    """Lookup a default model for an SDK and role."""
    adapter_defaults = _extract_default_models(_get_agent_sdk_config(key))
    return adapter_defaults.get(role) or adapter_defaults.get("default")


@dataclass
class TextBlock:
    """Simple text block for adapters without rich tool support."""

    text: str


@dataclass
class ToolUseBlock:
    """Tool use placeholder block."""

    name: str
    input: Any = None


@dataclass
class ToolResultBlock:
    """Tool result placeholder block."""

    name: str
    content: Any
    is_error: bool = False


@dataclass
class AssistantMessage:
    """Assistant message container."""

    content: list[Any]


@dataclass
class UserMessage:
    """User message container."""

    content: list[Any]


class AgentClientProtocol(Protocol):
    """Protocol describing the agent client interface used by the harness."""

    async def __aenter__(self) -> "AgentClientProtocol": ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    async def query(self, message: str) -> None: ...

    def receive_response(self) -> AsyncIterator[Any]: ...


class AgentSDKAdapter:
    """Base adapter for all agent SDK implementations."""

    def __init__(
        self,
        key: str,
        display_name: str,
        default_models: Optional[Dict[str, Optional[str]]] = None,
        api_key_env: Optional[str] = None,
        cli_command: Optional[str] = None,
        supports_tools: bool = False,
    ):
        self.key = key
        self.display_name = display_name
        self.default_models = default_models or {}
        self.api_key_env = api_key_env
        self.cli_command = cli_command
        self.supports_tools = supports_tools

    def get_default_model(self, role: str, fallback: Optional[str] = None) -> Optional[str]:
        """Return default model for a role (initializer/coding/audit)."""
        if self.default_models.get(role):
            return self.default_models.get(role)
        if self.default_models.get("default"):
            return self.default_models.get("default")
        return fallback

    def should_simulate(self, simulate_override: Optional[bool] = None) -> bool:
        """Determine whether to run in simulation mode."""
        if simulate_override is not None:
            return simulate_override
        return os.environ.get("AGENT_SDK_SIMULATE", "false").lower() in ("1", "true", "yes")

    def create_client(
        self,
        project_dir: Path,
        model: Optional[str],
        task_adapter: str,
        session_type: str = "coding",
        simulate: Optional[bool] = None,
    ) -> AgentClientProtocol:
        raise NotImplementedError


class AgentSDKRegistry:
    """Registry for available agent SDK adapters."""

    def __init__(self):
        self._adapters: Dict[str, AgentSDKAdapter] = {}

    def register(self, adapter: AgentSDKAdapter) -> None:
        self._adapters[adapter.key] = adapter

    def get(self, key: str) -> AgentSDKAdapter:
        if key not in self._adapters:
            raise ValueError(
                f"Unknown agent SDK '{key}'. Available: {', '.join(self._adapters.keys()) or 'none'}"
            )
        return self._adapters[key]

    def available(self) -> Dict[str, AgentSDKAdapter]:
        return dict(self._adapters)


# Puppeteer MCP tools for browser automation
PUPPETEER_TOOLS = [
    "mcp__puppeteer__puppeteer_navigate",
    "mcp__puppeteer__puppeteer_screenshot",
    "mcp__puppeteer__puppeteer_click",
    "mcp__puppeteer__puppeteer_fill",
    "mcp__puppeteer__puppeteer_select",
    "mcp__puppeteer__puppeteer_hover",
    "mcp__puppeteer__puppeteer_evaluate",
]

# Linear MCP tools for project management
# Official Linear MCP server at mcp.linear.app
LINEAR_TOOLS = [
    # Team & Project discovery
    "mcp__linear__list_teams",
    "mcp__linear__get_team",
    "mcp__linear__list_projects",
    "mcp__linear__get_project",
    "mcp__linear__create_project",
    "mcp__linear__update_project",
    # Issue management
    "mcp__linear__list_issues",
    "mcp__linear__get_issue",
    "mcp__linear__create_issue",
    "mcp__linear__update_issue",
    "mcp__linear__list_my_issues",
    # Comments
    "mcp__linear__list_comments",
    "mcp__linear__create_comment",
    # Workflow
    "mcp__linear__list_issue_statuses",
    "mcp__linear__get_issue_status",
    "mcp__linear__list_issue_labels",
    "mcp__linear__create_issue_label",
    # Users
    "mcp__linear__list_users",
    "mcp__linear__get_user",
]

# Built-in tools
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]


def build_system_prompt(task_adapter: str) -> str:
    """Build system prompt based on task adapter."""
    if task_adapter == "linear":
        return (
            "You are an expert full-stack developer building a production-quality web application. "
            "You use Linear for project management and tracking all your work."
        )
    if task_adapter == "beads":
        return (
            "You are an expert full-stack developer building a production-quality web application. "
            "You use BEADS (bd CLI) for local task management and tracking all your work."
        )
    if task_adapter == "github":
        return (
            "You are an expert full-stack developer building a production-quality web application. "
            "You use GitHub Issues for project management and tracking all your work."
        )
    return "You are an expert full-stack developer building a production-quality web application."


class SimulatedAgentClient:
    """Simple text-only client used for CLI adapters and simulation."""

    def __init__(
        self,
        provider: str,
        model: str,
        project_dir: Path,
        session_type: str,
        task_adapter: str,
        simulate: bool = True,
    ):
        self.provider = provider
        self.model = model
        self.project_dir = Path(project_dir)
        self.session_type = session_type
        self.task_adapter = task_adapter
        self.simulate = simulate
        self._response: str = ""

    async def __aenter__(self) -> "SimulatedAgentClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def query(self, message: str) -> None:
        preview = (message or "").strip().splitlines()[0:1]
        snippet = preview[0][:140] if preview else ""
        self._response = (
            f"[{self.provider}] Simulated {self.session_type} session with model '{self.model}'. "
            f"Task adapter: {self.task_adapter}. Prompt preview: {snippet}"
        )

    async def receive_response(self) -> AsyncIterator[Any]:
        yield AssistantMessage(content=[TextBlock(text=self._response)])


class ExternalProcessAgentClient(SimulatedAgentClient):
    """Agent client that shells out to a CLI tool with stdin prompts."""

    def __init__(
        self,
        provider: str,
        model: str,
        project_dir: Path,
        session_type: str,
        task_adapter: str,
        command: Optional[list[str]],
        simulate: bool = False,
    ):
        super().__init__(
            provider=provider,
            model=model,
            project_dir=project_dir,
            session_type=session_type,
            task_adapter=task_adapter,
            simulate=simulate or not command,
        )
        self.command = command or []

    async def query(self, message: str) -> None:
        if self.simulate or not self.command:
            await super().query(message)
            return

        cmd = list(self.command)
        if self.model:
            cmd += ["--model", self.model]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.project_dir),
            )
            stdout, _ = await proc.communicate(input=(message or "").encode("utf-8"))
            output = (stdout or b"").decode("utf-8", errors="ignore")
            if proc.returncode not in (0, None):
                output = f"[{self.provider}] command exited with code {proc.returncode}:\n{output}"
            self._response = output.strip() or f"[{self.provider}] command produced no output."
        except FileNotFoundError:
            self._response = (
                f"[{self.provider}] command '{self.command[0]}' not found. "
                "Install the CLI or enable simulation with AGENT_SDK_SIMULATE=1."
            )


class ClaudeAgentAdapter(AgentSDKAdapter):
    """Adapter for the Claude Agent SDK."""

    def __init__(self, default_models: Optional[Dict[str, Optional[str]]] = None, api_key_env: Optional[str] = None):
        super().__init__(
            key="claude-agent-sdk",
            display_name="Claude Agent SDK",
            default_models=default_models,
            api_key_env=api_key_env,
            supports_tools=True,
        )

    def create_client(
        self,
        project_dir: Path,
        model: Optional[str],
        task_adapter: str,
        session_type: str = "coding",
        simulate: Optional[bool] = None,
    ) -> AgentClientProtocol:
        # Determine API key for Claude
        api_key_env = self.api_key_env or "CLAUDE_CODE_OAUTH_TOKEN"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(
                f"{api_key_env} environment variable not set.\n"
                "Run 'claude setup-token' after installing the Claude Code CLI."
            )

        # Only require Linear API key if using Linear adapter
        linear_api_key = None
        if task_adapter == "linear":
            linear_api_key = os.environ.get("LINEAR_API_KEY")
            if not linear_api_key:
                raise ValueError(
                    "LINEAR_API_KEY environment variable not set.\n"
                    "Get your API key from: https://linear.app/YOUR-TEAM/settings/api"
                )

        # Build task management tools and servers based on adapter
        task_tools: list[str] = []
        task_mcp_servers: dict[str, dict[str, Any]] = {}
        task_manager_desc = ""

        if task_adapter == "linear":
            task_tools = LINEAR_TOOLS
            task_mcp_servers = {
                "linear": {
                    "type": "http",
                    "url": "https://mcp.linear.app/mcp",
                    "headers": {
                        "Authorization": f"Bearer {linear_api_key}"
                    }
                }
            }
            task_manager_desc = "linear (project management)"
        elif task_adapter == "beads":
            task_manager_desc = "BEADS (local task management)"
        elif task_adapter == "github":
            task_manager_desc = "GitHub Issues"

        # Security settings for Claude
        allowed_permissions = [
            # Allow all file operations within the project directory
            "Read(./**)",
            "Write(./**)",
            "Edit(./**)",
            "Glob(./**)",
            "Grep(./**)",
            # Bash permission granted here, but actual commands are validated
            # by the bash_security_hook (see security.py for allowed commands)
            "Bash(*)",
            # Allow Puppeteer MCP tools for browser automation
            *PUPPETEER_TOOLS,
            # Add task management tools
            *task_tools,
        ]

        security_settings = {
            "sandbox": {"enabled": False},
            "permissions": {
                "defaultMode": "acceptEdits",  # Auto-approve edits within allowed directories
                "allow": allowed_permissions,
            },
        }

        # Ensure project directory exists before creating settings file
        project_dir.mkdir(parents=True, exist_ok=True)

        # Write settings to a file in the project directory
        settings_file = project_dir / ".claude_settings.json"
        with open(settings_file, "w") as f:
            json.dump(security_settings, f, indent=2)

        print(f"Created security settings at {settings_file}")
        print(f"   - Filesystem restricted to: {project_dir.resolve()}")
        print("   - Bash commands restricted to allowlist (see security.py)")

        mcp_server_list = ["puppeteer (browser automation)"]
        if task_manager_desc:
            mcp_server_list.append(task_manager_desc)
        print(f"   - MCP servers: {', '.join(mcp_server_list)}")
        print()

        system_prompt = build_system_prompt(task_adapter)

        # Combine MCP servers
        all_mcp_servers = {
            "puppeteer": {"command": "npx", "args": ["puppeteer-mcp-server"]},
            **task_mcp_servers
        }

        resolved_model = model or self.get_default_model(session_type)

        return ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=resolved_model,
                system_prompt=system_prompt,
                allowed_tools=[
                    *BUILTIN_TOOLS,
                    *PUPPETEER_TOOLS,
                    *task_tools,
                ],
                mcp_servers=all_mcp_servers,
                hooks={
                    "PreToolUse": [
                        HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                    ],
                },
                max_turns=1000,
                cwd=str(project_dir.resolve()),
                settings=str(settings_file.resolve()),  # Use absolute path
            )
        )


class CliAgentAdapter(AgentSDKAdapter):
    """Adapter for CLI-first agents. Falls back to simulation when requested."""

    def __init__(
        self,
        key: str,
        display_name: str,
        command: Optional[Any],
        default_models: Optional[Dict[str, Optional[str]]] = None,
        api_key_env: Optional[str] = None,
    ):
        super().__init__(
            key=key,
            display_name=display_name,
            default_models=default_models,
            api_key_env=api_key_env,
            cli_command=command,
            supports_tools=False,
        )
        if command is None:
            self.command = None
        elif isinstance(command, str):
            # Allow commands with args separated by spaces
            self.command = command.split()
        elif isinstance(command, (list, tuple)):
            self.command = [str(part) for part in command]
        else:
            self.command = [str(command)]

    def create_client(
        self,
        project_dir: Path,
        model: Optional[str],
        task_adapter: str,
        session_type: str = "coding",
        simulate: Optional[bool] = None,
    ) -> AgentClientProtocol:
        resolved_model = model or self.get_default_model(session_type) or "default"
        simulate_flag = self.should_simulate(simulate)
        return ExternalProcessAgentClient(
            provider=self.display_name,
            model=resolved_model,
            project_dir=project_dir,
            session_type=session_type,
            task_adapter=task_adapter,
            command=self.command,
            simulate=simulate_flag,
        )


# Initialize registry and adapters
AGENT_SDK_REGISTRY = AgentSDKRegistry()

# Claude remains the default adapter
AGENT_SDK_REGISTRY.register(
    ClaudeAgentAdapter(
        default_models=_extract_default_models(_get_agent_sdk_config("claude-agent-sdk")),
        api_key_env=get_api_key_env_for_sdk("claude-agent-sdk"),
    )
)

# Additional adapters registered in requested order
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="factory-droid",
        display_name="Factory Droid",
        command=_get_agent_sdk_config("factory-droid").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("factory-droid")),
        api_key_env=get_api_key_env_for_sdk("factory-droid"),
    )
)
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="aider",
        display_name="Aider",
        command=_get_agent_sdk_config("aider").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("aider")),
        api_key_env=get_api_key_env_for_sdk("aider"),
    )
)
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="opencode",
        display_name="OpenCode",
        command=_get_agent_sdk_config("opencode").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("opencode")),
        api_key_env=get_api_key_env_for_sdk("opencode"),
    )
)
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="openai-codex-cli",
        display_name="OpenAI Codex CLI",
        command=_get_agent_sdk_config("openai-codex-cli").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("openai-codex-cli")),
        api_key_env=get_api_key_env_for_sdk("openai-codex-cli"),
    )
)
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="gemini-cli",
        display_name="Gemini CLI",
        command=_get_agent_sdk_config("gemini-cli").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("gemini-cli")),
        api_key_env=get_api_key_env_for_sdk("gemini-cli"),
    )
)
AGENT_SDK_REGISTRY.register(
    CliAgentAdapter(
        key="mistral",
        display_name="Mistral",
        command=_get_agent_sdk_config("mistral").get("cli_command"),
        default_models=_extract_default_models(_get_agent_sdk_config("mistral")),
        api_key_env=get_api_key_env_for_sdk("mistral"),
    )
)


def get_registered_agent_sdks() -> Dict[str, AgentSDKAdapter]:
    """Expose registered adapters for configuration resolution and tests."""
    return AGENT_SDK_REGISTRY.available()


def create_client(
    project_dir: Path,
    model: Optional[str],
    task_adapter: str = "linear",
    agent_sdk: Optional[str] = None,
    session_type: str = "coding",
    simulate: Optional[bool] = None,
) -> AgentClientProtocol:
    """
    Create an agent client via the adapter registry.

    Args:
        project_dir: Directory for the project
        model: Model identifier for the selected SDK (falls back to defaults if None)
        task_adapter: Task management adapter (linear, beads, github)
        agent_sdk: Agent SDK key (default: value from autocode-defaults.json)
        session_type: Session role (initializer, coding, audit, spec_change, etc.)
        simulate: Force simulation (True/False) or use env default when None

    Returns:
        Configured agent client implementing AgentClientProtocol
    """
    sdk_key = agent_sdk or DEFAULT_AGENT_SDK_KEY
    adapter = AGENT_SDK_REGISTRY.get(sdk_key)
    resolved_model = model or adapter.get_default_model(session_type)
    return adapter.create_client(
        project_dir=project_dir,
        model=resolved_model,
        task_adapter=task_adapter,
        session_type=session_type,
        simulate=simulate,
    )

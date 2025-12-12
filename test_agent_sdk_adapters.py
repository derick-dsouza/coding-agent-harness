import argparse
from pathlib import Path

import pytest

from autocode import DEFAULT_SPEC_FILE, resolve_config
from client import create_client, get_registered_agent_sdks


def test_registry_contains_all_agent_sdks():
    registry_keys = list(get_registered_agent_sdks().keys())
    expected_order = [
        "claude-agent-sdk",
        "factory-droid",
        "aider",
        "opencode",
        "openai-codex-cli",
        "gemini-cli",
        "mistral",
    ]
    assert registry_keys[: len(expected_order)] == expected_order


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sdk_key",
    ["factory-droid", "aider", "opencode", "openai-codex-cli", "gemini-cli", "mistral"],
)
async def test_cli_adapters_simulate_response(tmp_path: Path, sdk_key: str):
    display_name = get_registered_agent_sdks()[sdk_key].display_name
    client = create_client(
        project_dir=tmp_path,
        model="demo-model",
        task_adapter="linear",
        agent_sdk=sdk_key,
        session_type="coding",
        simulate=True,
    )

    async with client:
        await client.query("hello world")
        messages = [msg async for msg in client.receive_response()]

    assert messages
    combined_text = " ".join(
        block.text
        for msg in messages
        for block in getattr(msg, "content", [])
        if hasattr(block, "text")
    )
    assert display_name in combined_text
    assert "Simulated" in combined_text


def test_resolve_config_mix_and_match_agent_sdks(tmp_path: Path):
    spec_path = tmp_path / DEFAULT_SPEC_FILE
    spec_path.write_text("Feature: sample spec", encoding="utf-8")

    args = argparse.Namespace(
        project_dir=tmp_path,
        spec_file=None,
        model=None,
        initializer_model="init-model",
        coding_model="code-model",
        audit_model="audit-model",
        agent_sdk="claude-agent-sdk",
        initializer_sdk="factory-droid",
        coding_sdk="aider",
        audit_sdk="gemini-cli",
        simulate_agent_sdk=True,
        task_adapter=None,
        max_iterations=3,
        verbose=False,
    )

    resolved = resolve_config(args, tmp_path, {})

    assert resolved["agent_sdks"]["initializer"] == "factory-droid"
    assert resolved["agent_sdks"]["coding"] == "aider"
    assert resolved["agent_sdks"]["audit"] == "gemini-cli"
    assert resolved["initializer_model"] == "init-model"
    assert resolved["coding_model"] == "code-model"
    assert resolved["audit_model"] == "audit-model"
    assert resolved["simulate_agent_sdk"] is True
    assert resolved["max_iterations"] == 3
    assert resolved["spec_file"] == Path(DEFAULT_SPEC_FILE)

# Claude Agent SDK Authentication Flow

## Overview
This document details the current Claude Agent SDK authentication implementation to serve as a reference for implementing similar flows for Codex and Gemini SDKs.

## Environment Variable

**Primary Token Variable:** `CLAUDE_CODE_OAUTH_TOKEN`

- **Location in Code:** `client.py` line 365
- **Default Behavior:** If not set in the adapter config, defaults to `CLAUDE_CODE_OAUTH_TOKEN`
- **Configurable:** Can be overridden via `api_key_env` in the adapter configuration

## Token Acquisition

Users obtain the Claude OAuth token through the Claude CLI:

```bash
claude setup-token
```

This command handles the OAuth flow and stores the token for the user.

## Token Storage

**Storage Method:** Environment variable only

- The token is read from the environment at runtime
- No file-based token storage is implemented in the harness
- The Claude CLI may store tokens in its own config directory, but the harness only reads from environment

## Token Usage in ClaudeAgentAdapter

**Code Location:** `client.py` lines 344-477

### Authentication Flow:

1. **Adapter Initialization** (lines 347-354):
   - Creates `ClaudeAgentAdapter` with optional `api_key_env` parameter
   - Falls back to `CLAUDE_CODE_OAUTH_TOKEN` if not specified

2. **Client Creation** (lines 356-477):
   - Reads token from environment variable (line 366)
   - **Strict Enforcement:** Raises `ValueError` if token is not set (lines 367-371)
   - Error message directs users to run `claude setup-token`

3. **SDK Client Initialization** (lines 458-477):
   - Token is passed implicitly through Claude SDK's internal mechanisms
   - The `ClaudeSDKClient` reads the token from the environment variable internally
   - No explicit token parameter in the constructor

## Token Refresh Behavior

**Current Implementation:** No explicit refresh logic

- The Claude SDK handles token refresh internally
- The harness assumes the token is valid for the session duration
- If token expires, the SDK will throw an error which propagates to the user

## Security Settings

**Token Security:**
- Token is never logged or printed
- Token is never written to files by the harness
- Token is read-only from environment
- No token is embedded in code or configuration files

## Adapter Configuration

**Configuration File:** `autocode-defaults.json`

Example structure:
```json
{
  "agent_sdks": {
    "claude-agent-sdk": {
      "api_key_env": "CLAUDE_CODE_OAUTH_TOKEN",
      "defaults": {
        "initializer_model": "claude-sonnet-4-20250514",
        "coding_model": "claude-sonnet-4-20250514",
        "audit_model": "opus-4-20250514"
      }
    }
  }
}
```

## Error Handling

**Missing Token Error:**
```
ValueError: CLAUDE_CODE_OAUTH_TOKEN environment variable not set.
Run 'claude setup-token' after installing the Claude Code CLI.
```

**Actionable Error Messages:**
- Clear indication of which environment variable is missing
- Explicit instructions on how to fix (run `claude setup-token`)
- Only shown when attempting to create a client, not at import time

## Key Differences from Other Adapters

**Claude vs. CLI Adapters (Codex, Gemini, etc.):**

1. **Tool Support:**
   - Claude: Full tool support via `ClaudeAgentAdapter` (line 353: `supports_tools=True`)
   - CLI Adapters: No tool support via `CliAgentAdapter` (line 497: `supports_tools=False`)

2. **Execution Mode:**
   - Claude: Direct SDK integration with async streaming
   - CLI Adapters: External process execution via `ExternalProcessAgentClient`

3. **Simulation Mode:**
   - Claude: No simulation mode (always requires valid token)
   - CLI Adapters: Fallback to `SimulatedAgentClient` when `AGENT_SDK_SIMULATE=1` or CLI not found

## Integration Points for New Auth Flows

To implement similar authentication for Codex/Gemini:

1. **For CLI-based adapters** (current approach for Codex/Gemini):
   - Set `api_key_env` in the adapter configuration
   - Token validation happens when spawning the CLI process
   - CLI tool itself handles authentication

2. **For SDK-based adapters** (if/when SDKs are available):
   - Create new adapter class similar to `ClaudeAgentAdapter`
   - Implement token validation in `create_client` method
   - Provide clear error messages with resolution steps

3. **For CLIProxy fallback**:
   - New adapter or conditional logic within existing adapter
   - Check for `CLI_PROXY_URL` environment variable
   - Route requests through proxy service

## Token Lifecycle Summary

```
User Setup:
  1. Install Claude CLI
  2. Run: claude setup-token
  3. OAuth flow completes
  4. Token stored by Claude CLI

Harness Runtime:
  1. Export CLAUDE_CODE_OAUTH_TOKEN (from CLI storage or manual)
  2. Harness reads from environment
  3. Passes to Claude SDK
  4. SDK handles authentication/refresh internally
  5. Session runs with authenticated access
```

## Notes for Codex/Gemini Implementation

**Similarities to replicate:**
- Environment-based token configuration
- Clear error messages with actionable steps
- No hardcoded credentials
- Configurable environment variable names

**Differences to consider:**
- CLI adapters may need different validation approaches
- May need to check if CLI tool is installed
- May need to handle multiple auth methods (OAuth vs. API key)
- CLIProxy fallback adds complexity not present in Claude flow

**Unchanged Requirement:**
- Claude authentication MUST remain exactly as-is
- No modifications to `ClaudeAgentAdapter` class
- No changes to `CLAUDE_CODE_OAUTH_TOKEN` usage
- Existing Claude tests must continue to pass

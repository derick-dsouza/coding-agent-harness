# Agent SDK Auth Extension Plan

## Context
- Claude Agent SDK currently uses OAuth token (env-based) and works; keep unchanged.
- Adapter registry now supports CLI-oriented Codex, Gemini, Factory Droid, Aider, OpenCode, Mistral with simulation fallback.
- Goal: add reliable auth flows for Codex and Gemini comparable to Claude; if native OAuth is unavailable, use CLIProxy with subscription credentials.

## Plan (Detailed)
1) **Auth Options Inventory**
   - Document Claude flow specifics (env name, file outputs, refresh behavior).
   - Check Codex CLI: supported auth modes (device code/OAuth/API key); identify login command and token storage.
   - Check Gemini CLI: supported auth modes; identify login command and token storage.

2) **Codex Auth Path**
   - Preferred: CLI/device-code OAuth; capture token into `CODEX_OAUTH_TOKEN`.
   - If not available: enable CLIProxy fallback with config key `codex.use_cli_proxy`, using `CLI_PROXY_URL` and proxy token tied to subscription.
   - Adapter enforcement: block when token/proxy missing (unless simulation); pass token/flags to CLI or proxy command.

3) **Gemini Auth Path**
   - Preferred: CLI/device-code OAuth; capture token into `GEMINI_OAUTH_TOKEN` (or `GEMINI_API_KEY` if OAuth absent).
   - Fallback: CLIProxy via `gemini.use_cli_proxy` using the same proxy settings.
   - Adapter enforcement mirrors Codex (require token/proxy unless simulation).

4) **Shared Auth Utilities**
   - Add helper to resolve per-SDK auth: read env vars, optionally invoke CLI login flow, surface next steps.
   - Extend defaults/config schema: per-SDK `auth_type`, expected env vars, and fallback order (OAuth → API key → proxy → simulation).
   - Normalize diagnostics (which path selected, which env missing, suggested command).

5) **Adapter Wiring**
   - Codex/Gemini adapters accept auth payload (token/proxy flags) and include it in CLI invocations.
   - Simulation skips auth checks by design.
   - Startup prints active auth path and warnings when falling back to proxy/simulation.

6) **Testing**
   - Unit tests for auth resolution matrix: token present/missing; proxy enabled/disabled; simulation on/off.
   - Optional integration/manual: documented CLI login steps and expected outputs for Codex and Gemini; proxy smoke test if available.

7) **Documentation**
   - README/config updates: env vars, login commands, proxy setup, troubleshooting (missing/expired token, proxy misconfig).
   - Note that Claude path remains unchanged and still requires OAuth token.

8) **Rollout Safety**
   - Default Codex/Gemini to simulation until tokens/proxy configured.
   - No changes to Claude behavior.
   - Ensure errors are actionable: include exact env/command to fix.

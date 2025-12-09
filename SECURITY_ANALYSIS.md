# Security Policy Analysis & Recommendations

## Analysis Date
December 9, 2025

## Executive Summary
Analysis of the autonomous coding agent execution logs reveals several commands that are frequently blocked but could be safely allowed with proper validation. This document provides recommendations for improving the security allowlist.

---

## Blocked Commands Analysis

### 1. **`cd` (Change Directory)** ⚠️ HIGH IMPACT
**Frequency:** Very High (blocked 10+ times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `cd /path && git status`
- `cd /path && npm run build`
- `cd /path && ls -la`

**Recommendation:** ⛔ **DO NOT ADD**

**Rationale:**
- The `cd` command changes the shell's working directory state
- Agent SDK has `Bash` tool with absolute paths - no need for `cd`
- Allowing `cd` could lead to confusion about current working directory
- Security: Could enable directory traversal attacks

**Alternative Solution:**
- Use `-C` flag for git: `git -C /path status`
- Use `--prefix` flag for npm: `npm --prefix /path run build`
- Use absolute paths for all commands

---

### 2. **`curl` (HTTP Client)** ⚠️ HIGH IMPACT
**Frequency:** High (blocked 8+ times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- Testing API endpoints: `curl http://localhost:3001/api/health`
- Fetching data: `curl -s http://localhost:3001/api/user/profile`
- API validation during development

**Recommendation:** ✅ **ADD WITH RESTRICTIONS**

**Proposed Validation:**
```python
def validate_curl_command(command_string: str) -> tuple[bool, str]:
    """
    Validate curl commands - only allow localhost/127.0.0.1
    """
    tokens = shlex.split(command_string)
    
    # Find URL argument
    url = None
    for token in tokens[1:]:
        if not token.startswith('-') and ('http://' in token or 'https://' in token):
            url = token
            break
    
    if not url:
        return False, "No URL found in curl command"
    
    # Only allow localhost
    if 'localhost' in url or '127.0.0.1' in url:
        return True, ""
    
    return False, "curl only allowed for localhost URLs"
```

**Security Benefits:**
- Enables API testing without external network access
- Restricted to localhost prevents data exfiltration
- Useful for verifying backend endpoints

---

### 3. **`pgrep` (Process Grep)** ⚠️ MEDIUM IMPACT
**Frequency:** Medium (blocked 3+ times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `pgrep -f "node.*server"` - Check if server running
- `pgrep -f "vite"` - Check if frontend running

**Recommendation:** ✅ **ADD** (Low Risk)

**Rationale:**
- Read-only command (doesn't modify system state)
- Useful for checking process status
- Alternative `ps aux | grep` is more complex and already allowed
- Security: No known vulnerabilities, only lists process IDs

**Proposed Addition:**
```python
ALLOWED_COMMANDS = {
    # ... existing commands ...
    "pgrep",  # Process listing by pattern
}
```

---

### 4. **`find` (File Find)** ⚠️ MEDIUM IMPACT
**Frequency:** Low (blocked 2 times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `find /path -name "*.jsx" -type f` - Locate files by pattern

**Recommendation:** ⚠️ **CONDITIONAL ADD**

**Rationale:**
- Useful for locating files in large projects
- Agent SDK has `glob` tool which is better suited
- `find` can be slow on large directories
- Security: Limited risk if restricted to project directory

**Alternative Solution:**
- Use SDK's `glob` tool instead
- Document that `glob` should be used for file discovery

---

### 5. **`python3` / `python` (Python Interpreter)** ⚠️ HIGH IMPACT
**Frequency:** Low (blocked 2 times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- JSON parsing: `python3 -c "import sys, json; ..."`
- Quick data processing

**Recommendation:** ⛔ **DO NOT ADD**

**Rationale:**
- Extremely powerful - can execute arbitrary code
- Agent has Read/Write tools for file manipulation
- JSON parsing can be done in JavaScript/Node
- Security: High risk of code execution vulnerabilities

**Alternative Solution:**
- Use `node -e` for quick scripts (node is already allowed)
- Use `jq` for JSON processing (could be added)

---

### 6. **`xargs` (Extended Arguments)** ⚠️ LOW IMPACT
**Frequency:** Low (blocked 1 time)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `lsof -ti :3001 | xargs kill` - Kill process by port

**Recommendation:** ⛔ **DO NOT ADD**

**Rationale:**
- Can be used to construct complex command chains
- Alternative: `pkill` is already allowed and safer
- Security: Could enable command injection

**Alternative Solution:**
- Use `pkill -f "pattern"` which is already allowed
- Document proper pkill usage patterns

---

### 7. **`kill` (Kill Process)** ⚠️ HIGH IMPACT
**Frequency:** Medium (blocked 3+ times)

**Current Status:** ❌ Not allowed (but `pkill` is allowed)

**Use Cases in Logs:**
- `kill <PID>` - Terminate specific process
- `kill -9 <PID>` - Force kill

**Recommendation:** ✅ **ADD WITH VALIDATION**

**Proposed Validation:**
```python
def validate_kill_command(command_string: str) -> tuple[bool, str]:
    """
    Validate kill commands - only allow numeric PIDs
    Prevent killing system processes
    """
    tokens = shlex.split(command_string)
    
    if len(tokens) < 2:
        return False, "kill requires a PID"
    
    # Check for signal flag
    signal = None
    pid = None
    
    for token in tokens[1:]:
        if token.startswith('-'):
            # Allow common signals: -9, -15, -TERM, -KILL
            if token in ['-9', '-15', '-TERM', '-KILL', '-INT']:
                signal = token
            else:
                return False, f"Signal {token} not allowed"
        elif token.isdigit():
            pid = int(token)
    
    if pid is None:
        return False, "No valid PID provided"
    
    # Prevent killing system processes (PID < 1000)
    if pid < 1000:
        return False, f"Cannot kill system process {pid}"
    
    return True, ""
```

**Rationale:**
- More precise than `pkill` (targets specific PID)
- Needed when `lsof` returns a PID to kill
- With validation, safer than pkill for specific use cases
- Security: Validation prevents system process termination

---

### 8. **`which` (Command Locator)** ⚠️ LOW IMPACT
**Frequency:** Low (blocked 1 time)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `which npm` - Find npm path

**Recommendation:** ✅ **ADD** (Very Low Risk)

**Rationale:**
- Read-only command
- Useful for debugging PATH issues
- No security risk
- Commonly used in shell scripts

---

### 9. **`npx` (NPM Package Runner)** ⚠️ HIGH IMPACT
**Frequency:** Medium (blocked 2+ times)

**Current Status:** ❌ Not allowed (but in pkill allowlist!)

**Use Cases in Logs:**
- `npx vite --port 5173` - Run Vite dev server

**Recommendation:** ✅ **ADD** (needed for modern JS development)

**Rationale:**
- Essential for modern JavaScript development
- Already trusted in pkill validation
- Inconsistent to allow pkill for npx but not npx itself
- Security: Similar risk profile to npm (already allowed)

---

### 10. **`pnpm` (Package Manager)** ⚠️ MEDIUM IMPACT
**Frequency:** Medium (blocked 3+ times)

**Current Status:** ❌ Not allowed

**Use Cases in Logs:**
- `pnpm dev --prefix /path` - Run dev server
- `pnpm install` - Install dependencies

**Recommendation:** ✅ **ADD** (similar to npm)

**Rationale:**
- Alternative package manager to npm
- Many projects use pnpm instead of npm
- Same security profile as npm
- Agent forced to use npm even when project uses pnpm

---

### 11. **`jq` (JSON Processor)** 💡 NOT MENTIONED BUT USEFUL
**Frequency:** N/A (not attempted)

**Current Status:** ❌ Not allowed

**Recommendation:** ✅ **ADD** (Very Useful)

**Rationale:**
- Safer alternative to `python -c` for JSON processing
- Read-only operations
- Commonly needed for API testing
- No security risk

---

## Other Anomalies Detected

### 1. **Puppeteer MCP Tool Permission Issues**
**Issue:** Multiple attempts to use `puppeteer_connect_active_tab` were denied
```
Claude requested permissions to use mcp__puppeteer__puppeteer_connect_active_tab, 
but you haven't granted it yet.
```

**Impact:** Agent cannot reconnect to detached browser frames, causing test failures

**Recommendation:** Pre-grant puppeteer permissions in MCP configuration

---

### 2. **Linear API Rate Limiting**
**Issue:** Multiple `Rate limit exceeded` errors
```
Rate limit exceeded. Only 1500 requests are allowed per 1 hour.
```

**Impact:** Agent cannot update issue status, add comments, or check project state

**Recommendations:**
1. Implement exponential backoff for Linear API calls
2. Cache issue status locally to reduce API calls
3. Batch operations when possible
4. Add rate limit monitoring and warnings

---

### 3. **Inconsistent pkill Allowlist**
**Issue:** `npx`, `vite`, `next` are in pkill's allowed processes but not in ALLOWED_COMMANDS

**Code:**
```python
# In validate_pkill_command
allowed_process_names = {
    "node", "npm", "npx", "vite", "next"
}

# But in ALLOWED_COMMANDS
ALLOWED_COMMANDS = {
    "npm", "node",  # npx, vite, next missing!
}
```

**Impact:** Can kill npx/vite/next processes but cannot start them

**Recommendation:** Add consistency or document rationale

---

### 4. **Server Restart Challenges**
**Issue:** Agent struggled to restart backend server due to lack of kill/pkill capabilities

**Pattern Observed:**
1. Agent modifies server code
2. Needs to restart server to apply changes
3. Cannot use `kill <PID>` (blocked)
4. Cannot use `pkill node` (too broad, validation fails)
5. Resorts to manual intervention requests

**Recommendation:** Add `kill` command with validation (see recommendation #7)

---

### 5. **Browser Frame Detachment**
**Issue:** Puppeteer browser frames became detached frequently

**Error Pattern:**
```
Navigation failed: Attempted to use detached Frame
```

**Impact:** UI testing became impossible mid-session

**Recommendations:**
1. Add error recovery in Puppeteer tool
2. Implement automatic reconnection
3. Add timeout for stale frames

---

## Recommended Changes to security.py

### Priority 1 (High Value, Low Risk)
```python
ALLOWED_COMMANDS = {
    # ... existing commands ...
    
    # Process management improvements
    "pgrep",    # Check running processes (read-only)
    "which",    # Find command paths (read-only)
    
    # Package managers
    "npx",      # NPM package runner (needed for modern JS)
    "pnpm",     # Alternative package manager
    
    # Utilities
    "jq",       # JSON processor (safer than python -c)
}

COMMANDS_NEEDING_EXTRA_VALIDATION = {
    "pkill", "chmod", "init.sh",
    "curl",   # NEW: localhost only
    "kill",   # NEW: PID validation
}
```

### Priority 2 (Consider for Future)
- Document that `cd` should never be added (use absolute paths)
- Document that `python`/`python3` should use `node -e` instead
- Add `timeout` command for long-running operations
- Add `date` for timestamping

---

## Implementation Priority

### Phase 1 (Immediate - No Risk)
1. Add `pgrep` - read-only, very useful
2. Add `which` - read-only, debugging aid
3. Add `jq` - read-only, JSON processing
4. Add `npx` - already trusted in pkill
5. Add `pnpm` - same as npm

### Phase 2 (Short Term - Low Risk)
6. Add `curl` with localhost-only validation
7. Add `kill` with PID validation (>1000)

### Phase 3 (Future - Documentation)
8. Document alternatives to `cd`, `python`, `find`
9. Add developer guide for working within restrictions
10. Create troubleshooting guide for common patterns

---

## Testing Recommendations

After implementing changes:

1. **Test curl validation:**
   ```bash
   curl http://localhost:3001/health  # Should allow
   curl http://google.com            # Should block
   ```

2. **Test kill validation:**
   ```bash
   kill 12345      # Should allow (if PID > 1000)
   kill 999        # Should block (system process)
   kill -9 12345   # Should allow
   kill -HUP 12345 # Should block (signal not allowed)
   ```

3. **Test existing commands still work:**
   - All existing allowed commands
   - pkill validation
   - chmod validation

---

## Conclusion

The current security policy is generally sound but overly restrictive for development scenarios. The recommendations focus on:

1. **High-value additions** (curl, kill, pgrep) that significantly improve agent capability
2. **Consistency** (npx, pnpm) to match existing tool trust levels
3. **Safety** through validation functions rather than blanket blocks
4. **Documentation** to guide proper usage patterns

The proposed changes maintain security while reducing friction in the development workflow.

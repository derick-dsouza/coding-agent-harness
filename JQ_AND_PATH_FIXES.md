# jq Error and Hardcoded Path Fixes

## Issues Fixed

### 1. jq JSON Parsing Error

**Problem:** 
```bash
jq: error (at <stdin>:12): Cannot index array with string "description"
```

**Root Cause:**
The prompts were using `jq -r '.description'` to parse output from `bd show ISSUE_ID --json`, but `bd show` actually returns an **array** (even for a single issue), not a single object.

**Fix Applied (Updated 2025-12-11):**
Changed all occurrences in prompts from:
```bash
bd show ISSUE_ID --json | jq -r '.description'
```
To:
```bash
bd show ISSUE_ID --json | jq -r '.[0].description'
```

**Note:** `bd show` and `bd list` both return arrays. Always use `.[0]` to access the first element.

**Files Modified:**
- `prompts/coding_prompt.md` (line 107)
- `prompts/initializer_prompt.md` (line 68)

### 2. Hardcoded Project Path Assumptions

**Problem:**
```bash
ls: SmartAffirm/ClientApp: No such file or directory
```

Agent was making assumptions about project structure (e.g., `SmartAffirm/saUI`, `frontend/`, `src/`) without first discovering the actual structure.

**Root Cause:**
Prompts didn't emphasize that project structure should be discovered from `app_spec.txt` and the actual filesystem, not assumed.

**Fix Applied:**

Added explicit guidance in both prompts:

#### In coding_prompt.md (after Step 1):
```markdown
**CRITICAL - Discover Project Structure from app_spec.txt:**

The app_spec.txt may indicate the project structure. Look for:
- Directory paths (e.g., "frontend in ./src", "backend in ./api")
- Technology stack (React, Vue, Django, etc.)
- Build commands (npm, cargo, go build, etc.)

**DO NOT assume standard paths like:**
- ❌ `cd SmartAffirm/saUI` (hardcoded assumption)
- ❌ `cd frontend` (may not exist)
- ❌ `cd src` (may be different)

**Instead:**
1. Read app_spec.txt to understand project layout
2. Use `ls -la` to explore actual directory structure
3. Use `find . -name "package.json"` or similar to locate specific files
4. Infer paths from what you discover, never hardcode
```

#### In initializer_prompt.md (after reading app_spec):
```markdown
**CRITICAL - Understand Project Type from app_spec.txt:**

The app_spec.txt should indicate whether this is:
- **New/Greenfield Project:** Creating from scratch
- **Existing Project:** Fixing/enhancing existing code

The app_spec.txt may also indicate project structure:
- Directory paths
- Technology stack and build tools
- Existing codebase details

**DO NOT assume:**
- ❌ Project structure (don't hardcode paths)
- ❌ Whether it's new or existing
- ❌ Build commands (discover from package.json, etc.)
```

## Verification

After these fixes, the agent should:
1. ✅ Successfully parse BEADS issue descriptions without jq errors
2. ✅ Discover project structure from app_spec.txt instead of assuming
3. ✅ Use actual filesystem exploration before making path assumptions

## Related Issues

- Malware detection warning is NOT an error - it's a standard security reminder on every file read
- `Command 'X' is not in the allowed commands list` errors are expected security restrictions (blocked commands doc added separately)

## Testing

To verify the fix works:
1. Run autocode in a project with BEADS
2. Agent should successfully update issue descriptions
3. Agent should discover actual project structure instead of trying hardcoded paths

# Empty Spec File Behavior

## Question

**What happens if there are open issues in BEADS/Linear/GitHub but the spec file is empty?**

## Answer

Autocode will **detect and warn** about the empty spec file during startup validation.

### Startup Flow

1. **Detection Phase**
   ```
   ⚠️  WARNING: Spec file is empty: /path/to/app_spec.txt
   
   The spec file contains no requirements. Options:
     1. Add requirements to the spec file and run again
     2. Continue anyway (agent will only work on existing open issues)
   
     📋 Found 54 existing issues in task manager
        Agent can work on open issues without a spec file
   
   Continue with empty spec file? (y/n):
   ```

2. **User Chooses 'yes' (y)**
   - ✅ Agent proceeds to work on **existing open issues only**
   - ❌ Agent will **NOT** create new issues from spec
   - ❌ Spec change detection is **skipped**
   - Good for: bug fixes, backlog work, post-implementation maintenance

3. **User Chooses 'no' (n)**
   - ❌ Script exits gracefully
   - User should add requirements to spec file
   - Run autocode again after updating spec

## Use Cases

### ✅ Valid: Working on Existing Backlog
```
Scenario: Empty spec + 50 open issues in BEADS
Result: Agent works through existing 50 issues
Use for:
  - Fixing bugs in existing features
  - Completing partially done features
  - Working through technical debt
  - Post-audit bug fixes
```

### ✅ Valid: Maintenance Mode
```
Scenario: All 50 features implemented and closed
          New bugs found during testing
          Bugs added manually to BEADS
          Spec file is empty/unchanged
Result: Agent works on manually added bug issues
Use for:
  - Bug fixing phase after initial implementation
  - Iterative improvements
  - Production bug fixes
```

### ❌ Invalid: Fresh Project
```
Scenario: Empty spec + 0 issues
Result: Agent has nothing to do, will warn and exit
Solution: Add requirements to spec file first
```

## Best Practices

### Always Keep Spec Updated

The spec file is your **source of truth**. It should contain:

- **New features** you want to add
- **Changes** to existing features  
- **Clear acceptance criteria** for each feature
- **UI/UX requirements** and designs
- **Technical constraints** or architecture decisions

### When to Use Empty Spec

Empty spec is only appropriate when:

1. ✅ All spec requirements are fully implemented
2. ✅ You have existing open issues (bugs, improvements, etc.)
3. ✅ You want agent to focus ONLY on backlog, not new features

### When to Update Spec

Update spec when you want to:

1. ✅ Add new features to the application
2. ✅ Modify existing feature behavior
3. ✅ Change UI/UX design
4. ✅ Add new technical requirements

## Workflow Example

### Initial Development
```bash
# 1. Create spec with all requirements
vim app_spec.txt   # Add 50 features

# 2. Run autocode
autocode           # Creates 50 issues, implements them

# 3. All features done
# Status: 50 issues closed, spec unchanged
```

### Maintenance Phase
```bash
# 4. Testing reveals bugs, add them manually to BEADS
bd add "Fix login button not working on mobile"
bd add "Chat history not scrolling properly"

# 5. Empty the spec (features all done) or leave unchanged
# Status: 50 issues closed, 2 new bug issues open

# 6. Run autocode with empty/unchanged spec
autocode           # Detects empty spec, asks to continue
                   # Works on 2 bug issues

# Status: All 52 issues closed
```

### Adding New Features
```bash
# 7. Want to add new features
vim app_spec.txt   # Add: "51. Voice message support"
                   #      "52. Message reactions"

# 8. Run autocode
autocode           # Detects spec changes
                   # Creates 2 new issues
                   # Implements them

# Status: 54 issues total, all closed
```

## Technical Details

### Validation Logic

Located in: `autocode.py` → `resolve_config()` function

```python
# Check if spec file is empty or only whitespace
spec_content = spec_path.read_text().strip()
if not spec_content:
    # Warn user
    # Check for existing issues
    # Prompt to continue or exit
```

### Agent Behavior

When spec is empty:
- **Initializer session**: Skips spec change detection
- **Coding session**: Works only on open issues from task manager
- **Audit session**: Audits implemented features normally

### Task Manager Compatibility

Works with all task managers:
- **Linear**: Queries Linear API for open issues
- **GitHub Issues**: Queries via gh CLI for open issues  
- **BEADS**: Queries bd CLI for open issues

All adapters support "work on existing issues" mode.

## FAQ

**Q: Will the agent create new issues if spec is empty?**  
A: No. Empty spec = no new issues created.

**Q: Can I manually create issues and have agent work on them?**  
A: Yes! Use your task manager directly (bd, gh, Linear UI) to create issues.

**Q: What if I update spec later?**  
A: Run autocode again. It will detect changes and create new issues.

**Q: Does spec change detection work with empty spec?**  
A: It's skipped if spec is empty on first run. If spec was previously non-empty, changes will be detected.

**Q: Can I use empty spec for a brand new project?**  
A: Not recommended. You'll have no issues to work on. Add requirements to spec first.

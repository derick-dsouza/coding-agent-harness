# Migration Plan: Linear-Specific → Generic Task Management

## Overview

Convert all prompts and code from Linear-specific terminology to generic
task management terminology that works with any adapter (Linear, Jira, GitHub, etc.)

## Files to Update

### Core Task Management Module ✅ DONE

- [x] `task_management/interface.py` - Generic interface
- [x] `task_management/linear_adapter.py` - Linear implementation
- [x] `task_management/github_adapter.py` - GitHub implementation (CLI-based)
- [x] `task_management/beads_adapter.py` - BEADS implementation (CLI-based)
- [x] `task_management/factory.py` - Adapter factory
- [x] `task_management/__init__.py` - Public API
- [x] `task_management/TERMINOLOGY_MAPPING.md` - Mapping documentation
- [x] `task_management/PROMPT_GUIDELINES.md` - Prompt writing guide
- [x] `task_management/GITHUB_ADAPTER.md` - GitHub adapter documentation
- [x] `task_management/BEADS_ADAPTER.md` - BEADS adapter documentation

### Prompts to Update ⏳ TODO

1. **prompts/initializer_prompt.md**
   - Replace "Linear" with "task management system"
   - Replace "mcp__linear__*" references with generic descriptions
   - Use TODO/IN_PROGRESS/DONE instead of "Todo"/"In Progress"/"Done"
   - Use URGENT/HIGH/MEDIUM/LOW instead of 1-4
   - Update label creation section
   - Update META issue template

2. **prompts/coding_prompt.md**
   - Replace "Linear" terminology
   - Update issue update instructions
   - Use generic status/priority values
   - Update label workflow section

3. **prompts/audit_prompt.md**
   - Replace "Linear" references
   - Update issue querying instructions
   - Use generic terminology for status/labels

### Python Files to Update ⏳ TODO

1. **agent.py**
   - Import task_management module
   - Use generic adapter instead of hardcoded Linear
   - Update comments to be adapter-agnostic

2. **progress.py**
   - Update Linear-specific references
   - Use generic terminology in output

3. **autocode.py**
   - Add task adapter configuration
   - Update help text

### Configuration Files ⏳ TODO

1. **.autocode-config.example.json**
   - Add task_adapter_type field
   - Document adapter options

2. **README.md**
   - Update with task management abstraction info
   - Document supported adapters
   - Show configuration examples

### Documentation Files ⏳ TODO

1. **IMPLEMENTATION_SUMMARY.md**
   - Update with task management abstraction
   - Document adapter architecture

2. **AUDIT_SYSTEM.md**
   - Replace Linear-specific references
   - Use generic terminology

## Migration Strategy

### Phase 1: Core Infrastructure ✅ COMPLETE

- [x] Create task_management module
- [x] Implement generic interface
- [x] Implement Linear adapter
- [x] Create factory pattern
- [x] Write documentation

### Phase 2: Prompt Updates ⏳ NEXT

Update prompts to use generic terminology while maintaining compatibility:

**For each prompt file:**

1. **Find & Replace Linear-Specific Terms:**
   ```
   "Linear" → "task management system"
   "Linear project" → "project"
   "Linear issue" → "issue"
   "Linear label" → "label"
   "Linear team" → "team"
   ```

2. **Update MCP Tool References:**
   ```
   BEFORE: Use `mcp__linear__create_project` to create a Linear project
   AFTER:  Create a project in your task management system
   ```

3. **Update Status Values:**
   ```
   BEFORE: Set status to "In Progress"
   AFTER:  Set status to IN_PROGRESS
   ```

4. **Update Priority Values:**
   ```
   BEFORE: Set priority to 1 (urgent)
   AFTER:  Set priority to URGENT
   ```

5. **Add Adapter Note:**
   ```markdown
   **Note:** Your task management system may be Linear, Jira, GitHub Issues,
   or another platform. The workflow is the same regardless - the system
   handles the mapping automatically.
   ```

### Phase 3: Code Updates ⏳ PENDING

1. **Update agent.py:**
   ```python
   # OLD
   # Hardcoded Linear MCP tools
   
   # NEW
   from task_management import get_adapter_from_env
   adapter = get_adapter_from_env()
   ```

2. **Update progress.py:**
   - Use adapter.list_issues() instead of hardcoded Linear
   - Generic terminology in print statements

3. **Update autocode.py:**
   - Add `--task-adapter` CLI argument
   - Add task_adapter_type to config

### Phase 4: Testing ⏳ PENDING

1. Test with Linear adapter (ensure backward compatibility)
2. Verify all prompts use generic terminology
3. Ensure MCP tools still work through adapter
4. Test configuration options

### Phase 5: Documentation ⏳ PENDING

1. Update README with adapter architecture
2. Update IMPLEMENTATION_SUMMARY
3. Update AUDIT_SYSTEM docs
4. Create TASK_ADAPTERS.md guide

## Backward Compatibility

### Environment Variables

```bash
# Old (still works)
LINEAR_API_KEY=lin_api_...

# New (explicit)
TASK_ADAPTER_TYPE=linear
LINEAR_API_KEY=lin_api_...
```

### Configuration

```json
{
  // Old (implicit Linear)
  "spec_file": "app_spec.txt",
  
  // New (explicit adapter)
  "spec_file": "app_spec.txt",
  "task_adapter": "linear"
}
```

## Testing Checklist

- [ ] Linear adapter connects successfully
- [ ] Can create projects
- [ ] Can create issues with correct status mapping
- [ ] Can update issues
- [ ] Can create labels
- [ ] Can add comments
- [ ] Priority mapping works (URGENT → 1, etc.)
- [ ] Status mapping works (TODO → "Todo", etc.)
- [ ] Prompts don't mention "Linear" explicitly
- [ ] Prompts use generic terminology
- [ ] Documentation is adapter-agnostic

## Future: Adding New Adapters

Once prompts are generic, adding Jira/GitHub is straightforward:

1. Create `task_management/jira_adapter.py`
2. Implement TaskManagementAdapter interface
3. Map Jira terminology to generic terms
4. Add to factory.py
5. Test with existing prompts (no changes needed!)

**That's the beauty of this abstraction - prompts never need updating again!**

## Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Core Module | ✅ Done | task_management/ complete |
| Prompt Guidelines | ✅ Done | PROMPT_GUIDELINES.md |
| Terminology Map | ✅ Done | TERMINOLOGY_MAPPING.md |
| Prompts | ⏳ Next | 3 files to update |
| Python Code | ⏳ Pending | 3 files to update |
| Config | ⏳ Pending | 2 files to update |
| Docs | ⏳ Pending | 3 files to update |
| Testing | ⏳ Pending | After code updates |

**Next Step:** Update prompts/initializer_prompt.md to use generic terminology

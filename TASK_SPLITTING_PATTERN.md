# BEADS Task Splitting Pattern

## Problem with Initial Splitting
The original task splitting created independent subtasks that don't automatically share results with parent tasks. This leads to:
- Subtasks work in isolation
- No result aggregation mechanism
- Parent tasks can't automatically process findings
- Manual coordination required

## Proper Splitting Pattern

### 1. Subtasks MUST Store Results
Each subtask should:
- Store findings in a shared location (e.g., `docs/research_results.md`)
- Create structured data files (YAML/JSON) for programmatic access
- Include clear reference to parent task in description
- Use consistent file naming and section organization

### 2. Parent Tasks MUST Process Results
Each parent task should:
- Wait for all subtasks to complete
- Read stored results from designated files
- Consolidate and analyze findings
- Generate actionable outputs for next phase
- Update original parent task with consolidated results

### 3. Task Labels for Coordination
- `stores-results`: Subtask stores findings
- `coordination`: Parent task processes results
- `implements`: Implementation task creating components
- `integrates`: Integration task connecting components

### 4. Example Pattern

**Subtask Example:**
```
Title: Phase 1.2a: Research X AND store findings
Labels: [research, stores-results]
Body: 
- Research X 
- STORE FINDINGS in docs/research.md under "X Research" section
- Create YAML data in data/x_findings.yaml
- Reference parent task AGENT_SDK_AUTH-78x
```

**Parent Task Example:**
```
Title: Phase 1.2-parent: Consolidate research findings
Labels: [coordination]
Body:
- Wait for subtasks to complete
- READ docs/research.md findings
- READ data/*.yaml structured data
- CONSOLIDATE into comprehensive document
- UPDATE original parent task AGENT_SDK_AUTH-78x
```

### 5. File Structure for Results
```
docs/
├── codex_auth_research.md     # Research findings
├── gemini_auth_research.md     # Research findings
└── auth_implementation_guide.md # Implementation guidance

data/
├── codex_findings.yaml        # Structured data
├── gemini_findings.yaml       # Structured data
└── auth_config_schema.yaml    # Configuration schema
```

### 6. Result Storage Format

**Markdown Section Format:**
```markdown
## Device Code OAuth Research

### Status: ✅ Complete | ❌ Not Available | ⚠️ Limited

### Findings:
- Command: `codex auth login --device-code`
- Process: [Step-by-step documentation]
- Limitations: [Any constraints]
- Automation: [Manual/Partial/Fully automatable]

### Test Results:
- Success: [Yes/No]
- Error Messages: [Any errors encountered]
- Output Sample: [Example outputs]
```

**YAML Structured Format:**
```yaml
codex_auth:
  device_code_oauth:
    available: true
    command: "codex auth login --device-code"
    automation_possible: false
    limitations: ["Requires browser", "Manual confirmation"]
    token_storage: "config file"
    env_var: "CODEX_OAUTH_TOKEN"
```

This pattern ensures task splitting actually improves parallelization while maintaining coordination and result aggregation.

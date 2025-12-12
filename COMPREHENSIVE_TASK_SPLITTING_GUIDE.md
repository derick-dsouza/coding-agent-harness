# Comprehensive Task Splitting Guide for BEADS

## Executive Summary

This guide provides a systematic approach for agents to create atomic, low-complexity tasks in BEADS that can be safely parallelized while maintaining coordination and result aggregation.

## Why Task Splitting is Critical

### Benefits of Proper Splitting
1. **Parallelization**: Multiple agents can work simultaneously
2. **Reduced Cognitive Load**: Each task has single, clear focus
3. **Faster Delivery**: Smaller tasks can be completed quickly
4. **Better Estimation**: Low-complexity tasks are easier to estimate
5. **Reduced Risk**: Failure of one task doesn't block others

### Risks of Poor Splitting
1. **Coordination Overhead**: Tasks can't find each other's results
2. **Duplicate Work**: Multiple teams implement the same thing
3. **Integration Hell**: Components don't fit together
4. **Lost Results**: Findings aren't preserved for parent tasks
5. **Broken Dependencies**: Subtasks assume parent is complete

## The Task Splitting Pattern

### 1. Identification Criteria

Split a task if it meets ANY of these criteria:
- **Multiple Implementation Areas**: Involves config, code, docs, tests
- **Multiple SDKs**: Affects Codex, Gemini, Claude, etc.
- **Multiple Components**: Requires config + adapter + validation
- **Complex Implementation**: >3 distinct implementation steps
- **Research + Implementation**: Mixed discovery and building work

### 2. Splitting Categories

#### A. Research Tasks
**Pattern**: Break by authentication method/functionality
```
Parent: Research Codex CLI auth modes
├── Subtask 1: Device code OAuth research
├── Subtask 2: Direct OAuth research  
├── Subtask 3: API key research
├── Subtask 4: CLI commands inventory
└── Subtask 5: Token storage research
```

#### B. Implementation Tasks
**Pattern**: Break by component/architectural layer
```
Parent: Implement Codex OAuth flow
├── Subtask 1: Login helper function
├── Subtask 2: Token capture & storage
├── Subtask 3: Expiration & refresh logic
└── Subtask 4: Adapter integration
```

#### C. Configuration Tasks
**Pattern**: Break by config component
```
Parent: Extend config schema for auth
├── Subtask 1: Auth type fields
├── Subtask 2: Environment variable mapping
├── Subtask 3: Validation rules
└── Subtask 4: Default values
```

#### D. Testing Tasks
**Pattern**: Break by test type/scenario
```
Parent: Write auth resolution tests
├── Subtask 1: Token present scenarios
├── Subtask 2: Token missing scenarios
├── Subtask 3: Proxy enabled scenarios
├── Subtask 4: Simulation mode scenarios
└── Subtask 5: Integration test scenarios
```

### 3. Subtask Requirements

Every subtask MUST:

#### A. Store Results
- **File Location**: Store in designated shared location
- **Format**: Use standardized format (see Section 4)
- **Reference**: Mention parent task in description
- **Accessibility**: Results readable by parent task

#### B. Include Implementation
- **Working Code**: Provide functional implementation
- **Tests**: Include unit/integration tests
- **Documentation**: Document usage and behavior
- **Location**: Store in designated directory structure

#### C. Provide Clear Boundaries
- **Single Focus**: One clear responsibility
- **Dependencies**: Clear statement of what it depends on
- **Deliverables**: Specific output expectations

### 4. Result Storage Architecture

#### A. Directory Structure
```
project/
├── docs/
│   ├── codex_auth_research.md      # Research findings
│   ├── gemini_auth_research.md    # Research findings
│   ├── auth_configuration.md      # Implementation guidance
│   └── auth_troubleshooting.md   # Troubleshooting info
├── data/
│   ├── codex_findings.yaml        # Structured research data
│   ├── gemini_findings.yaml       # Structured research data
│   ├── auth_config_schema.yaml    # Configuration schema
│   └── auth_test_scenarios.yaml   # Test scenarios
├── src/
│   ├── auth/
│   │   ├── codex_auth.py         # Codex auth implementation
│   │   ├── gemini_auth.py        # Gemini auth implementation
│   │   ├── auth_resolver.py       # Shared auth resolver
│   │   ├── proxy_config.py        # Proxy configuration
│   │   └── auth_diagnostics.py   # Diagnostics
│   └── adapters/
│       ├── codex_adapter.py       # Codex adapter
│       └── gemini_adapter.py      # Gemini adapter
└── tests/
    ├── test_auth_resolver.py      # Auth resolver tests
    ├── test_codex_auth.py         # Codex auth tests
    └── test_gemini_auth.py        # Gemini auth tests
```

#### B. Standardized Formats

**Research Results (Markdown)**:
```markdown
## Device Code OAuth Research

### Status: ✅ Available | ❌ Not Available | ⚠️ Limited

### Findings:
- **Command**: `codex auth login --device-code`
- **Process**: [Step-by-step description]
- **Automation**: Manual/Partial/Fully automatable
- **Limitations**: [Any constraints]

### Test Results:
- **Success**: [Yes/No]
- **Errors**: [Error messages encountered]
- **Output**: [Example outputs]
```

**Structured Data (YAML)**:
```yaml
codex_auth:
  device_code_oauth:
    available: true
    command: "codex auth login --device-code"
    automation_possible: false
    limitations: 
      - "Requires browser"
      - "Manual confirmation"
    token_storage: "config file"
    env_var: "CODEX_OAUTH_TOKEN"
    implementation_files:
      - "src/auth/codex_auth.py"
      - "src/adapters/codex_adapter.py"
```

**Configuration Schema (YAML)**:
```yaml
auth_config:
  codex:
    auth_type: 
      type: string
      enum: ["oauth", "api_key", "proxy", "simulation"]
      default: "simulation"
    use_cli_proxy:
      type: boolean
      default: false
    oauth_token_env:
      type: string
      default: "CODEX_OAUTH_TOKEN"
```

### 5. Parent Task Requirements

Every parent coordination task MUST:

#### A. Wait for Completion
- List all subtask IDs
- Check completion status
- Handle missing/failed subtasks

#### B. Aggregate Results
- Read all stored results
- Parse structured data
- Consolidate findings
- Identify conflicts/gaps

#### C. Create Integration
- Combine components
- Test end-to-end flow
- Resolve integration issues
- Document integration approach

#### D. Update Original
- Report back to original parent task
- Include integration status
- Provide next phase recommendations
- Link to all delivered artifacts

### 6. Task Creation Template

#### Subtask Template
```
Title: Phase X.Ya: [Specific component] AND store findings
Labels: [component-type, sdk, stores-results]
Body: 
IMPLEMENT [specific component] AND STORE RESULTS:
1) Implement [detailed functionality]
2) Store implementation in [file path]
3) Store findings in [docs location]
4) Create/update structured data in [data location]
5) Add tests for [functionality]
6) Reference parent task [parent ID]
```

#### Parent Coordination Template
```
Title: Phase X.Y-parent: Integrate [feature] components
Labels: [coordination, component-type]
Body: 
PARENT TASK - INTEGRATES ALL COMPONENTS:
1) Wait for subtasks [list of subtask IDs] to complete
2) READ stored implementations from [src paths]
3) READ findings from [docs paths]
4) READ structured data from [data paths]
5) INTEGRATE all components into working [feature]
6) TEST complete [feature] flow end-to-end
7) UPDATE original parent task [original parent ID] with status
```

### 7. Agent Responsibilities

#### Task Creation Agent
1. **Analyze Complexity**: Identify tasks needing splitting
2. **Apply Pattern**: Use correct splitting category
3. **Create Coordination**: Include parent coordination tasks
4. **Verify Storage**: Ensure result storage mechanisms
5. **Set Dependencies**: Clear dependency chains

#### Implementation Agent
1. **Read Requirements**: Understand scope and boundaries
2. **Store Results**: Use designated locations and formats
3. **Follow Standards**: Maintain consistent patterns
4. **Include Tests**: Provide adequate test coverage
5. **Document Changes**: Update relevant documentation

#### Coordination Agent
1. **Monitor Progress**: Track subtask completion
2. **Aggregate Results**: Collect and analyze all stored data
3. **Integrate Components**: Combine implementations
4. **Validate Integration**: Test complete functionality
5. **Report Status**: Update parent tasks with outcomes

## Current Splitting Status

### ✅ Completed Splits
- **Phase 1.2** (Codex Research): 5 subtasks + 1 parent coordination
- **Phase 1.3** (Gemini Research): 5 subtasks + parent coordination (template ready)
- **Phase 2.1** (Codex OAuth): 4 subtasks + parent coordination (template ready)
- **Phase 3.1** (Gemini OAuth): 4 subtasks + parent coordination (template ready)
- **Phase 2.2** (Codex CLIProxy): 6 subtasks + 1 parent coordination ✅
- **Phase 3.2** (Gemini API Key): 5 subtasks + 1 parent coordination ✅

### 🔄 Remaining Tasks to Split
- **Phase 2.3** (Codex Adapter Enforcement)
- **Phase 3.3** (Gemini CLIProxy) 
- **Phase 3.4** (Gemini Adapter Enforcement)
- **Phase 4.2** (Config Schema Extension)
- **Phase 4.3** (Auth Diagnostics)
- **Phase 5.1** (Codex Adapter Wiring)
- **Phase 5.2** (Gemini Adapter Wiring)
- **Phase 5.3** (Simulation Mode)
- **Phase 6.1** (Unit Tests)
- **Phase 6.2-6.4** (Integration Tests)
- **Phase 7.1-7.3** (Documentation)
- **Phase 8.1-8.3** (Rollout Safety)

## Quick Reference Checklist

### Before Splitting
- [ ] Task involves multiple components/configs?
- [ ] Task affects multiple SDKs?
- [ ] Task has >3 distinct steps?
- [ ] Task mixes research + implementation?

### After Splitting
- [ ] Each subtask has single focus?
- [ ] Subtasks store results in designated locations?
- [ ] Parent coordination task created?
- [ ] Result storage architecture defined?
- [ ] Dependency chain clear?

### During Implementation
- [ ] Using standardized file locations?
- [ ] Following data format standards?
- [ ] Including adequate tests?
- [ ] Updating relevant documentation?
- [ ] Referencing parent tasks correctly?

## Implementation Examples

### Example 1: Research Task Splitting
**Original**: "Research Codex CLI auth modes"

**Split Into**:
1. "Check Codex device-code OAuth AND store findings"
2. "Check Codex direct OAuth AND store findings"
3. "Check Codex API key auth AND store findings"
4. "Identify Codex CLI auth commands AND store findings"
5. "Determine Codex token storage AND store findings"
6. "Consolidate Codex auth research findings" (coordination)

### Example 2: Implementation Task Splitting
**Original**: "Implement Codex CLIProxy fallback"

**Split Into**:
1. "Add codex.use_cli_proxy config key AND store schema"
2. "Implement CLI_PROXY_URL handling AND store implementation"
3. "Implement proxy token handling AND store implementation"
4. "Modify Codex adapter for proxy AND store implementation"
5. "Implement OAuth to proxy fallback AND store implementation"
6. "Add proxy mode diagnostics AND store implementation"
7. "Integrate Codex CLIProxy components" (coordination)

## Conclusion

This systematic approach to task splitting ensures:
- **True parallelization** without coordination overhead
- **Result preservation** for parent task consumption
- **Clear architecture** for component integration
- **Consistent standards** across all implementation work
- **Reduced risk** through smaller, focused tasks

Agents should use this guide as a reference whenever tasked with breaking down complex work into atomic BEADS tasks.

# App Spec Templates

This directory contains templates and guides for creating project specifications that work with the autonomous coding agent.

## Files

### `app_spec_template.txt`
The master template for creating comprehensive project specifications. This template is based on deep analysis of the successful Claude.ai Clone specification.

**Key Features:**
- XML-style structure for clarity and parsing
- Comprehensive sections covering all aspects of an application
- Placeholder text with examples to guide users
- Comments with additional guidance and common patterns

### `TEMPLATE_GUIDE.md`
Complete guide on how to use the template effectively, including:
- Philosophy and principles behind the template
- Step-by-step walkthrough of each section
- Patterns and best practices
- Examples of well-specified features
- Troubleshooting common issues
- Integration with the coding agent

## Quick Start

1. **Copy the template to your project:**
   ```bash
   autospec /path/to/your/project
   ```

2. **Read the guide:**
   ```bash
   cat ~/Projects/development/coding-agent-harness/templates/TEMPLATE_GUIDE.md
   ```

3. **Fill out the template systematically:**
   - Start with project name and overview
   - Define technology stack
   - List all features in categories
   - Map features to database schema
   - Document API endpoints
   - Describe UI and design system
   - Break into implementation steps
   - Define success criteria

4. **Run the coding agent:**
   ```bash
   cd /path/to/your/project
   autocode
   ```

## Template Design Principles

The template follows these core principles derived from analyzing successful specifications:

### 1. Structure
- **Hierarchical organization** - Clear parent-child relationships
- **Semantic tags** - Names that describe content
- **Consistent nesting** - Predictable structure throughout

### 2. Content
- **Action-oriented** - Features described with verbs
- **Comprehensive** - All aspects of the application covered
- **Cross-referenced** - Sections align and reference each other
- **Implementation-ready** - Enough detail for autonomous coding

### 3. Language
- **Present tense** for features ("User can upload photos")
- **Imperative mood** for tasks ("Create database schema")
- **Precise vocabulary** - No ambiguous terms
- **Explicit specifications** - Package names, versions, ports

### 4. Organization
- **Overview first** - What and why before how
- **Technology stack** - Tools and frameworks
- **Features** - Detailed functionality
- **Data structures** - Database schema
- **Interfaces** - API endpoints
- **Presentation** - UI/UX details
- **Implementation** - Step-by-step plan
- **Validation** - Success criteria

## Common Section Guide

| Section | Purpose | Required? |
|---------|---------|-----------|
| project_name | Identifies the application | ✅ Required |
| overview | Describes what and why | ✅ Required |
| technology_stack | Lists all technical choices | ✅ Required |
| prerequisites | Environment setup needs | ✅ Required |
| core_features | Detailed functionality list | ✅ Required |
| database_schema | Data structure definition | ✅ Required for data apps |
| api_endpoints_summary | All API contracts | ✅ Required for web apps |
| ui_layout | Interface structure | ✅ Required for UI apps |
| design_system | Visual language | ⚠️ Recommended |
| key_interactions | User flow documentation | ⚠️ Recommended |
| implementation_steps | Phased development plan | ✅ Required |
| success_criteria | Validation metrics | ✅ Required |
| notes | Additional context | ⚠️ Optional |

## Examples

### Minimal Spec (CLI Tool)
```xml
<project_specification>
  <project_name>Git Stats Analyzer</project_name>
  <overview>CLI tool to analyze git repository statistics</overview>
  <technology_stack>
    <language>Python 3.11</language>
    <libraries>
      - gitpython for git operations
      - click for CLI interface
      - pandas for data analysis
      - matplotlib for visualizations
    </libraries>
  </technology_stack>
  <core_features>
    - Parse git log for commit history
    - Calculate lines changed per author
    - Generate contribution graphs
    - Export stats to CSV
  </core_features>
  <implementation_steps>...</implementation_steps>
  <success_criteria>...</success_criteria>
</project_specification>
```

### Full Spec (Web Application)
Uses all sections from the template for comprehensive web applications with frontend, backend, database, and complex features.

See `app_spec_template.txt` for the complete structure.

## Integration with Coding Agent

The coding agent uses your spec to:

1. **Parse the specification** - Extract features and requirements
2. **Generate issues** - Create tasks in Linear/BEADS/GitHub
3. **Implement systematically** - Follow implementation steps
4. **Validate against criteria** - Check success conditions
5. **Handle ambiguity** - Make reasonable decisions with explicit guidance

### Agent Behavior

**When spec is clear:**
- Agent implements features directly
- Makes standard technical decisions
- Follows best practices

**When spec is ambiguous:**
- Agent makes assumptions based on context
- Documents decisions in code comments
- May add notes to issues

**When spec is incomplete:**
- Agent implements what's specified
- May flag missing information in issue comments
- Continues with reasonable defaults

## Best Practices

### DO ✅
- Be specific about versions and packages
- List features as actionable items
- Include error handling requirements
- Define validation rules explicitly
- Specify data relationships clearly
- Document user flows step-by-step

### DON'T ❌
- Leave placeholders unfilled
- Use vague terms like "user-friendly" or "fast"
- Mix different concerns in one feature
- Forget to align features with schema
- Skip success criteria
- Over-specify implementation details

## Version History

- **v1.0** (2025-12-11) - Initial template based on Claude.ai Clone spec analysis
  - Comprehensive sections for full-stack web applications
  - Inline guidance and examples
  - Integration with autonomous coding agent

## Contributing

To improve the template:

1. Identify patterns from successful specs
2. Extract reusable structure
3. Add to template with guidance
4. Update TEMPLATE_GUIDE.md with examples
5. Test with autonomous coding agent

## Support

For questions or issues with the template:

1. Check TEMPLATE_GUIDE.md for detailed instructions
2. Review example sections in the template
3. Refer to generations/autonomous_demo_project/app_spec.txt for real-world example
4. Experiment with the coding agent and iterate on your spec

---

**Remember:** A well-crafted spec is the foundation of successful autonomous development!

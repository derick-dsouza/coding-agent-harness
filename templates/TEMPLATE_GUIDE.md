# App Spec Template Guide

## Quick Start

### 1. Copy the Template

```bash
# From your project directory
autospec

# Or specify a target directory
autospec /path/to/your/project
```

This creates `app_spec.txt` in your target directory.

### 2. Fill Out the Template

Open `app_spec.txt` and replace all `{{PLACEHOLDER}}` values with your project details.

**Pro tip:** Search for `{{` to find all placeholders quickly.

### 3. Remove Unused Sections

Delete any sections that don't apply to your project. The template is comprehensive, but not every project needs every section.

### 4. Run Autocode

```bash
cd /path/to/your/project
python /path/to/coding-agent-harness/autocode.py
```

---

## Why XML Format?

The template uses XML for several key reasons:

### 1. **Hierarchical Structure**
```xml
<project_specification>
  <core_features>
    <authentication>
      <requirements>
        - Login form
        - Password reset
      </requirements>
    </authentication>
  </core_features>
</project_specification>
```
AI agents can easily parse nested relationships and understand feature groupings.

### 2. **Clear Boundaries**
XML tags provide explicit section boundaries, making it easier for agents to:
- Extract specific sections
- Navigate the document structure
- Understand relationships between sections

### 3. **Validation Capability**
XML can be validated against schemas, ensuring consistency across projects.

### 4. **Tool Support**
XML is widely supported by parsing libraries and tools, making it easy to:
- Extract data programmatically
- Transform into other formats
- Validate structure

### 5. **Natural Language + Structure**
The template combines:
- **XML tags** for structure and navigation
- **Natural language** in content for clarity
- **Examples and comments** for guidance

This hybrid approach works well with LLMs that excel at both structured data and natural language understanding.

---

## Template Philosophy

### Design Principles

1. **Explicit Over Implicit**
   - State requirements clearly, don't assume
   - Include examples for complex concepts
   - Specify exact behaviors

2. **Implementation-Focused**
   - Technical details, not just business requirements
   - Include data types, API methods, UI details
   - Specify error handling and edge cases

3. **Hierarchical Organization**
   - Group related features together
   - Use consistent nesting levels
   - Make dependencies clear

4. **Success-Oriented**
   - Define what "done" looks like
   - Include measurable criteria
   - Specify quality standards

5. **Iterative-Friendly**
   - Break into logical phases
   - Each phase builds on previous
   - Clear deliverables per phase

---

## Resources

### Example Specs
- **Demo project:** `generations/autonomous_demo_project/app_spec.txt`
  A complete, production-ready spec for a Claude.ai clone

### Related Documentation
- `README.md` - Overall system documentation
- `WORKFLOW.md` - How the coding agent works
- `SPEC_FILE_FORMATS.md` - Spec file format details
- `TASK_ADAPTER_ARCHITECTURE.md` - Task management system

---

## Checklist Before Running Autocode

- [ ] Project name is set
- [ ] Overview describes the project clearly
- [ ] Technology stack is fully specified
- [ ] All environment variables are documented
- [ ] Database schema is complete
- [ ] API endpoints are documented with request/response formats
- [ ] Core features have detailed requirements
- [ ] UI layout is described for major screens
- [ ] Key user workflows are documented step-by-step
- [ ] Implementation phases are defined logically
- [ ] Success criteria are specific and measurable
- [ ] All {{PLACEHOLDER}} values are replaced
- [ ] Unused sections are removed
- [ ] Spec has been reviewed for completeness

---

Happy building! 🚀

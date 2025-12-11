# App Spec Template System

## Overview

A comprehensive XML-based template system for defining application specifications that work optimally with AI coding agents.

## Created Files

### 1. `/templates/app_spec_template.xml`
- **33,000+ character comprehensive template**
- Hierarchical XML structure for clear organization
- Inline examples and guidance throughout
- Placeholder system: Replace `{{PLACEHOLDER}}` values
- Covers all aspects of software projects

### 2. `/templates/TEMPLATE_GUIDE.md`
- Quick start guide
- XML format rationale
- Template philosophy and principles
- Best practices and examples
- Checklist for completion

### 3. `/templates/README.md`
- Directory overview
- Quick reference
- Links to detailed docs

## Using the Template

### Quick Start

```bash
# In your project directory
autospec

# Or specify path
autospec /path/to/project
```

This creates `app_spec.txt` with the full XML template.

### Workflow

1. **Copy template** - Run `autospec` command
2. **Fill placeholders** - Replace all `{{PLACEHOLDER}}` values
3. **Customize** - Remove unused sections, add project-specific ones
4. **Run autocode** - Execute `python autocode.py` to start implementation

## Why XML?

### Advantages for AI Agents

1. **Hierarchical Structure** - Clear nesting and relationships
2. **Explicit Boundaries** - Tags define section starts/ends
3. **Parser-Friendly** - Easy to extract specific sections
4. **Validation** - Can validate structure programmatically
5. **Natural Language** - Content within tags remains human-readable

### Hybrid Approach

The template combines:
- **XML tags** for structure and navigation
- **Natural language** for requirements and descriptions
- **Examples** inline for clarity
- **Comments** for guidance

This works well with LLMs that excel at both structured data and natural language.

## Template Structure

### Core Sections

1. **Project Identity**
   - Project name
   - Comprehensive overview
   - Value proposition

2. **Technology Stack**
   - Frontend framework and tooling
   - Backend runtime and framework
   - Database and ORM
   - API integrations
   - Authentication method
   - Ports and infrastructure

3. **Prerequisites**
   - Environment variables
   - System requirements
   - Setup instructions

4. **Core Features**
   - Feature groups by functional area
   - Detailed requirements with UI/UX specs
   - Validation rules and error handling
   - Edge cases

5. **Database Schema**
   - All tables/collections
   - Fields with types and constraints
   - Foreign keys and relationships
   - Indexes

6. **API Endpoints**
   - Grouped by resource
   - Request/response formats
   - Status codes and errors
   - Authentication requirements

7. **UI Layout**
   - Overall structure
   - Navigation
   - Key screens
   - Modals and overlays

8. **Design System**
   - Color palette
   - Typography
   - Spacing scale
   - Component styles
   - Animations

9. **Key Interactions**
   - User workflows step-by-step
   - Edge cases and error handling

10. **Implementation Phases**
    - Logical sequential phases
    - Tasks per phase
    - Dependencies
    - Deliverables

11. **Success Criteria**
    - Functionality requirements
    - User experience standards
    - Technical quality benchmarks
    - Design polish criteria
    - Accessibility requirements
    - Performance metrics
    - Security standards

### Optional Sections

- Testing Strategy
- Deployment & Infrastructure
- Documentation Requirements
- Constraints & Considerations
- Future Enhancements

## Template Philosophy

### Design Principles

1. **Explicit Over Implicit** - State requirements clearly
2. **Implementation-Focused** - Include technical details
3. **Hierarchical Organization** - Group related features
4. **Success-Oriented** - Define measurable completion criteria
5. **Iterative-Friendly** - Break into logical phases

### Best Practices

#### ✅ Good Specifications

- Specific dimensions and sizes
- Exact validation rules (with regex)
- UI element placement described
- Complete error handling
- Security considerations
- User feedback clearly defined

Example:
```xml
<user_profile>
  <requirements>
    - Display user avatar (150x150px, circular)
    - Edit button (top-right, orange) opens inline editing
    - Validate email: ^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$
    - Auto-save after 3 seconds (debounced)
    - Max avatar size: 5MB, formats: JPG/PNG/WebP
    - Success toast: "Profile updated successfully"
    - Only user can edit own profile (403 for others)
  </requirements>
</user_profile>
```

#### ❌ Avoid Vagueness

- "User can edit profile" (what fields?)
- "Validation should work" (what rules?)
- "Show errors" (where, how, which errors?)

## Integration with Autocode

### Detection Flow

1. Template copied to project directory as `app_spec.txt`
2. User fills in placeholders and requirements
3. Run `autocode.py` to initialize project
4. Agent reads spec and creates issues in task manager
5. Agent implements features based on spec details

### Iterative Updates

1. Modify `app_spec.txt` to add/change features
2. Run `./work-on-project.sh detect` to detect changes
3. New issues created for added/modified features
4. Run `./work-on-project.sh run` to implement

## Example: Demo Project

Location: `generations/autonomous_demo_project/app_spec.txt`

**Project:** Claude.ai Clone - AI Chat Interface
- **Size:** ~700 lines of detailed specifications
- **Result:** 54 fully implemented features
- **Quality:** Grade A audit (100% pass rate)

This demonstrates the template's effectiveness in guiding comprehensive implementations.

## Shell Alias

### Updated Alias

```bash
autospec() {
    local target="${1:-.}"
    cp /path/to/templates/app_spec_template.xml "$target/app_spec.txt"
    echo "✅ Copied app_spec.txt template to: $target/"
    echo "📝 Edit the file and replace all {{PLACEHOLDER}} values"
    echo "📖 See template comments for detailed instructions"
}
```

### Usage

```bash
# In project directory
autospec

# Specify target
autospec ~/projects/my-app

# Then edit app_spec.txt
```

## Benefits

### For Users

- **Structured approach** to defining requirements
- **Comprehensive coverage** of all project aspects
- **Clear guidance** with examples throughout
- **Consistency** across projects
- **Better results** from AI agents

### For AI Agents

- **Hierarchical parsing** via XML structure
- **Clear section boundaries** for extraction
- **Detailed context** for implementation decisions
- **Success criteria** for validation
- **Phase organization** for sequential work

## Future Enhancements

### Potential Additions

1. **XML Schema Definition (XSD)** - Validate spec structure
2. **Template Variations** - Specialized templates for web/mobile/CLI/API
3. **Interactive Wizard** - Guide users through filling template
4. **Spec Validation Tool** - Check completeness before running
5. **Example Library** - More complete example specs

### Template Evolution

The template can evolve based on:
- User feedback
- Agent performance patterns
- New project types
- Best practice discoveries

## Related Documentation

- `README.md` - Overall system documentation
- `WORKFLOW.md` - How the coding agent works
- `SPEC_FILE_FORMATS.md` - Spec format details
- `TASK_ADAPTER_ARCHITECTURE.md` - Task management
- `templates/TEMPLATE_GUIDE.md` - Detailed usage guide
- `templates/README.md` - Templates directory overview

## Summary

The XML app spec template system provides:

✅ **Comprehensive structure** for defining application requirements
✅ **AI-optimized format** for better agent understanding
✅ **Natural language content** within structured tags
✅ **Inline examples and guidance** throughout
✅ **Flexible and customizable** for any project type
✅ **Production-proven** with demo project results

This system transforms vague ideas into detailed, actionable specifications that AI coding agents can implement successfully.

---

**Created:** December 2024
**Status:** Production Ready
**Example:** See `generations/autonomous_demo_project/app_spec.txt`

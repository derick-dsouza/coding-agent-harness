# App Spec Template System

## Overview

The app spec template system provides a structured, comprehensive template for creating project specifications that work seamlessly with the autonomous coding agent. The template is based on deep analysis of the successful Claude.ai Clone specification.

## Files Created

### 1. `templates/app_spec_template.txt`
**Purpose:** Master template for all new projects

**Features:**
- XML-style hierarchical structure for clarity
- Comprehensive sections covering all aspects of a full-stack application
- Inline guidance with `[placeholder]` examples
- Comments explaining common patterns and best practices
- 11,651 characters of structured guidance

**Sections:**
- `<project_name>` - Project identification
- `<overview>` - What, why, who, and high-level functionality
- `<technology_stack>` - Frontend, backend, communication choices
- `<prerequisites>` - Environment setup requirements
- `<core_features>` - Detailed feature categorization
- `<database_schema>` - Data structure definitions
- `<api_endpoints_summary>` - All API contracts
- `<ui_layout>` - Interface structure and components
- `<design_system>` - Visual language and styling
- `<key_interactions>` - User flow documentation
- `<implementation_steps>` - Phased development plan
- `<success_criteria>` - Validation across 4 dimensions
- `<notes>` - Additional context (optional)

### 2. `templates/TEMPLATE_GUIDE.md`
**Purpose:** Complete usage guide for the template

**Contents:**
- Template philosophy and design principles
- Step-by-step walkthrough of each section
- Patterns and best practices for feature specification
- Examples of well-specified features
- Troubleshooting common issues
- Integration guide with autonomous coding agent
- 12,775 characters of detailed documentation

**Key Sections:**
- How to use the template effectively
- Feature definition patterns (good vs bad examples)
- Database schema patterns
- API endpoint patterns
- Implementation task patterns
- Tips for agent-friendly specs
- Examples of comprehensive features

### 3. `templates/README.md`
**Purpose:** Quick reference and onboarding

**Contents:**
- Quick start instructions
- Design principles summary
- Section reference table (required vs optional)
- Minimal vs full spec examples
- Common section guide
- Best practices checklist
- Integration with coding agent
- 6,720 characters of quick reference

## Usage Workflow

### Starting a New Project

```bash
# 1. Navigate to your project directory
cd /path/to/your/new/project

# 2. Initialize with template
autospec

# 3. Review the guide
cat ~/Projects/development/coding-agent-harness/templates/TEMPLATE_GUIDE.md

# 4. Fill out your spec
vim app_spec.txt
# Replace all [placeholders] with your project details
# Remove unused sections
# Add custom sections as needed

# 5. Review for completeness
# ✓ All placeholders filled?
# ✓ Features align with database schema?
# ✓ API endpoints match features?
# ✓ Implementation steps are logical?
# ✓ Success criteria defined?

# 6. Initialize project with task manager
autocode
# Agent will:
# - Parse your spec
# - Create issues in task manager
# - Begin implementation
```

### The `autospec` Alias

Updated to use the new template system:

```bash
autospec() {
    local target="${1:-.}"
    cp /Users/derickdsouza/Projects/development/coding-agent-harness/templates/app_spec_template.txt "$target/app_spec.txt"
    echo "✅ Copied app_spec template to: $target/app_spec.txt"
    echo "📖 See templates/TEMPLATE_GUIDE.md for usage instructions"
}
```

**Usage:**
```bash
autospec              # Copy to current directory
autospec .            # Same as above
autospec /path/to/dir # Copy to specific directory
```

## Template Design Principles

### 1. Structure
Based on analysis of the Claude.ai Clone spec:
- **XML-style tags** - `<section_name>content</section_name>`
- **Hierarchical nesting** - Clear parent-child relationships
- **Semantic naming** - Tags describe their content (snake_case)
- **Consistent indentation** - 2 spaces per level

### 2. Content Organization
Follows a logical flow from high-level to implementation:
1. **Overview** → What and why
2. **Technology** → How and with what
3. **Features** → Detailed what
4. **Data** → Database schema
5. **Interfaces** → API endpoints
6. **Presentation** → UI/UX
7. **Design** → Visual system
8. **Interactions** → User flows
9. **Implementation** → Step-by-step plan
10. **Validation** → Success criteria

### 3. Language Patterns
Precise and unambiguous:
- **Present tense** for features: "User can upload photos"
- **Imperative mood** for tasks: "Create database schema"
- **Action verbs** throughout: upload, validate, display, implement
- **Technical precision** - Package names, versions, ports explicitly stated

### 4. Cross-Referencing
Sections reference and align with each other:
- Features → mentioned in database schema
- Database schema → used by API endpoints
- API endpoints → called by UI components
- UI components → described in UI layout
- Everything → grouped in implementation steps
- All → validated in success criteria

## Integration with Autonomous Coding Agent

### How the Agent Uses Your Spec

1. **Parsing Phase**
   - Reads XML structure
   - Extracts features from `<core_features>`
   - Identifies technology stack
   - Notes prerequisites

2. **Issue Generation Phase**
   - Creates task manager issues for each feature
   - Groups by `<implementation_steps>`
   - Tags with appropriate labels
   - Links related issues

3. **Implementation Phase**
   - Works through issues systematically
   - References spec for implementation details
   - Makes decisions based on technology stack
   - Follows patterns from spec examples

4. **Validation Phase**
   - Tests against `<success_criteria>`
   - Verifies all features implemented
   - Checks quality across 4 dimensions:
     - Functionality
     - User Experience
     - Technical Quality
     - Design Polish

### Agent-Friendly Spec Tips

**DO ✅**
- Specify exact package names: "React Markdown" not "markdown renderer"
- Include version numbers when critical: "Node.js 18+"
- Define ports explicitly: `<port>Only launch on port 3000</port>`
- List environment variables: "CLAUDE_CODE_OAUTH_TOKEN from process.env"
- Describe error handling: "On failure: show inline error, keep form populated"

**DON'T ❌**
- Use vague terms: "user-friendly", "fast", "robust"
- Leave implementation details: Agent decides how, you specify what
- Mix concerns: Keep features atomic and focused
- Forget relationships: Link features to data structures
- Skip validation: Always include success criteria

## Template Evolution

### Version 1.0 (Current)
**Based on:** Claude.ai Clone specification analysis

**Patterns Extracted:**
- XML-style structure
- 13-section organization
- Feature categorization pattern
- Database schema documentation
- API endpoint grouping
- UI component hierarchy
- Design system structure
- Implementation phasing
- Multi-dimensional success criteria

**Works With:**
- Linear task management
- BEADS task management
- GitHub Issues task management
- All coding agent features

### Future Enhancements
Potential additions based on usage:
- Mobile app template variant
- CLI tool template variant
- API-only service template
- Microservice template
- Data pipeline template

## Common Use Cases

### Full-Stack Web Application
Use complete template as-is:
- All sections filled out
- Comprehensive feature list
- Detailed UI/UX specifications
- Design system fully defined

### API Service
Simplify template:
- Remove `<ui_layout>` and `<design_system>`
- Focus on `<api_endpoints_summary>`
- Expand `<database_schema>`
- Add API documentation requirements

### CLI Tool
Minimal template:
- Keep `<overview>` and `<technology_stack>`
- Focus on command structure in features
- Minimal or no database schema
- No UI layout or design system
- Add CLI interaction patterns

### Mobile Application
Adapt template:
- Adjust `<technology_stack>` for mobile frameworks
- Modify `<ui_layout>` for mobile patterns
- Add native feature requirements
- Include platform-specific sections

## Success Stories

### Claude.ai Clone (Basis for Template)
- **Spec Size:** 687 lines, comprehensive
- **Features Generated:** 54 issues in Linear
- **Implementation:** Fully autonomous
- **Audit Results:** Grade A, 100% pass rate
- **Outcome:** Production-ready chat application

**What Made It Successful:**
- Clear hierarchical structure
- Precise technical specifications
- Comprehensive feature listing
- Detailed implementation steps
- Well-defined success criteria

## Best Practices

### Before Starting
1. Research similar applications
2. Sketch UI wireframes
3. List all features you need
4. Choose technology stack
5. Understand your constraints

### While Writing Spec
1. Start with overview (big picture)
2. Detail technology choices (be specific)
3. List ALL features (think comprehensively)
4. Design data structures (align with features)
5. Document API contracts (match features and data)
6. Describe UI layout (user perspective)
7. Define design system (visual consistency)
8. Map user flows (critical interactions)
9. Phase implementation (logical steps)
10. Set success criteria (4 dimensions)

### After Writing Spec
1. Review for completeness (no placeholders left)
2. Check consistency (features ↔ schema ↔ API ↔ UI)
3. Validate technical choices (compatibility)
4. Read as outsider (clear and unambiguous?)
5. Run autocode and iterate

### During Implementation
1. Spec is living document
2. Update when requirements change
3. Add new features to spec first
4. Re-run autocode to sync
5. Keep success criteria updated

## Troubleshooting

### "My spec is too vague"
**Symptom:** Agent asks clarifying questions or makes unexpected choices

**Solution:**
- For each feature, specify:
  - Exact user action
  - System response
  - Data involved
  - Error handling
  - Edge cases

### "My spec is too detailed"
**Symptom:** Agent gets bogged down in implementation minutiae

**Solution:**
- Focus on WHAT, not HOW
- Remove code-level details
- Trust agent to make standard technical decisions
- Specify behavior, not implementation

### "Features don't align with schema"
**Symptom:** Agent creates unnecessary tables or missing relationships

**Solution:**
- Map each feature to required tables
- Ensure all feature data has schema representation
- Add relationships between tables
- Review API endpoints to confirm alignment

### "Implementation order is wrong"
**Symptom:** Agent tries to build advanced features before foundation

**Solution:**
- Order `<implementation_steps>` by dependency
- Foundation → Core → Advanced → Polish
- Each step should build on previous
- Group related features in same step

## Resources

### Template Files
- `templates/app_spec_template.txt` - The template itself
- `templates/TEMPLATE_GUIDE.md` - Detailed usage guide
- `templates/README.md` - Quick reference

### Example Specs
- `generations/autonomous_demo_project/app_spec.txt` - Real working example
- Shows template in action for Claude.ai Clone
- Reference for how comprehensive spec looks when complete

### Related Documentation
- `WORKFLOW.md` - Overall agent workflow
- `TASK_ADAPTER_ARCHITECTURE.md` - Task manager integration
- `ADDING_FEATURES.md` - How to add features to existing projects
- `SPEC_FILE_FORMATS.md` - Spec file format details

## Quick Reference

### Template Sections (Required vs Optional)

| Section | Required? | Purpose |
|---------|-----------|---------|
| project_name | ✅ Required | Identifies the project |
| overview | ✅ Required | Describes what and why |
| technology_stack | ✅ Required | Lists all technical choices |
| prerequisites | ✅ Required | Environment setup |
| core_features | ✅ Required | All functionality |
| database_schema | ⚠️ If data app | Data structures |
| api_endpoints_summary | ⚠️ If web app | API contracts |
| ui_layout | ⚠️ If UI app | Interface structure |
| design_system | ⚙️ Recommended | Visual language |
| key_interactions | ⚙️ Recommended | User flows |
| implementation_steps | ✅ Required | Development phases |
| success_criteria | ✅ Required | Validation metrics |
| notes | ⚪ Optional | Additional context |

### Commands

```bash
# Copy template to project
autospec [directory]

# Start implementation
autocode

# Add new features
# 1. Update app_spec.txt
# 2. Run: autocode
# 3. Agent detects changes and creates new issues

# Switch task managers
# Edit .autocode-config.json, change task_manager value
```

---

**Remember:** A great spec is the foundation of successful autonomous development. Invest time in your specification—it pays dividends in implementation quality and speed! 🚀

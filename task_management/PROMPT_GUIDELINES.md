# Generic Task Management Terminology for Prompts

This file documents the generic task management terminology to use in ALL prompts.
These terms are adapter-agnostic and work with Linear, Jira, GitHub, Asana, etc.

## Core Terms to Use

### DO Use These Terms (Generic)

| Term | When to Use | Example |
|------|-------------|---------|
| **task management system** | Referring to the backend | "Create a project in your task management system" |
| **project** | Collection of issues | "Create a new project" |
| **issue** | Single work item | "Create issues for each feature" |
| **status** | Current state | "Update status to IN_PROGRESS" |
| **priority** | Importance level | "Set priority to HIGH" |
| **label** | Categorization tag | "Add label 'feature'" |
| **comment** | Discussion/update | "Add a comment to the issue" |
| **team** | Group of users | "List all teams" |

### DON'T Use These Terms (System-Specific)

| Term | Why Not | Use Instead |
|------|---------|-------------|
| ~~Linear project~~ | Ties to Linear | "project" |
| ~~Linear issue~~ | Ties to Linear | "issue" |
| ~~mcp__linear__*~~ | Exposes implementation | (Agents use tools transparently) |
| ~~Todo status~~ | Linear-specific | "TODO status" |
| ~~Priority 1-4~~ | Linear-specific | "URGENT/HIGH/MEDIUM/LOW priority" |

## MCP Tool References in Prompts

**BEFORE (Linear-Specific):**
```markdown
Use `mcp__linear__create_project` to create a Linear project.
Use `mcp__linear__create_issue` to create issues.
```

**AFTER (Generic):**
```markdown
Use the MCP tools to create a project in your task management system.
Use the MCP tools to create issues.
```

**BEST (No Tool Mention):**
```markdown
Create a project in your task management system.
Create issues for each feature in the specification.
```

The agent automatically knows which MCP tools to use based on the configured adapter.

## Status Values

### Use These Generic Values

```python
TODO          # Not started, in backlog
IN_PROGRESS   # Currently being worked on  
DONE          # Completed successfully
CANCELED      # Won't be implemented
```

### Don't Use System-Specific Values

```python
# ❌ Linear-specific
"Todo", "In Progress", "Done", "Canceled"

# ❌ Jira-specific  
"To Do", "Open", "Closed"

# ❌ GitHub-specific
"open", "closed"
```

## Priority Values

### Use These Generic Values

```python
URGENT   # P1 - Critical, blocking
HIGH     # P2 - Important, high value
MEDIUM   # P3 - Normal priority
LOW      # P4 - Nice to have
```

### Don't Use System-Specific Values

```python
# ❌ Linear-specific
1, 2, 3, 4

# ❌ Jira-specific
"Highest", "High", "Medium", "Low", "Lowest"

# ❌ Custom labels
"p0", "p1", "p2", "p3"
```

## Example Prompt Rewrites

### Example 1: Project Creation

**BEFORE (Linear-Specific):**
```markdown
### CRITICAL TASK: Create Linear Project

1. Use `mcp__linear__list_teams` to get your Linear team ID
2. Use `mcp__linear__create_project` to create a Linear project:
   - Set `teamIds` to your Linear team
   - Set status to "Todo"
```

**AFTER (Generic):**
```markdown
### CRITICAL TASK: Create Project

1. List all teams in your task management system
2. Create a new project:
   - Associate it with a team
   - Use the project name from the specification
```

### Example 2: Issue Creation

**BEFORE (Linear-Specific):**
```markdown
Create 50 Linear issues using `mcp__linear__create_issue`:
- Set `priority` to 1-4 based on importance
- Leave status as default ("Todo")
- Add Linear labels for categorization
```

**AFTER (Generic):**
```markdown
Create 50 issues in the project:
- Set priority (URGENT/HIGH/MEDIUM/LOW) based on importance
- Issues start in TODO status by default
- Add labels for categorization
```

### Example 3: Status Updates

**BEFORE (Linear-Specific):**
```markdown
Update the Linear issue using `mcp__linear__update_issue`:
- Set `status` to "In Progress"
- Set `priority` to 1 (urgent)
```

**AFTER (Generic):**
```markdown
Update the issue:
- Set status to IN_PROGRESS
- Set priority to URGENT
```

### Example 4: Labels

**BEFORE (Linear-Specific):**
```markdown
Create these Linear labels using `mcp__linear__create_label`:
- "awaiting-audit" (orange color)
- "audited" (green color)
```

**AFTER (Generic):**
```markdown
Create these labels for the audit workflow:
- "awaiting-audit" (orange)
- "audited" (green)
```

## Prompt Template Structure

Use this structure for all prompts:

```markdown
## YOUR ROLE - [Agent Type]

You are working with a **task management system** to track your work.
Your system may be Linear, Jira, GitHub Issues, or another platform - 
the interface is the same regardless.

### TASK: Create Project

Create a new project:
1. List available teams
2. Create a project with:
   - Name from specification
   - Associated with a team
   - Brief description

### TASK: Create Issues

Create issues for each feature:
- Title: Brief, descriptive
- Description: Detailed requirements
- Status: TODO (default)
- Priority: Based on importance (URGENT/HIGH/MEDIUM/LOW)
- Labels: Categorize by type (feature, bug, enhancement)

### TASK: Update Issue

When you complete an issue:
1. Add a comment with implementation details
2. Update status to DONE
3. Add label "awaiting-audit"

### Available Tools

The task management system provides these capabilities:
- Project management (create, list, update)
- Issue management (create, list, update)
- Label management (create, list, apply)
- Comment management (create, list)

You don't need to know which specific system is being used - 
the interface handles the mapping automatically.
```

## Variable Naming Conventions

When referencing task management concepts in prompts:

```markdown
# ✅ Good (Generic)
{project_id}
{issue_id}
{status}
{priority}
{label_name}

# ❌ Bad (System-Specific)
{linear_project_id}
{linear_issue_id}
{linear_status}
{linear_priority}
```

## Conditional Sections

If you need to provide system-specific guidance:

```markdown
**Note:** The specific commands and UI may vary depending on your 
task management system (Linear, Jira, GitHub, etc.), but the 
workflow remains the same:

1. Create a project
2. Create issues within the project  
3. Update issues as you work
4. Add comments for documentation
```

## Summary

### Golden Rules for Prompts

1. ✅ Use generic terms (project, issue, status, priority, label)
2. ✅ Use enum-style values (TODO, DONE, URGENT, HIGH)
3. ✅ Don't mention specific systems (Linear, Jira, GitHub)
4. ✅ Don't mention MCP tool names in prompts
5. ✅ Focus on WHAT to do, not HOW (tools handle HOW)
6. ✅ Describe workflow, not API calls

### Quick Reference Card

| Instead of... | Say... |
|---------------|--------|
| Linear project | project |
| Linear issue | issue |
| mcp__linear__create_issue | Create an issue |
| status="Todo" | status=TODO |
| priority=1 | priority=URGENT |
| Linear labels | labels |
| Linear comment | comment |

This ensures prompts work with ANY task management adapter!

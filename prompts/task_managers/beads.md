## BEADS TASK MANAGEMENT

BEADS is a git-backed, local task management system. Use the `bd` CLI command directly via bash.

### BEADS WORKFLOW

**Key BEADS Commands:**
```bash
# List all open issues
bd list --status open --json

# List issues by status
bd list --status todo --json
bd list --status in-progress --json
bd list --status done --json

# Get issue details
bd show <issue-id> --json

# Create new issue
bd create --title "Feature title" --description "Details" --status todo

# Update issue status
bd update <issue-id> --status in-progress
bd update <issue-id> --status done

# Add comment to issue
bd comment <issue-id> "Your comment here"

# Count issues by status
bd list --status todo --json | jq 'length'
bd list --status done --json | jq 'length'
```

### BEADS INITIALIZATION

**Steps:**
1. Check if `.task_project.json` exists to prevent duplicate initialization
2. Verify BEADS is initialized (`bd list` returns valid JSON)
3. Parse app_spec.txt to extract features
4. Create issues using `bd create` (one per feature)
5. Save state to `.task_project.json`

**Example Issue Creation:**
```bash
bd create --title "Implement user authentication" \
  --description "Add JWT-based auth with login/logout endpoints" \
  --status todo
```

### BEADS CODING WORKFLOW

**Steps:**
1. List open issues: `bd list --status todo --json`
2. Pick an issue to work on
3. Update status: `bd update <id> --status in-progress`
4. Implement the feature
5. Update status: `bd update <id> --status done`
6. Add summary comment: `bd comment <id> "Implemented feature X with Y"`

### BEADS STATE TRACKING

All BEADS project data is stored in `.task_project.json`:
```json
{
  "adapter": "beads",
  "workspace": "default",
  "initialized": true,
  "issues_created": 50
}
```

**Notes:**
- BEADS data is stored in `.beads/` directory (git-tracked)
- All operations are local (no API rate limits)
- Use `--json` flag for programmatic parsing
- Parse JSON with `jq` for filtering/counting

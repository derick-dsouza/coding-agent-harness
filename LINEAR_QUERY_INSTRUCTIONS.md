# Linear Project State Query Instructions

## Overview

I've created a Python script to query your Linear project and retrieve the information you requested. Due to security restrictions in the current environment, I cannot execute Python scripts directly. You'll need to run the script manually.

## Files Created

1. **`query_linear.py`** - Python script that queries Linear API
2. **`run_linear_query.sh`** - Shell script wrapper for easy execution

## What the Script Does

The script performs two main queries:

1. **META Issue Query (DER-55)**
   - Retrieves the issue with identifier `DER-55` or title containing "[META] Project Progress Tracker"
   - Displays the description and recent comments
   - This provides session context and handoff notes from previous sessions

2. **Project Issues Query**
   - Gets all issues for project ID: `c4ecebaf-9e40-4210-8301-f86be620124f`
   - Counts issues by status (Done, In Progress, Todo, etc.)
   - Lists all "In Progress" issues with identifiers and titles
   - Shows the top 5 highest priority "Todo" issues

## How to Run

### Option 1: Using the Shell Script (Easiest)

```bash
# Make the script executable
chmod +x run_linear_query.sh

# Run it
./run_linear_query.sh
```

### Option 2: Run Python Script Directly

```bash
python3 query_linear.py
```

### Prerequisites

Make sure your `LINEAR_API_KEY` environment variable is set:

```bash
export LINEAR_API_KEY='your_linear_api_key_here'
```

Get your API key from: https://linear.app/YOUR-TEAM/settings/api

## Expected Output

The script will output:

```
======================================================================
  LINEAR PROJECT STATE QUERY
======================================================================

1. Querying META issue (DER-55)...

META Issue: DER-55 - [META] Project Progress Tracker
Status: In Progress

Description:
----------------------------------------------------------------------
[Description content will be shown here]
----------------------------------------------------------------------

Recent Comments (X):
----------------------------------------------------------------------
[User] - [Date]
[Comment content]
...
----------------------------------------------------------------------

2. Querying all project issues...

Project: [Project Name]

Issue Status Counts:
----------------------------------------------------------------------
  Done: X
  In Progress: X
  Todo: X
----------------------------------------------------------------------

Issues In Progress (X):
----------------------------------------------------------------------
  DER-XX: Issue title
  ...
----------------------------------------------------------------------

Top 5 Priority Todo Issues:
----------------------------------------------------------------------
  [Urgent] DER-XX: Issue title
  [High] DER-XX: Issue title
  ...
----------------------------------------------------------------------

======================================================================
  QUERY COMPLETE
======================================================================
```

## Troubleshooting

### Error: "LINEAR_API_KEY environment variable is not set"

Make sure you've exported the Linear API key:
```bash
export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'
```

### Error: "HTTP Error: 401"

Your API key might be invalid or expired. Get a fresh one from Linear settings.

### Error: "META issue not found"

The issue with identifier DER-55 doesn't exist yet. This is normal if the project hasn't been initialized.

### Error: "Project not found"

The project ID `c4ecebaf-9e40-4210-8301-f86be620124f` might be incorrect. Double-check the project ID in Linear.

## Implementation Details

The script uses:
- Linear GraphQL API: `https://api.linear.app/graphql`
- Python's built-in `urllib` for HTTP requests
- GraphQL queries for efficient data retrieval

### API Endpoints Used

1. **Get Issue by ID**: `issue(id: "DER-55")`
2. **Get Project Issues**: `project(id: "project-id").issues`

### Priority Mapping

Linear uses the following priority scale:
- 0 = No priority
- 1 = Urgent
- 2 = High
- 3 = Medium
- 4 = Low

The script sorts by priority (lower number = higher priority) to show the most important items first.

## Next Steps

After running the query, you'll have:
- Summary of META issue content and session handoff notes
- Count of issues by status
- List of in-progress issues
- Top 5 priority todo items

This information will help you understand the current project state and what work has been completed or is pending.

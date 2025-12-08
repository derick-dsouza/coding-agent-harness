#!/usr/bin/env python3
"""
Linear Query Script
===================

Queries Linear API to get project state and META issue information.
"""

import os
import json
import sys
import urllib.request
import urllib.error

# Project ID from command line
PROJECT_ID = "c4ecebaf-9e40-4210-8301-f86be620124f"


def make_linear_request(query: str) -> dict:
    """Make a GraphQL request to Linear API."""
    linear_key = os.environ.get('LINEAR_API_KEY')
    if not linear_key:
        raise ValueError('LINEAR_API_KEY environment variable is not set')

    url = 'https://api.linear.app/graphql'
    headers = {
        'Authorization': linear_key,
        'Content-Type': 'application/json'
    }

    data = json.dumps({'query': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code}', file=sys.stderr)
        print(e.read().decode('utf-8'), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error: {str(e)}', file=sys.stderr)
        sys.exit(1)


def get_meta_issue():
    """Get the META issue (DER-55) with description and comments."""
    query = '''
    query GetMetaIssue {
      issue(id: "DER-55") {
        id
        identifier
        title
        description
        state {
          name
        }
        comments(first: 10, orderBy: updatedAt) {
          nodes {
            id
            body
            createdAt
            updatedAt
            user {
              name
            }
          }
        }
      }
    }
    '''
    return make_linear_request(query)


def get_project_issues():
    """Get all issues for the project with their statuses."""
    query = f'''
    query GetProjectIssues {{
      project(id: "{PROJECT_ID}") {{
        id
        name
        issues {{
          nodes {{
            id
            identifier
            title
            priority
            state {{
              name
              type
            }}
          }}
        }}
      }}
    }}
    '''
    return make_linear_request(query)


def main():
    print("=" * 70)
    print("  LINEAR PROJECT STATE QUERY")
    print("=" * 70)
    print()

    # 1. Get META issue
    print("1. Querying META issue (DER-55)...")
    print()
    meta_result = get_meta_issue()

    if 'errors' in meta_result:
        print("Error querying META issue:")
        print(json.dumps(meta_result['errors'], indent=2))
    else:
        meta_issue = meta_result.get('data', {}).get('issue')
        if meta_issue:
            print(f"META Issue: {meta_issue['identifier']} - {meta_issue['title']}")
            print(f"Status: {meta_issue['state']['name']}")
            print()
            print("Description:")
            print("-" * 70)
            print(meta_issue.get('description', '(No description)'))
            print("-" * 70)
            print()

            comments = meta_issue.get('comments', {}).get('nodes', [])
            if comments:
                print(f"Recent Comments ({len(comments)}):")
                print("-" * 70)
                for comment in comments:
                    user = comment.get('user', {}).get('name', 'Unknown')
                    created = comment.get('createdAt', '')
                    print(f"\n[{user}] - {created}")
                    print(comment.get('body', ''))
                print("-" * 70)
            else:
                print("No comments found.")
            print()
        else:
            print("META issue not found (may not exist yet)")
            print()

    # 2. Get all project issues
    print("2. Querying all project issues...")
    print()
    issues_result = get_project_issues()

    if 'errors' in issues_result:
        print("Error querying project issues:")
        print(json.dumps(issues_result['errors'], indent=2))
    else:
        project = issues_result.get('data', {}).get('project')
        if project:
            print(f"Project: {project['name']}")
            print()

            issues = project.get('issues', {}).get('nodes', [])

            # Count by status
            status_counts = {}
            in_progress_issues = []
            todo_issues = []

            for issue in issues:
                state = issue['state']['name']
                status_counts[state] = status_counts.get(state, 0) + 1

                if state == "In Progress":
                    in_progress_issues.append(issue)
                elif state == "Todo":
                    todo_issues.append(issue)

            # Print status counts
            print("Issue Status Counts:")
            print("-" * 70)
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
            print("-" * 70)
            print()

            # Print in progress issues
            if in_progress_issues:
                print(f"Issues In Progress ({len(in_progress_issues)}):")
                print("-" * 70)
                for issue in in_progress_issues:
                    print(f"  {issue['identifier']}: {issue['title']}")
                print("-" * 70)
                print()
            else:
                print("No issues in progress.")
                print()

            # Print top 5 priority todo issues
            # Priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
            # Lower number = higher priority
            todo_issues_with_priority = [
                issue for issue in todo_issues
                if issue.get('priority', 0) > 0
            ]
            todo_issues_with_priority.sort(key=lambda x: x.get('priority', 999))

            top_5_todo = todo_issues_with_priority[:5]

            if top_5_todo:
                print(f"Top 5 Priority Todo Issues:")
                print("-" * 70)
                priority_names = {0: "None", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
                for issue in top_5_todo:
                    priority = issue.get('priority', 0)
                    priority_name = priority_names.get(priority, "Unknown")
                    print(f"  [{priority_name}] {issue['identifier']}: {issue['title']}")
                print("-" * 70)
                print()
            else:
                print("No Todo issues with priority set.")
                print()
        else:
            print("Project not found")
            print()

    print("=" * 70)
    print("  QUERY COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()

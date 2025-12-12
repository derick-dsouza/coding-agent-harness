"""
Linear Cache Integration Helpers
=================================

Helper functions for integrating the cache with the Linear MCP calls.

Since we can't intercept MCP calls directly (they happen inside Claude SDK),
we use a tracking + invalidation approach:

1. Track what Linear calls were made (already implemented)
2. Invalidate cache based on write operations
3. Let cache naturally expire for reads

This provides significant API reduction without complex interception.
"""

from pathlib import Path
from typing import Set, Optional, List, Dict, Any
import json


def invalidate_cache_for_operations(
    cache,
    tracker,
    project_id: Optional[str] = None
):
    """
    Invalidate cache based on operations that were performed in the session.
    
    Call this after an agent session completes to invalidate cache entries
    that might have been modified.
    
    Args:
        cache: LinearCache instance
        tracker: LinearCallTracker instance
        project_id: Optional project ID to invalidate project-wide caches
    """
    if not cache or not tracker:
        return
    
    # Get session calls
    session_calls = tracker.session_calls
    
    # Track what needs invalidation
    invalidated_issues = set()
    invalidate_project_list = False
    
    for call in session_calls:
        operation = call.get("operation", "")
        endpoint = call.get("endpoint", "")
        metadata = call.get("metadata", {})
        
        # Create operations invalidate the issues list
        if operation == "create" and "issue" in endpoint:
            invalidate_project_list = True
            print(f"🔄 Cache: Invalidating issues list (created new issue)")
        
        # Update operations invalidate both issue and list
        elif operation == "update" and "issue" in endpoint:
            issue_id = metadata.get("id") or metadata.get("issueId")
            if issue_id:
                cache.invalidate(f"issue_{issue_id}")
                invalidated_issues.add(issue_id)
            invalidate_project_list = True
            print(f"🔄 Cache: Invalidating issue {issue_id} (updated)")
        
        # Comment operations invalidate the issue
        elif "comment" in endpoint and operation == "create":
            issue_id = metadata.get("issueId")
            if issue_id:
                cache.invalidate(f"issue_{issue_id}")
                invalidated_issues.add(issue_id)
                print(f"🔄 Cache: Invalidating issue {issue_id} (new comment)")
    
    # Invalidate project-wide issue list if needed
    if invalidate_project_list and project_id:
        cache.invalidate(f"project_{project_id}_issues")
        print(f"🔄 Cache: Invalidated project issues list")
    
    # Print summary
    if invalidated_issues or invalidate_project_list:
        print(f"📦 Cache: Invalidated {len(invalidated_issues)} issues, " +
              f"{'1 project list' if invalidate_project_list else '0 lists'}")


def get_cache_status_summary(cache, tracker) -> dict:
    """
    Get a summary of cache and API call status.
    
    Returns:
        Dictionary with combined statistics
    """
    if not cache or not tracker:
        return {}
    
    cache_stats = cache.get_stats()
    tracker_stats = tracker.get_session_stats()
    
    # Calculate effective reduction
    total_calls = tracker_stats.get("total_calls", 0)
    cache_hits = cache_stats.get("total_hits", 0)
    
    # Estimate API calls saved by cache
    # Each cache hit represents an API call we didn't make
    potential_calls = total_calls + cache_hits
    reduction = (cache_hits / potential_calls * 100) if potential_calls > 0 else 0
    
    return {
        "api_calls_made": total_calls,
        "cache_hits": cache_hits,
        "cache_misses": cache_stats.get("total_misses", 0),
        "cache_hit_rate": cache_stats.get("hit_rate", 0),
        "estimated_reduction": reduction,
        "total_requests": potential_calls
    }


def print_combined_stats(cache, tracker):
    """
    Print combined cache and API tracking statistics.
    
    Shows the full picture of API usage and cache effectiveness.
    """
    if not cache or not tracker:
        return
    
    stats = get_cache_status_summary(cache, tracker)
    
    print("\n" + "="*70)
    print("  LINEAR API USAGE - COMBINED STATS")
    print("="*70)
    print(f"\nAPI Calls:")
    print(f"  Made:     {stats['api_calls_made']}")
    print(f"  Avoided:  {stats['cache_hits']} (from cache)")
    print(f"  Total:    {stats['total_requests']}")
    
    if stats['cache_hits'] > 0:
        print(f"\nCache Performance:")
        print(f"  Hit rate:     {stats['cache_hit_rate']*100:.1f}%")
        print(f"  Reduction:    {stats['estimated_reduction']:.1f}%")
        print(f"  API calls saved: {stats['cache_hits']}")
    
    print("="*70)


def should_cache_operation(operation: str, endpoint: str) -> bool:
    """
    Determine if an operation should be cached.
    
    Args:
        operation: Operation type (list, get, create, update)
        endpoint: Endpoint (issues, issue, projects, etc.)
        
    Returns:
        True if this operation result should be cached
    """
    # Read operations should be cached
    if operation in ["list", "get"]:
        return True
    
    # Write operations should not be cached
    if operation in ["create", "update", "delete"]:
        return False
    
    return False


def get_cache_key(operation: str, endpoint: str, metadata: dict) -> Optional[str]:
    """
    Generate cache key for an operation.
    
    Args:
        operation: Operation type
        endpoint: Endpoint
        metadata: Operation metadata
        
    Returns:
        Cache key string or None if shouldn't be cached
    """
    if not should_cache_operation(operation, endpoint):
        return None
    
    # list_issues -> project_{id}_issues
    if operation == "list" and "issue" in endpoint:
        project_id = metadata.get("project") or metadata.get("projectId")
        if project_id:
            return f"project_{project_id}_issues"
    
    # get_issue -> issue_{id}
    elif operation == "get" and endpoint == "issue":
        issue_id = metadata.get("id") or metadata.get("issueId")
        if issue_id:
            return f"issue_{issue_id}"
    
    # list_projects -> team_{id}_projects
    elif operation == "list" and "project" in endpoint:
        team_id = metadata.get("team") or metadata.get("teamId")
        if team_id:
            return f"team_{team_id}_projects"
    
    # get_project -> project_{id}
    elif operation == "get" and endpoint == "project":
        project_id = metadata.get("id") or metadata.get("projectId")
        if project_id:
            return f"project_{project_id}"
    
    return None


def get_cache_ttl(operation: str, endpoint: str) -> int:
    """
    Get appropriate TTL for an operation.
    
    Args:
        operation: Operation type
        endpoint: Endpoint
        
    Returns:
        TTL in seconds
    """
    from linear_cache import LinearCache
    
    # Use cache-defined TTLs
    if "issue" in endpoint and operation == "list":
        return LinearCache.TTL_LIST_ISSUES
    elif "issue" in endpoint and operation == "get":
        return LinearCache.TTL_GET_ISSUE
    elif "project" in endpoint and operation == "list":
        return LinearCache.TTL_LIST_PROJECTS
    elif "project" in endpoint and operation == "get":
        return LinearCache.TTL_GET_PROJECT
    elif "team" in endpoint:
        return LinearCache.TTL_LIST_TEAMS
    
    return LinearCache.DEFAULT_TTL


def load_project_state(project_dir: Path) -> dict:
    """
    Load project state to get project ID for cache operations.
    
    Args:
        project_dir: Project directory
        
    Returns:
        Project state dictionary
    """
    state_file = project_dir / ".task_project.json"
    if not state_file.exists():
        return {}
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, UnicodeDecodeError):
        return {}


def get_project_id_from_state(project_dir: Path) -> Optional[str]:
    """
    Get project ID from saved state.
    
    Args:
        project_dir: Project directory
        
    Returns:
        Project ID or None
    """
    state = load_project_state(project_dir)
    return state.get("project_id")

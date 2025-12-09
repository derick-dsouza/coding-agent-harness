"""
Test Linear Cache Helpers
==========================

Verify that cache integration helpers work correctly.
"""

import tempfile
from pathlib import Path
import json

from linear_cache import LinearCache
from linear_tracker import LinearCallTracker
from linear_cache_helpers import (
    invalidate_cache_for_operations,
    should_cache_operation,
    get_cache_key,
    get_cache_ttl,
    get_cache_status_summary
)


def test_should_cache_operation():
    """Test operation caching decisions."""
    print("\n" + "="*70)
    print("TEST 1: Should Cache Operation")
    print("="*70)
    
    # Read operations should be cached
    assert should_cache_operation("list", "issues") == True
    assert should_cache_operation("get", "issue") == True
    assert should_cache_operation("list", "projects") == True
    assert should_cache_operation("get", "project") == True
    
    # Write operations should NOT be cached
    assert should_cache_operation("create", "issue") == False
    assert should_cache_operation("update", "issue") == False
    assert should_cache_operation("delete", "issue") == False
    
    print("✅ Operation caching decisions work correctly")


def test_get_cache_key():
    """Test cache key generation."""
    print("\n" + "="*70)
    print("TEST 2: Cache Key Generation")
    print("="*70)
    
    # list_issues
    key = get_cache_key("list", "issues", {"project": "proj-123"})
    assert key == "project_proj-123_issues", f"Expected project_proj-123_issues, got {key}"
    
    # get_issue
    key = get_cache_key("get", "issue", {"id": "ISS-456"})
    assert key == "issue_ISS-456", f"Expected issue_ISS-456, got {key}"
    
    # list_projects
    key = get_cache_key("list", "projects", {"team": "team-789"})
    assert key == "team_team-789_projects", f"Expected team_team-789_projects, got {key}"
    
    # get_project
    key = get_cache_key("get", "project", {"id": "proj-abc"})
    assert key == "project_proj-abc", f"Expected project_proj-abc, got {key}"
    
    # Write operations should return None
    key = get_cache_key("create", "issue", {})
    assert key is None, "Create operations should not have cache keys"
    
    print("✅ Cache key generation works correctly")


def test_get_cache_ttl():
    """Test TTL determination."""
    print("\n" + "="*70)
    print("TEST 3: Cache TTL Selection")
    print("="*70)
    
    from linear_cache import LinearCache
    
    # list_issues
    ttl = get_cache_ttl("list", "issues")
    assert ttl == LinearCache.TTL_LIST_ISSUES, f"Expected {LinearCache.TTL_LIST_ISSUES}, got {ttl}"
    
    # get_issue  
    ttl = get_cache_ttl("get", "issue")
    assert ttl == LinearCache.TTL_GET_ISSUE, f"Expected {LinearCache.TTL_GET_ISSUE}, got {ttl}"
    
    # list_projects
    ttl = get_cache_ttl("list", "projects")
    assert ttl == LinearCache.TTL_LIST_PROJECTS, f"Expected {LinearCache.TTL_LIST_PROJECTS}, got {ttl}"
    
    # teams
    ttl = get_cache_ttl("list", "teams")
    assert ttl == LinearCache.TTL_LIST_TEAMS, f"Expected {LinearCache.TTL_LIST_TEAMS}, got {ttl}"
    
    print("✅ TTL selection works correctly")


def test_invalidate_cache_for_operations():
    """Test cache invalidation based on operations."""
    print("\n" + "="*70)
    print("TEST 4: Cache Invalidation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        tracker = LinearCallTracker(project_dir)
        
        # Populate cache
        cache.set("project_proj-123_issues", ["issue1", "issue2", "issue3"])
        cache.set("issue_ISS-1", {"id": "ISS-1", "title": "Test"})
        cache.set("issue_ISS-2", {"id": "ISS-2", "title": "Test 2"})
        
        # Simulate update operation
        tracker.track_call("update", "issue", {"id": "ISS-1"})
        
        # Invalidate based on operations
        invalidate_cache_for_operations(cache, tracker, "proj-123")
        
        # Check invalidation
        assert cache.get("issue_ISS-1") is None, "Updated issue should be invalidated"
        assert cache.get("project_proj-123_issues") is None, "Issues list should be invalidated"
        assert cache.get("issue_ISS-2") is not None, "Other issue should remain"
        
        print("✅ Cache invalidation works correctly")


def test_invalidate_on_create():
    """Test cache invalidation on create operations."""
    print("\n" + "="*70)
    print("TEST 5: Invalidation on Create")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        tracker = LinearCallTracker(project_dir)
        
        # Populate cache with issues list
        cache.set("project_proj-123_issues", ["issue1", "issue2"])
        
        # Simulate create operation
        tracker.track_call("create", "issue", {"title": "New Issue"})
        
        # Invalidate
        invalidate_cache_for_operations(cache, tracker, "proj-123")
        
        # Issues list should be invalidated (new issue was added)
        assert cache.get("project_proj-123_issues") is None, "Issues list should be invalidated after create"
        
        print("✅ Create invalidation works correctly")


def test_combined_stats():
    """Test combined stats calculation."""
    print("\n" + "="*70)
    print("TEST 6: Combined Statistics")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        tracker = LinearCallTracker(project_dir)
        
        # Set up cache with some data
        cache.set("test_key", "value")
        
        # Simulate some API calls
        tracker.track_call("list", "issues")  # API call made
        
        # Simulate cache interactions
        cache.get("test_key")  # Hit
        cache.get("test_key")  # Hit
        cache.get("nonexistent")  # Miss
        
        # Get combined stats
        stats = get_cache_status_summary(cache, tracker)
        
        assert stats["api_calls_made"] == 1, f"Should have 1 API call, got {stats['api_calls_made']}"
        assert stats["cache_hits"] == 2, f"Should have 2 cache hits, got {stats['cache_hits']}"
        assert stats["cache_misses"] == 1, f"Should have 1 cache miss, got {stats['cache_misses']}"
        
        # Cache hit rate is hits/(hits+misses) = 2/3 = 0.666...
        expected_hit_rate = 2/3
        assert abs(stats["cache_hit_rate"] - expected_hit_rate) < 0.01, \
            f"Should have ~66.7% cache hit rate, got {stats['cache_hit_rate']*100:.1f}%"
        
        print("✅ Combined statistics work correctly")
        print(f"   API calls made: {stats['api_calls_made']}")
        print(f"   Cache hits: {stats['cache_hits']}")  
        print(f"   Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")


def test_project_state_loading():
    """Test loading project state."""
    print("\n" + "="*70)
    print("TEST 7: Project State Loading")
    print("="*70)
    
    from linear_cache_helpers import load_project_state, get_project_id_from_state
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create a task project state file
        state = {
            "initialized": True,
            "project_id": "test-project-123",
            "team_id": "test-team-456"
        }
        
        state_file = project_dir / ".task_project.json"
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        # Load state
        loaded_state = load_project_state(project_dir)
        assert loaded_state["project_id"] == "test-project-123"
        
        # Get project ID
        project_id = get_project_id_from_state(project_dir)
        assert project_id == "test-project-123"
        
        print("✅ Project state loading works correctly")


def run_all_tests():
    """Run all cache helper tests."""
    print("\n" + "="*70)
    print("  LINEAR CACHE HELPERS - TEST SUITE")
    print("="*70)
    
    test_should_cache_operation()
    test_get_cache_key()
    test_get_cache_ttl()
    test_invalidate_cache_for_operations()
    test_invalidate_on_create()
    test_combined_stats()
    test_project_state_loading()
    
    print("\n" + "="*70)
    print("  ✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nLinear cache integration helpers are working correctly.")
    print("Ready for production use.\n")


if __name__ == "__main__":
    run_all_tests()

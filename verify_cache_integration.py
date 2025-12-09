#!/usr/bin/env python3
"""
Cache Verification Script
==========================

Verify that the caching system works correctly by simulating
cache operations and checking behavior.

This doesn't test the actual MCP calls (can't without Linear API),
but verifies the cache infrastructure is properly integrated.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from linear_cache import init_cache, get_cache
from linear_tracker import init_tracker, get_tracker
from linear_cache_helpers import (
    invalidate_cache_for_operations,
    print_combined_stats,
    get_cache_status_summary
)


def test_cache_integration():
    """Test that cache is properly integrated."""
    print("\n" + "="*70)
    print("  CACHE INTEGRATION VERIFICATION")
    print("="*70)
    
    project_dir = Path.cwd()
    print(f"\nProject directory: {project_dir}")
    
    # Test 1: Initialize cache and tracker
    print("\n[Test 1] Initializing cache and tracker...")
    cache = init_cache(project_dir)
    tracker = init_tracker(project_dir)
    
    assert cache is not None, "Cache should be initialized"
    assert tracker is not None, "Tracker should be initialized"
    print("✅ Cache and tracker initialized")
    
    # Test 2: Verify global instances
    print("\n[Test 2] Checking global instances...")
    assert get_cache() is cache, "Should get same cache instance"
    assert get_tracker() is tracker, "Should get same tracker instance"
    print("✅ Global instances working")
    
    # Test 3: Simulate some operations
    print("\n[Test 3] Simulating cache operations...")
    
    # Populate cache with fake data
    cache.set("project_test-123_issues", [
        {"id": "ISS-1", "title": "Issue 1"},
        {"id": "ISS-2", "title": "Issue 2"},
        {"id": "ISS-3", "title": "Issue 3"}
    ], ttl=300)
    
    cache.set("issue_ISS-1", {"id": "ISS-1", "title": "Issue 1", "status": "todo"}, ttl=180)
    
    print("  • Set 2 cache entries")
    
    # Simulate cache hits
    result1 = cache.get("project_test-123_issues")
    result2 = cache.get("issue_ISS-1")
    result3 = cache.get("issue_ISS-1")  # Second hit
    
    assert result1 is not None, "Should get cached issues list"
    assert result2 is not None, "Should get cached issue"
    print("  • Got 3 cache hits")
    
    # Simulate an API call being tracked
    tracker.track_call("update", "issue", {"id": "ISS-1"})
    print("  • Tracked 1 API call (update)")
    
    print("✅ Operations simulated successfully")
    
    # Test 4: Test invalidation
    print("\n[Test 4] Testing cache invalidation...")
    
    # Invalidate based on the update operation
    invalidate_cache_for_operations(cache, tracker, "test-123")
    
    # Check that cache was invalidated
    result_after = cache.get("issue_ISS-1")
    list_after = cache.get("project_test-123_issues")
    
    assert result_after is None, "Updated issue should be invalidated"
    assert list_after is None, "Issues list should be invalidated"
    print("✅ Cache invalidation working")
    
    # Test 5: Check combined stats
    print("\n[Test 5] Testing combined statistics...")
    
    stats = get_cache_status_summary(cache, tracker)
    
    assert stats["api_calls_made"] == 1, "Should have 1 API call"
    assert stats["cache_hits"] == 3, "Should have 3 cache hits"
    
    print(f"  • API calls made: {stats['api_calls_made']}")
    print(f"  • Cache hits: {stats['cache_hits']}")
    print(f"  • Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")
    print("✅ Statistics working correctly")
    
    # Test 6: Print combined stats (visual verification)
    print("\n[Test 6] Testing combined stats output...")
    print_combined_stats(cache, tracker)
    print("✅ Stats printing working")
    
    # Test 7: Verify cache stats
    print("\n[Test 7] Testing cache stats output...")
    cache.print_stats()
    print("✅ Cache stats printing working")
    
    # Final summary
    print("\n" + "="*70)
    print("  ✅ ALL INTEGRATION TESTS PASSED!")
    print("="*70)
    print("\nCache system is properly integrated and working.")
    print("\nExpected behavior in production:")
    print("  1. Cache initialized at agent startup")
    print("  2. Linear API calls tracked automatically")
    print("  3. Cache invalidated after write operations")
    print("  4. Combined stats shown after each session")
    print("  5. Full stats breakdown at end of run")
    print("\nReady for production use! 🚀")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_cache_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

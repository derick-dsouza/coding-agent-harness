"""
Test Linear API Cache
======================

Verify that the caching system works correctly.
"""

import json
import time
from pathlib import Path
import tempfile
import shutil

from linear_cache import LinearCache, CacheEntry, init_cache, get_cache


def test_basic_caching():
    """Test basic cache set/get operations."""
    print("\n" + "="*70)
    print("TEST 1: Basic Caching")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set a value
        cache.set("test_key", {"data": "test_value"}, ttl=300)
        
        # Get it back
        result = cache.get("test_key")
        assert result == {"data": "test_value"}, "Should get cached value"
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_hits"] == 1, "Should have 1 hit"
        assert stats["total_misses"] == 0, "Should have 0 misses"
        assert stats["total_sets"] == 1, "Should have 1 set"
        assert stats["hit_rate"] == 1.0, "Should have 100% hit rate"
        
        print("✅ Basic caching works")


def test_cache_miss():
    """Test cache misses."""
    print("\n" + "="*70)
    print("TEST 2: Cache Miss")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Try to get non-existent key
        result = cache.get("nonexistent")
        assert result is None, "Should return None for missing key"
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_misses"] == 1, "Should have 1 miss"
        
        print("✅ Cache misses work correctly")


def test_ttl_expiration():
    """Test TTL-based expiration."""
    print("\n" + "="*70)
    print("TEST 3: TTL Expiration")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set with short TTL
        cache.set("short_ttl", "value", ttl=1)
        
        # Should exist immediately
        result = cache.get("short_ttl")
        assert result == "value", "Should get value immediately"
        
        # Wait for expiration
        print("Waiting 2 seconds for TTL to expire...")
        time.sleep(2)
        
        # Should be expired now
        result = cache.get("short_ttl")
        assert result is None, "Should return None after TTL expires"
        
        # Check that entry was removed
        assert "short_ttl" not in cache.entries, "Expired entry should be removed"
        
        print("✅ TTL expiration works correctly")


def test_persistence():
    """Test that cache persists across instances."""
    print("\n" + "="*70)
    print("TEST 4: Persistence")
    print("="*70)
    
    tmpdir = tempfile.mkdtemp()
    try:
        project_dir = Path(tmpdir)
        
        # First instance
        cache1 = LinearCache(project_dir)
        cache1.set("persistent_key", "persistent_value", ttl=300)
        cache1.set("another_key", {"complex": "data"}, ttl=600)
        
        # Second instance (reload)
        cache2 = LinearCache(project_dir)
        
        # Should load from file
        result1 = cache2.get("persistent_key")
        result2 = cache2.get("another_key")
        
        assert result1 == "persistent_value", "Should load first value"
        assert result2 == {"complex": "data"}, "Should load second value"
        
        print("✅ Cache persistence works correctly")
        
    finally:
        shutil.rmtree(tmpdir)


def test_invalidation():
    """Test cache invalidation."""
    print("\n" + "="*70)
    print("TEST 5: Invalidation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Invalidate one
        cache.invalidate("key2")
        
        # Check results
        assert cache.get("key1") == "value1", "key1 should still exist"
        assert cache.get("key2") is None, "key2 should be invalidated"
        assert cache.get("key3") == "value3", "key3 should still exist"
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_invalidations"] == 1, "Should have 1 invalidation"
        
        print("✅ Invalidation works correctly")


def test_pattern_invalidation():
    """Test pattern-based invalidation."""
    print("\n" + "="*70)
    print("TEST 6: Pattern Invalidation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set values with patterns
        cache.set("issue_123", "issue data 123")
        cache.set("issue_456", "issue data 456")
        cache.set("issue_789", "issue data 789")
        cache.set("project_abc", "project data")
        cache.set("team_xyz", "team data")
        
        # Invalidate all issues
        cache.invalidate_pattern("issue_.*")
        
        # Check results
        assert cache.get("issue_123") is None, "issue_123 should be invalidated"
        assert cache.get("issue_456") is None, "issue_456 should be invalidated"
        assert cache.get("issue_789") is None, "issue_789 should be invalidated"
        assert cache.get("project_abc") == "project data", "project should remain"
        assert cache.get("team_xyz") == "team data", "team should remain"
        
        print("✅ Pattern invalidation works correctly")


def test_clear_expired():
    """Test clearing expired entries."""
    print("\n" + "="*70)
    print("TEST 7: Clear Expired")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set entries with different TTLs
        cache.set("fresh", "value", ttl=300)  # 5 min
        cache.set("expired1", "value", ttl=1)  # 1 sec
        cache.set("expired2", "value", ttl=1)  # 1 sec
        
        # Wait for some to expire
        print("Waiting 2 seconds for TTL to expire...")
        time.sleep(2)
        
        # Clear expired
        removed = cache.clear_expired()
        
        assert removed == 2, "Should remove 2 expired entries"
        assert "fresh" in cache.entries, "Fresh entry should remain"
        assert "expired1" not in cache.entries, "Expired1 should be removed"
        assert "expired2" not in cache.entries, "Expired2 should be removed"
        
        print("✅ Clear expired works correctly")


def test_hit_count():
    """Test hit count tracking."""
    print("\n" + "="*70)
    print("TEST 8: Hit Count Tracking")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set a value
        cache.set("popular", "value")
        
        # Access it multiple times
        for i in range(5):
            cache.get("popular")
        
        # Check hit count
        entry = cache.entries["popular"]
        assert entry.hit_count == 5, "Should have 5 hits"
        
        # Check global stats
        stats = cache.get_stats()
        assert stats["total_hits"] == 5, "Should have 5 total hits"
        
        print("✅ Hit count tracking works correctly")


def test_global_cache():
    """Test global cache initialization."""
    print("\n" + "="*70)
    print("TEST 9: Global Cache")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Initialize global cache
        cache = init_cache(project_dir)
        
        # Set a value
        cache.set("global_key", "global_value")
        
        # Get it through global accessor
        global_cache = get_cache()
        assert global_cache is cache, "Should get same instance"
        
        result = global_cache.get("global_key")
        assert result == "global_value", "Should get value through global cache"
        
        print("✅ Global cache works correctly")


def test_entry_info():
    """Test cache entry information."""
    print("\n" + "="*70)
    print("TEST 10: Entry Information")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        cache = LinearCache(project_dir)
        
        # Set a value
        cache.set("info_key", "some data", ttl=300)
        
        # Access it a few times
        cache.get("info_key")
        cache.get("info_key")
        
        # Get entry info
        info = cache.get_entry_info("info_key")
        
        assert info is not None, "Should get entry info"
        assert info["key"] == "info_key", "Should have correct key"
        assert info["hit_count"] == 2, "Should have 2 hits"
        assert info["is_expired"] == False, "Should not be expired"
        assert info["remaining_ttl"] > 290, "Should have ~300s TTL remaining"
        
        print(f"✅ Entry info works correctly")
        print(f"   Entry details: {info}")


def run_all_tests():
    """Run all cache tests."""
    print("\n" + "="*70)
    print("  LINEAR API CACHE - TEST SUITE")
    print("="*70)
    
    test_basic_caching()
    test_cache_miss()
    test_ttl_expiration()
    test_persistence()
    test_invalidation()
    test_pattern_invalidation()
    test_clear_expired()
    test_hit_count()
    test_global_cache()
    test_entry_info()
    
    print("\n" + "="*70)
    print("  ✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nThe Linear API cache is working correctly.")
    print("Ready for integration with agent.\n")


if __name__ == "__main__":
    run_all_tests()

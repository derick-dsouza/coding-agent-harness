"""
Test Linear API Call Tracker
=============================

Verify that the tracking system works correctly.
"""

import json
import time
from pathlib import Path
import tempfile
import shutil

from linear_tracker import LinearCallTracker, init_tracker


def test_basic_tracking():
    """Test basic call tracking functionality."""
    print("\n" + "="*70)
    print("TEST 1: Basic Call Tracking")
    print("="*70)
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tracker = LinearCallTracker(project_dir)
        
        # Track some calls
        tracker.track_call("list", "issues", {"project": "test-123"})
        tracker.track_call("create", "issue", {"title": "Test Issue"})
        tracker.track_call("update", "issue", {"id": "ISS-1", "status": "done"})
        
        # Verify counts
        assert len(tracker.session_calls) == 3, "Should have 3 session calls"
        assert len(tracker.history) == 3, "Should have 3 history calls"
        
        stats = tracker.get_session_stats()
        assert stats["total_calls"] == 3, "Stats should show 3 calls"
        assert stats["operations"]["list"] == 1, "Should have 1 list operation"
        assert stats["operations"]["create"] == 1, "Should have 1 create operation"
        assert stats["operations"]["update"] == 1, "Should have 1 update operation"
        assert stats["endpoints"]["issues"] == 1, "Should have 1 issues endpoint"
        assert stats["endpoints"]["issue"] == 2, "Should have 2 issue endpoints"
        
        print("✅ Basic tracking works correctly")
        tracker.print_session_summary()


def test_rate_limit_checking():
    """Test rate limit monitoring."""
    print("\n" + "="*70)
    print("TEST 2: Rate Limit Checking")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tracker = LinearCallTracker(project_dir)
        
        # Temporarily disable output during bulk tracking
        original_check = tracker._check_rate_limit
        tracker._check_rate_limit = lambda: None  # Disable warnings during test
        
        # Should be safe initially
        assert tracker.is_safe_to_call(), "Should be safe with no calls"
        
        # Simulate approaching limit (make 1400 calls)
        print("Simulating 1400 API calls (output suppressed)...")
        for i in range(1400):
            tracker.track_call("list", "issues")
        
        # Re-enable check
        tracker._check_rate_limit = original_check
        
        # Should be safe with buffer of 100 (1400 < 1500-100)
        # Wait, that's wrong: 1400 < 1400 (1500-100) is False!
        # Let me fix the assertion
        assert not tracker.is_safe_to_call(buffer=100), "Should NOT be safe with 1400 calls and buffer=100"
        
        # Should be safe with buffer of 50 (1400 < 1500-50 = 1450)
        assert tracker.is_safe_to_call(buffer=50), "Should be safe with buffer=50"
        
        print(f"✅ Rate limit checking works correctly")
        print(f"   Current calls: {len(tracker.session_calls)}")
        print(f"   Safe with buffer=50: {tracker.is_safe_to_call(buffer=50)}")
        print(f"   Safe with buffer=100: {tracker.is_safe_to_call(buffer=100)}")


def test_time_window():
    """Test time window filtering."""
    print("\n" + "="*70)
    print("TEST 3: Time Window Filtering")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tracker = LinearCallTracker(project_dir)
        
        # Add call now
        tracker.track_call("list", "issues")
        
        # Add call 2 hours ago (manually)
        old_call = {
            "timestamp": time.time() - (2 * 3600),
            "datetime": "2 hours ago",
            "operation": "create",
            "endpoint": "issue",
            "metadata": {}
        }
        tracker.history.append(old_call)
        
        # Get calls in last hour
        calls_last_hour = tracker.get_calls_in_window(3600)
        assert len(calls_last_hour) == 1, "Should only get call from last hour"
        
        # Get calls in last 3 hours
        calls_last_3h = tracker.get_calls_in_window(3 * 3600)
        assert len(calls_last_3h) == 2, "Should get both calls in last 3 hours"
        
        print("✅ Time window filtering works correctly")


def test_persistence():
    """Test that tracking data persists across sessions."""
    print("\n" + "="*70)
    print("TEST 4: Persistence")
    print("="*70)
    
    tmpdir = tempfile.mkdtemp()
    try:
        project_dir = Path(tmpdir)
        
        # First session
        tracker1 = LinearCallTracker(project_dir)
        tracker1.track_call("list", "issues")
        tracker1.track_call("create", "issue")
        
        # Second session (reload)
        tracker2 = LinearCallTracker(project_dir)
        assert len(tracker2.history) == 2, "Should load 2 calls from history"
        
        # Add more calls
        tracker2.track_call("update", "issue")
        
        # Third session (reload again)
        tracker3 = LinearCallTracker(project_dir)
        assert len(tracker3.history) == 3, "Should load 3 calls from history"
        
        print("✅ Persistence works correctly")
        
    finally:
        shutil.rmtree(tmpdir)


def test_cleanup():
    """Test cleanup of old calls."""
    print("\n" + "="*70)
    print("TEST 5: Cleanup Old Calls")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tracker = LinearCallTracker(project_dir)
        
        # Add recent call
        tracker.track_call("list", "issues")
        
        # Add old call (8 days ago)
        old_call = {
            "timestamp": time.time() - (8 * 24 * 3600),
            "datetime": "8 days ago",
            "operation": "create",
            "endpoint": "issue",
            "metadata": {}
        }
        tracker.history.append(old_call)
        tracker._save_history()
        
        assert len(tracker.history) == 2, "Should have 2 calls before cleanup"
        
        # Cleanup (keep last 7 days)
        tracker.cleanup_old_calls(days=7)
        
        assert len(tracker.history) == 1, "Should have 1 call after cleanup"
        assert tracker.history[0]["operation"] == "list", "Should keep recent call"
        
        print("✅ Cleanup works correctly")


def test_global_tracker():
    """Test global tracker initialization."""
    print("\n" + "="*70)
    print("TEST 6: Global Tracker")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Initialize global tracker
        tracker = init_tracker(project_dir)
        
        # Verify we can get it
        from linear_tracker import get_tracker
        assert get_tracker() is tracker, "Should get same tracker instance"
        
        print("✅ Global tracker works correctly")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("  LINEAR API CALL TRACKER - TEST SUITE")
    print("="*70)
    
    test_basic_tracking()
    test_rate_limit_checking()
    test_time_window()
    test_persistence()
    test_cleanup()
    test_global_tracker()
    
    print("\n" + "="*70)
    print("  ✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nThe Linear API call tracker is working correctly.")
    print("It will now track all Linear API calls during agent sessions.\n")


if __name__ == "__main__":
    run_all_tests()

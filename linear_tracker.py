"""
Linear API Call Tracking & Rate Limit Monitoring
=================================================

Tracks all Linear API calls to help understand usage patterns and avoid rate limits.

Features:
- Per-session call counting
- Persistent call history across sessions
- Rate limit monitoring (1500 calls/hour)
- Call type breakdown (create, update, list, etc.)
- Time-based analysis
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class LinearCallTracker:
    """Tracks Linear API calls and monitors rate limits."""
    
    # Linear's rate limit
    RATE_LIMIT_PER_HOUR = 1500
    RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour
    
    def __init__(self, project_dir: Path):
        """
        Initialize tracker.
        
        Args:
            project_dir: Project directory for storing tracking data
        """
        self.project_dir = project_dir
        self.tracking_file = project_dir / ".linear_api_calls.json"
        self.session_calls = []
        self.session_start = time.time()
        
        # Load existing tracking data
        self.history = self._load_history()
        
    def _load_history(self) -> List[Dict]:
        """Load call history from file."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_history(self):
        """Save call history to file."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"⚠️  Warning: Could not save API tracking data: {e}")
    
    def track_call(
        self, 
        operation: str, 
        endpoint: str,
        metadata: Optional[Dict] = None
    ):
        """
        Track a Linear API call.
        
        Args:
            operation: Type of operation (create, update, list, get, delete)
            endpoint: Linear endpoint (issue, project, team, etc.)
            metadata: Additional metadata about the call
        """
        call_record = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "operation": operation,
            "endpoint": endpoint,
            "metadata": metadata or {}
        }
        
        # Add to session calls
        self.session_calls.append(call_record)
        
        # Add to persistent history
        self.history.append(call_record)
        
        # Save immediately (in case of crash)
        self._save_history()
        
        # Check rate limits
        self._check_rate_limit()
        
    def get_calls_in_window(self, window_seconds: int = None) -> List[Dict]:
        """
        Get all calls within the specified time window.
        
        Args:
            window_seconds: Time window in seconds (default: 1 hour)
            
        Returns:
            List of call records within the window
        """
        if window_seconds is None:
            window_seconds = self.RATE_LIMIT_WINDOW_SECONDS
            
        cutoff_time = time.time() - window_seconds
        return [
            call for call in self.history 
            if call["timestamp"] > cutoff_time
        ]
    
    def get_call_count_in_window(self, window_seconds: int = None) -> int:
        """Get number of calls in the specified time window."""
        return len(self.get_calls_in_window(window_seconds))
    
    def _check_rate_limit(self):
        """Check if we're approaching or have hit rate limits."""
        calls_last_hour = self.get_call_count_in_window()
        percent_used = (calls_last_hour / self.RATE_LIMIT_PER_HOUR) * 100
        
        if calls_last_hour >= self.RATE_LIMIT_PER_HOUR:
            print(f"\n🚨 RATE LIMIT HIT: {calls_last_hour}/{self.RATE_LIMIT_PER_HOUR} calls in last hour")
            print(f"   Wait {self._time_until_safe()} before making more calls")
        elif percent_used >= 90:
            print(f"\n⚠️  WARNING: {calls_last_hour}/{self.RATE_LIMIT_PER_HOUR} calls ({percent_used:.1f}%)")
            print(f"   Approaching rate limit - use caution")
        elif percent_used >= 75:
            print(f"\n⏰ NOTICE: {calls_last_hour}/{self.RATE_LIMIT_PER_HOUR} calls ({percent_used:.1f}%)")
    
    def _time_until_safe(self) -> str:
        """Calculate time until we're back under rate limit."""
        calls = self.get_calls_in_window()
        if not calls:
            return "0 minutes"
        
        # Find the oldest call in the window
        oldest_call = min(call["timestamp"] for call in calls)
        
        # Time until that call falls out of the window
        time_until_safe = oldest_call + self.RATE_LIMIT_WINDOW_SECONDS - time.time()
        
        if time_until_safe <= 0:
            return "0 minutes"
        
        minutes = int(time_until_safe / 60)
        seconds = int(time_until_safe % 60)
        
        if minutes > 0:
            return f"{minutes} minutes, {seconds} seconds"
        return f"{seconds} seconds"
    
    def is_safe_to_call(self, buffer: int = 100) -> bool:
        """
        Check if it's safe to make another API call.
        
        Args:
            buffer: Safety buffer (don't use all 1500 calls)
            
        Returns:
            True if safe to make calls
        """
        calls_last_hour = self.get_call_count_in_window()
        return calls_last_hour < (self.RATE_LIMIT_PER_HOUR - buffer)
    
    def get_session_stats(self) -> Dict:
        """Get statistics for current session."""
        operation_counts = defaultdict(int)
        endpoint_counts = defaultdict(int)
        
        for call in self.session_calls:
            operation_counts[call["operation"]] += 1
            endpoint_counts[call["endpoint"]] += 1
        
        return {
            "total_calls": len(self.session_calls),
            "session_duration_seconds": time.time() - self.session_start,
            "operations": dict(operation_counts),
            "endpoints": dict(endpoint_counts),
            "calls_last_hour": self.get_call_count_in_window(),
            "rate_limit_percent": (self.get_call_count_in_window() / self.RATE_LIMIT_PER_HOUR) * 100
        }
    
    def get_breakdown(self) -> Dict:
        """Get detailed breakdown of API usage."""
        calls_last_hour = self.get_calls_in_window()
        
        operation_counts = defaultdict(int)
        endpoint_counts = defaultdict(int)
        
        for call in calls_last_hour:
            operation_counts[call["operation"]] += 1
            endpoint_counts[call["endpoint"]] += 1
        
        return {
            "window": "last_hour",
            "total_calls": len(calls_last_hour),
            "rate_limit": self.RATE_LIMIT_PER_HOUR,
            "percent_used": (len(calls_last_hour) / self.RATE_LIMIT_PER_HOUR) * 100,
            "time_until_safe": self._time_until_safe(),
            "operations": dict(sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)),
            "endpoints": dict(sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True))
        }
    
    def print_session_summary(self):
        """Print a summary of the current session's API usage."""
        stats = self.get_session_stats()
        
        print("\n" + "="*70)
        print("  LINEAR API USAGE - SESSION SUMMARY")
        print("="*70)
        print(f"\nSession calls: {stats['total_calls']}")
        print(f"Session duration: {stats['session_duration_seconds']:.1f}s")
        print(f"\nCalls in last hour: {stats['calls_last_hour']}/{self.RATE_LIMIT_PER_HOUR}")
        print(f"Rate limit usage: {stats['rate_limit_percent']:.1f}%")
        
        if stats['operations']:
            print("\nOperations:")
            for op, count in sorted(stats['operations'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {op:15s}: {count}")
        
        if stats['endpoints']:
            print("\nEndpoints:")
            for endpoint, count in sorted(stats['endpoints'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {endpoint:15s}: {count}")
        
        print("="*70)
    
    def print_breakdown(self):
        """Print detailed breakdown of API usage."""
        breakdown = self.get_breakdown()
        
        print("\n" + "="*70)
        print("  LINEAR API USAGE - DETAILED BREAKDOWN")
        print("="*70)
        print(f"\nTime window: {breakdown['window']}")
        print(f"Total calls: {breakdown['total_calls']}/{breakdown['rate_limit']}")
        print(f"Usage: {breakdown['percent_used']:.1f}%")
        
        if breakdown['total_calls'] >= breakdown['rate_limit'] * 0.75:
            print(f"Time until safe: {breakdown['time_until_safe']}")
        
        if breakdown['operations']:
            print("\nTop Operations:")
            for op, count in list(breakdown['operations'].items())[:5]:
                print(f"  {op:15s}: {count:4d} calls")
        
        if breakdown['endpoints']:
            print("\nTop Endpoints:")
            for endpoint, count in list(breakdown['endpoints'].items())[:5]:
                print(f"  {endpoint:15s}: {count:4d} calls")
        
        print("="*70)
    
    def cleanup_old_calls(self, days: int = 7):
        """
        Remove calls older than specified days from history.
        
        Args:
            days: Keep calls from last N days
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        
        old_count = len(self.history)
        self.history = [
            call for call in self.history 
            if call["timestamp"] > cutoff_time
        ]
        
        removed = old_count - len(self.history)
        if removed > 0:
            print(f"🧹 Cleaned up {removed} old API call records (older than {days} days)")
            self._save_history()


# Global tracker instance (initialized by agent)
_tracker: Optional[LinearCallTracker] = None


def init_tracker(project_dir: Path):
    """Initialize the global tracker."""
    global _tracker
    _tracker = LinearCallTracker(project_dir)
    return _tracker


def get_tracker() -> Optional[LinearCallTracker]:
    """Get the global tracker instance."""
    return _tracker


def track_linear_call(operation: str, endpoint: str, metadata: Dict = None):
    """
    Convenience function to track a Linear API call.
    
    Args:
        operation: Type of operation (create, update, list, get)
        endpoint: Linear endpoint (issue, project, team)
        metadata: Additional metadata
    """
    if _tracker:
        _tracker.track_call(operation, endpoint, metadata)

"""
Linear API Caching System
==========================

Implements local caching for Linear API calls to reduce rate limit usage.

Features:
- TTL-based cache expiration
- Automatic invalidation on writes
- Cache hit/miss tracking
- Persistent JSON storage
- Integration with existing tracker
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern
import re
from datetime import datetime


@dataclass
class CacheEntry:
    """Represents a single cache entry."""
    data: Any
    timestamp: float
    ttl: int
    hit_count: int = 0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        age = time.time() - self.timestamp
        return age > self.ttl
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "data": self.data,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "hit_count": self.hit_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            data=d["data"],
            timestamp=d["timestamp"],
            ttl=d["ttl"],
            hit_count=d.get("hit_count", 0),
            metadata=d.get("metadata", {})
        )


class LinearCache:
    """
    Cache manager for Linear API responses.
    
    Implements TTL-based caching with automatic expiration and
    statistics tracking.
    """
    
    CACHE_VERSION = "1.0"
    
    # Default TTLs (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    TTL_LIST_ISSUES = 300  # 5 minutes
    TTL_GET_ISSUE = 180  # 3 minutes
    TTL_LIST_PROJECTS = 3600  # 1 hour
    TTL_GET_PROJECT = 3600  # 1 hour
    TTL_LIST_TEAMS = 86400  # 1 day
    TTL_GET_TEAM = 86400  # 1 day
    
    def __init__(self, project_dir: Path, default_ttl: int = None):
        """
        Initialize cache manager.
        
        Args:
            project_dir: Project directory for cache file
            default_ttl: Default TTL in seconds (default: 300)
        """
        self.project_dir = project_dir
        self.cache_file = project_dir / ".linear_cache.json"
        self.default_ttl = default_ttl or self.DEFAULT_TTL
        
        self.entries: Dict[str, CacheEntry] = {}
        self.stats = {
            "total_hits": 0,
            "total_misses": 0,
            "total_sets": 0,
            "total_invalidations": 0
        }
        
        # Load existing cache
        self._load()
        
        # Clean expired entries on init
        self.clear_expired()
    
    def _load(self):
        """Load cache from file."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Validate version
            if data.get("cache_version") != self.CACHE_VERSION:
                print(f"⚠️  Cache version mismatch, starting fresh")
                return
            
            # Load entries
            for key, entry_dict in data.get("entries", {}).items():
                self.entries[key] = CacheEntry.from_dict(entry_dict)
            
            # Load stats
            self.stats = data.get("stats", self.stats)
            
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"⚠️  Could not load cache: {e}, starting fresh")
            self.entries = {}
    
    def _save(self):
        """Save cache to file."""
        try:
            data = {
                "cache_version": self.CACHE_VERSION,
                "entries": {
                    key: entry.to_dict() 
                    for key, entry in self.entries.items()
                },
                "stats": self.stats
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except IOError as e:
            print(f"⚠️  Could not save cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if exists and not expired, None otherwise
        """
        entry = self.entries.get(key)
        
        if entry is None:
            self.stats["total_misses"] += 1
            return None
        
        if entry.is_expired():
            # Expired - remove and return miss
            del self.entries[key]
            self.stats["total_misses"] += 1
            self._save()
            return None
        
        # Cache hit
        entry.hit_count += 1
        self.stats["total_hits"] += 1
        self._save()
        
        return entry.data
    
    def set(self, key: str, data: Any, ttl: int = None):
        """
        Set cache value.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl,
            hit_count=0
        )
        
        self.entries[key] = entry
        self.stats["total_sets"] += 1
        self._save()
    
    def invalidate(self, key: str):
        """
        Invalidate (remove) a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self.entries:
            del self.entries[key]
            self.stats["total_invalidations"] += 1
            self._save()
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Regex pattern (e.g., "issue_.*", "project_.*_issues")
        """
        regex = re.compile(pattern)
        keys_to_remove = [
            key for key in self.entries.keys()
            if regex.match(key)
        ]
        
        for key in keys_to_remove:
            del self.entries[key]
            self.stats["total_invalidations"] += 1
        
        if keys_to_remove:
            self._save()
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.entries[key]
        
        if expired_keys:
            self._save()
        
        return len(expired_keys)
    
    def clear_all(self):
        """Clear all cache entries."""
        self.entries = {}
        self.stats["total_invalidations"] += 1
        self._save()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.stats["total_hits"] + self.stats["total_misses"]
        hit_rate = (self.stats["total_hits"] / total_requests) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self.entries),
            "total_hits": self.stats["total_hits"],
            "total_misses": self.stats["total_misses"],
            "total_sets": self.stats["total_sets"],
            "total_invalidations": self.stats["total_invalidations"],
            "hit_rate": hit_rate,
            "requests": total_requests
        }
    
    def print_stats(self):
        """Print cache statistics."""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("  LINEAR API CACHE STATISTICS")
        print("="*70)
        print(f"\nCache entries: {stats['total_entries']}")
        print(f"\nRequests:")
        print(f"  Total:  {stats['requests']}")
        print(f"  Hits:   {stats['total_hits']} ({stats['hit_rate']*100:.1f}%)")
        print(f"  Misses: {stats['total_misses']}")
        print(f"\nMutations:")
        print(f"  Sets:          {stats['total_sets']}")
        print(f"  Invalidations: {stats['total_invalidations']}")
        print("="*70)
    
    def get_entry_info(self, key: str) -> Optional[dict]:
        """
        Get information about a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Dictionary with entry info or None
        """
        entry = self.entries.get(key)
        if entry is None:
            return None
        
        age = time.time() - entry.timestamp
        remaining_ttl = max(0, entry.ttl - age)
        
        return {
            "key": key,
            "hit_count": entry.hit_count,
            "age_seconds": age,
            "remaining_ttl": remaining_ttl,
            "is_expired": entry.is_expired(),
            "data_size": len(str(entry.data))
        }
    
    def list_entries(self) -> List[dict]:
        """List all cache entries with their info."""
        return [
            self.get_entry_info(key)
            for key in self.entries.keys()
        ]


# Global cache instance
_cache: Optional[LinearCache] = None


def init_cache(project_dir: Path, default_ttl: int = None) -> LinearCache:
    """Initialize the global cache."""
    global _cache
    _cache = LinearCache(project_dir, default_ttl)
    return _cache


def get_cache() -> Optional[LinearCache]:
    """Get the global cache instance."""
    return _cache

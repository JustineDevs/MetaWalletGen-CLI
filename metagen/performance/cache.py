"""
Cache Management System for MetaWalletGen CLI.

This module provides intelligent caching capabilities for wallet data,
encryption keys, and frequently accessed resources to improve performance.
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable, Union
from collections import OrderedDict, defaultdict
import hashlib
import pickle
import sqlite3
from pathlib import Path


@dataclass
class CacheEntry:
    """Cache entry data structure."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: Optional[int] = None
    tags: List[str] = None


@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    memory_usage_percent: float
    last_cleanup: datetime


class CachePolicy(OrderedDict):
    """LRU cache policy implementation."""
    
    def __init__(self, maxsize=128):
        super().__init__()
        self.maxsize = maxsize
    
    def __getitem__(self, key):
        # Move to end (most recently used)
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value
    
    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        else:
            if len(self) >= self.maxsize:
                # Remove least recently used item
                self.popitem(last=False)
        super().__setitem__(key, value)


class CacheManager:
    """Intelligent cache management system."""
    
    def __init__(self, max_memory_mb: int = 100, max_entries: int = 1000,
                 cleanup_interval: float = 60.0, enable_persistence: bool = True):
        """Initialize cache manager."""
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cleanup_interval = cleanup_interval
        self.enable_persistence = enable_persistence
        
        self.logger = logging.getLogger(__name__)
        
        # Cache storage
        self.cache = {}
        self.cache_policy = CachePolicy(maxsize=max_entries)
        
        # Statistics
        self.stats = CacheStats(
            total_entries=0,
            total_size_bytes=0,
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            hit_rate=0.0,
            memory_usage_percent=0.0,
            last_cleanup=datetime.now(timezone.utc)
        )
        
        # Cache tags for grouping
        self.tagged_entries = defaultdict(set)
        
        # Persistence
        self.persistence_file = "cache.db" if enable_persistence else None
        self.persistence_lock = threading.Lock()
        
        # Cleanup thread
        self.cleanup_thread = None
        self.stop_event = threading.Event()
        
        # Initialize persistence
        if self.enable_persistence:
            self._init_persistence()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _init_persistence(self):
        """Initialize persistent storage."""
        try:
            with sqlite3.connect(self.persistence_file) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at TEXT NOT NULL,
                        accessed_at TEXT NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        size_bytes INTEGER DEFAULT 0,
                        ttl_seconds INTEGER,
                        tags TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_created_at ON cache_entries(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON cache_entries(accessed_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_tags ON cache_entries(tags)")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize persistence: {e}")
            self.enable_persistence = False
    
    def _start_cleanup_thread(self):
        """Start the cleanup thread."""
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_loop(self):
        """Main cleanup loop."""
        while not self.stop_event.is_set():
            try:
                self._cleanup_expired_entries()
                self._enforce_memory_limits()
                
                # Update statistics
                self._update_stats()
                
                # Wait for next cleanup cycle
                self.stop_event.wait(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                time.sleep(5.0)
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries."""
        current_time = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.ttl_seconds is not None:
                expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
                if current_time > expiry_time:
                    expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            self._remove_entry(key)
            self.logger.debug(f"Removed expired cache entry: {key}")
    
    def _enforce_memory_limits(self):
        """Enforce memory and entry limits."""
        # Check entry count limit
        while len(self.cache) > self.max_entries:
            # Remove least recently used entry
            if self.cache_policy:
                lru_key = next(iter(self.cache_policy))
                self._remove_entry(lru_key)
                self.stats.eviction_count += 1
        
        # Check memory limit
        while self.stats.total_size_bytes > self.max_memory_bytes and self.cache:
            # Remove largest entry
            largest_key = max(self.cache.keys(), key=lambda k: self.cache[k].size_bytes)
            self._remove_entry(largest_key)
            self.stats.eviction_count += 1
    
    def _remove_entry(self, key: str):
        """Remove a cache entry."""
        if key in self.cache:
            entry = self.cache[key]
            
            # Update statistics
            self.stats.total_entries -= 1
            self.stats.total_size_bytes -= entry.size_bytes
            
            # Remove from cache
            del self.cache[key]
            
            # Remove from policy
            if key in self.cache_policy:
                del self.cache_policy[key]
            
            # Remove from tags
            if entry.tags:
                for tag in entry.tags:
                    if key in self.tagged_entries[tag]:
                        self.tagged_entries[tag].remove(key)
            
            # Remove from persistence
            if self.enable_persistence:
                self._remove_from_persistence(key)
    
    def _remove_from_persistence(self, key: str):
        """Remove entry from persistent storage."""
        try:
            with self.persistence_lock:
                with sqlite3.connect(self.persistence_file) as conn:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        except Exception as e:
            self.logger.error(f"Failed to remove from persistence: {e}")
    
    def _update_stats(self):
        """Update cache statistics."""
        if self.stats.hit_count + self.stats.miss_count > 0:
            self.stats.hit_rate = self.stats.hit_count / (self.stats.hit_count + self.stats.miss_count)
        
        if self.max_memory_bytes > 0:
            self.stats.memory_usage_percent = (self.stats.total_size_bytes / self.max_memory_bytes) * 100
        
        self.stats.last_cleanup = datetime.now(timezone.utc)
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate the size of a value in bytes."""
        try:
            # Try to serialize and get size
            serialized = pickle.dumps(value)
            return len(serialized)
        except Exception:
            # Fallback to string representation
            return len(str(value).encode('utf-8'))
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if entry.ttl_seconds is not None:
                expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
                if datetime.now(timezone.utc) > expiry_time:
                    self._remove_entry(key)
                    self.stats.miss_count += 1
                    return default
            
            # Update access statistics
            entry.accessed_at = datetime.now(timezone.utc)
            entry.access_count += 1
            
            # Update policy
            if key in self.cache_policy:
                self.cache_policy[key] = entry
            
            self.stats.hit_count += 1
            return entry.value
        else:
            self.stats.miss_count += 1
            return default
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
            tags: List[str] = None) -> bool:
        """Set a value in cache."""
        try:
            # Calculate size
            size_bytes = self._calculate_size(value)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(timezone.utc),
                accessed_at=datetime.now(timezone.utc),
                access_count=1,
                size_bytes=size_bytes,
                ttl_seconds=ttl_seconds,
                tags=tags or []
            )
            
            # Check if we need to make space
            if len(self.cache) >= self.max_entries:
                self._enforce_memory_limits()
            
            if self.stats.total_size_bytes + size_bytes > self.max_memory_bytes:
                self._enforce_memory_limits()
            
            # Add to cache
            self.cache[key] = entry
            self.cache_policy[key] = entry
            
            # Update statistics
            self.stats.total_entries += 1
            self.stats.total_size_bytes += size_bytes
            
            # Add to tags
            if tags:
                for tag in tags:
                    self.tagged_entries[tag].add(key)
            
            # Add to persistence
            if self.enable_persistence:
                self._add_to_persistence(entry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set cache entry: {e}")
            return False
    
    def _add_to_persistence(self, entry: CacheEntry):
        """Add entry to persistent storage."""
        try:
            with self.persistence_lock:
                with sqlite3.connect(self.persistence_file) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries (
                            key, value, created_at, accessed_at, access_count,
                            size_bytes, ttl_seconds, tags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.key,
                        pickle.dumps(entry.value),
                        entry.created_at.isoformat(),
                        entry.accessed_at.isoformat(),
                        entry.access_count,
                        entry.size_bytes,
                        entry.ttl_seconds,
                        json.dumps(entry.tags) if entry.tags else None
                    ))
        except Exception as e:
            self.logger.error(f"Failed to add to persistence: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        if key in self.cache:
            self._remove_entry(key)
            return True
        return False
    
    def clear(self, tags: List[str] = None):
        """Clear cache entries."""
        if tags:
            # Clear entries with specific tags
            keys_to_remove = set()
            for tag in tags:
                if tag in self.tagged_entries:
                    keys_to_remove.update(self.tagged_entries[tag])
            
            for key in keys_to_remove:
                self._remove_entry(key)
        else:
            # Clear all entries
            self.cache.clear()
            self.cache_policy.clear()
            self.tagged_entries.clear()
            
            # Reset statistics
            self.stats.total_entries = 0
            self.stats.total_size_bytes = 0
            
            # Clear persistence
            if self.enable_persistence:
                self._clear_persistence()
    
    def _clear_persistence(self):
        """Clear persistent storage."""
        try:
            with self.persistence_lock:
                with sqlite3.connect(self.persistence_file) as conn:
                    conn.execute("DELETE FROM cache_entries")
        except Exception as e:
            self.logger.error(f"Failed to clear persistence: {e}")
    
    def get_with_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Get all cache entries with specific tags."""
        result = {}
        
        for tag in tags:
            if tag in self.tagged_entries:
                for key in self.tagged_entries[tag]:
                    if key in self.cache:
                        result[key] = self.cache[key].value
        
        return result
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats
    
    def get_keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self.cache.keys())
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return key in self.cache
    
    def touch(self, key: str) -> bool:
        """Update access time for a key without retrieving value."""
        if key in self.cache:
            entry = self.cache[key]
            entry.accessed_at = datetime.now(timezone.utc)
            entry.access_count += 1
            
            # Update policy
            if key in self.cache_policy:
                self.cache_policy[key] = entry
            
            return True
        return False
    
    def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Set TTL for an existing cache entry."""
        if key in self.cache:
            self.cache[key].ttl_seconds = ttl_seconds
            return True
        return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a cache entry."""
        if key in self.cache:
            entry = self.cache[key]
            if entry.ttl_seconds is not None:
                elapsed = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                remaining = max(0, entry.ttl_seconds - elapsed)
                return int(remaining)
        return None
    
    def warm_up(self, warmup_data: Dict[str, Any]):
        """Warm up cache with predefined data."""
        for key, value in warmup_data.items():
            self.set(key, value)
    
    def export_cache_info(self, format: str = "json", file_path: str = None) -> str:
        """Export cache information to file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"cache_info_{timestamp}.{format}"
        
        try:
            export_data = {
                'stats': asdict(self.stats),
                'entries': {},
                'tags': dict(self.tagged_entries)
            }
            
            # Export entry information (without values to avoid large files)
            for key, entry in self.cache.items():
                export_data['entries'][key] = {
                    'created_at': entry.created_at.isoformat(),
                    'accessed_at': entry.accessed_at.isoformat(),
                    'access_count': entry.access_count,
                    'size_bytes': entry.size_bytes,
                    'ttl_seconds': entry.ttl_seconds,
                    'tags': entry.tags
                }
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Cache info exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export cache info: {e}")
            raise
    
    def load_from_persistence(self):
        """Load cache entries from persistent storage."""
        if not self.enable_persistence:
            return
        
        try:
            with self.persistence_lock:
                with sqlite3.connect(self.persistence_file) as conn:
                    cursor = conn.execute("SELECT * FROM cache_entries")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        try:
                            # Parse row data
                            key, value_blob, created_at, accessed_at, access_count, \
                            size_bytes, ttl_seconds, tags_json = row
                            
                            # Create entry
                            entry = CacheEntry(
                                key=key,
                                value=pickle.loads(value_blob),
                                created_at=datetime.fromisoformat(created_at),
                                accessed_at=datetime.fromisoformat(accessed_at),
                                access_count=access_count,
                                size_bytes=size_bytes,
                                ttl_seconds=ttl_seconds,
                                tags=json.loads(tags_json) if tags_json else []
                            )
                            
                            # Add to cache
                            self.cache[key] = entry
                            self.cache_policy[key] = entry
                            
                            # Add to tags
                            if entry.tags:
                                for tag in entry.tags:
                                    self.tagged_entries[tag].add(key)
                            
                            # Update statistics
                            self.stats.total_entries += 1
                            self.stats.total_size_bytes += size_bytes
                            
                        except Exception as e:
                            self.logger.warning(f"Failed to load cache entry {key}: {e}")
                            continue
                            
        except Exception as e:
            self.logger.error(f"Failed to load from persistence: {e}")
    
    def close(self):
        """Close the cache manager."""
        self.stop_event.set()
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
        
        # Save to persistence
        if self.enable_persistence:
            self._save_to_persistence()
    
    def _save_to_persistence(self):
        """Save all cache entries to persistent storage."""
        try:
            with self.persistence_lock:
                with sqlite3.connect(self.persistence_file) as conn:
                    # Clear existing data
                    conn.execute("DELETE FROM cache_entries")
                    
                    # Insert current entries
                    for entry in self.cache.values():
                        conn.execute("""
                            INSERT INTO cache_entries (
                                key, value, created_at, accessed_at, access_count,
                                size_bytes, ttl_seconds, tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry.key,
                            pickle.dumps(entry.value),
                            entry.created_at.isoformat(),
                            entry.accessed_at.isoformat(),
                            entry.access_count,
                            entry.size_bytes,
                            entry.ttl_seconds,
                            json.dumps(entry.tags) if entry.tags else None
                        ))
                        
        except Exception as e:
            self.logger.error(f"Failed to save to persistence: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def create_cache_manager(max_memory_mb: int = 100, max_entries: int = 1000,
                        cleanup_interval: float = 60.0, 
                        enable_persistence: bool = True) -> CacheManager:
    """Create a new cache manager instance."""
    return CacheManager(max_memory_mb, max_entries, cleanup_interval, enable_persistence)


def quick_cache_test():
    """Quick test of cache functionality."""
    with create_cache_manager(max_memory_mb=10, max_entries=100) as cache:
        # Test basic operations
        cache.set("test_key", "test_value", ttl_seconds=60, tags=["test"])
        
        # Test retrieval
        value = cache.get("test_key")
        print(f"Retrieved value: {value}")
        
        # Test statistics
        stats = cache.get_stats()
        print(f"Cache stats: {stats.total_entries} entries, {stats.hit_rate:.2%} hit rate")
        
        # Test tags
        tagged_values = cache.get_with_tags(["test"])
        print(f"Tagged values: {tagged_values}")


# Example usage
if __name__ == "__main__":
    quick_cache_test()

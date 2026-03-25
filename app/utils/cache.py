"""Simple TTL-based in-memory cache."""

import time
import threading


class TTLCache:
    """Thread-safe in-memory cache with time-to-live expiration."""

    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        """Get a value from cache. Returns None if expired or missing."""
        with self._lock:
            if key in self._store:
                value, expiry = self._store[key]
                if time.time() < expiry:
                    return value
                del self._store[key]
        return None

    def set(self, key, value, ttl=300):
        """Set a value in cache with a TTL in seconds."""
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def delete(self, key):
        """Remove a key from cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()


# Global cache instance
cache = TTLCache()

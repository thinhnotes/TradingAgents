"""
cache.py - Caching layer for TradingAgents data fetching.

This module provides a caching mechanism to reduce API calls and save on LLM tokens.
It supports both file-based JSON storage and optional Redis caching.

Features:
- Time-based expiration with configurable TTL
- JSON file-based local storage (default)
- Optional Redis support for distributed caching
- Thread-safe operations
- Automatic cache cleanup of expired entries

Usage:
    from tradingagents.dataflows.cache import DataCache

    # Initialize cache with default settings
    cache = DataCache()

    # Or with Redis
    cache = DataCache(use_redis=True, redis_url="redis://localhost:6379/0")

    # Store and retrieve data
    cache.set("my_key", {"data": "value"}, ttl_seconds=3600)
    data = cache.get("my_key")
"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import os
import threading

# Try to import redis for optional Redis support
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# Default cache configuration
DEFAULT_CACHE_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "data_cache"
)
DEFAULT_TTL_SECONDS = 3600  # 1 hour default TTL
DEFAULT_NEWS_TTL_SECONDS = 1800  # 30 minutes for news data
DEFAULT_STOCK_TTL_SECONDS = 3600  # 1 hour for stock data
DEFAULT_INDICATORS_TTL_SECONDS = 86400  # 24 hours for indicators (rarely change)


class CacheEntry:
    """
    Represents a single cache entry with value and expiration time.
    """

    def __init__(self, value: Any, expires_at: datetime):
        """
        Initialize a cache entry.

        Args:
            value: The cached value
            expires_at: DateTime when this entry expires
        """
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for JSON serialization."""
        return {
            "value": self.value,
            "expires_at": self.expires_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create cache entry from dictionary."""
        expires_at = datetime.fromisoformat(data["expires_at"])
        return cls(value=data["value"], expires_at=expires_at)


class DataCache:
    """
    Data caching layer with file-based storage and optional Redis support.

    This class provides a simple interface for caching API responses to reduce
    the number of API calls and save on LLM tokens.

    Attributes:
        cache_dir: Directory for file-based cache storage
        default_ttl: Default time-to-live for cache entries in seconds
        use_redis: Whether to use Redis for caching
        redis_client: Redis client instance (if Redis is enabled)
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        default_ttl: int = DEFAULT_TTL_SECONDS,
        use_redis: bool = False,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize the data cache.

        Args:
            cache_dir: Directory for file-based cache. Defaults to data_cache/.
            default_ttl: Default TTL in seconds. Defaults to 3600 (1 hour).
            use_redis: Whether to use Redis instead of file-based caching.
            redis_url: Redis connection URL. Required if use_redis=True.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(DEFAULT_CACHE_DIR)
        self.default_ttl = default_ttl
        self.use_redis = use_redis
        self.redis_client = None
        self._lock = threading.RLock()

        # Initialize cache directory for file-based storage
        if not use_redis:
            self._init_file_cache()
        else:
            self._init_redis_cache(redis_url)

    def _init_file_cache(self) -> None:
        """Initialize file-based cache directory."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create cache directory: {e}")

    def _init_redis_cache(self, redis_url: Optional[str]) -> None:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis library is not installed. "
                "Install it with: pip install redis"
            )

        if not redis_url:
            # Try to get from environment variable
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
        except redis.exceptions.ConnectionError as e:
            raise RuntimeError(f"Failed to connect to Redis: {e}")

    def _generate_key(self, key: str) -> str:
        """
        Generate a safe cache key from input.

        Uses MD5 hash for file-based storage to avoid filesystem issues.

        Args:
            key: Original cache key

        Returns:
            Safe cache key string
        """
        # For Redis, we can use the key directly (with prefix)
        if self.use_redis:
            return f"tradingagents:{key}"

        # For file-based, hash the key to create valid filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return key_hash

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        safe_key = self._generate_key(key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if self.use_redis:
            return self._get_redis(key)
        return self._get_file(key)

    def _get_file(self, key: str) -> Optional[Any]:
        """Get value from file-based cache."""
        cache_path = self._get_cache_path(key)

        with self._lock:
            try:
                if not cache_path.exists():
                    return None

                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                entry = CacheEntry.from_dict(data)

                if entry.is_expired():
                    # Clean up expired entry
                    cache_path.unlink(missing_ok=True)
                    return None

                return entry.value

            except (json.JSONDecodeError, KeyError, OSError):
                # Invalid cache file, remove it
                cache_path.unlink(missing_ok=True)
                return None

    def _get_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None

        try:
            safe_key = self._generate_key(key)
            data = self.redis_client.get(safe_key)

            if data is None:
                return None

            # Redis handles expiration automatically, but we still decode JSON
            return json.loads(data)

        except (redis.exceptions.RedisError, json.JSONDecodeError):
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl_seconds: Time-to-live in seconds. Uses default_ttl if not specified.

        Returns:
            True if successfully cached, False otherwise
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl

        if self.use_redis:
            return self._set_redis(key, value, ttl_seconds)
        return self._set_file(key, value, ttl_seconds)

    def _set_file(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Store value in file-based cache."""
        cache_path = self._get_cache_path(key)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        entry = CacheEntry(value=value, expires_at=expires_at)

        with self._lock:
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
                return True

            except (OSError, TypeError) as e:
                # Failed to write cache
                return False

    def _set_redis(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Store value in Redis cache."""
        if not self.redis_client:
            return False

        try:
            safe_key = self._generate_key(key)
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(safe_key, ttl_seconds, serialized)
            return True

        except (redis.exceptions.RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if not found or error
        """
        if self.use_redis:
            return self._delete_redis(key)
        return self._delete_file(key)

    def _delete_file(self, key: str) -> bool:
        """Delete value from file-based cache."""
        cache_path = self._get_cache_path(key)

        with self._lock:
            try:
                if cache_path.exists():
                    cache_path.unlink()
                    return True
                return False
            except OSError:
                return False

    def _delete_redis(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self.redis_client:
            return False

        try:
            safe_key = self._generate_key(key)
            result = self.redis_client.delete(safe_key)
            return result > 0
        except redis.exceptions.RedisError:
            return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if self.use_redis:
            return self._clear_redis()
        return self._clear_file()

    def _clear_file(self) -> int:
        """Clear all file-based cache entries."""
        count = 0

        with self._lock:
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                        count += 1
                    except OSError:
                        pass
            except OSError:
                pass

        return count

    def _clear_redis(self) -> int:
        """Clear all Redis cache entries with tradingagents prefix."""
        if not self.redis_client:
            return 0

        try:
            # Find all keys with our prefix
            pattern = "tradingagents:*"
            keys = list(self.redis_client.scan_iter(match=pattern))

            if keys:
                return self.redis_client.delete(*keys)
            return 0

        except redis.exceptions.RedisError:
            return 0

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.

        This is automatically done on get() for file-based cache,
        and handled by Redis TTL for Redis cache.

        Returns:
            Number of expired entries removed
        """
        if self.use_redis:
            # Redis handles expiration automatically
            return 0
        return self._cleanup_file_expired()

    def _cleanup_file_expired(self) -> int:
        """Clean up expired file-based cache entries."""
        count = 0

        with self._lock:
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        entry = CacheEntry.from_dict(data)

                        if entry.is_expired():
                            cache_file.unlink()
                            count += 1

                    except (json.JSONDecodeError, KeyError, OSError):
                        # Invalid cache file, remove it
                        try:
                            cache_file.unlink()
                            count += 1
                        except OSError:
                            pass
            except OSError:
                pass

        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if self.use_redis:
            return self._get_redis_stats()
        return self._get_file_stats()

    def _get_file_stats(self) -> Dict[str, Any]:
        """Get file-based cache statistics."""
        total_entries = 0
        expired_entries = 0
        total_size_bytes = 0

        with self._lock:
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        total_entries += 1
                        total_size_bytes += cache_file.stat().st_size

                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        entry = CacheEntry.from_dict(data)
                        if entry.is_expired():
                            expired_entries += 1

                    except (json.JSONDecodeError, KeyError, OSError):
                        expired_entries += 1
            except OSError:
                pass

        return {
            "type": "file",
            "cache_dir": str(self.cache_dir),
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        }

    def _get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self.redis_client:
            return {"type": "redis", "status": "disconnected"}

        try:
            # Count keys with our prefix
            pattern = "tradingagents:*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            total_entries = len(keys)

            # Get Redis info
            info = self.redis_client.info("memory")
            used_memory = info.get("used_memory", 0)

            return {
                "type": "redis",
                "status": "connected",
                "total_entries": total_entries,
                "used_memory_bytes": used_memory,
                "used_memory_mb": round(used_memory / (1024 * 1024), 2),
            }

        except redis.exceptions.RedisError as e:
            return {"type": "redis", "status": "error", "error": str(e)}


# Module-level cache instance for convenience
_default_cache: Optional[DataCache] = None
_cache_lock = threading.Lock()


def get_cache() -> DataCache:
    """
    Get or create the default cache instance.

    The cache is configured based on environment variables:
    - REDIS_URL: If set, Redis will be used
    - TRADINGAGENTS_CACHE_DIR: Custom cache directory

    Returns:
        DataCache instance
    """
    global _default_cache

    with _cache_lock:
        if _default_cache is None:
            redis_url = os.environ.get("REDIS_URL")
            cache_dir = os.environ.get("TRADINGAGENTS_CACHE_DIR")

            # Use Redis if URL is set, otherwise use file-based cache
            use_redis = redis_url is not None and REDIS_AVAILABLE

            if use_redis:
                try:
                    _default_cache = DataCache(
                        use_redis=True,
                        redis_url=redis_url,
                    )
                except Exception:
                    # Fall back to file-based cache if Redis fails
                    _default_cache = DataCache(cache_dir=cache_dir)
            else:
                _default_cache = DataCache(cache_dir=cache_dir)

        return _default_cache


def set_cache(cache: DataCache) -> None:
    """
    Set the default cache instance.

    Useful for testing or custom configurations.

    Args:
        cache: DataCache instance to use as default
    """
    global _default_cache

    with _cache_lock:
        _default_cache = cache


def generate_cache_key(
    category: str,
    ticker: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate a standardized cache key.

    Args:
        category: Data category (e.g., 'stock_data', 'news', 'indicators')
        ticker: Stock ticker symbol
        start_date: Start date for date range
        end_date: End date for date range
        **kwargs: Additional key components

    Returns:
        Cache key string
    """
    parts = [category]

    if ticker:
        parts.append(ticker.upper())

    if start_date:
        parts.append(f"from_{start_date}")

    if end_date:
        parts.append(f"to_{end_date}")

    # Add any additional keyword arguments
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}_{value}")

    return ":".join(parts)


# TTL presets for different data types
TTL_PRESETS = {
    "stock_data": DEFAULT_STOCK_TTL_SECONDS,       # 1 hour
    "indicators": DEFAULT_INDICATORS_TTL_SECONDS,  # 24 hours
    "news": DEFAULT_NEWS_TTL_SECONDS,              # 30 minutes
    "fundamentals": 86400,                         # 24 hours (quarterly data)
    "balance_sheet": 86400,                        # 24 hours
    "cashflow": 86400,                             # 24 hours
    "income_statement": 86400,                     # 24 hours
    "company_overview": 604800,                    # 1 week (rarely changes)
}


def get_ttl_for_category(category: str) -> int:
    """
    Get recommended TTL for a data category.

    Args:
        category: Data category name

    Returns:
        TTL in seconds
    """
    return TTL_PRESETS.get(category, DEFAULT_TTL_SECONDS)


# Decorator for caching function results
def cached(
    category: str,
    ttl_seconds: Optional[int] = None,
    key_args: Optional[list] = None
):
    """
    Decorator to cache function results.

    Args:
        category: Cache category for TTL selection
        ttl_seconds: Override TTL (uses category default if not specified)
        key_args: List of argument names to use for cache key generation

    Returns:
        Decorated function

    Usage:
        @cached("stock_data", key_args=["ticker", "start_date", "end_date"])
        def get_stock_data(ticker, start_date, end_date):
            # ... fetch data
            return data
    """
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key from specified arguments
            cache_key_parts = {"category": category}

            if key_args:
                # Get argument names from function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                # Map positional args to their names
                for i, arg in enumerate(args):
                    if i < len(param_names) and param_names[i] in key_args:
                        cache_key_parts[param_names[i]] = arg

                # Add keyword arguments
                for key in key_args:
                    if key in kwargs:
                        cache_key_parts[key] = kwargs[key]

            cache_key = generate_cache_key(**cache_key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call the function
            result = func(*args, **kwargs)

            # Cache the result
            ttl = ttl_seconds if ttl_seconds is not None else get_ttl_for_category(category)
            cache.set(cache_key, result, ttl_seconds=ttl)

            return result

        return wrapper
    return decorator

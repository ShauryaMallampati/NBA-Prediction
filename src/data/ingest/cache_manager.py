"""Smart caching system for NBA data.

We try Redis first (fast in-memory cache), but if that's not available we fall back
to saving JSON files on disk. Either way, we avoid hitting the API too often.

Features:
- Redis for speed (with JSON file backup)
- Different cache lengths for different data types
- Easy cache clearing when needed
"""

import os
import json
import time
import logging
from typing import Any, Optional, Callable
from functools import wraps
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# Where we store cached files
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# How long different types of data stay cached (seconds)
CACHE_TTL = {
    "predictions": 300,          # 5 minutes
    "games": 300,                # 5 minutes
    "player_stats": 3600,        # 1 hour
    "team_stats": 3600,          # 1 hour
    "historical_games": 86400,   # 24 hours
    "season_averages": 86400,    # 24 hours
    "players_list": 86400,       # 24 hours
    "teams_list": 604800,        # 7 days
}

# Try to connect to Redis (it's okay if this fails)
try:
    import redis
    REDIS_AVAILABLE = True
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True
    )
    # Test the connection to make sure it's working
    redis_client.ping()
    logger.info("✅ Redis cache connected")
except Exception as e:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning(f"⚠️ Redis not available, using file cache only: {e}")


class CacheManager:
    """Handles caching with Redis or files as backup."""
    
    def __init__(self):
        """Set up the cache system."""
        self.redis_available = REDIS_AVAILABLE
        self.redis = redis_client
        logger.info(f"💾 Cache manager initialized (Redis: {self.redis_available})")
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Build a unique cache key from whatever we're requesting.
        
        Args:
            prefix: Type of data (like 'games' or 'player_stats')
            *args: Other identifiers
            **kwargs: Named parameters
        
        Returns:
            A unique string we can use to cache and retrieve this data
        """
        # Combine all arguments into a string
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # Create hash of key parts for consistent length
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]
        
        return f"nba:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Fetch from cache if it exists and hasn't expired.
        
        Args:
            key: The cache key
        
        Returns:
            Cached data or None if not found/expired
        """
        # Try Redis first
        if self.redis_available:
            try:
                value = self.redis.get(key)
                if value:
                    logger.debug(f"✅ Redis cache hit: {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to file cache
        cache_file = CACHE_DIR / f"{key.replace(':', '_')}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                
                # Check if expired
                if "expires_at" in data and time.time() < data["expires_at"]:
                    logger.debug(f"✅ File cache hit: {key}")
                    return data["value"]
                else:
                    logger.debug(f"🗑️ File cache expired: {key}")
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"File cache read error: {e}")
        
        logger.debug(f"❌ Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: str = "default") -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (overrides cache_type TTL)
            cache_type: Type of cache for default TTL
        
        Returns:
            True if successful
        """
        if ttl is None:
            ttl = CACHE_TTL.get(cache_type, 3600)
        
        # Try Redis first
        if self.redis_available:
            try:
                self.redis.setex(key, ttl, json.dumps(value))
                logger.debug(f"💾 Redis cache set: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Always write to file cache as backup
        try:
            cache_file = CACHE_DIR / f"{key.replace(':', '_')}.json"
            data = {
                "value": value,
                "expires_at": time.time() + ttl,
                "cached_at": time.time()
            }
            cache_file.write_text(json.dumps(data, indent=2))
            logger.debug(f"💾 File cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"File cache write error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful
        """
        success = True
        
        # Delete from Redis
        if self.redis_available:
            try:
                self.redis.delete(key)
                logger.debug(f"🗑️ Redis cache deleted: {key}")
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
                success = False
        
        # Delete from file cache
        cache_file = CACHE_DIR / f"{key.replace(':', '_')}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
                logger.debug(f"🗑️ File cache deleted: {key}")
            except Exception as e:
                logger.error(f"File cache delete error: {e}")
                success = False
        
        return success
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'nba:games:*')
        
        Returns:
            Number of keys deleted
        """
        count = 0
        
        # Clear from Redis
        if self.redis_available:
            try:
                keys = self.redis.keys(pattern)
                if keys:
                    count = self.redis.delete(*keys)
                    logger.info(f"🗑️ Redis cleared {count} keys matching {pattern}")
            except Exception as e:
                logger.warning(f"Redis pattern delete error: {e}")
        
        # Clear from file cache
        try:
            file_pattern = pattern.replace(":", "_").replace("*", "")
            for cache_file in CACHE_DIR.glob(f"{file_pattern}*.json"):
                cache_file.unlink()
                count += 1
            logger.info(f"🗑️ File cache cleared {count} files")
        except Exception as e:
            logger.error(f"File cache pattern delete error: {e}")
        
        return count
    
    def clear_all(self) -> bool:
        """Clear all cache data."""
        logger.warning("🗑️ Clearing ALL cache data!")
        
        # Clear Redis
        if self.redis_available:
            try:
                self.redis.flushdb()
                logger.info("✅ Redis cache cleared")
            except Exception as e:
                logger.error(f"Redis flush error: {e}")
        
        # Clear file cache
        try:
            for cache_file in CACHE_DIR.glob("*.json"):
                cache_file.unlink()
            logger.info("✅ File cache cleared")
            return True
        except Exception as e:
            logger.error(f"File cache clear error: {e}")
            return False


# Decorator for caching function results
def cached(cache_type: str = "default", ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        cache_type: Type of cache (determines default TTL)
        ttl: Override TTL in seconds
        key_prefix: Override key prefix (defaults to function name)
    
    Example:
        @cached(cache_type="player_stats", ttl=3600)
        def get_player_stats(player_id: int):
            # Expensive API call
            return fetch_from_api(player_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Create cache key
            prefix = key_prefix or func.__name__
            cache_key = cache._make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"⚡ Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"🔄 Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, ttl=ttl, cache_type=cache_type)
            
            return result
        return wrapper
    return decorator


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

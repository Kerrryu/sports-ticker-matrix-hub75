"""
Cache Layer for API Responses

Reduces API calls by caching responses for a configurable duration.
Helps with rate limiting and improves responsiveness.

Usage:
    from api.cache import Cache

    cache = Cache(ttl=60)  # 60 second TTL
    cache.set('nfl_scores', data)
    data = cache.get('nfl_scores')
"""

import time
import gc


class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl=60, max_items=20):
        """
        Initialize cache.

        Args:
            ttl: Time-to-live in seconds (default 60)
            max_items: Maximum items to store (default 20)
        """
        self.ttl = ttl
        self.max_items = max_items
        self._cache = {}

    def get(self, key):
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        item = self._cache[key]
        expires = item.get('expires', 0)

        # Check if expired
        if time.time() > expires:
            del self._cache[key]
            return None

        return item.get('value')

    def set(self, key, value, ttl=None):
        """
        Store item in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Optional TTL override
        """
        # Enforce max items
        if len(self._cache) >= self.max_items and key not in self._cache:
            self._evict_oldest()

        item_ttl = ttl if ttl is not None else self.ttl

        self._cache[key] = {
            'value': value,
            'expires': time.time() + item_ttl,
            'created': time.time()
        }

    def delete(self, key):
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cached items."""
        self._cache.clear()
        gc.collect()

    def has(self, key):
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def _evict_oldest(self):
        """Remove oldest item from cache."""
        if not self._cache:
            return

        oldest_key = None
        oldest_time = float('inf')

        for key, item in self._cache.items():
            created = item.get('created', 0)
            if created < oldest_time:
                oldest_time = created
                oldest_key = key

        if oldest_key:
            del self._cache[oldest_key]

    def cleanup(self):
        """Remove all expired items."""
        now = time.time()
        expired_keys = []

        for key, item in self._cache.items():
            if now > item.get('expires', 0):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            gc.collect()

        return len(expired_keys)

    def stats(self):
        """
        Get cache statistics.

        Returns:
            Dict with cache info
        """
        now = time.time()
        valid = 0
        expired = 0

        for item in self._cache.values():
            if now <= item.get('expires', 0):
                valid += 1
            else:
                expired += 1

        return {
            'total_items': len(self._cache),
            'valid_items': valid,
            'expired_items': expired,
            'max_items': self.max_items,
            'default_ttl': self.ttl,
        }


class ScorecardCache(Cache):
    """Specialized cache for sports scoreboards."""

    def __init__(self):
        """Initialize with sport-specific settings."""
        super().__init__(ttl=60, max_items=10)

    def get_scoreboard(self, sport):
        """Get cached scoreboard for sport."""
        return self.get(f"scoreboard_{sport}")

    def set_scoreboard(self, sport, data, ttl=None):
        """Cache scoreboard for sport."""
        # Use shorter TTL for live games
        if any(g.get('status') in ['live', 'in'] for g in data):
            ttl = 30  # 30 seconds for live games
        else:
            ttl = ttl or 120  # 2 minutes for non-live

        self.set(f"scoreboard_{sport}", data, ttl)

    def get_game(self, sport, team):
        """Get cached game for specific team."""
        scoreboard = self.get_scoreboard(sport)
        if not scoreboard:
            return None

        team = team.upper()
        for game in scoreboard:
            if game.get('home_team') == team or game.get('away_team') == team:
                return game

        return None


# Test when run directly
if __name__ == '__main__':
    print("Cache Test")
    print("=" * 40)

    cache = Cache(ttl=2)  # 2 second TTL for testing

    # Test basic operations
    print("Testing basic cache operations...")
    cache.set('test_key', 'test_value')
    assert cache.get('test_key') == 'test_value'
    print("  Set and get: OK")

    # Test expiration
    print("Testing expiration (waiting 3 seconds)...")
    time.sleep(3)
    assert cache.get('test_key') is None
    print("  Expiration: OK")

    # Test max items
    print("Testing max items...")
    cache = Cache(ttl=60, max_items=3)
    cache.set('a', 1)
    cache.set('b', 2)
    cache.set('c', 3)
    cache.set('d', 4)  # Should evict 'a'
    assert cache.get('a') is None
    assert cache.get('d') == 4
    print("  Max items eviction: OK")

    # Test scoreboard cache
    print("\nTesting ScorecardCache...")
    score_cache = ScorecardCache()

    test_games = [
        {'home_team': 'DET', 'away_team': 'GB', 'status': 'live'},
        {'home_team': 'KC', 'away_team': 'BUF', 'status': 'pre'},
    ]
    score_cache.set_scoreboard('nfl', test_games)

    det_game = score_cache.get_game('nfl', 'DET')
    assert det_game is not None
    assert det_game['home_team'] == 'DET'
    print("  Scoreboard cache: OK")

    print("\nAll cache tests passed!")

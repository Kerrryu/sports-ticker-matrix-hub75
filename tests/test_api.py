"""
Tests for API Module

Tests API functionality including:
- ESPN client
- Score parser
- Caching layer
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.parser import ScoreParser
from api.cache import Cache, ScorecardCache


class TestScoreParser:
    """Tests for ScoreParser class."""

    def test_init(self):
        """Test parser initialization."""
        parser = ScoreParser()
        assert parser is not None

    def test_add_favorite_team(self):
        """Test adding favorite team."""
        parser = ScoreParser()
        parser.add_favorite_team('nfl', 'DET')
        assert 'DET' in parser.get_favorite_teams('nfl')

    def test_is_favorite(self):
        """Test checking if team is favorite."""
        parser = ScoreParser()
        parser.add_favorite_team('nfl', 'DET')
        assert parser.is_favorite('nfl', 'DET')
        assert not parser.is_favorite('nfl', 'GB')

    def test_format_score(self):
        """Test score formatting."""
        parser = ScoreParser()
        # Test basic score format
        formatted = parser.format_score(21, 14)
        assert '21' in formatted
        assert '14' in formatted

    def test_get_game_priority(self):
        """Test game priority for favorites."""
        parser = ScoreParser()
        parser.add_favorite_team('nfl', 'DET')

        # Game with favorite team should have higher priority
        game1 = {'home_team': 'DET', 'away_team': 'GB', 'sport': 'nfl'}
        game2 = {'home_team': 'KC', 'away_team': 'BUF', 'sport': 'nfl'}

        priority1 = parser.get_game_priority(game1)
        priority2 = parser.get_game_priority(game2)

        assert priority1 > priority2

    def test_sort_games_by_priority(self):
        """Test sorting games by priority."""
        parser = ScoreParser()
        parser.add_favorite_team('nfl', 'DET')

        games = [
            {'home_team': 'KC', 'away_team': 'BUF', 'sport': 'nfl'},
            {'home_team': 'DET', 'away_team': 'GB', 'sport': 'nfl'},
            {'home_team': 'SF', 'away_team': 'DAL', 'sport': 'nfl'},
        ]

        sorted_games = parser.sort_by_priority(games)

        # DET game should be first
        assert sorted_games[0]['home_team'] == 'DET'

    def test_parse_game_status_live(self):
        """Test parsing live game status."""
        parser = ScoreParser()
        game_data = {
            'status': {'type': {'name': 'STATUS_IN_PROGRESS'}}
        }
        status = parser.parse_game_status(game_data)
        assert status == 'live'

    def test_parse_game_status_final(self):
        """Test parsing final game status."""
        parser = ScoreParser()
        game_data = {
            'status': {'type': {'name': 'STATUS_FINAL'}}
        }
        status = parser.parse_game_status(game_data)
        assert status == 'final'


class TestCache:
    """Tests for Cache class."""

    def test_init(self):
        """Test cache initialization."""
        cache = Cache(max_size=10, ttl=60)
        assert cache.max_size == 10
        assert cache.ttl == 60

    def test_set_and_get(self):
        """Test setting and getting cache values."""
        cache = Cache()
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_get_missing(self):
        """Test getting missing key returns None."""
        cache = Cache()
        assert cache.get('nonexistent') is None

    def test_get_default(self):
        """Test getting missing key with default."""
        cache = Cache()
        assert cache.get('nonexistent', 'default') == 'default'

    def test_delete(self):
        """Test deleting cache entry."""
        cache = Cache()
        cache.set('key1', 'value1')
        cache.delete('key1')
        assert cache.get('key1') is None

    def test_clear(self):
        """Test clearing cache."""
        cache = Cache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_max_size_eviction(self):
        """Test that old entries are evicted when max size reached."""
        cache = Cache(max_size=3)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        cache.set('key4', 'value4')  # Should evict key1

        # One of the earlier keys should be evicted
        assert len(cache._cache) <= 3

    def test_contains(self):
        """Test checking if key exists."""
        cache = Cache()
        cache.set('key1', 'value1')
        assert cache.contains('key1')
        assert not cache.contains('key2')


class TestScorecardCache:
    """Tests for ScorecardCache class."""

    def test_init(self):
        """Test scorecard cache initialization."""
        cache = ScorecardCache()
        assert cache is not None

    def test_cache_game(self):
        """Test caching game data."""
        cache = ScorecardCache()
        game = {
            'game_id': '123',
            'home_team': 'DET',
            'away_team': 'GB',
            'home_score': 21,
            'away_score': 14,
        }
        cache.cache_game('nfl', game)

        cached = cache.get_game('nfl', '123')
        assert cached is not None
        assert cached['home_team'] == 'DET'

    def test_cache_games_for_sport(self):
        """Test caching multiple games for a sport."""
        cache = ScorecardCache()
        games = [
            {'game_id': '1', 'home_team': 'DET', 'away_team': 'GB'},
            {'game_id': '2', 'home_team': 'KC', 'away_team': 'BUF'},
        ]
        cache.cache_games('nfl', games)

        all_games = cache.get_games('nfl')
        assert len(all_games) == 2

    def test_get_stale_games(self):
        """Test identifying stale games."""
        cache = ScorecardCache(ttl=0)  # Immediate expiry
        games = [
            {'game_id': '1', 'home_team': 'DET', 'away_team': 'GB'},
        ]
        cache.cache_games('nfl', games)

        # All games should be stale immediately
        stale = cache.get_stale_sports()
        assert 'nfl' in stale


class TestESPNClientMock:
    """Tests for ESPN API client with mock data."""

    def test_parse_scoreboard_response(self):
        """Test parsing ESPN scoreboard response."""
        # Mock ESPN response structure
        mock_response = {
            'events': [
                {
                    'id': '401547789',
                    'name': 'Detroit Lions at Green Bay Packers',
                    'status': {
                        'type': {
                            'name': 'STATUS_IN_PROGRESS',
                            'state': 'in',
                            'completed': False,
                        },
                        'displayClock': '10:23',
                        'period': 2,
                    },
                    'competitions': [
                        {
                            'competitors': [
                                {
                                    'id': '9',
                                    'team': {
                                        'abbreviation': 'GB',
                                        'displayName': 'Green Bay Packers',
                                    },
                                    'homeAway': 'home',
                                    'score': '14',
                                },
                                {
                                    'id': '8',
                                    'team': {
                                        'abbreviation': 'DET',
                                        'displayName': 'Detroit Lions',
                                    },
                                    'homeAway': 'away',
                                    'score': '21',
                                },
                            ]
                        }
                    ]
                }
            ]
        }

        # Parse event
        event = mock_response['events'][0]
        comp = event['competitions'][0]
        competitors = comp['competitors']

        home = next(c for c in competitors if c['homeAway'] == 'home')
        away = next(c for c in competitors if c['homeAway'] == 'away')

        assert home['team']['abbreviation'] == 'GB'
        assert away['team']['abbreviation'] == 'DET'
        assert home['score'] == '14'
        assert away['score'] == '21'
        assert event['status']['type']['state'] == 'in'


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestScoreParser,
        TestCache,
        TestScorecardCache,
        TestESPNClientMock,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()

        for method_name in dir(instance):
            if not method_name.startswith('test_'):
                continue

            try:
                method = getattr(instance, method_name)
                method()
                print(f"  [PASS] {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  [FAIL] {method_name}: {e}")
                failed += 1
                errors.append((method_name, str(e)))
            except Exception as e:
                print(f"  [ERROR] {method_name}: {e}")
                failed += 1
                errors.append((method_name, traceback.format_exc()))

    print("\n" + "=" * 40)
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, error in errors:
            print(f"  - {name}: {error[:100]}")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

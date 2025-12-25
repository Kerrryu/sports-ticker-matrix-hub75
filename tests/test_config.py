"""
Tests for Configuration Module

Tests configuration functionality including:
- Loading/saving config
- Team management
- Validation
- Quiet hours
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import ConfigManager, DEFAULTS


class TestConfigManager:
    """Tests for ConfigManager class."""

    def setup_test_config(self):
        """Create a test config manager."""
        return ConfigManager('test_config.json')

    def cleanup(self):
        """Clean up test files."""
        try:
            os.remove('test_config.json')
        except:
            pass

    def test_init(self):
        """Test config manager initialization."""
        config = self.setup_test_config()
        assert config is not None
        assert config.filename == 'test_config.json'
        self.cleanup()

    def test_load_defaults(self):
        """Test loading defaults when file doesn't exist."""
        config = self.setup_test_config()
        config.load()
        assert config.get('brightness') == DEFAULTS['brightness']
        assert config.get('update_interval') == DEFAULTS['update_interval']
        self.cleanup()

    def test_save_and_load(self):
        """Test saving and loading config."""
        config = self.setup_test_config()
        config.load()
        config.set('brightness', 200)
        config.save()

        # Load in new instance
        config2 = self.setup_test_config()
        config2.load()
        assert config2.get('brightness') == 200
        self.cleanup()

    def test_get_default(self):
        """Test getting with default value."""
        config = self.setup_test_config()
        config.load()
        assert config.get('nonexistent', 'default') == 'default'
        self.cleanup()

    def test_set(self):
        """Test setting value."""
        config = self.setup_test_config()
        config.load()
        config.set('brightness', 150)
        assert config.get('brightness') == 150
        self.cleanup()

    def test_update(self):
        """Test updating multiple values."""
        config = self.setup_test_config()
        config.load()
        config.update({
            'brightness': 100,
            'update_interval': 60
        })
        assert config.get('brightness') == 100
        assert config.get('update_interval') == 60
        self.cleanup()

    def test_reset(self):
        """Test resetting to defaults."""
        config = self.setup_test_config()
        config.load()
        config.set('brightness', 50)
        config.reset()
        assert config.get('brightness') == DEFAULTS['brightness']
        self.cleanup()

    def test_reset_single_key(self):
        """Test resetting single key."""
        config = self.setup_test_config()
        config.load()
        config.set('brightness', 50)
        config.set('update_interval', 30)
        config.reset('brightness')
        assert config.get('brightness') == DEFAULTS['brightness']
        assert config.get('update_interval') == 30
        self.cleanup()

    def test_is_dirty(self):
        """Test dirty flag."""
        config = self.setup_test_config()
        config.load()
        assert config.is_dirty  # Dirty after loading missing file
        config.save()
        assert not config.is_dirty
        config.set('brightness', 100)
        assert config.is_dirty
        self.cleanup()

    def test_to_dict(self):
        """Test converting to dictionary."""
        config = self.setup_test_config()
        config.load()
        data = config.to_dict()
        assert isinstance(data, dict)
        assert 'brightness' in data
        self.cleanup()


class TestTeamManagement:
    """Tests for team management functions."""

    def setup_test_config(self):
        """Create a test config manager."""
        config = ConfigManager('test_config.json')
        config.load()
        return config

    def cleanup(self):
        """Clean up test files."""
        try:
            os.remove('test_config.json')
        except:
            pass

    def test_get_teams_empty(self):
        """Test getting teams when none configured."""
        config = self.setup_test_config()
        teams = config.get_teams()
        assert teams == []
        self.cleanup()

    def test_add_team(self):
        """Test adding a team."""
        config = self.setup_test_config()
        result = config.add_team('nfl', 'DET', 'Detroit Lions')
        assert result is True
        teams = config.get_teams()
        assert len(teams) == 1
        assert teams[0]['sport'] == 'nfl'
        assert teams[0]['team_id'] == 'DET'
        self.cleanup()

    def test_add_team_duplicate(self):
        """Test adding duplicate team fails."""
        config = self.setup_test_config()
        config.add_team('nfl', 'DET', 'Detroit Lions')
        result = config.add_team('nfl', 'DET', 'Detroit Lions')
        assert result is False
        teams = config.get_teams()
        assert len(teams) == 1
        self.cleanup()

    def test_add_team_different_sports(self):
        """Test adding same team ID for different sports."""
        config = self.setup_test_config()
        config.add_team('nfl', 'DET', 'Detroit Lions')
        result = config.add_team('nba', 'DET', 'Detroit Pistons')
        assert result is True
        teams = config.get_teams()
        assert len(teams) == 2
        self.cleanup()

    def test_remove_team(self):
        """Test removing a team."""
        config = self.setup_test_config()
        config.add_team('nfl', 'DET', 'Detroit Lions')
        result = config.remove_team('nfl', 'DET')
        assert result is True
        teams = config.get_teams()
        assert len(teams) == 0
        self.cleanup()

    def test_remove_team_not_found(self):
        """Test removing non-existent team."""
        config = self.setup_test_config()
        result = config.remove_team('nfl', 'DET')
        assert result is False
        self.cleanup()

    def test_get_team_ids(self):
        """Test getting team IDs."""
        config = self.setup_test_config()
        config.add_team('nfl', 'DET')
        config.add_team('nfl', 'GB')
        config.add_team('nba', 'LAL')

        all_ids = config.get_team_ids()
        assert len(all_ids) == 3

        nfl_ids = config.get_team_ids('nfl')
        assert len(nfl_ids) == 2
        assert 'DET' in nfl_ids
        assert 'GB' in nfl_ids
        self.cleanup()


class TestQuietHours:
    """Tests for quiet hours functionality."""

    def setup_test_config(self):
        """Create a test config manager."""
        config = ConfigManager('test_config.json')
        config.load()
        return config

    def cleanup(self):
        """Clean up test files."""
        try:
            os.remove('test_config.json')
        except:
            pass

    def test_quiet_hours_disabled(self):
        """Test quiet hours when disabled."""
        config = self.setup_test_config()
        config.set('quiet_hours', {'enabled': False, 'start': 23, 'end': 7})
        assert not config.is_quiet_hours(2)  # 2 AM
        assert not config.is_quiet_hours(14)  # 2 PM
        self.cleanup()

    def test_quiet_hours_overnight(self):
        """Test overnight quiet hours (23:00 - 07:00)."""
        config = self.setup_test_config()
        config.set('quiet_hours', {'enabled': True, 'start': 23, 'end': 7})

        # In quiet hours
        assert config.is_quiet_hours(23)
        assert config.is_quiet_hours(0)
        assert config.is_quiet_hours(2)
        assert config.is_quiet_hours(6)

        # Not in quiet hours
        assert not config.is_quiet_hours(7)
        assert not config.is_quiet_hours(12)
        assert not config.is_quiet_hours(22)
        self.cleanup()

    def test_quiet_hours_daytime(self):
        """Test daytime quiet hours (09:00 - 17:00)."""
        config = self.setup_test_config()
        config.set('quiet_hours', {'enabled': True, 'start': 9, 'end': 17})

        # In quiet hours
        assert config.is_quiet_hours(9)
        assert config.is_quiet_hours(12)
        assert config.is_quiet_hours(16)

        # Not in quiet hours
        assert not config.is_quiet_hours(8)
        assert not config.is_quiet_hours(17)
        assert not config.is_quiet_hours(22)
        self.cleanup()


class TestValidation:
    """Tests for configuration validation."""

    def setup_test_config(self):
        """Create a test config manager."""
        config = ConfigManager('test_config.json')
        config.load()
        return config

    def cleanup(self):
        """Clean up test files."""
        try:
            os.remove('test_config.json')
        except:
            pass

    def test_validate_defaults(self):
        """Test validation with defaults passes."""
        config = self.setup_test_config()
        errors = config.validate()
        assert len(errors) == 0
        self.cleanup()

    def test_validate_brightness_range(self):
        """Test brightness validation."""
        config = self.setup_test_config()
        config.set('brightness', 300)
        errors = config.validate()
        assert len(errors) > 0
        assert any('brightness' in e.lower() for e in errors)
        self.cleanup()

    def test_validate_update_interval(self):
        """Test update interval validation."""
        config = self.setup_test_config()
        config.set('update_interval', 10)  # Too low
        errors = config.validate()
        assert len(errors) > 0
        assert any('interval' in e.lower() for e in errors)
        self.cleanup()

    def test_validate_teams_structure(self):
        """Test teams structure validation."""
        config = self.setup_test_config()
        config.set('teams', 'not a list')
        errors = config.validate()
        assert len(errors) > 0
        self.cleanup()

    def test_validate_team_sport(self):
        """Test team sport validation."""
        config = self.setup_test_config()
        config.set('teams', [{'sport': 'invalid', 'team_id': 'ABC'}])
        errors = config.validate()
        assert len(errors) > 0
        assert any('sport' in e.lower() for e in errors)
        self.cleanup()


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestConfigManager,
        TestTeamManagement,
        TestQuietHours,
        TestValidation,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        for method_name in dir(test_class):
            if not method_name.startswith('test_'):
                continue

            try:
                instance = test_class()
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

    # Cleanup
    try:
        os.remove('test_config.json')
    except:
        pass

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

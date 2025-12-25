"""
Configuration Manager

Handles loading, saving, and validating configuration data.
Uses JSON storage with sensible defaults.

Usage:
    from utils.config import ConfigManager

    config = ConfigManager()
    config.load()
    print(config.get('brightness'))
    config.set('brightness', 200)
    config.save()
"""

import json
import gc

# Default configuration values
DEFAULTS = {
    'teams': [],
    'brightness': 128,
    'update_interval': 120,
    'quiet_hours': {
        'enabled': False,
        'start': 23,
        'end': 7
    },
    'timezone_offset': -5,
    'display_mode': 'auto',
    'idle_message': 'Sports Ticker',
    'show_logos': True,
    'animation_speed': 50,
    'proxy_url': '',  # API proxy URL for memory-efficient data fetching
}

# Configuration file path
CONFIG_FILE = 'config.json'


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, filename=CONFIG_FILE):
        """
        Initialize configuration manager.

        Args:
            filename: Path to configuration file
        """
        self.filename = filename
        self._config = {}
        self._dirty = False

    def load(self):
        """
        Load configuration from file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.filename, 'r') as f:
                self._config = json.load(f)

            # Merge with defaults for any missing keys
            for key, value in DEFAULTS.items():
                if key not in self._config:
                    self._config[key] = value

            self._dirty = False
            gc.collect()
            return True

        except OSError:
            # File doesn't exist, use defaults
            self._config = DEFAULTS.copy()
            self._dirty = True
            return False

        except ValueError:
            # JSON parse error, use defaults
            print("Config: JSON parse error, using defaults")
            self._config = DEFAULTS.copy()
            self._dirty = True
            return False

    def save(self):
        """
        Save configuration to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.filename, 'w') as f:
                json.dump(self._config, f)
            self._dirty = False
            gc.collect()
            return True

        except OSError as e:
            print(f"Config: Save error: {e}")
            return False

    def get(self, key, default=None):
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key, value):
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        if self._config.get(key) != value:
            self._config[key] = value
            self._dirty = True

    def update(self, data):
        """
        Update multiple configuration values.

        Args:
            data: Dict of key-value pairs
        """
        for key, value in data.items():
            self.set(key, value)

    def reset(self, key=None):
        """
        Reset configuration to defaults.

        Args:
            key: Specific key to reset, or None for all
        """
        if key is None:
            self._config = DEFAULTS.copy()
            self._dirty = True
        elif key in DEFAULTS:
            self._config[key] = DEFAULTS[key]
            self._dirty = True

    @property
    def is_dirty(self):
        """Check if configuration has unsaved changes."""
        return self._dirty

    def to_dict(self):
        """Get configuration as dictionary."""
        return self._config.copy()

    # Team management helpers
    def get_teams(self):
        """Get list of configured teams."""
        return self.get('teams', [])

    def add_team(self, sport, team_id, team_name=None):
        """
        Add a team to favorites.

        Args:
            sport: Sport type (nfl, nba, mlb, nhl)
            team_id: Team identifier
            team_name: Optional team name

        Returns:
            True if added, False if already exists
        """
        teams = self.get_teams()

        # Check for duplicate
        for team in teams:
            if team.get('sport') == sport and team.get('team_id') == team_id:
                return False

        teams.append({
            'sport': sport.lower(),
            'team_id': team_id.upper(),
            'team_name': team_name or team_id
        })

        self.set('teams', teams)
        return True

    def remove_team(self, sport, team_id):
        """
        Remove a team from favorites.

        Args:
            sport: Sport type
            team_id: Team identifier

        Returns:
            True if removed, False if not found
        """
        teams = self.get_teams()
        original_count = len(teams)

        teams = [t for t in teams
                 if not (t.get('sport') == sport.lower() and
                        t.get('team_id') == team_id.upper())]

        if len(teams) < original_count:
            self.set('teams', teams)
            return True
        return False

    def get_team_ids(self, sport=None):
        """
        Get list of team IDs.

        Args:
            sport: Optional sport filter

        Returns:
            List of team ID strings
        """
        teams = self.get_teams()
        if sport:
            teams = [t for t in teams if t.get('sport') == sport.lower()]
        return [t.get('team_id') for t in teams]

    # Quiet hours helpers
    def is_quiet_hours(self, current_hour):
        """
        Check if current time is within quiet hours.

        Args:
            current_hour: Current hour (0-23)

        Returns:
            True if in quiet hours
        """
        quiet = self.get('quiet_hours', {})
        if not quiet.get('enabled', False):
            return False

        start = quiet.get('start', 23)
        end = quiet.get('end', 7)

        if start <= end:
            # Simple range (e.g., 9-17)
            return start <= current_hour < end
        else:
            # Overnight range (e.g., 23-7)
            return current_hour >= start or current_hour < end

    # Validation
    def validate(self):
        """
        Validate configuration values.

        Returns:
            List of validation error strings (empty if valid)
        """
        errors = []

        # Brightness
        brightness = self.get('brightness')
        if not isinstance(brightness, int) or not 0 <= brightness <= 255:
            errors.append("Brightness must be 0-255")

        # Update interval
        interval = self.get('update_interval')
        if not isinstance(interval, int) or not 30 <= interval <= 600:
            errors.append("Update interval must be 30-600 seconds")

        # Teams
        teams = self.get('teams')
        if not isinstance(teams, list):
            errors.append("Teams must be a list")
        else:
            valid_sports = {'nfl', 'nba', 'mlb', 'nhl'}
            for i, team in enumerate(teams):
                if not isinstance(team, dict):
                    errors.append(f"Team {i} must be a dict")
                elif team.get('sport', '').lower() not in valid_sports:
                    errors.append(f"Team {i} has invalid sport")
                elif not team.get('team_id'):
                    errors.append(f"Team {i} missing team_id")

        return errors


# Singleton instance
_config = None


def get_config():
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ConfigManager()
        _config.load()
    return _config


# Test when run directly
if __name__ == '__main__':
    print("Config Manager Test")
    print("=" * 40)

    config = ConfigManager('test_config.json')

    # Test defaults
    config.load()
    print(f"Brightness: {config.get('brightness')}")
    print(f"Update interval: {config.get('update_interval')}")

    # Test team management
    config.add_team('nfl', 'DET', 'Detroit Lions')
    config.add_team('nba', 'DET', 'Detroit Pistons')
    print(f"Teams: {config.get_teams()}")
    print(f"NFL team IDs: {config.get_team_ids('nfl')}")

    # Test quiet hours
    config.set('quiet_hours', {'enabled': True, 'start': 23, 'end': 7})
    print(f"Is 2am quiet? {config.is_quiet_hours(2)}")
    print(f"Is 2pm quiet? {config.is_quiet_hours(14)}")

    # Test validation
    errors = config.validate()
    print(f"Validation errors: {errors}")

    # Save
    config.save()
    print("Config saved!")

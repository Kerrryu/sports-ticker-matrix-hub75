"""
Score Parser - Transforms API responses into display-ready data

Handles normalization and formatting of game data from various sources.

Usage:
    from api.parser import ScoreParser

    parser = ScoreParser()
    display_data = parser.format_for_display(game)
"""


class ScoreParser:
    """Parses and formats game data for display."""

    def __init__(self):
        """Initialize parser."""
        pass

    def format_for_display(self, game):
        """
        Format game data for LED display.

        Args:
            game: Raw game dict from API

        Returns:
            Dict with display-ready data
        """
        if not game:
            return None

        return {
            'home_team': self._format_team(game.get('home_team', '')),
            'away_team': self._format_team(game.get('away_team', '')),
            'home_score': self._format_score(game.get('home_score', 0)),
            'away_score': self._format_score(game.get('away_score', 0)),
            'status': game.get('status', 'pre'),
            'period': self._format_period(game.get('period', ''), game.get('sport')),
            'time_remaining': self._format_time(game.get('time_remaining', '')),
            'sport': game.get('sport', 'nfl'),
        }

    def _format_team(self, team):
        """Format team abbreviation (3 chars max, uppercase)."""
        return str(team)[:3].upper()

    def _format_score(self, score):
        """Format score as string."""
        try:
            return str(int(score))
        except:
            return '0'

    def _format_period(self, period, sport=None):
        """Format period/quarter for display."""
        if not period:
            return ''

        # Keep it short for display
        period = str(period).upper()

        # Normalize common formats
        if period.startswith('Q'):
            return period  # Q1, Q2, etc.
        elif period.startswith('P'):
            return period  # P1, P2, P3 for hockey
        elif 'HALF' in period:
            return 'HT'
        elif 'OT' in period or 'OVER' in period:
            return 'OT'
        elif 'FINAL' in period:
            return 'FIN'

        return period[:4]  # Truncate to fit

    def _format_time(self, time_str):
        """Format time remaining for display."""
        if not time_str:
            return ''

        # Clean up time string
        time_str = str(time_str).strip()

        # Already short enough
        if len(time_str) <= 5:
            return time_str

        # Try to parse and reformat
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                mins = int(parts[0])
                secs = int(parts[1]) if len(parts) > 1 else 0
                return f"{mins}:{secs:02d}"
        except:
            pass

        return time_str[:5]

    def parse_scoreboard(self, raw_data, sport):
        """
        Parse raw scoreboard data.

        Args:
            raw_data: Raw API response
            sport: Sport type

        Returns:
            List of parsed game dicts
        """
        games = []

        try:
            events = raw_data.get('events', [])

            for event in events:
                game = self._parse_event(event, sport)
                if game:
                    games.append(game)

        except Exception as e:
            print(f"Scoreboard parse error: {e}")

        return games

    def _parse_event(self, event, sport):
        """Parse single game event."""
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) < 2:
                return None

            home = None
            away = None

            for comp in competitors:
                if comp.get('homeAway') == 'home':
                    home = comp
                else:
                    away = comp

            if not home or not away:
                return None

            status_info = competition.get('status', {})
            status_type = status_info.get('type', {})

            return {
                'sport': sport,
                'home_team': home.get('team', {}).get('abbreviation', 'HME'),
                'away_team': away.get('team', {}).get('abbreviation', 'AWY'),
                'home_score': int(home.get('score', 0)),
                'away_score': int(away.get('score', 0)),
                'status': status_type.get('state', 'pre'),
                'period': self._get_period(status_info, sport),
                'time_remaining': status_info.get('displayClock', ''),
            }

        except Exception as e:
            print(f"Event parse error: {e}")
            return None

    def _get_period(self, status_info, sport):
        """Extract period/quarter from status."""
        period_num = status_info.get('period', 0)

        if sport in ['nfl', 'nba']:
            return f"Q{period_num}" if period_num else ''
        elif sport == 'nhl':
            return f"P{period_num}" if period_num else ''
        elif sport == 'mlb':
            half = status_info.get('type', {}).get('name', '')
            if 'Top' in half:
                return f"T{period_num}"
            elif 'Bot' in half:
                return f"B{period_num}"
            return str(period_num)

        return str(period_num)

    def is_live_game(self, game):
        """Check if game is currently live."""
        status = game.get('status', 'pre')
        return status in ['live', 'in', 'in_progress']

    def is_final(self, game):
        """Check if game has ended."""
        status = game.get('status', 'pre')
        return status in ['final', 'post', 'complete']

    def sort_by_priority(self, games, favorite_teams=None):
        """
        Sort games by display priority.

        Priority:
        1. Live games with favorite teams
        2. Live games
        3. Upcoming games with favorite teams
        4. Other games

        Args:
            games: List of game dicts
            favorite_teams: List of team abbreviations

        Returns:
            Sorted list of games
        """
        if not favorite_teams:
            favorite_teams = []

        favorite_teams = [t.upper() for t in favorite_teams]

        def priority_key(game):
            is_live = self.is_live_game(game)
            has_favorite = (game.get('home_team', '').upper() in favorite_teams or
                           game.get('away_team', '').upper() in favorite_teams)

            if is_live and has_favorite:
                return 0
            elif is_live:
                return 1
            elif has_favorite:
                return 2
            else:
                return 3

        return sorted(games, key=priority_key)


# Test when run directly
if __name__ == '__main__':
    print("Score Parser Test")
    print("=" * 40)

    parser = ScoreParser()

    # Test game formatting
    test_game = {
        'home_team': 'DET',
        'away_team': 'GB',
        'home_score': 24,
        'away_score': 17,
        'status': 'live',
        'period': 'Q2',
        'time_remaining': '5:42',
        'sport': 'nfl',
    }

    formatted = parser.format_for_display(test_game)
    print("Formatted game:")
    for key, value in formatted.items():
        print(f"  {key}: {value}")

    # Test priority sorting
    games = [
        {'home_team': 'KC', 'away_team': 'BUF', 'status': 'pre'},
        {'home_team': 'DET', 'away_team': 'GB', 'status': 'live'},
        {'home_team': 'SF', 'away_team': 'PHI', 'status': 'live'},
    ]

    sorted_games = parser.sort_by_priority(games, ['DET'])
    print("\nSorted by priority (DET favorite):")
    for g in sorted_games:
        print(f"  {g['away_team']} @ {g['home_team']} - {g['status']}")

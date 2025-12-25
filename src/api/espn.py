"""
ESPN API Client for Sports Scores

Fetches live game data from ESPN's public API endpoints.
Supports both direct ESPN API and proxy API for memory-constrained devices.

Supported Sports:
- NFL (football)
- NBA (basketball)
- MLB (baseball)
- NHL (hockey)

Usage:
    from api.espn import ESPNClient

    # Use proxy API (recommended for Pico 2W)
    client = ESPNClient(proxy_url="https://your-proxy.vercel.app")
    games = client.get_games_for_teams(teams)

    # Or use direct ESPN API (requires more memory)
    client = ESPNClient()
    games = client.get_scoreboard('nfl')
"""

try:
    import urequests as requests
except ImportError:
    import requests

import json
import gc

# ESPN API endpoints
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

SPORT_PATHS = {
    'nfl': '/football/nfl/scoreboard',
    'nba': '/basketball/nba/scoreboard',
    'mlb': '/baseball/mlb/scoreboard',
    'nhl': '/hockey/nhl/scoreboard',
}

# Team ID mappings (ESPN uses numeric IDs internally)
# This maps common abbreviations to ESPN team IDs
NFL_TEAMS = {
    'DET': {'id': '8', 'name': 'Detroit Lions'},
    'GB': {'id': '9', 'name': 'Green Bay Packers'},
    'CHI': {'id': '3', 'name': 'Chicago Bears'},
    'MIN': {'id': '16', 'name': 'Minnesota Vikings'},
    'KC': {'id': '12', 'name': 'Kansas City Chiefs'},
    'BUF': {'id': '2', 'name': 'Buffalo Bills'},
    'SF': {'id': '25', 'name': 'San Francisco 49ers'},
    'PHI': {'id': '21', 'name': 'Philadelphia Eagles'},
    'DAL': {'id': '6', 'name': 'Dallas Cowboys'},
    'MIA': {'id': '15', 'name': 'Miami Dolphins'},
    'BAL': {'id': '33', 'name': 'Baltimore Ravens'},
    'CIN': {'id': '4', 'name': 'Cincinnati Bengals'},
    'LAR': {'id': '14', 'name': 'Los Angeles Rams'},
    'SEA': {'id': '26', 'name': 'Seattle Seahawks'},
    'NYG': {'id': '19', 'name': 'New York Giants'},
    'NYJ': {'id': '20', 'name': 'New York Jets'},
}

NBA_TEAMS = {
    'LAL': {'id': '13', 'name': 'Los Angeles Lakers'},
    'BOS': {'id': '2', 'name': 'Boston Celtics'},
    'GSW': {'id': '9', 'name': 'Golden State Warriors'},
    'MIL': {'id': '15', 'name': 'Milwaukee Bucks'},
    'DEN': {'id': '7', 'name': 'Denver Nuggets'},
    'PHX': {'id': '21', 'name': 'Phoenix Suns'},
    'MIA': {'id': '14', 'name': 'Miami Heat'},
    'CHI': {'id': '4', 'name': 'Chicago Bulls'},
}

MLB_TEAMS = {
    'NYY': {'id': '10', 'name': 'New York Yankees'},
    'LAD': {'id': '19', 'name': 'Los Angeles Dodgers'},
    'ATL': {'id': '15', 'name': 'Atlanta Braves'},
    'HOU': {'id': '18', 'name': 'Houston Astros'},
    'BOS': {'id': '2', 'name': 'Boston Red Sox'},
    'CHC': {'id': '16', 'name': 'Chicago Cubs'},
    'DET': {'id': '6', 'name': 'Detroit Tigers'},
}

NHL_TEAMS = {
    'TOR': {'id': '10', 'name': 'Toronto Maple Leafs'},
    'EDM': {'id': '22', 'name': 'Edmonton Oilers'},
    'VGK': {'id': '37', 'name': 'Vegas Golden Knights'},
    'COL': {'id': '17', 'name': 'Colorado Avalanche'},
    'BOS': {'id': '1', 'name': 'Boston Bruins'},
    'DET': {'id': '5', 'name': 'Detroit Red Wings'},
}

TEAM_MAPS = {
    'nfl': NFL_TEAMS,
    'nba': NBA_TEAMS,
    'mlb': MLB_TEAMS,
    'nhl': NHL_TEAMS,
}


class ESPNClient:
    """Client for fetching sports data from ESPN API."""

    def __init__(self, timeout=10, proxy_url=None):
        """
        Initialize ESPN client.

        Args:
            timeout: Request timeout in seconds
            proxy_url: Optional proxy API URL for memory-constrained devices
        """
        self.timeout = timeout
        self.proxy_url = proxy_url
        self.cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds

    def get_scoreboard(self, sport):
        """
        Get scoreboard for a sport (all games).

        Args:
            sport: 'nfl', 'nba', 'mlb', or 'nhl'

        Returns:
            List of game dictionaries
        """
        if sport not in SPORT_PATHS:
            print(f"Unknown sport: {sport}")
            return []

        url = ESPN_BASE + SPORT_PATHS[sport]

        try:
            print(f"Fetching {sport} scoreboard...")
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                print(f"API error: HTTP {response.status_code}")
                return []

            data = response.json()
            games = self._parse_scoreboard(data, sport)

            return games

        except Exception as e:
            print(f"Scoreboard fetch error: {e}")
            return []
        finally:
            gc.collect()

    def get_game(self, sport, team_abbrev):
        """
        Get current game for a specific team.

        Args:
            sport: 'nfl', 'nba', 'mlb', or 'nhl'
            team_abbrev: Team abbreviation (e.g., 'DET', 'GB')

        Returns:
            Game dict if team is playing, None otherwise
        """
        games = self.get_scoreboard(sport)

        team_abbrev = team_abbrev.upper()

        for game in games:
            if game['home_team'] == team_abbrev or game['away_team'] == team_abbrev:
                return game

        return None

    def get_team_games(self, teams):
        """
        Get games for multiple teams across sports.

        Args:
            teams: List of dicts with 'sport' and 'team_id' keys

        Returns:
            List of game dicts for all teams
        """
        games = []
        sports_checked = set()

        for team in teams:
            sport = team.get('sport', 'nfl')
            team_id = team.get('team_id', '')

            # Only fetch each sport's scoreboard once
            if sport not in sports_checked:
                all_games = self.get_scoreboard(sport)
                sports_checked.add(sport)

                # Find games for configured teams
                for g in all_games:
                    if g['home_team'] == team_id or g['away_team'] == team_id:
                        games.append(g)

        return games

    def get_games_via_proxy(self, teams):
        """
        Fetch games using the lightweight proxy API.
        Returns much smaller responses (~1-3KB) suitable for Pico 2W.

        Args:
            teams: List of dicts with 'sport' and 'team_id' keys

        Returns:
            Dict with 'active' and 'upcoming' game lists
        """
        if not self.proxy_url:
            print("No proxy URL configured")
            return {'active': [], 'upcoming': []}

        # Build query string
        team_params = ','.join(
            f"{t.get('sport', 'nfl')}:{t.get('team_id', '')}"
            for t in teams
        )
        url = f"{self.proxy_url}/api/games?teams={team_params}"

        try:
            print(f"Fetching via proxy...")
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                print(f"Proxy error: HTTP {response.status_code}")
                return {'active': [], 'upcoming': []}

            data = response.json()

            # Normalize proxy response to match internal format
            result = {
                'active': [],
                'upcoming': []
            }

            # Convert active games
            for g in data.get('active', []):
                result['active'].append({
                    'sport': g.get('sport', 'nfl'),
                    'home_team': g.get('home', '???'),
                    'away_team': g.get('away', '???'),
                    'home_score': g.get('hs', 0),
                    'away_score': g.get('as', 0),
                    'status': g.get('status', 'pre'),
                    'period': g.get('period', ''),
                    'time_remaining': g.get('time', ''),
                })

            # Convert upcoming games
            for g in data.get('upcoming', []):
                result['upcoming'].append({
                    'sport': g.get('sport', 'nfl'),
                    'home_team': g.get('home', '???'),
                    'away_team': g.get('away', '???'),
                    'home_score': 0,
                    'away_score': 0,
                    'status': 'pre',
                    'date': g.get('date', ''),
                    'time': g.get('time', ''),
                })

            return result

        except Exception as e:
            print(f"Proxy fetch error: {e}")
            return {'active': [], 'upcoming': []}
        finally:
            gc.collect()

    def get_all_games(self, teams):
        """
        Get all games for configured teams.
        Uses proxy if available, otherwise falls back to direct API.

        Args:
            teams: List of dicts with 'sport' and 'team_id' keys

        Returns:
            Dict with 'active' and 'upcoming' game lists
        """
        if self.proxy_url:
            return self.get_games_via_proxy(teams)
        else:
            # Fallback to direct ESPN API (may fail on memory-constrained devices)
            games = self.get_team_games(teams)
            return {
                'active': [g for g in games if g['status'] in ['live', 'final']],
                'upcoming': [g for g in games if g['status'] == 'pre'][:4]
            }

    def _parse_scoreboard(self, data, sport):
        """
        Parse ESPN API response into game list.

        Args:
            data: Raw API response dict
            sport: Sport type for context

        Returns:
            List of normalized game dicts
        """
        games = []

        try:
            events = data.get('events', [])

            for event in events:
                game = self._parse_event(event, sport)
                if game:
                    games.append(game)

        except Exception as e:
            print(f"Parse error: {e}")

        return games

    def _parse_event(self, event, sport):
        """
        Parse single event (game) from ESPN data.

        Args:
            event: Event dict from ESPN API
            sport: Sport type

        Returns:
            Normalized game dict
        """
        try:
            # Get competition info
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) < 2:
                return None

            # Find home and away teams
            home = None
            away = None
            for comp in competitors:
                if comp.get('homeAway') == 'home':
                    home = comp
                else:
                    away = comp

            if not home or not away:
                return None

            # Get team info
            home_team = home.get('team', {}).get('abbreviation', 'HME')
            away_team = away.get('team', {}).get('abbreviation', 'AWY')
            home_score = int(home.get('score', 0))
            away_score = int(away.get('score', 0))

            # Get status
            status_info = competition.get('status', {})
            status_type = status_info.get('type', {})
            status_state = status_type.get('state', 'pre')

            # Map status
            if status_state == 'in':
                status = 'live'
            elif status_state == 'post':
                status = 'final'
            else:
                status = 'pre'

            # Get period/quarter and time
            period = ''
            time_remaining = ''

            if status == 'live':
                display_clock = status_info.get('displayClock', '')
                period_num = status_info.get('period', 0)

                # Format period based on sport
                if sport == 'nfl':
                    period = f"Q{period_num}"
                elif sport == 'nba':
                    period = f"Q{period_num}"
                elif sport == 'mlb':
                    # Baseball uses innings
                    half = 'TOP' if status_type.get('name', '').startswith('Top') else 'BOT'
                    period = f"{half} {period_num}"
                elif sport == 'nhl':
                    period = f"P{period_num}"

                time_remaining = display_clock

            return {
                'sport': sport,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'status': status,
                'period': period,
                'time_remaining': time_remaining,
                'event_id': event.get('id', ''),
            }

        except Exception as e:
            print(f"Event parse error: {e}")
            return None

    def get_available_sports(self):
        """Get list of supported sports."""
        return list(SPORT_PATHS.keys())

    def get_teams(self, sport):
        """
        Get available teams for a sport.

        Args:
            sport: Sport type

        Returns:
            Dict of team abbreviations to team info
        """
        return TEAM_MAPS.get(sport, {})


# Test when run directly
if __name__ == '__main__':
    print("ESPN API Client Test")
    print("=" * 50)

    client = ESPNClient()

    # Test NFL scoreboard
    print("\nFetching NFL scoreboard...")
    games = client.get_scoreboard('nfl')
    print(f"Found {len(games)} NFL games")

    for game in games[:3]:  # Show first 3
        print(f"  {game['away_team']} @ {game['home_team']}: "
              f"{game['away_score']}-{game['home_score']} ({game['status']})")

    # Test specific team
    print("\nChecking for Detroit Lions game...")
    det_game = client.get_game('nfl', 'DET')
    if det_game:
        print(f"  Found: {det_game['away_team']} @ {det_game['home_team']}")
    else:
        print("  Lions not playing today")

    print("\nESPN client test complete!")

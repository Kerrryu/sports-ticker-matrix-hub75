"""
Sports Ticker Proxy API

Lightweight proxy that fetches sports data and returns minimal JSON
responses sized for microcontrollers (~1-3KB instead of ~225KB).

Deploy to: Vercel, Railway, Render, or Cloudflare Workers (all have free tiers)

Features:
- Fetches only team-specific data (not full scoreboards)
- Returns active games and upcoming games
- Response size optimized for Pico 2W memory constraints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# ESPN API endpoints
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

SPORT_CONFIG = {
    'nfl': {'path': 'football/nfl', 'type': 'football'},
    'nba': {'path': 'basketball/nba', 'type': 'basketball'},
    'mlb': {'path': 'baseball/mlb', 'type': 'baseball'},
    'nhl': {'path': 'hockey/nhl', 'type': 'hockey'},
}

# ESPN team ID mappings
TEAM_IDS = {
    'nfl': {
        'DET': '8', 'GB': '9', 'CHI': '3', 'MIN': '16', 'KC': '12',
        'BUF': '2', 'SF': '25', 'PHI': '21', 'DAL': '6', 'MIA': '15',
        'BAL': '33', 'CIN': '4', 'LAR': '14', 'SEA': '26', 'NYG': '19',
        'NYJ': '20', 'NE': '17', 'PIT': '23', 'CLE': '5', 'TEN': '10',
        'IND': '11', 'JAX': '30', 'HOU': '34', 'DEN': '7', 'LV': '13',
        'LAC': '24', 'ARI': '22', 'ATL': '1', 'CAR': '29', 'NO': '18',
        'TB': '27', 'WAS': '28',
    },
    'nba': {
        'DET': '8', 'CHI': '4', 'CLE': '5', 'IND': '11', 'MIL': '15',
        'ATL': '1', 'CHA': '30', 'MIA': '14', 'ORL': '19', 'WAS': '27',
        'BOS': '2', 'BKN': '17', 'NYK': '18', 'PHI': '20', 'TOR': '28',
        'DEN': '7', 'MIN': '16', 'OKC': '25', 'POR': '22', 'UTA': '26',
        'GSW': '9', 'LAC': '12', 'LAL': '13', 'PHX': '21', 'SAC': '23',
        'DAL': '6', 'HOU': '10', 'MEM': '29', 'NOP': '3', 'SAS': '24',
    },
    'mlb': {
        'DET': '6', 'CHW': '4', 'CLE': '5', 'KC': '7', 'MIN': '9',
        'BAL': '1', 'BOS': '2', 'NYY': '10', 'TB': '30', 'TOR': '14',
        'HOU': '18', 'LAA': '3', 'OAK': '11', 'SEA': '12', 'TEX': '13',
        'ATL': '15', 'MIA': '28', 'NYM': '21', 'PHI': '22', 'WAS': '24',
        'CHC': '16', 'CIN': '17', 'MIL': '8', 'PIT': '23', 'STL': '25',
        'ARI': '29', 'COL': '27', 'LAD': '19', 'SD': '25', 'SF': '26',
    },
    'nhl': {
        'DET': '5', 'CHI': '4', 'BUF': '2', 'BOS': '1', 'TOR': '10',
        'MTL': '8', 'OTT': '9', 'FLA': '3', 'TB': '25', 'CAR': '12',
        'NYR': '6', 'NYI': '7', 'NJ': '6', 'PHI': '4', 'PIT': '5',
        'WAS': '15', 'CBJ': '29', 'EDM': '22', 'CGY': '20', 'VAN': '23',
        'VGK': '37', 'LAK': '26', 'ANA': '24', 'SJ': '28', 'SEA': '55',
        'COL': '17', 'MIN': '30', 'WPG': '52', 'DAL': '25', 'STL': '19',
        'NSH': '18', 'ARI': '53',
    },
}


def get_team_schedule(sport, team_abbrev):
    """
    Fetch team-specific schedule from ESPN.
    Returns much smaller response than full scoreboard.
    """
    if sport not in SPORT_CONFIG:
        return None

    team_id = TEAM_IDS.get(sport, {}).get(team_abbrev.upper())
    if not team_id:
        return None

    config = SPORT_CONFIG[sport]
    url = f"{ESPN_BASE}/{config['path']}/teams/{team_id}/schedule"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching {sport} {team_abbrev}: {e}")

    return None


def get_scoreboard(sport):
    """Fetch current scoreboard for a sport."""
    if sport not in SPORT_CONFIG:
        return None

    config = SPORT_CONFIG[sport]
    url = f"{ESPN_BASE}/{config['path']}/scoreboard"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching {sport} scoreboard: {e}")

    return None


def parse_game(event, sport, tz_offset=0):
    """Parse ESPN event into minimal game dict.

    Args:
        event: ESPN event data
        sport: Sport type (nfl, nba, etc.)
        tz_offset: Timezone offset in hours from UTC (e.g., -5 for EST)
    """
    try:
        comp = event.get('competitions', [{}])[0]
        competitors = comp.get('competitors', [])

        if len(competitors) < 2:
            return None

        home = away = None
        for c in competitors:
            if c.get('homeAway') == 'home':
                home = c
            else:
                away = c

        if not home or not away:
            return None

        # Get status
        status_info = comp.get('status', {})
        status_type = status_info.get('type', {})
        state = status_type.get('state', 'pre')

        # Map to simple status
        if state == 'in':
            status = 'live'
        elif state == 'post':
            status = 'final'
        else:
            status = 'pre'

        game = {
            'sport': sport,
            'home': home.get('team', {}).get('abbreviation', '???'),
            'away': away.get('team', {}).get('abbreviation', '???'),
            'hs': int(home.get('score', '0') or 0),
            'as': int(away.get('score', '0') or 0),
            'status': status,
        }

        # Add live game details
        if status == 'live':
            period = status_info.get('period', 0)
            clock = status_info.get('displayClock', '')

            if sport == 'nfl':
                game['period'] = f"Q{period}"
            elif sport == 'nba':
                game['period'] = f"Q{period}"
            elif sport == 'mlb':
                half = 'T' if 'Top' in status_type.get('name', '') else 'B'
                game['period'] = f"{half}{period}"
            elif sport == 'nhl':
                game['period'] = f"P{period}"

            game['time'] = clock

        # Add scheduled game time
        if status == 'pre':
            date_str = event.get('date', '')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    # Apply timezone offset
                    dt = dt + timedelta(hours=tz_offset)
                    game['date'] = dt.strftime('%b %d')
                    game['time'] = dt.strftime('%I:%M %p').lstrip('0')
                    game['sort_date'] = date_str  # Keep original for sorting
                except:
                    pass

        return game

    except Exception as e:
        print(f"Parse error: {e}")
        return None


def get_upcoming_games(sport, team_abbrev, limit=4, tz_offset=0):
    """Get upcoming games for a team."""
    schedule = get_team_schedule(sport, team_abbrev)
    if not schedule:
        return []

    upcoming = []
    now = datetime.now()

    events = schedule.get('events', [])
    for event in events:
        try:
            date_str = event.get('date', '')
            if not date_str:
                continue

            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Only future games
            if dt.replace(tzinfo=None) > now:
                game = parse_game(event, sport, tz_offset)
                if game and game['status'] == 'pre':
                    upcoming.append(game)
                    if len(upcoming) >= limit:
                        break
        except:
            continue

    return upcoming


@app.route('/api/games', methods=['GET', 'POST'])
def get_games():
    """
    Main endpoint for Pico to fetch game data.

    POST body or GET params:
    {
        "teams": [
            {"sport": "nfl", "team_id": "DET"},
            {"sport": "nba", "team_id": "DET"},
            ...
        ],
        "tz": -5,  # Timezone offset (EST = -5, PST = -8)
        "final_mins": 30  # How long to show final scores (minutes)
    }

    Returns minimal JSON (~1-3KB):
    {
        "active": [...],   # Currently live/final games
        "upcoming": [...]  # Next games when no active
    }
    """
    # Get teams and options from request
    if request.method == 'POST':
        data = request.get_json() or {}
        teams = data.get('teams', [])
        tz_offset = data.get('tz', 0)
        final_mins = data.get('final_mins', 30)
    else:
        # Support GET with comma-separated teams
        teams_param = request.args.get('teams', '')
        tz_offset = int(request.args.get('tz', 0))
        final_mins = int(request.args.get('final_mins', 30))
        teams = []
        for t in teams_param.split(','):
            if ':' in t:
                sport, team_id = t.split(':')
                teams.append({'sport': sport.strip(), 'team_id': team_id.strip()})

    if not teams:
        return jsonify({'error': 'No teams specified', 'active': [], 'upcoming': []})

    active_games = []
    live_games = []  # Separate list for live games (always show)
    final_games = []  # Final games (filter by time)
    upcoming_games = []
    sports_checked = set()

    # Check each sport's scoreboard for active games
    for team in teams:
        sport = team.get('sport', 'nfl').lower()
        team_id = team.get('team_id', '').upper()

        if sport not in sports_checked:
            scoreboard = get_scoreboard(sport)
            sports_checked.add(sport)

            if scoreboard:
                for event in scoreboard.get('events', []):
                    game = parse_game(event, sport, tz_offset)
                    if game:
                        # Check if this game involves any of our teams
                        for t in teams:
                            if t.get('sport') == sport:
                                tid = t.get('team_id', '').upper()
                                if game['home'] == tid or game['away'] == tid:
                                    if game['status'] == 'live':
                                        if game not in live_games:
                                            live_games.append(game)
                                    elif game['status'] == 'final':
                                        if game not in final_games:
                                            final_games.append(game)
                                    break

    # Live games always take priority
    active_games = live_games.copy()

    # Only add final games if within the time window (final_mins)
    # ESPN doesn't give us exact end time, so we show finals for a period
    # After final_mins, we stop showing them and switch to upcoming
    if final_games and not live_games:
        # Show final scores for limited time, then switch to upcoming
        # Since we can't know exact end time, we limit to showing max 1 final
        active_games.extend(final_games[:1])

    # If no active games (or only stale finals), get upcoming games
    if not live_games:
        for team in teams:
            sport = team.get('sport', 'nfl').lower()
            team_id = team.get('team_id', '').upper()

            upcoming = get_upcoming_games(sport, team_id, limit=2, tz_offset=tz_offset)
            upcoming_games.extend(upcoming)

        # Sort by date chronologically and limit to 4
        upcoming_games.sort(key=lambda g: g.get('sort_date', '9999'))
        upcoming_games = upcoming_games[:4]

        # Remove sort_date from response (not needed by client)
        for g in upcoming_games:
            g.pop('sort_date', None)

    return jsonify({
        'active': active_games,
        'upcoming': upcoming_games,
        'ts': datetime.now().isoformat()
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'sports-ticker-proxy'})


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with usage info."""
    return jsonify({
        'service': 'Sports Ticker Proxy API',
        'endpoints': {
            '/api/games': 'GET/POST - Fetch games for configured teams',
            '/api/health': 'GET - Health check',
        },
        'example': '/api/games?teams=nfl:DET,nba:DET,nhl:DET,mlb:DET'
    })


# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

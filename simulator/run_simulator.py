#!/usr/bin/env python3
"""
Sports Ticker Local Simulator

A clean, readable simulator for testing the sports ticker before hardware arrives.

Usage:
    python simulator/run_simulator.py

Controls:
    q - Quit
    r - Refresh scores now
    n - Next game
    p - Previous game
    s - Switch sport (NFL/NBA/MLB/NHL)
"""

import sys
import os
import time
import json
import threading
import select

# Add project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ANSI colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_WHITE = '\033[47m'

# Team colors for display
TEAM_COLORS = {
    # NFL
    'DET': (Colors.BLUE, 'Lions'),
    'CHI': (Colors.BLUE, 'Bears'),
    'GB': (Colors.GREEN, 'Packers'),
    'MIN': (Colors.MAGENTA, 'Vikings'),
    'DAL': (Colors.BLUE, 'Cowboys'),
    'PHI': (Colors.GREEN, 'Eagles'),
    'NYG': (Colors.BLUE, 'Giants'),
    'WAS': (Colors.RED, 'Commanders'),
    'KC': (Colors.RED, 'Chiefs'),
    'BUF': (Colors.BLUE, 'Bills'),
    'MIA': (Colors.CYAN, 'Dolphins'),
    'NE': (Colors.BLUE, 'Patriots'),
    'BAL': (Colors.MAGENTA, 'Ravens'),
    'CIN': (Colors.YELLOW, 'Bengals'),
    'CLE': (Colors.YELLOW, 'Browns'),
    'PIT': (Colors.YELLOW, 'Steelers'),
    'SF': (Colors.RED, 'SF 49ers'),
    'SEA': (Colors.GREEN, 'Seahawks'),
    'LAR': (Colors.BLUE, 'Rams'),
    'ARI': (Colors.RED, 'Cardinals'),

    # NBA
    'LAL': (Colors.MAGENTA, 'Lakers'),
    'BOS': (Colors.GREEN, 'Celtics'),
    'GSW': (Colors.BLUE, 'Warriors'),
    'MIL': (Colors.GREEN, 'Bucks'),
    'PHX': (Colors.YELLOW, 'Suns'),
    'DEN': (Colors.BLUE, 'Nuggets'),
    'MEM': (Colors.CYAN, 'Grizzlies'),
    'CLE': (Colors.RED, 'Cavaliers'),
    'NYK': (Colors.BLUE, 'Knicks'),
    'BKN': (Colors.WHITE, 'Nets'),

    # MLB
    'NYY': (Colors.BLUE, 'Yankees'),
    'LAD': (Colors.BLUE, 'Dodgers'),
    'HOU': (Colors.YELLOW, 'Astros'),
    'ATL': (Colors.RED, 'Braves'),
    'PHI': (Colors.RED, 'Phillies'),
    'SD': (Colors.YELLOW, 'Padres'),
    'SEA': (Colors.CYAN, 'Mariners'),
    'TB': (Colors.CYAN, 'Rays'),
    'TOR': (Colors.BLUE, 'Blue Jays'),
    'TEX': (Colors.BLUE, 'Rangers'),

    # NHL
    'TOR': (Colors.BLUE, 'Maple Leafs'),
    'MTL': (Colors.RED, 'Canadiens'),
    'BOS': (Colors.YELLOW, 'Bruins'),
    'NYR': (Colors.BLUE, 'Rangers'),
    'PIT': (Colors.YELLOW, 'Penguins'),
    'CHI': (Colors.RED, 'Blackhawks'),
    'DET': (Colors.RED, 'Red Wings'),
    'COL': (Colors.RED, 'Avalanche'),
    'VGK': (Colors.YELLOW, 'Golden Knights'),
    'EDM': (Colors.BLUE, 'Oilers'),
}


def get_team_color(team_abbrev):
    """Get color for team, default to white."""
    if team_abbrev in TEAM_COLORS:
        return TEAM_COLORS[team_abbrev][0]
    return Colors.WHITE


def clear_screen():
    """Clear terminal screen."""
    print('\033[2J\033[H', end='')


class ESPNClient:
    """Fetch scores from ESPN API."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

    ENDPOINTS = {
        'nfl': '/football/nfl/scoreboard',
        'nba': '/basketball/nba/scoreboard',
        'mlb': '/baseball/mlb/scoreboard',
        'nhl': '/hockey/nhl/scoreboard',
    }

    def get_scores(self, sport='nfl'):
        """Fetch scores for a sport."""
        endpoint = self.ENDPOINTS.get(sport.lower())
        if not endpoint:
            return []

        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_games(data, sport)
        except Exception as e:
            print(f"API Error: {e}")
            return []

    def _parse_games(self, data, sport):
        """Parse ESPN response into game objects."""
        games = []

        for event in data.get('events', []):
            try:
                competition = event['competitions'][0]
                competitors = competition['competitors']

                home = next(c for c in competitors if c['homeAway'] == 'home')
                away = next(c for c in competitors if c['homeAway'] == 'away')

                status = competition['status']
                state = status['type']['state']  # pre, in, post

                game = {
                    'sport': sport.upper(),
                    'home_team': home['team']['abbreviation'],
                    'home_name': home['team'].get('shortDisplayName', home['team']['abbreviation']),
                    'home_score': int(home.get('score', 0)),
                    'away_team': away['team']['abbreviation'],
                    'away_name': away['team'].get('shortDisplayName', away['team']['abbreviation']),
                    'away_score': int(away.get('score', 0)),
                    'state': state,
                    'status': status['type']['shortDetail'],
                    'detail': status.get('displayClock', ''),
                }

                # Add period info
                if state == 'in':
                    game['period'] = status.get('period', 0)
                    game['clock'] = status.get('displayClock', '')

                games.append(game)
            except (KeyError, StopIteration):
                continue

        return games


class SimulatorDisplay:
    """Clean text-based display for simulator."""

    WIDTH = 64

    def __init__(self):
        self.current_game_idx = 0
        self.games = []
        self.current_sport = 'nfl'
        self.sports = ['nfl', 'nba', 'mlb', 'nhl']
        self.message = ""

    def set_games(self, games):
        """Update game list."""
        self.games = games
        if self.current_game_idx >= len(games):
            self.current_game_idx = 0

    def next_game(self):
        """Show next game."""
        if self.games:
            self.current_game_idx = (self.current_game_idx + 1) % len(self.games)

    def prev_game(self):
        """Show previous game."""
        if self.games:
            self.current_game_idx = (self.current_game_idx - 1) % len(self.games)

    def next_sport(self):
        """Cycle to next sport."""
        idx = self.sports.index(self.current_sport)
        self.current_sport = self.sports[(idx + 1) % len(self.sports)]
        return self.current_sport

    def render(self):
        """Render current display to terminal."""
        clear_screen()

        # Header
        print(f"{Colors.CYAN}{'═' * 66}{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}  {Colors.BOLD}SPORTS TICKER SIMULATOR{Colors.RESET}  " +
              f"[{self.current_sport.upper()}]  " +
              f"Game {self.current_game_idx + 1}/{len(self.games) if self.games else 0}  " +
              f"{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 66}{Colors.RESET}")

        if not self.games:
            self._render_no_games()
        else:
            self._render_game(self.games[self.current_game_idx])

        # Footer
        print(f"{Colors.CYAN}{'═' * 66}{Colors.RESET}")
        print(f"{Colors.DIM}Controls: [n]ext [p]rev [s]port [r]efresh [q]uit{Colors.RESET}")
        print(f"{Colors.DIM}Web interface: http://localhost:8080{Colors.RESET}")

        if self.message:
            print(f"\n{Colors.YELLOW}{self.message}{Colors.RESET}")

    def _render_no_games(self):
        """Render when no games available."""
        print()
        print(f"  {Colors.DIM}No games currently available for {self.current_sport.upper()}{Colors.RESET}")
        print()
        print(f"  {Colors.DIM}Try switching sports with 's' key{Colors.RESET}")
        print()
        for _ in range(10):
            print()

    def _render_game(self, game):
        """Render a single game."""
        away_color = get_team_color(game['away_team'])
        home_color = get_team_color(game['home_team'])

        state = game['state']

        print()

        # Game status header
        if state == 'pre':
            status_color = Colors.CYAN
            status_text = f"UPCOMING: {game['status']}"
        elif state == 'in':
            status_color = Colors.GREEN
            status_text = f"LIVE: {game['status']}"
        else:
            status_color = Colors.DIM
            status_text = f"FINAL: {game['status']}"

        print(f"  {status_color}{Colors.BOLD}{status_text}{Colors.RESET}")
        print()

        # Score display
        print(f"  {'─' * 62}")
        print()

        # Away team
        away_score = str(game['away_score']).rjust(3) if state != 'pre' else '   '
        print(f"  {away_color}{Colors.BOLD}{game['away_team']:>6}{Colors.RESET}  " +
              f"{game['away_name']:<20}  " +
              f"{Colors.BOLD}{away_score}{Colors.RESET}")

        print()
        print(f"  {'VS':^62}")
        print()

        # Home team
        home_score = str(game['home_score']).rjust(3) if state != 'pre' else '   '
        print(f"  {home_color}{Colors.BOLD}{game['home_team']:>6}{Colors.RESET}  " +
              f"{game['home_name']:<20}  " +
              f"{Colors.BOLD}{home_score}{Colors.RESET}")

        print()
        print(f"  {'─' * 62}")
        print()

        # Additional info for live games
        if state == 'in' and game.get('clock'):
            print(f"  {Colors.GREEN}⏱  {game.get('clock', '')}{Colors.RESET}")

        print()


class WebHandler(BaseHTTPRequestHandler):
    """Simple web handler for configuration."""

    simulator = None
    config_path = os.path.join(PROJECT_ROOT, 'config.json')

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self._serve_home()
        elif self.path == '/api/status':
            self._serve_status()
        elif self.path == '/api/games':
            self._serve_games()
        else:
            self._serve_404()

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/config':
            self._save_config()
        else:
            self._serve_404()

    def _serve_home(self):
        """Serve home page."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Sports Ticker Simulator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }
        h2 { color: #00d4ff; margin-top: 30px; }
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .game {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #0f3460;
            border-radius: 8px;
        }
        .team { font-weight: bold; font-size: 1.2em; }
        .score { font-size: 1.5em; font-weight: bold; color: #00d4ff; }
        .status {
            text-align: center;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .status.live { background: #22c55e; color: white; }
        .status.final { background: #666; }
        .status.upcoming { background: #3b82f6; }
        .btn {
            background: #00d4ff;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
        }
        .btn:hover { background: #00a8cc; }
        select, input {
            background: #0f3460;
            color: #eee;
            border: 1px solid #00d4ff;
            padding: 10px;
            border-radius: 5px;
            margin: 5px;
        }
        .sports-tabs {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        .tab {
            padding: 10px 20px;
            background: #0f3460;
            border-radius: 5px;
            cursor: pointer;
        }
        .tab.active { background: #00d4ff; color: #1a1a2e; }
        #games { min-height: 200px; }
        .loading { text-align: center; color: #888; padding: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏈 Sports Ticker Simulator</h1>

        <div class="card">
            <h2>Live Scores</h2>
            <div class="sports-tabs">
                <div class="tab active" data-sport="nfl">NFL</div>
                <div class="tab" data-sport="nba">NBA</div>
                <div class="tab" data-sport="mlb">MLB</div>
                <div class="tab" data-sport="nhl">NHL</div>
            </div>
            <div id="games"><div class="loading">Loading games...</div></div>
            <button class="btn" onclick="refreshGames()">↻ Refresh</button>
        </div>

        <div class="card">
            <h2>Configuration</h2>
            <p>Add your favorite teams to track:</p>
            <select id="sport-select">
                <option value="nfl">NFL</option>
                <option value="nba">NBA</option>
                <option value="mlb">MLB</option>
                <option value="nhl">NHL</option>
            </select>
            <input type="text" id="team-input" placeholder="Team abbreviation (e.g., DET)">
            <button class="btn" onclick="addTeam()">Add Team</button>

            <h3>Your Teams</h3>
            <div id="my-teams"></div>
        </div>

        <div class="card">
            <h2>System Status</h2>
            <div id="status">Loading...</div>
        </div>
    </div>

    <script>
        let currentSport = 'nfl';
        let config = { teams: [], update_interval: 120, brightness: 200 };

        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.onclick = () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentSport = tab.dataset.sport;
                loadGames();
            };
        });

        async function loadGames() {
            const gamesDiv = document.getElementById('games');
            gamesDiv.innerHTML = '<div class="loading">Loading...</div>';

            try {
                const res = await fetch('/api/games?sport=' + currentSport);
                const games = await res.json();

                if (games.length === 0) {
                    gamesDiv.innerHTML = '<p>No games scheduled</p>';
                    return;
                }

                gamesDiv.innerHTML = games.map(g => `
                    <div class="game">
                        <div>
                            <div class="team">${g.away_team}</div>
                            <div>${g.away_name}</div>
                        </div>
                        <div class="score">${g.state === 'pre' ? '-' : g.away_score}</div>
                        <div class="status ${g.state === 'in' ? 'live' : g.state === 'post' ? 'final' : 'upcoming'}">
                            ${g.status}
                        </div>
                        <div class="score">${g.state === 'pre' ? '-' : g.home_score}</div>
                        <div>
                            <div class="team">${g.home_team}</div>
                            <div>${g.home_name}</div>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                gamesDiv.innerHTML = '<p>Error loading games</p>';
            }
        }

        function refreshGames() { loadGames(); }

        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                document.getElementById('status').innerHTML = `
                    <p><strong>Mode:</strong> Simulator</p>
                    <p><strong>Games Loaded:</strong> ${status.games_count}</p>
                    <p><strong>Current Sport:</strong> ${status.sport}</p>
                `;
            } catch (e) {
                document.getElementById('status').innerHTML = '<p>Error loading status</p>';
            }
        }

        function addTeam() {
            const sport = document.getElementById('sport-select').value;
            const team = document.getElementById('team-input').value.toUpperCase();
            if (!team) return;

            config.teams.push({ sport, team_id: team, team_name: team });
            renderTeams();
            document.getElementById('team-input').value = '';
        }

        function removeTeam(idx) {
            config.teams.splice(idx, 1);
            renderTeams();
        }

        function renderTeams() {
            const div = document.getElementById('my-teams');
            if (config.teams.length === 0) {
                div.innerHTML = '<p>No teams added yet</p>';
                return;
            }
            div.innerHTML = config.teams.map((t, i) => `
                <div class="game">
                    <span>${t.sport.toUpperCase()} - ${t.team_id}</span>
                    <button class="btn" onclick="removeTeam(${i})">Remove</button>
                </div>
            `).join('');
        }

        // Initial load
        loadGames();
        loadStatus();
        renderTeams();

        // Auto-refresh
        setInterval(loadGames, 60000);
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_status(self):
        """Serve status JSON."""
        status = {
            'mode': 'simulator',
            'games_count': len(self.simulator.games) if self.simulator else 0,
            'sport': self.simulator.current_sport if self.simulator else 'nfl',
        }
        self._send_json(status)

    def _serve_games(self):
        """Serve games JSON."""
        query = parse_qs(urlparse(self.path).query)
        sport = query.get('sport', ['nfl'])[0]

        client = ESPNClient()
        games = client.get_scores(sport)
        self._send_json(games)

    def _send_json(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _serve_404(self):
        """Send 404 response."""
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

    def _save_config(self):
        """Save configuration."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            config = json.loads(post_data)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self._send_json({'success': True})
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})


def run_web_server(display, port=8080):
    """Run web server in background."""
    WebHandler.simulator = display
    server = HTTPServer(('localhost', port), WebHandler)
    server.serve_forever()


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  SPORTS TICKER SIMULATOR")
    print("  Local Development & Testing")
    print("=" * 60 + "\n")

    # Initialize
    display = SimulatorDisplay()
    client = ESPNClient()

    # Start web server
    web_thread = threading.Thread(target=run_web_server, args=(display,), daemon=True)
    web_thread.start()
    print("Web server started: http://localhost:8080")

    # Initial fetch
    print("Fetching scores...")
    games = client.get_scores(display.current_sport)
    display.set_games(games)
    print(f"Loaded {len(games)} games\n")

    # Enable raw input mode for single keypress detection
    import tty
    import termios

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        last_fetch = time.time()
        fetch_interval = 120  # seconds

        while True:
            # Render display
            display.render()

            # Check for auto-refresh
            if time.time() - last_fetch > fetch_interval:
                display.message = "Refreshing..."
                display.render()
                games = client.get_scores(display.current_sport)
                display.set_games(games)
                display.message = f"Updated: {len(games)} games"
                last_fetch = time.time()

            # Check for keypress (non-blocking)
            if select.select([sys.stdin], [], [], 1)[0]:
                key = sys.stdin.read(1)

                if key == 'q':
                    break
                elif key == 'n':
                    display.next_game()
                    display.message = ""
                elif key == 'p':
                    display.prev_game()
                    display.message = ""
                elif key == 'r':
                    display.message = "Refreshing..."
                    display.render()
                    games = client.get_scores(display.current_sport)
                    display.set_games(games)
                    display.message = f"Refreshed: {len(games)} games"
                    last_fetch = time.time()
                elif key == 's':
                    sport = display.next_sport()
                    display.message = f"Switching to {sport.upper()}..."
                    display.render()
                    games = client.get_scores(sport)
                    display.set_games(games)
                    display.message = f"Loaded {len(games)} {sport.upper()} games"
                    last_fetch = time.time()

    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear_screen()
        print("Simulator stopped.")


if __name__ == '__main__':
    main()

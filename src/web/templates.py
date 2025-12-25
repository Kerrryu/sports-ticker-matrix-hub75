"""
HTML Templates for Web Interface

Provides HTML page templates for the sports ticker web interface.
Uses simple string formatting for MicroPython compatibility.

Usage:
    from web.templates import HOME_PAGE, render_template

    html = render_template(HOME_PAGE, {'version': '1.0.0'})
"""

# Base HTML structure
BASE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{title} - Sports Ticker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a2e;
            color: #eee;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #00d4ff;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #00d4ff;
            font-size: 1.2em;
            margin-top: 30px;
        }}
        .card {{
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .nav {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .nav a {{
            background: #0f3460;
            color: #00d4ff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
        }}
        .nav a:hover, .nav a.active {{
            background: #00d4ff;
            color: #1a1a2e;
        }}
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #0f3460;
        }}
        .stat:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            color: #888;
        }}
        .stat-value {{
            color: #00d4ff;
            font-weight: bold;
        }}
        button {{
            background: #00d4ff;
            color: #1a1a2e;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
            margin-top: 10px;
        }}
        button:hover {{
            background: #00b8e6;
        }}
        button.danger {{
            background: #e94560;
        }}
        button.danger:hover {{
            background: #d63850;
        }}
        input, select {{
            background: #0f3460;
            border: 1px solid #00d4ff;
            color: #eee;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
            margin-bottom: 10px;
        }}
        input:focus, select:focus {{
            outline: none;
            border-color: #00ff88;
        }}
        .team-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #0f3460;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .team-info {{
            flex-grow: 1;
        }}
        .team-sport {{
            font-size: 0.8em;
            color: #888;
            text-transform: uppercase;
        }}
        .team-name {{
            font-weight: bold;
        }}
        .slider-container {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .slider {{
            flex-grow: 1;
        }}
        input[type="range"] {{
            -webkit-appearance: none;
            height: 8px;
            background: #0f3460;
            border-radius: 4px;
        }}
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            background: #00d4ff;
            border-radius: 50%;
            cursor: pointer;
        }}
        .message {{
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .message.success {{
            background: #00ff8833;
            border: 1px solid #00ff88;
        }}
        .message.error {{
            background: #e9456033;
            border: 1px solid #e94560;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sports Ticker</h1>
        <nav class="nav">
            <a href="/" class="{nav_home}">Home</a>
            <a href="/teams" class="{nav_teams}">Teams</a>
            <a href="/settings" class="{nav_settings}">Settings</a>
        </nav>
        {content}
        <div class="footer">Sports Ticker v{version}</div>
    </div>
</body>
</html>"""

# Home page content
HOME_CONTENT = """
<div class="card">
    <h2>System Status</h2>
    <div class="stat">
        <span class="stat-label">Version</span>
        <span class="stat-value">{version}</span>
    </div>
    <div class="stat">
        <span class="stat-label">IP Address</span>
        <span class="stat-value">{ip}</span>
    </div>
    <div class="stat">
        <span class="stat-label">Teams Configured</span>
        <span class="stat-value">{teams_count}</span>
    </div>
    <div class="stat">
        <span class="stat-label">Active Games</span>
        <span class="stat-value">{games_count}</span>
    </div>
</div>
<div class="card">
    <h2>Quick Actions</h2>
    <button onclick="location.href='/teams'">Configure Teams</button>
    <button onclick="location.href='/settings'">Settings</button>
    <button onclick="checkUpdates()">Check Updates</button>
</div>
<div class="card">
    <h2>Demo Mode</h2>
    <p style="color:#888;font-size:0.9em;margin-bottom:15px;">Test display screens without waiting for real game data.</p>
    <button onclick="showDemo('live')">Live Game</button>
    <button onclick="showDemo('final')">Final Score</button>
    <button onclick="showDemo('upcoming')">Upcoming</button>
    <button class="danger" onclick="showDemo('reset')">Reset</button>
</div>
<script>
function checkUpdates() {{
    fetch('/api/update/check')
        .then(r => r.json())
        .then(data => {{
            if (data.update_available) {{
                if (confirm('Update ' + data.latest_version + ' available!\\n\\n' + data.changelog + '\\n\\nInstall now?')) {{
                    fetch('/api/update/install', {{method: 'POST'}})
                        .then(() => alert('Installing... Device will restart.'));
                }}
            }} else {{
                alert('You are on the latest version.');
            }}
        }})
        .catch(e => alert('Error: ' + e));
}}

function showDemo(mode) {{
    fetch('/api/demo/' + mode, {{method: 'POST'}})
        .then(r => r.json())
        .then(data => {{
            if (data.status === 'ok') {{
                // Brief confirmation
                var msg = mode === 'reset' ? 'Display reset to live data' : 'Showing ' + mode + ' demo';
                console.log(msg);
            }} else {{
                alert('Error: ' + data.message);
            }}
        }})
        .catch(e => alert('Demo error: ' + e));
}}
</script>
"""

# Teams page content
TEAMS_CONTENT = """
<div class="card">
    <h2>Add Team</h2>
    <form id="addTeamForm">
        <select id="sport" name="sport">
            <option value="nfl">NFL - Football</option>
            <option value="nba">NBA - Basketball</option>
            <option value="mlb">MLB - Baseball</option>
            <option value="nhl">NHL - Hockey</option>
        </select>
        <input type="text" id="team_id" placeholder="Team ID (e.g., DET, GB, KC)" required>
        <input type="text" id="team_name" placeholder="Team Name (optional)">
        <button type="submit">Add Team</button>
    </form>
</div>
<div class="card">
    <h2>Your Teams</h2>
    <div id="teamsList">Loading...</div>
</div>
<script>
function loadTeams() {{
    fetch('/api/teams')
        .then(r => r.json())
        .then(data => {{
            const list = document.getElementById('teamsList');
            if (data.teams.length === 0) {{
                list.innerHTML = '<p>No teams configured. Add your favorite teams above!</p>';
                return;
            }}
            list.innerHTML = data.teams.map(t => `
                <div class="team-item">
                    <div class="team-info">
                        <div class="team-sport">${{t.sport.toUpperCase()}}</div>
                        <div class="team-name">${{t.team_id}} - ${{t.team_name || 'Unknown'}}</div>
                    </div>
                    <button class="danger" onclick="removeTeam('${{t.sport}}', '${{t.team_id}}')">Remove</button>
                </div>
            `).join('');
        }});
}}

function removeTeam(sport, teamId) {{
    if (!confirm('Remove ' + teamId + '?')) return;
    fetch('/api/teams', {{
        method: 'DELETE',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{sport: sport, team_id: teamId}})
    }}).then(() => loadTeams());
}}

document.getElementById('addTeamForm').onsubmit = function(e) {{
    e.preventDefault();
    fetch('/api/teams', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
            sport: document.getElementById('sport').value,
            team_id: document.getElementById('team_id').value,
            team_name: document.getElementById('team_name').value
        }})
    }}).then(r => r.json()).then(data => {{
        if (data.status === 'ok') {{
            document.getElementById('team_id').value = '';
            document.getElementById('team_name').value = '';
            loadTeams();
        }} else {{
            alert(data.message);
        }}
    }});
}};

loadTeams();
</script>
"""

# Settings page content
SETTINGS_CONTENT = """
<div class="card">
    <h2>Display Settings</h2>
    <label>Brightness</label>
    <div class="slider-container">
        <input type="range" id="brightness" min="0" max="255" value="{brightness}" class="slider">
        <span id="brightnessVal">{brightness}</span>
    </div>
    <label>Update Interval (seconds)</label>
    <input type="number" id="update_interval" value="{update_interval}" min="30" max="600">
    <button onclick="saveSettings()">Save Settings</button>
</div>
<div class="card">
    <h2>API Settings</h2>
    <label>Proxy URL</label>
    <input type="text" id="proxy_url" value="{proxy_url}" placeholder="https://your-proxy.vercel.app">
    <p style="color:#888;font-size:0.85em;margin-top:-5px;">Required for fetching scores. ESPN data is too large for Pico without a proxy.</p>
    <button onclick="saveProxy()">Save Proxy URL</button>
    <button onclick="testProxy()">Test Connection</button>
</div>
<div class="card">
    <h2>System</h2>
    <button onclick="location.reload()">Refresh Page</button>
    <button class="danger" onclick="rollback()">Rollback Update</button>
</div>
<script>
document.getElementById('brightness').oninput = function() {{
    document.getElementById('brightnessVal').textContent = this.value;
}};

function saveSettings() {{
    fetch('/api/settings', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
            brightness: parseInt(document.getElementById('brightness').value),
            update_interval: parseInt(document.getElementById('update_interval').value)
        }})
    }}).then(r => r.json()).then(data => {{
        alert(data.status === 'ok' ? 'Settings saved!' : 'Error: ' + data.message);
    }});
}}

function saveProxy() {{
    fetch('/api/settings', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
            proxy_url: document.getElementById('proxy_url').value
        }})
    }}).then(r => r.json()).then(data => {{
        alert(data.status === 'ok' ? 'Proxy URL saved!' : 'Error: ' + data.message);
    }});
}}

function testProxy() {{
    var url = document.getElementById('proxy_url').value;
    if (!url) {{
        alert('Please enter a proxy URL first');
        return;
    }}
    fetch(url + '/api/health')
        .then(r => r.json())
        .then(data => {{
            if (data.status === 'ok') {{
                alert('Proxy connection successful!');
            }} else {{
                alert('Proxy responded but status not ok: ' + JSON.stringify(data));
            }}
        }})
        .catch(e => alert('Connection failed: ' + e));
}}

function rollback() {{
    if (!confirm('Rollback to previous version? Device will restart.')) return;
    fetch('/api/update/rollback', {{method: 'POST'}})
        .then(() => alert('Rolling back... Device will restart.'));
}}
</script>
"""

# Complete page templates
HOME_PAGE = {
    'title': 'Home',
    'nav_home': 'active',
    'nav_teams': '',
    'nav_settings': '',
    'content': HOME_CONTENT,
}

TEAMS_PAGE = {
    'title': 'Teams',
    'nav_home': '',
    'nav_teams': 'active',
    'nav_settings': '',
    'content': TEAMS_CONTENT,
}

SETTINGS_PAGE = {
    'title': 'Settings',
    'nav_home': '',
    'nav_teams': '',
    'nav_settings': 'active',
    'content': SETTINGS_CONTENT,
}


def render_template(template_data, context=None):
    """
    Render HTML template with context data.

    Args:
        template_data: Dict with template info
        context: Dict with values to substitute

    Returns:
        Rendered HTML string
    """
    if context is None:
        context = {}

    # Merge template data with context
    merged = {}
    merged.update(template_data)
    merged.update(context)

    # Set defaults
    merged.setdefault('version', '1.0.0')
    merged.setdefault('ip', 'Unknown')
    merged.setdefault('teams_count', 0)
    merged.setdefault('games_count', 0)
    merged.setdefault('brightness', 128)
    merged.setdefault('update_interval', 120)
    merged.setdefault('proxy_url', '')

    # Render content first
    content = template_data.get('content', '')
    try:
        content = content.format(**merged)
    except KeyError:
        pass  # Some placeholders might be missing

    # Update merged with rendered content
    merged['content'] = content

    # Render base template
    try:
        return BASE_TEMPLATE.format(**merged)
    except KeyError as e:
        return f"<h1>Template Error</h1><p>Missing key: {e}</p>"


# Test when run directly
if __name__ == '__main__':
    print("Template Test")
    print("=" * 40)

    context = {
        'version': '1.0.0',
        'ip': '192.168.1.100',
        'teams_count': 3,
        'games_count': 1,
    }

    html = render_template(HOME_PAGE, context)
    print(f"Rendered HTML length: {len(html)} bytes")
    print("\nFirst 500 characters:")
    print(html[:500])

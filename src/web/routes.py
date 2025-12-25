"""
Web Routes - URL Handlers for Sports Ticker

Defines all HTTP endpoints for the web interface:
- Home page
- Team configuration
- Settings
- API endpoints
- OTA updates

Usage:
    from web.routes import setup_routes

    setup_routes(server, app)
"""

import json
from .templates import (
    HOME_PAGE,
    TEAMS_PAGE,
    SETTINGS_PAGE,
    render_template,
)


def setup_routes(server, app):
    """
    Register all routes with the web server.

    Args:
        server: WebServer instance
        app: SportsTicker application instance
    """
    # HTML Pages
    server.route('/', lambda r: handle_home(r, app), ['GET'])
    server.route('/teams', lambda r: handle_teams_page(r, app), ['GET'])
    server.route('/settings', lambda r: handle_settings_page(r, app), ['GET'])

    # API Endpoints
    server.route('/api/status', lambda r: handle_api_status(r, app), ['GET'])
    server.route('/api/config', lambda r: handle_api_config(r, app), ['GET', 'POST'])
    server.route('/api/teams', lambda r: handle_api_teams(r, app), ['GET', 'POST', 'DELETE'])
    server.route('/api/settings', lambda r: handle_api_settings(r, app), ['GET', 'POST'])
    server.route('/api/games', lambda r: handle_api_games(r, app), ['GET'])

    # OTA Update Routes
    server.route('/api/update/check', lambda r: handle_update_check(r, app), ['GET'])
    server.route('/api/update/install', lambda r: handle_update_install(r, app), ['POST'])
    server.route('/api/update/rollback', lambda r: handle_update_rollback(r, app), ['POST'])

    # Demo/Test Routes
    server.route('/api/demo/live', lambda r: handle_demo_live(r, app), ['POST'])
    server.route('/api/demo/upcoming', lambda r: handle_demo_upcoming(r, app), ['POST'])
    server.route('/api/demo/final', lambda r: handle_demo_final(r, app), ['POST'])
    server.route('/api/demo/reset', lambda r: handle_demo_reset(r, app), ['POST'])

    print("Web routes registered")


# === HTML Page Handlers ===

def handle_home(request, app):
    """Render home page."""
    # Get system info
    info = {
        'version': app.__version__ if hasattr(app, '__version__') else '1.0.0',
        'ip': app.wifi.ip_address if app.wifi else 'Not connected',
        'teams_count': len(app.config.get('teams', [])) if app.config else 0,
        'games_count': len(app.current_games) if hasattr(app, 'current_games') else 0,
    }
    return render_template(HOME_PAGE, info)


def handle_teams_page(request, app):
    """Render teams configuration page."""
    info = {
        'teams': app.config.get('teams', []) if app.config else [],
    }
    return render_template(TEAMS_PAGE, info)


def handle_settings_page(request, app):
    """Render settings page."""
    info = {
        'brightness': app.config.get('brightness', 128) if app.config else 128,
        'update_interval': app.config.get('update_interval', 120) if app.config else 120,
        'proxy_url': app.config.get('proxy_url', '') if app.config else '',
    }
    return render_template(SETTINGS_PAGE, info)


# === API Handlers ===

def handle_api_status(request, app):
    """Return system status."""
    import gc

    status = {
        'status': 'ok',
        'version': getattr(app, '__version__', '1.0.0'),
        'wifi_connected': app.wifi.is_connected if app.wifi else False,
        'ip_address': app.wifi.ip_address if app.wifi else None,
        'free_memory': gc.mem_free(),
        'games_active': len(app.current_games) if hasattr(app, 'current_games') else 0,
    }

    return status


def handle_api_config(request, app):
    """Get or set configuration."""
    if request['method'] == 'GET':
        return app.config.data if app.config else {}

    elif request['method'] == 'POST':
        try:
            body = json.loads(request['body'])
            if app.config:
                app.config.update(body)
                app.config.save()
            return {'status': 'ok', 'message': 'Config saved'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def handle_api_teams(request, app):
    """Manage team list."""
    if request['method'] == 'GET':
        teams = app.config.get('teams', []) if app.config else []
        return {'teams': teams}

    elif request['method'] == 'POST':
        try:
            body = json.loads(request['body'])
            team = {
                'sport': body.get('sport', 'nfl'),
                'team_id': body.get('team_id', '').upper(),
                'team_name': body.get('team_name', ''),
                'enabled': body.get('enabled', True),
            }

            if app.config:
                teams = app.config.get('teams', [])
                # Check for duplicate
                for t in teams:
                    if t['team_id'] == team['team_id'] and t['sport'] == team['sport']:
                        return {'status': 'error', 'message': 'Team already exists'}
                teams.append(team)
                app.config.set('teams', teams)
                app.config.save()

            return {'status': 'ok', 'message': 'Team added', 'team': team}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    elif request['method'] == 'DELETE':
        try:
            body = json.loads(request['body'])
            team_id = body.get('team_id', '').upper()
            sport = body.get('sport', 'nfl')

            if app.config:
                teams = app.config.get('teams', [])
                teams = [t for t in teams if not (t['team_id'] == team_id and t['sport'] == sport)]
                app.config.set('teams', teams)
                app.config.save()

            return {'status': 'ok', 'message': 'Team removed'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def handle_api_settings(request, app):
    """Get or update settings."""
    if request['method'] == 'GET':
        settings = {
            'brightness': app.config.get('brightness', 128) if app.config else 128,
            'update_interval': app.config.get('update_interval', 120) if app.config else 120,
            'auto_updates': app.config.get('auto_updates', True) if app.config else True,
            'timezone_offset': app.config.get('timezone_offset', -5) if app.config else -5,
            'proxy_url': app.config.get('proxy_url', '') if app.config else '',
        }
        return settings

    elif request['method'] == 'POST':
        try:
            body = json.loads(request['body'])

            if app.config:
                if 'brightness' in body:
                    app.config.set('brightness', int(body['brightness']))
                if 'update_interval' in body:
                    app.config.set('update_interval', int(body['update_interval']))
                if 'auto_updates' in body:
                    app.config.set('auto_updates', bool(body['auto_updates']))
                if 'timezone_offset' in body:
                    app.config.set('timezone_offset', int(body['timezone_offset']))
                if 'proxy_url' in body:
                    app.config.set('proxy_url', str(body['proxy_url']).strip())
                    # Update API client with new proxy URL
                    if app.api:
                        app.api.proxy_url = body['proxy_url'].strip() or None

                app.config.save()

                # Apply brightness immediately
                if app.display and 'brightness' in body:
                    app.display.set_brightness(int(body['brightness']))

            return {'status': 'ok', 'message': 'Settings saved'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def handle_api_games(request, app):
    """Get current games."""
    games = app.current_games if hasattr(app, 'current_games') else []
    return {'games': games}


# === OTA Update Handlers ===

def handle_update_check(request, app):
    """Check for available updates."""
    if not app.ota:
        return {'status': 'error', 'message': 'OTA not configured'}

    try:
        has_update = app.ota.check_for_update()
        return {
            'update_available': has_update,
            'current_version': app.ota.current_version,
            'latest_version': app.ota.latest_version if has_update else app.ota.current_version,
            'changelog': app.ota.get_changelog() if has_update else '',
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def handle_update_install(request, app):
    """Install available update."""
    if not app.ota:
        return {'status': 'error', 'message': 'OTA not configured'}

    try:
        success = app.ota.full_update_flow()
        if success:
            return {'status': 'ok', 'message': 'Update installing, restarting...'}
        else:
            return {'status': 'error', 'message': 'Update failed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def handle_update_rollback(request, app):
    """Rollback to previous version."""
    if not app.ota:
        return {'status': 'error', 'message': 'OTA not configured'}

    try:
        success = app.ota.rollback()
        if success:
            app.ota.restart_device()
            return {'status': 'ok', 'message': 'Rolling back, restarting...'}
        else:
            return {'status': 'error', 'message': 'Rollback failed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# === Demo/Test Handlers ===

def handle_demo_live(request, app):
    """Show demo live game on display."""
    try:
        # Sample live game data
        demo_game = {
            'sport': 'nfl',
            'home_team': 'MIN',
            'away_team': 'DET',
            'home_score': 17,
            'away_score': 24,
            'status': 'live',
            'period': 'Q3',
            'time_remaining': '8:42',
        }

        if app.renderer:
            app.renderer.draw_game(demo_game)
            app.display.show()

        return {'status': 'ok', 'message': 'Showing demo live game'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def handle_demo_final(request, app):
    """Show demo final score on display."""
    try:
        # Sample final game data
        demo_game = {
            'sport': 'nfl',
            'home_team': 'MIN',
            'away_team': 'DET',
            'home_score': 24,
            'away_score': 31,
            'status': 'final',
            'period': 'FINAL',
            'time_remaining': '',
        }

        if app.renderer:
            app.renderer.draw_game(demo_game)
            app.display.show()

        return {'status': 'ok', 'message': 'Showing demo final score'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def handle_demo_upcoming(request, app):
    """Show demo upcoming games on display."""
    try:
        # Sample upcoming games
        demo_games = [
            {'sport': 'nfl', 'away_team': 'DET', 'home_team': 'MIN', 'date': 'Dec 25', 'time': '9:30 PM'},
            {'sport': 'nba', 'away_team': 'DET', 'home_team': 'CHI', 'date': 'Dec 27', 'time': '8:00 PM'},
            {'sport': 'nhl', 'away_team': 'DET', 'home_team': 'BOS', 'date': 'Dec 28', 'time': '7:00 PM'},
        ]

        if app.renderer:
            app.renderer.draw_upcoming_games(demo_games)
            app.display.show()

        return {'status': 'ok', 'message': 'Showing demo upcoming games'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def handle_demo_reset(request, app):
    """Reset display to normal operation."""
    try:
        # Trigger a fresh data fetch and display update
        app.check_scores()
        app.update_display()

        return {'status': 'ok', 'message': 'Display reset to live data'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

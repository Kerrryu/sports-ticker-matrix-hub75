"""
Web Routes for OTA Updates

Adds update management endpoints to the web interface:
- GET /api/update/check - Check for updates
- POST /api/update/install - Install available update
- POST /api/update/rollback - Rollback to previous version
- GET /api/update/history - View update history
- GET /api/update/status - Current update status
"""

import json

try:
    import os
    OS_AVAILABLE = True
except ImportError:
    OS_AVAILABLE = False


class UpdateRoutes:
    """Web routes for update management."""

    def __init__(self, updater):
        """
        Initialize update routes.

        Args:
            updater: OTAUpdater instance
        """
        self.updater = updater
        self.update_in_progress = False

    def register(self, server):
        """
        Register routes with web server.

        Args:
            server: WebServer instance
        """
        server.add_route('/api/update/check', self.handle_check_update, 'GET')
        server.add_route('/api/update/install', self.handle_install_update, 'POST')
        server.add_route('/api/update/rollback', self.handle_rollback, 'POST')
        server.add_route('/api/update/history', self.handle_update_history, 'GET')
        server.add_route('/api/update/status', self.handle_update_status, 'GET')

    def handle_check_update(self, request):
        """
        Check for available updates.

        Response:
            {
                "update_available": bool,
                "current_version": str,
                "latest_version": str,
                "changelog": str,
                "breaking_changes": bool,
                "size_bytes": int
            }
        """
        try:
            update_available = self.updater.check_for_update()

            response = {
                "update_available": update_available,
                "current_version": self.updater.current_version,
                "latest_version": self.updater.latest_version if update_available else self.updater.current_version,
                "changelog": self.updater.get_changelog() if update_available else "",
                "breaking_changes": self.updater.is_breaking_change() if update_available else False,
                "size_bytes": self.updater.update_info.get('size_bytes', 0) if update_available and self.updater.update_info else 0
            }

            return ('application/json', json.dumps(response))

        except Exception as e:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': f"Update check failed: {e}"
            }))

    def handle_install_update(self, request):
        """
        Install available update.

        Response:
            {
                "status": "installing" | "error",
                "message": str
            }
        """
        if self.update_in_progress:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': 'Update already in progress'
            }))

        if not self.updater.update_info:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': 'No update available. Check for updates first.'
            }))

        try:
            self.update_in_progress = True

            # Start update flow
            success = self.updater.full_update_flow()

            if success:
                return ('application/json', json.dumps({
                    'status': 'installing',
                    'message': 'Update installing. Device will restart shortly.'
                }))
            else:
                self.update_in_progress = False
                return ('application/json', json.dumps({
                    'status': 'error',
                    'message': 'Update installation failed'
                }))

        except Exception as e:
            self.update_in_progress = False
            return ('application/json', json.dumps({
                'status': 'error',
                'message': f'Installation error: {e}'
            }))

    def handle_rollback(self, request):
        """
        Rollback to previous version.

        Response:
            {
                "status": "success" | "error",
                "message": str
            }
        """
        try:
            success = self.updater.rollback()

            if success:
                # Restart after rollback
                self.updater.restart_device()

                return ('application/json', json.dumps({
                    'status': 'success',
                    'message': 'Rolling back. Device will restart shortly.'
                }))
            else:
                return ('application/json', json.dumps({
                    'status': 'error',
                    'message': 'Rollback failed. No backup available?'
                }))

        except Exception as e:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': f'Rollback error: {e}'
            }))

    def handle_update_history(self, request):
        """
        Get update history.

        Response:
            {
                "history": [
                    {
                        "timestamp": int,
                        "from_version": str,
                        "to_version": str,
                        "status": str,
                        "error": str | null
                    }
                ]
            }
        """
        try:
            history = []

            # Read log file
            try:
                with open('/logs/ota_update.log', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                history.append(entry)
                            except:
                                pass
            except:
                pass  # Log file might not exist

            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

            # Limit to last 20 entries
            history = history[:20]

            return ('application/json', json.dumps({'history': history}))

        except Exception as e:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': f'Error reading history: {e}'
            }))

    def handle_update_status(self, request):
        """
        Get current update status.

        Response:
            {
                "current_version": str,
                "update_in_progress": bool,
                "auto_updates": bool,
                "uptime_seconds": int
            }
        """
        try:
            status = self.updater.get_status()
            status['update_in_progress'] = self.update_in_progress

            return ('application/json', json.dumps(status))

        except Exception as e:
            return ('application/json', json.dumps({
                'status': 'error',
                'message': f'Status error: {e}'
            }))


# HTML Template for Update Interface
UPDATE_PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Updates - Sports Ticker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a2e;
            color: #eee;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #00d4ff; }
        h2 { color: #00d4ff; font-size: 1.2em; margin-top: 30px; }
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .version {
            font-size: 24px;
            font-weight: bold;
            color: #00d4ff;
        }
        .changelog {
            background: #0f3460;
            border-left: 4px solid #00ff88;
            padding: 15px;
            margin: 15px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }
        button {
            background: #00d4ff;
            color: #1a1a2e;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
            margin-top: 10px;
        }
        button:hover { background: #00b8e6; }
        button:disabled { background: #666; cursor: not-allowed; }
        button.danger { background: #e94560; }
        button.danger:hover { background: #d63850; }
        button.secondary { background: #0f3460; color: #00d4ff; }
        .status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
        }
        .status.success { background: #00ff8833; color: #00ff88; }
        .status.failed { background: #e9456033; color: #e94560; }
        .status.rolled_back { background: #ffc10733; color: #ffc107; }
        .history-entry {
            border-bottom: 1px solid #0f3460;
            padding: 15px 0;
        }
        .history-entry:last-child { border-bottom: none; }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading.active { display: block; }
        .spinner {
            border: 4px solid #0f3460;
            border-top: 4px solid #00d4ff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .warning {
            background: #ffc10722;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            color: #ffc107;
        }
        .nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .nav a {
            background: #0f3460;
            color: #00d4ff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
        }
        .nav a:hover { background: #00d4ff; color: #1a1a2e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Software Updates</h1>
        <nav class="nav">
            <a href="/">Home</a>
            <a href="/teams">Teams</a>
            <a href="/settings">Settings</a>
        </nav>

        <div class="card">
            <strong>Current Version:</strong>
            <span class="version" id="currentVersion">Loading...</span>
        </div>

        <div class="card" id="updateCard" style="display:none;">
            <h2>Update Available</h2>
            <div>
                <strong>New Version:</strong>
                <span class="version" id="latestVersion"></span>
            </div>
            <div id="breakingWarning" class="warning" style="display:none;">
                Warning: This update includes breaking changes.
            </div>
            <div class="changelog" id="changelog"></div>
            <div>
                <strong>Download Size:</strong> <span id="downloadSize"></span>
            </div>
            <div style="margin-top: 20px;">
                <button onclick="installUpdate()" id="installBtn">Install Update</button>
                <button onclick="checkForUpdates()" class="secondary">Check Again</button>
            </div>
        </div>

        <div class="card" id="noUpdateCard" style="display:none;">
            <p>You're running the latest version</p>
            <button onclick="checkForUpdates()" class="secondary">Check for Updates</button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p id="loadingText">Checking for updates...</p>
        </div>

        <div class="card">
            <h2>Actions</h2>
            <button onclick="rollback()" class="danger">Rollback to Previous Version</button>
            <button onclick="showHistory()" class="secondary">View Update History</button>
        </div>

        <div class="card" id="historyCard" style="display:none;">
            <h2>Update History</h2>
            <div id="historyList"></div>
        </div>
    </div>

    <script>
        function setLoading(active, text) {
            document.getElementById('loading').className = active ? 'loading active' : 'loading';
            document.getElementById('loadingText').textContent = text || 'Loading...';
        }

        async function checkForUpdates() {
            setLoading(true, 'Checking for updates...');
            document.getElementById('updateCard').style.display = 'none';
            document.getElementById('noUpdateCard').style.display = 'none';

            try {
                const response = await fetch('/api/update/check');
                const data = await response.json();

                document.getElementById('currentVersion').textContent = data.current_version;

                if (data.update_available) {
                    document.getElementById('latestVersion').textContent = data.latest_version;
                    document.getElementById('changelog').textContent = data.changelog || 'No changelog';
                    document.getElementById('downloadSize').textContent = formatBytes(data.size_bytes);
                    document.getElementById('breakingWarning').style.display = data.breaking_changes ? 'block' : 'none';
                    document.getElementById('updateCard').style.display = 'block';
                } else {
                    document.getElementById('noUpdateCard').style.display = 'block';
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                setLoading(false);
            }
        }

        async function installUpdate() {
            if (!confirm('Install update? Device will restart.')) return;

            setLoading(true, 'Installing update...');
            document.getElementById('installBtn').disabled = true;

            try {
                const response = await fetch('/api/update/install', { method: 'POST' });
                const data = await response.json();

                if (data.status === 'installing') {
                    alert('Update installing. Device will restart.');
                    setLoading(true, 'Restarting...');
                } else {
                    alert('Failed: ' + data.message);
                    setLoading(false);
                    document.getElementById('installBtn').disabled = false;
                }
            } catch (error) {
                alert('Error: ' + error.message);
                setLoading(false);
                document.getElementById('installBtn').disabled = false;
            }
        }

        async function rollback() {
            if (!confirm('Rollback to previous version? Device will restart.')) return;

            setLoading(true, 'Rolling back...');

            try {
                const response = await fetch('/api/update/rollback', { method: 'POST' });
                const data = await response.json();

                if (data.status === 'success') {
                    alert('Rolling back. Device will restart.');
                } else {
                    alert('Failed: ' + data.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                setLoading(false);
            }
        }

        async function showHistory() {
            setLoading(true, 'Loading history...');

            try {
                const response = await fetch('/api/update/history');
                const data = await response.json();

                const list = document.getElementById('historyList');
                list.innerHTML = data.history.length === 0
                    ? '<p>No update history</p>'
                    : data.history.map(e => `
                        <div class="history-entry">
                            <strong>${e.from_version} → ${e.to_version}</strong><br>
                            <span class="status ${e.status}">${e.status}</span>
                            <span style="color:#888">${new Date(e.timestamp * 1000).toLocaleString()}</span>
                            ${e.error ? '<br><span style="color:#e94560">' + e.error + '</span>' : ''}
                        </div>
                    `).join('');

                document.getElementById('historyCard').style.display = 'block';
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                setLoading(false);
            }
        }

        function formatBytes(bytes) {
            if (!bytes) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 10) / 10 + ' ' + sizes[i];
        }

        checkForUpdates();
    </script>
</body>
</html>"""


# Test when run directly
if __name__ == '__main__':
    print("OTA Routes Test")
    print("=" * 40)
    print("Routes module loaded successfully")
    print("Available endpoints:")
    print("  GET  /api/update/check")
    print("  POST /api/update/install")
    print("  POST /api/update/rollback")
    print("  GET  /api/update/history")
    print("  GET  /api/update/status")

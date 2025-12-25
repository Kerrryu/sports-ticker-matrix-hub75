"""
Sports Ticker - Main Application

A MicroPython-based sports score display for Raspberry Pi Pico 2W
with 64x64 RGB LED Matrix. Displays live scores for NFL, NBA, MLB, NHL.

Features:
- Live score display with team colors
- Web-based configuration interface
- Over-the-air (OTA) updates
- Automatic WiFi reconnection
- Multiple sports support

Hardware:
- Raspberry Pi Pico 2W
- 64x64 RGB LED Matrix (HUB75)
- 5V/4A Power Supply

Usage:
    Upload to Pico, power on, connect to web interface at displayed IP.
"""

import gc
import time
import machine

# Version info
__version__ = "1.0.0"

# Constants
UPDATE_INTERVAL = 120  # seconds between API checks
WIFI_RETRY_INTERVAL = 30  # seconds between WiFi reconnect attempts
BOOT_SUCCESS_DELAY = 300  # seconds before marking boot successful (5 min)


class SportsTicker:
    """Main application class."""

    def __init__(self):
        """Initialize all components."""
        print(f"Sports Ticker v{__version__}")
        print("-" * 40)

        # Initialize components (lazy load to save memory)
        self.display = None
        self.wifi = None
        self.api = None
        self.web_server = None
        self.config = None
        self.ota = None

        # State
        self.running = False
        self.last_api_check = 0
        self.current_games = []
        self.upcoming_games = []  # For display when no active games
        self.boot_time = time.time()
        self.boot_success_marked = False

    def init_display(self):
        """Initialize LED matrix display."""
        print("Initializing display...")
        try:
            from src.display import HUB75Display, Renderer
            self.display = HUB75Display(width=64, height=64)
            self.renderer = Renderer(self.display)

            # Hardware driver handles refresh automatically via PIO+DMA
            # No need to call start() - it's always running

            print("Display initialized (hardware accelerated)")
            return True
        except ImportError:
            # Fall back to simulator for development
            print("Hardware not available, using simulator")
            from src.display.simulator import DisplaySimulator
            self.display = DisplaySimulator(64, 64)
            self.renderer = None
            return True
        except Exception as e:
            print(f"Display init error: {e}")
            return False

    def init_wifi(self):
        """Initialize WiFi connection."""
        print("Initializing WiFi...")
        try:
            from src.utils.network import NetworkManager
            self.wifi = NetworkManager()

            # Load credentials
            try:
                from secrets import WIFI_SSID, WIFI_PASSWORD
                connected = self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
                if connected:
                    ip = self.wifi.ip_address
                    print(f"WiFi connected: {ip}")
                    self._show_ip(ip)
                    return True
                else:
                    print("WiFi connection failed")
                    return False
            except ImportError:
                print("No secrets.py found - WiFi credentials needed")
                self._show_message("No WiFi Config")
                return False

        except Exception as e:
            print(f"WiFi init error: {e}")
            return False

    def init_config(self):
        """Load configuration."""
        print("Loading configuration...")
        try:
            from src.utils.config import ConfigManager
            self.config = ConfigManager()
            self.config.load()
            print(f"Config loaded: {len(self.config.get('teams', []))} teams configured")
            return True
        except Exception as e:
            print(f"Config error: {e}")
            return False

    def init_api(self):
        """Initialize sports API client."""
        print("Initializing API client...")
        try:
            from src.api import ESPNClient

            # Get proxy URL from config if available
            proxy_url = None
            if self.config:
                proxy_url = self.config.get('proxy_url', '')

            self.api = ESPNClient(proxy_url=proxy_url if proxy_url else None)

            if proxy_url:
                print(f"API client ready (using proxy)")
            else:
                print("API client ready (direct ESPN - may have memory issues)")
            return True
        except Exception as e:
            print(f"API init error: {e}")
            return False

    def init_web_server(self):
        """Initialize web configuration server."""
        print("Starting web server...")
        try:
            from src.web import WebServer, setup_routes
            self.web_server = WebServer(port=80)
            setup_routes(self.web_server, self)
            self.web_server.start()
            print(f"Web server started on port 80")
            return True
        except Exception as e:
            print(f"Web server error: {e}")
            return False

    def init_ota(self):
        """Initialize OTA update system."""
        print("Initializing OTA updater...")
        try:
            from src.ota import OTAUpdater
            update_url = self.config.get('update_url', '') if self.config else ''
            if update_url:
                self.ota = OTAUpdater(update_url, auto_check=True)
                print("OTA updater ready")
            else:
                print("No update URL configured, OTA disabled")
            return True
        except Exception as e:
            print(f"OTA init error: {e}")
            return False

    def _show_ip(self, ip):
        """Display IP address on matrix."""
        if self.display:
            self.display.clear()
            if self.renderer:
                # Split IP into two lines to fit on 64px display
                # e.g., "192.168.50.123" -> "192.168." and "50.123"
                parts = ip.split('.')
                if len(parts) == 4:
                    line1 = f"{parts[0]}.{parts[1]}."
                    line2 = f"{parts[2]}.{parts[3]}"
                else:
                    line1 = ip[:8]
                    line2 = ip[8:]

                self.renderer.draw_text(2, 20, "WiFi IP:", (100, 100, 100))
                self.renderer.draw_text(2, 32, line1, (255, 255, 255))
                self.renderer.draw_text(2, 44, line2, (255, 255, 255))
            self.display.show()
            time.sleep(5)  # Show IP for 5 seconds

    def _show_message(self, message):
        """Display message on matrix."""
        if self.display:
            self.display.clear()
            if self.renderer:
                self.renderer.draw_text(5, 30, message, (255, 255, 0))
            self.display.show()

    def startup(self):
        """Run startup sequence."""
        print("\n" + "=" * 40)
        print("STARTUP SEQUENCE")
        print("=" * 40)

        # Initialize in order
        steps = [
            ("Display", self.init_display),
            ("Config", self.init_config),
            ("WiFi", self.init_wifi),
            ("API", self.init_api),
            ("Web Server", self.init_web_server),
            ("OTA", self.init_ota),
        ]

        for name, init_func in steps:
            if not init_func():
                print(f"WARNING: {name} initialization failed")
            gc.collect()  # Free memory after each init

        print("\n" + "=" * 40)
        print("STARTUP COMPLETE")
        print(f"Free memory: {gc.mem_free()} bytes")
        print("=" * 40 + "\n")

        return True

    def check_scores(self):
        """Fetch latest scores from API."""
        if not self.api or not self.config:
            return

        teams = self.config.get('teams', [])
        if not teams:
            return

        try:
            # Use the unified get_all_games method (uses proxy if configured)
            result = self.api.get_all_games(teams)

            self.current_games = result.get('active', [])
            self.upcoming_games = result.get('upcoming', [])

            if self.current_games:
                print(f"Found {len(self.current_games)} active games")
            elif self.upcoming_games:
                print(f"No active games, {len(self.upcoming_games)} upcoming")
            else:
                print("No games found")

        except Exception as e:
            print(f"Score check error: {e}")
        finally:
            gc.collect()

    def update_display(self):
        """Update LED matrix with current data."""
        if not self.display:
            return

        try:
            if self.current_games:
                # Show first active game (TODO: rotate through games)
                game = self.current_games[0]
                if self.renderer:
                    self.renderer.draw_game(game)
            elif self.upcoming_games:
                # Show upcoming games when no active games
                if self.renderer:
                    self.renderer.draw_upcoming_games(self.upcoming_games)
            else:
                # Idle display
                if self.renderer:
                    self.renderer.draw_idle()

            # Flip the double buffer to display new content
            self.display.show()

        except Exception as e:
            print(f"Display update error: {e}")

    def check_wifi(self):
        """Check and reconnect WiFi if needed."""
        if self.wifi and not self.wifi.is_connected:
            print("WiFi disconnected, attempting reconnect...")
            try:
                from secrets import WIFI_SSID, WIFI_PASSWORD
                self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            except:
                pass

    def mark_boot_successful(self):
        """Mark boot as successful after stable runtime."""
        if not self.boot_success_marked:
            uptime = time.time() - self.boot_time
            if uptime >= BOOT_SUCCESS_DELAY:
                print("Boot marked successful (5 min uptime)")
                if self.ota:
                    self.ota.mark_boot_successful()
                self.boot_success_marked = True

    def run(self):
        """Main application loop."""
        self.running = True
        print("Entering main loop...")

        # Fetch data immediately on startup, then update display
        self.check_scores()
        self.last_api_check = time.time()
        self.update_display()
        print("Initial content drawn with game data")

        while self.running:
            try:
                now = time.time()

                # Check scores periodically - only redraw when new data arrives
                if now - self.last_api_check >= UPDATE_INTERVAL:
                    old_active = self.current_games.copy() if self.current_games else []
                    old_upcoming = self.upcoming_games.copy() if self.upcoming_games else []
                    self.check_scores()
                    self.last_api_check = now

                    # Redraw if active OR upcoming games changed
                    if self.current_games != old_active or self.upcoming_games != old_upcoming:
                        self.update_display()
                        print("Display updated with new data")

                # Handle web requests (non-blocking)
                if self.web_server:
                    self.web_server.handle_request()

                # Periodic maintenance
                self.check_wifi()
                self.mark_boot_successful()

                # Sleep - hardware refresh runs independently on core 1
                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\nShutdown requested")
                self.running = False
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(1)

        self.shutdown()

    def shutdown(self):
        """Clean shutdown."""
        print("\nShutting down...")
        self.running = False

        if self.web_server:
            self.web_server.stop()

        if self.display:
            self.display.clear()
            # Stop background refresh thread
            self.display.stop()

        print("Shutdown complete")


# Entry point
if __name__ == '__main__':
    app = SportsTicker()

    if app.startup():
        app.run()
    else:
        print("Startup failed!")
        # Show error on display if possible
        if app.display:
            app._show_message("STARTUP FAILED")

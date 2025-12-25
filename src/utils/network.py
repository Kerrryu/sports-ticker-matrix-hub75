"""
Network Manager

Handles WiFi connectivity for Raspberry Pi Pico 2W.
Provides connection management, status monitoring, and auto-reconnect.

Usage:
    from utils.network import NetworkManager

    wifi = NetworkManager()
    wifi.connect('MyNetwork', 'password')
    print(wifi.ip_address)
"""

import time
import gc

# Try to import network module (only available on Pico)
try:
    import network
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False


class NetworkManager:
    """Manages WiFi connectivity."""

    # Connection states
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    STATE_ERROR = 3

    def __init__(self):
        """Initialize network manager."""
        self._wlan = None
        self._ssid = None
        self._password = None
        self._state = self.STATE_DISCONNECTED
        self._last_check = 0
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._check_interval = 30  # seconds

        if NETWORK_AVAILABLE:
            self._wlan = network.WLAN(network.STA_IF)

    def connect(self, ssid, password, timeout=30):
        """
        Connect to WiFi network.

        Args:
            ssid: Network name
            password: Network password
            timeout: Connection timeout in seconds

        Returns:
            True if connected, False otherwise
        """
        if not NETWORK_AVAILABLE:
            print("Network: Not available (running on PC?)")
            self._state = self.STATE_ERROR
            return False

        self._ssid = ssid
        self._password = password
        self._state = self.STATE_CONNECTING
        self._reconnect_attempts = 0

        print(f"Network: Connecting to {ssid}...")

        # Activate interface
        self._wlan.active(True)

        # Disconnect if already connected
        if self._wlan.isconnected():
            self._wlan.disconnect()
            time.sleep(1)

        # Connect
        self._wlan.connect(ssid, password)

        # Wait for connection
        start_time = time.time()
        while not self._wlan.isconnected():
            if time.time() - start_time > timeout:
                print("Network: Connection timeout")
                self._state = self.STATE_ERROR
                return False

            status = self._wlan.status()
            if status == network.STAT_WRONG_PASSWORD:
                print("Network: Wrong password")
                self._state = self.STATE_ERROR
                return False
            elif status == network.STAT_NO_AP_FOUND:
                print("Network: Network not found")
                self._state = self.STATE_ERROR
                return False
            elif status < 0:
                print(f"Network: Connection failed (status={status})")
                self._state = self.STATE_ERROR
                return False

            time.sleep(0.5)

        self._state = self.STATE_CONNECTED
        self._last_check = time.time()
        gc.collect()

        print(f"Network: Connected! IP: {self.ip_address}")
        return True

    def disconnect(self):
        """Disconnect from WiFi network."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return

        if self._wlan.isconnected():
            self._wlan.disconnect()
        self._wlan.active(False)
        self._state = self.STATE_DISCONNECTED
        print("Network: Disconnected")

    @property
    def is_connected(self):
        """Check if connected to WiFi."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return False
        return self._wlan.isconnected()

    @property
    def ip_address(self):
        """Get current IP address."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return "0.0.0.0"

        if self._wlan.isconnected():
            return self._wlan.ifconfig()[0]
        return "0.0.0.0"

    @property
    def subnet_mask(self):
        """Get subnet mask."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return "0.0.0.0"

        if self._wlan.isconnected():
            return self._wlan.ifconfig()[1]
        return "0.0.0.0"

    @property
    def gateway(self):
        """Get gateway address."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return "0.0.0.0"

        if self._wlan.isconnected():
            return self._wlan.ifconfig()[2]
        return "0.0.0.0"

    @property
    def dns_server(self):
        """Get DNS server address."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return "0.0.0.0"

        if self._wlan.isconnected():
            return self._wlan.ifconfig()[3]
        return "0.0.0.0"

    @property
    def mac_address(self):
        """Get MAC address as string."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return "00:00:00:00:00:00"

        mac = self._wlan.config('mac')
        return ':'.join('{:02x}'.format(b) for b in mac)

    @property
    def rssi(self):
        """Get signal strength (RSSI)."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return -100

        try:
            return self._wlan.status('rssi')
        except:
            return -100

    @property
    def state(self):
        """Get connection state."""
        return self._state

    @property
    def state_string(self):
        """Get connection state as string."""
        states = {
            self.STATE_DISCONNECTED: 'Disconnected',
            self.STATE_CONNECTING: 'Connecting',
            self.STATE_CONNECTED: 'Connected',
            self.STATE_ERROR: 'Error'
        }
        return states.get(self._state, 'Unknown')

    def check_connection(self):
        """
        Check connection status and reconnect if needed.

        Call this periodically from main loop.

        Returns:
            True if connected, False if disconnected/reconnecting
        """
        if not NETWORK_AVAILABLE or not self._wlan:
            return False

        current_time = time.time()

        # Only check periodically
        if current_time - self._last_check < self._check_interval:
            return self.is_connected

        self._last_check = current_time

        if self._wlan.isconnected():
            self._state = self.STATE_CONNECTED
            self._reconnect_attempts = 0
            return True

        # Not connected, try to reconnect
        return self._attempt_reconnect()

    def _attempt_reconnect(self):
        """Attempt to reconnect to WiFi."""
        if not self._ssid or not self._password:
            return False

        if self._reconnect_attempts >= self._max_reconnect_attempts:
            print("Network: Max reconnect attempts reached")
            self._state = self.STATE_ERROR
            return False

        self._reconnect_attempts += 1
        print(f"Network: Reconnect attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}")

        return self.connect(self._ssid, self._password, timeout=15)

    def reset_reconnect_counter(self):
        """Reset the reconnect attempt counter."""
        self._reconnect_attempts = 0

    def scan(self):
        """
        Scan for available networks.

        Returns:
            List of (ssid, bssid, channel, rssi, security, hidden) tuples
        """
        if not NETWORK_AVAILABLE or not self._wlan:
            return []

        was_active = self._wlan.active()
        if not was_active:
            self._wlan.active(True)
            time.sleep(0.5)

        try:
            networks = self._wlan.scan()
            return networks
        except:
            return []
        finally:
            if not was_active:
                self._wlan.active(False)

    def get_network_list(self):
        """
        Get list of available networks as dicts.

        Returns:
            List of network info dicts
        """
        raw_networks = self.scan()
        networks = []

        for net in raw_networks:
            ssid = net[0].decode('utf-8') if isinstance(net[0], bytes) else net[0]
            networks.append({
                'ssid': ssid,
                'rssi': net[3],
                'channel': net[2],
                'security': 'Open' if net[4] == 0 else 'Secured'
            })

        # Sort by signal strength
        networks.sort(key=lambda x: x['rssi'], reverse=True)
        return networks

    def get_status(self):
        """
        Get complete network status.

        Returns:
            Dict with network status info
        """
        return {
            'connected': self.is_connected,
            'state': self.state_string,
            'ssid': self._ssid or 'None',
            'ip': self.ip_address,
            'subnet': self.subnet_mask,
            'gateway': self.gateway,
            'dns': self.dns_server,
            'mac': self.mac_address,
            'rssi': self.rssi,
            'reconnect_attempts': self._reconnect_attempts,
        }

    def set_hostname(self, hostname):
        """Set device hostname."""
        if not NETWORK_AVAILABLE or not self._wlan:
            return

        try:
            # Note: May not work on all MicroPython builds
            network.hostname(hostname)
        except:
            pass


# Convenience function to load credentials from secrets.py
def load_credentials():
    """
    Load WiFi credentials from secrets.py.

    Returns:
        Tuple of (ssid, password) or (None, None) if not found
    """
    try:
        import secrets
        return (
            getattr(secrets, 'WIFI_SSID', None),
            getattr(secrets, 'WIFI_PASSWORD', None)
        )
    except ImportError:
        print("Network: secrets.py not found")
        return (None, None)


# Singleton instance
_network = None


def get_network():
    """Get global network manager instance."""
    global _network
    if _network is None:
        _network = NetworkManager()
    return _network


# Test when run directly
if __name__ == '__main__':
    print("Network Manager Test")
    print("=" * 40)

    wifi = NetworkManager()

    if NETWORK_AVAILABLE:
        # Try to load credentials
        ssid, password = load_credentials()

        if ssid and password:
            print(f"Connecting to {ssid}...")
            if wifi.connect(ssid, password):
                print("\nConnection successful!")
                status = wifi.get_status()
                for key, value in status.items():
                    print(f"  {key}: {value}")
        else:
            print("No credentials found in secrets.py")
            print("\nScanning for networks...")
            networks = wifi.get_network_list()
            for net in networks[:10]:
                print(f"  {net['ssid']}: {net['rssi']} dBm ({net['security']})")
    else:
        print("Network module not available (running on PC)")
        print("Status:", wifi.get_status())

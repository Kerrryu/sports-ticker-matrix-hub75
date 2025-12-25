"""
MicroPython HTTP Web Server

Lightweight HTTP server for configuration web interface.
Handles GET and POST requests with JSON API support.

Usage:
    from web.server import WebServer

    server = WebServer(port=80)
    server.route('/', handler_func)
    server.start()

    # In main loop:
    server.handle_request()
"""

import socket
import json
import gc


class WebServer:
    """Simple HTTP server for MicroPython."""

    def __init__(self, port=80):
        """
        Initialize web server.

        Args:
            port: Port to listen on (default 80)
        """
        self.port = port
        self.routes = {}
        self.socket = None
        self.running = False

    def route(self, path, handler, methods=None):
        """
        Register a route handler.

        Args:
            path: URL path (e.g., '/', '/api/config')
            handler: Function to handle request
            methods: List of methods ['GET', 'POST'] (default all)
        """
        if methods is None:
            methods = ['GET', 'POST', 'PUT', 'DELETE']

        self.routes[path] = {
            'handler': handler,
            'methods': [m.upper() for m in methods]
        }

    def start(self):
        """Start the web server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.socket.setblocking(False)
            self.running = True
            print(f"Web server started on port {self.port}")
            return True
        except Exception as e:
            print(f"Server start error: {e}")
            return False

    def stop(self):
        """Stop the web server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        print("Web server stopped")

    def handle_request(self):
        """
        Handle one incoming request (non-blocking).

        Call this repeatedly in main loop.
        """
        if not self.socket or not self.running:
            return

        try:
            client, addr = self.socket.accept()
            client.settimeout(2.0)  # Reduced timeout

            try:
                # Read request
                request = self._read_request(client)
                if request:
                    print(f"[HTTP] {request['method']} {request['path']}")
                    # Parse and handle
                    response = self._process_request(request)
                    # Send response
                    self._send_response(client, response)
            finally:
                client.close()
                gc.collect()

        except OSError:
            # No connection waiting (non-blocking)
            pass
        except Exception as e:
            print(f"Request error: {e}")

    def _read_request(self, client):
        """Read and parse HTTP request."""
        try:
            data = b''
            # Read headers
            while True:
                chunk = client.recv(1024)
                if not chunk:
                    break
                data += chunk
                # Check for end of headers
                if b'\r\n\r\n' in data:
                    break

            if not data:
                return None

            # Parse headers to get Content-Length
            header_end = data.find(b'\r\n\r\n')
            headers_raw = data[:header_end].decode('utf-8')
            body_start = data[header_end + 4:]

            # Check for Content-Length
            content_length = 0
            for line in headers_raw.split('\r\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())
                    break

            # Read remaining body if needed
            while len(body_start) < content_length:
                chunk = client.recv(1024)
                if not chunk:
                    break
                body_start += chunk

            # Combine for parsing
            full_data = headers_raw + '\r\n\r\n' + body_start.decode('utf-8')
            return self._parse_request(full_data)

        except Exception as e:
            print(f"Read error: {e}")
            return None

    def _parse_request(self, data):
        """Parse HTTP request string."""
        lines = data.split('\r\n')
        if not lines:
            return None

        # Parse request line
        parts = lines[0].split(' ')
        if len(parts) < 2:
            return None

        method = parts[0].upper()
        full_path = parts[1]

        # Split path and query string
        if '?' in full_path:
            path, query_string = full_path.split('?', 1)
        else:
            path = full_path
            query_string = ''

        # Parse headers
        headers = {}
        body_start = 0
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Get body if present
        body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''

        return {
            'method': method,
            'path': path,
            'query_string': query_string,
            'headers': headers,
            'body': body,
        }

    def _process_request(self, request):
        """Process request and generate response."""
        path = request['path']
        method = request['method']

        # Find matching route
        route_info = self.routes.get(path)

        if not route_info:
            # Check for API routes with wildcards
            for route_path, info in self.routes.items():
                if route_path.endswith('/*'):
                    prefix = route_path[:-2]
                    if path.startswith(prefix):
                        route_info = info
                        break

        if not route_info:
            return self._error_response(404, 'Not Found')

        if method not in route_info['methods']:
            return self._error_response(405, 'Method Not Allowed')

        try:
            handler = route_info['handler']
            result = handler(request)

            # Handler can return dict, string, or tuple
            if isinstance(result, dict):
                return self._json_response(result)
            elif isinstance(result, tuple):
                return result
            else:
                return self._html_response(str(result))

        except Exception as e:
            print(f"Handler error: {e}")
            return self._error_response(500, f'Internal Error: {e}')

    def _send_response(self, client, response):
        """Send HTTP response to client."""
        status, headers, body = response

        # Encode body to bytes for accurate Content-Length
        if isinstance(body, str):
            body_bytes = body.encode('utf-8')
        else:
            body_bytes = body

        # Update Content-Length with actual byte length
        headers['Content-Length'] = str(len(body_bytes))

        # Build and send headers
        status_line = f"HTTP/1.1 {status}\r\n"
        header_lines = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())
        header_data = f"{status_line}{header_lines}\r\n"

        try:
            # Use sendall to ensure complete transmission
            client.sendall(header_data.encode('utf-8'))
            client.sendall(body_bytes)
        except Exception as e:
            print(f"Send error: {e}")

    def _html_response(self, html, status=200):
        """Create HTML response tuple."""
        headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Connection': 'close',
        }
        return (f"{status} OK", headers, html)

    def _json_response(self, data, status=200):
        """Create JSON response tuple."""
        body = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'close',
        }
        status_text = 'OK' if status == 200 else 'Error'
        return (f"{status} {status_text}", headers, body)

    def _error_response(self, code, message):
        """Create error response tuple."""
        body = json.dumps({'error': message})
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'close',
        }
        return (f"{code} {message}", headers, body)


# Test when run directly (on desktop Python)
if __name__ == '__main__':
    print("Web Server Test")
    print("=" * 40)

    server = WebServer(port=8080)

    def home_handler(request):
        return "<h1>Sports Ticker</h1><p>Web server working!</p>"

    def api_handler(request):
        return {'status': 'ok', 'method': request['method']}

    server.route('/', home_handler, ['GET'])
    server.route('/api/status', api_handler, ['GET', 'POST'])

    print("Starting server on port 8080...")
    print("Press Ctrl+C to stop")

    if server.start():
        try:
            while True:
                server.handle_request()
        except KeyboardInterrupt:
            print("\nStopping...")
            server.stop()

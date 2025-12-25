"""
Display Simulator for Development Without Hardware

This module provides a text-based simulator for the 64x64 LED matrix
when you don't have the physical hardware available. Use this for:
- Developing rendering logic
- Testing layouts
- Debugging display code
- CI/CD without hardware

Usage:
    from display.simulator import DisplaySimulator

    display = DisplaySimulator(64, 64)
    display.set_pixel(10, 10, 255, 0, 0)  # Red pixel
    display.show()  # Print to console
"""


class DisplaySimulator:
    """Simulates 64x64 LED matrix in terminal."""

    def __init__(self, width=64, height=64):
        """
        Initialize simulator.

        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.framebuffer = bytearray(width * height * 3)
        self.brightness = 255

    def set_pixel(self, x, y, r, g, b):
        """
        Set pixel color.

        Args:
            x: X coordinate (0-63)
            y: Y coordinate (0-63)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return  # Out of bounds

        # Apply brightness
        r = int(r * self.brightness / 255)
        g = int(g * self.brightness / 255)
        b = int(b * self.brightness / 255)

        offset = (y * self.width + x) * 3
        self.framebuffer[offset] = r
        self.framebuffer[offset + 1] = g
        self.framebuffer[offset + 2] = b

    def get_pixel(self, x, y):
        """Get pixel color at coordinates."""
        offset = (y * self.width + x) * 3
        return (
            self.framebuffer[offset],
            self.framebuffer[offset + 1],
            self.framebuffer[offset + 2]
        )

    def clear(self, r=0, g=0, b=0):
        """Clear display to color."""
        for i in range(0, len(self.framebuffer), 3):
            self.framebuffer[i] = r
            self.framebuffer[i + 1] = g
            self.framebuffer[i + 2] = b

    def set_brightness(self, value):
        """Set global brightness (0-255)."""
        self.brightness = max(0, min(255, value))

    def show(self, mode='ascii'):
        """
        Display framebuffer.

        Args:
            mode: 'ascii' for terminal output, 'compact' for smaller view
        """
        if mode == 'ascii':
            self._show_ascii()
        elif mode == 'compact':
            self._show_compact()
        elif mode == 'color':
            self._show_color()

    def _show_ascii(self):
        """Show full ASCII art representation."""
        print('\n' + '=' * (self.width + 2))
        for y in range(self.height):
            row = '|'
            for x in range(self.width):
                r, g, b = self.get_pixel(x, y)
                brightness = (r + g + b) // 3

                # Map brightness to ASCII characters
                if brightness > 200:
                    char = '#'
                elif brightness > 150:
                    char = '*'
                elif brightness > 100:
                    char = '+'
                elif brightness > 50:
                    char = '.'
                else:
                    char = ' '
                row += char
            row += '|'
            print(row)
        print('=' * (self.width + 2))

    def _show_compact(self):
        """Show compact representation (useful for 64x64)."""
        print('\n' + '-' * (self.width // 2 + 2))
        for y in range(0, self.height, 2):  # Every other row
            row = '|'
            for x in range(0, self.width, 2):  # Every other column
                r1, g1, b1 = self.get_pixel(x, y)
                # Sample 2x2 block
                brightness = (r1 + g1 + b1) // 3

                if brightness > 128:
                    char = '#'
                elif brightness > 64:
                    char = '+'
                else:
                    char = ' '
                row += char
            row += '|'
            print(row)
        print('-' * (self.width // 2 + 2))

    def _show_color(self):
        """Show with ANSI color codes (terminal dependent)."""
        print('\n' + '=' * (self.width + 2))
        for y in range(self.height):
            row = '|'
            for x in range(self.width):
                r, g, b = self.get_pixel(x, y)
                # Simple ANSI color mapping
                if r > g and r > b:
                    color_code = '\033[91m'  # Red
                elif g > r and g > b:
                    color_code = '\033[92m'  # Green
                elif b > r and b > g:
                    color_code = '\033[94m'  # Blue
                elif r + g + b > 384:
                    color_code = '\033[97m'  # White
                else:
                    color_code = '\033[90m'  # Dark gray

                brightness = (r + g + b) // 3
                if brightness > 128:
                    char = '#'
                elif brightness > 0:
                    char = '+'
                else:
                    char = ' '

                row += f'{color_code}{char}\033[0m'
            row += '|'
            print(row)
        print('=' * (self.width + 2))

    def save_to_file(self, filename):
        """Save current display state to text file."""
        with open(filename, 'w') as f:
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = self.get_pixel(x, y)
                    brightness = (r + g + b) // 3
                    if brightness > 200:
                        f.write('#')
                    elif brightness > 150:
                        f.write('*')
                    elif brightness > 100:
                        f.write('+')
                    elif brightness > 50:
                        f.write('.')
                    else:
                        f.write(' ')
                f.write('\n')


# Example usage and tests
if __name__ == '__main__':
    print("Testing Display Simulator")
    print("=" * 50)

    # Create simulator
    display = DisplaySimulator(64, 64)

    # Test 1: Single pixel
    print("\nTest 1: Single bright pixel at (10, 10)")
    display.clear()
    display.set_pixel(10, 10, 255, 255, 255)
    display.show('compact')

    # Test 2: Horizontal line
    print("\nTest 2: Horizontal line across middle")
    display.clear()
    for x in range(64):
        display.set_pixel(x, 32, 255, 255, 255)
    display.show('compact')

    # Test 3: Box
    print("\nTest 3: Box outline")
    display.clear()
    for x in range(20, 44):
        display.set_pixel(x, 20, 255, 0, 0)
        display.set_pixel(x, 43, 255, 0, 0)
    for y in range(20, 44):
        display.set_pixel(20, y, 0, 255, 0)
        display.set_pixel(43, y, 0, 255, 0)
    display.show('compact')

    # Test 4: Gradient
    print("\nTest 4: Vertical brightness gradient")
    display.clear()
    for y in range(64):
        brightness = int(y * 255 / 64)
        for x in range(64):
            display.set_pixel(x, y, brightness, brightness, brightness)
    display.show('compact')

    # Test 5: Text simulation (simple)
    print("\nTest 5: Simulated text 'HI'")
    display.clear()
    # H
    for y in range(10, 20):
        display.set_pixel(10, y, 255, 255, 0)
        display.set_pixel(15, y, 255, 255, 0)
    for x in range(10, 16):
        display.set_pixel(x, 14, 255, 255, 0)
    # I
    for y in range(10, 20):
        display.set_pixel(20, y, 0, 255, 255)
    display.show('compact')

    print("\nSimulator tests complete!")
    print("\nYou can use this simulator for development until")
    print("the actual LED matrix arrives.")

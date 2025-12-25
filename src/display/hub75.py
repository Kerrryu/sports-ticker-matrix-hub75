"""
HUB75 Display Driver - High Performance Version

Uses the Pi-Pico-Hub75-Driver library for hardware-accelerated,
flicker-free display using PIO + DMA.

The display refresh runs entirely in hardware - no CPU overhead.
"""

from machine import Pin

# Try to import the optimized library
try:
    from hub75 import Hub75Driver, Hub75Display as _Hub75Display
    HAS_OPTIMIZED_DRIVER = True
except ImportError:
    HAS_OPTIMIZED_DRIVER = False
    print("WARNING: Optimized hub75 library not found!")
    print("Install with: mpremote mip install https://github.com/dgrantpete/Pi-Pico-Hub75-Driver/releases/latest/download/package.json")


def rgb_to_565(r, g, b):
    """Convert RGB888 to RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class HUB75Display:
    """
    High-performance HUB75 display wrapper.

    Uses PIO + DMA for hardware-accelerated refresh.
    After initialization, display refresh is completely CPU-free.

    Usage:
        display = HUB75Display(64, 64)
        display.set_pixel(10, 10, 255, 0, 0)  # Red pixel
        display.show()  # Update display
    """

    def __init__(self, width=64, height=64, brightness=255):
        self.width = width
        self.height = height
        self.brightness = brightness

        if not HAS_OPTIMIZED_DRIVER:
            raise RuntimeError("Optimized hub75 library not installed!")

        # Initialize the hardware driver
        # Pin configuration matches our wiring:
        # R1=0, G1=1, B1=2, R2=3, G2=4, B2=5 (consecutive from 0)
        # CLK=6, LAT=7 (consecutive from 6)
        # OE=8
        # A=9, B=10, C=11, D=12, E=13 (consecutive from 9)

        self._driver = Hub75Driver(
            address_bit_count=5,        # 5 address lines for 64-row (1/32 scan)
            shift_register_depth=64,    # Panel width
            base_data_pin=Pin(0),       # R1,G1,B1,R2,G2,B2 on GPIO 0-5
            base_clock_pin=Pin(6),      # CLK,LAT on GPIO 6-7
            output_enable_pin=Pin(8),   # OE on GPIO 8
            base_address_pin=Pin(9),    # A,B,C,D,E on GPIO 9-13
            data_frequency=20_000_000   # 20 MHz - conservative for stability
        )

        # High-level display wrapper with drawing primitives
        self._display = _Hub75Display(self._driver)

        # Clear to black
        self._display.fill(0x0000)
        self._display.show()

        print(f"HUB75 Display: {width}x{height} (Hardware accelerated, flicker-free)")

    def set_pixel(self, x, y, r, g, b):
        """Set pixel color."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        # Apply brightness
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8

        # Convert to RGB565 and set
        color = rgb_to_565(r, g, b)
        self._display.pixel(x, y, color)

    def get_pixel(self, x, y):
        """Get pixel color (returns RGB565)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        return self._display.pixel(x, y)

    def clear(self, r=0, g=0, b=0):
        """Clear display to color."""
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        color = rgb_to_565(r, g, b)
        self._display.fill(color)

    def fill(self, color):
        """Fill with RGB565 color."""
        self._display.fill(color)

    def show(self):
        """Update display with current buffer."""
        self._display.show()

    def set_brightness(self, value):
        """Set brightness 0-255."""
        self.brightness = max(0, min(255, value))

    def fill_rect(self, x, y, w, h, r, g, b):
        """Fill rectangle."""
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        color = rgb_to_565(r, g, b)
        self._display.rect(x, y, w, h, color, fill=True)

    def draw_rect(self, x, y, w, h, r, g, b, filled=False):
        """Draw rectangle."""
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        color = rgb_to_565(r, g, b)
        self._display.rect(x, y, w, h, color, fill=filled)

    def draw_line(self, x0, y0, x1, y1, r, g, b):
        """Draw line."""
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        color = rgb_to_565(r, g, b)
        self._display.line(x0, y0, x1, y1, color)

    def draw_text(self, x, y, text, r, g, b):
        """Draw text using built-in font."""
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        color = rgb_to_565(r, g, b)
        self._display.text(text, x, y, color)

    def start(self):
        """
        Start display - for API compatibility.

        With the hardware driver, refresh runs automatically
        via PIO + DMA. This method is a no-op.
        """
        pass  # Hardware refresh is always running

    def stop(self):
        """Stop display and clean up."""
        if hasattr(self, '_driver'):
            self._driver.deinit()
            print("Display stopped")

    def test_pattern(self):
        """Display RGB test pattern."""
        self.clear()

        # Red stripe
        for y in range(21):
            for x in range(self.width):
                self.set_pixel(x, y, 255, 0, 0)

        # Green stripe
        for y in range(21, 42):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 255, 0)

        # Blue stripe
        for y in range(42, 64):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 0, 255)

        self.show()


if __name__ == '__main__':
    print("HUB75 Hardware-Accelerated Display Test")

    display = HUB75Display(64, 64)
    display.test_pattern()

    print("Test pattern displayed - should be flicker-free!")
    print("Press Ctrl+C to exit")

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        display.stop()
        print("Done")

"""
HUB75 Display Driver with Background Refresh Thread

Uses the Pico's second core to continuously refresh the display
while the main core handles application logic.

Usage:
    display = HUB75Display(64, 64)
    display.start()  # Start background refresh on core 1

    # Now you can update pixels whenever - refresh happens automatically
    display.set_pixel(10, 10, 255, 0, 0)
    display.set_pixel(20, 20, 0, 255, 0)

    # Your main app runs normally
    while True:
        scores = fetch_scores()
        display.clear()
        draw_scores(display, scores)
        time.sleep(60)  # Display keeps refreshing during sleep!
"""

import _thread
from machine import Pin
import micropython
import time

# Pin definitions
PIN_R1 = 0
PIN_G1 = 1
PIN_B1 = 2
PIN_R2 = 3
PIN_G2 = 4
PIN_B2 = 5
PIN_CLK = 6
PIN_LAT = 7
PIN_OE = 8
PIN_A = 9
PIN_B = 10
PIN_C = 11
PIN_D = 12
PIN_E = 13


class HUB75Display:
    """
    HUB75 driver with automatic background refresh.

    The display refresh runs on the Pico's second core,
    leaving the main core free for application logic.
    """

    def __init__(self, width=64, height=64, brightness=255):
        self.width = width
        self.height = height
        self.brightness = brightness

        # Framebuffer
        self.framebuffer = bytearray(width * height * 3)

        # Thread control
        self._running = False
        self._lock = _thread.allocate_lock()

        # Initialize pins
        self._init_pins()

        print(f"HUB75 Threaded Display: {width}x{height}")

    def _init_pins(self):
        """Initialize GPIO pins."""
        self.r1 = Pin(PIN_R1, Pin.OUT, value=0)
        self.g1 = Pin(PIN_G1, Pin.OUT, value=0)
        self.b1 = Pin(PIN_B1, Pin.OUT, value=0)
        self.r2 = Pin(PIN_R2, Pin.OUT, value=0)
        self.g2 = Pin(PIN_G2, Pin.OUT, value=0)
        self.b2 = Pin(PIN_B2, Pin.OUT, value=0)
        self.clk = Pin(PIN_CLK, Pin.OUT, value=0)
        self.lat = Pin(PIN_LAT, Pin.OUT, value=0)
        self.oe = Pin(PIN_OE, Pin.OUT, value=1)
        self.addr_a = Pin(PIN_A, Pin.OUT, value=0)
        self.addr_b = Pin(PIN_B, Pin.OUT, value=0)
        self.addr_c = Pin(PIN_C, Pin.OUT, value=0)
        self.addr_d = Pin(PIN_D, Pin.OUT, value=0)
        self.addr_e = Pin(PIN_E, Pin.OUT, value=0)

    def set_pixel(self, x, y, r, g, b):
        """Set pixel color (thread-safe)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8

        offset = (y * self.width + x) * 3

        # Thread-safe write
        with self._lock:
            self.framebuffer[offset] = r
            self.framebuffer[offset + 1] = g
            self.framebuffer[offset + 2] = b

    def clear(self, r=0, g=0, b=0):
        """Clear display (thread-safe)."""
        with self._lock:
            for i in range(0, len(self.framebuffer), 3):
                self.framebuffer[i] = r
                self.framebuffer[i + 1] = g
                self.framebuffer[i + 2] = b

    def set_brightness(self, value):
        """Set brightness 0-255."""
        self.brightness = max(0, min(255, value))

    def _refresh_loop(self):
        """
        Background refresh loop - runs on second core.
        This function never returns while display is running.
        """
        # Cache everything for maximum speed
        fb = self.framebuffer
        threshold = 128
        width = self.width

        r1v = self.r1.value
        g1v = self.g1.value
        b1v = self.b1.value
        r2v = self.r2.value
        g2v = self.g2.value
        b2v = self.b2.value
        clkv = self.clk.value
        latv = self.lat.value
        oev = self.oe.value
        av = self.addr_a.value
        bv = self.addr_b.value
        cv = self.addr_c.value
        dv = self.addr_d.value
        ev = self.addr_e.value

        while self._running:
            for row in range(32):
                # Disable output
                oev(1)

                # Set row address
                av(row & 1)
                bv((row >> 1) & 1)
                cv((row >> 2) & 1)
                dv((row >> 3) & 1)
                ev((row >> 4) & 1)

                # Calculate offsets
                u_base = row * width * 3
                l_base = (row + 32) * width * 3

                # Shift pixel data
                for col in range(width):
                    idx_u = u_base + col * 3
                    idx_l = l_base + col * 3

                    r1v(fb[idx_u] >= threshold)
                    g1v(fb[idx_u + 1] >= threshold)
                    b1v(fb[idx_u + 2] >= threshold)
                    r2v(fb[idx_l] >= threshold)
                    g2v(fb[idx_l + 1] >= threshold)
                    b2v(fb[idx_l + 2] >= threshold)

                    clkv(1)
                    clkv(0)

                # Latch
                latv(1)
                latv(0)

                # Enable output
                oev(0)

                # Row display time
                time.sleep_us(25)

            # End of frame - brief disable
            oev(1)

    def start(self):
        """Start background refresh on second core."""
        if self._running:
            return

        self._running = True
        _thread.start_new_thread(self._refresh_loop, ())
        print("Display refresh started on core 1")

    def stop(self):
        """Stop background refresh."""
        self._running = False
        time.sleep_ms(100)  # Let thread exit
        self.oe.value(1)  # Disable output
        print("Display refresh stopped")

    def show(self):
        """
        Manual refresh - use this if not using background thread.
        When using start(), you don't need to call this.
        """
        fb = self.framebuffer
        threshold = 128
        width = self.width

        r1v = self.r1.value
        g1v = self.g1.value
        b1v = self.b1.value
        r2v = self.r2.value
        g2v = self.g2.value
        b2v = self.b2.value
        clkv = self.clk.value
        latv = self.lat.value
        oev = self.oe.value

        for row in range(32):
            oev(1)

            self.addr_a.value(row & 1)
            self.addr_b.value((row >> 1) & 1)
            self.addr_c.value((row >> 2) & 1)
            self.addr_d.value((row >> 3) & 1)
            self.addr_e.value((row >> 4) & 1)

            u_base = row * width * 3
            l_base = (row + 32) * width * 3

            for col in range(width):
                idx_u = u_base + col * 3
                idx_l = l_base + col * 3

                r1v(fb[idx_u] >= threshold)
                g1v(fb[idx_u + 1] >= threshold)
                b1v(fb[idx_u + 2] >= threshold)
                r2v(fb[idx_l] >= threshold)
                g2v(fb[idx_l + 1] >= threshold)
                b2v(fb[idx_l + 2] >= threshold)

                clkv(1)
                clkv(0)

            latv(1)
            latv(0)
            oev(0)
            time.sleep_us(25)

        oev(1)

    def fill_rect(self, x, y, w, h, r, g, b):
        """Fill rectangle."""
        for py in range(y, min(y + h, self.height)):
            for px in range(x, min(x + w, self.width)):
                self.set_pixel(px, py, r, g, b)

    def test_pattern(self):
        """Display test pattern."""
        self.clear()
        for y in range(21):
            for x in range(self.width):
                self.set_pixel(x, y, 255, 0, 0)
        for y in range(21, 42):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 255, 0)
        for y in range(42, 64):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 0, 255)


if __name__ == '__main__':
    print("Testing threaded HUB75 display")

    display = HUB75Display(64, 64)
    display.test_pattern()

    print("Starting background refresh...")
    display.start()

    print("Main thread is free! Sleeping 10 seconds...")
    print("Display should show RGB stripes with NO flicker")
    time.sleep(10)

    display.stop()
    print("Done")

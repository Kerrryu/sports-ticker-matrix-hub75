"""
Fast HUB75 Driver using PIO for pixel data shifting.

PIO handles the fast inner loop (shifting 64 pixels per row),
Python handles row selection and timing.
"""

import rp2
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin, freq
import time
import _thread

# Boost CPU frequency for faster Python code
freq(250_000_000)  # 250MHz (max stable)

# Pin definitions
PIN_R1, PIN_G1, PIN_B1 = 0, 1, 2
PIN_R2, PIN_G2, PIN_B2 = 3, 4, 5
PIN_CLK = 6
PIN_LAT = 7
PIN_OE = 8
PIN_A, PIN_B, PIN_C, PIN_D, PIN_E = 9, 10, 11, 12, 13


@asm_pio(
    out_init=(rp2.PIO.OUT_LOW,) * 6,  # Data pins GP0-5
    sideset_init=(rp2.PIO.OUT_LOW,),   # Clock pin GP6
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=True,
    pull_thresh=8,
)
def hub75_data_pio():
    """
    PIO program to shift out 6-bit pixel data with clock.

    Input: Stream of bytes, lower 6 bits = R1,G1,B1,R2,G2,B2
    Sideset: CLK pin
    Out pins: Data pins 0-5

    Each pixel: output 6 bits, pulse clock
    Runs at PIO clock speed (125MHz / divider)
    """
    wrap_target()
    out(pins, 6)       .side(0)  # Output 6 data bits, CLK low
    nop()              .side(1)  # CLK high
    wrap()


class HUB75Display:
    """
    Fast HUB75 display using PIO for data shifting.
    """

    def __init__(self, width=64, height=64, brightness=255):
        self.width = width
        self.height = height
        self.brightness = brightness

        # Framebuffer - RGB bytes
        self.framebuffer = bytearray(width * height * 3)

        # Pre-computed row data buffer (6 bits packed per pixel)
        # Each row = 64 bytes (one byte per pixel, only lower 6 bits used)
        self._row_data = bytearray(width)

        # Control pins (directly managed by Python)
        self.lat = Pin(PIN_LAT, Pin.OUT, value=0)
        self.oe = Pin(PIN_OE, Pin.OUT, value=1)  # Active low, start disabled
        self.addr = [
            Pin(PIN_A, Pin.OUT, value=0),
            Pin(PIN_B, Pin.OUT, value=0),
            Pin(PIN_C, Pin.OUT, value=0),
            Pin(PIN_D, Pin.OUT, value=0),
            Pin(PIN_E, Pin.OUT, value=0),
        ]

        # Initialize PIO state machine for data shifting
        # Data pins: GP0-5, Sideset (CLK): GP6
        self._sm = StateMachine(
            0,  # State machine 0
            hub75_data_pio,
            freq=10_000_000,  # 10MHz clock = 5MHz pixel rate
            out_base=Pin(PIN_R1),  # OUT pins start at GP0
            sideset_base=Pin(PIN_CLK),  # Sideset is CLK
        )
        self._sm.active(1)

        # Thread control
        self._running = False

        print(f"HUB75 Fast Display: {width}x{height} @ {freq()//1_000_000}MHz CPU")

    def set_pixel(self, x, y, r, g, b):
        """Set pixel color."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8
        offset = (y * self.width + x) * 3
        self.framebuffer[offset] = r
        self.framebuffer[offset + 1] = g
        self.framebuffer[offset + 2] = b

    def clear(self, r=0, g=0, b=0):
        """Clear display."""
        for i in range(0, len(self.framebuffer), 3):
            self.framebuffer[i] = r
            self.framebuffer[i + 1] = g
            self.framebuffer[i + 2] = b

    def set_brightness(self, value):
        self.brightness = max(0, min(255, value))

    def _set_row_addr(self, row):
        """Set row address pins."""
        self.addr[0].value(row & 1)
        self.addr[1].value((row >> 1) & 1)
        self.addr[2].value((row >> 2) & 1)
        self.addr[3].value((row >> 3) & 1)
        self.addr[4].value((row >> 4) & 1)

    def _prepare_row_data(self, upper_row, lower_row):
        """Pack pixel data for one row pair into 6-bit format."""
        fb = self.framebuffer
        rd = self._row_data
        width = self.width
        threshold = 128

        u_base = upper_row * width * 3
        l_base = lower_row * width * 3

        for col in range(width):
            u_idx = u_base + col * 3
            l_idx = l_base + col * 3

            # Pack: bit0=R1, bit1=G1, bit2=B1, bit3=R2, bit4=G2, bit5=B2
            pixel = 0
            if fb[u_idx] >= threshold: pixel |= 0x01      # R1
            if fb[u_idx + 1] >= threshold: pixel |= 0x02  # G1
            if fb[u_idx + 2] >= threshold: pixel |= 0x04  # B1
            if fb[l_idx] >= threshold: pixel |= 0x08      # R2
            if fb[l_idx + 1] >= threshold: pixel |= 0x10  # G2
            if fb[l_idx + 2] >= threshold: pixel |= 0x20  # B2

            rd[col] = pixel

    def show(self):
        """Single refresh cycle using PIO for data shifting."""
        sm = self._sm
        lat = self.lat
        oe = self.oe

        for row in range(32):
            # 1. Disable output
            oe.value(1)

            # 2. Prepare packed pixel data for this row pair
            self._prepare_row_data(row, row + 32)

            # 3. Set row address
            self._set_row_addr(row)

            # 4. Send pixel data via PIO (very fast!)
            sm.put(self._row_data)

            # 5. Wait for PIO to finish shifting (64 pixels)
            time.sleep_us(15)

            # 6. Latch the data
            lat.value(1)
            lat.value(0)

            # 7. Enable output
            oe.value(0)

            # 8. Display time for this row
            time.sleep_us(30)

        # End of frame
        oe.value(1)

    def _refresh_loop(self):
        """Background refresh loop for second core."""
        while self._running:
            self.show()

    def start(self):
        """Start background refresh on core 1."""
        if self._running:
            return
        self._running = True
        _thread.start_new_thread(self._refresh_loop, ())
        print("Background refresh started")

    def stop(self):
        """Stop background refresh."""
        self._running = False
        time.sleep_ms(50)
        self.oe.value(1)
        print("Refresh stopped")

    def fill_rect(self, x, y, w, h, r, g, b):
        for py in range(y, min(y + h, self.height)):
            for px in range(x, min(x + w, self.width)):
                self.set_pixel(px, py, r, g, b)

    def test_pattern(self):
        """RGB stripes test pattern."""
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
    display = HUB75Display(64, 64)
    display.test_pattern()
    display.start()

    print("Running for 10 seconds...")
    time.sleep(10)

    display.stop()

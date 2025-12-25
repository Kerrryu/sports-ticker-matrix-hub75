"""
Boot Configuration for Sports Ticker

This file runs before main.py on every boot.
Handles early initialization and crash recovery.
"""

import gc
import machine

# Enable garbage collection
gc.enable()

# Set CPU frequency for optimal performance
# 125MHz is default, can go up to 133MHz but watch thermals
machine.freq(125000000)

# Boot diagnostics
print("=" * 50)
print("Sports Ticker - Boot Sequence")
print("=" * 50)
print(f"CPU Frequency: {machine.freq() / 1_000_000}MHz")
print(f"Free Memory: {gc.mem_free()} bytes")

# Check for crash recovery flag
try:
    with open('/crash_flag.txt', 'r') as f:
        crash_count = int(f.read().strip())
        print(f"Previous crashes detected: {crash_count}")
        if crash_count >= 3:
            print("Multiple crashes detected - entering safe mode")
            # Safe mode: skip normal boot, just start web server
            import sys
            sys.exit()  # Will not run main.py
except:
    pass  # No crash flag, normal boot

print("Boot complete - starting main application...")
print("=" * 50)

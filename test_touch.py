from machine import Pin, SPI
import time
from xpt2046 import Touch

print("==========================================================")
print("👉 CYD Touch Screen Diagnostic Probe Initiated...")
print("Please TAP the screen to test touch responsiveness!")
print("==========================================================")

# Backlight ON
backlight21 = Pin(21, Pin.OUT)
backlight21.value(1)

# SPI Mode 3
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

# Initialize Touch Controller (CS=25, IRQ=36)
try:
    touch = Touch(spi, cs=Pin(25), int_pin=Pin(36))
    print("✅ Touch controller initialized successfully!")
    print("Listening for taps... (Press Ctrl+C to stop)")
    
    tap_count = 0
    while tap_count < 10:
        pos = touch.get_touch()
        if pos is not None:
            tap_count += 1
            print("🎯 TAP #{} detected at coordinates: X={}, Y={}".format(tap_count, pos[0], pos[1]))
            time.sleep(0.5) # Debounce cooldown
        time.sleep(0.05)
        
except Exception as e:
    print("❌ Touch initialization failed:", e)

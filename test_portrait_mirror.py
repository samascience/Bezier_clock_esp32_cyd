from machine import Pin, SPI
import time
from ili9341 import Display

print("==========================================================")
print("🩵 Testing Portrait Mirror Mode (rotation=0, mirror=True)...")

# Backlight ON
backlight21 = Pin(21, Pin.OUT)
backlight21.value(1)

# SPI Mode 3
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

try:
    # Initialize with rotation=0, mirror=True (maps to 0xC0)
    display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=240, height=320, rotation=0, mirror=True)
    print("Clearing display to CYAN...")
    display.clear(0x07FF) # Big-Endian Cyan
    print("✅ Screen cleared to CYAN successfully!")
except Exception as e:
    print("❌ Portrait mirror failed:", e)

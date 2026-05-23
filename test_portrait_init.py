from machine import Pin, SPI
import time
from ili9341 import Display

print("==========================================================")
# Backlight ON
backlight21 = Pin(21, Pin.OUT)
backlight21.value(1)

backlight27 = Pin(27, Pin.OUT)
backlight27.value(1) # Turn on both just in case!

# SPI Mode 3
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

print("Initializing Display with rotation=180, mirror=True (Portrait)...")
try:
    display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=240, height=320, rotation=180, mirror=True)
    print("Clearing display to RED...")
    display.clear(0xF800) # Big-Endian Red
    print("✅ Screen cleared to RED successfully!")
except Exception as e:
    print("❌ Initialization failed:", e)

from machine import Pin, SPI
import time
from ili9341 import Display

print("==========================================================")
print("🔴 CYD ST7789 SPI Mode 3 Probe Initiated")
print("==========================================================")

# Force backlight ON (GPIO 21, active-HIGH)
backlight = Pin(21, Pin.OUT)
backlight.value(1)

# Initialize SPI in Mode 3 (polarity=1, phase=1) at a stable 20 MHz
print("Initializing SPI Mode 3...")
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

# Initialize Display
print("Initializing Display Driver...")
display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=320, height=240, rotation=90)

# Clear to solid bright RED (0xF800 is Red in Big-Endian RGB565)
print("Writing solid RED to screen...")
display.clear(0xF800)

print("✅ Finished! Is your screen glowing RED?")

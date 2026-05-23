from machine import Pin, SPI
import time
from ili9341 import Display

print("==========================================================")
print("🎨 CYD ST7789 Color Cycle Prober")
print("==========================================================")

# Backlight ON
backlight = Pin(21, Pin.OUT)
backlight.value(1)

# SPI Mode 3
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

# Initialize Display
display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=320, height=240, rotation=90)

# Colors to test (Big-Endian RGB565)
color_tests = [
    (0xF800, "Red (0xF800)"),
    (0x07E0, "Green (0x07E0)"),
    (0x001F, "Blue (0x001F)"),
    (0x0000, "Black (0x0000)"),
    (0xFFFF, "White (0xFFFF)")
]

cycle = 1
while True:
    print("\n--- Cycle #{} ---".format(cycle))
    for color, name in color_tests:
        print("👉 Writing color: {}".format(name))
        display.clear(color)
        time.sleep(2)
    cycle += 1

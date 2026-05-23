from machine import Pin, SPI
import time
import math
from framebuf import FrameBuffer, RGB565  # type: ignore
from ili9341 import Display

print("==========================================================")
print("📐 Drawing sample portrait clock numbers (rotation=180, mirror=False)...")

# Backlight ON
backlight21 = Pin(21, Pin.OUT)
backlight21.value(1)

# SPI Mode 3
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

# Initialize Display in rotation=180, mirror=False
display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=240, height=320, rotation=180, mirror=False)

# Colors
COLOR_BG_DIS = 0x0862      # Big-endian for Display
COLOR_BG_FB = 0x6208       # Little-endian for FrameBuffer
COLOR_HOUR_FB = 0x00FC     # Little-endian for FrameBuffer (Neon Orange)
COLOR_MIN_FB = 0xFF06      # Little-endian for FrameBuffer (Neon Cyan)
COLOR_SEC_FB = 0x9BF7      # Little-endian for FrameBuffer (Warm White)
COLOR_COLON_DIS = 0xF79B   # Big-endian for Display

# 13-Point Topologies for 0-9
DIGITS = {
    1: [(50, 0)] * 13,
    2: [(15, 30), (15, 0), (85, 0), (85, 40), (85, 75), (50, 115), (25, 140), (15, 150), (15, 160), (15, 160), (40, 160), (65, 160), (85, 160)],
    3: [(15, 30), (15, 0), (85, 0), (85, 40), (85, 65), (65, 80), (45, 80), (65, 80), (85, 95), (85, 120), (85, 160), (15, 160), (15, 130)],
    4: [(75, 0), (55, 35), (35, 75), (15, 110), (35, 110), (65, 110), (85, 110), (75, 110), (75, 60), (75, 30), (75, 75), (75, 120), (75, 160)],
    5: [(85, 0), (60, 0), (35, 0), (15, 0), (15, 25), (15, 50), (15, 70), (50, 70), (85, 85), (85, 115), (85, 160), (15, 160), (15, 130)],
    6: [(80, 0), (60, 0), (25, 30), (15, 70), (15, 100), (15, 130), (15, 160), (50, 160), (85, 160), (85, 115), (85, 75), (15, 75), (15, 115)]
}

# Fix 1 representation to be a nice clean line
DIGITS[1] = [
    (50, 0), (50, 13), (50, 26), (50, 40), (50, 53), (50, 66), (50, 80),
    (50, 93), (50, 106), (50, 120), (50, 133), (50, 146), (50, 160)
]

# Framebuffers for digits
fbuf_bytes = bytearray(50 * 90 * 2)
fbuf = FrameBuffer(fbuf_bytes, 50, 90, RGB565)

fbuf_sec_bytes = bytearray(30 * 54 * 2)
fbuf_sec = FrameBuffer(fbuf_sec_bytes, 30, 54, RGB565)

def draw_thick_line(fb, x1, y1, x2, y2, color):
    fb.line(int(x1), int(y1), int(x2), int(y2), color)
    fb.line(int(x1 + 1), int(y1), int(x2 + 1), int(y2), color)
    fb.line(int(x1 - 1), int(y1), int(x2 - 1), int(y2), color)
    fb.line(int(x1), int(y1 + 1), int(x2), int(y2 + 1), color)
    fb.line(int(x1), int(y1 - 1), int(x2), int(y2 - 1), color)

def draw_bezier_segment(fb, p0, p1, p2, p3, color, d_width=50, d_height=90, steps=8):
    x_prev, y_prev = None, None
    pad_x = d_width * 0.1
    pad_y = d_height * 0.056
    scale_x = (d_width - 2 * pad_x) / 100.0
    scale_y = (d_height - 2 * pad_y) / 160.0
    
    for i in range(steps + 1):
        t = i / steps
        t2 = t * t
        t3 = t2 * t
        mt = 1.0 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        w0 = mt3
        w1 = 3.0 * mt2 * t
        w2 = 3.0 * mt * t2
        w3 = t3
        
        x = w0 * p0[0] + w1 * p1[0] + w2 * p2[0] + w3 * p3[0]
        y = w0 * p0[1] + w1 * p1[1] + w2 * p2[1] + w3 * p3[1]
        
        xl = x * scale_x + pad_x
        yl = y * scale_y + pad_y
        
        if x_prev is not None:
            draw_thick_line(fb, x_prev, y_prev, xl, yl, color)
        x_prev, y_prev = xl, yl

def render_digit(fb, points, color, bg_color, d_width=50, d_height=90):
    fb.fill(bg_color)
    draw_bezier_segment(fb, points[0], points[1], points[2], points[3], color, d_width, d_height)
    draw_bezier_segment(fb, points[3], points[4], points[5], points[6], color, d_width, d_height)
    draw_bezier_segment(fb, points[6], points[7], points[8], points[9], color, d_width, d_height)
    draw_bezier_segment(fb, points[9], points[10], points[11], points[12], color, d_width, d_height)

# Draw screen background and colon
display.clear(COLOR_BG_DIS)
display.fill_circle(120, 135, 4, COLOR_COLON_DIS)
display.fill_circle(120, 150, 4, COLOR_COLON_DIS)

# Draw Hour "1" and "2"
render_digit(fbuf, DIGITS[1], COLOR_HOUR_FB, COLOR_BG_FB)
display.draw_sprite(fbuf_bytes, 65, 30, 50, 90)

render_digit(fbuf, DIGITS[2], COLOR_HOUR_FB, COLOR_BG_FB)
display.draw_sprite(fbuf_bytes, 125, 30, 50, 90)

# Draw Minute "3" and "4"
render_digit(fbuf, DIGITS[3], COLOR_MIN_FB, COLOR_BG_FB)
display.draw_sprite(fbuf_bytes, 65, 160, 50, 90)

render_digit(fbuf, DIGITS[4], COLOR_MIN_FB, COLOR_BG_FB)
display.draw_sprite(fbuf_bytes, 125, 160, 50, 90)

# Draw Second "5" and "6"
render_digit(fbuf_sec, DIGITS[5], COLOR_SEC_FB, COLOR_BG_FB, 30, 54)
display.draw_sprite(fbuf_sec_bytes, 87, 260, 30, 54)

render_digit(fbuf_sec, DIGITS[6], COLOR_SEC_FB, COLOR_BG_FB, 30, 54)
display.draw_sprite(fbuf_sec_bytes, 123, 260, 30, 54)

print("✅ Numbers drawn on screen!")

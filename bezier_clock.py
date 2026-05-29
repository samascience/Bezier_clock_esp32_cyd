from machine import Pin, SPI, RTC, PWM, ADC
import time
import math
from framebuf import FrameBuffer, RGB565  # type: ignore
from ili9341 import Display

# ==========================================
# CONFIGURATION BLOCK (MAGICALLY UPDATED BY MAGIC INSTALLER!)
# ==========================================
# === CONFIG_START ===
DISPLAY_ROTATION = 180


ENABLE_AUTO_BRIGHTNESS = False
ENABLE_RGB_BREATHING = False
ENABLE_24H_MODE = False
TZ_LOCAL_NAME = "CDT"
TZ_LOCAL_OFFSET = -5.0
TZ_FOREIGN_NAME = "IST"
TZ_FOREIGN_OFFSET = 5.5
WIFI_SSID = "Antharjalam"
WIFI_PASSWORD = "Superman$9"
# === CONFIG_END ===

# Colors (16-bit RGB565)
# Note: Display methods expect Big-Endian, FrameBuffer expects Little-Endian.
# We define both explicitly to avoid byte-swapping overhead at runtime!

# Midnight Blue (#0B0E14) - Background
COLOR_BG_FB = 0x6208       # Little-endian for FrameBuffer
COLOR_BG_DIS = 0x0862      # Big-endian for Display methods

# Glowing Neon Orange - Hour Digits (Saffron Orange in IST)
COLOR_HOUR_FB = 0x00FC     # Little-endian for FrameBuffer

# Glowing Neon Cyan - Minute Digits (CST Mode)
COLOR_MIN_FB = 0xFF06      # Little-endian for FrameBuffer

# Emerald Green - Minute Digits (IST Mode)
COLOR_IST_GREEN_FB = 0xE007  # Little-endian for FrameBuffer

# Warm White - Seconds Digits
COLOR_SEC_FB = 0x9BF7      # Little-endian for FrameBuffer

# Warm White - Separator Colon
COLOR_COLON_DIS = 0xF79B   # Big-endian for Display methods

# ==========================================
# HARDWARE INTERFACES & INITIALIZATION
# ==========================================

# 1. SPI & Display Configuration
# SPI 1 is mapped to pins 14 (SCK), 13 (MOSI), 12 (MISO)
# Lowered to 20MHz and configured for SPI Mode 3 (polarity=1, phase=1) for ST7789 compatibility
spi = SPI(1, baudrate=20000000, polarity=1, phase=1, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

# CS=15, DC=2, RST=22 (unused Pin on extended connector to prevent Red LED reset conflicts)
# mirror=True and rotation=180 initializes the ST7789 in standard mirrored portrait mode (0x00)
# bgr=False is passed to fix the Red/Blue color swap!
display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(22), width=240, height=320, rotation=DISPLAY_ROTATION, mirror=True, bgr=False)

# 2. Hardware Touch IRQ Pin (GPIO 36) - Pulls LOW (0) when tapped!
# Direct hardware polling avoids all SPI bus conflicts and is 100% reliable.
touch_irq = Pin(36, Pin.IN)

# 3. Backlight Pins (GPIO 21 & 27) - Turn on both to support both 2.8" (standard) and 3.5" CYD models!
backlight = Pin(21, Pin.OUT)
backlight.value(1)  # Turn fully ON
backlight27 = Pin(27, Pin.OUT)
backlight27.value(1)  # Turn fully ON


# 3. LDR Light Sensor (GPIO 34)
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  # Full 0-3.6V range for LDR

# 4. On-Board RGB LED (GPIO 4=R, 16=G, 17=B) - Active-LOW PWM
red_led = PWM(Pin(4), freq=1000)
green_led = PWM(Pin(16), freq=1000)
blue_led = PWM(Pin(17), freq=1000)

# Active-LOW initialize: 1023 duty cycle is fully OFF
red_led.duty(1023)
green_led.duty(1023)
blue_led.duty(1023)

# 5. Local Digit FrameBuffer Setup
# Bounding box is 50x90 pixels.
# Memory requirement: 50 * 90 * 2 = 9,000 bytes. Perfect for heap!
fbuf_bytes = bytearray(50 * 90 * 2)
fbuf = FrameBuffer(fbuf_bytes, 50, 90, RGB565)

# 7. Local Seconds Digit FrameBuffer Setup
# Bounding box is 30x54 pixels (60% scale).
# Memory requirement: 30 * 54 * 2 = 3,240 bytes. Extremely efficient!
fbuf_sec_bytes = bytearray(30 * 54 * 2)
fbuf_sec = FrameBuffer(fbuf_sec_bytes, 30, 54, RGB565)

# 6. Real-Time Clock Initialization (Set to User's Local Time)
rtc = RTC()
# Set RTC: (Year, Month, Day, Weekday, Hour, Minute, Second, Subsecond)
# Matches Metadata time: Friday, May 22, 2026 at 21:31:59 (9:31 PM)
rtc.datetime((2026, 5, 22, 4, 21, 31, 59, 0))

# ==========================================
# MATHEMATICAL 13-POINT DIGIT TOPOLOGY
# ==========================================
# Each digit is mapped to a normalized 100x160 canvas, using exactly
# 13 points forming 4 joined Cubic Bézier curves.
DIGITS = {
    0: [
        (50, 0),   # P0
        (85, 0),   # P1
        (100, 35), # P2
        (100, 80), # P3 (Right center)
        (100, 125),# P4
        (85, 160), # P5
        (50, 160), # P6 (Bottom center)
        (15, 160), # P7
        (0, 125),  # P8
        (0, 80),   # P9 (Left center)
        (0, 35),   # P10
        (15, 0),   # P11
        (50, 0)    # P12 (Top center - closed)
    ],
    1: [
        (50, 0),   # Collapse all points into a straight vertical line
        (50, 13),
        (50, 26),
        (50, 40),
        (50, 53),
        (50, 66),
        (50, 80),
        (50, 93),
        (50, 106),
        (50, 120),
        (50, 133),
        (50, 146),
        (50, 160)
    ],
    2: [
        (15, 30),  # P0 (Top-left start)
        (15, 0),   # P1
        (85, 0),   # P2
        (85, 40),  # P3 (Top-right arch)
        (85, 75),  # P4
        (50, 115), # P5
        (25, 140), # P6 (Diagonal down-left)
        (15, 150), # P7
        (15, 160), # P8
        (15, 160), # P9 (Corner)
        (40, 160), # P10
        (65, 160), # P11
        (85, 160)  # P12 (Bottom-right end)
    ],
    3: [
        (15, 30),  # P0 (Top-left start)
        (15, 0),   # P1
        (85, 0),   # P2
        (85, 40),  # P3
        (85, 65),  # P4
        (65, 80),  # P5
        (45, 80),  # P6 (Junction middle)
        (65, 80),  # P7
        (85, 95),  # P8
        (85, 120), # P9
        (85, 160), # P10
        (15, 160), # P11
        (15, 130)  # P12 (Bottom-left end)
    ],
    4: [
        (75, 0),   # P0
        (55, 35),  # P1
        (35, 75),  # P2
        (15, 110), # P3 (Diagonal corner)
        (35, 110), # P4
        (65, 110), # P5
        (85, 110), # P6 (Horizontal end)
        (75, 110), # P7
        (75, 60),  # P8
        (75, 30),  # P9 (Vertical start)
        (75, 75),  # P10
        (75, 120), # P11
        (75, 160)  # P12 (Vertical end)
    ],
    5: [
        (85, 0),   # P0 (Top-right start)
        (60, 0),   # P1
        (35, 0),   # P2
        (15, 0),   # P3 (Top-left corner)
        (15, 25),  # P4
        (15, 50),  # P5
        (15, 70),  # P6 (Middle-left)
        (50, 70),  # P7
        (85, 85),  # P8
        (85, 115), # P9 (Bottom loop right)
        (85, 160), # P10
        (15, 160), # P11
        (15, 130)  # P12 (Bottom-left end)
    ],
    6: [
        (80, 0),   # P0 (Top-right hook start)
        (60, 0),   # P1
        (25, 30),  # P2
        (15, 70),  # P3
        (15, 100), # P4
        (15, 130), # P5
        (15, 160), # P6 (Bottom-left)
        (50, 160), # P7
        (85, 160), # P8
        (85, 115), # P9 (Loop right)
        (85, 75),  # P10
        (15, 75),  # P11
        (15, 115)  # P12 (Loop back start)
    ],
    7: [
        (15, 0),   # P0
        (40, 0),   # P1
        (65, 0),   # P2
        (85, 0),   # P3 (Top-right corner)
        (75, 30),  # P4
        (65, 60),  # P5
        (55, 90),  # P6 (Diagonal middle)
        (45, 115), # P7
        (35, 140), # P8
        (25, 160), # P9 (Bottom-left end)
        (25, 160), # P10 (Collapsed)
        (25, 160), # P11 (Collapsed)
        (25, 160)  # P12 (Collapsed)
    ],
    8: [
        (50, 80),  # P0 (Center)
        (20, 80),  # P1
        (20, 0),   # P2
        (50, 0),   # P3 (Top center)
        (80, 0),   # P4
        (80, 80),  # P5
        (50, 80),  # P6 (Center)
        (20, 80),  # P7
        (20, 160), # P8
        (50, 160), # P9 (Bottom center)
        (80, 160), # P10
        (80, 80),  # P11
        (50, 80)   # P12 (Center - closed)
    ],
    9: [
        (85, 45),  # P0
        (85, 5),   # P1
        (15, 5),   # P2
        (15, 45),  # P3 (Top-left loop)
        (15, 85),  # P4
        (85, 85),  # P5
        (85, 45),  # P6 (Loop closed)
        (85, 75),  # P7
        (85, 115), # P8
        (85, 130), # P9
        (85, 160), # P10
        (15, 160), # P11
        (15, 130)  # P12 (Bottom hook end)
    ]
}

# ==========================================
# BÉZIER MATH & RENDER ENGINE
# ==========================================

def draw_thick_line(fb, x1, y1, x2, y2, color):
    """Draw a robust 3-pixel-thick line on the FrameBuffer for high visibility."""
    # Central stroke
    fb.line(int(x1), int(y1), int(x2), int(y2), color)
    # Surrounding offsets (brush effect)
    fb.line(int(x1 + 1), int(y1), int(x2 + 1), int(y2), color)
    fb.line(int(x1 - 1), int(y1), int(x2 - 1), int(y2), color)
    fb.line(int(x1), int(y1 + 1), int(x2), int(y2 + 1), color)
    fb.line(int(x1), int(y1 - 1), int(x2), int(y2 - 1), color)

def draw_bezier_segment(fb, p0, p1, p2, p3, color, d_width=50, d_height=90, steps=8):
    """Evaluate and render a single Cubic Bézier curve segment with dynamic scaling."""
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
        
        # Bezier polynomial weights
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
    """Render all 4 Bézier segments of a digit into the local FrameBuffer with custom sizes."""
    fb.fill(bg_color)
    draw_bezier_segment(fb, points[0], points[1], points[2], points[3], color, d_width, d_height)
    draw_bezier_segment(fb, points[3], points[4], points[5], points[6], color, d_width, d_height)
    draw_bezier_segment(fb, points[6], points[7], points[8], points[9], color, d_width, d_height)
    draw_bezier_segment(fb, points[9], points[10], points[11], points[12], color, d_width, d_height)

def interpolate_points(points_a, points_b, progress):
    """Linearly interpolate control points between two digits (lerp)."""
    return [
        (a[0] + (b[0] - a[0]) * progress, a[1] + (b[1] - a[1]) * progress)
        for a, b in zip(points_a, points_b)
    ]

# ==========================================
# DECORATIVE ANIMATIONS & CONTROLS
# ==========================================

def draw_colon(dis, color):
    """Draw a modern digital colon vertically in the center of the display (portrait layout)."""
    dis.fill_circle(120, 135, 4, color)
    dis.fill_circle(120, 150, 4, color)

def update_ambient_effects(breathe_val, ldr_avg):
    """Perform background auto-brightness and breathing RGB glow."""
    # 1. Low-Pass Auto-Brightness
    if ENABLE_AUTO_BRIGHTNESS:
        ldr_raw = ldr.read()
        # Bright room (high ADC) -> Bright screen; Dark room -> Dim screen
        target_br = int(100 + (ldr_raw / 4095.0) * 923)
        target_br = max(80, min(1023, target_br)) # Caps to safe duty ranges
        
        # Apply gentle low-pass smoothing (10% target, 90% current)
        new_br = int(ldr_avg[0] + (target_br - ldr_avg[0]) * 0.1)
        backlight.duty(new_br)
        ldr_avg[0] = new_br
        
    # 2. Breathing RGB Aura Pulse
    if ENABLE_RGB_BREATHING:
        # Generate a beautiful breathing violet pulse (Cyan-indigo hue)
        # PWM active-LOW: 1023 is off, 0 is fully on.
        # Max intensity when breathe_val is peak (breathe_val goes 0 -> 1 -> 0)
        duty_red = int(1023 - (breathe_val * 150))
        duty_blue = int(1023 - (breathe_val * 250))
        red_led.duty(max(0, min(1023, duty_red)))
        blue_led.duty(max(0, min(1023, duty_blue)))
        green_led.duty(1023)  # Green remains off for violet glow

def animate_morph(dis, fb, fb_bytes, bg_color_fb,
                  h1_s, h1_e, h1_color,
                  h2_s, h2_e, h2_color,
                  m1_s, m1_e, m1_color,
                  m2_s, m2_e, m2_color,
                  ldr_avg, duration_frames=18):
    """Coordinate the smooth, zero-flicker morphing transition of all digits."""
    for frame in range(duration_frames + 1):
        p = frame / duration_frames
        
        # Cubic ease-out: 1 - (1 - p)^3
        ease_p = 1.0 - math.pow(1.0 - p, 3)
        
        # Draw and push Hour 1 (HH:xx) - Centered at the top
        pts_h1 = interpolate_points(h1_s, h1_e, ease_p)
        render_digit(fb, pts_h1, h1_color, bg_color_fb)
        dis.draw_sprite(fb_bytes, 65, 30, 50, 90)
        
        # Draw and push Hour 2 (xH:xx) - Centered at the top
        pts_h2 = interpolate_points(h2_s, h2_e, ease_p)
        render_digit(fb, pts_h2, h2_color, bg_color_fb)
        dis.draw_sprite(fb_bytes, 125, 30, 50, 90)
        
        # Draw and push Minute 1 (xx:Mx) - Centered in the middle
        pts_m1 = interpolate_points(m1_s, m1_e, ease_p)
        render_digit(fb, pts_m1, m1_color, bg_color_fb)
        dis.draw_sprite(fb_bytes, 65, 160, 50, 90)
        
        # Draw and push Minute 2 (xx:xM) - Centered in the middle
        pts_m2 = interpolate_points(m2_s, m2_e, ease_p)
        render_digit(fb, pts_m2, m2_color, bg_color_fb)
        dis.draw_sprite(fb_bytes, 125, 160, 50, 90)
        
        # Maintain breathing LED during animations
        # Animation runs roughly over 360ms, breathing tracks with animation frames
        breath_p = math.sin(p * math.pi)
        update_ambient_effects(breath_p, ldr_avg)
        
        time.sleep_ms(20)  # ~50 FPS target

# ==========================================
# WIFI NETWORK & NTP CLOCK SYNC
# ==========================================

def sync_time_from_ntp():
    """Connect to WiFi and sync ESP32 RTC to UTC time using NTP."""
    if not WIFI_SSID or WIFI_SSID == "your_wifi_ssid":
        print("WiFi SSID not configured. Skipping NTP sync.")
        return False
        
    print("Connecting to WiFi SSID: {}...".format(WIFI_SSID))
    import network
    import ntptime
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Check if already connected
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait up to 10 seconds for connection
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep_ms(500)
            
    if wlan.isconnected():
        print("WiFi connected! IP:", wlan.ifconfig()[0])
        try:
            print("Syncing time from NTP pool.ntp.org...")
            ntptime.timeout = 5
            ntptime.settime()
            print("NTP Sync successful! RTC set to UTC.")
            return True
        except Exception as e:
            print("NTP sync failed:", e)
    else:
        print("WiFi connection timeout.")
        
    return False

# ==========================================
# MAIN EXECUTION LOOP
# ==========================================

def run():
    print("Initializing ESP32 CYD Bezier Morphing Clock...")
    
    # Draw a premium boot status screen
    display.clear(COLOR_BG_DIS)
    # Drawing elegant glowing title
    display.draw_text8x8(20, 50, "BEZIER MORPHING CLOCK", COLOR_HOUR_FB, COLOR_BG_DIS)
    display.draw_text8x8(20, 70, "Powered by Antigravity AI", COLOR_SEC_FB, COLOR_BG_DIS)
    
    if WIFI_SSID and WIFI_SSID != "your_wifi_ssid":
        display.draw_text8x8(20, 110, "WiFi: Connecting...", COLOR_MIN_FB, COLOR_BG_DIS)
        display.draw_text8x8(20, 130, "SSID: " + WIFI_SSID, COLOR_SEC_FB, COLOR_BG_DIS)
        
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        connected = False
        for _ in range(20):
            if wlan.isconnected():
                connected = True
                break
            time.sleep_ms(500)
            
        if connected:
            ip_addr = wlan.ifconfig()[0]
            display.draw_text8x8(20, 110, "WiFi: Connected!      ", COLOR_IST_GREEN_FB, COLOR_BG_DIS)
            display.draw_text8x8(20, 150, "IP: " + ip_addr, COLOR_MIN_FB, COLOR_BG_DIS)
            print("WiFi connected! IP:", ip_addr)
            
            display.draw_text8x8(20, 180, "NTP: Syncing time...", COLOR_MIN_FB, COLOR_BG_DIS)
            try:
                import ntptime
                ntptime.timeout = 5
                ntptime.settime()
                display.draw_text8x8(20, 180, "NTP: Sync Success!   ", COLOR_IST_GREEN_FB, COLOR_BG_DIS)
            except Exception as e:
                print("NTP failed:", e)
                display.draw_text8x8(20, 180, "NTP: Sync Failed     ", COLOR_HOUR_FB, COLOR_BG_DIS)
        else:
            display.draw_text8x8(20, 110, "WiFi: Timeout!       ", COLOR_HOUR_FB, COLOR_BG_DIS)
            display.draw_text8x8(20, 150, "Running Offline mode", COLOR_SEC_FB, COLOR_BG_DIS)
        
        time.sleep(2.5) # Allow user to read the IP address comfortably!
    else:
        display.draw_text8x8(20, 110, "WiFi: Not configured", COLOR_HOUR_FB, COLOR_BG_DIS)
        time.sleep(1.5)
        
    # Draw screen background and initial static elements once
    display.clear(COLOR_BG_DIS)
    draw_colon(display, COLOR_COLON_DIS)
    
    # Store LDR rolling average (mutable list to pass by reference)
    ldr_avg = [512]
    
    # Track current clock state
    curr_h1, curr_h2, curr_m1, curr_m2 = -1, -1, -1, -1
    last_second = -1
    colon_state = True
    
    # Timezone states (False = CST/Local, True = IST/India)
    active_tz_is_ist = False
    last_touch_ms = 0
    
    # NTP periodic sync tracking (every 2 hours = 7,200,000 ms)
    last_ntp_sync_ms = time.ticks_ms()
    SYNC_INTERVAL_MS = 7200000
    
    try:
        while True:
            # 1. Handle Touch Screen Taps to Switch Timezones (via direct hardware IRQ polling)
            if touch_irq.value() == 0:
                now_ms = time.ticks_ms()
                # 1.2 seconds debounce to prevent rapid toggling
                if time.ticks_diff(now_ms, last_touch_ms) > 1200:
                    last_touch_ms = now_ms
                    active_tz_is_ist = not active_tz_is_ist
                    print("Timezone toggled via hardware tap! Active: " + (TZ_FOREIGN_NAME if active_tz_is_ist else TZ_LOCAL_NAME))
                    # Force instant refresh of all digits!
                    curr_h1, curr_h2, curr_m1, curr_m2 = -1, -1, -1, -1
                    last_second = -1
                    
            # 2. Handle Periodic NTP Time Synchronization (Every 2 Hours)
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_ntp_sync_ms) > SYNC_INTERVAL_MS:
                last_ntp_sync_ms = now_ms
                print("Periodic NTP clock sync triggered...")
                if not sync_time_from_ntp():
                    # If sync failed (e.g. WiFi offline), retry in 5 minutes (300,000 ms)
                    last_ntp_sync_ms = now_ms - (SYNC_INTERVAL_MS - 300000)
                    print("NTP sync failed. Retrying in 5 minutes.")
                
            # 3. Fetch current time (UTC from RTC)
            t = time.localtime()
            hour = t[3]
            minute = t[4]
            second = t[5]
            millisecond = time.ticks_ms()
            
            # Apply corresponding timezone offset relative to UTC (CDT vs IST)
            offset = TZ_FOREIGN_OFFSET if active_tz_is_ist else TZ_LOCAL_OFFSET
            total_min = hour * 60 + minute + int(offset * 60)
            total_min = total_min % 1440 # Rollover at 24 hours
            hour = total_min // 60
            minute = total_min % 60
                
            # Convert 24-hour format to 12-hour format if 24h mode is disabled
            if not ENABLE_24H_MODE:
                hour = hour % 12
                if hour == 0:
                    hour = 12
            
            # Split time into discrete digits
            h1 = hour // 10
            h2 = hour % 10
            m1 = minute // 10
            m2 = minute % 10
            
            # Select colors dynamically based on active timezone
            if active_tz_is_ist:
                h_color = COLOR_HOUR_FB       # Saffron Orange
                m_color = COLOR_IST_GREEN_FB  # Emerald Green
                s_color = COLOR_SEC_FB        # Warm White
            else:
                h_color = COLOR_HOUR_FB       # Saffron Orange
                m_color = COLOR_MIN_FB        # Neon Cyan
                s_color = COLOR_SEC_FB        # Warm White
            
            # 3. Check for Minute/Hour updates -> Trigger Morphing Animation
            if (h1 != curr_h1) or (h2 != curr_h2) or (m1 != curr_m1) or (m2 != curr_m2):
                print("Time updated: {:02d}:{:02d} - Morphing...".format(hour, minute))
                
                # Instantly draw seconds "00" on the screen before morphing hours/minutes
                # so the seconds digits don't look frozen on "59" during the animation!
                if curr_h1 != -1:  # Only if it's not the very first boot render
                    render_digit(fbuf_sec, DIGITS[0], s_color, COLOR_BG_FB, 30, 54)
                    display.draw_sprite(fbuf_sec_bytes, 87, 260, 30, 54)
                    render_digit(fbuf_sec, DIGITS[0], s_color, COLOR_BG_FB, 30, 54)
                    display.draw_sprite(fbuf_sec_bytes, 123, 260, 30, 54)
                    
                    # Also update colon and last_second state
                    draw_colon(display, COLOR_COLON_DIS)
                    last_second = 0
                    colon_state = True
                
                # Sourcing coordinate frames (prevent out-of-bounds on start)
                h1_s = DIGITS[h1] if curr_h1 == -1 else DIGITS[curr_h1]
                h2_s = DIGITS[h2] if curr_h2 == -1 else DIGITS[curr_h2]
                m1_s = DIGITS[m1] if curr_m1 == -1 else DIGITS[curr_m1]
                m2_s = DIGITS[m2] if curr_m2 == -1 else DIGITS[curr_m2]
                
                # Trigger smooth bezier morphing animation
                animate_morph(display, fbuf, fbuf_bytes, COLOR_BG_FB,
                              h1_s, DIGITS[h1], h_color,
                              h2_s, DIGITS[h2], h_color,
                              m1_s, DIGITS[m1], m_color,
                              m2_s, DIGITS[m2], m_color,
                              ldr_avg, duration_frames=18)
                
                # Lock digits state
                curr_h1, curr_h2, curr_m1, curr_m2 = h1, h2, m1, m2
                
            # 4. Handle Blinking Colon (1 Hz tick) & Seconds Bézier Morphing
            if second != last_second:
                s1_curr = last_second // 10 if last_second != -1 else second // 10
                s2_curr = last_second % 10 if last_second != -1 else second % 10
                s1_targ = second // 10
                s2_targ = second % 10

                last_second = second
                colon_state = not colon_state
                # Redraw colon (warm white when active, midnight blue background when inactive)
                c_color = COLOR_COLON_DIS if colon_state else COLOR_BG_DIS
                draw_colon(display, c_color)

                # If rolling over to a new minute (second == 0), skip the seconds animation
                # because the minute morph already provides a smooth transition.
                if second == 0:
                    # Directly render 00 seconds without animation
                    render_digit(fbuf_sec, DIGITS[0], s_color, COLOR_BG_FB, 30, 54)
                    display.draw_sprite(fbuf_sec_bytes, 87, 260, 30, 54)
                    render_digit(fbuf_sec, DIGITS[0], s_color, COLOR_BG_FB, 30, 54)
                    display.draw_sprite(fbuf_sec_bytes, 123, 260, 30, 54)
                else:
                    s1_s = DIGITS[s1_curr]
                    s2_s = DIGITS[s2_curr]
                    s1_e = DIGITS[s1_targ]
                    s2_e = DIGITS[s2_targ]

                    for frame in range(8 + 1):
                        p = frame / 8.0
                        ease_p = 1.0 - math.pow(1.0 - p, 3)  # Cubic ease-out

                        # Draw Second 1 (X=87, Y=260, size 30x54) - Centered at the bottom
                        pts_s1 = interpolate_points(s1_s, s1_e, ease_p)
                        render_digit(fbuf_sec, pts_s1, s_color, COLOR_BG_FB, 30, 54)
                        display.draw_sprite(fbuf_sec_bytes, 87, 260, 30, 54)

                        # Draw Second 2 (X=123, Y=260, size 30x54) - Centered at the bottom
                        pts_s2 = interpolate_points(s2_s, s2_e, ease_p)
                        render_digit(fbuf_sec, pts_s2, s_color, COLOR_BG_FB, 30, 54)
                        display.draw_sprite(fbuf_sec_bytes, 123, 260, 30, 54)

                        time.sleep_ms(10)
            
            # 5. Standard Background Ambient Effects (Breathing LED & Auto-Brightness)
            # Breathing is driven by a sine wave over the current second
            ms_frac = (millisecond % 1000) / 1000.0
            breath_p = math.sin(ms_frac * math.pi)
            update_ambient_effects(breath_p, ldr_avg)
            
            # Tiny cycle sleep
            time.sleep_ms(50)
            
    except KeyboardInterrupt:
        # Safe termination: clean up and turn off screen backlight/LEDs
        print("\nShutting down clock...")
        backlight.value(0)
        try:
            backlight27.value(0)
        except:
            pass
        red_led.duty(1023)
        green_led.duty(1023)
        blue_led.duty(1023)

        display.cleanup()

# Automatically execute when run
if __name__ == '__main__':
    run()

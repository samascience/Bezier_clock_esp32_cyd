from machine import Pin
import time

print("==========================================================")
print("🔍 CYD Backlight Hardware Probe Initiated")
print("==========================================================")

# Initialize standard pins
backlight_21 = None
backlight_27 = None

try:
    backlight_21 = Pin(21, Pin.OUT)
except Exception as e:
    print("Could not initialize Pin 21:", e)

try:
    backlight_27 = Pin(27, Pin.OUT)
except Exception as e:
    print("Could not initialize Pin 27:", e)

# Test sequence: Pin, Level, Description
tests = [
    (backlight_21, 1, "GPIO 21 HIGH (Active-HIGH NPN standard 2.8\")"),
    (backlight_21, 0, "GPIO 21 LOW  (Active-LOW PNP standard 2.8\")"),
    (backlight_27, 1, "GPIO 27 HIGH (Active-HIGH 3.5\" model)"),
    (backlight_27, 0, "GPIO 27 LOW  (Active-LOW 3.5\" model)"),
]

print("\nStarting 2-second cycle tests. Watch your CYD screen!")
cycle = 1

while True:
    print("\n--- Cycle #{} ---".format(cycle))
    for pin, val, desc in tests:
        if pin is None:
            continue
            
        # Turn off both pins first to prevent conflicts
        if backlight_21: backlight_21.value(0 if "LOW" in desc else 0)
        if backlight_27: backlight_27.value(0 if "LOW" in desc else 0)
        time.sleep_ms(100)
        
        # Apply the test
        print("👉 Testing: {}".format(desc))
        pin.value(val)
        
        # Pulse RGB LED as a heartbeat so the user knows the script is running
        time.sleep(2)
        
    cycle += 1

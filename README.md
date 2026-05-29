# 🌈 ESP32 CYD Bezier Morphing Clock ⏰

Welcome to the **most beautiful, fluid, and mesmerizing clock** you can run on your Cheap Yellow Display (CYD) board! 

Inspired by the famous **Timely** app digits, this clock doesn't just change numbers—it **morphs** them! Using mathematical **Cubic Bézier curves**, the lines bend, stretch, and wiggle like jelly a[...]

This clock is configured in **portrait mode** (standing up vertically: Hours at the top, Minutes in the middle, Seconds at the bottom) with high-contrast glowing neon colors and a completely dark top [...]

<img width="415" height="925" alt="output" src="https://github.com/user-attachments/assets/686abdf3-b582-400b-8875-0269b27610ee" />


---

## 📸 How it Looks!
*   **Midnight Blue Background** 🌌 (Clean, sleek dark mode)
*   **Glowing Neon Orange Hours** 🧡
*   **Neon Cyan Minutes** 🩵
*   **Warm White Seconds** 🤍
*   **Blinking Colon** ⏰ (Flickers at a perfect 1 Hz)

---

## 🛠️ What You Need (Prerequisites)

1.  **Your Screen**: An ESP32 CYD (Cheap Yellow Display) board (usually the 2.8" ST7789 single USB-C version).
2.  **Your Cable**: 🔌 **IMPORTANT: A USB-C DATA CABLE!** 🚨 
    > [!IMPORTANT]
    > Many standard phone charging cables do *not* carry data lines. If you use a charge-only cable, your computer won't see the screen! Make sure your cable is a **data-capable USB cable**.
3.  **Your Computer**: A Mac, Linux, or Windows machine.

---

## 🚀 One-Click Magic Install (Recommended!)

We built a super-friendly installer script that does **all the hard work** for you. It automatically checks your computer, installs helper tools, detects your board, and copies all files.

### For Mac & Linux Users:

1.  **Plug your screen** into your computer's USB port using your data cable.
2.  **Open your Terminal** app.
3.  **Navigate** to this folder (drag the folder into Terminal, or type `cd ` followed by the folder path).
4.  Type this magic command and press **Enter**:
    ```bash
    ./upload.sh
    ```
5.  Follow the fun on-screen instructions! 
    *   *First time using this screen?* Select **Option 2** to flash MicroPython automatically!
    *   *Just updating your clock code?* Select **Option 1** for a super-fast file upload!

---

## 🎨 Manual Install (Using Thonny IDE)

If you love programming and want to see the code run line-by-line:

1.  Download and install **Thonny IDE** from: [https://thonny.org/](https://thonny.org/)
2.  Plug in your CYD screen.
3.  In Thonny, click on **Run -> Configure Interpreter** (bottom right of the screen or menu).
4.  Choose **MicroPython (ESP32)** and select your board's serial port (e.g. `/dev/cu.usbserial-110` or similar).
5.  Open these three files in Thonny and save them **to the MicroPython Device**:
    *   `ili9341.py` (Save as: `ili9341.py`)
    *   `xpt2046.py` (Save as: `xpt2046.py`)
    *   `bezier_clock.py` (Save as: `main.py` — *naming it main.py makes it boot automatically when powered!*)
6.  Click the **Red Stop Button** in Thonny to restart the board, and watch the screen glow!

---

## 📂 File Map (What's in the box?)

*   📂 `bezier_clock.py` - The core clock software! It holds the coordinate formulas for all digits (0-9) and calculates the smooth curves.
*   📂 `ili9341.py` - The fast screen controller driver (configured for ST7789 color and orientation).
*   📂 `xpt2046.py` - The touch sensor driver (available for future interactive features).
*   📂 `upload.sh` - The friendly automated installer script.
*   📂 `esp32_micropython.bin` - The stable MicroPython system firmware we use to flash brand new screens.

---

## 🩺 Help! Troubleshooting Tips

### ⚪ The screen is blank or completely white!
*   **Reboot**: Run `./upload.sh` and select **Option 4 (Reboot)**, or unplug the USB cord and plug it back in.
*   **Flash MicroPython**: If it's a brand new screen, it still has the factory test code on it! Run `./upload.sh` and select **Option 2 (Brand New Screen Install)** to erase and flash MicroPython.

### 🔌 Script says "No ESP32 serial ports found"
*   **Cable check**: Swap your USB cable! 90% of the time, the cable is a charge-only cord.
*   **Drivers**: If using an older computer, you might need the CH340 serial driver. Download it here: [https://sparks.gogo.co.nz/ch340.html](https://sparks.gogo.co.nz/ch340.html)

### 🟨 The screen is Yellow, or colors are inverted!
*   Our display driver is pre-tuned to disable inversion (`INVOFF` register), which keeps Midnight Blue looking dark and neon colors vibrant. Make sure you are using our provided `ili9341.py` driver!

---

## 🧬 The Math Magic (For curious minds!)
Each digit on the screen is made of **13 custom control points** forming **4 connected Cubic Bézier curves**. 
When the time ticks over (like `3` changing to `4`):
1.  The board takes the 13 points of the number `3`.
2.  It calculates a path to slide each point smoothly to the 13 points of the number `4`.
3.  It does this over **18 easing steps** utilizing a cubic ease-out calculation to make it look springy!
4.  Each frame is drawn in RAM first (double-buffered) and pushed to the screen via fast SPI at **50 frames per second** to prevent any blinking or flicker!

---

## 🌟 License & Credits
Created with ❤️ by **Antigravity AI** and pair-programmed. 

#!/bin/bash

# ==========================================================
# ⚡️ ESP32 CYD Bezier Morphing Clock Installer ⚡️
# Designed to be simple enough for a 5-year-old!
# Powered by Antigravity AI
# ==========================================================

# Color codes for pretty terminal messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RESET='\033[0m'

# Clear screen for a neat experience
clear

echo -e "${MAGENTA}================================================================${RESET}"
echo -e "${CYAN}    🌟 ⏰   ESP32 CYD BEZIER CLOCK MAGIC INSTALLER   ⏰ 🌟    ${RESET}"
echo -e "${MAGENTA}================================================================${RESET}"
echo -e "         ,-.                               "
echo -e "        / \\ \\  ⚡️ Let's bring your screen to life!   "
echo -e "       |   | |                             "
echo -e "        \\ / /                              "
echo -e "         \`-'   ⏰  MM:SS                   "
echo -e "${MAGENTA}================================================================${RESET}"
echo ""

# ==========================================
# STEP 1: CHECK YOUR COMPUTER'S BRAIN (PYTHON)
# ==========================================
echo -e "${CYAN}[Step 1] Checking your computer's brain... 🧠${RESET}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed on your computer.${RESET}"
    echo -e "${YELLOW}💡 How to fix (so simple a child can do it!):${RESET}"
    echo -e "   1. Open a web browser and go to: ${GREEN}https://www.python.org/downloads/${RESET}"
    echo -e "   2. Click the big download button for macOS."
    echo -e "   3. Open the downloaded file and click 'Next' until it's finished!"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 is installed and ready to roll!${RESET}"
echo ""

# ==========================================
# STEP 2: CHECK HELPER TOOLS (MPREMOTE & ESPTOOL)
# ==========================================
echo -e "${CYAN}[Step 2] Checking for magic helper tools... 🛠️${RESET}"

check_and_install() {
    MODULE=$1
    FRIENDLY_NAME=$2
    
    echo -e "🔍 Checking for ${FRIENDLY_NAME}... "
    
    # Try importing or running it to verify presence
    if python3 -m $MODULE --help &> /dev/null || python3 -m $MODULE version &> /dev/null; then
        echo -e "${GREEN}   ✅ ${FRIENDLY_NAME} is already installed!${RESET}"
        return 0
    fi
    
    echo -e "${YELLOW}   ⚠️ ${FRIENDLY_NAME} is missing. Installing it automatically... 🚀${RESET}"
    
    # Try installing using pip with the macOS system-package override flag
    python3 -m pip install --break-system-packages "$MODULE" &> /dev/null || \
    python3 -m pip install "$MODULE" &> /dev/null
    
    # Verify installation
    if python3 -m $MODULE --help &> /dev/null || python3 -m $MODULE version &> /dev/null; then
        echo -e "${GREEN}   ✅ ${FRIENDLY_NAME} was installed successfully!${RESET}"
    else
        echo -e "${RED}   ❌ Failed to install ${FRIENDLY_NAME} automatically.${RESET}"
        echo -e "${YELLOW}   💡 Troubleshooting:${RESET} In your terminal, type and run:"
        echo -e "      ${CYAN}python3 -m pip install --break-system-packages $MODULE${RESET}"
        exit 1
    fi
}

check_and_install "mpremote" "mpremote (to copy clock files)"
check_and_install "esptool" "esptool (to flash fresh screens)"
echo ""

# ==========================================
# STEP 3: SCAN FOR CONNECTED USB SCREENS
# ==========================================
echo -e "${CYAN}[Step 3] Scanning for connected yellow screens... 🔌${RESET}"

# Look for standard Mac USB serial drivers
PORTS=$(ls /dev/cu.usbserial* /dev/cu.usbmodem* /dev/cu.wchusbserial* /dev/cu.SLAB* 2>/dev/null)

if [ -z "$PORTS" ]; then
    echo -e "${RED}❌ No ESP32 screens found plugging into your Mac.${RESET}"
    echo ""
    echo -e "${YELLOW}🚨 THE #1 BIGGEST TRAP:${RESET}"
    echo -e "   Many USB cords are ${RED}CHARGE-ONLY${RESET} cables. They power the screen but"
    echo -e "   cannot send files! You ${GREEN}MUST${RESET} use a ${CYAN}DATA-capable USB cable${RESET}."
    echo ""
    echo -e "${YELLOW}💡 How to fix:${RESET}"
    echo -e "   1. Try plugging your screen into a different USB port."
    echo -e "   2. Unplug your cable, and find a different cable (like one that came with a phone or controller)."
    echo -e "   3. Make sure the screen's back LED lights up when plugged in!"
    exit 1
fi

# Pick the first matching port
PORT=$(echo "$PORTS" | head -n 1)
echo -e "${GREEN}✅ FOUND SCREEN!${RESET} We will talk to it on port: ${YELLOW}$PORT${RESET}"
echo ""

# ==========================================
# TIMEZONE CONFIGURATION WIZARD HELPER
# ==========================================
configure_timezones() {
    echo -e "${MAGENTA}================================================================${RESET}"
    echo -e "📶 WiFi & 🕒 TIMEZONE SETUP WIZARD"
    echo -e "${MAGENTA}================================================================${RESET}"
    echo -e "Let's connect your clock to WiFi to keep the time perfectly synced!"
    echo ""
    
    # Run the interactive TUI scanner
    if python3 wifi_scanner.py "$PORT" > .wifi_creds.tmp; then
        eval $(cat .wifi_creds.tmp)
        rm -f .wifi_creds.tmp
    else
        # Fallback to manual entry if python script fails
        echo -e "${YELLOW}⚠️ Could not scan WiFi automatically (board busy or not connected)${RESET}"
        read -p "📶 Enter your WiFi SSID (press Enter to skip): " WIFI_SSID
        if [ ! -z "$WIFI_SSID" ]; then
            read -s -p "🔑 Enter your WiFi Password: " WIFI_PASS
            echo ""
        fi
    fi

    # Handle standard placeholder mapping
    WIFI_SSID=${WIFI_SSID:-your_wifi_ssid}
    WIFI_PASS=${WIFI_PASS:-your_wifi_password}

    if [ "$WIFI_SSID" = "__SKIP__" ]; then
        WIFI_SSID="your_wifi_ssid"
        WIFI_PASS="your_wifi_password"
    fi

    
    echo ""
    echo -e "Configure your two desktop timezones relative to standard UTC time:"
    echo ""
    
    read -p "⏰ Enter Name for Timezone 1 (Local, e.g. CDT, CST) [Default: CDT]: " TZ1_NAME
    TZ1_NAME=${TZ1_NAME:-CDT}
    
    read -p "⏰ Enter UTC Offset for $TZ1_NAME in hours (e.g. -5.0 for CDT, -6.0 for CST) [Default: -5.0]: " TZ1_OFFSET
    TZ1_OFFSET=${TZ1_OFFSET:--5.0}
    
    read -p "⏰ Enter Name for Timezone 2 (Foreign, e.g. IST, GMT) [Default: IST]: " TZ2_NAME
    TZ2_NAME=${TZ2_NAME:-IST}
    
    read -p "⏰ Enter UTC Offset for $TZ2_NAME in hours (e.g. 5.5 for IST, 0.0 for GMT) [Default: 5.5]: " TZ2_OFFSET
    TZ2_OFFSET=${TZ2_OFFSET:-5.5}
    
    read -p "⏰ Enable 24-Hour mode? (y/n) [Default: n]: " TZ_24H
    if [[ "$TZ_24H" =~ ^[Yy]$ ]]; then
        MODE_24H="True"
    else
        MODE_24H="False"
    fi
    
    echo ""
    echo -e "${CYAN}🔧 Applying custom settings locally to bezier_clock.py...${RESET}"
    
    python3 -c "
with open('bezier_clock.py', 'r') as f:
    lines = f.read()

start_tag = '# === CONFIG_START ==='
end_tag = '# === CONFIG_END ==='

start_idx = lines.find(start_tag)
end_idx = lines.find(end_tag)

if start_idx != -1 and end_idx != -1:
    new_config = '''DISPLAY_ROTATION = 180


ENABLE_AUTO_BRIGHTNESS = False
ENABLE_RGB_BREATHING = False
ENABLE_24H_MODE = $MODE_24H
TZ_LOCAL_NAME = \"$TZ1_NAME\"
TZ_LOCAL_OFFSET = $TZ1_OFFSET
TZ_FOREIGN_NAME = \"$TZ2_NAME\"
TZ_FOREIGN_OFFSET = $TZ2_OFFSET
WIFI_SSID = \"$WIFI_SSID\"
WIFI_PASSWORD = \"$WIFI_PASS\"'''
    
    modified = lines[:start_idx + len(start_tag) + 1] + new_config + '\\n' + lines[end_idx:]
    with open('bezier_clock.py', 'w') as f:
        f.write(modified)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Settings successfully applied!${RESET}"
        if [ "$WIFI_SSID" != "your_wifi_ssid" ]; then
            echo -e "   📶 WiFi SSID: ${YELLOW}$WIFI_SSID${RESET}"
        else
            echo -e "   📶 WiFi Setup: ${RED}Skipped (NTP sync disabled)${RESET}"
        fi
        echo -e "   ⏰ Timezone 1: ${YELLOW}$TZ1_NAME${RESET} (UTC $TZ1_OFFSET)"
        echo -e "   ⏰ Timezone 2: ${YELLOW}$TZ2_NAME${RESET} (UTC $TZ2_OFFSET)"
        echo -e "   ⏰ Mode: ${YELLOW}24-Hour = $MODE_24H${RESET}"
    else
        echo -e "${RED}❌ Failed to apply timezone settings dynamically.${RESET}"
    fi
    echo ""
}

# ==========================================
# INTERACTIVE OPTIONS MENU
# ==========================================
echo -e "${MAGENTA}================================================================${RESET}"
echo -e "🎈 What would you like to do with your screen today?"
echo -e "${MAGENTA}================================================================${RESET}"
echo -e "  ${GREEN}1)${RESET} ${CYAN}Fast Update (USB)${RESET}"
echo -e "  ${GREEN}2)${RESET} ${YELLOW}Brand New Screen Install (USB)${RESET}"
echo -e "  ${GREEN}3)${RESET} ${GREEN}WiFi Remote Update (Over-the-Air to IP Address! 📶)${RESET}"
echo -e "  ${GREEN}4)${RESET} ${MAGENTA}Configure WiFi Remote Flashing on Board (Requires USB)${RESET}"
echo -e "  ${GREEN}5)${RESET} ${RED}Erase Board Completely (USB)${RESET}"
echo -e "  ${GREEN}6)${RESET} ${BLUE}Reboot Screen (USB)${RESET}"
echo -e "  ${GREEN}7)${RESET} Exit"
echo -e "${MAGENTA}================================================================${RESET}"
read -p "Type your choice number (1-7) and press Enter: " CHOICE

# Helper to force-exit raw REPL developer mode and reboot
reboot_board() {
    echo -e "🔄 Sending standard reboot signal..."
    python3 -m mpremote connect "$PORT" soft-reset &> /dev/null
    
    # Try direct serial escape sequences
    python3 -c "
try:
    import serial, time
    ser = serial.Serial('$PORT', 115200, timeout=1)
    ser.write(b'\x03\x03\x02\x04') # Ctrl+C, Ctrl+B (exit raw REPL), Ctrl+D (soft reset)
    ser.close()
except Exception:
    pass
" 2>/dev/null
}

case $CHOICE in
    1)
        # ==========================================
        # STANDARD FILE UPLOAD (USB)
        # ==========================================
        configure_timezones
        
        echo -e "${CYAN}🚀 Uploading files to your screen... Please do not unplug!${RESET}"
        
        # Upload ili9341.py
        echo -e "📤 Sending display driver (ili9341.py)..."
        python3 -m mpremote connect "$PORT" fs cp ili9341.py :ili9341.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to upload ili9341.py display driver.${RESET}"
            exit 1
        fi
        
        # Upload xpt2046.py
        echo -e "📤 Sending touch driver (xpt2046.py)..."
        python3 -m mpremote connect "$PORT" fs cp xpt2046.py :xpt2046.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to upload xpt2046.py touch driver.${RESET}"
            exit 1
        fi
        
        # Upload bezier_clock.py as main.py (so it boots automatically)
        echo -e "📤 Sending portrait clock engine (bezier_clock.py)..."
        python3 -m mpremote connect "$PORT" fs cp bezier_clock.py :main.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to upload clock file.${RESET}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ All files uploaded successfully!${RESET}"
        
        reboot_board
        
        echo ""
        echo -e "${GREEN}🎉 SUCCESS! Your portrait-mode morphing clock is now set up! 🌟${RESET}"
        echo -e "💡 ${YELLOW}NOTE:${RESET} If your screen is blank or the LED is teal, simply press"
        echo -e "   the physical ${GREEN}RESET button${RESET} on the back of your screen (or unplug"
        echo -e "   and replug the USB cable) to start the clock!"
        ;;
        
    2)
        # ==========================================
        # FULL FLASH AND UPLOAD (USB)
        # ==========================================
        configure_timezones
        
        echo -e "${YELLOW}🚨 WARNING: This will erase all old data and flash MicroPython!${RESET}"
        if [ ! -f "esp32_micropython.bin" ]; then
            echo -e "${RED}❌ Error: 'esp32_micropython.bin' not found in this folder!${RESET}"
            echo -e "Please make sure you downloaded the complete repository folder."
            exit 1
        fi
        
        read -p "Are you ready? (y/n): " CONFIRM
        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            echo ""
            echo -e "${CYAN}🧹 Step A: Erasing the screen's memory...${RESET}"
            python3 -m esptool --chip esp32 --port "$PORT" erase_flash
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ Erase failed. Check USB connection and try again.${RESET}"
                exit 1
            fi
            
            echo ""
            echo -e "${CYAN}💾 Step B: Flashing MicroPython firmware... (Takes ~30 seconds)${RESET}"
            python3 -m esptool --chip esp32 --port "$PORT" --baud 460800 write_flash -z 0x1000 esp32_micropython.bin
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ Flashing firmware failed.${RESET}"
                exit 1
            fi
            
            echo -e "${GREEN}✅ Firmware flashed! Waiting 3 seconds for screen to settle...${RESET}"
            sleep 3
            
            echo ""
            echo -e "${CYAN}📤 Step C: Uploading display driver (ili9341.py)...${RESET}"
            python3 -m mpremote connect "$PORT" fs cp ili9341.py :ili9341.py
            
            echo -e "${CYAN}📤 Step D: Uploading touch driver (xpt2046.py)...${RESET}"
            python3 -m mpremote connect "$PORT" fs cp xpt2046.py :xpt2046.py
            
            echo -e "${CYAN}📤 Step E: Uploading portrait clock engine (bezier_clock.py)...${RESET}"
            python3 -m mpremote connect "$PORT" fs cp bezier_clock.py :main.py
            
            reboot_board
            
            echo ""
            echo -e "${GREEN}🎉 CONGRATULATIONS! Your fresh screen is successfully set up! 🌟${RESET}"
            echo -e "💡 ${YELLOW}NOTE:${RESET} If your screen is blank or the LED is teal, simply press"
            echo -e "   the physical ${GREEN}RESET button${RESET} on the back of your screen (or unplug"
            echo -e "   and replug the USB cable) to start the clock!"
        else
            echo "Cancelled."
        fi
        ;;
        
    3)
        # ==========================================
        # WIFI REMOTE OTA UPDATE
        # ==========================================
        configure_timezones
        
        echo -e "${MAGENTA}================================================================${RESET}"
        echo -e "📡 WIFI REMOTE OTA FLASHING WIZARD"
        echo -e "${MAGENTA}================================================================${RESET}"
        read -p "📶 Enter your screen's IP address: " WR_IP
        if [ -z "$WR_IP" ]; then
            echo -e "${RED}❌ Error: IP address is required for remote flashing.${RESET}"
            exit 1
        fi
        
        read -p "🔑 Enter your WebREPL password [Default: 1234]: " WR_PASS
        WR_PASS=${WR_PASS:-1234}
        
        echo ""
        echo -e "${CYAN}🚀 Launching remote wireless flash...${RESET}"
        python3 remote_flash.py "$WR_IP" "$WR_PASS" ili9341.py:ili9341.py xpt2046.py:xpt2046.py bezier_clock.py:main.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}🎉 SUCCESS! Your portrait-mode clock has been updated remotely over WiFi! 📶${RESET}"
        else
            echo ""
            echo -e "${RED}❌ Wireless flashing failed. Please double check IP, network, and password.${RESET}"
        fi
        ;;

    4)
        # ==========================================
        # CONFIGURE WEBREPL ON BOARD VIA USB
        # ==========================================
        echo ""
        echo -e "${MAGENTA}================================================================${RESET}"
        echo -e "🔑 CONFIGURE WIFI REMOTE FLASHING (WEBREPL)"
        echo -e "${MAGENTA}================================================================${RESET}"
        echo -e "This will configure your screen to accept wireless updates over WiFi."
        echo -e "It requires the screen to be plugged in via USB right now."
        echo ""
        
        read -p "🔐 Set a password for remote flashing [Default: 1234]: " WR_PASS
        WR_PASS=${WR_PASS:-1234}
        
        echo -e "${CYAN}🔨 Creating configuration helper...${RESET}"
        cat <<EOF > setup_webrepl.py
# Temporary file to configure WebREPL on target board
with open('webrepl_cfg.py', 'w') as f:
    f.write("PASS = '${WR_PASS}'\n")

boot_content = ""
try:
    with open('boot.py', 'r') as f:
        boot_content = f.read()
except OSError:
    pass

if 'webrepl.start()' not in boot_content:
    with open('boot.py', 'w') as f:
        f.write(boot_content + "\nimport webrepl\nwebrepl.start()\n")
EOF

        echo -e "${CYAN}📤 Sending helper to target board...${RESET}"
        python3 -m mpremote connect "$PORT" fs cp setup_webrepl.py :setup_webrepl.py
        if [ $? -eq 0 ]; then
            echo -e "${CYAN}⚙️ Running configuration helper on board...${RESET}"
            python3 -m mpremote connect "$PORT" run :setup_webrepl.py
            
            echo -e "${CYAN}🧹 Cleaning up target filesystem...${RESET}"
            python3 -m mpremote connect "$PORT" fs rm :setup_webrepl.py
            
            rm -f setup_webrepl.py
            
            echo -e "${GREEN}✅ WebREPL configured successfully with password: ${YELLOW}${WR_PASS}${RESET}"
            
            reboot_board
            
            echo ""
            echo -e "${GREEN}🎉 Your screen is ready for remote updates! Once it connects to your WiFi,${RESET}"
            echo -e "   you can update it completely wire-free using option 3 of this installer! 🚀"
        else
            rm -f setup_webrepl.py
            echo -e "${RED}❌ Failed to configure WebREPL on board. Check USB connection.${RESET}"
        fi
        ;;

    5)
        # ==========================================
        # ERASE BOARD ONLY
        # ==========================================
        echo ""
        read -p "⚠️ Are you SURE you want to erase your screen? (y/n): " CONFIRM
        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}🧹 Erasing screen flash...${RESET}"
            python3 -m esptool --chip esp32 --port "$PORT" erase_flash
            echo -e "${GREEN}✅ Screen cleared completely!${RESET}"
        else
            echo "Cancelled."
        fi
        ;;
        
    6)
        # ==========================================
        # REBOOT ONLY
        # ==========================================
        echo ""
        echo -e "${CYAN}🔄 Sending reboot signal to $PORT...${RESET}"
        reboot_board
        echo -e "${GREEN}✅ Rebooted! If it stays blank, press the RESET button on the back of the screen.${RESET}"
        ;;
        
    *)
        echo ""
        echo "Goodbye! Have a happy time morphing! 👋"
        exit 0
        ;;
esac

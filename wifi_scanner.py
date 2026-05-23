#!/usr/bin/env python3
import sys
import subprocess
import shlex
import getpass
import ast
import time

# Save the original stdout to print final shell variables for eval redirection
real_stdout = sys.stdout
# Redirect default print and input calls to stderr so they show on terminal
sys.stdout = sys.stderr

# Styling ANSI Escape Sequences
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
MAGENTA = '\033[0;35m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_banner():
    print(f"{MAGENTA}┌──────────────────────────────────────────────────────────┐{RESET}")
    print(f"{MAGENTA}│{RESET}  {CYAN}{BOLD}📶  ESP32 CYD WIFI NETWORK SCANNER                     {RESET}{MAGENTA}│{RESET}")
    print(f"{MAGENTA}└──────────────────────────────────────────────────────────┘{RESET}")

def scan_networks(port):
    print(f"\n{YELLOW}⏳ Scanning for nearby WiFi networks... Please wait...{RESET}")
    
    # Python code to execute on ESP32 MicroPython
    # We active STA interface, scan, and print as a Python list of tuples
    esp32_code = (
        "import network, time; "
        "wlan = network.WLAN(network.STA_IF); "
        "wlan.active(True); "
        "time.sleep(0.5); "
        "nets = wlan.scan(); "
        "print([(n[0].decode('utf-8', 'ignore'), n[3]) for n in nets if n[0]])"
    )
    
    cmd = ["python3", "-m", "mpremote", "connect", port, "exec", esp32_code]
    
    try:
        # Run with a 12-second timeout in case serial is locked/slow
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if result.returncode != 0:
            return None, f"mpremote returned exit code {result.returncode}. Error: {result.stderr.strip()}"
        
        output = result.stdout.strip()
        # Parse the printed Python list
        try:
            # Look for the last line that matches list pattern in case of boot logs
            lines = output.split('\n')
            list_str = ""
            for line in reversed(lines):
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    list_str = line.strip()
                    break
            if not list_str:
                list_str = output
            
            networks_raw = ast.literal_eval(list_str)
            return networks_raw, None
        except Exception as e:
            return None, f"Failed to parse scan output: {e}\nRaw output was:\n{output}"
            
    except subprocess.TimeoutExpired:
        return None, "Scanning timed out (serial port is busy or non-responsive)."
    except Exception as e:
        return None, str(e)

def process_networks(networks_raw):
    # Deduplicate networks keeping the highest signal strength (RSSI closer to 0)
    deduped = {}
    for ssid, rssi in networks_raw:
        ssid = ssid.strip()
        if not ssid:
            continue
        if ssid not in deduped or rssi > deduped[ssid]:
            deduped[ssid] = rssi
            
    # Sort by RSSI descending (strongest signal first)
    sorted_nets = sorted(deduped.items(), key=lambda item: item[1], reverse=True)
    return sorted_nets

def get_signal_emoji_and_desc(rssi):
    if rssi >= -60:
        return f"{GREEN}🟢 Strong{RESET}", f"{GREEN}{rssi} dBm{RESET}"
    elif rssi >= -80:
        return f"{YELLOW}🟡 Medium{RESET}", f"{YELLOW}{rssi} dBm{RESET}"
    else:
        return f"{RED}🔴 Weak  {RESET}", f"{RED}{rssi} dBm{RESET}"

def run_tui(port):
    print_banner()
    
    while True:
        networks_raw, error = scan_networks(port)
        
        if error:
            print(f"\n{RED}⚠️  WiFi Scan Failed!{RESET}")
            print(f"{YELLOW}Reason: {error}{RESET}")
            print(f"\n{CYAN}💡 Falling back to manual configuration...{RESET}\n")
            # Fallback to manual configuration parameters
            return manual_input()
            
        networks = process_networks(networks_raw)
        
        if not networks:
            print(f"\n{YELLOW}⚠️  No WiFi networks found in range!{RESET}")
            print(f"  [R] 🔄  Rescan Networks")
            print(f"  [M] ✏️   Manual SSID Input")
            print(f"  [S] ⏭️   Skip WiFi Setup")
            print("")
            choice = input(f"{BOLD}Select an option [R/M/S]: {RESET}").strip().upper()
            if choice == 'R':
                continue
            elif choice == 'M':
                return manual_input()
            elif choice == 'S':
                return '__SKIP__', '__SKIP__'
            else:
                print(f"{RED}Invalid choice. Defaulting to manual input.{RESET}")
                return manual_input()
        
        print(f"\n{GREEN}✅ Scanned {len(networks)} networks successfully (sorted by signal):{RESET}\n")
        
        # Display table header
        print(f"  {BOLD}{'#':<4} {'Signal':<18} {'RSSI':<10} {'Network Name (SSID)'}{RESET}")
        print(f"  {CYAN}─────────────────────────────────────────────────────────────────{RESET}")
        
        for idx, (ssid, rssi) in enumerate(networks, 1):
            sig_desc, rssi_desc = get_signal_emoji_and_desc(rssi)
            print(f"  [{idx:<2}] {sig_desc:<18} {rssi_desc:<10} {BOLD}{ssid}{RESET}")
            
        print(f"  {CYAN}─────────────────────────────────────────────────────────────────{RESET}")
        print(f"  [R]  🔄  Rescan Networks")
        print(f"  [M]  ✏️   Manual SSID Input")
        print(f"  [S]  ⏭️   Skip WiFi Setup")
        print(f"  {CYAN}─────────────────────────────────────────────────────────────────{RESET}\n")
        
        choice = input(f"{BOLD}Select a network [1-{len(networks)}, R, M, S]: {RESET}").strip()
        
        if choice.upper() == 'R':
            continue
        elif choice.upper() == 'M':
            return manual_input()
        elif choice.upper() == 'S':
            return '__SKIP__', '__SKIP__'
        
        try:
            val = int(choice)
            if 1 <= val <= len(networks):
                selected_ssid = networks[val - 1][0]
                print(f"\n{GREEN}🔒 Selected Network: {BOLD}{selected_ssid}{RESET}")
                password = getpass.getpass(f"🔑 {BOLD}Enter WiFi Password (will be hidden): {RESET}")
                return selected_ssid, password
            else:
                print(f"\n{RED}❌ Invalid number! Please pick a number from the list.{RESET}")
                time.sleep(1.5)
        except ValueError:
            print(f"\n{RED}❌ Invalid selection! Please enter a valid number or option.{RESET}")
            time.sleep(1.5)

def manual_input():
    print(f"{CYAN}✏️  Manual WiFi Configuration{RESET}")
    ssid = input(f"📶 {BOLD}Enter WiFi SSID: {RESET}").strip()
    if not ssid:
        return '__SKIP__', '__SKIP__'
    password = getpass.getpass(f"🔑 {BOLD}Enter WiFi Password (will be hidden): {RESET}")
    return ssid, password

def main():
    if len(sys.argv) < 2:
        # If no port provided, try to discover or fail back to manual
        print(f"{RED}Error: Serial port argument missing.{RESET}", file=sys.stderr)
        ssid, password = manual_input()
    else:
        port = sys.argv[1]
        ssid, password = run_tui(port)
        
    # Output the result formatted securely for shell eval to the real stdout
    real_stdout.write(f"WIFI_SSID={shlex.quote(ssid)}\n")
    real_stdout.write(f"WIFI_PASS={shlex.quote(password)}\n")
    real_stdout.flush()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  WiFi setup cancelled by user. Skipping...{RESET}\n")
        real_stdout.write("WIFI_SSID='__SKIP__'\n")
        real_stdout.write("WIFI_PASS='__SKIP__'\n")
        real_stdout.flush()
        sys.exit(0)


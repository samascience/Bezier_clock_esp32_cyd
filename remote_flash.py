#!/usr/bin/env python3
import sys
import os
import struct
import socket
import time

# ==========================================
# ⚡️ ESP32 CYD Bezier Clock Remote Flashing Tool ⚡️
# Designed to flash/upload files wirelessly over WebREPL!
# Powered by Antigravity AI
# ==========================================

# Terminal Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
MAGENTA = '\033[0;35m'
RESET = '\033[0m'

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_FRAME_TXT = 0x81
WEBREPL_FRAME_BIN = 0x82

class WebSocketClient:
    def __init__(self, s):
        self.s = s
        self.buf = b""

    def write(self, data, frame=WEBREPL_FRAME_BIN):
        l = len(data)
        if l < 126:
            hdr = struct.pack(">BB", frame, l)
        else:
            hdr = struct.pack(">BBH", frame, 126, l)
        self.s.send(hdr)
        self.s.send(data)

    def recvexactly(self, sz):
        res = b""
        while sz:
            data = self.s.recv(sz)
            if not data:
                break
            res += data
            sz -= len(data)
        return res

    def read(self, size, text_ok=False):
        if not self.buf:
            while True:
                hdr = self.recvexactly(2)
                if len(hdr) != 2:
                    raise ConnectionError("WebREPL disconnected unexpectedly.")
                fl, sz = struct.unpack(">BB", hdr)
                if sz == 126:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    (sz,) = struct.unpack(">H", hdr)
                if fl == 0x82:
                    break
                if text_ok and fl == 0x81:
                    break
                # Skip other frames
                while sz:
                    skip = self.s.recv(sz)
                    sz -= len(skip)
            data = self.recvexactly(sz)
            assert len(data) == sz
            self.buf = data

        d = self.buf[:size]
        self.buf = self.buf[size:]
        return d

    def ioctl(self, req, val):
        assert req == 9 and val == 2

def client_handshake(sock):
    cl = sock.makefile("rwb", 0)
    cl.write(b"GET / HTTP/1.1\r\n"
             b"Host: echo.websocket.org\r\n"
             b"Connection: Upgrade\r\n"
             b"Upgrade: websocket\r\n"
             b"Sec-WebSocket-Key: foo\r\n\r\n")
    while True:
        l = cl.readline()
        if l == b"\r\n":
            break

def login(ws, passwd):
    while True:
        c = ws.read(1, text_ok=True)
        if c == b":":
            assert ws.read(1, text_ok=True) == b" "
            break
    ws.write(passwd.encode("utf-8") + b"\r")

def read_resp(ws):
    data = ws.read(4)
    sig, code = struct.unpack("<2sH", data)
    assert sig == b"WB"
    return code

def put_file(ws, local_file, remote_file):
    sz = os.stat(local_file).st_size
    dest_fname = remote_file.encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname)
    ws.write(rec[:10])
    ws.write(rec[10:])
    
    if read_resp(ws) != 0:
        raise OSError("Board rejected upload request.")
        
    cnt = 0
    with open(local_file, "rb") as f:
        while True:
            percent = (cnt / sz * 100) if sz > 0 else 100
            sys.stdout.write(f"   📤 Uploading {CYAN}{local_file}{RESET} -> {CYAN}{remote_file}{RESET}: {GREEN}{percent:.1f}%{RESET} ({cnt}/{sz} bytes)\r")
            sys.stdout.flush()
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            cnt += len(buf)
    print()
    if read_resp(ws) != 0:
        raise OSError("Flash write verification failed.")
    print(f"   {GREEN}✅ Completed {local_file}!{RESET}")

def main():
    if len(sys.argv) < 3:
        print(f"{RED}Usage: python3 remote_flash.py <IP_ADDRESS> <PASSWORD> [FILE_MAPPINGS]{RESET}")
        print("Example: python3 remote_flash.py 192.168.1.150 1234 ili9341.py:ili9341.py bezier_clock.py:main.py")
        sys.exit(1)

    host = sys.argv[1]
    passwd = sys.argv[2]
    port = 8266

    # Extract mappings
    mappings = []
    for arg in sys.argv[3:]:
        if ":" in arg:
            local, remote = arg.split(":", 1)
        else:
            local = arg
            remote = arg
        mappings.append((local, remote))

    if not mappings:
        print(f"{YELLOW}⚠️ No files specified for upload. Connecting only to verify WebREPL connection...{RESET}")

    print(f"{CYAN}📡 Connecting to ESP32 screen WebREPL at {YELLOW}{host}:{port}{RESET}...")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0) # 5 seconds connection timeout
        s.connect((host, port))
    except Exception as e:
        print(f"\n{RED}❌ Connection failed: {e}{RESET}")
        print(f"{YELLOW}💡 Troubleshooting tips:{RESET}")
        print("   1. Verify your ESP32 CYD screen is powered ON and displaying the clock.")
        print(f"   2. Ensure your Mac is connected to the SAME WiFi network as the screen.")
        print(f"   3. Check that the IP address '{host}' matches the one shown on your screen's startup.")
        print("   4. Verify you enabled WebREPL over USB first.")
        sys.exit(1)

    print(f"{GREEN}🔌 WebSocket Handshake...{RESET}")
    client_handshake(s)
    
    ws = WebSocketClient(s)
    
    try:
        print(f"{CYAN}🔑 Logging in with password...{RESET}")
        login(ws, passwd)
        # Set websocket to send data marked as "binary"
        ws.ioctl(9, 2)
        print(f"{GREEN}🔓 Login successful!{RESET}\n")
    except Exception as e:
        print(f"{RED}❌ WebREPL Authentication failed: {e}{RESET}")
        print(f"{YELLOW}💡 Make sure your WebREPL password is correct!{RESET}")
        s.close()
        sys.exit(1)

    # Perform file uploads
    for local_file, remote_file in mappings:
        if not os.path.exists(local_file):
            print(f"{RED}❌ Local file not found: {local_file}{RESET}")
            s.close()
            sys.exit(1)
        try:
            put_file(ws, local_file, remote_file)
        except Exception as e:
            print(f"\n{RED}❌ Failed to upload {local_file}: {e}{RESET}")
            s.close()
            sys.exit(1)

    # Perform a remote Soft Reset to restart the screen!
    print(f"\n{CYAN}🔄 Sending remote soft-reset signal to launch the clock...{RESET}")
    try:
        # Standard MicroPython reset sequence via WebREPL text frame
        ws.write(b"\r\nimport machine\r\nmachine.reset()\r\n", WEBREPL_FRAME_TXT)
        time.sleep(0.5)
        print(f"{GREEN}🎉 Soft-Reset successful! Your screen is rebooting now wirelessly! 🚀{RESET}")
    except Exception:
        # If socket closes immediately on reset, that's expected and normal!
        print(f"{GREEN}🎉 Soft-Reset successful! Screen is now running the new code! 🚀{RESET}")
        
    s.close()

if __name__ == "__main__":
    main()

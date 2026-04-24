import threading
import time
import shutil
import os
import socket
import webbrowser
import uvicorn

BUILD_PATH  = r"C:\Users\STUDY\Desktop\surveillance-dashboard\build"
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(BUILD_PATH):
    if os.path.exists(STATIC_PATH):
        shutil.rmtree(STATIC_PATH)
    shutil.copytree(BUILD_PATH, STATIC_PATH)
    print("Dashboard build ready.")
else:
    print("WARNING: React build not found at:", BUILD_PATH)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def start_server():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="warning")

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

time.sleep(2)

local_ip = get_local_ip()

print("\n" + "="*55)
print("  SENTINEL BORDER SURVEILLANCE SYSTEM")
print("="*55)
print(f"  Desktop  : http://localhost:8000")
print(f"  Mobile   : http://{local_ip}:8000/mobile")
print("="*55)
print("\n  MOBILE SETUP:")
print(f"  1. Connect your phone to the SAME WiFi")
print(f"  2. Open browser on phone")
print(f"  3. Go to: http://{local_ip}:8000/mobile")
print(f"  4. Add to home screen for app-like experience")
print("="*55 + "\n")

webbrowser.open("http://localhost:8000")

exec(open(os.path.join(os.path.dirname(__file__), "detect.py"),
          encoding='utf-8').read())

#!/usr/bin/env python3
"""
🎹 Cubase AI Studio - All-in-One Launcher
==========================================

הרץ את זה וכל השירותים יעלו אוטומטית!
"""

import subprocess
import sys
import time
import webbrowser
import threading
from pathlib import Path

ROOT = Path(__file__).parent

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎹  C U B A S E   A I   S T U D I O  🎹                ║
║                                                              ║
║     העוזר החכם להפקת מוזיקה                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def start_service(name, command, port):
    """Start a service in a subprocess."""
    print(f"  🚀 Starting {name} on port {port}...")
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    return process

def check_dependencies():
    """Check if all dependencies are installed."""
    print("📦 Checking dependencies...")
    try:
        import flask
        import google.generativeai
        print("  ✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def main():
    print_banner()

    if not check_dependencies():
        sys.exit(1)

    print("\n🔧 Starting services...\n")

    # Start main web app
    web_app = start_service(
        "Web App",
        f"{sys.executable} app.py",
        5001
    )

    # Start bridge server
    bridge = start_service(
        "Bridge Server",
        f"{sys.executable} cubase_bridge/bridge_server.py",
        5002
    )

    # Wait for services to start
    time.sleep(2)

    print("""
╔══════════════════════════════════════════════════════════════╗
║  ✅ All services started!                                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🌐 Web Interface:    http://127.0.0.1:5001                 ║
║  💬 Chat Mode:        http://127.0.0.1:5001/chat            ║
║  🌉 Bridge Server:    http://127.0.0.1:5002                 ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  📋 Quick Commands:                                          ║
║     Ctrl+C  - Stop all services                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Open browser
    def open_browser():
        time.sleep(1)
        webbrowser.open('http://127.0.0.1:5001/chat')

    threading.Thread(target=open_browser, daemon=True).start()

    # Keep running until Ctrl+C
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            if web_app.poll() is not None:
                print("❌ Web app crashed!")
                break
            if bridge.poll() is not None:
                print("❌ Bridge server crashed!")
                break
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        web_app.terminate()
        bridge.terminate()
        print("✅ All services stopped. Goodbye!")

if __name__ == "__main__":
    main()

"""
Build script to create standalone EXE for Cubase Assistant
Run this script to create a Windows executable.
"""

import os
import sys
import subprocess

def build_exe():
    """Build the executable using PyInstaller."""
    print("🔨 Building Cubase Assistant EXE...")
    print("=" * 50)

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',  # Single EXE file
        '--windowed',  # No console window
        '--name', 'CubaseAssistant',
        '--icon', 'icon.ico',  # Add an icon if available
        '--add-data', 'templates;templates',  # Include templates for Flask
        '--hidden-import', 'pystray',
        '--hidden-import', 'PIL',
        '--hidden-import', 'keyboard',
        'desktop_app_advanced.py'
    ]

    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Build successful!")
        print(f"📦 EXE created in: dist/CubaseAssistant.exe")
        print("\nNote: Make sure the Flask server (app.py) is running before using the desktop app!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(e.stderr)
        sys.exit(1)

    except FileNotFoundError:
        print("❌ PyInstaller not found. Install it with:")
        print("   pip install pyinstaller")
        sys.exit(1)


def build_simple():
    """Build a simpler version without external dependencies."""
    print("🔨 Building Simple Desktop App...")
    print("=" * 50)

    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'CubaseAssistantSimple',
        'desktop_app.py'
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Simple build successful!")
        print(f"📦 EXE created in: dist/CubaseAssistantSimple.exe")

    except Exception as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Cubase Assistant - Build Tool")
    print("=" * 50)
    print("1. Build Advanced (with hotkeys, tray, monitoring)")
    print("2. Build Simple (basic GUI only)")
    print()

    choice = input("Choose (1 or 2): ").strip()

    if choice == "1":
        build_exe()
    elif choice == "2":
        build_simple()
    else:
        print("Invalid choice!")
        sys.exit(1)

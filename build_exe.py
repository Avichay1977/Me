#!/usr/bin/env python3
"""
Build Executable for Cubase AI Studio
======================================

הרץ את הסקריפט הזה כדי ליצור קובץ EXE:
    python build_exe.py

דרישות:
    pip install pyinstaller

הפלט יהיה בתיקייה: dist/CubaseAIStudio/
"""

import subprocess
import sys
import os
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller."""
    print("📦 Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    """Build the executable."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🔨 Building Cubase AI Studio Executable                  ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Check/install PyInstaller
    if not check_pyinstaller():
        install_pyinstaller()

    root = Path(__file__).parent

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=CubaseAIStudio",
        "--onedir",  # Create a directory with all files (more reliable)
        "--windowed",  # No console window (for GUI app)
        "--add-data", f"templates{os.pathsep}templates",
        "--add-data", f"cubase_bridge{os.pathsep}cubase_bridge",
        "--add-data", f"macros{os.pathsep}macros",
        "--add-data", f".env{os.pathsep}." if (root / ".env").exists() else "",
        "--hidden-import=flask",
        "--hidden-import=google.generativeai",
        "--hidden-import=google.ai.generativelanguage",
        "--hidden-import=google.auth",
        "--hidden-import=google.api_core",
        "--hidden-import=dotenv",
        "--hidden-import=flask_cors",
        "--icon=NONE",  # No icon (you can add one later)
        "--clean",
        "start.py"
    ]

    # Remove empty strings
    cmd = [c for c in cmd if c]

    print("🔧 Running PyInstaller...")
    print(f"   Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.check_call(cmd, cwd=root)
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ✅ Build completed successfully!                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Output: dist/CubaseAIStudio/                            ║
║  🚀 Run:    dist/CubaseAIStudio/CubaseAIStudio.exe          ║
║                                                              ║
║  📋 To distribute:                                           ║
║     Zip the entire 'dist/CubaseAIStudio' folder             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()

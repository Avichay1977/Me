@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     🔨 Building Cubase AI Studio Executable                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo 🔧 Building executable...
echo.

REM Build with PyInstaller
pyinstaller ^
    --name=CubaseAIStudio ^
    --onedir ^
    --windowed ^
    --add-data "templates;templates" ^
    --add-data "cubase_bridge;cubase_bridge" ^
    --add-data "macros;macros" ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=google.generativeai ^
    --hidden-import=google.ai.generativelanguage ^
    --hidden-import=google.auth ^
    --hidden-import=google.api_core ^
    --hidden-import=dotenv ^
    --clean ^
    launcher.py

if errorlevel 1 (
    echo.
    echo ❌ Build failed!
    pause
    exit /b 1
)

REM Copy .env file if exists
if exist .env (
    echo 📄 Copying .env file...
    copy .env dist\CubaseAIStudio\
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  ✅ Build completed successfully!                            ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  📁 Output: dist\CubaseAIStudio\                            ║
echo ║  🚀 Run:    dist\CubaseAIStudio\CubaseAIStudio.exe          ║
echo ║                                                              ║
echo ║  ⚠️  Don't forget to add your .env file with API key!       ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

pause

@echo off
echo ========================================
echo Cubase Assistant - Windows EXE Builder
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/4] Installing required packages...
pip install --upgrade pip
pip install pyinstaller keyboard pystray Pillow pytesseract requests Flask google-generativeai python-dotenv

echo.
echo [3/4] Building Advanced Desktop App (with all features)...
pyinstaller --onefile --windowed --name "CubaseAssistant" --icon=NONE ^
    --add-data "templates;templates" ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=keyboard ^
    --hidden-import=google.generativeai ^
    --hidden-import=learning_system ^
    desktop_app_advanced.py

echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo SUCCESS! Your EXE is ready:
echo dist\CubaseAssistant.exe
echo ========================================
echo.
echo IMPORTANT NOTES:
echo 1. Make sure to run app.py (Flask server) before using the desktop app
echo 2. Keep the .env file with your Google API key in the same folder
echo 3. The EXE is portable - you can move it anywhere
echo.
pause

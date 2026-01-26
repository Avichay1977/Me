@echo off
echo ========================================
echo Building SIMPLE version (no hotkeys/tray)
echo ========================================
echo.

pip install pyinstaller requests Flask google-generativeai python-dotenv

pyinstaller --onefile --windowed --name "CubaseAssistantSimple" ^
    --add-data "templates;templates" ^
    desktop_app.py

echo.
echo ========================================
echo Simple version built!
echo dist\CubaseAssistantSimple.exe
echo ========================================
pause

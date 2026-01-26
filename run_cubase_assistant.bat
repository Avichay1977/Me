@echo off
chcp 65001 >nul
title Cubase Assistant - Launcher

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║          🎵 Cubase Assistant - מפעיל אוטומטי 🎵        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if EXE exists
if not exist "dist\CubaseAssistant.exe" (
    echo ❌ לא נמצא קובץ EXE!
    echo.
    echo אנא הרץ קודם את: install_and_build.bat
    echo.
    pause
    exit /b 1
)

REM Check if .env exists and has API key
if not exist ".env" (
    echo ❌ לא נמצא קובץ .env!
    echo.
    echo נא ליצור קובץ .env עם:
    echo GOOGLE_API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

REM Check if API key is set
findstr /C:"your_api_key_here" .env >nul
if %errorlevel% equ 0 (
    echo ⚠️  נראה שלא הגדרת את ה-API Key!
    echo.
    echo ערוך את קובץ .env והכנס את ה-Google API Key שלך
    echo קבל API Key: https://makersuite.google.com/app/apikey
    echo.
    echo האם להמשיך בכל זאת? (Y/N)
    choice /C YN /N
    if errorlevel 2 exit /b 0
)

echo ✅ בודק קובץ .env...
echo ✅ בודק EXE...
echo.
echo 🚀 מפעיל את Cubase Assistant...
echo.

REM Start Flask server in background
echo [1/2] מפעיל שרת Flask...
start "Cubase Assistant Server" /MIN python app.py

REM Wait a bit for server to start
timeout /t 3 /nobreak >nul

REM Start the desktop app
echo [2/2] מפעיל אפליקציה...
start "" "dist\CubaseAssistant.exe"

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                  ✅ האפליקציה פועלת!                  ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 🌐 שרת Flask: http://127.0.0.1:8080
echo 🖥️  Desktop App: dist\CubaseAssistant.exe
echo.
echo 🎹 קיצורי מקלדת:
echo    • Ctrl+Shift+C - הצג/הסתר אפליקציה
echo    • Ctrl+S - שמור סקריפט
echo    • Escape - סגור חלון
echo.
echo ⚠️  כדי לסגור הכל, סגור חלון זה או לחץ Ctrl+C
echo.
pause

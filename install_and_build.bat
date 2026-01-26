@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     🎵 Cubase Assistant - התקנה אוטומטית מלאה 🎵      ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
echo [שלב 1/5] בודק התקנת Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python לא מותקן!
    echo.
    echo 📥 הורד Python מכאן:
    echo https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
    echo.
    echo ⚠️  חשוב: בהתקנה, סמן ✓ "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo ✅ Python מותקן!

REM Upgrade pip
echo.
echo [שלב 2/5] משדרג pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip מעודכן!

REM Install all dependencies
echo.
echo [שלב 3/5] מתקין חבילות נדרשות (זה ייקח דקה-שתיים)...
pip install --upgrade pyinstaller keyboard pystray Pillow pytesseract requests Flask google-generativeai python-dotenv --quiet
if %errorlevel% neq 0 (
    echo ❌ שגיאה בהתקנת חבילות
    pause
    exit /b 1
)
echo ✅ כל החבילות הותקנו!

REM Create .env file if not exists
echo.
echo [שלב 4/5] בודק קובץ .env...
if not exist ".env" (
    echo GOOGLE_API_KEY=your_api_key_here > .env
    echo ⚠️  נוצר קובץ .env - אנא הוסף את ה-API Key שלך!
    echo    ערוך את .env והחלף את your_api_key_here ב-API Key אמיתי
    echo    קבל API Key מכאן: https://makersuite.google.com/app/apikey
) else (
    echo ✅ קובץ .env קיים!
)

REM Build the EXE
echo.
echo [שלב 5/5] בונה את ה-EXE (זה ייקח 2-5 דקות)... ☕
echo.
pyinstaller --onefile --windowed --name "CubaseAssistant" ^
    --add-data "templates;templates" ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=keyboard ^
    --hidden-import=google.generativeai ^
    --hidden-import=learning_system ^
    desktop_app_advanced.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ שגיאה בבניית ה-EXE
    pause
    exit /b 1
)

REM Success!
echo.
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║              ✨ ההתקנה הושלמה בהצלחה! ✨              ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📦 קובץ ה-EXE שלך מוכן:
echo    dist\CubaseAssistant.exe
echo.
echo 📋 כדי להשתמש באפליקציה:
echo.
echo    1️⃣  הרץ את השרת:
echo       python app.py
echo.
echo    2️⃣  הרץ את ה-EXE:
echo       dist\CubaseAssistant.exe
echo.
echo 🎹 קיצורי מקלדת:
echo    • Ctrl+Shift+C - הצג/הסתר
echo    • Ctrl+S - שמור סקריפט
echo    • Escape - סגור
echo.
echo 🔑 אל תשכח להוסיף את ה-Google API Key לקובץ .env!
echo.
pause

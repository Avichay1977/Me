# 🔨 הוראות בניית EXE - Cubase Assistant

## דרישות מקדימות

1. **מחשב Windows** (Windows 10/11)
2. **Python 3.8 ומעלה** - [הורד כאן](https://www.python.org/downloads/)
3. **חיבור אינטרנט** לשליפת חבילות

---

## שיטה 1: בניה אוטומטית (הכי פשוט!)

### צעדים:

1. **העתק את כל הקבצים** למחשב Windows שלך

2. **לחץ פעמיים** על אחד מהקבצים:
   - `build_windows.bat` - גרסה מלאה עם כל התכונות
   - `build_simple.bat` - גרסה פשוטה בלי Global Hotkeys

3. **המתן** - התהליך לוקח 2-5 דקות

4. **מצא את ה-EXE** בתיקייה `dist/`

✅ זהו! ה-EXE מוכן!

---

## שיטה 2: בניה ידנית

### 1. פתח Command Prompt (CMD)

לחץ `Win + R`, הקלד `cmd`, Enter

### 2. נווט לתיקיית הפרויקט

```cmd
cd C:\path\to\your\project
```

### 3. התקן חבילות

```cmd
pip install pyinstaller keyboard pystray Pillow pytesseract requests Flask google-generativeai python-dotenv
```

### 4. בנה את ה-EXE

**גרסה מלאה:**
```cmd
pyinstaller --onefile --windowed --name "CubaseAssistant" --add-data "templates;templates" desktop_app_advanced.py
```

**גרסה פשוטה:**
```cmd
pyinstaller --onefile --windowed --name "CubaseAssistantSimple" desktop_app.py
```

### 5. מצא את ה-EXE

הקובץ יהיה ב: `dist\CubaseAssistant.exe`

---

## שיטה 3: דרך הסקריפט Python

```cmd
python build_exe.py
```

בחר אפשרות 1 או 2

---

## בעיות נפוצות ופתרונות

### ❌ "Python is not recognized"
**פתרון:** התקן Python מחדש וסמן "Add Python to PATH"

### ❌ "pip is not recognized"
**פתרון:**
```cmd
python -m pip install --upgrade pip
```

### ❌ "ModuleNotFoundError"
**פתרון:** התקן את החבילה החסרה:
```cmd
pip install [package-name]
```

### ❌ ה-EXE לא פותח
**פתרון:** בדוק Windows Defender - אולי חסם את הקובץ

---

## הרצת ה-EXE

### דרישות:

1. **Flask Server חייב לרוץ:**
   ```cmd
   python app.py
   ```

2. **קובץ .env** עם ה-API Key חייב להיות באותה תיקייה

### שימוש:

1. **הרץ** את `app.py` בטרמינל
2. **לחץ פעמיים** על `CubaseAssistant.exe`
3. **השתמש** באפליקציה!

---

## קיצורי מקלדת

- `Ctrl+Shift+C` - הצג/הסתר את החלון
- `Enter` - צור סקריפט
- `Escape` - סגור חלון

---

## אופטימיזציות נוספות

### הקטנת גודל ה-EXE

הוסף flags ל-PyInstaller:
```cmd
--exclude-module matplotlib --exclude-module numpy
```

### הוספת אייקון

1. צור קובץ `icon.ico`
2. הוסף: `--icon=icon.ico`

### קומפילציה ללא console

כבר כלול: `--windowed`

---

## קבצים שצריך להיות לצד ה-EXE

```
CubaseAssistant.exe
.env (עם GOOGLE_API_KEY)
templates/ (רק אם אתה רוצה גם Web UI)
```

**הערה:** ה-EXE עצמאי ולא צריך Python מותקן במחשב היעד!

---

## גרסאות EXE

| גרסה | גודל | תכונות | מומלץ ל |
|------|------|---------|---------|
| CubaseAssistant.exe | ~50MB | הכל | משתמשים מתקדמים |
| CubaseAssistantSimple.exe | ~30MB | בסיסי | משתמשים רגילים |

---

## תמיכה טכנית

אם יש בעיות, בדוק:
1. ✅ Python מותקן?
2. ✅ כל החבילות הותקנו?
3. ✅ Flask Server רץ?
4. ✅ .env עם API Key?
5. ✅ Windows Defender לא חוסם?

---

**🎉 בהצלחה! תהנה מהאפליקציה!**

# 🚀 התקנה מהירה על Windows 11

## שלב 1: הורד את הפרויקט

```cmd
git clone <repository-url>
cd Me
```

או אם יש לך כבר את הקבצים - פשוט פתח את התיקייה.

## שלב 2: צור EXE בקליק אחד! ⚡

**לחץ פעמיים על:** `build_windows.bat`

זהו! ⏱️ 2-5 דקות ויהיה לך:
```
dist\CubaseAssistant.exe
```

---

## אם אין לך Python מותקן:

### הורד Python 3.11:
https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe

**חשוב:** ☑️ סמן "Add Python to PATH" בהתקנה!

---

## מה קורה בבניית ה-EXE?

1. ✅ בודק Python
2. 📦 מתקין חבילות (pyinstaller, flask, וכו')
3. 🔨 בונה את ה-EXE
4. ✨ מוכן!

---

## הרצת האפליקציה

### שלב א': הפעל את השרת
```cmd
python app.py
```

השרת רץ על: http://127.0.0.1:8080

### שלב ב': הרץ את ה-EXE
לחץ פעמיים על: `dist\CubaseAssistant.exe`

---

## קיצורי מקלדת 🎹

- `Ctrl+Shift+C` - הצג/הסתר חלון
- `Ctrl+S` - שמור סקריפט
- `Escape` - סגור חלון

---

## קבצים נדרשים

```
📁 dist/
  📄 CubaseAssistant.exe  ← זה ה-EXE שלך!
📄 .env                   ← עם GOOGLE_API_KEY
📄 app.py                 ← השרת (צריך לרוץ)
```

---

## בעיות?

### ❌ "Python is not recognized"
**פתרון:** התקן Python עם "Add to PATH"

### ❌ Windows Defender חוסם
**פתרון:** לחץ "More info" → "Run anyway"

### ❌ ה-EXE לא מתחבר לשרת
**פתרון:** וודא ש-`python app.py` רץ!

---

## API Key 🔑

צור קובץ `.env` עם:
```
GOOGLE_API_KEY=your_api_key_here
```

קבל API Key: https://makersuite.google.com/app/apikey

---

**🎉 זהו! תהנה!**

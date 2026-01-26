# 🎵 Cubase Assistant - Windows 11 Installation Guide

## 🚀 התקנה בקליק אחד (הדרך הכי פשוטה!)

### שלב 1: הורד את הפרויקט
```cmd
git clone <your-repository-url>
cd Me
```

### שלב 2: התקן ובנה
**לחץ פעמיים על:** `install_and_build.bat`

זהו! ⏱️ 3-7 דקות והאפליקציה מוכנה!

---

## 🎯 הפעלה מהירה

**לחץ פעמיים על:** `run_cubase_assistant.bat`

הסקריפט יפעיל אוטומטית:
- ✅ שרת Flask (backend)
- ✅ Desktop Application (GUI)

---

## 📋 מה צריך לפני שמתחילים?

### 1️⃣ Python 3.11
**הורד מכאן:** https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe

**חשוב ביותר:** ☑️ סמן "Add Python to PATH" בהתקנה!

### 2️⃣ Google Gemini API Key
1. גש ל: https://makersuite.google.com/app/apikey
2. לחץ "Create API Key"
3. העתק את ה-Key

### 3️⃣ קובץ .env
צור קובץ בשם `.env` (בלי שם, רק סיומת) עם:
```
GOOGLE_API_KEY=AIzaSy... (ה-Key שלך)
```

---

## 📁 מבנה הקבצים

```
Me/
├── 📄 install_and_build.bat    ← התקנה אוטומטית
├── 📄 run_cubase_assistant.bat ← הפעלה מהירה
├── 📄 build_windows.bat        ← בניית גרסה מלאה
├── 📄 build_simple.bat         ← בניית גרסה פשוטה
├── 📄 app.py                   ← שרת Flask
├── 📄 desktop_app_advanced.py  ← Desktop App מתקדם
├── 📄 desktop_app.py           ← Desktop App פשוט
├── 📄 learning_system.py       ← מערכת למידה AI
├── 📄 .env                     ← API Key (תיצור)
├── 📁 templates/               ← Web UI
└── 📁 dist/
    └── 📄 CubaseAssistant.exe  ← זה ה-EXE!
```

---

## 🎹 שימוש באפליקציה

### Desktop App (מומלץ!)

**קיצורי מקלדת:**
- `Ctrl+Shift+C` - הצג/הסתר חלון (גם כשהאפליקציה מוקטנת!)
- `Ctrl+S` - שמור סקריפט שנוצר
- `Escape` - סגור חלון
- **Click ימני על System Tray** - תפריט מלא

**תכונות:**
- ✨ Always on top - תמיד מעל כל החלונות
- 🎤 זיהוי קולי בעברית
- 🧠 למידה חכמה של ההרגלים שלך
- 👀 ניטור מסך (אופציונלי)
- 📊 סטטיסטיקות שימוש

### Web Interface

פתח דפדפן וגש ל: http://127.0.0.1:8080

**תכונות Web:**
- 🎤 אסיסטנט קולי
- 📊 פאנל למידה עם הצעות חכמות
- 💾 היסטוריית בקשות
- ⚡ מטמון תגובות (מהיר יותר!)

---

## 🔧 בעיות נפוצות ופתרונות

### ❌ "Python is not recognized"
**פתרון:**
1. הסר התקנת Python
2. התקן מחדש עם ✓ "Add Python to PATH"
3. אתחל את המחשב

### ❌ "ModuleNotFoundError: No module named 'flask'"
**פתרון:**
```cmd
pip install Flask google-generativeai python-dotenv requests
```

### ❌ Windows Defender חוסם את ה-EXE
**פתרון:**
1. לחץ "More info"
2. לחץ "Run anyway"

זה קורה כי ה-EXE נוצר על המחשב שלך ולא נחתם דיגיטלית.

### ❌ ה-Desktop App לא מתחבר לשרת
**פתרון:**
1. וודא ש-`python app.py` רץ (או השתמש ב-`run_cubase_assistant.bat`)
2. בדוק ש-port 8080 פנוי
3. נסה לגשת ל-http://127.0.0.1:8080 בדפדפן

### ❌ "Failed to generate content"
**פתרון:**
1. בדוק שה-API Key תקין בקובץ `.env`
2. ודא שיש חיבור לאינטרנט
3. בדוק מכסת API ב-Google Cloud Console

### ❌ הזיהוי הקולי לא עובד
**פתרון:**
1. השתמש ב-Chrome/Edge (Firefox לא תומך)
2. אשר הרשאות מיקרופון
3. בדוק שהמיקרופון עובד

---

## 🎨 התאמה אישית

### שינוי קיצור מקלדת גלובלי
ערוך `desktop_app_advanced.py` שורה ~180:
```python
keyboard.add_hotkey('ctrl+shift+c', self.toggle_window)
# שנה ל:
keyboard.add_hotkey('ctrl+alt+c', self.toggle_window)
```

### שינוי פורט שרת
ערוך `app.py` שורה אחרונה:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
# שנה ל:
app.run(debug=True, host='0.0.0.0', port=5000)
```

### שינוי שקיפות חלון
ערוך `desktop_app_advanced.py` שורה ~75:
```python
self.root.attributes('-alpha', 0.95)  # 0.0-1.0
```

---

## 🧠 מערכת הלמידה

האפליקציה לומדת את ההרגלים שלך:

**מה היא לומדת?**
- ✅ פעולות נפוצות (צור, הוסף, מחק...)
- ✅ מספרים מועדפים (כמה ערוצים אתה יוצר?)
- ✅ תבניות שחוזרות

**איפה הנתונים?**
- 📁 `user_learning.db` - SQLite מקומי
- 🔒 לא נשלח לשום מקום!
- 🗑️ מחק את הקובץ לאיפוס

**הצעות חכמות:**
- לחץ על הצעה בפאנל הלמידה
- ההצעות משתפרות עם הזמן
- אחוז ביטחון מוצג לכל הצעה

---

## 🔐 אבטחה ופרטיות

- ✅ כל הנתונים נשמרים **מקומית** על המחשב שלך
- ✅ רק הפרומפט נשלח ל-Google Gemini API
- ✅ אין שרתים חיצוניים
- ✅ קוד פתוח - אתה יכול לראות בדיוק מה קורה

**המלצות:**
- שמור את ה-API Key במקום בטוח
- אל תשתף את קובץ `.env`
- אפשר לבדוק את הקוד לפני השימוש

---

## 📊 ביצועים

**Desktop App:**
- גודל: ~50-70MB
- זיכרון: ~150MB RAM
- CPU: זניח (עד שמבצעים פעולה)

**Flask Server:**
- זיכרון: ~80MB RAM
- CPU: זניח

**מטמון:**
- תגובות זהות נשמרות 60 דקות
- חוסך זמן וכסף API

---

## 🆘 תמיכה טכנית

אם משהו לא עובד:

1. ✅ Python 3.8+ מותקן?
2. ✅ "Add to PATH" נבחר בהתקנה?
3. ✅ כל החבילות הותקנו? (`pip list`)
4. ✅ קובץ `.env` עם API Key קיים?
5. ✅ שרת Flask רץ? (בדוק ב-http://127.0.0.1:8080)
6. ✅ Firewall/Antivirus לא חוסם?

---

## 🚀 גרסאות

| גרסה | גודל | תכונות | מומלץ ל |
|------|------|---------|---------|
| **CubaseAssistant.exe** | ~60MB | הכל (hotkeys, tray, למידה, מסך) | מתקדמים |
| **CubaseAssistantSimple.exe** | ~35MB | GUI בסיסי בלבד | מתחילים |

בנה את הגרסה הפשוטה:
```cmd
build_simple.bat
```

---

## 🎯 Cubase Remote Control API

**הערה:** כרגע האינטגרציה עם Cubase היא דרך העתקת הקוד שנוצר.

**עבודה עתידית:**
- אינטגרציה ישירה עם Cubase MIDI Remote API
- הפעלת סקריפטים אוטומטית
- Real-time feedback מ-Cubase

---

## 📝 Changelog

### v1.0 (2026-01)
- ✨ Desktop App עם Always on Top
- ✨ Global Hotkeys (Ctrl+Shift+C)
- ✨ System Tray Integration
- ✨ מערכת למידה AI
- ✨ זיהוי קולי בעברית
- ✨ ניטור מסך אופציונלי
- ✨ Web Interface מלא
- ✨ Response Caching
- ✨ Rate Limiting
- ✨ Retry Logic

---

## 📄 רישיון

פרויקט זה ליצירת סקריפטים ל-Cubase בעזרת AI.

**חופשי לשימוש אישי!**

---

## 🙏 תודות

- **Google Gemini AI** - מנוע ה-AI
- **Flask** - Web Framework
- **PyInstaller** - יצירת EXE
- **tkinter** - GUI Framework

---

**🎉 בהצלחה עם Cubase! 🎵**

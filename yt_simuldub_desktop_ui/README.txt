# YT SimulDub HE (Desktop UI Demo)

דמו שולחני משופר עם ממשק:
- Start/Stop
- שליטת Ducking
- בחירת קול עברית (אם מותקן בדפדפן/מערכת)

## התקנה
1. Chrome/Edge → `chrome://extensions/` → הפעל Developer mode.
2. `Load unpacked` → בחר את התיקייה `yt_simuldub_desktop_ui`.
3. פתח סרטון ביוטיוב → לחץ על אייקון התוסף → Start.
4. וודא שאתה שומע משפט בדיקה בעברית והווליום של הווידאו ירד.

> הערה: זהו דמו מקומי בלבד (אין ASR/תרגום). זה בסיס נקי להרחבה.

## הרחבה בהמשך
- הוסף נקודות חיבור ל-ASR/Translate/TTS בענן דרך offscreen.js (WebSocket/HTTP).
- נהל מפתחות API בצורה בטוחה (אל תשמור ישירות בקוד).

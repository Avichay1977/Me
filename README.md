# Cubase Script Assistant

This application is a web-based tool that uses the Google Gemini AI model to translate natural language prompts into executable JavaScript for the Cubase Scripting API.

---

## Features / תכונות

### 🔄 Retry Logic
The application automatically retries failed API requests with exponential backoff (1s, 2s, 4s) to handle temporary network issues.

### 💾 Response Caching
Identical requests are cached for 60 minutes to improve response time and reduce API usage.

### 🚦 Rate Limiting
Protected against API quota exhaustion with a limit of 10 requests per minute per user.

### ✅ Enhanced Input Validation
- Prevents empty requests
- Limits prompt length to 1000 characters
- Validates request format

### 📝 Improved Error Messages
User-friendly Hebrew error messages for common issues:
- Invalid API key
- Quota exceeded
- Network errors
- Timeout errors

---

## הסבר על הקוד (Hebrew Code Explanation)

תיאור כללי של הקוד

הקוד יוצר שרת אינטרנט (backend) באמצעות פריימוורק בשם Flask. מטרתו המרכזית של השרת היא לשמש כ"מתורגמן" בין משתמש אנושי לבין ה-API של תוכנת המוזיקה Cubase. השרת מקבל פקודות בשפה טבעית (עברית, לפי ההנחיות), שולח אותן למודל השפה המתקדם Gemini של גוגל, ומקבל בחזרה קוד JavaScript מדויק שניתן להריץ ישירות בקיובייס כדי לבצע את הפקודה.

### פירוט רכיבי הקוד המרכזיים

#### 1. ייבוא ספריות והגדרות ראשוניות

- **flask, os, google.generativeai, dotenv, logging**: אלו הן הספריות שהקוד משתמש בהן.
- **Flask**: לבניית שרת האינטרנט.
- **google.generativeai**: לתקשורת עם ה-API של Gemini.
- **dotenv**: לטעינת משתני סביבה (כמו מפתח ה-API) מקובץ `.env` באופן מאובטח.
- **logging**: לרישום הודעות על פעילות השרת, מה שעוזר מאוד באיתור תקלות.
- `app = Flask(__name__)`: שורת הקוד הזו מאתחלת את אפליקציית השרת של Flask.

#### 2. הגדרת ה-API של Gemini

- `load_dotenv()`: טוען את המידע הרגיש (מפתח ה-API) מקובץ `.env` שנמצא בתיקיית הפרויקט. זוהי פרקטיקה מומלצת כדי לא לחשוף מפתחות בקוד המקור.
- `GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')`: קורא את מפתח ה-API מתוך משתני הסביבה.
- `genai.configure(api_key=GOOGLE_API_KEY)`: מגדיר את ספריית Gemini כך שתשתמש במפתח ה-API שלך בכל פנייה לשירות של גוגל.

#### 3. הנחיית המערכת (System Prompt)

זהו החלק החשוב ביותר באינטראקציה עם מודל השפה. הוא מגדיר את "האישיות" והחוקים שלפיהם המודל חייב לפעול.

- **התפקיד**: "אתה עוזר הפקה וירטואלי מומחה לתוכנת Cubase". זה מכניס את המודל להקשר הנכון.
- **המטרה**: לתרגם בקשות בשפה טבעית לקוד JavaScript התואם את ה-API של קיובייס.
- **כללי פעולה נוקשים**:
    - **פלט נקי**: הפלט חייב להכיל אך ורק קוד JavaScript.
    - **עטיפה (Wrapping)**: הקוד חייב להיות עטוף בתוך בלוק של ```javascript ... ```. זה מאפשר לשרת לזהות ולחלץ את הקוד בקלות.
    - **בלי תוספות**: אסור להוסיף הסברים, הערות או טקסט אחר מחוץ לבלוק הקוד.
    - **שימוש ב-API הרשמי**: להבטיח שהקוד יהיה שימושי ויעבוד בתוך קיובייס.
    - **טיפול בשגיאות**: אם הבקשה לא ברורה, המודל מתבקש להחזיר הודעת שגיאה קצרה בתוך הערת JavaScript.
- **דוגמה**: הדוגמה המצורפת (User: תיצור לי ערוץ אודיו...) עוזרת למודל להבין בדיוק את מבנה הפלט המצופה ממנו.

#### 4. תצורת המודל (generation_config, safety_settings, get_model)

- **generation_config**: הגדרות אלו שולטות ב"יצירתיות" של המודל.
    - `"temperature": 0.2`: ערך נמוך זה הופך את התשובות של המודל ליותר צפויות, מדויקות ועקביות, ופחות "יצירתיות". זהו מצב אידיאלי ליצירת קוד, שבו דיוק הוא קריטי.
- **safety_settings**: הגדרות בטיחות סטנדרטיות לחסימת תוכן פוגעני.
- **get_model()**: פונקציית עזר שמאתחלת את מודל `gemini-1.0-pro` עם כל ההגדרות שנקבעו (הנחיית המערכת, תצורת הפלט והבטיחות).

#### 5. נתיבי השרת (Flask Routes)

- **`@app.route('/')`**:
    - מגדיר את ההתנהגות עבור כתובת ה-URL הראשית של השרת (למשל, `http://127.0.0.1:5001/`).
    - הפונקציה `index()` מגישה את הקובץ `index.html`, שהוא הממשק הגרפי (UI) שהמשתמש רואה בדפדפן.
- **`@app.route('/generate', methods=['POST'])`**:
    - זהו הנתיב המרכזי שבו מתבצעת הלוגיקה. הוא מוגדר לקבל בקשות מסוג `POST` בלבד.
    - **מהלך הפעולה**:
        1.  **בדיקות תקינות**: מוודאת שהבקשה שהגיעה תקינה.
        2.  **קבלת הבקשה**: שולפת את הטקסט שהמשתמש הקליד.
        3.  **שליחה ל-Gemini**: שולחת את הטקסט למודל.
        4.  **עיבוד התשובה**: מקבלת את התשובה מהמודל ומחלצת ממנה את קוד ה-JavaScript הטהור.
        5.  **החזרת תשובה**: שולחת בחזרה לדפדפן של המשתמש את הקוד הנקי בפורמט JSON.
        6.  **טיפול בשגיאות**: אם מתרחשת תקלה, השרת יחזיר הודעת שגיאה מסודרת.

#### 6. מנגנוני הגנה ואופטימיזציה

**Rate Limiting (הגבלת קצב):**
- `check_rate_limit()`: מונע שימוש יתר ב-API על ידי הגבלה של 10 בקשות לדקה למשתמש.
- שומר רשימה של timestamps ומוחק כניסות ישנות מעל דקה.

**Response Cache (מטמון תשובות):**
- `get_cached_response()`: בודק אם יש תשובה שמורה בזיכרון עבור אותה בקשה.
- `cache_response()`: שומר תשובות למשך 60 דקות כדי להפחית שימוש ב-API ולשפר מהירות.
- התשובות נשמרות עם normalization (הקטנת אותיות) כדי להתאים גם בקשות דומות.

**Retry Logic (ניסיון חוזר):**
- `generate_with_retry()`: מנסה לשלוח בקשה ל-API עד 3 פעמים במקרה של כשל.
- משתמש ב-exponential backoff: ממתין שנייה אחת, אז 2, אז 4 לפני כל ניסיון.
- עוזר להתמודד עם שגיאות רשת זמניות.

**Input Validation (אימות קלט):**
- בדיקה שהבקשה לא ריקה ולא ארוכה מדי (מקסימום 1000 תווים).
- החזרת הודעות שגיאה מפורטות בעברית עבור כל סוג בעיה.

#### 7. בלוק הרצה ראשי

- `if __name__ == '__main__'`: קטע קוד סטנדרטי בפייתון שדואג שהפקודות שבתוכו ירוצו רק כאשר מריצים את הקובץ ישירות.
- `app.run(debug=True, host='0.0.0.0', port=8080)`: מפעיל את שרת הפיתוח של Flask.
    - `debug=True`: מצב פיתוח המציג שגיאות מפורטות ומטעין את השרת מחדש אוטומטית בכל שינוי בקוד.
    - `host='0.0.0.0'`: מאפשר גישה לשרת מכל כתובת IP (לא רק localhost).
    - `port=8080`: מריץ את השרת על פורט 8080.

---

## How to Run the Application

To run the application, you will need **Python 3** and a **web browser**.

### 1. Set up your API Key
Create a file named `.env` in the root of the project. Add the following line to the file, replacing `YOUR_API_KEY_HERE` with your actual Google API key:
```
GOOGLE_API_KEY=YOUR_API_KEY_HERE
```

### 2. Install Dependencies
Open a terminal or command prompt in the project directory. It's recommended to create a virtual environment first:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
In the same terminal, run the following command:
```bash
python app.py
```
You will see output indicating that the server is running, something like:
`* Running on http://127.0.0.1:8080`

### 4. Use the Assistant
Open your web browser and go to the following address:
[http://127.0.0.1:8080](http://127.0.0.1:8080)

You should see the web interface. You can now enter your requests in the text box to generate Cubase scripts.

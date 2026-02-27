#!/usr/bin/env python3
"""
Cubase AI Studio - Single File Launcher
========================================
This file is optimized for PyInstaller packaging.
"""

import os
import sys
import threading
import webbrowser
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Set template folder for Flask
os.environ['FLASK_TEMPLATE_FOLDER'] = resource_path('templates')

# --- Import Flask app components ---
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
env_path = resource_path('.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

import google.generativeai as genai

# --- Flask App Setup ---
app = Flask(__name__, template_folder=resource_path('templates'))
CORS(app)

# --- Gemini Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logging.info("Gemini API configured")
else:
    logging.warning("GOOGLE_API_KEY not found!")

SYSTEM_PROMPT = """
אתה עוזר הפקה וירטואלי מומחה לתוכנת Cubase.
מטרתך היא לתרגם בקשות של משתמשים בשפה טבעית לקוד JavaScript מדויק ובר-ביצוע, התואם את ה-API של Cubase (Cubase Scripting API).

כללי פעולה:
1.  הפלט שלך חייב להכיל אך ורק את קוד ה-JavaScript.
2.  עטוף את כל קוד ה-JavaScript בתוך בלוק של ```javascript ... ```.
3.  אל תוסיף הסברים, הערות או כל טקסט אחר מחוץ לבלוק הקוד.
4.  השתמש בפונקציות ובאובייקטים הרשמיים של ה-API של קיובייס.
5.  אם אינך יכול למלא את הבקשה או שהיא לא ברורה, החזר הודעת שגיאה קצרה בתוך בלוק הקוד כהערה.

דוגמה:
User: תיצור לי ערוץ אודיו מונו בשם 'Vocals'
Assistant:
```javascript
// Creates a mono audio track named 'Vocals'
cubase.createAudioTrack('Vocals', 'mono');
```
"""

generation_config = {
    "temperature": 0.2,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

def get_model():
    if not GOOGLE_API_KEY:
        return None
    try:
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=SYSTEM_PROMPT
        )
    except Exception as e:
        logging.error(f"Model init error: {e}")
        return None

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['GET'])
def chat_page():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    model = get_model()
    if not model:
        return jsonify({'error': 'API key not configured'}), 500

    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        history = data.get('history', [])
        chat_session = model.start_chat(history=[
            {'role': 'model' if m['role'] == 'assistant' else m['role'], 'parts': [m['content']]}
            for m in history
        ])

        response = chat_session.send_message(data['message'])
        raw_text = response.text

        code = None
        response_text = raw_text

        if '```javascript' in raw_text:
            parts = raw_text.split('```javascript')
            if len(parts) > 1:
                code = parts[1].split('```')[0].strip()
                response_text = parts[0].strip() or "הנה הסקריפט:"

        return jsonify({'response': response_text, 'code': code})

    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    model = get_model()
    if not model:
        return jsonify({'error': 'API key not configured'}), 500

    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        response = model.generate_content([data['prompt']])
        raw_text = response.text

        code = raw_text.strip()
        if code.startswith("```javascript"):
            code = code[len("```javascript"):].strip()
        if code.endswith("```"):
            code = code[:-3].strip()

        return jsonify({'code': code})

    except Exception as e:
        logging.error(f"Generate error: {e}")
        return jsonify({'error': str(e)}), 500

# --- Main ---
def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5001/chat')

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎹  C U B A S E   A I   S T U D I O  🎹                ║
║                                                              ║
║     http://127.0.0.1:5001                                   ║
║     http://127.0.0.1:5001/chat                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()

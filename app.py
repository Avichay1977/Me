import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Gemini API Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logging.error("GOOGLE_API_KEY not found. Please set it in your .env file.")
    # We will let the app run and show an error on the frontend.
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logging.info("Gemini API key configured successfully.")
    except Exception as e:
        logging.error(f"Error configuring Gemini API: {e}")


# --- System Prompt Definition ---
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

# --- Model Configuration ---
generation_config = {
  "temperature": 0.2,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

def get_model():
    """Initializes and returns the Gemini model."""
    if not GOOGLE_API_KEY:
        return None
    try:
        model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                                      generation_config=generation_config,
                                      system_instruction=SYSTEM_PROMPT,
                                      safety_settings=safety_settings)
        return model
    except Exception as e:
        logging.error(f"Failed to initialize the model: {e}")
        return None

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_script():
    """Handles the script generation request."""
    model = get_model()
    if model is None:
        return jsonify({'error': 'API key not configured or model initialization failed.'}), 500

    if not request.json or 'prompt' not in request.json:
        return jsonify({'error': 'Invalid request. "prompt" is required.'}), 400

    user_prompt = request.json['prompt']
    if not user_prompt.strip():
        return jsonify({'error': 'Prompt cannot be empty.'}), 400

    try:
        logging.info(f"Received prompt: {user_prompt}")

        response = model.generate_content([user_prompt])

        raw_text = response.text
        logging.info(f"Raw response from model: {raw_text}")

        # Extract the javascript code from the markdown block as per system prompt rules
        code = raw_text.strip()
        if code.startswith("```javascript"):
            code = code[len("```javascript"):].strip()
        if code.endswith("```"):
            code = code[:-len("```")].strip()

        return jsonify({'code': code})

    except Exception as e:
        logging.error(f"Error during script generation: {e}")
        if "API key not valid" in str(e):
             return jsonify({'error': 'The configured Google API key is invalid.'}), 500
        return jsonify({'error': f'An unexpected error occurred on the server.'}), 500

if __name__ == '__main__':
    # Port 5001 is used to avoid potential conflicts with other services.
    app.run(debug=True, port=5001)

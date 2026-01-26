import os
import time
from functools import lru_cache
from datetime import datetime, timedelta
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

# --- Rate Limiting ---
request_timestamps = []
MAX_REQUESTS_PER_MINUTE = 10

def check_rate_limit():
    """Check if request is within rate limit."""
    global request_timestamps
    now = datetime.now()
    # Remove timestamps older than 1 minute
    request_timestamps = [ts for ts in request_timestamps if now - ts < timedelta(minutes=1)]

    if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        return False, f"חרגת ממכסת הבקשות. אפשר לשלוח עד {MAX_REQUESTS_PER_MINUTE} בקשות לדקה."

    request_timestamps.append(now)
    return True, None

# --- Response Cache ---
response_cache = {}
CACHE_EXPIRY_MINUTES = 60

def get_cached_response(prompt):
    """Get cached response if available and not expired."""
    if prompt in response_cache:
        cached_data, timestamp = response_cache[prompt]
        if datetime.now() - timestamp < timedelta(minutes=CACHE_EXPIRY_MINUTES):
            logging.info(f"Cache hit for prompt: {prompt[:50]}...")
            return cached_data
        else:
            # Remove expired cache entry
            del response_cache[prompt]
    return None

def cache_response(prompt, code):
    """Cache the response."""
    response_cache[prompt] = (code, datetime.now())
    logging.info(f"Cached response for prompt: {prompt[:50]}...")

# --- Retry Logic with Exponential Backoff ---
def generate_with_retry(model, prompt, max_retries=3):
    """Generate content with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt])
            return response
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")

            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                # Last attempt failed
                logging.error(f"All {max_retries} attempts failed for prompt generation.")
                raise

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_script():
    """Handles the script generation request."""
    # Check rate limit
    allowed, error_msg = check_rate_limit()
    if not allowed:
        return jsonify({'error': error_msg}), 429

    model = get_model()
    if model is None:
        return jsonify({'error': 'מפתח ה-API לא מוגדר או אתחול המודל נכשל. אנא בדוק את הגדרות ה-API.'}), 500

    if not request.json or 'prompt' not in request.json:
        return jsonify({'error': 'בקשה לא תקינה. שדה "prompt" נדרש.'}), 400

    user_prompt = request.json['prompt']

    # Enhanced input validation
    if not user_prompt or not user_prompt.strip():
        return jsonify({'error': 'הבקשה לא יכולה להיות רקה. אנא הזן טקסט.'}), 400

    if len(user_prompt) > 1000:
        return jsonify({'error': 'הבקשה ארוכה מדי. אנא הגביל את הטקסט ל-1000 תווים.'}), 400

    # Normalize prompt for caching
    normalized_prompt = user_prompt.strip().lower()

    # Check cache
    cached_code = get_cached_response(normalized_prompt)
    if cached_code:
        return jsonify({'code': cached_code, 'cached': True})

    try:
        logging.info(f"Received prompt: {user_prompt}")

        # Use retry logic
        response = generate_with_retry(model, user_prompt, max_retries=3)

        raw_text = response.text
        logging.info(f"Raw response from model: {raw_text}")

        # Extract the javascript code from the markdown block as per system prompt rules
        code = raw_text.strip()
        if code.startswith("```javascript"):
            code = code[len("```javascript"):].strip()
        if code.endswith("```"):
            code = code[:-len("```")].strip()

        # Validate that we got some code
        if not code:
            return jsonify({'error': 'המודל החזיר תשובה ריקה. אנא נסה שוב עם בקשה שונה.'}), 500

        # Cache the response
        cache_response(normalized_prompt, code)

        return jsonify({'code': code, 'cached': False})

    except Exception as e:
        logging.error(f"Error during script generation: {e}")
        error_str = str(e)

        # Enhanced error messages
        if "API key not valid" in error_str or "invalid" in error_str.lower():
            return jsonify({'error': 'מפתח ה-API של Google אינו תקין. אנא בדוק את ההגדרות.'}), 500
        elif "quota" in error_str.lower() or "limit" in error_str.lower():
            return jsonify({'error': 'חרגת ממכסת ה-API. אנא נסה שוב מאוחר יותר.'}), 429
        elif "timeout" in error_str.lower():
            return jsonify({'error': 'הבקשה לקחה יותר מדי זמן. אנא נסה שוב.'}), 504
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            return jsonify({'error': 'שגיאת רשת. אנא בדוק את החיבור לאינטרנט ונסה שוב.'}), 503
        else:
            return jsonify({'error': 'אירעה שגיאה בלתי צפויה בשרת. אנא נסה שוב מאוחר יותר.'}), 500

if __name__ == '__main__':
    # Port 8080 is used to avoid potential conflicts with other services.
    app.run(debug=True, host='0.0.0.0', port=8080)

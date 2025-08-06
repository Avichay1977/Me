import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import logging
from PIL import Image
import io
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Gemini API Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logging.error("GOOGLE_API_KEY not found. Please set it in your .env file.")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logging.info("Gemini API key configured successfully.")
    except Exception as e:
        logging.error(f"Error configuring Gemini API: {e}")

# --- System Prompt Definition ---
# This is a general prompt, as the model now needs to handle both script generation and visual questions.
SYSTEM_PROMPT = """
You are a helpful and expert assistant for the music production software Cubase.

Your tasks are:
1.  If the user provides an image and asks a question about it, answer the question concisely.
2.  If the user provides a text prompt asking to create a script, translate the request into precise, executable JavaScript code that conforms to the Cubase Scripting API.
    - When generating a script, your output must ONLY contain the JavaScript code, wrapped in a ```javascript ... ``` block.
    - Do not add any explanations or any other text outside the code block.
    - If you cannot fulfill a script request, return a short error message inside a JavaScript comment.

Example for a script request:
User: "Create a mono audio track named 'Vocals'"
Assistant:
```javascript
// Creates a mono audio track named 'Vocals'
cubase.createAudioTrack('Vocals', 'mono');
```

Example for a visual question:
User: (Image of a Cubase mixer) "What does the red 'R' button do?"
Assistant: "The red 'R' button is the 'Read' button for automation. When it's enabled, the track will read and follow any existing automation data."
"""

# --- Model Configuration ---
generation_config = {
  "temperature": 0.3,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def get_generative_model():
    """Initializes and returns the standard text-based Gemini model."""
    if not GOOGLE_API_KEY: return None
    try:
        return genai.GenerativeModel(model_name="gemini-1.0-pro",
                                     generation_config=generation_config,
                                     system_instruction=SYSTEM_PROMPT,
                                     safety_settings=safety_settings)
    except Exception as e:
        logging.error(f"Failed to initialize the generative model: {e}")
        return None

def get_vision_model():
    """Initializes and returns the vision-capable Gemini model."""
    if not GOOGLE_API_KEY: return None
    try:
        # Note: The system prompt might be handled differently or partially ignored by vision models.
        # The main instruction should be part of the user prompt.
        return genai.GenerativeModel(model_name="gemini-pro-vision",
                                     generation_config=generation_config,
                                     safety_settings=safety_settings)
    except Exception as e:
        logging.error(f"Failed to initialize the vision model: {e}")
        return None

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_script():
    """Handles script/answer generation from text and optional image."""
    if not request.json:
        return jsonify({'error': 'Invalid request. JSON is required.'}), 400

    user_prompt = request.json.get('prompt')
    image_data_url = request.json.get('image')

    if not user_prompt or not user_prompt.strip():
        return jsonify({'error': 'Prompt cannot be empty.'}), 400

    try:
        content = [user_prompt]
        if image_data_url:
            model = get_vision_model()
            if not model: return jsonify({'error': 'Vision model not available.'}), 500

            # Decode the base64 image
            header, encoded = image_data_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data))

            # The vision model takes a list of prompt parts
            content.append(image)
            logging.info(f"Received prompt with image: {user_prompt}")
        else:
            model = get_generative_model()
            if not model: return jsonify({'error': 'Generative model not available.'}), 500
            logging.info(f"Received prompt without image: {user_prompt}")

        response = model.generate_content(content)
        raw_text = response.text
        logging.info(f"Raw response from model: {raw_text}")

        # Extract javascript code if present, otherwise return raw text.
        code = raw_text.strip()
        if code.startswith("```javascript"):
            code = code[len("```javascript"):].strip()
            if code.endswith("```"):
                code = code[:-len("```")].strip()

        return jsonify({'code': code})

    except Exception as e:
        logging.error(f"Error during generation: {e}")
        if "API key not valid" in str(e):
             return jsonify({'error': 'The configured Google API key is invalid.'}), 500
        return jsonify({'error': f'An unexpected error occurred on the server.'}), 500

# A simple in-memory cache for TTS audio
tts_cache = {}
# A placeholder for a more advanced TTS model if needed
# For now, we'll use a basic generative model to create a "response"
# In a real app, you would use a dedicated TTS API like Google's Text-to-Speech API.
@app.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Handles text-to-speech conversion.
    This is a simplified implementation for demonstration.
    A real-world application should use a dedicated TTS service.
    """
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'Invalid request. "text" is required.'}), 400

    text = request.json['text']
    if not text.strip():
        return jsonify({'error': 'Text cannot be empty.'}), 400

    # Check cache first
    if text in tts_cache:
        logging.info(f"TTS cache hit for: {text[:30]}...")
        return send_file(tts_cache[text], mimetype="audio/mpeg", as_attachment=False)

    try:
        logging.info(f"Generating TTS for: {text[:30]}...")
        # This is a placeholder. Using a generative model for TTS is not ideal.
        # We are using the text model to generate a response, not actual audio.
        # This part should be replaced with a real TTS engine.
        tts_model = genai.GenerativeModel(model_name="gemini-1.0-pro")
        # A simple prompt to make the model "speak" the text
        tts_response = tts_model.generate_content(f"Say the following sentence out loud, in a clear and friendly voice: '{text}'")

        # In a real implementation, you would get audio bytes here.
        # For this demo, we can't generate actual audio bytes, so we will
        # have to rely on the browser's speech synthesis on the client side.
        # This endpoint is now more of a placeholder to show the architecture.
        # We will return the original text and let the client handle synthesis.
        return jsonify({'message': 'TTS generation is handled client-side in this demo.', 'text_to_speak': text})


    except Exception as e:
        logging.error(f"Error during TTS generation: {e}")
        return jsonify({'error': 'Failed to generate speech.'}), 500


if __name__ == '__main__':
    # Port 5001 is used to avoid potential conflicts with other services.
    app.run(debug=True, port=5001)

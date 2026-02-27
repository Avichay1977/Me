#!/usr/bin/env python3
"""
Cubase Bridge Server
====================
שרת גשר שמחבר בין ה-Web Assistant לבין Cubase.

הרץ את זה במקביל ל-app.py:
    python bridge_server.py

הסקריפט ב-Cubase מתחבר לשרת הזה ומקבל פקודות לביצוע.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import queue
import threading
import time
import uuid

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# --- Command Queue ---
command_queue = queue.Queue()
results = {}

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'bridge': 'active'})


@app.route('/send', methods=['POST'])
def send_command():
    """
    Send a command to Cubase.
    Called by the main web app when user generates a script.
    """
    data = request.json
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400

    command_id = str(uuid.uuid4())
    command = {
        'id': command_id,
        'code': data['code'],
        'timestamp': time.time()
    }

    command_queue.put(command)

    return jsonify({
        'status': 'queued',
        'command_id': command_id,
        'message': 'Command sent to Cubase'
    })


@app.route('/poll', methods=['GET'])
def poll_commands():
    """
    Poll for pending commands.
    Called by the Cubase MIDI Remote script.
    """
    try:
        command = command_queue.get_nowait()
        return jsonify({
            'has_command': True,
            'command': command
        })
    except queue.Empty:
        return jsonify({'has_command': False})


@app.route('/result', methods=['POST'])
def report_result():
    """
    Report execution result.
    Called by Cubase after executing a command.
    """
    data = request.json
    if not data or 'command_id' not in data:
        return jsonify({'error': 'Invalid result'}), 400

    results[data['command_id']] = {
        'success': data.get('success', False),
        'result': data.get('result'),
        'error': data.get('error'),
        'timestamp': time.time()
    }

    return jsonify({'status': 'received'})


@app.route('/status/<command_id>', methods=['GET'])
def get_status(command_id):
    """Check the status of a command."""
    if command_id in results:
        return jsonify({
            'status': 'completed',
            'result': results[command_id]
        })
    else:
        return jsonify({'status': 'pending'})


# --- Cleanup old results ---
def cleanup_old_results():
    """Remove results older than 5 minutes."""
    while True:
        time.sleep(60)
        current_time = time.time()
        old_keys = [
            k for k, v in results.items()
            if current_time - v.get('timestamp', 0) > 300
        ]
        for key in old_keys:
            del results[key]


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_results, daemon=True)
cleanup_thread.start()


if __name__ == '__main__':
    print("=" * 50)
    print("🌉 Cubase Bridge Server")
    print("=" * 50)
    print("📡 Listening on http://127.0.0.1:5002")
    print("")
    print("This server connects the web assistant to Cubase.")
    print("Make sure the Cubase Script Bridge is installed!")
    print("=" * 50)

    app.run(host='127.0.0.1', port=5002, debug=False)

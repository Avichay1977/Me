"""
Learning System for Cubase Script Assistant
Tracks user actions, learns patterns, and provides intelligent suggestions.
"""

import sqlite3
import json
from datetime import datetime
from collections import Counter, defaultdict
import re


class LearningSystem:
    def __init__(self, db_path='user_learning.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for storing all user requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prompt TEXT NOT NULL,
                generated_code TEXT NOT NULL,
                was_cached BOOLEAN DEFAULT 0,
                session_id TEXT
            )
        ''')

        # Table for storing identified patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.0
            )
        ''')

        # Table for user preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_request(self, user_prompt, generated_code, was_cached=False, session_id=None):
        """Save a user request to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_requests (user_prompt, generated_code, was_cached, session_id)
            VALUES (?, ?, ?, ?)
        ''', (user_prompt, generated_code, was_cached, session_id))

        conn.commit()
        request_id = cursor.lastrowid
        conn.close()

        # Analyze patterns after saving
        self.analyze_patterns()

        return request_id

    def analyze_patterns(self):
        """Analyze user requests to identify patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent requests (last 100)
        cursor.execute('''
            SELECT user_prompt, generated_code
            FROM user_requests
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        requests = cursor.fetchall()

        if len(requests) < 3:  # Need at least 3 requests to identify patterns
            conn.close()
            return

        # Analyze common keywords
        all_prompts = ' '.join([req[0].lower() for req in requests])
        words = re.findall(r'\b\w+\b', all_prompts)
        word_freq = Counter(words)

        # Identify common actions (create, add, delete, etc.)
        common_actions = ['צור', 'הוסף', 'מחק', 'שנה', 'צבע', 'הגדר']
        action_patterns = defaultdict(int)

        for prompt, _ in requests:
            prompt_lower = prompt.lower()
            for action in common_actions:
                if action in prompt_lower:
                    action_patterns[action] += 1

        # Save identified patterns
        for action, freq in action_patterns.items():
            if freq >= 3:  # Pattern needs to appear at least 3 times
                confidence = min(freq / len(requests), 1.0)
                self._save_pattern('common_action', action, freq, confidence)

        # Identify number patterns (e.g., "always creates 4 channels")
        numbers = re.findall(r'\d+', all_prompts)
        if numbers:
            num_freq = Counter(numbers)
            for num, freq in num_freq.most_common(3):
                if freq >= 3:
                    confidence = min(freq / len(requests), 1.0)
                    self._save_pattern('common_number', num, freq, confidence)

        conn.close()

    def _save_pattern(self, pattern_type, pattern_data, frequency, confidence):
        """Save or update a learned pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM learned_patterns
            WHERE pattern_type = ? AND pattern_data = ?
        ''', (pattern_type, pattern_data))

        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            cursor.execute('''
                UPDATE learned_patterns
                SET frequency = ?, confidence = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (frequency, confidence, existing[0]))
        else:
            # Insert new pattern
            cursor.execute('''
                INSERT INTO learned_patterns (pattern_type, pattern_data, frequency, confidence)
                VALUES (?, ?, ?, ?)
            ''', (pattern_type, pattern_data, frequency, confidence))

        conn.commit()
        conn.close()

    def get_suggestions(self, current_prompt=''):
        """Get intelligent suggestions based on learned patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        suggestions = []

        # Get common actions
        cursor.execute('''
            SELECT pattern_data, frequency, confidence
            FROM learned_patterns
            WHERE pattern_type = 'common_action' AND confidence > 0.3
            ORDER BY frequency DESC
            LIMIT 5
        ''')
        common_actions = cursor.fetchall()

        if common_actions:
            top_action = common_actions[0]
            suggestions.append({
                'type': 'frequent_action',
                'text': f'שמתי לב שאתה משתמש הרבה ב"{top_action[0]}" - רוצה דוגמה?',
                'confidence': top_action[2],
                'data': top_action[0]
            })

        # Get common numbers
        cursor.execute('''
            SELECT pattern_data, frequency, confidence
            FROM learned_patterns
            WHERE pattern_type = 'common_number' AND confidence > 0.3
            ORDER BY frequency DESC
            LIMIT 3
        ''')
        common_numbers = cursor.fetchall()

        if common_numbers and current_prompt:
            # Check if current prompt might benefit from the common number
            if any(action in current_prompt.lower() for action in ['צור', 'הוסף']):
                top_num = common_numbers[0]
                suggestions.append({
                    'type': 'frequent_number',
                    'text': f'בדרך כלל אתה עובד עם {top_num[0]} ערוצים - להוסיף?',
                    'confidence': top_num[2],
                    'data': top_num[0]
                })

        # Get recent similar requests
        if current_prompt:
            cursor.execute('''
                SELECT user_prompt, generated_code
                FROM user_requests
                WHERE user_prompt LIKE ?
                ORDER BY timestamp DESC
                LIMIT 3
            ''', (f'%{current_prompt[:10]}%',))
            similar = cursor.fetchall()

            if similar:
                suggestions.append({
                    'type': 'recent_similar',
                    'text': f'שאלת משהו דומה לפני כמה זמן',
                    'confidence': 0.8,
                    'data': similar[0][0]
                })

        # Get usage statistics
        cursor.execute('SELECT COUNT(*) FROM user_requests')
        total_requests = cursor.fetchone()[0]

        if total_requests > 10:
            suggestions.append({
                'type': 'stats',
                'text': f'כבר השתמשת במערכת {total_requests} פעמים! 🎉',
                'confidence': 1.0,
                'data': str(total_requests)
            })

        conn.close()
        return suggestions

    def get_stats(self):
        """Get learning system statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total requests
        cursor.execute('SELECT COUNT(*) FROM user_requests')
        stats['total_requests'] = cursor.fetchone()[0]

        # Requests today
        cursor.execute('''
            SELECT COUNT(*) FROM user_requests
            WHERE DATE(timestamp) = DATE('now')
        ''')
        stats['requests_today'] = cursor.fetchone()[0]

        # Most common action
        cursor.execute('''
            SELECT pattern_data, frequency
            FROM learned_patterns
            WHERE pattern_type = 'common_action'
            ORDER BY frequency DESC
            LIMIT 1
        ''')
        top_action = cursor.fetchone()
        stats['top_action'] = top_action[0] if top_action else None

        # Cache hit rate
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN was_cached = 1 THEN 1 END) * 100.0 / COUNT(*)
            FROM user_requests
        ''')
        cache_rate = cursor.fetchone()[0]
        stats['cache_hit_rate'] = round(cache_rate, 1) if cache_rate else 0.0

        conn.close()
        return stats

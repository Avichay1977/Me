"""
Cubase Script Assistant - Desktop Application
Windows desktop app with screen monitoring, voice control, and AI learning.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import json
from datetime import datetime
import sys


class CubaseAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 Cubase Assistant AI")
        self.root.geometry("400x600")

        # Always on top
        self.root.attributes('-topmost', True)

        # Server URL
        self.server_url = "http://127.0.0.1:8080"

        # Initialize UI
        self.create_ui()

        # Check server connection
        self.check_server_connection()

    def create_ui(self):
        """Create the main UI."""
        # Header
        header_frame = tk.Frame(self.root, bg='#667eea', pady=10)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame,
            text="🎤 Cubase Assistant",
            font=('Arial', 16, 'bold'),
            bg='#667eea',
            fg='white'
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="AI + Voice + Learning",
            font=('Arial', 10),
            bg='#667eea',
            fg='white'
        )
        subtitle_label.pack()

        # Stats Panel
        stats_frame = tk.LabelFrame(self.root, text="📊 סטטיסטיקות", font=('Arial', 10, 'bold'))
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        self.stats_text = tk.Label(
            stats_frame,
            text="מחובר לשרת...",
            font=('Arial', 9),
            justify=tk.LEFT
        )
        self.stats_text.pack(padx=5, pady=5)

        # Input Frame
        input_frame = tk.LabelFrame(self.root, text="💬 בקשה", font=('Arial', 10, 'bold'))
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Text input
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=5,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons frame
        button_frame = tk.Frame(input_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.voice_button = tk.Button(
            button_frame,
            text="🎤 דבר",
            font=('Arial', 10, 'bold'),
            bg='#28a745',
            fg='white',
            command=self.start_voice_recognition
        )
        self.voice_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.generate_button = tk.Button(
            button_frame,
            text="✨ צור",
            font=('Arial', 10, 'bold'),
            bg='#007bff',
            fg='white',
            command=self.generate_script
        )
        self.generate_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.clear_button = tk.Button(
            button_frame,
            text="🗑️ נקה",
            font=('Arial', 10),
            bg='#6c757d',
            fg='white',
            command=self.clear_all
        )
        self.clear_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Output Frame
        output_frame = tk.LabelFrame(self.root, text="📝 תוצאה", font=('Arial', 10, 'bold'))
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Output text
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            font=('Courier', 9),
            wrap=tk.WORD,
            bg='#282c34',
            fg='#abb2bf'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Copy button
        copy_button = tk.Button(
            output_frame,
            text="📋 העתק לזיכרון",
            font=('Arial', 9),
            bg='#17a2b8',
            fg='white',
            command=self.copy_to_clipboard
        )
        copy_button.pack(padx=5, pady=5)

        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="מוכן",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Arial', 8)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_server_connection(self):
        """Check if Flask server is running."""
        def check():
            try:
                response = requests.get(f"{self.server_url}/stats", timeout=2)
                if response.status_code == 200:
                    stats = response.json()
                    self.update_stats(stats)
                    self.update_status("✅ מחובר לשרת", "green")
                else:
                    self.update_status("⚠️ שרת לא זמין", "orange")
            except Exception as e:
                self.update_status("❌ שרת לא רץ - הפעל את app.py", "red")

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

        # Check every 10 seconds
        self.root.after(10000, self.check_server_connection)

    def update_stats(self, stats):
        """Update statistics display."""
        stats_text = f"""
📊 סה"כ בקשות: {stats.get('total_requests', 0)}
📅 היום: {stats.get('requests_today', 0)}
💾 מטמון: {stats.get('cache_hit_rate', 0)}%
        """
        self.stats_text.config(text=stats_text.strip())

    def update_status(self, message, color="black"):
        """Update status bar."""
        self.status_bar.config(text=message, fg=color)

    def start_voice_recognition(self):
        """Start voice recognition (placeholder for now)."""
        self.update_status("🎤 זיהוי קולי זמין בדפדפן בלבד כרגע", "blue")
        # Note: Browser-based speech recognition works best
        # For desktop, we'd need to integrate with Google Speech API or similar

    def generate_script(self):
        """Generate script from prompt."""
        prompt = self.input_text.get("1.0", tk.END).strip()

        if not prompt:
            self.update_status("⚠️ הזן בקשה קודם", "orange")
            return

        self.generate_button.config(state=tk.DISABLED, text="⏳ מעבד...")
        self.update_status("🔄 שולח לשרת...", "blue")

        def generate():
            try:
                response = requests.post(
                    f"{self.server_url}/generate",
                    json={"prompt": prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    code = data.get('code', '')
                    cached = data.get('cached', False)

                    self.output_text.delete("1.0", tk.END)
                    self.output_text.insert("1.0", code)

                    cache_msg = " (מטמון)" if cached else ""
                    self.update_status(f"✅ הקוד נוצר בהצלחה{cache_msg}", "green")
                else:
                    error = response.json().get('error', 'שגיאה לא ידועה')
                    self.output_text.delete("1.0", tk.END)
                    self.output_text.insert("1.0", f"// שגיאה: {error}")
                    self.update_status(f"❌ {error}", "red")

            except requests.exceptions.Timeout:
                self.update_status("⏱️ זמן הבקשה פג - נסה שוב", "red")
            except Exception as e:
                self.update_status(f"❌ שגיאה: {str(e)}", "red")
            finally:
                self.generate_button.config(state=tk.NORMAL, text="✨ צור")

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def copy_to_clipboard(self):
        """Copy output to clipboard."""
        code = self.output_text.get("1.0", tk.END).strip()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.update_status("✅ הועתק לזיכרון!", "green")
        else:
            self.update_status("⚠️ אין מה להעתיק", "orange")

    def clear_all(self):
        """Clear input and output."""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.update_status("🗑️ נוקה", "blue")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = CubaseAssistantApp(root)

    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()

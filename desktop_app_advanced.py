"""
Cubase Script Assistant - Advanced Desktop Application
Features:
- Always on top window
- Global hotkeys (Ctrl+Shift+C)
- System tray icon
- Screen monitoring
- Cubase Remote Control integration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
from datetime import datetime
import sys
import os

# Try importing advanced libraries
try:
    import keyboard  # For global hotkeys
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: 'keyboard' library not installed. Global hotkeys disabled.")

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Warning: 'pystray' and 'Pillow' not installed. System tray disabled.")

try:
    from PIL import ImageGrab, Image
    import pytesseract
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False
    print("Warning: Screen capture libraries not available.")


class CubaseAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 Cubase Assistant AI")

        # Window size and position
        window_width = 450
        window_height = 650
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Position in top-right corner
        x = screen_width - window_width - 20
        y = 50

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Always on top
        self.root.attributes('-topmost', True)

        # Opacity (semi-transparent when not focused)
        self.root.attributes('-alpha', 0.95)

        # Server URL
        self.server_url = "http://127.0.0.1:8080"

        # State
        self.is_minimized = False
        self.is_monitoring = False

        # Initialize UI
        self.create_ui()

        # Setup global hotkeys
        if KEYBOARD_AVAILABLE:
            self.setup_hotkeys()

        # Setup system tray
        if TRAY_AVAILABLE:
            self.setup_tray()

        # Check server connection
        self.check_server_connection()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_ui(self):
        """Create the main UI."""
        # Header with drag capability
        header_frame = tk.Frame(self.root, bg='#667eea', pady=10, cursor='fleur')
        header_frame.pack(fill=tk.X)
        header_frame.bind('<Button-1>', self.start_drag)
        header_frame.bind('<B1-Motion>', self.do_drag)

        title_label = tk.Label(
            header_frame,
            text="🎤 Cubase Assistant",
            font=('Arial', 16, 'bold'),
            bg='#667eea',
            fg='white',
            cursor='fleur'
        )
        title_label.pack()
        title_label.bind('<Button-1>', self.start_drag)
        title_label.bind('<B1-Motion>', self.do_drag)

        subtitle_label = tk.Label(
            header_frame,
            text="AI + Voice + Screen Monitoring",
            font=('Arial', 9),
            bg='#667eea',
            fg='white',
            cursor='fleur'
        )
        subtitle_label.pack()
        subtitle_label.bind('<Button-1>', self.start_drag)
        subtitle_label.bind('<B1-Motion>', self.do_drag)

        # Control buttons (minimize, close)
        controls_frame = tk.Frame(header_frame, bg='#667eea')
        controls_frame.pack(anchor=tk.E, padx=5)

        minimize_btn = tk.Button(
            controls_frame,
            text="─",
            font=('Arial', 8),
            bg='#5566d6',
            fg='white',
            command=self.minimize_to_tray,
            width=3
        )
        minimize_btn.pack(side=tk.LEFT, padx=2)

        close_btn = tk.Button(
            controls_frame,
            text="✕",
            font=('Arial', 8),
            bg='#dc3545',
            fg='white',
            command=self.on_closing,
            width=3
        )
        close_btn.pack(side=tk.LEFT)

        # Hotkey info
        hotkey_label = tk.Label(
            self.root,
            text="⌨️ קיצור דרך: Ctrl+Shift+C",
            font=('Arial', 8),
            fg='#6c757d',
            bg='#f8f9fa'
        )
        hotkey_label.pack(fill=tk.X, pady=2)

        # Stats Panel
        stats_frame = tk.LabelFrame(self.root, text="📊 סטטיסטיקות", font=('Arial', 10, 'bold'))
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.stats_text = tk.Label(
            stats_frame,
            text="מחובר לשרת...",
            font=('Arial', 9),
            justify=tk.LEFT
        )
        self.stats_text.pack(padx=5, pady=5)

        # Screen monitoring toggle
        if SCREEN_CAPTURE_AVAILABLE:
            monitor_frame = tk.Frame(self.root)
            monitor_frame.pack(fill=tk.X, padx=10, pady=5)

            self.monitor_button = tk.Button(
                monitor_frame,
                text="👁️ הפעל מעקב מסך",
                font=('Arial', 9, 'bold'),
                bg='#ffc107',
                fg='black',
                command=self.toggle_screen_monitoring
            )
            self.monitor_button.pack(fill=tk.X)

        # Input Frame
        input_frame = tk.LabelFrame(self.root, text="💬 בקשה", font=('Arial', 10, 'bold'))
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Text input
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=4,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons frame
        button_frame = tk.Frame(input_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.voice_button = tk.Button(
            button_frame,
            text="🎤",
            font=('Arial', 10, 'bold'),
            bg='#28a745',
            fg='white',
            command=self.start_voice_recognition,
            width=3
        )
        self.voice_button.pack(side=tk.LEFT, padx=2)

        self.generate_button = tk.Button(
            button_frame,
            text="✨ צור סקריפט",
            font=('Arial', 10, 'bold'),
            bg='#007bff',
            fg='white',
            command=self.generate_script
        )
        self.generate_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.clear_button = tk.Button(
            button_frame,
            text="🗑️",
            font=('Arial', 10),
            bg='#6c757d',
            fg='white',
            command=self.clear_all,
            width=3
        )
        self.clear_button.pack(side=tk.LEFT, padx=2)

        # Output Frame
        output_frame = tk.LabelFrame(self.root, text="📝 תוצאה", font=('Arial', 10, 'bold'))
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Output text
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=8,
            font=('Courier', 9),
            wrap=tk.WORD,
            bg='#282c34',
            fg='#abb2bf'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Action buttons
        action_frame = tk.Frame(output_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        copy_button = tk.Button(
            action_frame,
            text="📋 העתק",
            font=('Arial', 9),
            bg='#17a2b8',
            fg='white',
            command=self.copy_to_clipboard
        )
        copy_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        execute_button = tk.Button(
            action_frame,
            text="▶️ הרץ בקיובייס",
            font=('Arial', 9),
            bg='#28a745',
            fg='white',
            command=self.execute_in_cubase
        )
        execute_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="✅ מוכן | Ctrl+Shift+C להצגה/הסתרה",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Arial', 8)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_drag(self, event):
        """Start window drag."""
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        """Perform window drag."""
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def setup_hotkeys(self):
        """Setup global hotkeys."""
        try:
            keyboard.add_hotkey('ctrl+shift+c', self.toggle_window)
            self.update_status("⌨️ קיצורי דרך הופעלו", "green")
        except Exception as e:
            print(f"Failed to setup hotkeys: {e}")

    def setup_tray(self):
        """Setup system tray icon."""
        try:
            # Create an icon
            def create_image():
                width = 64
                height = 64
                image = Image.new('RGB', (width, height), '#667eea')
                dc = ImageDraw.Draw(image)
                dc.rectangle([16, 16, 48, 48], fill='white')
                dc.text((24, 24), "🎤", fill='black')
                return image

            menu = pystray.Menu(
                pystray.MenuItem('הצג', self.show_window),
                pystray.MenuItem('הסתר', self.hide_window),
                pystray.MenuItem(pystray.Menu.SEPARATOR),
                pystray.MenuItem('יציאה', self.quit_app)
            )

            self.tray_icon = pystray.Icon("cubase_assistant", create_image(), "Cubase Assistant", menu)

            # Run tray in separate thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()

        except Exception as e:
            print(f"Failed to setup tray: {e}")

    def toggle_window(self):
        """Toggle window visibility (global hotkey)."""
        if self.root.state() == 'withdrawn':
            self.show_window()
        else:
            self.hide_window()

    def show_window(self, icon=None, item=None):
        """Show window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized = False

    def hide_window(self, icon=None, item=None):
        """Hide window."""
        self.root.withdraw()
        self.is_minimized = True

    def minimize_to_tray(self):
        """Minimize to system tray."""
        if TRAY_AVAILABLE:
            self.hide_window()
            self.update_status("📍 ממוזער ל-System Tray", "blue")
        else:
            self.root.iconify()

    def toggle_screen_monitoring(self):
        """Toggle screen monitoring."""
        if not SCREEN_CAPTURE_AVAILABLE:
            messagebox.showwarning("לא זמין", "יכולות Screen Capture לא מותקנות")
            return

        self.is_monitoring = not self.is_monitoring

        if self.is_monitoring:
            self.monitor_button.config(text="👁️ עצור מעקב", bg='#dc3545')
            self.start_monitoring()
            self.update_status("👁️ מעקב מסך פעיל", "blue")
        else:
            self.monitor_button.config(text="👁️ הפעל מעקב", bg='#ffc107')
            self.update_status("👁️ מעקב מסך הופסק", "gray")

    def start_monitoring(self):
        """Start screen monitoring (captures screen every 5 seconds)."""
        def monitor():
            while self.is_monitoring:
                try:
                    # Capture screen
                    screenshot = ImageGrab.grab()

                    # Here you would:
                    # 1. Use OCR to extract text
                    # 2. Detect UI elements
                    # 3. Understand context
                    # 4. Provide suggestions

                    # Placeholder for now
                    self.update_status(f"👁️ סריקה... {datetime.now().strftime('%H:%M:%S')}", "blue")

                    # Wait 5 seconds
                    for _ in range(50):
                        if not self.is_monitoring:
                            break
                        threading.Event().wait(0.1)

                except Exception as e:
                    print(f"Monitoring error: {e}")
                    self.is_monitoring = False
                    self.monitor_button.config(text="👁️ הפעל מעקב", bg='#ffc107')

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def check_server_connection(self):
        """Check if Flask server is running."""
        def check():
            try:
                response = requests.get(f"{self.server_url}/stats", timeout=2)
                if response.status_code == 200:
                    stats = response.json()
                    self.update_stats(stats)
                    self.update_status("✅ מחובר לשרת", "green")
            except:
                self.update_status("❌ שרת לא רץ", "red")

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

        # Check every 10 seconds
        self.root.after(10000, self.check_server_connection)

    def update_stats(self, stats):
        """Update statistics display."""
        stats_text = f"📊 {stats.get('total_requests', 0)} | 📅 {stats.get('requests_today', 0)} | 💾 {stats.get('cache_hit_rate', 0)}%"
        self.stats_text.config(text=stats_text)

    def update_status(self, message, color="black"):
        """Update status bar."""
        self.status_bar.config(text=message, fg=color)

    def start_voice_recognition(self):
        """Open browser for voice recognition."""
        import webbrowser
        webbrowser.open(self.server_url)
        self.update_status("🌐 פתחתי את הדפדפן לזיהוי קולי", "blue")

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

                    self.output_text.delete("1.0", tk.END)
                    self.output_text.insert("1.0", code)

                    self.update_status("✅ הקוד נוצר!", "green")
                else:
                    error = response.json().get('error', 'שגיאה')
                    self.update_status(f"❌ {error}", "red")

            except Exception as e:
                self.update_status(f"❌ שגיאה: {str(e)}", "red")
            finally:
                self.generate_button.config(state=tk.NORMAL, text="✨ צור סקריפט")

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def copy_to_clipboard(self):
        """Copy output to clipboard."""
        code = self.output_text.get("1.0", tk.END).strip()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.update_status("✅ הועתק!", "green")

    def execute_in_cubase(self):
        """Execute script in Cubase (placeholder)."""
        code = self.output_text.get("1.0", tk.END).strip()
        if code:
            # This would integrate with Cubase Remote Control API
            # For now, just copy to clipboard
            self.copy_to_clipboard()
            self.update_status("📋 הועתק - הדבק בקיובייס", "blue")
            messagebox.showinfo(
                "הרצה בקיובייס",
                "הקוד הועתק לזיכרון.\nהדבק אותו בקיובייס Script Editor והרץ."
            )

    def clear_all(self):
        """Clear all text."""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.update_status("🗑️ נוקה", "blue")

    def on_closing(self):
        """Handle window close event."""
        if TRAY_AVAILABLE:
            if messagebox.askokcancel("יציאה", "האם לצאת? (התוכנה תימצא ב-System Tray)"):
                self.quit_app()
            else:
                self.hide_window()
        else:
            if messagebox.askokcancel("יציאה", "האם לצאת מהתוכנה?"):
                self.quit_app()

    def quit_app(self, icon=None, item=None):
        """Quit application completely."""
        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()
        if TRAY_AVAILABLE and hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.quit()
        sys.exit(0)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = CubaseAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

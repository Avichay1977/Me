#!/usr/bin/env python3
"""
Cubase Script Auto-Installer
=============================
סקריפט שרץ ברקע ומתקין אוטומטית סקריפטים לקיובייס.

הרץ את הסקריפט הזה ותשאיר אותו פתוח - כל סקריפט שתוריד
מהעוזר יועבר אוטומטית לתיקיית הסקריפטים של קיובייס!
"""

import os
import sys
import time
import shutil
import platform
from pathlib import Path

# --- Configuration ---
SCRIPT_PREFIX = "cubase_script_"
CHECK_INTERVAL = 2  # seconds

def get_downloads_folder():
    """Get the user's Downloads folder."""
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", "")) / "Downloads"
    elif platform.system() == "Darwin":  # macOS
        return Path.home() / "Downloads"
    else:  # Linux
        return Path.home() / "Downloads"

def get_cubase_scripts_folder():
    """Get the Cubase MIDI Remote scripts folder."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", ""))
        return base / "Steinberg" / "Cubase" / "MIDI Remote" / "Driver Scripts" / "Local"
    elif platform.system() == "Darwin":  # macOS
        return Path.home() / "Library" / "Preferences" / "Cubase" / "MIDI Remote" / "Driver Scripts" / "Local"
    else:  # Linux (if Cubase runs via Wine)
        return Path.home() / ".wine" / "drive_c" / "users" / os.getlogin() / "AppData" / "Roaming" / "Steinberg" / "Cubase" / "MIDI Remote" / "Driver Scripts" / "Local"

def ensure_cubase_folder_exists(folder):
    """Create the Cubase scripts folder if it doesn't exist."""
    if not folder.exists():
        print(f"📁 יוצר תיקייה: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
    return folder.exists()

def show_notification(title, message):
    """Show a system notification."""
    try:
        if platform.system() == "Windows":
            # Windows 10+ toast notification
            from subprocess import run
            run(['powershell', '-Command', f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
                $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Cubase Auto-Installer")
                $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($template))
            '''], capture_output=True)
        elif platform.system() == "Darwin":  # macOS
            os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
        else:  # Linux
            os.system(f'notify-send "{title}" "{message}"')
    except:
        pass  # Notification failed, not critical

def main():
    downloads = get_downloads_folder()
    cubase_folder = get_cubase_scripts_folder()

    print("=" * 50)
    print("🎹 Cubase Script Auto-Installer")
    print("=" * 50)
    print(f"📂 מעקב אחרי: {downloads}")
    print(f"📁 יעד: {cubase_folder}")
    print("-" * 50)
    print("✨ השאר חלון זה פתוח!")
    print("   כל סקריפט שתוריד יועבר אוטומטית לקיובייס.")
    print("-" * 50)

    if not downloads.exists():
        print(f"❌ תיקיית ההורדות לא נמצאה: {downloads}")
        sys.exit(1)

    ensure_cubase_folder_exists(cubase_folder)

    processed_files = set()

    # Initial scan - don't process existing files
    for f in downloads.glob(f"{SCRIPT_PREFIX}*.js"):
        processed_files.add(f.name)

    print(f"🔍 מתחיל מעקב... (לחץ Ctrl+C לעצירה)\n")

    try:
        while True:
            for script_file in downloads.glob(f"{SCRIPT_PREFIX}*.js"):
                if script_file.name not in processed_files:
                    processed_files.add(script_file.name)

                    dest = cubase_folder / script_file.name
                    try:
                        shutil.move(str(script_file), str(dest))
                        print(f"✅ הותקן: {script_file.name}")
                        show_notification(
                            "סקריפט הותקן בהצלחה!",
                            f"{script_file.name}\nהפעל מחדש את Cubase לטעינה."
                        )
                    except Exception as e:
                        print(f"❌ שגיאה בהעברת {script_file.name}: {e}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n👋 Auto-installer הופסק.")

if __name__ == "__main__":
    main()

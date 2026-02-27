#!/usr/bin/env python3
"""
Macro Manager - Save and replay sequences of Cubase commands
=============================================================
"""

import json
import os
from datetime import datetime
from pathlib import Path

MACROS_FILE = Path(__file__).parent / "saved_macros.json"


def load_macros():
    """Load saved macros from file."""
    if MACROS_FILE.exists():
        with open(MACROS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_macros(macros):
    """Save macros to file."""
    with open(MACROS_FILE, 'w', encoding='utf-8') as f:
        json.dump(macros, f, ensure_ascii=False, indent=2)


def create_macro(name, commands, description=""):
    """
    Create a new macro.

    Args:
        name: Macro name
        commands: List of command strings or code snippets
        description: Optional description
    """
    macros = load_macros()

    macros[name] = {
        "name": name,
        "description": description,
        "commands": commands,
        "created": datetime.now().isoformat(),
        "run_count": 0
    }

    save_macros(macros)
    return macros[name]


def run_macro(name):
    """
    Get macro commands for execution.

    Args:
        name: Macro name to run

    Returns:
        List of commands or None if not found
    """
    macros = load_macros()

    if name not in macros:
        return None

    # Increment run count
    macros[name]["run_count"] += 1
    macros[name]["last_run"] = datetime.now().isoformat()
    save_macros(macros)

    return macros[name]["commands"]


def list_macros():
    """List all saved macros."""
    return load_macros()


def delete_macro(name):
    """Delete a macro."""
    macros = load_macros()
    if name in macros:
        del macros[name]
        save_macros(macros)
        return True
    return False


# --- Pre-defined macros ---
DEFAULT_MACROS = {
    "quick-drums": {
        "name": "quick-drums",
        "description": "יצירת תבנית תופים מהירה",
        "commands": [
            "cubase.createAudioTrack('Kick', 'mono');",
            "cubase.createAudioTrack('Snare', 'mono');",
            "cubase.createAudioTrack('Hi-Hat', 'stereo');",
            "cubase.createGroupTrack('Drums Bus');",
        ],
        "created": "2024-01-01T00:00:00",
        "run_count": 0
    },
    "color-organize": {
        "name": "color-organize",
        "description": "ארגון צבעים אוטומטי",
        "commands": [
            "// Color drums red",
            "cubase.setTrackColorByName('*Drum*', 'red');",
            "cubase.setTrackColorByName('*Kick*', 'red');",
            "cubase.setTrackColorByName('*Snare*', 'red');",
            "// Color bass blue",
            "cubase.setTrackColorByName('*Bass*', 'blue');",
            "// Color vocals yellow",
            "cubase.setTrackColorByName('*Vocal*', 'yellow');",
        ],
        "created": "2024-01-01T00:00:00",
        "run_count": 0
    },
    "mixing-prep": {
        "name": "mixing-prep",
        "description": "הכנה למיקס",
        "commands": [
            "cubase.createGroupTrack('Drums');",
            "cubase.createGroupTrack('Bass');",
            "cubase.createGroupTrack('Guitars');",
            "cubase.createGroupTrack('Keys');",
            "cubase.createGroupTrack('Vocals');",
            "cubase.createFXTrack('Reverb');",
            "cubase.createFXTrack('Delay');",
        ],
        "created": "2024-01-01T00:00:00",
        "run_count": 0
    }
}


def init_default_macros():
    """Initialize default macros if none exist."""
    macros = load_macros()
    if not macros:
        save_macros(DEFAULT_MACROS)


if __name__ == "__main__":
    init_default_macros()
    print("Available macros:")
    for name, macro in list_macros().items():
        print(f"  - {name}: {macro['description']}")

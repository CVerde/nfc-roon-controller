"""NFC Roon Controller - Configuration"""
import json
import os

# Application info for Roon API
APP_INFO = {
    "extension_id": "nfc_roon_controller",
    "display_name": "NFC Roon Controller",
    "display_version": "2.1.0",
    "publisher": "NFC Roon Controller",
    "email": "nfc@roon.controller",
}

# Server settings
SERVER_PORT = 5001
SCAN_TIMEOUT = 30  # seconds

# Settings file path
SETTINGS_FILE = "settings.json"

def load_settings() -> dict:
    """Load user settings from file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"default_zone": "", "language": "en"}

def save_settings(settings: dict):
    """Save user settings to file"""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# Load settings on import
SETTINGS = load_settings()

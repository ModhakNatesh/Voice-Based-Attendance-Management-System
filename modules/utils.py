"""Utility functions for voice attendance system."""
import json
import os
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("attendance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("attendance")

def validate_date(date_str):
    """Validates YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_user_id(user_id):
    """Prevents SQL injection and ensures alphanumeric IDs."""
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,20}$", user_id))

def is_strong_password(password):
    """Enforces password policy."""
    return (
        len(password) >= 8 and
        bool(re.search(r"[A-Z]", password)) and
        bool(re.search(r"\d", password)) and
        bool(re.search(r"[!@#$%^&*]", password))
    )

def load_config():
    """Loads configuration from config.json."""
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        logger.warning("config.json not found. Using default values.")
        return {
            "audio_folder": "voice_samples/",
            "attendance_temp": "temp_samples/",
            "attendance_db": "attendance.db",
            "speaker_embeddings": "speaker_embeddings.pkl",
            "default_similarity_threshold": 0.75,
            "min_energy_threshold": 0.01,
            "admin_username": "admin",
            "teacher_username": "teacher",
            "debug_mode": False
        }

# Load configuration globally
CONFIG = load_config()
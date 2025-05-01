"""Voice attendance system modules."""
from modules.utils import CONFIG
import os

# Ensure required directories exist
os.makedirs(CONFIG["audio_folder"], exist_ok=True)
os.makedirs(CONFIG["attendance_temp"], exist_ok=True)
import os
import json
import datetime
import logging
import sqlite3
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# File paths for development and PyInstaller
def get_app_dir():
    """Get the application directory that works in both development and when packaged with PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # If running as PyInstaller bundle, use the directory where the executable is located
        base_dir = Path(os.path.dirname(sys.executable))
    else:
        # In development, use the current directory
        base_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    # Create an 'App_Data' subfolder for all user data
    return base_dir / "App_Data"

# Use the function to set the paths
APP_DIR = get_app_dir()
SAVE_DIR = APP_DIR / datetime.datetime.now().strftime("%Y-%m-%d")
CONFIG_FILE = APP_DIR / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "dark_mode": True,
    "api_provider": "openai",
    "api_key": "",
}

# Ensure directories exist
def ensure_dirs():
    """Create necessary directories if they don't exist."""
    if not APP_DIR.exists():
        APP_DIR.mkdir(parents=True, exist_ok=True)
    if not SAVE_DIR.exists():
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
    return SAVE_DIR

# Load app configuration from config.json
def load_config():
    """Load configuration from config.json"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
                return config
        else:
            save_config(DEFAULT_CONFIG)
            logger.info(f"Created default configuration in {CONFIG_FILE}")
            return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
        return DEFAULT_CONFIG

# Save app configuration to config.json
def save_config(config):
    """Save configuration to config.json"""
    try:
        ensure_dirs()  # Make sure APP_DIR exists
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

# Get config value
def get_config(key, default=None):
    """Get a configuration value with fallback to default"""
    config = load_config()
    
    # Convert key to lowercase for JSON keys
    json_key = key.lower()
    
    # Try getting from config.json
    if json_key in config:
        return config[json_key]
    
    # If not found, return default
    return default

# Save configuration value
def save_setting(key, value):
    """Save a setting to the configuration file"""
    config = load_config()
    # Convert key to lowercase for JSON keys
    json_key = key.lower()
    
    # Đảm bảo dark_mode được lưu là boolean
    if json_key == "dark_mode" or json_key == "darkmode":
        value = bool(value)
        logger.info(f"Setting dark_mode to: {value}")
    
    config[json_key] = value
    
    # Also update in memory
    global AI_API_KEY, API_PROVIDER, DARK_MODE
    if json_key == "api_key":
        AI_API_KEY = value
    elif json_key == "api_provider":
        API_PROVIDER = value
    elif json_key == "dark_mode" or json_key == "darkmode":
        DARK_MODE = bool(value)  # Ensure this is a boolean
        logger.info(f"Updated global DARK_MODE to: {DARK_MODE}")
    
    # Save to config file
    result = save_config(config)
    
    if result:
        logger.info(f"Successfully saved setting: {json_key}")
    else:
        logger.error(f"Failed to save setting: {json_key}")
        
    return result

# Load initial configuration
APP_CONFIG = load_config()

# Database settings
DB_PATH = APP_DIR / "history.db"

# Image settings
DEFAULT_IMAGE_SIZE = (512, 512)
MAX_IMAGE_SIZE = (1024, 1024)
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg"]

# UI settings - load from config
DARK_MODE = APP_CONFIG.get("dark_mode", True)
API_PROVIDER = APP_CONFIG.get("api_provider", "openai")
AI_API_KEY = APP_CONFIG.get("api_key", "")
DEFAULT_FONT = ("Segoe UI", 11)
ACCENT_COLOR = ["#3B8ED0", "#1F6AA5"]

# For compatibility with older code that might still use these functions
def save_to_env(key, value):
    """Compatibility function that now uses the JSON config system"""
    logger.debug(f"Redirecting env var save to config system: {key}")
    return save_setting(key, value)

# Alias for backward compatibility
save_env_variable = save_to_env

# Database settings
def initialize_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create images table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        provider TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        width INTEGER,
        height INTEGER,
        extra_data TEXT
    )
    ''')
    
    conn.commit()
    conn.close() 
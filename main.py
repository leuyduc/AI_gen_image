import os
import sys
import logging
from pathlib import Path

from ui.main_window import MainWindow
from core.settings import ensure_dirs, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def setup_app():
    """Set up application directories and database."""
    # Create application directories
    save_dir = ensure_dirs()
    logger.info(f"Image save directory: {save_dir}")
    
    # Check database
    logger.info(f"Database path: {DB_PATH}")
    
    # Set resource path for PyInstaller
    if hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable
        logger.info(f"Running from PyInstaller bundle: {sys._MEIPASS}")

def main():
    """Application entry point."""
    try:
        # Setup
        setup_app()
        
        # Start the UI
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
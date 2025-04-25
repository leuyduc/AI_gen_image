import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.settings import DB_PATH

logger = logging.getLogger(__name__)

class Database:
    """Database wrapper for storing image history."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db_exists()
        logger.info(f"Database initialized at {db_path}")
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist."""
        # Make sure directory exists
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create history table if it doesn't exist
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
    
    def add_image(self, prompt: str, filename: str, filepath: str, provider: str = "unknown",
                width: int = None, height: int = None, extra_data: str = None) -> int:
        """Add a new image to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO images (prompt, filename, filepath, provider, created_at, width, height, extra_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prompt, 
            filename, 
            filepath, 
            provider, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            width,
            height,
            extra_data
        ))
        
        # Get the ID of the inserted row
        image_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Added image to database with ID {image_id}")
        return image_id
    
    def get_all_images(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all images from the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM images
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        conn.close()
        return results
    
    def search_images(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for images matching the search term."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search in prompt field
        cursor.execute('''
        SELECT * FROM images
        WHERE prompt LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        ''', (f'%{search_term}%', limit))
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        conn.close()
        return results
    
    def get_image(self, image_id: int) -> Optional[Dict[str, Any]]:
        """Get an image by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def delete_image(self, image_id: int) -> bool:
        """Delete an image from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
        
        # Check if a row was affected
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Deleted image with ID {image_id}, success: {success}")
        return success 
"""
Component for administrative database tasks within the booking module.
"""
import logging
import sqlite3
from pathlib import Path
from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def admin_reset_database(_db_path: str = None) -> bool:
    """
    Clear all records from the bookings table for administrative or testing purposes.

    Args:
        _db_path (str, optional): An injected database path for testing overrides.

    Returns:
        bool: True if the database reset was successful, False otherwise.
    """
    settings = get_settings()
    db_path = Path(_db_path) if _db_path else settings.db_path
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Delete all records from the bookings table
        cur.execute("DELETE FROM bookings")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

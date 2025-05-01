"""Data cleanup module for voice attendance system."""
import os
from datetime import datetime, timedelta
import sqlite3
from modules.utils import CONFIG, logger
from modules.db_manager import log_event

def cleanup_temp_samples(max_age_days=1):
    """Clean up temporary voice samples older than specified days."""
    try:
        temp_dir = CONFIG["attendance_temp"]
        current_time = datetime.now()
        cleaned = 0

        for file in os.listdir(temp_dir):
            if not file.endswith('.wav'):
                continue
                
            file_path = os.path.join(temp_dir, file)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if current_time - file_time > timedelta(days=max_age_days):
                os.remove(file_path)
                cleaned += 1
        
        if cleaned > 0:
            log_event("CLEANUP", f"Removed {cleaned} old temporary voice samples")
            logger.info(f"Cleaned up {cleaned} temporary voice samples")
            
    except Exception as e:
        logger.error(f"Error cleaning up temporary samples: {str(e)}")

def archive_old_attendance_records(months_to_keep=6):
    """Archive attendance records older than specified months."""
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        
        # Create archive table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT,
                timestamp DATETIME,
                archived_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=30 * months_to_keep)).strftime("%Y-%m-%d")
        
        # Move old records to archive
        cursor.execute("""
            INSERT INTO attendance_archive (user_id, name, status, timestamp)
            SELECT user_id, name, status, timestamp 
            FROM attendance 
            WHERE DATE(timestamp) < ?
        """, (cutoff_date,))
        
        # Delete archived records from main table
        cursor.execute("DELETE FROM attendance WHERE DATE(timestamp) < ?", (cutoff_date,))
        
        archived_count = cursor.rowcount
        conn.commit()
        
        if archived_count > 0:
            log_event("ARCHIVE", f"Archived {archived_count} attendance records older than {months_to_keep} months")
            logger.info(f"Archived {archived_count} old attendance records")
            
    except Exception as e:
        logger.error(f"Error archiving attendance records: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
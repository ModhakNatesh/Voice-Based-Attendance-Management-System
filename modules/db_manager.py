"""Database manager for attendance system."""
import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import bcrypt
import pyotp
from modules.utils import CONFIG, validate_user_id, is_strong_password, logger

def init_db():
    """Initializes all database tables."""
    conn = sqlite3.connect(CONFIG["attendance_db"])
    cursor = conn.cursor()
    
    # Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Archive Table
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
    
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            two_fa_secret TEXT,
            user_id TEXT UNIQUE 
        )
    """)
    
    # Add default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        hashed_pwd = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            ("admin", hashed_pwd, "admin", pyotp.random_base32(), "admin")
        )
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def log_event(log_type, message):
    """Logs events to the database."""
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (log_type, message) VALUES (?, ?)",
            (log_type, f"{datetime.now()}: {message}")
        )
        conn.commit()
        logger.info(f"{log_type}: {message}")
    except Exception as e:
        logger.error(f"Failed to log event: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def register_student_db(student_name, user_id):
    """Handles database part of student registration."""
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        
        # 1. Verify unique user_id
        cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone():
            raise ValueError(f"User ID {user_id} already exists")
        
        # 2. Add to users table (student role)
        temp_password = pyotp.random_base32()[:8]  # Temporary password
        hashed_pwd = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt())
        two_fa_secret = pyotp.random_base32()
        
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            (user_id, hashed_pwd, "student", two_fa_secret, user_id)
        )
        conn.commit()
        log_event("INFO", f"Initialized registration for {student_name} ({user_id})")
        return temp_password
        
    except Exception as e:
        log_event("ERROR", f"DB registration failed: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def rollback_student_registration(user_id):
    """Cleans up failed registrations."""
    delete_student(user_id)
    log_event("WARNING", f"Rolled back registration for {user_id}")

def add_user(username, password, role, user_id=None):
    """Adds user with validation."""
    
    try:
        # Input validation
        if not validate_user_id(username):
            raise ValueError("Username must be 3-20 alphanumeric chars")
        if not is_strong_password(password):
            raise ValueError("Password needs 8+ chars with uppercase, number, and special char")
        if role.lower() not in ("admin", "teacher", "student"):
            raise ValueError("Invalid role")

        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        two_fa_secret = pyotp.random_base32()
        
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            (username, hashed_pwd, role.lower(), two_fa_secret, user_id)
        )
        conn.commit()
        log_event("INFO", f"Added {role} user: {username}")
        return True
        
    except sqlite3.IntegrityError:
        log_event("ERROR", f"Username {username} exists")
        return False
    except ValueError as e:
        log_event("ERROR", f"Invalid input: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def verify_user(username, password):
    """Authenticates a user."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, role FROM users WHERE username=?",
            (username,)
        )
        result = cursor.fetchone()
        
        if result and bcrypt.checkpw(password.encode(), result[0]):
            return result[1]  # Returns role if authenticated
        return None
    except Exception as e:
        log_event("ERROR", f"Authentication error: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_2fa_secret(username):
    """Gets the 2FA secret for a user."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute("SELECT two_fa_secret FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if conn:
            conn.close()

def verify_2fa(username, token):
    """Validates a 2FA token."""
    secret = get_2fa_secret(username)
    if not secret:
        return False
    return pyotp.TOTP(secret).verify(token)

def mark_attendance(user_id, name):
    """Marks attendance if not already marked today."""
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE user_id=? AND DATE(timestamp)=?
        """, (user_id, today))
        if cursor.fetchone():
            logger.warning(f"{name} already marked present today.")
            return False
        else:
            cursor.execute("""
                INSERT INTO attendance (user_id, name) 
                VALUES (?, ?)
            """, (user_id, name))
            conn.commit()
            logger.info(f"Attendance marked for {name}.")
            return True
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def fetch_attendance_by_student(user_id):
    """Fetches attendance for a specific student."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM attendance WHERE user_id=?",
            (user_id,)
        )
        records = cursor.fetchall()
        return records
    except Exception as e:
        logger.error(f"Error fetching student attendance: {e}")
        return []
    finally:
        if conn:
            conn.close()


def fetch_attendance_by_date(date):
    """Fetches attendance for a specific date (YYYY-MM-DD)."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance WHERE DATE(timestamp)=?", (date,))
        records = cursor.fetchall()
        return records
    except Exception as e:
        logger.error(f"Error fetching attendance by date: {e}")
        return []
    finally:
        if conn:
            conn.close()

def fetch_attendance_by_range(start_date, end_date):
    """Fetches attendance between two dates (inclusive)."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE DATE(timestamp) BETWEEN ? AND ?
        """, (start_date, end_date))
        records = cursor.fetchall()
        return records
    except Exception as e:
        logger.error(f"Error fetching attendance by range: {e}")
        return []
    finally:
        if conn:
            conn.close()

def calculate_attendance_percentage(start_date, end_date, user_id=None):
    """Calculates attendance % for all students or a specific student in a date range."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Calculate working days (Mon-Fri)
        delta = end_date - start_date
        working_days = sum(1 for i in range(delta.days + 1)
                           if (start_date + timedelta(days=i)).weekday() < 5)
        
        if working_days == 0:
            return []

        if user_id:
            cursor.execute("""
                SELECT username as student_id, 
                       (SELECT COUNT(*) FROM attendance 
                        WHERE user_id = u.user_id AND DATE(timestamp) BETWEEN ? AND ?) as present_days
                FROM users u
                WHERE u.role = 'student' AND u.user_id = ?
            """, (start_date, end_date, user_id))
        else:
            cursor.execute("""
                SELECT username as student_id, 
                       (SELECT COUNT(*) FROM attendance 
                        WHERE user_id = u.user_id AND DATE(timestamp) BETWEEN ? AND ?) as present_days
                FROM users u
                WHERE u.role = 'student'
            """, (start_date, end_date))

        rows = cursor.fetchall()
        result = []
        for row in rows:
            percentage = (row["present_days"] / working_days) * 100
            result.append({
                "student_id": row["student_id"],
                "name": row["student_id"],  # Adjust if you have a full name column
                "percentage": percentage
            })
        return result

    except Exception as e:
        logger.error(f"Error calculating attendance percentage: {e}")
        return []
    finally:
        if conn:
            conn.close()
            

def export_to_excel(start_date=None, end_date=None, user_id=None):
    """
    Exports attendance data to an Excel file.
    You can filter by date range and/or user_id.
    
    Parameters:
        start_date (str): Start date in format 'YYYY-MM-DD'
        end_date (str): End date in format 'YYYY-MM-DD'
        user_id (str): Student ID to filter by
    """
    try:
        import pandas as pd
        
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        
        base_query = "SELECT id, user_id, name, status, timestamp FROM attendance"
        conditions = []
        params = []
        
        # Apply filters only if they're provided
        if start_date and end_date:
            conditions.append("DATE(timestamp) BETWEEN ? AND ?")
            params.extend([start_date, end_date])
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY timestamp ASC"
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No records found for export with the given filters")
            return None
        
        df = pd.DataFrame(rows, columns=["ID", "User ID", "Name", "Status", "Timestamp"])
        
        downloads_path = str(Path.home() / "Downloads")
        filename = os.path.join(downloads_path, f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(filename, index=False)
        
        return filename
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return None

def delete_student(user_id):
    """Deletes a student with error handling."""
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        
        # Delete from users table
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        
        # Delete from attendance table
        cursor.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
        
        # Delete voice samples
        deleted_files = 0
        for file in os.listdir(CONFIG["audio_folder"]):
            if file.startswith(f"{user_id}_"):
                os.remove(os.path.join(CONFIG["audio_folder"], file))
                deleted_files += 1
        
        conn.commit()
        log_event("DELETE", f"Deleted student {user_id} and {deleted_files} samples.")
        
        logger.info(f"Deleted student {user_id}")
        return True
    except Exception as e:
        log_event("ERROR", f"Failed to delete {user_id}: {str(e)}")
        logger.error(f"Deletion failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_student_name(user_id):
    """Gets a student's name from their ID."""
    conn = None
    try:
        conn = sqlite3.connect(CONFIG["attendance_db"])
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM attendance WHERE user_id=? LIMIT 1", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting student name: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Initialize DB on first run
if not os.path.exists(CONFIG["attendance_db"]):
    init_db()
import os
import sys
import sqlite3
import datetime
import socket
import requests
import threading
import time
import shutil
import pytz
import json
import platform
import uuid



# ---------------------- Path Utilities ----------------------
def get_app_dir():
    """Gets the directory where the .exe or .py file is located"""
    if getattr(sys, "frozen", False):  # Running as .exe
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


# def get_data_dir():
#     """Gets the persistent data directory"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         return os.path.dirname(sys.executable)
#     else:
#         return os.path.dirname(os.path.abspath(__file__))

# def get_app_dir():
#     """Gets the directory where the .exe or .py file is located"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         return os.path.dirname(sys.executable)
#     else:
#         return os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    if getattr(sys, "frozen", False):
        # APPDATA ke andar FixHR folder banao
        data_dir = os.path.join(os.environ.get("APPDATA"), "FixHR")
    else:
        data_dir = os.path.join(get_app_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir






# ---------------------- Configuration ----------------------
DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "employees.db")
IMAGE_DIR = os.path.join(DATA_DIR, "profile_images")
os.makedirs(IMAGE_DIR, exist_ok=True)
SYNC_LOCK = threading.Lock()  # Lock to prevent multiple sync threads
IS_SYNCING = False  # Flag to track if sync is in progress
SYNC_INTERVAL = 300  # Sync interval in seconds (5 minutes, unused now)
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed syncs
RETRY_DELAY = 5  # Delay between retries in seconds

DEFAULT_APP_SETTINGS = {
    "auto_sync_enabled": "0",
    "auto_sync_time": "09:00",
    "sync_mode": "both",
    "auto_sync_last_run": "",
    "face_marking_enabled": "0",
    "blink_detection_enabled": "0",
    "blink_detection_count": "1",
}


def ensure_app_settings(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    for key, value in DEFAULT_APP_SETTINGS.items():
        cursor.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES (?, ?)
            """,
            (key, value),
        )



# ---------------------- Time Utilities ----------------------
class OfflinePunchHelper:
    @staticmethod
    # def get_accurate_indian_time():
    #     """Get IST time (UTC+5:30) without blocking network calls."""
    #     utc_now = datetime.datetime.utcnow()
    #     return utc_now + datetime.timedelta(hours=5, minutes=30)
    def get_accurate_indian_time():
        india_tz = pytz.timezone("Asia/Kolkata")
        return datetime.datetime.now(india_tz)


def get_current_date_str():
    """Get current date in DD-MM-YYYY format (IST) for storage"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%d-%m-%Y")


def get_current_time_str():
    """Get current time in 24-hour format (IST)"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%H:%M:%S")


def get_current_datetime_str():
    """Get current datetime in DD-MM-YYYY HH:mm:ss format (24-hour, IST)"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%d-%m-%Y %H:%M:%S")


def normalize_date(date_input):
    """Normalize date input to DD-MM-YYYY format (storage) using IST"""
    if date_input is None:
        return get_current_date_str()

    if isinstance(date_input, str):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.datetime.strptime(date_input, fmt)
                return parsed_date.strftime("%d-%m-%Y")
            except ValueError:
                continue
        return get_current_date_str()

    if isinstance(date_input, datetime.date):
        return date_input.strftime("%d-%m-%Y")

    if isinstance(date_input, datetime.datetime):
        return date_input.strftime("%d-%m-%Y")

    return get_current_date_str()


def normalize_time(time_input):
    """Normalize time input to 24-hour format.
    Prioritizes 24-hour format parsing to avoid misinterpreting noon (12:00) as midnight (00:00).
    """
    if time_input is None:
        return get_current_time_str()


# ---------------------- Device Identity Helpers ----------------------
def get_system_mac_address():
    """Return system MAC address in colon-separated format."""
    try:
        mac_int = uuid.getnode()
        mac_hex = f"{mac_int:012x}"
        mac = ":".join(mac_hex[i : i + 2] for i in range(0, 12, 2))
        return mac.upper()
    except Exception as exc:
        print(f"[WARNING] Unable to determine MAC address: {exc}")
        return "00:00:00:00:00:00"


def get_device_name():
    """Return a stable device/host name."""
    try:
        return platform.node() or socket.gethostname() or "Unknown-Device"
    except Exception:
        return "Unknown-Device"


def get_sync_device_metadata():
    """Collect device metadata that should accompany every sync payload."""
    return {
        "device_name": get_device_name(),
        "system_mac_address": get_system_mac_address(),
    }

    if isinstance(time_input, str):
        # First try 24-hour format (HH:MM:SS) - this is the standard format we use
        try:
            parsed_time = datetime.datetime.strptime(time_input, "%H:%M:%S")
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            pass
        
        # Try 24-hour format without seconds (HH:MM)
        try:
            parsed_time = datetime.datetime.strptime(time_input, "%H:%M")
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            pass
        
        # Try 12-hour format with AM/PM (I:MM:SS %p)
        try:
            parsed_time = datetime.datetime.strptime(time_input, "%I:%M:%S %p")
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            pass
        
        # Try 12-hour format with AM/PM without seconds (I:MM %p)
        try:
            parsed_time = datetime.datetime.strptime(time_input, "%I:%M %p")
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            pass
        
        # Last resort: try 12-hour format without AM/PM (but this is risky - defaults to AM)
        # Only use this if we can't parse it any other way
        try:
            # If it's "12:XX:XX" without AM/PM, assume it's noon (12:00 PM), not midnight
            if time_input.startswith("12:") and len(time_input) >= 5:
                # Parse as 12:MM:SS PM (noon)
                time_with_pm = time_input + " PM"
                parsed_time = datetime.datetime.strptime(time_with_pm, "%I:%M:%S %p")
                return parsed_time.strftime("%H:%M:%S")
            else:
                # For other times without AM/PM, try parsing as AM first
                parsed_time = datetime.datetime.strptime(time_input, "%I:%M:%S")
                return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            # If all parsing fails, return current time
            return get_current_time_str()

    if isinstance(time_input, datetime.datetime):
        return time_input.strftime("%H:%M:%S")

    return str(time_input)


def _parse_storage_date(date_text):
    try:
        return datetime.datetime.strptime(date_text, "%d-%m-%Y").date()
    except Exception:
        return None


def _date_from_input(date_input):
    if date_input in (None, ""):
        return None
    try:
        normalized = normalize_date(date_input)
        return datetime.datetime.strptime(normalized, "%d-%m-%Y").date()
    except Exception:
        return None



# ---------------------- Database Init ----------------------
def init_db():
    """Initialize the database with proper schema and strict constraints"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT UNIQUE NOT NULL,
            emp_b_id TEXT, 
            emp_full_name TEXT NOT NULL,
            emp_phone TEXT,
            emp_email TEXT,
            emp_profile_photo TEXT,
            emp_profile_image_local TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_b_id TEXT,
            emp_code TEXT NOT NULL,
            emp_full_name TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_date TEXT,
            checkout_time TEXT,
            status TEXT DEFAULT 'CHECKED_IN' CHECK(status IN ('CHECKED_IN', 'CHECKED_OUT')),
            mode TEXT DEFAULT 'Offline-Face',
            sync INTEGER DEFAULT 0 CHECK(sync IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_employee_date UNIQUE(emp_code, checkin_date)
        )
        """
   )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_b_id TEXT,
            emp_code TEXT NOT NULL,
            emp_full_name TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_date TEXT,
            checkout_time TEXT,
            status TEXT DEFAULT 'CHECKED_IN' CHECK(status IN ('CHECKED_IN', 'CHECKED_OUT')),
            mode TEXT DEFAULT 'Offline-Face',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_employee_date_daily UNIQUE(emp_code, checkin_date)
        )
        """
    )

    try:
        cursor.execute("PRAGMA table_info(attendance_logs)")
        cols = [row[1].lower() for row in cursor.fetchall()]
        if "mode" not in cols:
            cursor.execute(
                "ALTER TABLE attendance_logs ADD COLUMN mode TEXT DEFAULT 'Offline-Face'"
            )
    except Exception:
        pass

    try:
        cursor.execute("PRAGMA table_info(daily_attendance_logs)")
        cols = [row[1].lower() for row in cursor.fetchall()]
        if "mode" not in cols:
            cursor.execute(
                "ALTER TABLE daily_attendance_logs ADD COLUMN mode TEXT DEFAULT 'Offline-Face'"
            )
    except Exception:
        pass

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            business_id TEXT,
            business_name TEXT,
            branch_id TEXT,
            user_id TEXT,
            phone TEXT,
            emp_code TEXT,
            role_name TEXT,
            role_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    try:
        cursor.execute("PRAGMA table_info(sessions)")
        session_cols = [row[1].lower() for row in cursor.fetchall()]
        column_defaults = {
            "business_id": "TEXT",
            "business_name": "TEXT",
            "branch_id": "TEXT",
            "user_id": "TEXT",
            "phone": "TEXT",
            "emp_code": "TEXT",
            "role_name": "TEXT",
            "role_id": "TEXT",
        }
        for col, col_type in column_defaults.items():
            if col not in session_cols:
                cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_type}")
    except Exception:
        pass
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_sync_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            last_sync_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_fail_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            payload TEXT,
            error_message TEXT,
            attempts INTEGER DEFAULT 0,
            last_attempt_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(emp_code, checkin_date, checkin_time)
        )
        """
    )
    
    # Create attendance_sync_logs table to store all attendance records for syncing
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_b_id TEXT,
            emp_code TEXT NOT NULL,
            emp_full_name TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_date TEXT,
            checkout_time TEXT,
            status TEXT DEFAULT 'CHECKED_IN' CHECK(status IN ('CHECKED_IN', 'CHECKED_OUT')),
            mode TEXT DEFAULT 'Offline-Face',
            sync_status INTEGER DEFAULT 0 CHECK(sync_status IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Create index for attendance_sync_logs for better query performance
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_logs_emp_date ON attendance_sync_logs(emp_code, checkin_date)
        """
    )
    
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON attendance_sync_logs(sync_status, checkin_date)
        """
    )
    
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_logs_date ON attendance_sync_logs(checkin_date)
        """
    )
    
    ensure_app_settings(cursor)

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_emp_code ON employees(emp_code)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance_logs(emp_code, checkin_date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance_logs(status, checkin_date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_daily_attendance_emp_date ON daily_attendance_logs(emp_code, checkin_date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_daily_attendance_status ON daily_attendance_logs(status, checkin_date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_session_employee_id ON sessions(employee_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_metadata ON sync_metadata(id)
        """
    )

    conn.commit()
    conn.close()
    print(
        "[INFO] Database initialized with strict attendance constraints including daily_attendance_logs and attendance_sync_logs"
    )


# ---------------------- Enhanced Attendance Functions ----------------------
def get_employee_attendance_status(emp_code, target_date=None, table="attendance_logs"):
    """
    Get detailed attendance status for an employee on a specific date from specified table
    Returns: dict with comprehensive status information
    """
    target_date = normalize_date(target_date)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"""
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM {table} 
        WHERE emp_code = ? AND checkin_date = ?
        ORDER BY id DESC
        LIMIT 1
    """
    cursor.execute(query, (emp_code, target_date))
    result = cursor.fetchone()
    conn.close()

    if result:
        has_checkout = result[7] is not None
        return {
            "exists": True,
            "id": result[0],
            "emp_b_id": result[1],
            "emp_code": result[2],
            "emp_full_name": result[3],
            "checkin_date": result[4],
            "checkin_time": result[5],
            "checkout_date": result[6],
            "checkout_time": result[7],
            "status": result[8],
            "mode": result[9] if len(result) > 9 else "Offline-Face",
            "created_at": result[10],
            "updated_at": result[11],
            "has_checked_in": True,
            "has_checked_out": has_checkout,
            "can_checkin": False,
            "can_checkout": not has_checkout,
        }
    else:
        return {
            "exists": False,
            "has_checked_in": False,
            "has_checked_out": False,
            "can_checkin": True,
            "can_checkout": False,
        }


def checkin_employee(
    emp_b_id, emp_code, emp_full_name, checkin_date=None, checkin_time=None
):
    """
    Check in employee with complete validation - ONLY ONE ENTRY PER DAY ALLOWED
    Returns: dict with success status and message
    """
    checkin_date = normalize_date(checkin_date)
    checkin_time = normalize_time(checkin_time)

    print(
        f"[DEBUG] Attempting checkin for {emp_code} on {checkin_date} at {checkin_time}"
    )

    status = get_employee_attendance_status(
        emp_code, checkin_date, table="attendance_logs"
    )

    if status["exists"]:
        if status["has_checked_out"]:
            return {
                "success": False,
                "message": f"Employee {emp_code} has already completed full attendance for {checkin_date} in attendance_logs",
                "action": "ALREADY_COMPLETED",
                "details": status,
            }
        else:
            return {
                "success": False,
                "message": f"Employee {emp_code} is already checked in for {checkin_date} in attendance_logs. Next action: CHECKOUT",
                "action": "ALREADY_CHECKED_IN",
                "details": status,
            }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO attendance_logs (
                emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, status, mode
            )
            VALUES (?, ?, ?, ?, ?, 'CHECKED_IN', 'Offline-Face')
            """,
            (emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time),
        )

        cursor.execute(
            """
            INSERT INTO daily_attendance_logs (
                emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, status, mode
            )
            VALUES (?, ?, ?, ?, ?, 'CHECKED_IN', 'Offline-Face')
            """,
            (emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time),
        )

        # Insert into attendance_sync_logs for syncing
        cursor.execute(
            """
            INSERT INTO attendance_sync_logs (
                emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, status, mode, sync_status
            )
            VALUES (?, ?, ?, ?, ?, 'CHECKED_IN', 'Offline-Face', 0)
            """,
            (emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time),
        )

        conn.commit()
        record_id = cursor.lastrowid

        print(
            f"✅ CHECK-IN successful for {emp_code} ({emp_full_name}) on {checkin_date} at {checkin_time}"
        )

        return {
            "success": True,
            "message": f"Employee {emp_full_name} checked in successfully at {checkin_time}",
            "action": "CHECKED_IN",
            "record_id": record_id,
            "checkin_date": checkin_date,
            "checkin_time": checkin_time,
            "emp_code": emp_code,
            "emp_full_name": emp_full_name,
        }

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Integrity constraint violation: {e}")
        return {
            "success": False,
            "message": f"Employee {emp_code} already has an attendance record for {checkin_date}",
            "action": "DUPLICATE_ENTRY",
            "error": str(e),
        }
    except Exception as e:
        print(f"[ERROR] Database error during check-in: {e}")
        return {
            "success": False,
            "message": f"Database error during check-in: {str(e)}",
            "action": "DATABASE_ERROR",
            "error": str(e),
        }
    finally:
        conn.close()


# def checkout_employee(emp_code, checkout_date=None, checkout_time=None):
#     """
#     Check out employee - updates checkout_time every time
#     """
#     checkout_date = normalize_date(checkout_date)
#     checkout_time = normalize_time(checkout_time)

#     print(
#         f"[DEBUG] Updating checkout for {emp_code} on {checkout_date} at {checkout_time}"
#     )

#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     try:
#         cursor.execute(
#             """
#             UPDATE attendance_logs
#             SET checkout_date = ?,
#                 checkout_time = ?,
#                 status = 'CHECKED_OUT',
#                 updated_at = CURRENT_TIMESTAMP
#             WHERE emp_code = ? AND checkin_date = ?
#             """,
#             (checkout_date, checkout_time, emp_code, checkout_date),
#         )
#         attendance_rows_affected = cursor.rowcount

#         cursor.execute(
#             """
#             UPDATE daily_attendance_logs
#             SET checkout_date = ?,
#                 checkout_time = ?,
#                 status = 'CHECKED_OUT',
#                 updated_at = CURRENT_TIMESTAMP
#             WHERE emp_code = ? AND checkin_date = ?
#             """,
#             (checkout_date, checkout_time, emp_code, checkout_date),
#         )
#         daily_rows_affected = cursor.rowcount

#         if attendance_rows_affected == 0:
#             return {
#                 "success": False,
#                 "message": f"No check-in record found for {emp_code} on {checkout_date} in attendance_logs",
#                 "action": "NO_RECORD",
#                 "attendance_rows_affected": attendance_rows_affected,
#                 "daily_rows_affected": daily_rows_affected,
#             }

#         conn.commit()

#         print(
#             f"✅ CHECK-OUT updated for {emp_code} on {checkout_date} at {checkout_time}"
#         )

#         return {
#             "success": True,
#             "message": f"Checkout time updated to {checkout_time}",
#             "action": "CHECKED_OUT_UPDATED",
#             "checkout_date": checkout_date,
#             "checkout_time": checkout_time,
#             "emp_code": emp_code,
#         }

#     except Exception as e:
#         print(f"[ERROR] Database error: {e}")
#         return {"success": False, "message": str(e), "action": "ERROR"}
#     finally:
#         conn.close()


def checkout_employee(emp_code, checkout_date=None, checkout_time=None, force_checkout=False):
    """
    Check out employee.

    - Updates checkout_time; previous checkout is ignored.
    - Enforces 10-minute rule only for first checkout after check-in.
    - If no daily_attendance_logs row exists, insert it.
    - force_checkout=True bypasses the 10-minute rule.
    """
    checkout_date = normalize_date(checkout_date)
    checkout_time = normalize_time(checkout_time)

    print(f"[DEBUG] Attempting checkout for {emp_code} on {checkout_date} at {checkout_time}")

    # Get current attendance status
    status = get_employee_attendance_status(emp_code, checkout_date, table="attendance_logs")

    if not status["exists"] or not status["has_checked_in"]:
        return {
            "success": False,
            "message": f"No check-in record found for {emp_code} on {checkout_date}",
            "action": "NO_CHECKIN_RECORD",
        }

    # Parse datetime in 24-hour format
    try:
        checkin_dt = datetime.datetime.strptime(
            f"{status['checkin_date']} {status['checkin_time']}", "%d-%m-%Y %H:%M:%S"
        )
        checkout_dt = datetime.datetime.strptime(
            f"{checkout_date} {checkout_time}", "%d-%m-%Y %H:%M:%S"
        )
        time_diff_minutes = (checkout_dt - checkin_dt).total_seconds() / 60
    except ValueError as e:
        return {
            "success": False,
            "message": f"Invalid time format (expected 24-hour HH:MM:SS): {e}",
            "action": "INVALID_TIME_FORMAT",
        }

    # 10-minute rule applied only if first checkout
    if not force_checkout and not status["has_checked_out"] and time_diff_minutes < 10:
        return {
            "success": False,
            "message": f"Checkout too soon: {checkout_time} is {time_diff_minutes:.2f} mins after check-in {status['checkin_time']}",
            "action": "CHECKOUT_TOO_SOON",
            "time_difference_minutes": time_diff_minutes,
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Update attendance_logs and reset sync status to 0 (unsynced) when attendance is updated
        cursor.execute("""
            UPDATE attendance_logs
            SET checkout_date=?, checkout_time=?, status='CHECKED_OUT', 
                sync=0, updated_at=CURRENT_TIMESTAMP
            WHERE emp_code=? AND checkin_date=?
        """, (checkout_date, checkout_time, emp_code, status["checkin_date"]))

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "No attendance record found to update checkout",
                "action": "NO_RECORD",
            }

        # Update or insert daily_attendance_logs
        cursor.execute("""
            SELECT id FROM daily_attendance_logs WHERE emp_code=? AND checkin_date=?
        """, (emp_code, status["checkin_date"]))
        daily_row = cursor.fetchone()

        if daily_row:
            cursor.execute("""
                UPDATE daily_attendance_logs
                SET checkout_date=?, checkout_time=?, status='CHECKED_OUT', updated_at=CURRENT_TIMESTAMP
                WHERE emp_code=? AND checkin_date=?
            """, (checkout_date, checkout_time, emp_code, status["checkin_date"]))
        else:
            cursor.execute("""
                INSERT INTO daily_attendance_logs (
                    emp_b_id, emp_code, emp_full_name,
                    checkin_date, checkin_time, checkout_date, checkout_time, status, mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'CHECKED_OUT', ?)
            """, (
                status["emp_b_id"], emp_code, status["emp_full_name"],
                status["checkin_date"], status["checkin_time"],
                checkout_date, checkout_time, status.get("mode", "Offline-Face")
            ))

        # Update or insert attendance_sync_logs for syncing
        cursor.execute("""
            SELECT id FROM attendance_sync_logs 
            WHERE emp_code=? AND checkin_date=? AND checkin_time=?
        """, (emp_code, status["checkin_date"], status["checkin_time"]))
        sync_row = cursor.fetchone()

        if sync_row:
            # Update attendance_sync_logs and reset sync_status to 0 (unsynced) when attendance is updated
            cursor.execute("""
                UPDATE attendance_sync_logs
                SET checkout_date=?, checkout_time=?, status='CHECKED_OUT', 
                    sync_status=0, updated_at=CURRENT_TIMESTAMP
                WHERE emp_code=? AND checkin_date=? AND checkin_time=?
            """, (checkout_date, checkout_time, emp_code, status["checkin_date"], status["checkin_time"]))
            print(f"[INFO] Reset sync_status to 0 for updated checkout: {emp_code} on {status['checkin_date']} {status['checkin_time']}")
        else:
            cursor.execute("""
                INSERT INTO attendance_sync_logs (
                    emp_b_id, emp_code, emp_full_name,
                    checkin_date, checkin_time, checkout_date, checkout_time, status, mode, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'CHECKED_OUT', ?, 0)
            """, (
                status["emp_b_id"], emp_code, status["emp_full_name"],
                status["checkin_date"], status["checkin_time"],
                checkout_date, checkout_time, status.get("mode", "Offline-Face")
            ))

        conn.commit()
        print(f"✅ Checkout updated for {emp_code} on {checkout_date} at {checkout_time}")

        return {
            "success": True,
            "message": f"Checkout time updated to {checkout_time}",
            "action": "CHECKED_OUT_UPDATED",
            "checkout_date": checkout_date,
            "checkout_time": checkout_time,
            "emp_code": emp_code,
        }

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "action": "DATABASE_ERROR",
        }
    finally:
        conn.close()





def get_next_attendance_action(emp_code, current_date=None):
    """
    Get the next required action for an employee's attendance
    Returns: 'CHECKIN', 'CHECKOUT', or 'COMPLETED'
    """
    current_date = normalize_date(current_date)

    status = get_employee_attendance_status(
        emp_code, current_date, table="attendance_logs"
    )

    if not status["has_checked_in"]:
        return "CHECKIN"
    elif not status["has_checked_out"]:
        return "CHECKOUT"
    else:
        return "COMPLETED"


def process_employee_attendance(
    emp_b_id, emp_code, emp_full_name, current_date=None, current_time=None
):
    """
    Smart attendance processing:
      - Ensures only one CHECKIN per employee per date
      - Allows multiple CHECKOUT updates
    """
    current_date = normalize_date(current_date)
    current_time = normalize_time(current_time)

    print(
        f"[INFO] Processing attendance for {emp_code} ({emp_full_name}) on {current_date}"
    )

    next_action = get_next_attendance_action(emp_code, current_date)
    print(f"[INFO] Next required action: {next_action}")

    if next_action == "CHECKIN":
        return checkin_employee(
            emp_b_id, emp_code, emp_full_name, current_date, current_time
        )

    elif next_action == "CHECKOUT":
        result = checkout_employee(emp_code, current_date, current_time)
        result["message"] = (
            "Checkout time updated successfully"
            if result["success"]
            else result["message"]
        )
        return result

    else:
        result = checkout_employee(emp_code, current_date, current_time)
        result["action"] = "CHECKOUT_UPDATE"
        result["next_action"] = "NONE"
        result["message"] = (
            "Checkout time updated again"
            if result["success"]
            else "No record found for updating checkout"
        )
        return result


def can_employee_checkin(emp_code, current_date=None):
    """Check if employee can check in today"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(
        emp_code, current_date, table="attendance_logs"
    )
    return status["can_checkin"]


def can_employee_checkout(emp_code, current_date=None):
    """Check if employee can check out today"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(
        emp_code, current_date, table="attendance_logs"
    )
    return status["can_checkout"]


def has_checkin_today(emp_code, current_date=None):
    """Check if employee has checked in on given date"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(
        emp_code, current_date, table="attendance_logs"
    )
    return status["has_checked_in"]


def has_completed_attendance_today(emp_code, current_date=None):
    """Check if employee has completed full attendance for the day"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(
        emp_code, current_date, table="attendance_logs"
    )
    return status["has_checked_in"] and status["has_checked_out"]


def get_attendance_logs(emp_code=None, status_filter=None, table="attendance_logs"):
    """Retrieve attendance logs for the current date from specified table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current_date = get_current_date_str()

    query = f"""
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at, sync
        FROM {table}
        WHERE checkin_date = ?
    """
    params = [current_date]

    if emp_code:
        query += " AND emp_code = ?"
        params.append(emp_code)

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY updated_at DESC, checkin_time DESC"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    logs = []
    for row in results:
        logs.append(
            {
                "id": row[0],
                "emp_b_id": row[1],
                "emp_code": row[2],
                "emp_full_name": row[3],
                "checkin_date": row[4],
                "checkin_time": row[5],
                "checkout_date": row[6],
                "checkout_time": row[7],
                "status": row[8],
                "mode": row[9] if len(row) > 9 else "Offline-Face",
                "created_at": row[10],
                "updated_at": row[11],
                "is_complete": row[7] is not None,
                "sync": row[12] if row[12] is not None else 0,
            }
        )

    return logs


def get_daily_attendance_summary(target_date=None, table="attendance_logs"):
    """Get daily attendance summary with statistics from specified table"""
    target_date = normalize_date(target_date)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"""
        SELECT emp_code, emp_full_name, checkin_time, checkout_time, status, mode
        FROM {table} 
        WHERE checkin_date = ?
        ORDER BY checkin_time
    """
    cursor.execute(query, (target_date,))
    records = cursor.fetchall()
    conn.close()

    summary = {
        "date": target_date,
        "total_employees": len(records),
        "checked_in_only": 0,
        "completed_attendance": 0,
        "records": [],
    }

    for record in records:
        emp_code, emp_full_name, checkin_time, checkout_time, status, mode = record

        record_data = {
            "emp_code": emp_code,
            "emp_full_name": emp_full_name,
            "checkin_time": checkin_time,
            "checkout_time": checkout_time,
            "status": status,
            "mode": mode,
            "is_complete": checkout_time is not None,
        }

        summary["records"].append(record_data)

        if checkout_time is None:
            summary["checked_in_only"] += 1
        else:
            summary["completed_attendance"] += 1

    return summary


# ---------------------- Employee Functions ----------------------
def employee_exists(emp_code):
    """Check if employee already exists in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees WHERE emp_code = ?", (emp_code,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists


def update_employee(
    emp_code,
    emp_b_id,
    emp_full_name,
    emp_phone,
    emp_email,
    emp_profile_photo,
    emp_profile_image_local,
):
    """Update existing employee record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE employees 
        SET emp_b_id = ?, emp_full_name = ?, emp_phone = ?, emp_email = ?, 
            emp_profile_photo = ?, emp_profile_image_local = ?, updated_at = CURRENT_TIMESTAMP
        WHERE emp_code = ?
        """,
        (
            emp_b_id,
            emp_full_name,
            emp_phone,
            emp_email,
            emp_profile_photo,
            emp_profile_image_local,
            emp_code,
        ),
    )

    conn.commit()
    conn.close()


def insert_employee(
    emp_code,
    emp_b_id,
    emp_full_name,
    emp_phone,
    emp_email,
    emp_profile_photo,
    emp_profile_image_local,
):
    """Insert new employee record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO employees (
            emp_code, emp_b_id, emp_full_name, emp_phone, emp_email,
            emp_profile_photo, emp_profile_image_local
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            emp_code,
            emp_b_id,
            emp_full_name,
            emp_phone,
            emp_email,
            emp_profile_photo,
            emp_profile_image_local,
        ),
    )

    conn.commit()
    conn.close()


def get_employee_by_code(emp_code):
    """Retrieve employee information by employee code"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, emp_code, emp_b_id, emp_full_name, emp_phone, emp_email,
               emp_profile_photo, emp_profile_image_local, created_at, updated_at
        FROM employees 
        WHERE emp_code = ?
        """,
        (emp_code,),
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "id": result[0],
            "emp_code": result[1],
            "emp_b_id": result[2],
            "emp_full_name": result[3],
            "emp_phone": result[4],
            "emp_email": result[5],
            "emp_profile_photo": result[6],
            "emp_profile_image_local": result[7],
            "created_at": result[8],
            "updated_at": result[9],
        }
    return None


def get_all_employees():
    """Retrieve all employees from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, emp_code, emp_b_id, emp_full_name, emp_phone, emp_email,
               emp_profile_photo, emp_profile_image_local, created_at, updated_at
        FROM employees 
        ORDER BY emp_full_name
        """
    )
    results = cursor.fetchall()
    conn.close()

    employees = []
    for row in results:
        employees.append(
            {
                "id": row[0],
                "emp_code": row[1],
                "emp_b_id": row[2],
                "emp_full_name": row[3],
                "emp_phone": row[4],
                "emp_email": row[5],
                "emp_profile_photo": row[6],
                "emp_profile_image_local": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }
        )
    return employees


def get_employee_count():
    """Get total number of employees in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_setting(key, default=None):
    """Retrieve application setting value"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT value FROM app_settings WHERE key = ?",
        (key,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return default
    return row[0]


def set_setting(key, value):
    """Persist application setting value"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def get_sync_settings():
    """Return consolidated sync settings"""
    enabled = get_setting("auto_sync_enabled", DEFAULT_APP_SETTINGS["auto_sync_enabled"])
    auto_time = get_setting("auto_sync_time", DEFAULT_APP_SETTINGS["auto_sync_time"])
    mode = get_setting("sync_mode", DEFAULT_APP_SETTINGS["sync_mode"])
    last_run = get_setting("auto_sync_last_run", DEFAULT_APP_SETTINGS["auto_sync_last_run"])
    return {
        "auto_sync_enabled": enabled == "1",
        "auto_sync_time": auto_time or DEFAULT_APP_SETTINGS["auto_sync_time"],
        "sync_mode": (mode or "both").lower(),
        "auto_sync_last_run": last_run or "",
    }


def get_detection_settings():
    """Return detection related feature flags"""
    def _to_bool(value, default_key):
        if value is None:
            value = DEFAULT_APP_SETTINGS[default_key]
        return str(value) == "1"

    face_marking = get_setting("face_marking_enabled", DEFAULT_APP_SETTINGS["face_marking_enabled"])
    blink_enabled = get_setting("blink_detection_enabled", DEFAULT_APP_SETTINGS["blink_detection_enabled"])
    blink_count = get_setting("blink_detection_count", DEFAULT_APP_SETTINGS["blink_detection_count"])

    try:
        blink_count_value = max(1, int(blink_count))
    except (TypeError, ValueError):
        blink_count_value = 1

    return {
        "face_marking_enabled": _to_bool(face_marking, "face_marking_enabled"),
        "blink_detection_enabled": _to_bool(blink_enabled, "blink_detection_enabled"),
        "blink_detection_count": blink_count_value,
    }


def record_sync_failure(log, error_message, attempts=1):
    """Store or update failed sync payload"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        payload = json.dumps(log)
    except Exception:
        payload = ""
    cursor.execute(
        """
        INSERT INTO sync_fail_queue (
            emp_code, checkin_date, checkin_time, payload, error_message, attempts, last_attempt_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(emp_code, checkin_date, checkin_time)
        DO UPDATE SET
            payload = excluded.payload,
            error_message = excluded.error_message,
            attempts = excluded.attempts,
            last_attempt_at = CURRENT_TIMESTAMP
        """,
        (
            log.get("emp_code"),
            log.get("checkin_date"),
            log.get("checkin_time"),
            payload,
            error_message,
            attempts,
        ),
    )
    conn.commit()
    conn.close()


def clear_failed_sync(emp_code, checkin_date, checkin_time):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM sync_fail_queue
        WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
        """,
        (emp_code, checkin_date, checkin_time),
    )
    conn.commit()
    conn.close()


def get_failed_sync_records():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, emp_code, checkin_date, checkin_time, attempts, last_attempt_at, error_message, payload
        FROM sync_fail_queue
        ORDER BY last_attempt_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    records = []
    for row in rows:
        records.append(
            {
                "id": row[0],
                "emp_code": row[1],
                "checkin_date": row[2],
                "checkin_time": row[3],
                "attempts": row[4],
                "last_attempt_at": row[5],
                "error_message": row[6],
                "payload": row[7],
            }
        )
    return records


# ---------------------- Utility Functions ----------------------
def get_sqlite_version():
    """Return SQLite database engine version"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sqlite_version();")
    version = cursor.fetchone()[0]
    conn.close()
    return version


def reset_database(clear_data_only=True):
    """Reset the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if clear_data_only:
        print("⚠️ Deleting all rows but keeping schema...")
        cursor.execute("DELETE FROM employees;")
        cursor.execute("DELETE FROM attendance_logs;")
        cursor.execute("DELETE FROM daily_attendance_logs;")
    else:
        print("⚠️ Dropping all tables (schema will be lost)...")
        cursor.execute("DROP TABLE IF EXISTS employees;")
        cursor.execute("DROP TABLE IF EXISTS attendance_logs;")
        cursor.execute("DROP TABLE IF EXISTS daily_attendance_logs;")

    conn.commit()
    conn.close()

    if not clear_data_only:
        init_db()
        print("✅ Database schema recreated.")


def clear_daily_attendance_logs():
    """Clear all records from daily_attendance_logs table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM daily_attendance_logs")
        rows_deleted = cursor.rowcount
        conn.commit()
        print(
            f"✅ Successfully cleared {rows_deleted} records from daily_attendance_logs"
        )
        return {
            "success": True,
            "message": f"Cleared {rows_deleted} records from daily_attendance_logs",
            "rows_deleted": rows_deleted,
        }
    except Exception as e:
        print(f"[ERROR] Failed to clear daily_attendance_logs: {e}")
        return {
            "success": False,
            "message": f"Failed to clear daily_attendance_logs: {str(e)}",
            "error": str(e),
        }
    finally:
        conn.close()


def verify_database():
    """Verify database setup and contents"""
    print(f"🔍 VERIFYING DATABASE")
    print(f"{'='*50}")
    print(f"Database file: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")
    print(f"SQLite Version: {get_sqlite_version()}")

    if os.path.exists(DB_PATH):
        try:
            count = get_employee_count()
            print(f"Employees in database: {count}")

            today_summary = get_daily_attendance_summary()
            print(f"\nToday's Attendance Summary ({today_summary['date']}):")
            print(f"  Total Records: {today_summary['total_employees']}")
            print(f"  Checked In Only: {today_summary['checked_in_only']}")
            print(f"  Completed: {today_summary['completed_attendance']}")

            employees = get_all_employees()
            if employees:
                print(f"\nSample employees (first 3):")
                for emp in employees[:3]:
                    print(
                        f"  - {emp['emp_code']}: {emp['emp_full_name']} (b_id: {emp['emp_b_id']})"
                    )

        except Exception as e:
            print(f"Error reading database: {e}")

    print(f"{'='*50}")


def validate_attendance_integrity():
    """Check for any attendance data integrity issues in both tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT emp_code, checkin_date, COUNT(*) as count
        FROM attendance_logs
        GROUP BY emp_code, checkin_date
        HAVING COUNT(*) > 1
    """
    )
    duplicates = cursor.fetchall()
    if duplicates:
        print(
            f"⚠️ WARNING: Found {len(duplicates)} duplicate attendance entries in attendance_logs:"
        )
        for emp_code, date, count in duplicates:
            print(f"  - {emp_code} on {date}: {count} entries")
    else:
        print("✅ No duplicate attendance entries found in attendance_logs")

    cursor.execute(
        """
        SELECT emp_code, checkin_date, COUNT(*) as count
        FROM daily_attendance_logs
        GROUP BY emp_code, checkin_date
        HAVING COUNT(*) > 1
    """
    )
    duplicates = cursor.fetchall()
    if duplicates:
        print(
            f"⚠️ WARNING: Found {len(duplicates)} duplicate attendance entries in daily_attendance_logs:"
        )
        for emp_code, date, count in duplicates:
            print(f"  - {emp_code} on {date}: {count} entries")
    else:
        print("✅ No duplicate attendance entries found in daily_attendance_logs")

    conn.close()


def get_attendance_by_date(date_selected, table="attendance_logs"):
    """Fetch all attendance logs for a specific date from specified table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"""
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
               checkout_date, checkout_time, status, mode, created_at, updated_at, sync
        FROM {table}
        WHERE checkin_date = ?
        ORDER BY updated_at DESC, checkin_time DESC
    """

    cursor.execute(query, (normalize_date(date_selected),))
    results = cursor.fetchall()
    conn.close()

    logs = []
    for row in results:
        logs.append(
            {
                "id": row[0],
                "emp_b_id": row[1],
                "emp_code": row[2],
                "emp_full_name": row[3],
                "checkin_date": row[4],
                "checkin_time": row[5],
                "checkout_date": row[6],
                "checkout_time": row[7],
                "status": row[8],
                "mode": row[9] if len(row) > 9 else "Offline-Face",
                "created_at": row[10],
                "updated_at": row[11],
                "is_complete": row[7] is not None,
                "sync": row[12] if row[12] is not None else 0,
            }
        )

    return logs


# ---------------------- Sync Functions ----------------------
def is_internet_available(timeout: float = 2.0) -> bool:
    """Return True if internet looks reachable (free, no external services)."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


def get_session_token():
    """Fetch the latest session token from the sessions table"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT token FROM sessions ORDER BY created_at DESC LIMIT 1
        """
    )
    result = cursor.fetchone()
    conn.close()
    token = result[0] if result else None
    print(f"[DEBUG] Retrieved session token: {token}")
    return token


def get_daily_attendance_logs(sync_mode="both", start_date=None, end_date=None):
    """Fetch data from both attendance_sync_logs and daily_attendance_logs with optional filters - only unsynced records.
    Checks both tables to ensure no records are missed (double check).
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    
    # Get unsynced records from attendance_sync_logs
    query_sync_logs = """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM attendance_sync_logs
        WHERE sync_status = 0
        ORDER BY checkin_date DESC, checkin_time DESC
    """
    cursor.execute(query_sync_logs)
    sync_logs_results = cursor.fetchall()
    
    # Get all records from daily_attendance_logs (to double check)
    query_daily_logs = """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM daily_attendance_logs
        ORDER BY checkin_date DESC, checkin_time DESC
    """
    cursor.execute(query_daily_logs)
    daily_logs_results = cursor.fetchall()
    conn.close()

    sync_mode = (sync_mode or "both").lower()
    if sync_mode not in ("both", "checkin", "checkout"):
        sync_mode = "both"

    start_dt = _date_from_input(start_date)
    end_dt = _date_from_input(end_date)

    # Use a set to track unique records (emp_code, checkin_date, checkin_time)
    seen_records = set()
    logs = []
    
    # Process attendance_sync_logs first (primary source)
    for row in sync_logs_results:
        row_date = _parse_storage_date(row[4])
        if start_dt and row_date and row_date < start_dt:
            continue
        if end_dt and row_date and row_date > end_dt:
            continue

        status = row[8]
        if sync_mode == "checkin" and status != "CHECKED_IN":
            continue
        if sync_mode == "checkout" and status != "CHECKED_OUT":
            continue

        # Normalize time to 24-hour format
        checkin_time_24h = normalize_time(row[5])
        checkout_time_24h = normalize_time(row[7]) if row[7] else None
        
        # Create unique key
        record_key = (row[2], row[4], checkin_time_24h)  # (emp_code, checkin_date, checkin_time)
        if record_key in seen_records:
            continue
        seen_records.add(record_key)

        logs.append(
            {
                "emp_code": row[2],
                "emp_b_id": row[1],
                "check_in_time": f"{row[4]} {checkin_time_24h}",  # 24-hour format
                "check_out_time": f"{row[6]} {checkout_time_24h}" if checkout_time_24h else None,  # 24-hour format
                "am_id": 1,
                "atd_checkin_method_id": 324,
                "id": row[0],
                "checkin_date": row[4],
                "checkin_time": checkin_time_24h,  # 24-hour format
            }
        )
    
    # Process daily_attendance_logs (double check - only add if not already synced or if updated after sync)
    # Reconnect to check sync status for daily_attendance_logs records
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    
    for row in daily_logs_results:
        row_date = _parse_storage_date(row[4])
        if start_dt and row_date and row_date < start_dt:
            continue
        if end_dt and row_date and row_date > end_dt:
            continue

        status = row[8]
        if sync_mode == "checkin" and status != "CHECKED_IN":
            continue
        if sync_mode == "checkout" and status != "CHECKED_OUT":
            continue

        # Normalize time to 24-hour format
        checkin_time_24h = normalize_time(row[5])
        checkout_time_24h = normalize_time(row[7]) if row[7] else None
        
        # Create unique key
        record_key = (row[2], row[4], checkin_time_24h)  # (emp_code, checkin_date, checkin_time)
        if record_key in seen_records:
            continue  # Already added from attendance_sync_logs
        
        # Check if this record exists in attendance_sync_logs and if it was updated after sync
        cursor.execute(
            """
            SELECT sync_status, updated_at FROM attendance_sync_logs
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (row[2], row[4], checkin_time_24h),
        )
        sync_record = cursor.fetchone()
        
        # Only add if:
        # 1. Not in attendance_sync_logs (needs sync)
        # 2. In attendance_sync_logs but unsynced (sync_status=0)
        # 3. In attendance_sync_logs and synced, but daily_attendance_logs was updated after sync (needs re-sync)
        should_add = False
        if not sync_record:
            # Not in sync_logs - needs sync
            should_add = True
        elif sync_record[0] == 0:
            # Unsynced - needs sync
            should_add = True
        elif sync_record[0] == 1:
            # Already synced - check if daily_attendance_logs was updated after sync
            sync_updated_at = sync_record[1]
            daily_updated_at = row[11]  # updated_at is at index 11
            if daily_updated_at and sync_updated_at:
                try:
                    # Compare timestamps - if daily was updated after sync, re-sync it
                    if isinstance(daily_updated_at, str) and isinstance(sync_updated_at, str):
                        # Parse timestamps and compare
                        daily_dt = datetime.datetime.strptime(daily_updated_at, "%Y-%m-%d %H:%M:%S") if len(daily_updated_at) > 10 else datetime.datetime.strptime(daily_updated_at, "%d-%m-%Y %H:%M:%S")
                        sync_dt = datetime.datetime.strptime(sync_updated_at, "%Y-%m-%d %H:%M:%S") if len(sync_updated_at) > 10 else datetime.datetime.strptime(sync_updated_at, "%d-%m-%Y %H:%M:%S")
                        if daily_dt > sync_dt:
                            should_add = True  # Daily was updated after sync - re-sync it
                            # Reset sync_status to 0 so it can be re-synced
                            cursor.execute(
                                """
                                UPDATE attendance_sync_logs
                                SET sync_status = 0, updated_at = CURRENT_TIMESTAMP
                                WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
                                """,
                                (row[2], row[4], checkin_time_24h),
                            )
                            conn.commit()
                            print(f"[INFO] Reset sync_status to 0 for updated record: {row[2]} on {row[4]} {checkin_time_24h}")
                except Exception as e:
                    # If timestamp parsing fails, don't re-sync
                    print(f"[WARNING] Failed to compare timestamps: {e}")
                    pass
        
        if should_add:
            seen_records.add(record_key)
            logs.append(
                {
                    "emp_code": row[2],
                    "emp_b_id": row[1],
                    "check_in_time": f"{row[4]} {checkin_time_24h}",  # 24-hour format
                    "check_out_time": f"{row[6]} {checkout_time_24h}" if checkout_time_24h else None,  # 24-hour format
                    "am_id": 1,
                    "atd_checkin_method_id": 324,
                    "id": row[0],
                    "checkin_date": row[4],
                    "checkin_time": checkin_time_24h,  # 24-hour format
                }
            )
    
    conn.close()
    
    print(
        "[DEBUG] Retrieved "
        f"{len(logs)} unsynced records from attendance_sync_logs and daily_attendance_logs (mode={sync_mode}, "
        f"start={start_date}, end={end_date})"
    )
    return logs


def check_if_record_already_synced(emp_code, checkin_date, checkin_time):
    """Check if a record is already synced in attendance_sync_logs"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT sync_status FROM attendance_sync_logs
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        result = cursor.fetchone()
        return result is not None and result[0] == 1
    except Exception:
        return False
    finally:
        conn.close()


def mark_sync_log_as_synced(emp_code, checkin_date, checkin_time):
    """Mark a record as synced in attendance_sync_logs by unique fields.
    If record doesn't exist, insert it from attendance_logs or daily_attendance_logs, then mark as synced.
    Always updates sync_status to 1 when API accepts the data, regardless of current status.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        # First, try to update existing record - update to synced (1) regardless of current status
        # This ensures that if attendance was updated and then synced, it's marked as synced
        cursor.execute(
            """
            UPDATE attendance_sync_logs
            SET sync_status = 1, updated_at = CURRENT_TIMESTAMP
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        rows_updated = cursor.rowcount
        conn.commit()
        
        if rows_updated > 0:
            print(
                f"✅ Successfully marked record as synced (emp_code={emp_code}, date={checkin_date}, time={checkin_time}) in attendance_sync_logs"
            )
            return {
                "success": True,
                "message": f"Marked record as synced for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                "rows_updated": rows_updated,
            }
        
        # Record doesn't exist - check if it exists
        cursor.execute(
            """
            SELECT id, sync_status FROM attendance_sync_logs
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Record exists - if it's already synced, that's fine, but we should have updated it above
            # This case shouldn't happen, but handle it gracefully
            if existing_record[1] == 1:
                print(
                    f"[INFO] Record already synced (emp_code={emp_code}, date={checkin_date}, time={checkin_time}) in attendance_sync_logs"
                )
                return {
                    "success": True,
                    "message": f"Record already synced for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                    "rows_updated": 0,
                }
        
        # Record doesn't exist - get it from attendance_logs or daily_attendance_logs
        # Try attendance_logs first
        cursor.execute(
            """
            SELECT emp_b_id, emp_full_name, checkout_date, checkout_time, status, mode
            FROM attendance_logs
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        record_data = cursor.fetchone()
        
        # If not found in attendance_logs, try daily_attendance_logs
        if not record_data:
            cursor.execute(
                """
                SELECT emp_b_id, emp_full_name, checkout_date, checkout_time, status, mode
                FROM daily_attendance_logs
                WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
                """,
                (emp_code, checkin_date, checkin_time),
            )
            record_data = cursor.fetchone()
        
        if record_data:
            # Insert new record with sync_status=1 (already synced since API accepted it)
            cursor.execute(
                """
                INSERT INTO attendance_sync_logs (
                    emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
                    checkout_date, checkout_time, status, mode, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    record_data[0],  # emp_b_id
                    emp_code,
                    record_data[1],  # emp_full_name
                    checkin_date,
                    checkin_time,
                    record_data[2],  # checkout_date
                    record_data[3],  # checkout_time
                    record_data[4],  # status
                    record_data[5],  # mode
                ),
            )
            conn.commit()
            print(
                f"✅ Inserted and marked as synced new record (emp_code={emp_code}, date={checkin_date}, time={checkin_time}) in attendance_sync_logs"
            )
            return {
                "success": True,
                "message": f"Inserted and marked as synced new record for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                "rows_updated": 1,
            }
        else:
            # Record not found in any table - this shouldn't happen if sync was successful
            print(
                f"[WARNING] No record found in attendance_logs or daily_attendance_logs for emp_code={emp_code}, date={checkin_date}, time={checkin_time}"
            )
            return {
                "success": False,
                "message": f"No record found in attendance_logs or daily_attendance_logs for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                "rows_updated": 0,
            }
    except Exception as e:
        print(f"[ERROR] Failed to mark record as synced: {e}")
        return {
            "success": False,
            "message": f"Failed to mark record as synced: {str(e)}",
            "error": str(e),
        }
    finally:
        conn.close()


def ensure_daily_log_synced(emp_code, checkin_date, checkin_time):
    """Ensure a record from daily_attendance_logs is also in attendance_sync_logs and marked as synced.
    This function handles the double-check requirement - if a record exists in daily_attendance_logs,
    it should also be in attendance_sync_logs and marked as synced.
    Uses 24-hour format for time matching.
    """
    # Normalize time to 24-hour format
    checkin_time_24h = normalize_time(checkin_time)
    
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        # Check if record exists in daily_attendance_logs (match by emp_code and date, then normalize time)
        cursor.execute(
            """
            SELECT emp_b_id, emp_full_name, checkin_time, checkout_date, checkout_time, status, mode
            FROM daily_attendance_logs
            WHERE emp_code = ? AND checkin_date = ?
            """,
            (emp_code, checkin_date),
        )
        daily_records = cursor.fetchall()
        
        # Find matching record by normalizing times
        daily_record = None
        for record in daily_records:
            record_checkin_time_24h = normalize_time(record[2])  # checkin_time is at index 2
            if record_checkin_time_24h == checkin_time_24h:
                daily_record = record
                break
        
        if daily_record:
            # Normalize checkout time if exists
            checkout_time_24h = normalize_time(daily_record[4]) if daily_record[4] else None
            
            # Check if it exists in attendance_sync_logs
            cursor.execute(
                """
                SELECT id, sync_status FROM attendance_sync_logs
                WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
                """,
                (emp_code, checkin_date, checkin_time_24h),
            )
            sync_record = cursor.fetchone()
            
            if sync_record:
                # Update sync_status if not already synced
                if sync_record[1] == 0:
                    cursor.execute(
                        """
                        UPDATE attendance_sync_logs
                        SET sync_status = 1, updated_at = CURRENT_TIMESTAMP
                        WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
                        """,
                        (emp_code, checkin_date, checkin_time_24h),
                    )
                    conn.commit()
                    print(f"✅ Updated sync_status for record from daily_attendance_logs in attendance_sync_logs")
            else:
                # Insert into attendance_sync_logs with sync_status=1 (already synced)
                cursor.execute(
                    """
                    INSERT INTO attendance_sync_logs (
                        emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
                        checkout_date, checkout_time, status, mode, sync_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        daily_record[0],  # emp_b_id
                        emp_code,
                        daily_record[1],  # emp_full_name
                        checkin_date,
                        checkin_time_24h,  # normalized checkin_time
                        daily_record[3],  # checkout_date
                        checkout_time_24h,  # normalized checkout_time
                        daily_record[5],  # status
                        daily_record[6],  # mode
                    ),
                )
                conn.commit()
                print(f"✅ Inserted record from daily_attendance_logs into attendance_sync_logs as synced")
    except Exception as e:
        print(f"[ERROR] Failed to ensure daily log synced: {e}")
    finally:
        conn.close()



# def delete_single_attendance_log(record_id):
#     """Delete a single record from daily_attendance_logs by ID only if status is CHECKED_OUT"""
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     conn.execute("PRAGMA busy_timeout = 10000")
#     cursor = conn.cursor()

#     try:
#         # Check the status of the record
#         cursor.execute(
#             "SELECT status FROM daily_attendance_logs WHERE id = ?", (record_id,)
#         )
#         result = cursor.fetchone()

#         if not result:
#             print(
#                 f"[WARNING] No record found with ID {record_id} in daily_attendance_logs"
#             )
#             return {
#                 "success": False,
#                 "message": f"No record found with ID {record_id}",
#                 "rows_deleted": 0,
#             }

#         status = result[0]
#         if status != "CHECKED_OUT":
#             print(
#                 f"[INFO] Record ID {record_id} has status {status}, deletion not allowed"
#             )
#             return {
#                 "success": False,
#                 "message": f"Record ID {record_id} has status {status}, deletion not allowed for non-checked-out records",
#                 "rows_deleted": 0,
#             }

#         # Delete the record if status is CHECKED_OUT
#         cursor.execute("DELETE FROM daily_attendance_logs WHERE id = ?", (record_id,))
#         rows_deleted = cursor.rowcount
#         conn.commit()

#         if rows_deleted > 0:
#             print(
#                 f"✅ Successfully deleted record ID {record_id} from daily_attendance_logs"
#             )
#             return {
#                 "success": True,
#                 "message": f"Deleted record ID {record_id}",
#                 "rows_deleted": rows_deleted,
#             }
#         else:
#             print(
#                 f"[WARNING] No record found with ID {record_id} in daily_attendance_logs"
#             )
#             return {
#                 "success": False,
#                 "message": f"No record found with ID {record_id}",
#                 "rows_deleted": 0,
#             }

#     except Exception as e:
#         print(f"[ERROR] Failed to delete record ID {record_id}: {e}")
#         return {
#             "success": False,
#             "message": f"Failed to delete record ID {record_id}: {str(e)}",
#             "error": str(e),
#         }
#     finally:
#         conn.close()


def sync_single_record(log, token, device_meta=None):
    """Attempt to sync a single record with retries. Handles records from both attendance_sync_logs and daily_attendance_logs."""
    # url = "https://dev.fixhr.app/api/offline-attendance/syncOfflineAttendance"
    url = "https://fixhr.app/api/offline-attendance/syncOfflineAttendance"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    device_meta = device_meta or {}
    device_name = device_meta.get("device_name", get_device_name())
    system_mac = device_meta.get("system_mac_address", get_system_mac_address())

    # Ensure time is in 24-hour format for sync payload
    checkin_time_24h = normalize_time(log.get("checkin_time", ""))
    checkout_time_24h = None
    if log.get("check_out_time"):
        # Extract time from "DD-MM-YYYY HH:MM:SS" format
        try:
            parts = log["check_out_time"].split()
            if len(parts) >= 2:
                checkout_time_24h = normalize_time(parts[1])
        except:
            checkout_time_24h = normalize_time(log.get("checkout_time"))
    
    # Update payload with 24-hour format times
    payload = log.copy()
    payload["check_in_time"] = f"{log['checkin_date']} {checkin_time_24h}"  # 24-hour format
    if checkout_time_24h:
        payload["check_out_time"] = f"{log.get('checkout_date', log['checkin_date'])} {checkout_time_24h}"  # 24-hour format

    # Attach device + sync metadata
    payload["device_name"] = device_name
    payload["system_mac_address"] = system_mac
    payload["sync_date"] = get_current_datetime_str()
    
    print(f"[DEBUG] Syncing record for emp_code={log['emp_code']} on {log['checkin_date']} {checkin_time_24h} with payload: {payload}")

    for attempt in range(RETRY_ATTEMPTS):
        try:
            print(payload)
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # Check HTTP status code - must be 2xx for success
            if response.status_code not in [200, 201]:
                error_msg = f"API returned status code {response.status_code}: {response.text}"
                print(f"[ERROR] {error_msg}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return {
                    "success": False,
                    "message": f"API rejected the data: {error_msg}",
                    "attempts": attempt + 1,
                    "error": error_msg,
                }
            
            # Check response body for errors - API might return 200 but with error in body
            try:
                response_data = response.json()
                # Check if response indicates error (common patterns: error, success=false, status=false, etc.)
                if isinstance(response_data, dict):
                    # Check for status field (API uses "status": true/false)
                    if "status" in response_data:
                        if response_data["status"] is False or response_data["status"] == "false":
                            error_msg = f"API returned status=false: {response_data.get('message', 'Unknown error')}"
                            print(f"[ERROR] {error_msg}")
                            if attempt < RETRY_ATTEMPTS - 1:
                                time.sleep(RETRY_DELAY)
                                continue
                            return {
                                "success": False,
                                "message": f"API rejected the data: {error_msg}",
                                "attempts": attempt + 1,
                                "error": error_msg,
                            }
                        # If status is true, check if result array exists and has data
                        if response_data["status"] is True or response_data["status"] == "true":
                            # Check if result array exists (API returns {"status": true, "result": [...]})
                            if "result" in response_data:
                                if not response_data["result"] or len(response_data["result"]) == 0:
                                    error_msg = "API returned status=true but result array is empty"
                                    print(f"[ERROR] {error_msg}")
                                    if attempt < RETRY_ATTEMPTS - 1:
                                        time.sleep(RETRY_DELAY)
                                        continue
                                    return {
                                        "success": False,
                                        "message": f"API rejected the data: {error_msg}",
                                        "attempts": attempt + 1,
                                        "error": error_msg,
                                    }
                                # Result array has data, API accepted the record
                                print(f"[DEBUG] API response: status=true, result count={len(response_data['result'])}")
                    
                    # Check for common error indicators in response
                    if response_data.get("error") or response_data.get("errors"):
                        error_msg = f"API returned error in response: {response_data.get('error') or response_data.get('errors')}"
                        print(f"[ERROR] {error_msg}")
                        if attempt < RETRY_ATTEMPTS - 1:
                            time.sleep(RETRY_DELAY)
                            continue
                        return {
                            "success": False,
                            "message": f"API rejected the data: {error_msg}",
                            "attempts": attempt + 1,
                            "error": error_msg,
                        }
                    # Check if success field exists and is False (for other API formats)
                    if "success" in response_data and response_data["success"] is False:
                        error_msg = f"API returned success=false: {response_data.get('message', 'Unknown error')}"
                        print(f"[ERROR] {error_msg}")
                        if attempt < RETRY_ATTEMPTS - 1:
                            time.sleep(RETRY_DELAY)
                            continue
                        return {
                            "success": False,
                            "message": f"API rejected the data: {error_msg}",
                            "attempts": attempt + 1,
                            "error": error_msg,
                        }
            except (ValueError, KeyError) as json_error:
                # Response is not JSON or doesn't have expected structure
                # If status code is 200/201, check response text for error indicators
                response_text = response.text.lower()
                if any(keyword in response_text for keyword in ["error", "failed", "reject", "invalid", "false"]):
                    error_msg = f"API response indicates error: {response.text[:200]}"
                    print(f"[ERROR] {error_msg}")
                    if attempt < RETRY_ATTEMPTS - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return {
                        "success": False,
                        "message": f"API rejected the data: {error_msg}",
                        "attempts": attempt + 1,
                        "error": error_msg,
                    }
                # If we can't parse JSON but status is 200/201 and no error keywords, log warning
                print(f"[WARNING] Could not parse API response as JSON: {json_error}. Response: {response.text[:200]}")
            
            # ✅ API accepted the data - only now mark as synced
            print(
                f"[SUCCESS] API accepted record for emp_code={log['emp_code']} on {log['checkin_date']} {checkin_time_24h}"
            )

            # Check if record was already synced before marking (to track if it's a new sync)
            was_already_synced = check_if_record_already_synced(
                log["emp_code"], log["checkin_date"], checkin_time_24h
            )

            # ✅ Mark as synced in attendance_sync_logs (using 24-hour format time)
            sync_log_result = mark_sync_log_as_synced(
                log["emp_code"], log["checkin_date"], checkin_time_24h
            )

            # ✅ Update sync=1 in attendance_logs using same unique fields (24-hour format)
            attendance_log_result = mark_record_as_synced(
                log["emp_code"], log["checkin_date"], checkin_time_24h
            )
            
            # ✅ If record exists in daily_attendance_logs, ensure it's also in attendance_sync_logs and marked as synced
            ensure_daily_log_synced(log["emp_code"], log["checkin_date"], checkin_time_24h)

            # Determine if this was a newly synced record or already synced
            is_newly_synced = not was_already_synced and sync_log_result.get("rows_updated", 0) > 0

            if sync_log_result["success"] and attendance_log_result["success"]:
                return {
                    "success": True,
                    "message": f"Synced and marked as synced in attendance_sync_logs and attendance_logs for emp_code {log['emp_code']}",
                    "attempts": attempt + 1,
                    "is_newly_synced": is_newly_synced,  # Track if this was a new sync
                }
            elif not sync_log_result["success"]:
                return {
                    "success": False,
                    "message": f"API accepted data but failed to mark as synced in attendance_sync_logs: {sync_log_result['message']}",
                    "attempts": attempt + 1,
                    "error": sync_log_result.get("error", "Unknown error"),
                    "is_newly_synced": False,
                }
            elif not attendance_log_result["success"]:
                return {
                    "success": False,
                    "message": f"API accepted data but failed to update sync=1 in attendance_logs: {attendance_log_result.get('error', 'Unknown error')}",
                    "attempts": attempt + 1,
                    "is_newly_synced": False,
                }

        except requests.exceptions.RequestException as e:
            print(
                f"[ERROR] Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed for emp_code={log['emp_code']}: {e}"
            )
            if hasattr(e, "response") and e.response is not None:
                print(
                    f"[DEBUG] API error response: {e.response.status_code} {e.response.text}"
                )
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
                continue
            return {
                "success": False,
                "message": f"Failed to sync record for emp_code={log['emp_code']} after {RETRY_ATTEMPTS} attempts",
                "attempts": attempt + 1,
                "error": str(e),
            }
        except Exception as e:
            # Handle any other unexpected errors
            error_msg = f"Unexpected error during sync: {str(e)}"
            print(f"[ERROR] {error_msg}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
                continue
            return {
                "success": False,
                "message": f"Unexpected error: {error_msg}",
                "attempts": attempt + 1,
                "error": error_msg,
            }


# def sync_single_record(log, token):
#     """Attempt to sync a single record with retries, delete only if CHECKED_OUT"""
#     url = "https://dev.fixhr.app/api/offline-attendance/syncOfflineAttendance"
#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     payload = log
#     print(f"[DEBUG] Syncing record ID {log['id']} with payload: {payload}")

#     # Check the status of the record in daily_attendance_logs
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     conn.execute("PRAGMA busy_timeout = 10000")
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT status FROM daily_attendance_logs WHERE id = ?", (log["id"],)
#     )
#     result = cursor.fetchone()
#     conn.close()

#     if not result:
#         print(f"[WARNING] No record found with ID {log['id']} in daily_attendance_logs")
#         return {
#             "success": False,
#             "message": f"No record found with ID {log['id']}",
#             "attempts": 0,
#             "error": "Record not found",
#         }

#     status = result[0]
#     print(f"[DEBUG] Record ID {log['id']} has status {status}")

#     for attempt in range(RETRY_ATTEMPTS):
#         try:
#             response = requests.post(url, json=payload, headers=headers, timeout=10)
#             response.raise_for_status()
#             print(
#                 f"[SUCCESS] Synced record ID {log['id']} for emp_code {log['emp_code']} on {log['check_in_time']}"
#             )
#             # print(f"[DEBUG] API response: {response.status_code} {response.text}")

#             if status == "CHECKED_OUT":
#                 delete_result = delete_single_attendance_log(log["id"])
#                 if delete_result["success"]:
#                     return {
#                         "success": True,
#                         "message": f"Synced and deleted record ID {log['id']}",
#                         "attempts": attempt + 1,
#                     }
#                 else:
#                     return {
#                         "success": False,
#                         "message": f"Synced but failed to delete: {delete_result['message']}",
#                         "attempts": attempt + 1,
#                         "error": delete_result.get("error", "Unknown error"),
#                     }
#             else:
#                 print(
#                     f"[INFO] Record ID {log['id']} is CHECKED_IN, keeping in daily_attendance_logs"
#                 )
#                 return {
#                     "success": True,
#                     "message": f"Synced record ID {log['id']} (CHECKED_IN, not deleted)",
#                     "attempts": attempt + 1,
#                 }

#         except requests.exceptions.RequestException as e:
#             print(
#                 f"[ERROR] Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed for record ID {log['id']}: {e}"
#             )
#             if hasattr(e, "response") and e.response is not None:
#                 print(
#                     f"[DEBUG] API error response: {e.response.status_code} {e.response.text}"
#                 )
#             if attempt < RETRY_ATTEMPTS - 1:
#                 time.sleep(RETRY_DELAY)
#                 continue
#             return {
#                 "success": False,
#                 "message": f"Failed to sync record ID {log['id']} after {RETRY_ATTEMPTS} attempts",
#                 "attempts": attempt + 1,
#                 "error": str(e),
#             }

def mark_record_as_synced(emp_code: str, checkin_date: str, checkin_time: str):
    """Mark a record as synced in attendance_logs without using record ID.
    Always updates sync to 1 when API accepts the data, regardless of current sync status.
    This ensures that if attendance was updated (sync=0) and then synced, it's marked as synced (sync=1).
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE attendance_logs
            SET sync = 1, updated_at = CURRENT_TIMESTAMP
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        rows_updated = cursor.rowcount
        conn.commit()
        if rows_updated > 0:
            print(f"✅ Updated sync=1 in attendance_logs for {emp_code} on {checkin_date} {checkin_time}")
        return {"success": True, "rows_updated": rows_updated}
    except Exception as e:
        print(f"[ERROR] Failed to mark record as synced in attendance_logs: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def sync_data_to_server(sync_mode=None, start_date=None, end_date=None):
    """Sync attendance_sync_logs data to the server one by one"""
    if not is_internet_available():
        print("[INFO] No internet connection available. Sync skipped.")
        return {
            "success": False,
            "message": "No internet connection available. Sync skipped.",
        }

    token = get_session_token()
    if not token:
        print("[ERROR] No session token found in the database.")
        return {"success": False, "message": "No session token found in the database."}

    if sync_mode is None:
        sync_mode = get_setting("sync_mode", DEFAULT_APP_SETTINGS["sync_mode"])
    sync_mode = (sync_mode or "both").lower()
    logs = get_daily_attendance_logs(sync_mode=sync_mode, start_date=start_date, end_date=end_date)
    if not logs:
        print("[INFO] No unsynced data in attendance_sync_logs to sync.")
        return {"success": True, "message": "No unsynced data in attendance_sync_logs to sync."}

    device_metadata = get_sync_device_metadata()

    sync_results = {
        "success": True,
        "message": "",
        "records_synced": 0,
        "records_failed": 0,
        "failed_records": [],
    }

    for log in logs:
        result = sync_single_record(log, token, device_metadata)
        if result["success"]:
            # Only count as newly synced if it was actually synced (not already synced)
            if result.get("is_newly_synced", True):  # Default to True for backward compatibility
                sync_results["records_synced"] += 1
            else:
                print(f"[INFO] Record for {log['emp_code']} was already synced, not counting as new sync")
            clear_failed_sync(log["emp_code"], log["checkin_date"], log["checkin_time"])
        else:
            sync_results["success"] = False
            sync_results["records_failed"] += 1
            sync_results["failed_records"].append(
                {
                    "id": log["id"],
                    "emp_code": log["emp_code"],
                    "error": result.get("error", "Unknown error"),
                    "attempts": result.get("attempts", 1),
                }
            )
            record_sync_failure(log, result.get("message", "Sync failed"), result.get("attempts", 1))

    sync_results["message"] = (
        f"Synced {sync_results['records_synced']} records, "
        f"failed {sync_results['records_failed']} records "
        f"(mode={sync_mode}, range={start_date or '---'} to {end_date or '---'})"
    )
    update_last_sync_count(sync_results["records_synced"], sync_results["records_failed"])
    
    # Clean up old synced records daily (keep last 7 days)
    try:
        cleanup_old_synced_records(days_to_keep=7)
    except Exception as e:
        print(f"[WARNING] Failed to cleanup old synced records: {e}")
    
    print(f"[INFO] Sync completed: {sync_results['message']}")
    return sync_results


def retry_failed_sync(record_ids=None):
    """Retry failed queue entries"""
    records = get_failed_sync_records()
    if record_ids:
        id_set = set(record_ids)
        records = [rec for rec in records if rec["id"] in id_set]
    if not records:
        return {"success": True, "message": "No failed records to retry.", "retried": 0, "resolved": 0}

    token = get_session_token()
    if not token:
        return {"success": False, "message": "No session token found in the database.", "retried": 0, "resolved": 0}

    resolved = 0
    retried = 0
    device_metadata = get_sync_device_metadata()

    for rec in records:
        payload = {}
        if rec["payload"]:
            try:
                payload = json.loads(rec["payload"])
            except Exception:
                payload = {}
        if not payload:
            payload = {
                "emp_code": rec["emp_code"],
                "checkin_date": rec["checkin_date"],
                "checkin_time": rec["checkin_time"],
            }
        result = sync_single_record(payload, token, device_metadata)
        retried += 1
        if result["success"]:
            resolved += 1
            clear_failed_sync(rec["emp_code"], rec["checkin_date"], rec["checkin_time"])
        else:
            record_sync_failure(payload, result.get("message", "Retry failed"), rec["attempts"] + 1)

    message = f"Retried {retried} records, resolved {resolved}"
    return {"success": resolved == retried, "message": message, "retried": retried, "resolved": resolved}


def register_device_on_server(token, payload):
    """Register device metadata with FixHR server."""
    if not token:
        return {"success": False, "message": "Authentication token missing."}
    url = "https://fixhr.app/api/offline-attendance/register-device"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = {}
        success = response.status_code in (200, 201) and data.get("success", True) not in (False, "false", 0, "0")
        message = data.get("message") or ("Device registered successfully." if success else response.text)
        if success:
            return {"success": True, "message": message}
        return {
            "success": False,
            "message": message or f"Device registration failed with status {response.status_code}",
        }
    except requests.exceptions.RequestException as exc:
        return {"success": False, "message": f"Failed to register device: {exc}"}


def start_background_sync(sync_mode=None, start_date=None, end_date=None):
    """Start the sync process in a background thread"""
    global IS_SYNCING
    with SYNC_LOCK:
        if IS_SYNCING:
            print("[INFO] Background sync is already running.")
            return {"success": False, "message": "Background sync is already running."}

        IS_SYNCING = True
        print("[INFO] Starting background sync...")

    def sync_thread():
        global IS_SYNCING
        try:
            result = sync_data_to_server(
                sync_mode=sync_mode,
                start_date=start_date,
                end_date=end_date,
            )
            print(f"[INFO] Background sync completed: {result['message']}")
        except Exception as e:
            print(f"[ERROR] Background sync failed: {e}")
        finally:
            with SYNC_LOCK:
                IS_SYNCING = False
                print("[INFO] Background sync thread terminated.")

    thread = threading.Thread(target=sync_thread, daemon=True)
    thread.start()
    return {"success": True, "message": "Background sync started."}




#==============================================================Sync Metadat=================================================================#



def update_last_sync_count(synced: int, failed: int):
    """Update last sync stats in sync_metadata with IST timestamp in DD-MM-YYYY HH:MM:SS"""
    ist_now = OfflinePunchHelper.get_accurate_indian_time()  # get IST datetime
    ist_now_str = ist_now.strftime("%d-%m-%Y %H:%M:%S")      # DD-MM-YYYY format

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sync_metadata (last_sync_count, failed_count, last_sync_at)
        VALUES (?, ?, ?)
        """,
        (synced, failed, ist_now_str),
    )
    conn.commit()
    conn.close()




def get_last_sync_count():
    """Fetch last sync stats"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT last_sync_count, failed_count, last_sync_at
        FROM sync_metadata
        ORDER BY id DESC LIMIT 1
        """
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "last_sync_count": result[0],
            "failed_count": result[1],
            "last_sync_at": result[2],
        }
    else:
        return {
            "last_sync_count": 0,
            "failed_count": 0,
            "last_sync_at": None,
        }


def get_remaining_sync_count():
    """Fetch how many records are pending sync in attendance_sync_logs"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM attendance_sync_logs WHERE sync_status = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return {"remaining_sync_count": count}


def cleanup_old_synced_records(days_to_keep=7):
    """Clean up old synced records from attendance_sync_logs to prevent table from growing too large.
    Keeps records for the specified number of days. Only deletes records that are synced (sync_status=1).
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    
    try:
        # Calculate cutoff date
        ist_now = OfflinePunchHelper.get_accurate_indian_time()
        cutoff_date = (ist_now - datetime.timedelta(days=days_to_keep)).strftime("%d-%m-%Y")
        
        # Delete old synced records
        cursor.execute(
            """
            DELETE FROM attendance_sync_logs
            WHERE sync_status = 1 AND checkin_date < ?
            """,
            (cutoff_date,)
        )
        rows_deleted = cursor.rowcount
        conn.commit()
        
        print(f"✅ Cleaned up {rows_deleted} old synced records from attendance_sync_logs (older than {days_to_keep} days)")
        return {
            "success": True,
            "message": f"Cleaned up {rows_deleted} old synced records",
            "rows_deleted": rows_deleted,
        }
    except Exception as e:
        print(f"[ERROR] Failed to cleanup old synced records: {e}")
        return {
            "success": False,
            "message": f"Failed to cleanup old synced records: {str(e)}",
            "error": str(e),
        }
    finally:
        conn.close()

def get_sync_status_overview():
    """Return formatted strings for overview cards (IST-based)"""
    last_sync = get_last_sync_count()
    remaining = get_remaining_sync_count()

    # Last Sync card
    if last_sync["last_sync_at"]:
        last_sync_str = (
            f"No. of Log = {last_sync['last_sync_count'] + last_sync['failed_count']}\n"
            f"Synchronized = {last_sync['last_sync_count']} || "
            f"No. of Failed logs = {last_sync['failed_count']}\n"
            f"Sync. Date = {last_sync['last_sync_at']}"
        )
    else:
        last_sync_str = "No sync history available"

    # Next Sync card → schedule for 7 days later (IST)
    ist_now = OfflinePunchHelper.get_accurate_indian_time()
    next_sync_time = (ist_now + datetime.timedelta(days=7)).strftime("%d-%b-%Y at %H:%M")

    next_sync_str = (
        f"Remaining Sync Data\n"
        f"Remaining logs = {remaining['remaining_sync_count']}"
    )

    return last_sync_str, next_sync_str


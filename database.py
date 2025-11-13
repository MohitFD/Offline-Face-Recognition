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
    """Normalize time input to 24-hour format"""
    if time_input is None:
        return get_current_time_str()

    if isinstance(time_input, str):
        try:
            parsed_time = datetime.datetime.strptime(time_input, "%I:%M:%S")
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            try:
                # Already in 24-hour format
                datetime.datetime.strptime(time_input, "%H:%M:%S")
                return time_input
            except ValueError:
                return get_current_time_str()

    if isinstance(time_input, datetime.datetime):
        return time_input.strftime("%H:%M:%S")

    return str(time_input)



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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
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
        "[INFO] Database initialized with strict attendance constraints including daily_attendance_logs"
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
        # Update attendance_logs
        cursor.execute("""
            UPDATE attendance_logs
            SET checkout_date=?, checkout_time=?, status='CHECKED_OUT', updated_at=CURRENT_TIMESTAMP
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


def get_daily_attendance_logs():
    """Fetch all data from daily_attendance_logs"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    query = """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM daily_attendance_logs
        ORDER BY updated_at DESC
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    logs = []
    for row in results:
        logs.append(
            {
                "emp_code": row[2],
                "emp_b_id": row[1],
                "check_in_time": f"{row[4]} {row[5]}",
                "check_out_time": f"{row[6]} {row[7]}" if row[7] else None,
                "am_id": 1,
                "atd_checkin_method_id": 324,
                "id": row[0],
                "checkin_date": row[4],   # ✅ separate field
                "checkin_time": row[5],   # ✅ separate field
            }
        )
    print(f"[DEBUG] Retrieved {len(logs)} records from daily_attendance_logs")
    return logs


def delete_single_attendance_log(emp_code, checkin_date, checkin_time):
    """Delete a single record from daily_attendance_logs by unique fields"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM daily_attendance_logs
            WHERE emp_code = ? AND checkin_date = ? AND checkin_time = ?
            """,
            (emp_code, checkin_date, checkin_time),
        )
        rows_deleted = cursor.rowcount
        conn.commit()
        if rows_deleted > 0:
            print(
                f"✅ Successfully deleted record (emp_code={emp_code}, date={checkin_date}, time={checkin_time}) from daily_attendance_logs"
            )
            return {
                "success": True,
                "message": f"Deleted record for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                "rows_deleted": rows_deleted,
            }
        else:
            print(
                f"[WARNING] No record found for emp_code={emp_code}, date={checkin_date}, time={checkin_time} in daily_attendance_logs"
            )
            return {
                "success": False,
                "message": f"No record found for emp_code={emp_code}, date={checkin_date}, time={checkin_time}",
                "rows_deleted": 0,
            }
    except Exception as e:
        print(f"[ERROR] Failed to delete record: {e}")
        return {
            "success": False,
            "message": f"Failed to delete record: {str(e)}",
            "error": str(e),
        }
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


def sync_single_record(log, token):
    """Attempt to sync a single record with retries"""
    # url = "https://dev.fixhr.app/api/offline-attendance/syncOfflineAttendance"
    url = "https://fixhr.app/api/offline-attendance/syncOfflineAttendance"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = log
    print(f"[DEBUG] Syncing record for emp_code={log['emp_code']} on {log['checkin_date']} {log['checkin_time']} with payload: {payload}")

    for attempt in range(RETRY_ATTEMPTS):
        try:
            print(payload)
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            print(
                f"[SUCCESS] Synced record for emp_code={log['emp_code']} on {log['checkin_date']} {log['checkin_time']}"
            )

            # ✅ Delete from daily_attendance_logs by unique fields
            delete_result = delete_single_attendance_log(
                log["emp_code"], log["checkin_date"], log["checkin_time"]
            )

            # ✅ Update sync=1 in attendance_logs using same unique fields
            if delete_result["success"]:
                update_result = mark_record_as_synced(
                    log["emp_code"], log["checkin_date"], log["checkin_time"]
                )
            else:
                update_result = {"success": False, "error": "Delete failed, so not updating sync"}

            if delete_result["success"] and update_result["success"]:
                return {
                    "success": True,
                    "message": f"Synced, deleted (daily_attendance_logs) and updated sync=1 (attendance_logs) for emp_code {log['emp_code']}",
                    "attempts": attempt + 1,
                }
            elif not delete_result["success"]:
                return {
                    "success": False,
                    "message": f"Synced but failed to delete in daily_attendance_logs: {delete_result['message']}",
                    "attempts": attempt + 1,
                    "error": delete_result.get("error", "Unknown error"),
                }
            elif not update_result["success"]:
                return {
                    "success": False,
                    "message": f"Synced but failed to update sync=1 in attendance_logs: {update_result['error']}",
                    "attempts": attempt + 1,
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
    """Mark a record as synced in attendance_logs without using record ID"""
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
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def sync_data_to_server():
    """Sync daily_attendance_logs data to the server one by one"""
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

    logs = get_daily_attendance_logs()
    if not logs:
        print("[INFO] No data in daily_attendance_logs to sync.")
        return {"success": True, "message": "No data in daily_attendance_logs to sync."}

    sync_results = {
        "success": True,
        "message": "",
        "records_synced": 0,
        "records_failed": 0,
        "failed_records": [],
    }

    for log in logs:
        result = sync_single_record(log, token)
        if result["success"]:
            sync_results["records_synced"] += 1
        else:
            sync_results["success"] = False
            sync_results["records_failed"] += 1
            sync_results["failed_records"].append(
                {
                    "id": log["id"],
                    "emp_code": log["emp_code"],
                    "error": result["error"],
                    "attempts": result["attempts"],
                }
            )

    sync_results["message"] = (
        f"Synced {sync_results['records_synced']} records, "
        f"failed {sync_results['records_failed']} records"
    )
    update_last_sync_count(sync_results["records_synced"], sync_results["records_failed"])
    print(f"[INFO] Sync completed: {sync_results['message']}")
    return sync_results


def start_background_sync():
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
            result = sync_data_to_server()
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
    """Fetch how many records are pending sync in daily_attendance_logs"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM daily_attendance_logs")
    count = cursor.fetchone()[0]
    conn.close()
    return {"remaining_sync_count": count}

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


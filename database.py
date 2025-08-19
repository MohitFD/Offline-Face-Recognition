import os
import sys
import sqlite3
import datetime


# ---------------------- Path Utilities ----------------------
def get_app_dir():
    """Gets the directory where the .exe or .py file is located"""
    if getattr(sys, "frozen", False):  # Running as .exe
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_data_dir():
    """Gets the persistent data directory"""
    if getattr(sys, "frozen", False):  # Running as .exe
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


# ---------------------- Configuration ----------------------
DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "employees.db")
IMAGE_DIR = os.path.join(DATA_DIR, "profile_images")




# import datetime
class OfflinePunchHelper:
    @staticmethod
    def get_accurate_indian_time():
        """Get IST time (UTC+5:30) without blocking network calls.

        Uses system UTC time and applies fixed IST offset. This avoids network
        latency and hanging caused by NTP lookups during frequent calls.
        """
        utc_now = datetime.datetime.utcnow()
        return utc_now + datetime.timedelta(hours=5, minutes=30)


def get_current_date_str():
    """Get current date in YYYY-MM-DD format (IST) for storage"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%d-%m-%Y")


def get_current_time_str():
    """Get current time in 12-hour format without AM/PM (IST)"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%I:%M:%S")


def get_current_datetime_str():
    """Get current datetime in YYYY-MM-DD hh:mm:ss format (IST)"""
    ist_time = OfflinePunchHelper.get_accurate_indian_time()
    return ist_time.strftime("%Y-%m-%d %I:%M:%S")


def normalize_date(date_input):
    """Normalize date input to YYYY-MM-DD format (storage)"""
    if date_input is None:
        return get_current_date_str()

    if isinstance(date_input, str):
        return date_input

    if isinstance(date_input, datetime.date):
        return date_input.strftime("%Y-%m-%d")

    if isinstance(date_input, datetime.datetime):
        return date_input.strftime("%Y-%m-%d")

    return str(date_input)


def normalize_time(time_input):
    """Normalize time input to 12-hour format without AM/PM"""
    if time_input is None:
        return get_current_time_str()

    if isinstance(time_input, str):
        return time_input

    if isinstance(time_input, datetime.datetime):
        return time_input.strftime("%I:%M:%S")

    return str(time_input)


# ---------------------- Database Init ----------------------
def init_db():
    """Initialize the database with proper schema and strict constraints"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Employees Table
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

    # Enhanced Attendance Logs Table with STRICT constraints to prevent duplicates
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_b_id TEXT,
            emp_code TEXT NOT NULL,
            emp_full_name TEXT NOT NULL,
            checkin_date DATE NOT NULL,
            checkin_time TEXT NOT NULL,
            checkout_date DATE,   
            checkout_time TEXT,
            status TEXT DEFAULT 'CHECKED_IN' CHECK(status IN ('CHECKED_IN', 'CHECKED_OUT')),
            mode TEXT DEFAULT 'FACE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_employee_date UNIQUE(emp_code, checkin_date)
        )
        """
    )

    # Ensure 'mode' column exists (for existing databases)
    try:
        cursor.execute("PRAGMA table_info(attendance_logs)")
        cols = [row[1].lower() for row in cursor.fetchall()]
        if 'mode' not in cols:
            cursor.execute("ALTER TABLE attendance_logs ADD COLUMN mode TEXT DEFAULT 'FACE'")
    except Exception:
        pass
        # Sessions Table for storing session data
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

    # Create indexes for fast search
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
        CREATE INDEX IF NOT EXISTS idx_session_employee_id ON sessions(employee_id)
        """
    )

    conn.commit()
    conn.close()
    print("[INFO] Database initialized with strict attendance constraints")


# ---------------------- Enhanced Attendance Functions ----------------------
def get_employee_attendance_status(emp_code, target_date=None):
    """
    Get detailed attendance status for an employee on a specific date
    Returns: dict with comprehensive status information
    """
    target_date = normalize_date(target_date)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM attendance_logs 
        WHERE emp_code = ? AND checkin_date = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (emp_code, target_date),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        has_checkout = result[7] is not None  # checkout_time exists
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
            "mode": result[9] if len(result) > 10 else 'FACE',
            "created_at": result[10],
            "updated_at": result[11],
            "has_checked_in": True,
            "has_checked_out": has_checkout,
            "can_checkin": False,  # Already checked in today
            "can_checkout": not has_checkout,  # Can checkout only if not already checked out
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

    # Check current attendance status FIRST
    status = get_employee_attendance_status(emp_code, checkin_date)

    if status["exists"]:
        if status["has_checked_out"]:
            return {
                "success": False,
                "message": f"Employee {emp_code} has already completed full attendance for {checkin_date}",
                "action": "ALREADY_COMPLETED",
                "details": status,
            }
        else:
            return {
                "success": False,
                "message": f"Employee {emp_code} is already checked in for {checkin_date}. Next action: CHECKOUT",
                "action": "ALREADY_CHECKED_IN",
                "details": status,
            }

    # Proceed with check-in (only if no existing record)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO attendance_logs (
                emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, status, mode
            )
            VALUES (?, ?, ?, ?, ?, 'CHECKED_IN', 'FACE')
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
        # This should not happen due to our pre-check, but handle it anyway
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


def checkout_employee(emp_code, checkout_date=None, checkout_time=None):
    """
    Check out employee - updates checkout_time every time
    """
    checkout_date = normalize_date(checkout_date)
    checkout_time = normalize_time(checkout_time)

    print(
        f"[DEBUG] Updating checkout for {emp_code} on {checkout_date} at {checkout_time}"
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE attendance_logs 
            SET checkout_date = ?, 
                checkout_time = ?, 
                status = 'CHECKED_OUT',
                updated_at = CURRENT_TIMESTAMP
            WHERE emp_code = ? AND checkin_date = ?
            """,
            (checkout_date, checkout_time, emp_code, checkout_date),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": f"No check-in record found for {emp_code} on {checkout_date}",
                "action": "NO_RECORD",
            }

        conn.commit()

        print(
            f"✅ CHECK-OUT updated for {emp_code} on {checkout_date} at {checkout_time}"
        )

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
        return {"success": False, "message": str(e), "action": "ERROR"}
    finally:
        conn.close()


# def checkout_employee(emp_code, checkout_date=None, checkout_time=None):
#     """
#     Check out employee with complete validation - UPDATES EXISTING RECORD
#     Returns: dict with success status and message
#     """
#     checkout_date = normalize_date(checkout_date)
#     checkout_time = normalize_time(checkout_time)

#     print(
#         f"[DEBUG] Attempting checkout for {emp_code} on {checkout_date} at {checkout_time}"
#     )

#     # Check current attendance status FIRST
#     status = get_employee_attendance_status(emp_code, checkout_date)

#     if not status["exists"]:
#         return {
#             "success": False,
#             "message": f"Employee {emp_code} has not checked in on {checkout_date}. Please check in first.",
#             "action": "NOT_CHECKED_IN",
#             "details": status,
#         }

#     if status["has_checked_out"]:
#         return {
#             "success": False,
#             "message": f"Employee {emp_code} has already checked out at {status['checkout_time']} on {checkout_date}",
#             "action": "ALREADY_CHECKED_OUT",
#             "details": status,
#         }

#     # Proceed with check-out (update existing record)
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
#             WHERE emp_code = ? AND checkin_date = ? AND checkout_time IS NULL
#             """,
#             (checkout_date, checkout_time, emp_code, checkout_date),
#         )

#         if cursor.rowcount == 0:
#             return {
#                 "success": False,
#                 "message": f"No active check-in found for employee {emp_code} on {checkout_date}",
#                 "action": "NO_ACTIVE_CHECKIN",
#             }

#         conn.commit()

#         print(
#             f"✅ CHECK-OUT successful for {emp_code} on {checkout_date} at {checkout_time}"
#         )

#         # Get updated employee details
#         updated_status = get_employee_attendance_status(emp_code, checkout_date)

#         return {
#             "success": True,
#             "message": f"Employee {emp_code} checked out successfully at {checkout_time}",
#             "action": "CHECKED_OUT",
#             "checkout_date": checkout_date,
#             "checkout_time": checkout_time,
#             "emp_code": emp_code,
#             "emp_full_name": updated_status.get("emp_full_name", ""),
#             "details": updated_status,
#         }

#     except Exception as e:
#         print(f"[ERROR] Database error during check-out: {e}")
#         return {
#             "success": False,
#             "message": f"Database error during check-out: {str(e)}",
#             "action": "DATABASE_ERROR",
#             "error": str(e),
#         }
#     finally:
#         conn.close()


def get_next_attendance_action(emp_code, current_date=None):
    """
    Get the next required action for an employee's attendance
    Returns: 'CHECKIN', 'CHECKOUT', or 'COMPLETED'
    """
    current_date = normalize_date(current_date)

    status = get_employee_attendance_status(emp_code, current_date)

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
      - Allows multiple CHECKOUT updates (latest checkout_time always updated)
    Returns: dict with result details
    """
    current_date = normalize_date(current_date)
    current_time = normalize_time(current_time)

    print(
        f"[INFO] Processing attendance for {emp_code} ({emp_full_name}) on {current_date}"
    )

    next_action = get_next_attendance_action(emp_code, current_date)
    print(f"[INFO] Next required action: {next_action}")

    if next_action == "CHECKIN":
        # First check-in of the day → insert record
        return checkin_employee(
            emp_b_id, emp_code, emp_full_name, current_date, current_time
        )

    elif next_action == "CHECKOUT":
        # Allow multiple checkout updates → always update checkout_time
        result = checkout_employee(emp_code, current_date, current_time)
        result["message"] = (
            "Checkout time updated successfully"
            if result["success"]
            else result["message"]
        )
        return result

    else:  # ALREADY_COMPLETED but allow further checkout updates
        # Even if already checked out earlier, allow updating checkout time
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
    status = get_employee_attendance_status(emp_code, current_date)
    return status["can_checkin"]


def can_employee_checkout(emp_code, current_date=None):
    """Check if employee can check out today"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(emp_code, current_date)
    return status["can_checkout"]


def has_checkin_today(emp_code, current_date=None):
    """Check if employee has checked in on given date"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(emp_code, current_date)
    return status["has_checked_in"]


def has_completed_attendance_today(emp_code, current_date=None):
    """Check if employee has completed full attendance (both check-in and check-out) for the day"""
    current_date = normalize_date(current_date)
    status = get_employee_attendance_status(emp_code, current_date)
    return status["has_checked_in"] and status["has_checked_out"]


def get_attendance_logs(emp_code=None, status_filter=None):
    """Retrieve attendance logs for the current date only"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get today's date in IST
    current_date = get_current_date_str()

    query = """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time, 
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM attendance_logs
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
                "mode": row[9] if len(row) > 11 else 'FACE',
                "created_at": row[10],
                "updated_at": row[11],
                "is_complete": row[7] is not None,  # Has checkout time
            }
        )

    return logs


def get_daily_attendance_summary(target_date=None):
    """Get daily attendance summary with statistics"""
    target_date = normalize_date(target_date)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all attendance records for the date
    cursor.execute(
        """
        SELECT emp_code, emp_full_name, checkin_time, checkout_time, status, mode
        FROM attendance_logs 
        WHERE checkin_date = ?
        ORDER BY checkin_time
        """,
        (target_date,),
    )

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
    else:
        print("⚠️ Dropping all tables (schema will be lost)...")
        cursor.execute("DROP TABLE IF EXISTS employees;")
        cursor.execute("DROP TABLE IF EXISTS attendance_logs;")

    conn.commit()
    conn.close()

    if not clear_data_only:
        init_db()
        print("✅ Database schema recreated.")


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


# ---------------------- Data Validation Functions ----------------------
def validate_attendance_integrity():
    """Check for any attendance data integrity issues"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for duplicate entries (should be impossible with our constraints)
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
        print(f"⚠️ WARNING: Found {len(duplicates)} duplicate attendance entries:")
        for emp_code, date, count in duplicates:
            print(f"  - {emp_code} on {date}: {count} entries")
    else:
        print("✅ No duplicate attendance entries found")

    conn.close()


def get_attendance_by_date(date_selected):
    """Fetch all attendance logs for a specific date"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT id, emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
               checkout_date, checkout_time, status, mode, created_at, updated_at
        FROM attendance_logs
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
                "mode": row[9] if len(row) > 11 else 'FACE',
                "created_at": row[10],
                "updated_at": row[11],
                "is_complete": row[7] is not None,
            }
        )

    return logs



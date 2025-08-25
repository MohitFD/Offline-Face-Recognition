# import os
# import shutil
# import threading
# import time
# import psutil
# import sqlite3
# from datetime import datetime, timedelta


# class BackupManager:
#     def __init__(self, db_path="employees.db"):
#         self.db_path = db_path
#         self.thread = None
#         self.running = False

#         # 🔍 Detect backup drive dynamically
#         self.backup_dir = self._find_backup_drive()

#         if not os.path.exists(self.backup_dir):
#             os.makedirs(self.backup_dir)

#         # Subfolders
#         self.daily_dir = os.path.join(self.backup_dir, "Daily_Attendance")
#         self.weekly_dir = os.path.join(self.backup_dir, "Weekly_Attendance")
#         self.monthly_dir = os.path.join(self.backup_dir, "Monthly_Attendance")

#         for folder in [self.daily_dir, self.weekly_dir, self.monthly_dir]:
#             os.makedirs(folder, exist_ok=True)

#     def _find_backup_drive(self):
#         """Find alternate drive for backup (not same as DB drive)"""
#         db_drive = os.path.splitdrive(self.db_path)[0]  # Example: "C:"
#         backup_drive = None

#         for part in psutil.disk_partitions(all=False):
#             drive = part.device.rstrip("\\")  # Example: "D:"
#             if drive != db_drive and os.path.exists(drive):
#                 backup_drive = drive
#                 break

#         if backup_drive:
#             print(f"[BackupManager] 💾 Backup drive found: {backup_drive}")
#             return os.path.join(backup_drive, "FixHR_Backups")
#         else:
#             print("[BackupManager] ⚠ No alternate drive found, using same drive as DB")
#             return os.path.join(os.path.dirname(self.db_path), "FixHR_Backups")

#     def _get_next_run_times(self):
#         """Return today's run times: 11:00 AM and 7:00 PM"""
#         now = datetime.now()
#         run_times = [
#             now.replace(hour=15, minute= 17, second=0, microsecond=0),
#             now.replace(hour=19, minute=0, second=0, microsecond=0),
#         ]
#         # अगर आज का समय निकल गया है, तो अगला दिन
#         return [t if t > now else t + timedelta(days=1) for t in run_times]

#     def _backup_loop(self):
#         print("[BackupManager] Backup loop started...")

#         while self.running:
#             run_times = self._get_next_run_times()
#             next_run = min(run_times)
#             print(f"[BackupManager] ⏳ Next backup scheduled at {next_run}")

#             while self.running and datetime.now() < next_run:
#                 time.sleep(30)

#             if not self.running:
#                 break

#             self._do_backups()

#     def _do_backups(self):
#         print(f"[BackupManager] 🚀 Running backups at {datetime.now()}")

#         self._do_full_backup()
#         self._do_daily_backup()

#         # Weekly (Monday 11AM only)
#         if datetime.now().weekday() == 0 and datetime.now().hour == 11:
#             self._do_weekly_backup()

#         # Monthly (1st day of month at 11AM)
#         if datetime.now().day == 1 and datetime.now().hour == 11:
#             self._do_monthly_backup()

#     def _do_full_backup(self):
#         """Complete DB backup (once daily with timestamp)"""
#         if not os.path.exists(self.db_path):
#             print(f"[BackupManager] ❌ Database not found: {self.db_path}")
#             return

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         backup_file = os.path.join(self.backup_dir, f"db_backup_{timestamp}.db")

#         try:
#             shutil.copy(self.db_path, backup_file)
#             print(f"[BackupManager] ✅ Full DB Backup created: {backup_file}")
#         except Exception as e:
#             print(f"[BackupManager] ❌ Full backup failed: {e}")

#     def _extract_attendance(self, days=None):
#         """Fetch attendance_logs data"""
#         if not os.path.exists(self.db_path):
#             print(f"[BackupManager] ❌ Database not found: {self.db_path}")
#             return None

#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()

#             query = "SELECT * FROM attendance_logs"
#             params = ()

#             if days:
#                 cutoff = datetime.now() - timedelta(days=days)

#                 # ✅ अगर created_at से filter करना है
#                 query += " WHERE created_at >= ?"

#                 # या अगर updated_at से filter करना है तो ऊपर वाली line की जगह ये रख दो:
#                 # query += " WHERE updated_at >= ?"

#                 params = (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)

#             cursor.execute(query, params)
#             rows = cursor.fetchall()

#             conn.close()
#             return rows

#         except Exception as e:
#             print(f"[BackupManager] ❌ Attendance extract failed: {e}")
#             return None


#     def _save_attendance_backup(self, rows, folder, label):
#         """Save attendance logs into a proper SQLite .db file (tuple-safe)"""
#         if not rows:
#             print(f"[BackupManager] ⚠ No attendance data for {label} backup")
#             return

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         db_path = os.path.join(folder, f"{label}_attendance_{timestamp}.db")

#         try:
#             conn = sqlite3.connect(db_path)
#             cursor = conn.cursor()

#             # Create table with headings
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS attendance_logs (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     emp_b_id TEXT,
#                     emp_code TEXT NOT NULL,
#                     emp_full_name TEXT NOT NULL,
#                     checkin_date DATE NOT NULL,
#                     checkin_time TEXT NOT NULL,
#                     checkout_date DATE,
#                     checkout_time TEXT,
#                     status TEXT DEFAULT 'CHECKED_IN' CHECK(status IN ('CHECKED_IN', 'CHECKED_OUT')),
#                     mode TEXT DEFAULT 'FACE',
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     CONSTRAINT unique_employee_date UNIQUE(emp_code, checkin_date)
#                 )
#             """)

#             # Insert rows (tuple-safe)
#             for row in rows:
#                 # row is a tuple, skip original ID (row[0])
#                 cursor.execute("""
#                     INSERT OR IGNORE INTO attendance_logs (
#                         emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
#                         checkout_date, checkout_time, status, mode, created_at, updated_at
#                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """, row[1:])  # slice from 1 to skip original ID

#             conn.commit()
#             conn.close()
#             print(f"[BackupManager] ✅ {label} backup saved as DB: {db_path}")

#         except Exception as e:
#             print(f"[BackupManager] ❌ {label} backup save failed: {e}")

#     def _do_daily_backup(self):
#         rows = self._extract_attendance(days=1)
#         self._save_attendance_backup(rows, self.daily_dir, "daily")

#     def _do_weekly_backup(self):
#         rows = self._extract_attendance(days=7)
#         self._save_attendance_backup(rows, self.weekly_dir, "weekly")

#     def _do_monthly_backup(self):
#         rows = self._extract_attendance(days=30)
#         self._save_attendance_backup(rows, self.monthly_dir, "monthly")

#     def start(self):
#         if self.thread and self.thread.is_alive():
#             return
#         self.running = True
#         self.thread = threading.Thread(target=self._backup_loop, daemon=True)
#         self.thread.start()
#         print("[BackupManager] 🔄 Backup thread started")

#     def stop(self):
#         self.running = False
#         print("[BackupManager] ⏹ Backup stopped")



import os
import shutil
import threading
import time
import psutil
import sqlite3
import socket
from datetime import datetime, timedelta
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


class BackupManager:
    def __init__(self, db_path="employees.db"):
        self.db_path = db_path
        self.thread = None
        self.running = False

        # 🔍 Detect backup drive dynamically
        self.backup_dir = self._find_backup_drive()

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        # Subfolders
        self.daily_dir = os.path.join(self.backup_dir, "Daily_Attendance")
        self.weekly_dir = os.path.join(self.backup_dir, "Weekly_Attendance")
        self.monthly_dir = os.path.join(self.backup_dir, "Monthly_Attendance")

        for folder in [self.daily_dir, self.weekly_dir, self.monthly_dir]:
            os.makedirs(folder, exist_ok=True)

        # 🔑 Google Drive Auth
        self.drive = self._google_drive_auth()

        # Drive folder IDs (optional: आप चाहो तो अपने Google Drive में पहले folder बनाकर IDs डाल सकते हो)
        self.daily_drive_folder = None
        self.weekly_drive_folder = None
        self.monthly_drive_folder = None

    def _find_backup_drive(self):
        """Find alternate drive for backup (not same as DB drive)"""
        db_drive = os.path.splitdrive(self.db_path)[0]  # Example: "C:"
        backup_drive = None

        for part in psutil.disk_partitions(all=False):
            drive = part.device.rstrip("\\")  # Example: "D:"
            if drive != db_drive and os.path.exists(drive):
                backup_drive = drive
                break

        if backup_drive:
            print(f"[BackupManager] 💾 Backup drive found: {backup_drive}")
            return os.path.join(backup_drive, "FixHR_Backups")
        else:
            print("[BackupManager] ⚠ No alternate drive found, using same drive as DB")
            return os.path.join(os.path.dirname(self.db_path), "FixHR_Backups")

    def _google_drive_auth(self):
        """Authenticate Google Drive"""
        try:
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()  # पहली बार login होगा browser से
            drive = GoogleDrive(gauth)
            print("[BackupManager] ✅ Google Drive connected")
            return drive
        except Exception as e:
            print(f"[BackupManager] ❌ Google Drive Auth failed: {e}")
            return None

    def _is_internet_available(self, host="8.8.8.8", port=53, timeout=3):
        """Check Internet connectivity"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False

    def _upload_to_drive(self, file_path, folder_id=None):
        """Upload file to Google Drive"""
        if not self.drive:
            print("[BackupManager] ⚠ Drive not authenticated")
            return

        if not os.path.exists(file_path):
            print(f"[BackupManager] ❌ File not found: {file_path}")
            return

        try:
            file_name = os.path.basename(file_path)
            gfile = self.drive.CreateFile({
                "title": file_name,
                "parents": [{"id": folder_id}] if folder_id else []
            })
            gfile.SetContentFile(file_path)
            gfile.Upload()
            print(f"[BackupManager] ☁ Uploaded to Google Drive: {file_name}")
        except Exception as e:
            print(f"[BackupManager] ❌ Upload failed: {e}")

    def _do_full_backup(self):
        """Complete DB backup (once daily with timestamp)"""
        if not os.path.exists(self.db_path):
            print(f"[BackupManager] ❌ Database not found: {self.db_path}")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"db_backup_{timestamp}.db")

        try:
            shutil.copy(self.db_path, backup_file)
            print(f"[BackupManager] ✅ Full DB Backup created: {backup_file}")

            if self._is_internet_available():
                self._upload_to_drive(backup_file)

        except Exception as e:
            print(f"[BackupManager] ❌ Full backup failed: {e}")

    def _extract_attendance(self, days=None):
        """Fetch attendance_logs data"""
        if not os.path.exists(self.db_path):
            print(f"[BackupManager] ❌ Database not found: {self.db_path}")
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM attendance_logs"
            params = ()

            if days:
                cutoff = datetime.now() - timedelta(days=days)
                query += " WHERE created_at >= ?"
                params = (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return rows

        except Exception as e:
            print(f"[BackupManager] ❌ Attendance extract failed: {e}")
            return None

    def _save_attendance_backup(self, rows, folder, label, drive_folder=None):
        """Save attendance logs into a proper SQLite .db file (tuple-safe)"""
        if not rows:
            print(f"[BackupManager] ⚠ No attendance data for {label} backup")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_path = os.path.join(folder, f"{label}_attendance_{timestamp}.db")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
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
            """)

            for row in rows:
                cursor.execute("""
                    INSERT OR IGNORE INTO attendance_logs (
                        emp_b_id, emp_code, emp_full_name, checkin_date, checkin_time,
                        checkout_date, checkout_time, status, mode, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, row[1:])

            conn.commit()
            conn.close()
            print(f"[BackupManager] ✅ {label} backup saved as DB: {db_path}")

            # 🌐 Upload to Google Drive
            if self._is_internet_available():
                self._upload_to_drive(db_path, drive_folder)

        except Exception as e:
            print(f"[BackupManager] ❌ {label} backup save failed: {e}")

    def _do_daily_backup(self):
        rows = self._extract_attendance(days=1)
        self._save_attendance_backup(rows, self.daily_dir, "daily", self.daily_drive_folder)

    def _do_weekly_backup(self):
        rows = self._extract_attendance(days=7)
        self._save_attendance_backup(rows, self.weekly_dir, "weekly", self.weekly_drive_folder)

    def _do_monthly_backup(self):
        rows = self._extract_attendance(days=30)
        self._save_attendance_backup(rows, self.monthly_dir, "monthly", self.monthly_drive_folder)

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.thread.start()
        print("[BackupManager] 🔄 Backup thread started")

    def stop(self):
        self.running = False
        print("[BackupManager] ⏹ Backup stopped")

    def _backup_loop(self):
        print("[BackupManager] Backup loop started...")
        while self.running:
            self._do_backups()
            time.sleep(60 * 60 * 12)  # हर 12 घंटे में run होगा

    def _do_backups(self):
        print(f"[BackupManager] 🚀 Running backups at {datetime.now()}")
        self._do_full_backup()
        self._do_daily_backup()
        if datetime.now().weekday() == 0:  # Monday
            self._do_weekly_backup()
        if datetime.now().day == 1:  # First of month
            self._do_monthly_backup()

# import os
# import sys
# import requests
# import sqlite3
# from PIL import Image
# from io import BytesIO
# import time
# import json

# # ---------------------- Path Utilities (Same as face recognition) ----------------------


# def get_app_dir():
#     """Gets the directory where the .exe or .py file is located"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         return os.path.dirname(sys.executable)
#     else:
#         return os.path.dirname(os.path.abspath(__file__))


# def get_data_dir():
#     """Gets the persistent data directory"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         return os.path.dirname(sys.executable)
#     else:
#         return os.path.dirname(os.path.abspath(__file__))


# # ---------------------- Configuration ----------------------

# DATA_DIR = get_data_dir()
# DB_PATH = os.path.join(DATA_DIR, "employees.db")
# IMAGE_DIR = os.path.join(DATA_DIR, "profile_images")

# print(f"[DEBUG] Data directory: {DATA_DIR}")
# print(f"[DEBUG] Database: {DB_PATH}")
# print(f"[DEBUG] Image directory: {IMAGE_DIR}")
# print(f"[DEBUG] Running as exe: {getattr(sys, 'frozen', False)}")


# def init_db():
#     """Initialize the database with proper schema"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         CREATE TABLE IF NOT EXISTS employees (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             emp_code TEXT UNIQUE,
#             emp_full_name TEXT NOT NULL,
#             emp_phone TEXT,
#             emp_email TEXT,
#             emp_profile_photo TEXT,
#             emp_profile_image_local TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     """
#     )

#     # Create index for faster searches
#     cursor.execute(
#         """
#         CREATE INDEX IF NOT EXISTS idx_emp_code ON employees(emp_code)
#     """
#     )

#     conn.commit()
#     conn.close()


# def employee_exists(emp_code):
#     """Check if employee already exists in database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("SELECT COUNT(*) FROM employees WHERE emp_code = ?", (emp_code,))
#     exists = cursor.fetchone()[0] > 0

#     conn.close()
#     return exists


# def update_employee(
#     emp_code,
#     emp_full_name,
#     emp_phone,
#     emp_email,
#     emp_profile_photo,
#     emp_profile_image_local,
# ):
#     """Update existing employee record"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         UPDATE employees
#         SET emp_full_name = ?, emp_phone = ?, emp_email = ?,
#             emp_profile_photo = ?, emp_profile_image_local = ?, updated_at = CURRENT_TIMESTAMP
#         WHERE emp_code = ?
#     """,
#         (
#             emp_full_name,
#             emp_phone,
#             emp_email,
#             emp_profile_photo,
#             emp_profile_image_local,
#             emp_code,
#         ),
#     )

#     conn.commit()
#     conn.close()


# def insert_employee(
#     emp_code,
#     emp_full_name,
#     emp_phone,
#     emp_email,
#     emp_profile_photo,
#     emp_profile_image_local,
# ):
#     """Insert new employee record"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         INSERT INTO employees (emp_code, emp_full_name, emp_phone, emp_email, emp_profile_photo, emp_profile_image_local)
#         VALUES (?, ?, ?, ?, ?, ?)
#     """,
#         (
#             emp_code,
#             emp_full_name,
#             emp_phone,
#             emp_email,
#             emp_profile_photo,
#             emp_profile_image_local,
#         ),
#     )

#     conn.commit()
#     conn.close()


# def fetch_and_store_employees(token):
#     """
#     Fetch employee data from the API, download their profile images,
#     and save both to a local SQLite DB and local image folder.
#     Prevents duplicate entries and updates existing records.
#     """

#     url = "https://dev.fixhr.app/api/admin/employee/get-employees-list"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json",
#         "Content-Type": "application/json",
#     }

#     # Initialize database
#     init_db()

#     # Ensure image directory exists
#     try:
#         os.makedirs(IMAGE_DIR, exist_ok=True)
#         print(f"[INFO] Created/verified image directory: {IMAGE_DIR}")
#         print(f"[DEBUG] Absolute path: {os.path.abspath(IMAGE_DIR)}")
#     except Exception as e:
#         print(f"[ERROR] Failed to create image directory: {e}")
#         raise Exception(f"Failed to create image directory: {e}")

#     # Fetch data from API with enhanced error handling
#     try:
#         print("[INFO] Fetching employee data from API...")
#         print(f"[DEBUG] Request URL: {url}")
#         print(f"[DEBUG] Request Headers: {headers}")

#         response = requests.get(url, headers=headers, timeout=30)

#         print(f"[DEBUG] Response Status Code: {response.status_code}")
#         print(f"[DEBUG] Response Headers: {dict(response.headers)}")
#         print(
#             f"[DEBUG] Response Content Type: {response.headers.get('content-type', 'Unknown')}"
#         )
#         print(f"[DEBUG] Response Content Length: {len(response.content)} bytes")

#         # Print first 500 characters of response for debugging
#         response_preview = response.text[:500]
#         print(f"[DEBUG] Response Preview (first 500 chars): {repr(response_preview)}")

#         if response.status_code == 401:
#             error_msg = "Authentication failed - Token may be expired or invalid"
#             print(f"[ERROR] {error_msg}")
#             raise Exception(error_msg)
#         elif response.status_code == 403:
#             error_msg = "Access forbidden - Insufficient permissions"
#             print(f"[ERROR] {error_msg}")
#             raise Exception(error_msg)
#         elif response.status_code == 404:
#             error_msg = "API endpoint not found"
#             print(f"[ERROR] {error_msg}")
#             raise Exception(error_msg)
#         elif response.status_code != 200:
#             error_msg = f"API request failed: HTTP {response.status_code}"
#             print(f"[ERROR] {error_msg}")
#             print(f"Response: {response.text[:1000]}")
#             raise Exception(error_msg)

#     except requests.exceptions.Timeout:
#         error_msg = "Request timeout - API server not responding"
#         print(f"[ERROR] {error_msg}")
#         raise Exception(error_msg)
#     except requests.exceptions.ConnectionError:
#         error_msg = "Connection error - Check internet connection"
#         print(f"[ERROR] {error_msg}")
#         raise Exception(error_msg)
#     except Exception as e:
#         print(f"[ERROR] API request exception: {e}")
#         raise

#     # Parse JSON response with enhanced error handling
#     try:
#         # Check if response is empty
#         if not response.text.strip():
#             print("[ERROR] Empty response from API")
#             raise Exception("Empty response from API")

#         # Check if response looks like JSON
#         response_text = response.text.strip()
#         if not (response_text.startswith("{") or response_text.startswith("[")):
#             print(
#                 f"[ERROR] Response doesn't look like JSON. First 100 chars: {response_text[:100]}"
#             )
#             print(f"[ERROR] Full response: {response_text}")
#             raise Exception("API response is not in JSON format")

#         json_data = response.json()
#         print("[INFO] API response parsed successfully")
#         print(
#             f"[DEBUG] JSON keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Response is not a dict'}"
#         )

#     except json.JSONDecodeError as e:
#         print(f"[ERROR] Failed to parse JSON response: {e}")
#         print(f"[ERROR] JSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
#         print(
#             f"[ERROR] Problematic content around error: {response.text[max(0, e.pos-50):e.pos+50]}"
#         )
#         print(f"[ERROR] Full response: {response.text}")
#         raise Exception(f"Invalid JSON response: {e}")
#     except Exception as e:
#         print(f"[ERROR] Unexpected error parsing response: {e}")
#         raise

#     # Extract employee data with better validation
#     if isinstance(json_data, dict):
#         employees_data = json_data.get("result", json_data.get("data", []))
#     else:
#         employees_data = json_data if isinstance(json_data, list) else []

#     print(f"[DEBUG] Employee data type: {type(employees_data)}")

#     if not employees_data:
#         print("[WARNING] No employee data found in API response")
#         print(
#             f"[DEBUG] Available keys in response: {list(json_data.keys()) if isinstance(json_data, dict) else 'N/A'}"
#         )
#         print(
#             "[INFO] This might be normal if no employees exist or different API structure"
#         )
#         return

#     if not isinstance(employees_data, list):
#         print(f"[ERROR] Expected list of employees, got {type(employees_data)}")
#         raise Exception("Invalid employee data format from API")

#     print(f"[INFO] Found {len(employees_data)} employees to process")

#     successful_downloads = 0
#     failed_downloads = 0
#     new_employees = 0
#     updated_employees = 0

#     # Loop through employee data
#     for i, emp in enumerate(employees_data, 1):
#         if not isinstance(emp, dict):
#             print(f"[SKIP] Invalid employee data format at index {i-1}: {type(emp)}")
#             continue

#         emp_code = emp.get("emp_code", "")
#         full_name = emp.get("emp_full_name", "")
#         phone = emp.get("emp_phone", "")
#         email = emp.get("emp_email", "")
#         image_url = emp.get("emp_profile_photo", "")

#         if not emp_code:
#             print(f"[SKIP] Employee with missing emp_code: {emp}")
#             continue

#         print(f"[{i}/{len(employees_data)}] Processing: {emp_code} - {full_name}")

#         local_image_path = ""

#         # Download and save image
#         if image_url and image_url.strip():
#             try:
#                 print(f"[DEBUG] Downloading image from: {image_url}")
#                 img_resp = requests.get(
#                     image_url,
#                     timeout=15,
#                     headers={
#                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#                     },
#                 )

#                 if img_resp.status_code == 200:
#                     if len(img_resp.content) < 100:
#                         print(
#                             f"[WARNING] Image too small for {emp_code}: {len(img_resp.content)} bytes"
#                         )
#                         failed_downloads += 1
#                     else:
#                         try:
#                             # Open and verify image
#                             image = Image.open(BytesIO(img_resp.content))
#                             print(
#                                 f"[DEBUG] Image loaded: {image.size}, mode: {image.mode}"
#                             )

#                             # Convert to RGB if necessary
#                             if image.mode in ("RGBA", "LA", "P"):
#                                 image = image.convert("RGB")
#                                 print(f"[DEBUG] Converted image to RGB")

#                             # Resize if too large
#                             max_size = 1024
#                             if max(image.size) > max_size:
#                                 original_size = image.size
#                                 image.thumbnail(
#                                     (max_size, max_size), Image.Resampling.LANCZOS
#                                 )
#                                 print(
#                                     f"[DEBUG] Resized from {original_size} to {image.size}"
#                                 )

#                             filename = f"{emp_code}.jpg"
#                             local_image_path = os.path.join(IMAGE_DIR, filename)

#                             print(f"[DEBUG] Saving to: {local_image_path}")

#                             # Save as JPEG with good quality
#                             image.save(local_image_path, "JPEG", quality=90)

#                             # Verify the saved file
#                             if os.path.exists(local_image_path):
#                                 saved_size = os.path.getsize(local_image_path)
#                                 if saved_size > 0:
#                                     print(
#                                         f"[SUCCESS] Saved: {filename} ({saved_size} bytes)"
#                                     )
#                                     successful_downloads += 1
#                                 else:
#                                     print(f"[ERROR] Saved file is empty: {filename}")
#                                     failed_downloads += 1
#                                     local_image_path = ""
#                             else:
#                                 print(
#                                     f"[ERROR] File not found after saving: {filename}"
#                                 )
#                                 failed_downloads += 1
#                                 local_image_path = ""

#                         except Exception as img_error:
#                             print(
#                                 f"[ERROR] Image processing failed for {emp_code}: {img_error}"
#                             )
#                             failed_downloads += 1

#                 else:
#                     print(
#                         f"[ERROR] HTTP {img_resp.status_code} downloading image for {emp_code}"
#                     )
#                     failed_downloads += 1

#             except requests.exceptions.Timeout:
#                 print(f"[ERROR] Timeout downloading image for {emp_code}")
#                 failed_downloads += 1
#             except Exception as e:
#                 print(f"[ERROR] Exception downloading image for {emp_code}: {e}")
#                 failed_downloads += 1
#         else:
#             print(f"[WARNING] No image URL for {emp_code}")
#             failed_downloads += 1

#         # Check if employee exists and insert/update accordingly
#         try:
#             if employee_exists(emp_code):
#                 update_employee(
#                     emp_code, full_name, phone, email, image_url, local_image_path
#                 )
#                 updated_employees += 1
#                 print(f"[UPDATE] Updated employee: {emp_code}")
#             else:
#                 insert_employee(
#                     emp_code, full_name, phone, email, image_url, local_image_path
#                 )
#                 new_employees += 1
#                 print(f"[NEW] Added new employee: {emp_code}")

#         except Exception as db_error:
#             print(f"[ERROR] Database operation failed for {emp_code}: {db_error}")

#         # Small delay to be respectful
#         time.sleep(0.1)

#     # Final verification
#     print(f"\n{'='*50}")
#     print(f"PROCESSING SUMMARY:")
#     print(f"✅ New employees added: {new_employees}")
#     print(f"🔄 Employees updated: {updated_employees}")
#     print(f"✅ Successful image downloads: {successful_downloads}")
#     print(f"❌ Failed image downloads: {failed_downloads}")
#     print(f"📁 Images directory: {os.path.abspath(IMAGE_DIR)}")

#     # Verify what's actually in the directory
#     try:
#         if os.path.exists(IMAGE_DIR):
#             actual_files = os.listdir(IMAGE_DIR)
#             image_files = [
#                 f for f in actual_files if f.lower().endswith((".png", ".jpg", ".jpeg"))
#             ]
#             print(f"📸 Actual files in directory: {len(actual_files)}")
#             print(f"📸 Actual image files: {len(image_files)}")

#             if len(image_files) > 0:
#                 print("✅ Images successfully saved:")
#                 for img_file in image_files[:5]:  # Show first 5
#                     file_path = os.path.join(IMAGE_DIR, img_file)
#                     file_size = os.path.getsize(file_path)
#                     print(f"   - {img_file} ({file_size} bytes)")
#                 if len(image_files) > 5:
#                     print(f"   ... and {len(image_files) - 5} more")
#             else:
#                 print("❌ No image files found in directory!")
#                 print("This will cause face recognition to not work properly.")
#         else:
#             print(f"❌ Image directory doesn't exist: {IMAGE_DIR}")
#     except Exception as e:
#         print(f"[ERROR] Directory verification failed: {e}")

#     print(f"{'='*50}\n")

#     if successful_downloads == 0 and new_employees == 0 and updated_employees == 0:
#         print("❌ CRITICAL: No employees were processed!")
#         raise Exception("No employees were successfully processed")
#     elif successful_downloads == 0:
#         print("⚠️ WARNING: No images were downloaded, but employee data was saved")
#         print("Face recognition will not work until images are available")

#     print("🎉 Employee data processing completed.")


# def get_employee_by_code(emp_code):
#     """Retrieve employee information by employee code"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         SELECT id, emp_code, emp_full_name, emp_phone, emp_email, emp_profile_photo, emp_profile_image_local, created_at, updated_at
#         FROM employees
#         WHERE emp_code = ?
#     """,
#         (emp_code,),
#     )

#     result = cursor.fetchone()
#     conn.close()

#     if result:
#         return {
#             "id": result[0],
#             "emp_code": result[1],
#             "emp_full_name": result[2],
#             "emp_phone": result[3],
#             "emp_email": result[4],
#             "emp_profile_photo": result[5],
#             "emp_profile_image_local": result[6],
#             "created_at": result[7],
#             "updated_at": result[8],
#         }
#     return None


# def get_all_employees():
#     """Retrieve all employees from database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         SELECT id, emp_code, emp_full_name, emp_phone, emp_email, emp_profile_photo, emp_profile_image_local, created_at, updated_at
#         FROM employees
#         ORDER BY emp_full_name
#     """
#     )

#     results = cursor.fetchall()
#     conn.close()

#     employees = []
#     for row in results:
#         employees.append(
#             {
#                 "id": row[0],
#                 "emp_code": row[1],
#                 "emp_full_name": row[2],
#                 "emp_phone": row[3],
#                 "emp_email": row[4],
#                 "emp_profile_photo": row[5],
#                 "emp_profile_image_local": row[6],
#                 "created_at": row[7],
#                 "updated_at": row[8],
#             }
#         )

#     return employees


# def get_employee_count():
#     """Get total number of employees in database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("SELECT COUNT(*) FROM employees")
#     count = cursor.fetchone()[0]

#     conn.close()
#     return count


# def verify_setup():
#     """Debug function to verify the setup"""
#     print(f"🔍 VERIFYING SETUP")
#     print(f"{'='*50}")
#     print(f"Data directory: {DATA_DIR}")
#     print(f"Database file: {DB_PATH}")
#     print(f"Image directory: {IMAGE_DIR}")
#     print(f"Running as .exe: {getattr(sys, 'frozen', False)}")

#     print(f"\nDirectory checks:")
#     print(f"Data dir exists: {os.path.exists(DATA_DIR)}")
#     print(f"Image dir exists: {os.path.exists(IMAGE_DIR)}")
#     print(f"Database exists: {os.path.exists(DB_PATH)}")

#     if os.path.exists(IMAGE_DIR):
#         files = os.listdir(IMAGE_DIR)
#         image_files = [
#             f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))
#         ]
#         print(f"Files in image directory: {len(files)}")
#         print(f"Image files: {len(image_files)}")

#     if os.path.exists(DB_PATH):
#         try:
#             count = get_employee_count()
#             print(f"Employees in database: {count}")
#         except Exception as e:
#             print(f"Error reading database: {e}")

#     print(f"{'='*50}")


# if __name__ == "__main__":
#     verify_setup()


import os
import requests
from PIL import Image
from io import BytesIO
import time
import json
from database import (
    init_db,
    employee_exists,
    update_employee,
    insert_employee,
    IMAGE_DIR,
    DATA_DIR,
)


def fetch_and_store_employees(token):
    url = "https://dev.fixhr.app/api/admin/employee/get-employees-list"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    init_db()
    os.makedirs(IMAGE_DIR, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    json_data = response.json()

    employees_data = json_data.get("result", json_data.get("data", []))
    if not employees_data:
        print("No employees found")
        return

    for i, emp in enumerate(employees_data, 1):
        if not isinstance(emp, dict):
            continue

        emp_code = emp.get("emp_code", "")
        emp_b_id = emp.get("emp_b_id", "")
        full_name = emp.get("emp_full_name", "")
        phone = emp.get("emp_phone", "")
        email = emp.get("emp_email", "")
        image_url = emp.get("emp_profile_photo", "")

        if not emp_code:
            continue

        local_image_path = download_employee_image(emp_code, image_url)

        if employee_exists(emp_code):
            update_employee(
                emp_code, emp_b_id, full_name, phone, email, image_url, local_image_path
            )
        else:
            insert_employee(
                emp_code, emp_b_id, full_name, phone, email, image_url, local_image_path
            )

        time.sleep(0.1)


def download_employee_image(emp_code, image_url):
    if not image_url or not image_url.strip():
        return ""

    try:
        img_resp = requests.get(image_url, timeout=15)
        if img_resp.status_code != 200:
            return ""

        image = Image.open(BytesIO(img_resp.content))
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        filename = f"{emp_code}.jpg"
        local_image_path = os.path.join(IMAGE_DIR, filename)
        image.save(local_image_path, "JPEG", quality=90)
        return local_image_path
    except Exception:
        return ""


# if __name__ == "__main__":
#     token = "YOUR_API_TOKEN_HERE"
#     fetch_and_store_employees(token)

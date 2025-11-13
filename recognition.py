# import insightface
# import numpy as np
# import faiss
# import cv2
# import sqlite3
# import os
# import sys
# from pathlib import Path
# from database import checkout_employee, checkin_employee, has_checkin_today
# import datetime

# # ---------------------- Enhanced Path Management for PyInstaller ----------------------


# def get_app_dir():
#     """Gets the directory where the .exe or .py file is located"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         # Use the directory containing the .exe file
#         return os.path.dirname(sys.executable)
#     else:
#         # Running as .py file
#         return os.path.dirname(os.path.abspath(__file__))


# def get_data_dir():
#     """Gets the persistent data directory"""
#     if getattr(sys, "frozen", False):  # Running as .exe
#         # For .exe, use the same directory as the executable
#         return os.path.dirname(sys.executable)
#     else:
#         # For .py file, use the script directory
#         return os.path.dirname(os.path.abspath(__file__))


# def get_bundled_resource_path(relative_path):
#     """Get path to bundled resource in PyInstaller temp directory"""
#     if getattr(sys, "frozen", False):
#         try:
#             # PyInstaller's temp folder for bundled resources
#             base_path = sys._MEIPASS
#             return os.path.join(base_path, relative_path)
#         except AttributeError:
#             pass
#     # Fallback to app directory
#     return os.path.join(get_app_dir(), relative_path)


# # ---------------------- Initialize Directories ----------------------

# APP_DIR = get_app_dir()
# DATA_DIR = get_data_dir()
# DB_PATH = os.path.join(DATA_DIR, "employees.db")

# # Profile images should be in the same directory as the .exe for easy access
# IMG_DIR = os.path.join(DATA_DIR, "profile_images")

# print("=" * 60)
# print("FACE RECOGNITION SYSTEM - INITIALIZATION")
# print("=" * 60)
# print(f"[DEBUG] Running as executable: {getattr(sys, 'frozen', False)}")
# print(f"[DEBUG] App directory: {APP_DIR}")
# print(f"[DEBUG] Data directory: {DATA_DIR}")
# print(f"[DEBUG] Database path: {DB_PATH}")
# print(f"[DEBUG] Profile images directory: {IMG_DIR}")
# print(f"[DEBUG] Current working directory: {os.getcwd()}")

# if getattr(sys, "frozen", False):
#     print(f"[DEBUG] Executable path: {sys.executable}")
#     try:
#         print(f"[DEBUG] PyInstaller temp directory: {sys._MEIPASS}")
#     except AttributeError:
#         print("[DEBUG] No PyInstaller temp directory found")

# # ---------------------- Create Required Directories ----------------------


# def setup_directories():
#     """Create necessary directories and provide helpful messages"""
#     directories_created = []

#     try:
#         # Create profile images directory
#         os.makedirs(IMG_DIR, exist_ok=True)
#         directories_created.append(IMG_DIR)
#         print(f"[INFO] Profile images directory ready: {IMG_DIR}")

#         # Check if directory is empty and provide instructions
#         if os.path.exists(IMG_DIR):
#             image_files = [
#                 f
#                 for f in os.listdir(IMG_DIR)
#                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
#             ]
#             if not image_files:
#                 print("[INFO] " + "=" * 50)
#                 print("[INFO] SETUP REQUIRED: No employee profile images found!")
#                 print(f"[INFO] Please add employee profile images to: {IMG_DIR}")
#                 print("[INFO] Image naming format: EMP001.jpg, EMP002.png, etc.")
#                 print("[INFO] Supported formats: PNG, JPG, JPEG, BMP")
#                 print("[INFO] After adding images, restart the application.")
#                 print("[INFO] " + "=" * 50)

#         return True

#     except Exception as e:
#         print(f"[ERROR] Failed to create directories: {e}")
#         return False


# # Setup directories
# setup_directories()

# # ---------------------- Constants ----------------------

# THRESHOLD = 0.35
# CTX_ID = -1
# IMG_SIZE = (640, 640)

# # ---------------------- Enhanced Model Loading with Error Handling ----------------------


# def load_insightface_model():
#     """Load InsightFace model with comprehensive error handling"""
#     print("[INFO] Loading InsightFace model...")

#     try:
#         # Try to load the model
#         model = insightface.app.FaceAnalysis(name="buffalo_l")
#         model.prepare(ctx_id=CTX_ID, det_size=IMG_SIZE)
#         print("[INFO] InsightFace model loaded successfully.")
#         return model

#     except Exception as e:
#         print(f"[ERROR] Failed to load InsightFace model: {e}")
#         print("[ERROR] Common solutions:")
#         print("  1. Ensure InsightFace is properly installed")
#         print("  2. Check if model files are accessible")
#         print("  3. Verify ONNX runtime is available")

#         if getattr(sys, "frozen", False):
#             print("[ERROR] PyInstaller specific issues:")
#             print("  - Model files might not be bundled correctly")
#             print("  - ONNX runtime DLLs might be missing")
#             print("  - Add model path to PyInstaller spec file")

#         raise


# # Load model
# model = load_insightface_model()

# # ---------------------- Enhanced Database Functions ----------------------


# def get_db_connection():
#     """Get database connection with better error handling"""
#     try:
#         if not os.path.exists(DB_PATH):
#             print(f"[WARNING] Database file not found: {DB_PATH}")
#             print(
#                 "[INFO] Please ensure employees.db is in the same directory as the executable"
#             )

#         return sqlite3.connect(DB_PATH)
#     except Exception as e:
#         print(f"[ERROR] Database connection failed: {e}")
#         print(f"[DEBUG] Attempted DB path: {DB_PATH}")
#         raise


# def get_employee_by_code(emp_code):
#     """Get employee details by employee code"""
#     try:
#         conn = get_db_connection()
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM employees WHERE emp_code = ?", (emp_code,))
#         emp = cursor.fetchone()
#         conn.close()
#         return dict(emp) if emp else None
#     except Exception as e:
#         print(f"[ERROR] Failed to get employee {emp_code}: {e}")
#         return None


# # ---------------------- Utilities ----------------------


# def normalize(emb):
#     """Normalize embedding vector"""
#     return emb / np.linalg.norm(emb)


# # ---------------------- Enhanced Face Encoding with Comprehensive Debugging ----------------------


# def comprehensive_image_directory_check():
#     """Perform comprehensive check of image directory and files"""
#     print("\n" + "=" * 60)
#     print("COMPREHENSIVE IMAGE DIRECTORY ANALYSIS")
#     print("=" * 60)

#     # Check if directory exists
#     print(f"Profile images directory: {IMG_DIR}")
#     print(f"Directory exists: {os.path.exists(IMG_DIR)}")
#     print(f"Directory absolute path: {os.path.abspath(IMG_DIR)}")

#     if not os.path.exists(IMG_DIR):
#         print("[ERROR] Profile images directory does not exist!")
#         return False, []

#     try:
#         # List all files in directory
#         all_files = os.listdir(IMG_DIR)
#         print(f"Total files in directory: {len(all_files)}")
#         print(f"All files: {all_files}")

#         # Filter image files
#         supported_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")
#         image_files = [f for f in all_files if f.lower().endswith(supported_extensions)]
#         print(f"Image files found: {len(image_files)}")
#         print(f"Image files: {image_files}")

#         if not image_files:
#             print("[WARNING] No supported image files found!")
#             print(f"[INFO] Supported formats: {', '.join(supported_extensions)}")
#             print(f"[INFO] Please add employee profile images to: {IMG_DIR}")
#             return False, []

#         # Check each image file
#         valid_images = []
#         for img_file in image_files:
#             image_path = os.path.join(IMG_DIR, img_file)
#             file_size = os.path.getsize(image_path)
#             print(f"  {img_file}: {file_size} bytes")

#             if file_size == 0:
#                 print(f"    [ERROR] File is empty!")
#                 continue

#             # Try to read with OpenCV
#             try:
#                 img = cv2.imread(image_path)
#                 if img is None:
#                     print(f"    [ERROR] OpenCV cannot read this image")
#                     continue

#                 print(f"    [OK] Image shape: {img.shape}")
#                 valid_images.append((img_file, image_path))

#             except Exception as e:
#                 print(f"    [ERROR] Failed to read image: {e}")
#                 continue

#         print(f"Valid images found: {len(valid_images)}")
#         print("=" * 60)
#         return len(valid_images) > 0, valid_images

#     except Exception as e:
#         print(f"[ERROR] Failed to analyze directory: {e}")
#         return False, []


# def prepare_face_encodings():
#     """Prepare face encodings from profile images"""
#     known_encodings = []
#     known_codes = []

#     print("[INFO] Starting face encoding process...")

#     # Comprehensive directory check
#     has_images, valid_images = comprehensive_image_directory_check()

#     if not has_images:
#         print("[INFO] No valid images found for face encoding")
#         return known_encodings, known_codes

#     # Process each valid image
#     for i, (img_file, image_path) in enumerate(valid_images, 1):
#         print(f"\n[{i}/{len(valid_images)}] Processing: {img_file}")

#         emp_code = os.path.splitext(img_file)[0]

#         try:
#             # Load image
#             img = cv2.imread(image_path)
#             print(f"  [OK] Image loaded: {img.shape}")

#             # Detect faces
#             faces = model.get(img)
#             if not faces:
#                 print(f"  [SKIP] No face detected in image")
#                 continue

#             print(f"  [OK] Found {len(faces)} face(s)")

#             # Use the first face for encoding
#             face = faces[0]
#             print(f"  [OK] Face bounding box: {face.bbox}")
#             print(f"  [OK] Face confidence: {face.det_score:.3f}")

#             # Generate embedding
#             embedding = face.embedding.astype(np.float32)
#             normalized_embedding = normalize(embedding)

#             known_encodings.append(normalized_embedding)
#             known_codes.append(emp_code)

#             print(f"  [SUCCESS] Face encoded for employee: {emp_code}")

#         except Exception as e:
#             print(f"  [ERROR] Failed to process {img_file}: {e}")
#             continue

#     print(f"\n[INFO] Face encoding completed!")
#     print(f"[INFO] Successfully encoded {len(known_encodings)} faces")
#     print(f"[INFO] Employee codes: {known_codes}")

#     return known_encodings, known_codes


# # ---------------------- FAISS Index Management ----------------------

# # Global variables
# face_encodings = []
# face_codes = []
# index = None


# def initialize_dummy_index():
#     """Create a dummy index to prevent errors when no faces are loaded"""
#     global index, face_codes
#     print("[INFO] Creating dummy index (no employee images loaded yet)...")
#     dummy_embedding = np.random.random((1, 512)).astype("float32")
#     index = faiss.IndexFlatIP(512)
#     index.add(dummy_embedding)
#     face_codes = ["DUMMY"]
#     return True


# def rebuild_face_index():
#     """Rebuild the face index from current profile images"""
#     global face_encodings, face_codes, index

#     print("[INFO] Rebuilding face recognition index...")

#     try:
#         new_face_encodings, new_face_codes = prepare_face_encodings()

#         if not new_face_encodings:
#             print("[INFO] No face encodings found, keeping dummy index...")
#             if index is None:
#                 initialize_dummy_index()
#             return False

#         # Create FAISS index
#         print(f"[INFO] Building FAISS index with {len(new_face_codes)} faces...")
#         embeddings_np = np.vstack(new_face_encodings).astype("float32")
#         new_index = faiss.IndexFlatIP(embeddings_np.shape[1])
#         new_index.add(embeddings_np)

#         # Update global variables
#         face_encodings = new_face_encodings
#         face_codes = new_face_codes
#         index = new_index

#         print(f"[SUCCESS] Face recognition index built successfully!")
#         print(f"[SUCCESS] Loaded {len(face_codes)} employee profiles")
#         return True

#     except Exception as e:
#         print(f"[ERROR] Failed to rebuild face index: {e}")
#         if index is None:
#             initialize_dummy_index()
#         return False


# # ---------------------- Initialize System ----------------------

# print("\n" + "=" * 60)
# print("INITIALIZING FACE RECOGNITION SYSTEM")
# print("=" * 60)

# # Start with dummy index
# initialize_dummy_index()

# # Try to build actual index
# try:
#     if rebuild_face_index():
#         print("[INFO] ✅ Face recognition system ready with employee profiles")
#     else:
#         print("[INFO] ⚠️  Face recognition system using dummy index")
#         print("[INFO] Add employee profile images and restart to enable recognition")
# except Exception as e:
#     print(f"[WARNING] Failed to build initial index: {e}")

# print("=" * 60)

# # ---------------------- Recognition Functions ----------------------


# def recognize_from_image(img):
#     """Recognize faces in the given image"""
#     results = []

#     if img is None:
#         return [
#             {
#                 "status": False,
#                 "emp_full_name": "Invalid image",
#                 "message": "No image provided",
#                 "similarity": 0.0,
#             }
#         ]

#     # Check if we have real faces loaded
#     if len(face_codes) == 1 and face_codes[0] == "DUMMY":
#         return [
#             {
#                 "status": False,
#                 "emp_full_name": "No profiles loaded",
#                 "message": f"Add profile images to: {os.path.basename(IMG_DIR)}",
#                 "similarity": 0.0,
#             }
#         ]

#     try:
#         faces = model.get(img)
#     except Exception as e:
#         return [
#             {
#                 "status": False,
#                 "emp_full_name": "Detection Error",
#                 "message": str(e),
#                 "similarity": 0.0,
#             }
#         ]

#     if not faces:
#         return [
#             {
#                 "status": False,
#                 "emp_full_name": "No face detected",
#                 "message": "Please face the camera clearly",
#                 "similarity": 0.0,
#             }
#         ]

#     for face in faces:
#         try:
#             emb = normalize(face.embedding.astype("float32")).reshape(1, -1)
#             D, I = index.search(emb, k=1)
#             sim = float(D[0][0])
#             matched_idx = int(I[0][0])

#             if sim > THRESHOLD:
#                 emp_code = face_codes[matched_idx]
#                 emp_details = get_employee_by_code(emp_code)

#                 if emp_details:
#                     current_date = datetime.datetime.now().strftime("%Y-%m-%d")
#                     current_time = datetime.datetime.now().strftime("%I:%M %p")
#                     print(emp_details)
#                     if has_checkin_today(emp_code, current_date):
#                         print("already checked in today")
#                         # Employee already checked in today, so checkout
#                         checkout_employee(emp_code, current_date, current_time)
#                         print("checkout completed")
#                     else:
#                         # Employee hasn't checked in today, so checkin
#                         print("checkin processs started")
#                         checkin_employee(
#                             emp_details["emp_b_id"],
#                             emp_code,
#                             emp_details["emp_full_name"],
#                             current_date,  # Current date
#                             current_time,  # Current time
#                         )
#                         print("checkin completed")

#                     result = {
#                         "status": True,
#                         "id": emp_details["id"],
#                         "emp_code": emp_details["emp_code"],
#                         "emp_b_id": emp_details["emp_b_id"],
#                         "emp_full_name": emp_details["emp_full_name"],
#                         "email": emp_details.get("emp_email", ""),
#                         "similarity": round(sim, 4),
#                     }
#                 else:
#                     result = {
#                         "status": False,
#                         "emp_full_name": "Unknown employee",
#                         "message": f"Employee {emp_code} not found in database",
#                         "similarity": round(sim, 4),
#                     }
#             else:
#                 result = {
#                     "status": False,
#                     "emp_full_name": "Unauthorized person",
#                     "message": "Face not recognized",
#                     "similarity": round(sim, 4),
#                 }

#             results.append(result)

#         except Exception as e:
#             results.append(
#                 {
#                     "status": False,
#                     "emp_full_name": "Recognition Error",
#                     "message": str(e),
#                     "similarity": 0.0,
#                 }
#             )

#     return results


# def detect_and_predict(frame):
#     """Main function called by the GUI for face recognition"""
#     try:
#         # Check if we need to rebuild index (new images might have been added)
#         if should_rebuild_index():
#             print("[INFO] New images detected, rebuilding index...")
#             rebuild_face_index()

#         results = recognize_from_image(frame)
#         return (
#             results[0]
#             if results
#             else {
#                 "status": False,
#                 "emp_full_name": "No face detected",
#                 "message": "Please face the camera",
#                 "similarity": 0.0,
#             }
#         )

#     except Exception as e:
#         return {
#             "status": False,
#             "emp_full_name": "System Error",
#             "message": str(e),
#             "similarity": 0.0,
#         }


# def should_rebuild_index():
#     """Check if face index needs to be rebuilt due to new images"""
#     global face_codes

#     try:
#         if not os.path.exists(IMG_DIR):
#             return False

#         current_images = [
#             f
#             for f in os.listdir(IMG_DIR)
#             if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
#         ]
#         current_codes = [os.path.splitext(f)[0] for f in current_images]

#         # If we have dummy index and now we have real images
#         if len(face_codes) == 1 and face_codes[0] == "DUMMY" and len(current_codes) > 0:
#             return True

#         # If number of images changed
#         real_face_codes = [code for code in face_codes if code != "DUMMY"]
#         if len(current_codes) != len(real_face_codes):
#             return True

#         # If image names changed
#         if set(current_codes) != set(real_face_codes):
#             return True

#         return False

#     except Exception as e:
#         print(f"[ERROR] Error checking if rebuild needed: {e}")
#         return False


# def force_rebuild_index():
#     """Force rebuild the face index (call this after adding new employees)"""
#     return rebuild_face_index()


# # ---------------------- Utility Functions for Debugging ----------------------


# def get_system_info():
#     """Get system information for debugging"""
#     return {
#         "app_dir": APP_DIR,
#         "data_dir": DATA_DIR,
#         "img_dir": IMG_DIR,
#         "db_path": DB_PATH,
#         "is_frozen": getattr(sys, "frozen", False),
#         "loaded_faces": len([code for code in face_codes if code != "DUMMY"]),
#         "face_codes": [code for code in face_codes if code != "DUMMY"],
#     }


# def print_system_status():
#     """Print current system status"""
#     info = get_system_info()
#     print("\n" + "=" * 40)
#     print("SYSTEM STATUS")
#     print("=" * 40)
#     for key, value in info.items():
#         print(f"{key}: {value}")
#     print("=" * 40)


# # Print initial system status
# print_system_status()


import insightface
import numpy as np
import faiss
import cv2
import sqlite3
import os
import sys
from pathlib import Path
from database import (
    process_employee_attendance,
    get_employee_attendance_status,
    get_next_attendance_action,
    normalize_date,
    normalize_time,
    get_current_date_str,
    get_current_time_str,
    get_app_dir,
    get_data_dir,
)
import datetime

# ---------------------- Enhanced Path Management for PyInstaller ----------------------


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


def get_bundled_resource_path(relative_path):
    """Get path to bundled resource in PyInstaller temp directory"""
    if getattr(sys, "frozen", False):
        try:
            base_path = sys._MEIPASS  # PyInstaller's temp folder for bundled resources
            return os.path.join(base_path, relative_path)
        except AttributeError:
            pass
    return os.path.join(get_app_dir(), relative_path)


# ---------------------- Initialize Directories ----------------------

APP_DIR = get_app_dir()
DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "employees.db")
IMG_DIR = os.path.join(DATA_DIR, "profile_images")

# Reduce noisy initialization logging to keep startup fast/clean
# Use on-demand logging via print_system_status() when needed.

# ---------------------- Create Required Directories ----------------------


def setup_directories():
    """Create necessary directories and provide helpful messages"""
    directories_created = []

    try:
        os.makedirs(IMG_DIR, exist_ok=True)
        directories_created.append(IMG_DIR)
        print(f"[INFO] Profile images directory ready: {IMG_DIR}")

        if os.path.exists(IMG_DIR):
            image_files = [
                f
                for f in os.listdir(IMG_DIR)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
            ]
            if not image_files:
                print("[INFO] " + "=" * 50)
                print("[INFO] SETUP REQUIRED: No employee profile images found!")
                print(f"[INFO] Please add employee profile images to: {IMG_DIR}")
                print("[INFO] Image naming format: EMP001.jpg, EMP002.png, etc.")
                print("[INFO] Supported formats: PNG, JPG, JPEG, BMP")
                print("[INFO] After adding images, restart the application.")
                print("[INFO] " + "=" * 50)

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create directories: {e}")
        return False


# Setup directories
setup_directories()

# ---------------------- Constants ----------------------

THRESHOLD = 0.35
CTX_ID = -1
IMG_SIZE = (640, 640)

# ---------------------- Enhanced Model Loading with Error Handling ----------------------


_model_instance = None


def load_insightface_model():
    """Load InsightFace model with error handling (lazy singleton)."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    try:
        instance = insightface.app.FaceAnalysis(name="buffalo_l")
        instance.prepare(ctx_id=CTX_ID, det_size=IMG_SIZE)
        _model_instance = instance
        return _model_instance
    except Exception as e:
        # Do not spam stdout; let caller decide how to handle
        raise


# Model will be loaded on first use to avoid heavy import-time cost
model = None

# ---------------------- Enhanced Database Functions ----------------------


def get_db_connection():
    """Get database connection with better error handling"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"[WARNING] Database file not found: {DB_PATH}")
            print(
                "[INFO] Please ensure employees.db is in the same directory as the executable"
            )

        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print(f"[DEBUG] Attempted DB path: {DB_PATH}")
        raise


def get_employee_by_code(emp_code):
    """Get employee details by employee code"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE emp_code = ?", (emp_code,))
        emp = cursor.fetchone()
        conn.close()
        return dict(emp) if emp else None
    except Exception as e:
        print(f"[ERROR] Failed to get employee {emp_code}: {e}")
        return None


# ---------------------- Utilities ----------------------


def normalize(emb):
    """Normalize embedding vector"""
    return emb / np.linalg.norm(emb)


# ---------------------- Enhanced Face Encoding with Comprehensive Debugging ----------------------


def comprehensive_image_directory_check():
    """Perform comprehensive check of image directory and files"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE IMAGE DIRECTORY ANALYSIS")
    print("=" * 60)

    print(f"Profile images directory: {IMG_DIR}")
    print(f"Directory exists: {os.path.exists(IMG_DIR)}")
    print(f"Directory absolute path: {os.path.abspath(IMG_DIR)}")

    if not os.path.exists(IMG_DIR):
        print("[ERROR] Profile images directory does not exist!")
        return False, []

    try:
        all_files = os.listdir(IMG_DIR)
        # Keep this lightweight
        # print(f"Total files in directory: {len(all_files)}")

        supported_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")
        image_files = [f for f in all_files if f.lower().endswith(supported_extensions)]
        print(f"Image files found: {len(image_files)}")
        # print(f"Image files: {image_files}")

        if not image_files:
            print("[WARNING] No supported image files found!")
            print(f"[INFO] Supported formats: {', '.join(supported_extensions)}")
            print(f"[INFO] Please add employee profile images to: {IMG_DIR}")
            return False, []

        valid_images = []
        for img_file in image_files:
            image_path = os.path.join(IMG_DIR, img_file)
            file_size = os.path.getsize(image_path)
            print(f"  {img_file}: {file_size} bytes")

            if file_size == 0:
                print(f"    [ERROR] File is empty!")
                continue

            try:
                img = cv2.imread(image_path)
                if img is None:
                    print(f"    [ERROR] OpenCV cannot read this image")
                    continue

                # print(f"    [OK] Image shape: {img.shape}")
                valid_images.append((img_file, image_path))

            except Exception as e:
                print(f"    [ERROR] Failed to read image: {e}")
                continue

        # print(f"Valid images found: {len(valid_images)}")
        return len(valid_images) > 0, valid_images

    except Exception as e:
        print(f"[ERROR] Failed to analyze directory: {e}")
        return False, []


def prepare_face_encodings():
    """Prepare face encodings from profile images"""
    known_encodings = []
    known_codes = []

    # Lightweight log
    print("[INFO] Building face encodings from profile images...")

    has_images, valid_images = comprehensive_image_directory_check()

    if not has_images:
        print("[INFO] No valid images found for face encoding")
        return known_encodings, known_codes

    for i, (img_file, image_path) in enumerate(valid_images, 1):
        # print progress occasionally
        if i % 10 == 1 or i == len(valid_images):
            print(f"[INFO] Encoding image {i}/{len(valid_images)}: {img_file}")

        emp_code = os.path.splitext(img_file)[0]

        try:
            img = cv2.imread(image_path)
            # print(f"  [OK] Image loaded: {img.shape}")

            faces = model.get(img)
            if not faces:
                print(f"  [SKIP] No face detected in image")
                continue

            # print(f"  [OK] Found {len(faces)} face(s)")

            face = faces[0]
            # print(f"  [OK] Face bounding box: {face.bbox}")
            # print(f"  [OK] Face confidence: {face.det_score:.3f}")

            embedding = face.embedding.astype(np.float32)
            normalized_embedding = normalize(embedding)

            known_encodings.append(normalized_embedding)
            known_codes.append(emp_code)

            # print(f"  [SUCCESS] Face encoded for employee: {emp_code}")

        except Exception as e:
            print(f"  [ERROR] Failed to process {img_file}: {e}")
            continue

    print(f"[INFO] Encoded {len(known_encodings)} faces")

    return known_encodings, known_codes


# ---------------------- FAISS Index Management ----------------------

face_encodings = []
face_codes = []
index = None
_last_index_codes_snapshot = set()
_last_dir_signature = None
_INDEX_FILENAME = "face_index.faiss"
_CODES_FILENAME = "face_codes.txt"
_SIG_FILENAME = "face_index.sig"


def _compute_dir_signature():
    """
    Compute a lightweight signature of the profile images directory
    based on (filename, size, mtime). Returns a frozenset for quick
    equality checks. This avoids rebuilding encodings unless files changed.
    """
    if not os.path.exists(IMG_DIR):
        return frozenset()

    supported_exts = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")
    entries = []
    for name in os.listdir(IMG_DIR):
        if not name.lower().endswith(supported_exts):
            continue
        path = os.path.join(IMG_DIR, name)
        try:
            stat = os.stat(path)
            entries.append((name, stat.st_size, int(stat.st_mtime)))
        except OSError:
            # If file disappeared between listdir and stat, skip it
            continue
    return frozenset(entries)


def _get_index_paths():
    """Return file paths for persisted index, codes and signature in DATA_DIR."""
    index_path = os.path.join(DATA_DIR, _INDEX_FILENAME)
    codes_path = os.path.join(DATA_DIR, _CODES_FILENAME)
    sig_path = os.path.join(DATA_DIR, _SIG_FILENAME)
    return index_path, codes_path, sig_path


def _save_index_to_disk():
    """Persist FAISS index, codes and directory signature to disk for fast reloads."""
    try:
        if index is None or not face_codes:
            return False
        index_path, codes_path, sig_path = _get_index_paths()
        # Save faiss index
        faiss.write_index(index, index_path)
        # Save codes (one per line)
        with open(codes_path, "w", encoding="utf-8") as f:
            for code in face_codes:
                f.write(f"{code}\n")
        # Save signature (as repr of sorted tuples for determinism)
        sig = _compute_dir_signature()
        with open(sig_path, "w", encoding="utf-8") as f:
            f.write(repr(sorted(list(sig))))
        print(f"[INFO] Persisted face index to disk at: {index_path}")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to persist face index: {e}")
        return False


def _load_index_from_disk_if_valid():
    """
    Try loading a persisted index if signature matches current directory.
    Returns True if loaded, else False.
    """
    global index, face_codes, _last_dir_signature
    try:
        index_path, codes_path, sig_path = _get_index_paths()
        if not (os.path.exists(index_path) and os.path.exists(codes_path) and os.path.exists(sig_path)):
            return False
        # Read saved signature
        with open(sig_path, "r", encoding="utf-8") as f:
            saved_sig_text = f.read().strip()
        current_sig = _compute_dir_signature()
        # Compare by string to avoid ordering differences
        if saved_sig_text != repr(sorted(list(current_sig))):
            return False
        # Load index and codes
        loaded_index = faiss.read_index(index_path)
        with open(codes_path, "r", encoding="utf-8") as f:
            loaded_codes = [line.strip() for line in f if line.strip()]
        if loaded_index.ntotal != len(loaded_codes):
            return False
        index = loaded_index
        face_codes = loaded_codes
        _last_dir_signature = current_sig
        print(f"[INFO] Loaded persisted face index with {len(face_codes)} profiles")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to load persisted face index: {e}")
        return False


def initialize_dummy_index():
    """Create a dummy index to prevent errors when no faces are loaded"""
    global index, face_codes
    print("[INFO] Creating dummy index (no employee images loaded yet)...")
    dummy_embedding = np.random.random((1, 512)).astype("float32")
    index = faiss.IndexFlatIP(512)
    index.add(dummy_embedding)
    face_codes = ["DUMMY"]
    return True


def rebuild_face_index():
    """Rebuild the face index from current profile images"""
    global face_encodings, face_codes, index, _last_dir_signature

    print("[INFO] Rebuilding face recognition index...")

    try:
        new_face_encodings, new_face_codes = prepare_face_encodings()

        if not new_face_encodings:
            print("[INFO] No face encodings found, keeping dummy index...")
            if index is None:
                initialize_dummy_index()
            return False

        print(f"[INFO] Building FAISS index with {len(new_face_codes)} faces...")
        embeddings_np = np.vstack(new_face_encodings).astype("float32")
        new_index = faiss.IndexFlatIP(embeddings_np.shape[1])
        new_index.add(embeddings_np)

        face_encodings = new_face_encodings
        face_codes = new_face_codes
        index = new_index

        print(f"[INFO] Index ready with {len(face_codes)} profiles")

        # Update directory signature after successful build
        _last_dir_signature = _compute_dir_signature()
        # Persist to disk for fast reuse on next app start
        _save_index_to_disk()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to rebuild face index: {e}")
        if index is None:
            initialize_dummy_index()
        return False


# ---------------------- Initialize System ----------------------

# Defer any heavy work until first call

def ensure_model_and_index_ready():
    global model, index, _last_index_codes_snapshot, _last_dir_signature
    if model is None:
        model = load_insightface_model()
    if index is None:
        # Try load persisted index; else build; fallback to dummy
        if not _load_index_from_disk_if_valid():
            if not rebuild_face_index():
                initialize_dummy_index()
                _last_index_codes_snapshot = set([code for code in face_codes])
    else:
        # Rebuild if images actually changed on disk (robust signature)
        current_sig = _compute_dir_signature()
        if _last_dir_signature is None:
            _last_dir_signature = current_sig
        elif current_sig != _last_dir_signature:
            # Only then rebuild
            if rebuild_face_index():
                _save_index_to_disk()
    if not _last_index_codes_snapshot:
        _last_index_codes_snapshot = set([code for code in face_codes])

# ---------------------- Enhanced Recognition Functions with FIXED Attendance Validation ----------------------


def recognize_from_image(img):
    """Recognize faces in the given image with STRICT attendance validation"""
    results = []

    if img is None:
        return [
            {
                "status": False,
                "emp_full_name": "Invalid image",
                "message": "No image provided",
                "similarity": 0.0,
                "status_icon": "❌",
            }
        ]

    # Check if we have real faces loaded
    if len(face_codes) == 1 and face_codes[0] == "DUMMY":
        return [
            {
                "status": False,
                "emp_full_name": "No profiles loaded",
                "message": f"Add profile images to: {os.path.basename(IMG_DIR)}",
                "similarity": 0.0,
                "status_icon": "⚠️",
            }
        ]

    try:
        ensure_model_and_index_ready()
        faces = model.get(img)
    except Exception as e:
        return [
            {
                "status": False,
                "emp_full_name": "Detection Error",
                "message": str(e),
                "similarity": 0.0,
                "status_icon": "❌",
            }
        ]

    if not faces:
        return [
            {
                "status": False,
                "emp_full_name": "No face detected",
                "message": "Please face the camera clearly",
                "similarity": 0.0,
                "status_icon": "👤",
            }
        ]

    for face in faces:
        try:
            emb = normalize(face.embedding.astype("float32")).reshape(1, -1)
            D, I = index.search(emb, k=1)
            sim = float(D[0][0])
            matched_idx = int(I[0][0])

            if sim > THRESHOLD:
                emp_code = face_codes[matched_idx]
                emp_details = get_employee_by_code(emp_code)

                if emp_details:
                    # Use normalized date and time functions
                    current_date = get_current_date_str()
                    current_time = get_current_time_str()

                    print(
                        f"[INFO] Employee recognized: {emp_details['emp_full_name']} ({emp_code})"
                    )
                    print(f"[INFO] Similarity: {sim:.4f}")
                    print(
                        f"[INFO] Processing attendance for date: {current_date} at time: {current_time}"
                    )

                    # Get current attendance status BEFORE processing
                    pre_attendance_status = get_employee_attendance_status(
                        emp_code, current_date
                    )
                    next_action = get_next_attendance_action(emp_code, current_date)

                    print(
                        f"[INFO] Pre-processing attendance status: {pre_attendance_status}"
                    )
                    print(f"[INFO] Next required action: {next_action}")

                    # Process attendance using the FIXED smart function
                    attendance_result = process_employee_attendance(
                        emp_details["emp_b_id"],
                        emp_code,
                        emp_details["emp_full_name"],
                        current_date,
                        current_time,
                    )

                    print(f"[INFO] Attendance processing result: {attendance_result}")

                    # Prepare detailed response based on attendance result
                    if attendance_result["success"]:
                        if attendance_result["action"] == "CHECKED_IN":
                            action_message = (
                                f"✅ Successfully checked in at {current_time}"
                            )
                            status_icon = "🟢"
                            detailed_message = f"Welcome {emp_details['emp_full_name']}! You have been checked in for {current_date}."
                        elif attendance_result["action"] == "CHECKED_OUT":
                            action_message = (
                                f"✅ Successfully checked out at {current_time}"
                            )
                            status_icon = "🔴"
                            detailed_message = f"Goodbye {emp_details['emp_full_name']}! You have been checked out for {current_date}."
                        else:
                            action_message = attendance_result["message"]
                            status_icon = "⚠️"
                            detailed_message = action_message
                    else:
                        if attendance_result["action"] == "ALREADY_CHECKED_IN":
                            action_message = (
                                f"⚠️ Already checked in today. Ready to check out."
                            )
                            status_icon = "🟡"
                            detailed_message = f"{emp_details['emp_full_name']}, you are already checked in. Your next action should be CHECK OUT."
                        elif attendance_result["action"] == "ALREADY_CHECKED_OUT":
                            action_message = (
                                f"⚠️ Already checked out today. Attendance completed."
                            )
                            status_icon = "🔵"
                            detailed_message = f"{emp_details['emp_full_name']}, you have already completed your attendance for today."
                        elif attendance_result["action"] == "ALREADY_COMPLETED":
                            action_message = (
                                f"⚠️ Attendance already completed for today."
                            )
                            status_icon = "🔵"
                            detailed_message = f"{emp_details['emp_full_name']}, your attendance for {current_date} is already complete."
                        elif attendance_result["action"] == "NOT_CHECKED_IN":
                            action_message = f"⚠️ Please check in first."
                            status_icon = "❓"
                            detailed_message = f"{emp_details['emp_full_name']}, you need to check in before you can check out."
                        else:
                            action_message = attendance_result["message"]
                            status_icon = "❌"
                            detailed_message = attendance_result["message"]

                    # Get updated attendance status after processing
                    post_attendance_status = get_employee_attendance_status(
                        emp_code, current_date
                    )
                    next_available_action = get_next_attendance_action(
                        emp_code, current_date
                    )

                    result = {
                        "status": attendance_result["success"],
                        "id": emp_details["id"],
                        "emp_code": emp_details["emp_code"],
                        "emp_b_id": emp_details["emp_b_id"],
                        "emp_full_name": emp_details["emp_full_name"],
                        "emp_email": emp_details.get("emp_email", ""),
                        "similarity": round(sim, 4),
                        "attendance_action": attendance_result["action"],
                        "attendance_message": action_message,
                        "detailed_message": detailed_message,
                        "status_icon": status_icon,
                        "next_action": next_available_action,
                        "current_date": current_date,
                        "current_time": current_time,
                        "attendance_details": attendance_result,
                        "pre_status": pre_attendance_status,
                        "post_status": post_attendance_status,
                        "can_checkin": post_attendance_status.get("can_checkin", False),
                        "can_checkout": post_attendance_status.get(
                            "can_checkout", False
                        ),
                        "has_checked_in": post_attendance_status.get(
                            "has_checked_in", False
                        ),
                        "has_checked_out": post_attendance_status.get(
                            "has_checked_out", False
                        ),
                    }
                else:
                    result = {
                        "status": False,
                        "emp_full_name": "Unknown employee",
                        "message": f"Employee {emp_code} not found in database",
                        "similarity": round(sim, 4),
                        "status_icon": "❓",
                    }
            else:
                result = {
                    "status": False,
                    "emp_full_name": "Unauthorized person",
                    "message": f"Face not recognized (similarity: {sim:.4f}, required: {THRESHOLD})",
                    "similarity": round(sim, 4),
                    "status_icon": "🚫",
                }

            results.append(result)

        except Exception as e:
            print(f"[ERROR] Face recognition error: {e}")
            results.append(
                {
                    "status": False,
                    "emp_full_name": "Recognition Error",
                    "message": str(e),
                    "similarity": 0.0,
                    "status_icon": "❌",
                }
            )

    return results


def detect_and_predict(frame):
    """Main function called by the GUI for face recognition - FIXED VERSION"""
    try:
        # Ensure model and index available (non-blocking if already loaded)
        ensure_model_and_index_ready()

        results = recognize_from_image(frame)
        return (
            results[0]
            if results
            else {
                "status": False,
                "emp_full_name": "No face detected",
                "message": "Please face the camera",
                "similarity": 0.0,
                "status_icon": "❓",
            }
        )

    except Exception as e:
        print(f"[ERROR] System error in detect_and_predict: {e}")
        return {
            "status": False,
            "emp_full_name": "System Error",
            "message": str(e),
            "similarity": 0.0,
            "status_icon": "❌",
        }


def should_rebuild_index():
    """Check if face index needs to be rebuilt due to new images"""
    global face_codes, _last_dir_signature

    try:
        if not os.path.exists(IMG_DIR):
            return False

        # Prefer robust signature check; fall back to name-based heuristics
        current_sig = _compute_dir_signature()
        if _last_dir_signature is None:
            _last_dir_signature = current_sig
        elif current_sig != _last_dir_signature:
            return True

        current_images = [
            f
            for f in os.listdir(IMG_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ]
        current_codes = [os.path.splitext(f)[0] for f in current_images]

        # If we have dummy index and now we have real images
        if len(face_codes) == 1 and face_codes[0] == "DUMMY" and len(current_codes) > 0:
            return True

        # If number of images changed
        real_face_codes = [code for code in face_codes if code != "DUMMY"]
        if len(current_codes) != len(real_face_codes):
            return True

        # If image names changed
        if set(current_codes) != set(real_face_codes):
            return True

        return False

    except Exception as e:
        print(f"[ERROR] Error checking if rebuild needed: {e}")
        return False


def force_rebuild_index():
    """Force rebuild the face index (call this after adding new employees)"""
    return rebuild_face_index()


# ---------------------- Enhanced Utility Functions ----------------------


def get_employee_attendance_today(emp_code):
    """Get today's attendance status for an employee"""
    current_date = get_current_date_str()
    return get_employee_attendance_status(emp_code, current_date)


def get_system_info():
    """Get system information for debugging"""
    return {
        "app_dir": APP_DIR,
        "data_dir": DATA_DIR,
        "img_dir": IMG_DIR,
        "db_path": DB_PATH,
        "is_frozen": getattr(sys, "frozen", False),
        "loaded_faces": len([code for code in face_codes if code != "DUMMY"]),
        "face_codes": [code for code in face_codes if code != "DUMMY"],
        "recognition_threshold": THRESHOLD,
        "current_date": get_current_date_str(),
        "current_time": get_current_time_str(),
    }


def print_system_status():
    """Print current system status"""
    info = get_system_info()
    print("\n" + "=" * 40)
    print("SYSTEM STATUS")
    print("=" * 40)
    for key, value in info.items():
        print(f"{key}: {value}")
    print("=" * 40)


def test_employee_recognition(emp_code):
    """Test function to check an employee's current attendance status"""
    print(f"\n{'='*50}")
    print(f"TESTING EMPLOYEE: {emp_code}")
    print(f"{'='*50}")

    emp_details = get_employee_by_code(emp_code)
    if not emp_details:
        print(f"❌ Employee {emp_code} not found in database")
        return

    print(f"Employee Name: {emp_details['emp_full_name']}")
    print(f"Employee B-ID: {emp_details['emp_b_id']}")

    current_date = get_current_date_str()
    attendance_status = get_employee_attendance_status(emp_code, current_date)

    print(f"\nAttendance Status for {current_date}:")
    print(f"Record Exists: {'✅' if attendance_status['exists'] else '❌'}")
    print(f"Has Checked In: {'✅' if attendance_status['has_checked_in'] else '❌'}")
    print(f"Has Checked Out: {'✅' if attendance_status['has_checked_out'] else '❌'}")
    print(f"Can Check In: {'✅' if attendance_status['can_checkin'] else '❌'}")
    print(f"Can Check Out: {'✅' if attendance_status['can_checkout'] else '❌'}")

    if attendance_status["has_checked_in"]:
        print(f"Check-in Time: {attendance_status['checkin_time']}")
    if attendance_status["has_checked_out"]:
        print(f"Check-out Time: {attendance_status['checkout_time']}")

    next_action = get_next_attendance_action(emp_code, current_date)
    print(f"Next Required Action: {next_action}")

    print(f"{'='*50}")


# Print initial system status
# print_system_status()

# ---------------------- Example Usage ----------------------
# if __name__ == "__main__":
#     print("\n" + "=" * 60)
#     print("FACE RECOGNITION ATTENDANCE SYSTEM READY")
#     print("=" * 60)

#     # Test with sample employee codes (if they exist)
#     test_codes = ["EMP001", "EMP002", "ADMIN"]
#     for code in test_codes:
#         if get_employee_by_code(code):
#             test_employee_recognition(code)
#             break

# ---------------------- Public Helpers for App Startup or Button ----------------------

def warm_up_recognition():
    """
    Load the InsightFace model and ensure a valid index exists without
    running any detection. Safe to call at startup or on a 'Start Detection' click.
    """
    ensure_model_and_index_ready()
    return {
        "loaded_faces": len([c for c in face_codes if c != "DUMMY"]),
        "using_dummy_index": len(face_codes) == 1 and face_codes[0] == "DUMMY",
        "img_dir": IMG_DIR,
    }


def build_index_now():
    """
    Force rebuild the face index immediately (e.g., after adding/removing images).
    Returns counts and success flag for UI feedback.
    """
    # Ensure model is loaded, but avoid unconditional rebuilds
    ensure_model_and_index_ready()
    # Only rebuild if index missing or images changed
    need_rebuild = index is None or should_rebuild_index()
    ok = True
    if need_rebuild:
        ok = rebuild_face_index()
    return {
        "success": ok,
        "profiles": len([c for c in face_codes if c != "DUMMY"]),
        "img_dir": IMG_DIR,
    }

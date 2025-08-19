# import os
# import cv2
# import numpy as np
# import tensorflow as tf
# import mediapipe as mp
# import sys
# from recognition import recognize_from_image
# def get_resource_path(relative_path):
#     """Return the absolute path to resource, even if frozen with PyInstaller"""
#     try:
#         base_path = sys._MEIPASS  # PyInstaller temp folder
#     except AttributeError:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)

# # Load TFLite model
# tflite_model_path = get_resource_path("liveness_model.tflite")

# # Check if liveness model exists
# liveness_model_available = os.path.exists(tflite_model_path)

# if liveness_model_available:
#     try:
#         interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
#         interpreter.allocate_tensors()
#         input_details = interpreter.get_input_details()
#         output_details = interpreter.get_output_details()
#         print("[INFO] Liveness model loaded successfully")
#     except Exception as e:
#         print(f"[WARNING] Failed to load liveness model: {e}")
#         liveness_model_available = False
# else:
#     print(f"[WARNING] Liveness model not found at: {tflite_model_path}")
#     print("[INFO] Running in face recognition only mode")

# # Initialize MediaPipe Face Detection
# mp_face_detection = mp.solutions.face_detection
# face_detection = mp_face_detection.FaceDetection(
#     model_selection=0, min_detection_confidence=0.6
# )

# def predict_liveness_tflite(face_img):
#     """Predict if face is live using TFLite model"""
#     if not liveness_model_available:
#         # If no liveness model, assume all faces are real
#         return True

#     try:
#         face = cv2.resize(face_img, (224, 224))
#         face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
#         face = np.expand_dims(face.astype("float32") / 255.0, axis=0)
#         interpreter.set_tensor(input_details[0]["index"], face)
#         interpreter.invoke()
#         output = interpreter.get_tensor(output_details[0]["index"])
#         return bool(output[0][0] < 0.5)
#     except Exception as e:
#         print(f"[ERROR] Liveness prediction failed: {e}")
#         # If liveness check fails, assume face is real to avoid blocking legitimate users
#         return True

# def detect_and_predict(img):
#     """Main function that combines face detection, liveness check, and face recognition"""
#     img = cv2.resize(img, (640, 480))
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     results = face_detection.process(img_rgb)

#     if not results.detections:
#         return {"status": False, "message": "No face detected", "face_image": None}

#     h, w, _ = img.shape
#     for detection in results.detections:
#         box = detection.location_data.relative_bounding_box
#         x = int(box.xmin * w)
#         y = int(box.ymin * h)
#         box_w = int(box.width * w)
#         box_h = int(box.height * h)

#         # Add margins
#         margin = 0.4
#         x_margin = int(box_w * margin)
#         y_margin = int(box_h * margin)
#         x1 = max(0, x - x_margin)
#         y1 = max(0, y - y_margin)
#         x2 = min(w, x + box_w + x_margin)
#         y2 = min(h, y + box_h + y_margin)

#         face_img = img[y1:y2, x1:x2]

#         if face_img.size == 0:
#             continue

#         # Liveness check (only if model is available)
#         if liveness_model_available:
#             is_real = predict_liveness_tflite(face_img)
#             if not is_real:
#                 print("❌ Liveness check failed")
#                 return {
#                     "status": False,
#                     "message": "Liveness check failed. Please try again.",
#                 }
#             print("✅ Human face detected")
#         else:
#             print("✅ Face detected (liveness check skipped - model not available)")

#         # Face recognition - try multiple import paths
#         recognition_results = None

#         # Try importing from liveness_detector first

#         try:
#             # Fallback to recognition module

#             recognition_results = recognize_from_image(face_img)
#         except ImportError:
#             return {
#                 "status": False,
#                 "message": "Face recognition module not available",
#             }


#         if recognition_results and recognition_results[0]["status"]:
#             recognized = recognition_results[0]
#             print(f"✅ Recognized: {recognized['emp_full_name']}")
#             return {
#                 "status": True,
#                 "message": "Person Found",
#                 "id": recognized["id"],
#                 "emp_code": recognized["emp_code"],
#                 "emp_b_id": recognized["emp_b_id"],
#                 "emp_full_name": recognized["emp_full_name"],
#                 "email": recognized.get("emp_email", ""),
#                 "similarity": recognized.get("similarity"),
#                 "face_image": face_img,
#             }
#         else:
#             return {
#                 "status": False,
#                 "message": "Unauthorized Person",
#                 "emp_full_name": "Unknown",
#                 "similarity": None,
#                 "face_image": face_img,
#             }

#     return {"status": False, "message": "No valid face cropped", "face_image": None}


import os
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
import sys
from recognition import recognize_from_image, get_current_date_str, get_current_time_str


def get_resource_path(relative_path):
    """Return the absolute path to resource, even if frozen with PyInstaller"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------- Liveness Model Setup ----------------------

# Load TFLite model
tflite_model_path = get_resource_path("liveness_model.tflite")

# Check if liveness model exists
liveness_model_available = os.path.exists(tflite_model_path)

if liveness_model_available:
    try:
        interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        print("[INFO] ✅ Liveness model loaded successfully")
        print(f"[INFO] Model input shape: {input_details[0]['shape']}")
        print(f"[INFO] Model output shape: {output_details[0]['shape']}")
    except Exception as e:
        print(f"[WARNING] Failed to load liveness model: {e}")
        liveness_model_available = False
else:
    print(f"[WARNING] Liveness model not found at: {tflite_model_path}")
    print("[INFO] Running in face recognition only mode (liveness check disabled)")

# ---------------------- MediaPipe Face Detection Setup ----------------------

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

try:
    face_detection = mp_face_detection.FaceDetection(
        model_selection=0,  # 0 for close-range detection, 1 for full-range
        min_detection_confidence=0.6,
    )
    print("[INFO] ✅ MediaPipe face detection initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize MediaPipe face detection: {e}")
    face_detection = None


# ---------------------- Enhanced Liveness Detection Functions ----------------------


def predict_liveness_tflite(face_img):
    """
    Predict if face is live using TFLite model
    Returns: True if live, False if spoofed
    """
    if not liveness_model_available:
        print("[DEBUG] Liveness model not available, assuming face is live")
        return True

    if face_img is None or face_img.size == 0:
        print("[DEBUG] Invalid face image for liveness detection")
        return False

    try:
        # Preprocess face image for liveness model
        face = cv2.resize(face_img, (224, 224))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        # Normalize pixel values to [0, 1]
        face = face.astype("float32") / 255.0
        face = np.expand_dims(face, axis=0)

        # Run inference
        interpreter.set_tensor(input_details[0]["index"], face)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])

        # Interpret output (assuming binary classification: 0=real, 1=fake)
        prediction_score = float(output[0][0])
        is_live = prediction_score < 0.5  # Threshold for real vs fake

        print(f"[DEBUG] Liveness prediction score: {prediction_score:.4f}")
        print(f"[DEBUG] Is live: {is_live}")

        return is_live

    except Exception as e:
        print(f"[ERROR] Liveness prediction failed: {e}")
        # If liveness check fails, assume face is real to avoid blocking legitimate users
        return True


def enhanced_face_detection(img):
    """
    Enhanced face detection with better error handling and validation
    Returns: List of face detections with bounding boxes
    """
    if img is None:
        print("[ERROR] No image provided for face detection")
        return []

    if face_detection is None:
        print("[ERROR] MediaPipe face detection not available")
        return []

    try:
        # Ensure image is in correct format
        if len(img.shape) == 3 and img.shape[2] == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img

        # Run MediaPipe face detection
        results = face_detection.process(img_rgb)

        if not results.detections:
            print("[DEBUG] No faces detected by MediaPipe")
            return []

        print(f"[DEBUG] MediaPipe detected {len(results.detections)} face(s)")
        return results.detections

    except Exception as e:
        print(f"[ERROR] Face detection failed: {e}")
        return []


def extract_face_with_margin(img, detection, margin=0.4):
    """
    Extract face region with margin from detection
    Returns: face_img, (x1, y1, x2, y2)
    """
    if img is None or detection is None:
        return None, None

    try:
        h, w, _ = img.shape
        box = detection.location_data.relative_bounding_box

        # Convert relative coordinates to absolute
        x = int(box.xmin * w)
        y = int(box.ymin * h)
        box_w = int(box.width * w)
        box_h = int(box.height * h)

        # Add margins
        x_margin = int(box_w * margin)
        y_margin = int(box_h * margin)

        # Calculate final coordinates with bounds checking
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(w, x + box_w + x_margin)
        y2 = min(h, y + box_h + y_margin)

        # Ensure we have a valid region
        if x2 <= x1 or y2 <= y1:
            print(f"[ERROR] Invalid face region: ({x1}, {y1}) to ({x2}, {y2})")
            return None, None

        # Extract face region
        face_img = img[y1:y2, x1:x2]

        if face_img.size == 0:
            print(f"[ERROR] Extracted face image is empty")
            return None, None

        print(
            f"[DEBUG] Extracted face region: ({x1}, {y1}) to ({x2}, {y2}), size: {face_img.shape}"
        )
        return face_img, (x1, y1, x2, y2)

    except Exception as e:
        print(f"[ERROR] Face extraction failed: {e}")
        return None, None


# ---------------------- Main Detection and Recognition Function ----------------------


def detect_and_predict(img):
    """
    Main function that combines face detection, liveness check, and face recognition
    This is the primary function called by the GUI system

    Returns: Dictionary with comprehensive results
    """
    print(f"\n[INFO] ========== STARTING DETECTION AND PREDICTION ==========")
    print(f"[INFO] Current date: {get_current_date_str()}")
    print(f"[INFO] Current time: {get_current_time_str()}")

    # Input validation
    if img is None:
        print("[ERROR] No image provided")
        return {
            "status": False,
            "message": "No image provided",
            "emp_full_name": "Error",
            "face_image": None,
            "status_icon": "❌",
        }

    # Resize image for consistent processing
    try:
        img = cv2.resize(img, (640, 480))
        print(f"[DEBUG] Image resized to: {img.shape}")
    except Exception as e:
        print(f"[ERROR] Failed to resize image: {e}")
        return {
            "status": False,
            "message": "Invalid image format",
            "emp_full_name": "Error",
            "face_image": None,
            "status_icon": "❌",
        }

    # Step 1: Face Detection
    print("[INFO] Step 1: Detecting faces...")
    detections = enhanced_face_detection(img)

    if not detections:
        print("[INFO] No faces detected")
        return {
            "status": False,
            "message": "No face detected. Please position your face clearly in front of the camera.",
            "emp_full_name": "No Face",
            "face_image": None,
            "status_icon": "👤",
        }

    # Process the first (most confident) detection
    detection = detections[0]
    confidence = (
        detection.score[0] if hasattr(detection, "score") and detection.score else 0.0
    )
    print(f"[INFO] Processing face with confidence: {confidence:.3f}")

    # Step 2: Extract face region
    print("[INFO] Step 2: Extracting face region...")
    face_img, bbox = extract_face_with_margin(img, detection, margin=0.4)

    if face_img is None:
        print("[ERROR] Failed to extract face region")
        return {
            "status": False,
            "message": "Could not extract face region. Please try again.",
            "emp_full_name": "Extraction Error",
            "face_image": None,
            "status_icon": "❌",
        }

    # Step 3: Liveness Detection (if available)
    print("[INFO] Step 3: Performing liveness check...")
    if liveness_model_available:
        is_real = predict_liveness_tflite(face_img)
        if not is_real:
            print("[WARNING] ❌ Liveness check FAILED - Potential spoofing detected")
            return {
                "status": False,
                "message": "Liveness check failed. Please ensure you are a real person and try again.",
                "emp_full_name": "Spoof Detection",
                "face_image": face_img,
                "status_icon": "🚫",
                "liveness_check": False,
                "liveness_available": True,
            }
        else:
            print("[INFO] ✅ Liveness check PASSED - Real human detected")
    else:
        print("[INFO] ⚠️ Liveness check SKIPPED - Model not available")

    # Step 4: Face Recognition and Attendance Processing
    print("[INFO] Step 4: Performing face recognition and attendance processing...")
    try:
        recognition_results = recognize_from_image(face_img)

        if not recognition_results:
            print("[ERROR] No recognition results returned")
            return {
                "status": False,
                "message": "Face recognition system error",
                "emp_full_name": "System Error",
                "face_image": face_img,
                "status_icon": "❌",
            }

        # Get the first (best) recognition result
        recognition_result = recognition_results[0]
        print(f"[INFO] Recognition result: {recognition_result}")

        if recognition_result["status"]:
            # Successful recognition and attendance processing
            print(f"[SUCCESS] ✅ Employee recognized and attendance processed")
            print(f"[SUCCESS] Employee: {recognition_result['emp_full_name']}")
            print(
                f"[SUCCESS] Action: {recognition_result.get('attendance_action', 'N/A')}"
            )
            print(
                f"[SUCCESS] Message: {recognition_result.get('attendance_message', 'N/A')}"
            )

            # Enhance the result with additional information
            enhanced_result = {
                "status": True,
                "message": recognition_result.get(
                    "detailed_message",
                    recognition_result.get("attendance_message", "Success"),
                ),
                "id": recognition_result.get("id"),
                "emp_code": recognition_result.get("emp_code"),
                "emp_b_id": recognition_result.get("emp_b_id"),
                "emp_full_name": recognition_result.get("emp_full_name"),
                "emp_email": recognition_result.get("emp_email", ""),
                "similarity": recognition_result.get("similarity"),
                "face_image": face_img,
                "status_icon": recognition_result.get("status_icon", "✅"),
                "attendance_action": recognition_result.get("attendance_action"),
                "attendance_message": recognition_result.get("attendance_message"),
                "detailed_message": recognition_result.get("detailed_message"),
                "next_action": recognition_result.get("next_action"),
                "current_date": recognition_result.get("current_date"),
                "current_time": recognition_result.get("current_time"),
                "can_checkin": recognition_result.get("can_checkin", False),
                "can_checkout": recognition_result.get("can_checkout", False),
                "has_checked_in": recognition_result.get("has_checked_in", False),
                "has_checked_out": recognition_result.get("has_checked_out", False),
                "liveness_check": True if liveness_model_available else None,
                "liveness_available": liveness_model_available,
                "face_confidence": confidence,
                "bbox": bbox,
            }

            return enhanced_result

        else:
            # Recognition failed or attendance issue
            print(f"[INFO] ❌ Recognition failed or attendance issue")
            print(f"[INFO] Reason: {recognition_result.get('message', 'Unknown')}")

            return {
                "status": False,
                "message": recognition_result.get("message", "Person not recognized"),
                "emp_full_name": recognition_result.get("emp_full_name", "Unknown"),
                "similarity": recognition_result.get("similarity"),
                "face_image": face_img,
                "status_icon": recognition_result.get("status_icon", "🚫"),
                "attendance_action": recognition_result.get("attendance_action"),
                "liveness_check": True if liveness_model_available else None,
                "liveness_available": liveness_model_available,
                "face_confidence": confidence,
                "bbox": bbox,
            }

    except ImportError as e:
        print(f"[ERROR] Recognition module import failed: {e}")
        return {
            "status": False,
            "message": "Face recognition module not available. Please check system configuration.",
            "emp_full_name": "Module Error",
            "face_image": face_img,
            "status_icon": "❌",
        }

    except Exception as e:
        print(f"[ERROR] Recognition processing failed: {e}")
        return {
            "status": False,
            "message": f"Recognition system error: {str(e)}",
            "emp_full_name": "System Error",
            "face_image": face_img,
            "status_icon": "❌",
        }

    finally:
        print(f"[INFO] ========== DETECTION AND PREDICTION COMPLETED ==========\n")


# ---------------------- Additional Utility Functions ----------------------


def validate_system_components():
    """Validate all system components are working"""
    print("\n" + "=" * 60)
    print("LIVENESS DETECTION SYSTEM VALIDATION")
    print("=" * 60)

    issues = []

    # Check MediaPipe
    if face_detection is None:
        issues.append("MediaPipe face detection not available")
    else:
        print("✅ MediaPipe face detection: Available")

    # Check Liveness Model
    if liveness_model_available:
        print("✅ Liveness model: Available")
        print(f"   Model path: {tflite_model_path}")
    else:
        issues.append("Liveness model not available (running in recognition-only mode)")
        print("⚠️ Liveness model: Not available")

    # Check Recognition Module
    try:
        from recognition import recognize_from_image

        print("✅ Face recognition module: Available")
    except ImportError as e:
        issues.append(f"Face recognition module not available: {e}")
        print("❌ Face recognition module: Not available")

    # Check TensorFlow
    try:
        print(f"✅ TensorFlow version: {tf.__version__}")
    except:
        issues.append("TensorFlow not available")
        print("❌ TensorFlow: Not available")

    # Check OpenCV
    try:
        print(f"✅ OpenCV version: {cv2.__version__}")
    except:
        issues.append("OpenCV not available")
        print("❌ OpenCV: Not available")

    print("=" * 60)

    if issues:
        print("⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ ALL COMPONENTS VALIDATED SUCCESSFULLY")

    print("=" * 60)

    return len(issues) == 0


def get_system_capabilities():
    """Get current system capabilities"""
    return {
        "face_detection": face_detection is not None,
        "liveness_detection": liveness_model_available,
        "face_recognition": True,  # Always assume available since we import it
        "tensorflow_available": True,
        "opencv_available": True,
        "mediapipe_available": face_detection is not None,
        "liveness_model_path": tflite_model_path if liveness_model_available else None,
    }


def test_with_sample_image(image_path):
    """Test the system with a sample image"""
    if not os.path.exists(image_path):
        print(f"[ERROR] Test image not found: {image_path}")
        return None

    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"[ERROR] Could not read image: {image_path}")
            return None

        print(f"[INFO] Testing with image: {image_path}")
        result = detect_and_predict(img)
        print(f"[INFO] Test result: {result}")
        return result

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return None


# ---------------------- System Initialization ----------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LIVENESS DETECTION SYSTEM INITIALIZATION")
    print("=" * 60)

    # Validate system
    validate_system_components()

    print("\nSystem capabilities:")
    capabilities = get_system_capabilities()
    for capability, available in capabilities.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {capability}: {status}")

    print("\n" + "=" * 60)
    print("LIVENESS DETECTION SYSTEM READY")
    print("=" * 60)


# ---------------------- Main Entry Point ----------------------

# if __name__ == "__main__":
#     print("\n[INFO] Liveness Detection System - Standalone Test Mode")

#     # Test with a sample image if provided
#     if len(sys.argv) > 1:
#         test_image_path = sys.argv[1]
#         print(f"[INFO] Testing with provided image: {test_image_path}")
#         test_with_sample_image(test_image_path)
#     else:
#         print("[INFO] No test image provided. System ready for integration.")
#         print("[INFO] Usage: python liveness_detector.py <path_to_test_image>")

#     # Show system status
#     print("\n[INFO] Current system status:")
#     capabilities = get_system_capabilities()
#     for capability, status in capabilities.items():
#         print(f"  {capability}: {'✅' if status else '❌'}")

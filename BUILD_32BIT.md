# Building 32-bit (x86) Version

## ⚠️ Important Limitations

**32-bit builds have significant limitations:**
- Older package versions required (some features may be missing)
- Lower performance due to memory constraints
- Some dependencies may not work perfectly
- **Recommended: Use 64-bit if possible**

## Requirements for 32-bit Build

### 1. Python Installation
- **Python 3.8 or 3.9 (32-bit)** - Download from python.org
- **DO NOT use 3.10+** (many packages dropped 32-bit support)

### 2. Modified Dependencies

Create a separate `requirements_32bit.txt` with these versions:

```
# 32-bit Compatible Versions
tensorflow==1.15.5          # Last version with 32-bit support
keras==2.3.1                 # Compatible with TensorFlow 1.15
opencv-python==4.5.5.64      # Older version with 32-bit wheels
numpy==1.19.5                # Last version with 32-bit support
PyQt5==5.15.4                # Should work on 32-bit
requests==2.28.2
psutil==5.9.5
ntplib==0.4.0
pyttsx3==2.90

# These may need alternatives or removal:
# mediapipe - NO 32-bit support (consider removing liveness detection)
# insightface - NO 32-bit support (consider alternative face recognition)
# onnxruntime - NO 32-bit support (consider removing if not critical)
# faiss-cpu - NO 32-bit support (use alternative search or remove)
```

### 3. Code Modifications Needed

You'll need to:
1. **Remove or disable MediaPipe** (liveness detection won't work)
2. **Remove or replace InsightFace** (face recognition alternative needed)
3. **Remove or replace FAISS** (use simpler face matching)
4. **Update TensorFlow code** (1.15 uses different APIs than 2.x)

### 4. Build Steps

```bash
# 1. Install 32-bit Python 3.8 or 3.9
# 2. Create virtual environment
python -m venv venv_32bit
venv_32bit\Scripts\activate

# 3. Install 32-bit compatible packages
pip install -r requirements_32bit.txt

# 4. Modify code to remove unsupported features
# (See code changes below)

# 5. Build with PyInstaller
pyinstaller --onefile --windowed --icon=fix_hr_prod_logo.png main_32bit.py
```

## Alternative Approach: Dual Build Script

Create a build script that detects architecture and builds accordingly.


# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os
import sys

# Collect data files
mediapipe_datas = collect_data_files('mediapipe', include_py_files=False)
insightface_datas = collect_data_files('insightface', include_py_files=False)

# Collect dynamic libraries
mediapipe_binaries = collect_dynamic_libs('mediapipe')
insightface_binaries = collect_dynamic_libs('insightface')

block_cipher = None

# ✅ Include profile_images directory if it exists (but it's okay if it doesn't)
profile_images_data = []
if os.path.exists('profile_images'):
    profile_images_data = [('profile_images', 'profile_images')]
    print("✅ Found profile_images directory - will be included in .exe")
elif os.path.exists('data/profile_images'):
    profile_images_data = [('data/profile_images', 'profile_images')]
    print("✅ Found profile_images in data/ - will be included in .exe")
else:
    print("ℹ️ profile_images directory not found - will be created dynamically at runtime")

# ✅ Include database file if it exists (but it's okay if it doesn't)
database_data = []
if os.path.exists('employees.db'):
    database_data = [('employees.db', '.')]
    print("✅ Found employees.db - will be included in .exe")
elif os.path.exists('data/employees.db'):
    database_data = [('data/employees.db', 'employees.db')]
    print("✅ Found employees.db in data/ - will be included in .exe")
else:
    print("ℹ️ employees.db not found - will be created dynamically at runtime")

# Include face index files if they exist
face_index_data = []
for f in ['face_index.faiss', 'face_codes.txt', 'face_index.sig']:
    if os.path.exists(f):
        face_index_data.append((f, '.'))
    elif os.path.exists(f'data/{f}'):
        face_index_data.append((f'data/{f}', '.'))

# Hidden imports for all modules
hidden_imports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'cv2',
    'numpy',
    'tensorflow',
    'keras',
    'mediapipe',
    'insightface',
    'onnxruntime',
    'faiss',
    'sqlite3',
    'requests',
    'psutil',
    'ntplib',
    'pyttsx3',
    'pytz',
    'threading',
    'datetime',
    'json',
    'io',
    'sys',
    'os',
    'scipy',
    'scipy.ndimage',
    'scipy.spatial',
    'matplotlib',
    'matplotlib.pyplot',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=mediapipe_binaries + insightface_binaries,
    datas=[
        ('liveness_model.tflite', '.'),  # ✅ Your custom model
        ('background-img.jpg', '.'),
        ('fix_hr_prod_logo.png', '.'),
    ] + mediapipe_datas                  # ✅ Include MediaPipe internal model files
    + insightface_datas                  # ✅ Include InsightFace data files
    + profile_images_data                # ✅ Include profile images directory
    + database_data                      # ✅ Include database if exists
    + face_index_data,                   # ✅ Include face index files if exist
    hiddenimports=hidden_imports,
    hookspath=['.'],  # Include custom hooks
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FixHR_FaceAttendance_x64',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid DLL issues
    console=True,             # ✅ Keep console=True for debugging during development
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fix_hr_prod_logo.png' if os.path.exists('fix_hr_prod_logo.png') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX to avoid DLL issues
    upx_exclude=[],
    name='FixHR_FaceAttendance_x64',
)

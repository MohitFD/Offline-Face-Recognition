# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# ✅ Collect MediaPipe model/data files
mediapipe_datas = collect_data_files('mediapipe', include_py_files=False)

block_cipher = None

# ✅ Include profile_images directory if it exists (but it's okay if it doesn't)
profile_images_data = []
if os.path.exists('profile_images'):
    # Add the entire directory
    profile_images_data = [('profile_images', 'profile_images')]
    print("✅ Found profile_images directory - will be included in .exe")
else:
    print("ℹ️ profile_images directory not found - will be created dynamically at runtime")

# ✅ Include database file if it exists (but it's okay if it doesn't)
database_data = []
if os.path.exists('employees.db'):
    database_data = [('employees.db', '.')]
    print("✅ Found employees.db - will be included in .exe")
else:
    print("ℹ️ employees.db not found - will be created dynamically at runtime")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('liveness_model.tflite', '.'),  # ✅ Your custom model
    ] + mediapipe_datas                  # ✅ Include MediaPipe internal model files
    + profile_images_data                # ✅ Include profile images directory
    + database_data,                     # ✅ Include database if exists
    hiddenimports=[
        'insightface',
        'onnxruntime',
        'numpy',
        'cv2',
        'faiss',
        'sqlite3',
        'mediapipe',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='face_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,             # ✅ Keep console=True for debugging during development
    windowed=False,           # ✅ Set to True later when everything works
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='face_app',
)
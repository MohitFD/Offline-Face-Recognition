# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# ✅ Collect MediaPipe model/data files
mediapipe_datas = collect_data_files('mediapipe', include_py_files=False)

block_cipher = None


# Hidden imports for InsightFace and dependencies
hidden_imports = [
    'insightface',
    'onnxruntime',
    'onnx',
    'cv2',
    'numpy',
    'faiss',
    'sqlite3',
    'pickle',
    'skimage',
    'PIL',
    'PIL.Image',
    'sklearn',
    'scipy',
    'matplotlib',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'onnxruntime.capi._pybind_state',
]

# Data files to include
datas = [
    # Include InsightFace models if bundling them
    # ('C:/Users/suppo/.insightface/models', 'insightface/models'),
    
    # Include any other data files
    ('profile_images', 'profile_images'),  # If you want to bundle default images
    ('C:\\Users\\suppo\\.insightface\\models\\buffalo_l\\*', '.insightface/models/buffalo_l'),
    ('liveness_model.tflite', '.'),
]+ mediapipe_datas

# Binary files to include (for ONNX runtime)
binaries = []

a = Analysis(
    ['main.py'],  # Your main script
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='face_recognition_app',
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window
)
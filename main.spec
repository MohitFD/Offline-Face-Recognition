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
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=mediapipe_binaries + insightface_binaries,
    datas=[
        ('liveness_model.tflite', '.'),
        ('background-img.jpg', '.'),
        ('fix_hr_prod_logo.png', '.'),
    ]
    + (
        [('data/profile_images', 'profile_images')]
        if os.path.isdir(os.path.join('data', 'profile_images'))
        else []
    )
    + (
        [(p, '.') for p in ['data/employees.db', 'data/face_index.faiss', 'data/face_codes.txt', 'data/face_index.sig']
         if os.path.exists(p)]
    )
    + mediapipe_datas
    + insightface_datas,

    hiddenimports=hidden_imports,
    hookspath=['.'],  # Include custom hooks
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FixHR_FaceAttendance_x64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid DLL issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fix_hr_prod_logo.png',
    version=None,
)

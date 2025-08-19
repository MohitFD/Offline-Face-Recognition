# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# ✅ Collect MediaPipe model/data files
mediapipe_datas = collect_data_files('mediapipe', include_py_files=False)
insightface_datas = collect_data_files('insightface', include_py_files=False)
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('liveness_model.tflite', '.'),
        ('employees.db', '.'),
        ('profile_images/*', 'profile_images/'),
    ] + mediapipe_datas + insightface_datas,

    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fix_hr_prod_logo.png',
)

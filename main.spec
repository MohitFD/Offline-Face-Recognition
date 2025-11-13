
from PyInstaller.utils.hooks import collect_data_files
import os


mediapipe_datas = collect_data_files('mediapipe', include_py_files=False)
insightface_datas = collect_data_files('insightface', include_py_files=False)
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
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

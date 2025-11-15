# PyInstaller hook to ensure Python DLL is included
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
import sys
import os

# Collect Python DLL
binaries = []
datas = []

# Find Python DLL
python_dll_name = f'python{sys.version_info.major}{sys.version_info.minor}.dll'
python_dll_path = os.path.join(sys.executable.replace('python.exe', ''), python_dll_name)

if os.path.exists(python_dll_path):
    binaries.append((python_dll_path, '.'))

# Also try common locations
common_paths = [
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), 'DLLs'),
    sys.prefix,
    os.path.join(sys.prefix, 'DLLs'),
]

for path in common_paths:
    dll_path = os.path.join(path, python_dll_name)
    if os.path.exists(dll_path) and dll_path not in [b[0] for b in binaries]:
        binaries.append((dll_path, '.'))


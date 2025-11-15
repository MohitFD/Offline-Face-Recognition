@echo off
REM Build script for both 32-bit and 64-bit versions
echo ========================================
echo Building FixHR Face Recognition App
echo ========================================
echo.

REM Check Python architecture
python -c "import platform; print('Python Architecture:', platform.architecture()[0])"
echo.

set /p BUILD_TYPE="Build 32-bit (1), 64-bit (2), or Both (3)? "

if "%BUILD_TYPE%"=="1" goto BUILD_32
if "%BUILD_TYPE%"=="2" goto BUILD_64
if "%BUILD_TYPE%"=="3" goto BUILD_BOTH
goto END

:BUILD_32
echo.
echo ========================================
echo Building 32-bit (x86) Version
echo ========================================
echo WARNING: 32-bit build has limitations!
echo - Liveness detection disabled
echo - Some face recognition features may not work
echo - Requires Python 3.8 or 3.9 (32-bit)
echo.
pause

REM Check if 32-bit Python
python -c "import sys; assert sys.maxsize <= 2**32, 'ERROR: Not 32-bit Python!'; print('32-bit Python detected')"
if errorlevel 1 (
    echo ERROR: You need 32-bit Python for this build!
    pause
    goto END
)

REM Install 32-bit dependencies
echo Installing 32-bit dependencies...
pip install -r requirements_32bit.txt

REM Build
echo Building 32-bit executable...
pyinstaller --onefile --windowed --icon=fix_hr_prod_logo.png --name="FixHR_FaceAttendance_32bit" main.py
echo.
echo 32-bit build complete! Check dist\FixHR_FaceAttendance_32bit.exe
goto END

:BUILD_64
echo.
echo ========================================
echo Building 64-bit (x64) Version
echo ========================================
echo Installing dependencies...
pip install -r requirements.txt
echo Building 64-bit executable...
pyinstaller --onefile --windowed --icon=fix_hr_prod_logo.png --name="FixHR_FaceAttendance_64bit" main.py
echo.
echo 64-bit build complete! Check dist\FixHR_FaceAttendance_64bit.exe
goto END

:BUILD_BOTH
echo.
echo ========================================
echo Building BOTH Versions
echo ========================================
echo.
echo This requires TWO separate Python installations:
echo 1. 32-bit Python 3.8/3.9 for 32-bit build
echo 2. 64-bit Python 3.9-3.11 for 64-bit build
echo.
echo Please run this script twice:
echo - First with 32-bit Python installed
echo - Then with 64-bit Python installed
echo.
pause
goto END

:END
echo.
echo Build process finished!
pause


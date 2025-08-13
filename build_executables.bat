@echo off
echo ================================================
echo ScoShow - Building Executable Files
echo ================================================
echo.

REM Set console encoding to UTF-8
chcp 65001 > nul

REM Create dist directory if not exists
if not exist "dist" mkdir dist

echo 🚀 Building ScoShow Client (Debug Version)...
echo ================================================
pyinstaller --onefile --windowed --name="ScoShow_Client_Debug" ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=screeninfo ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=build ^
    scoshow_client_debug.py

if %ERRORLEVEL% EQU 0 (
    echo ✅ ScoShow Client built successfully!
) else (
    echo ❌ Failed to build ScoShow Client
    pause
    exit /b 1
)

echo.
echo 🚀 Building ScoShow Remote Super...
echo ================================================
pyinstaller --onefile --windowed --name="ScoShow_Remote_Super" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=screeninfo ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=build ^
    scoshow_remote_super.py

if %ERRORLEVEL% EQU 0 (
    echo ✅ ScoShow Remote Super built successfully!
) else (
    echo ❌ Failed to build ScoShow Remote Super
    pause
    exit /b 1
)

echo.
echo 🎉 All executables built successfully!
echo ================================================
echo 📁 Files created in dist\ folder:
echo    - ScoShow_Client_Debug.exe
echo    - ScoShow_Remote_Super.exe
echo.
echo 📋 What's next:
echo    1. Copy background folder to same location as .exe files
echo    2. Copy mqtt_config.py and other config files if needed
echo    3. Test the executables
echo.
pause

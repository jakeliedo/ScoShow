@echo off
title ScoShow Advanced Build System
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🚀 ScoShow Advanced Builder              ║
echo ║                                                              ║
echo ║     Building Professional Edition Executables               ║
echo ║     • ScoShow Professional Client (Debug Enhanced)          ║
echo ║     • ScoShow Super Remote Control                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/4] 📦 Installing required packages...
pip install -r requirements_exe.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

echo.
echo [2/4] 🔧 Building ScoShow Professional Client (Debug Enhanced)...
pyinstaller --onefile --windowed ^
    --name "ScoShow_Professional_Client" ^
    --add-data "mqtt_config.py;." ^
    --add-data "background;background" ^
    --hidden-import=screeninfo ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtGui ^
    --version-file=version_info_client.txt ^
    scoshow_client_debug.py

if errorlevel 1 (
    echo ❌ Failed to build client executable
    pause
    exit /b 1
)

echo.
echo [3/4] 🎮 Building ScoShow Super Remote Control...
pyinstaller --onefile --windowed ^
    --name "ScoShow_Super_Remote" ^
    --add-data "mqtt_config.py;." ^
    --add-data "remote_config.json;." ^
    --hidden-import=screeninfo ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtGui ^
    --version-file=version_info_remote.txt ^
    scoshow_remote_super.py

if errorlevel 1 (
    echo ❌ Failed to build remote executable
    pause
    exit /b 1
)

echo.
echo [4/4] 📋 Creating deployment structure...
if not exist "ScoShow_Professional_Deploy" mkdir "ScoShow_Professional_Deploy"
if not exist "ScoShow_Professional_Deploy\Client" mkdir "ScoShow_Professional_Deploy\Client"
if not exist "ScoShow_Professional_Deploy\Remote" mkdir "ScoShow_Professional_Deploy\Remote"

echo Copying client files...
copy "dist\ScoShow_Professional_Client.exe" "ScoShow_Professional_Deploy\Client\"
copy "mqtt_session.json" "ScoShow_Professional_Deploy\Client\" 2>nul
xcopy "background" "ScoShow_Professional_Deploy\Client\background\" /E /I /Y

echo Copying remote files...
copy "dist\ScoShow_Super_Remote.exe" "ScoShow_Professional_Deploy\Remote\"
copy "mqtt_session.json" "ScoShow_Professional_Deploy\Remote\" 2>nul
copy "remote_config.json" "ScoShow_Professional_Deploy\Remote\" 2>nul

echo.
echo ✅ Build completed successfully!
echo.
echo 📂 Executables created:
echo    • ScoShow_Professional_Client.exe (in dist\ and Client\)
echo    • ScoShow_Super_Remote.exe (in dist\ and Remote\)
echo.
echo 📁 Deployment folder: ScoShow_Professional_Deploy\
echo    ├── Client\
echo    │   ├── ScoShow_Professional_Client.exe
echo    │   ├── background\
echo    │   └── mqtt_session.json
echo    └── Remote\
echo        ├── ScoShow_Super_Remote.exe
echo        ├── mqtt_session.json
echo        └── remote_config.json
echo.
echo 🎉 Ready for deployment!
pause

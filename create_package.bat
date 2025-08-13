@echo off
echo Creating ScoShow Deployment Package...
echo.

:: Create deployment folder
if exist "ScoShow_Deploy" rmdir /s /q "ScoShow_Deploy"
mkdir "ScoShow_Deploy"
mkdir "ScoShow_Deploy\Client"
mkdir "ScoShow_Deploy\Remote"

:: Copy executables
copy "dist\ScoShow_Client_Debug.exe" "ScoShow_Deploy\Client\ScoShow_Client.exe"
copy "dist\ScoShow_Remote_Super.exe" "ScoShow_Deploy\Remote\ScoShow_Remote.exe"

:: Copy background folder for client
xcopy "background" "ScoShow_Deploy\Client\background\" /E /I

:: Copy documentation
copy "DEPLOYMENT.md" "ScoShow_Deploy\"
copy "README_MQTT.md" "ScoShow_Deploy\" 2>nul

:: Create quick start guides
echo Creating Quick Start guides...

:: Client Quick Start
echo # ScoShow Client - Quick Start > "ScoShow_Deploy\Client\QUICKSTART.txt"
echo. >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo 1. Simply run ScoShow_Client.exe >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo 2. Keep this running on your display computer >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo 3. The client will connect to MQTT broker automatically >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo 4. Wait for remote control commands >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo. >> "ScoShow_Deploy\Client\QUICKSTART.txt"
echo Note: Make sure background folder is in same directory as EXE! >> "ScoShow_Deploy\Client\QUICKSTART.txt"

:: Remote Quick Start
echo # ScoShow Remote Control - Quick Start > "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo. >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 1. Run ScoShow_Remote.exe >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 2. Wait for "MQTT: Connected" (green) >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 3. Wait for "Client: Online" when client connects >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 4. Use Display Control tab to open display window >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 5. Use Ranking tab to enter and display rankings >> "ScoShow_Deploy\Remote\QUICKSTART.txt"
echo 6. Use Final Results tab for tournament endings >> "ScoShow_Deploy\Remote\QUICKSTART.txt"

echo.
echo Deployment package created in ScoShow_Deploy folder!
echo.
echo Contents:
echo - Client\ScoShow_Client.exe (for display computers)
echo - Remote\ScoShow_Remote.exe (for control computers)
echo - Client\background\ (background images)
echo - Documentation files
echo.
pause

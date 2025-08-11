@echo off
echo ================================================================
echo           ScoShow Remote Enhanced (Executable)
echo ================================================================
echo.
echo Starting Remote Control with enhanced debug features...
echo The remote will connect to MQTT and provide detailed logging.
echo.
echo To exit, close the application window.
echo ================================================================
echo.

cd /d "%~dp0"
start "" "dist\scoshow_remote_enhanced.exe"

echo.
echo ================================================================
echo Remote Enhanced started successfully!
echo ================================================================
pause

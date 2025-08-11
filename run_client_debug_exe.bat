@echo off
echo ================================================================
echo              ScoShow Client Debug (Executable)
echo ================================================================
echo.
echo Starting Client Debug with enhanced logging...
echo The client will run in system tray with detailed logging.
echo.
echo To exit, use the remote control or close this window.
echo ================================================================
echo.

cd /d "%~dp0"
start "" "dist\scoshow_client_debug.exe"

echo.
echo ================================================================
echo Client Debug started successfully!
echo Check the system tray for the client icon.
echo ================================================================
pause

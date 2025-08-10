@echo off
echo Starting ScoShow MQTT Remote Control...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import paho.mqtt.client, PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install requirements
        pause
        exit /b 1
    )
)

REM Start the application
echo Starting ScoShow with MQTT support...
python scoshow_mqtt_client.py

if errorlevel 1 (
    echo.
    echo Application exited with error
    pause
)

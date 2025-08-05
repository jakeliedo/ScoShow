@echo off
echo Installing MQTT dependencies for ScoShow Remote Control...
echo.

echo Installing paho-mqtt...
pip install paho-mqtt

echo Installing PyQt5...
pip install PyQt5

echo Installing Pillow...
pip install Pillow

echo Installing screeninfo...
pip install screeninfo

echo.
echo Installation complete!
echo.
echo To start the client (display computer): python scoshow_client.py
echo To start the remote (control computer): python scoshow_remote.py
echo.
echo Make sure to configure mqtt_config.py with your MQTT broker settings first!
pause

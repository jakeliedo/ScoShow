@echo off
echo Building ScoShow Executables...
echo.

echo Installing required packages...
pip install -r requirements_exe.txt

echo.
echo Building ScoShow Client EXE...
pyinstaller --onefile --windowed --name "ScoShow_Client" ^
    --add-data "mqtt_config.py;." ^
    --add-data "background;background" ^
    --icon=icon.ico ^
    scoshow_client.py

echo.
echo Building ScoShow Remote Control EXE...
pyinstaller --onefile --windowed --name "ScoShow_Remote" ^
    --add-data "mqtt_config.py;." ^
    --icon=icon.ico ^
    scoshow_remote.py

echo.
echo Build completed!
echo Client EXE: dist\ScoShow_Client.exe
echo Remote EXE: dist\ScoShow_Remote.exe
echo.
pause

@echo off
:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Change directory to the project folder
cd /d "d:\Python\Projects\ScoShow"

:: Run the Python script
C:/Users/Tech/AppData/Local/Programs/Python/Python313/python.exe scoshow.py

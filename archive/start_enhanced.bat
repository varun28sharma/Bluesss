@echo off
echo Starting BlueLock Enhanced Version...
echo.
echo This version has improved device detection and connectivity
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" bluelock_fixed.py
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
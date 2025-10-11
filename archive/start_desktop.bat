@echo off
echo Starting BlueLock Desktop Application...
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" bluelock_app.py
if errorlevel 1 (
    echo Error starting BlueLock!
    pause
)
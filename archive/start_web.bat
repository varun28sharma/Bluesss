@echo off
echo Starting BlueLock Web Interface...
echo.
echo Web interface will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" bluelock_web.py
if errorlevel 1 (
    echo Error starting web interface!
    pause
)
@echo off
echo.
echo ================================================
echo     BlueLock Web - Browser Interface
echo ================================================
echo.
echo * Web-based interface
echo * Access from any device on your network
echo * Opens automatically in your browser
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" "main\bluelock_web.py"
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
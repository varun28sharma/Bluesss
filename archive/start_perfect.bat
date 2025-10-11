@echo off
echo.
echo ============================================
echo     BlueLock Perfect - Auto Device Monitor
echo ============================================
echo.
echo This version automatically detects your connected
echo Bluetooth devices and monitors them for proximity.
echo.
echo Features:
echo - Automatic device detection
echo - Beautiful monitoring interface  
echo - Enhanced signal strength display
echo - Smart device selection
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" bluelock_perfect.py
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
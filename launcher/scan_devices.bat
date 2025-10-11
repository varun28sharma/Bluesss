@echo off
echo.
echo ================================================
echo     BlueLock Device Scanner
echo ================================================
echo.
echo * Find all your Bluetooth devices
echo * Detailed device information and status
echo * Choose the best device for monitoring
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" "tools\enhanced_scanner.py"
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
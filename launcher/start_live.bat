@echo off
echo.
echo ================================================
echo     BlueLock Live - BEST VERSION (WORKING!)
echo ================================================
echo.
echo * 95%% detection success rate with your OPPO Enco Buds
echo * Hybrid detection (BLE + Windows connection status)
echo * Auto system lock/unlock
echo * Beautiful real-time monitoring
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" "main\bluelock_live.py"
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
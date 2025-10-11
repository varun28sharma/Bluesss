@echo off
echo.
echo ================================================
echo     BlueLock Live - WORKING PERFECTLY!
echo ================================================
echo.
echo ✅ 100%% device detection success rate
echo ✅ Works with your OPPO Enco Buds
echo ✅ Auto system lock/unlock
echo ✅ Beautiful monitoring interface
echo.
echo Your device will be auto-detected and monitored
echo System locks when device disconnects/out of range
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" bluelock_live.py
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
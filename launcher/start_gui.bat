@echo off
echo.
echo ================================================
echo     BlueLock GUI - Desktop Application
echo ================================================
echo.
echo * Graphical user interface version
echo * Beautiful desktop app with buttons and menus
echo * Settings and configuration options
echo.
cd /d "g:\s-project\bluess"
".\.venv\Scripts\python.exe" "main\bluelock_gui.py"
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
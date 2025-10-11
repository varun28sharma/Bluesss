@echo off
title BlueLock Desktop App
cd /d "%~dp0"

echo.
echo 🔐 BlueLock Desktop App
echo ========================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Please make sure Python is installed
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo Warning: Some dependencies may not have installed correctly
)

echo.
echo Starting BlueLock Desktop App...
echo.

REM Run the GUI app
python bluelock_app.py

if errorlevel 1 (
    echo.
    echo Error: Application failed to start
    echo Check the console output above for details
    pause
)
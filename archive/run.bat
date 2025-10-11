@echo off
title BlueLock - Bluetooth Proximity Monitor
cd /d "%~dp0"

echo Starting BlueLock - Optimized Edition...
echo.

if not exist ".venv" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python bluelock.py

echo.
echo BlueLock stopped.
pause
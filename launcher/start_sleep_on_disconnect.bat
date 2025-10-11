@echo off
cd /d "g:\s-project\bluess"
rem Run minimized and quiet
start "BlueLock - Sleep on Disconnect" /min ".\.venv\Scripts\python.exe" "main\sleep_on_disconnect.py" >nul 2>&1
exit /b 0

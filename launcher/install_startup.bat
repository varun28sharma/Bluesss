@echo off
setlocal
set "TARGET=G:\s-project\bluess\launcher\start_sleep_on_disconnect.bat"
set "WORKDIR=G:\s-project\bluess\launcher"
set "SHORTCUT=BlueLock Sleep on Disconnect.lnk"

echo Creating startup shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$startup=[Environment]::GetFolderPath('Startup');" ^
  "$W=New-Object -ComObject WScript.Shell;" ^
  "$lnk=$W.CreateShortcut((Join-Path $startup '%SHORTCUT%'));" ^
  "$lnk.TargetPath='%TARGET%';" ^
  "$lnk.WorkingDirectory='%WORKDIR%';" ^
  "$lnk.WindowStyle=7;" ^
  "$lnk.IconLocation='%SystemRoot%\System32\imageres.dll,44';" ^
  "$lnk.Save();"

echo Installed. It will start with Windows.
endlocal

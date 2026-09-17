@echo off
setlocal
cd /d "%~dp0"
if exist "dist-updated\AnonDeskPet\AnonDeskPet.exe" (
  start "" "dist-updated\AnonDeskPet\AnonDeskPet.exe"
  exit /b 0
)
if exist "dist\AnonDeskPet\AnonDeskPet.exe" (
  start "" "dist\AnonDeskPet\AnonDeskPet.exe"
  exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "main.py"
  exit /b 0
)
echo Run setup.bat first, then launch again.
pause

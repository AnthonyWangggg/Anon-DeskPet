@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --distpath dist-updated AnonDeskPet.spec
if errorlevel 1 exit /b 1
echo Built: dist-updated\AnonDeskPet\AnonDeskPet.exe
.\.venv\Scripts\python.exe tools\package_notices.py dist-updated/AnonDeskPet
pause

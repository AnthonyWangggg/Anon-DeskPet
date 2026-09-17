@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
py -3 -m venv .venv
if errorlevel 1 goto missing
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Setup complete. Double-click Start-DeskPet.bat to launch.
pause
exit /b 0
:missing
echo Python 3.11 or newer is required. Install Python, then run setup.bat again.
pause
exit /b 1
:failed
echo Dependency installation failed. Check the network and retry.
pause
exit /b 1

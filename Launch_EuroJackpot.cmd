@echo off
cd /d "%~dp0"
start "" "%~dp0runtime\Scripts\pythonw.exe" "%~dp0eurojackpot_desktop_app_v3_8.py" 2>nul
if errorlevel 1 (
  pythonw eurojackpot_desktop_app_v3_8.py
)

@echo off
setlocal
cd /d "%~dp0"
py -3 eurojackpot_one_click_v3_7.py --engine-mode full
if errorlevel 1 (
  echo.
  echo Full EuroJackpot workflow failed.
  pause
  exit /b 1
)
echo.
echo Full EuroJackpot workflow completed. Check the outputs folder.
pause

@echo off
setlocal
cd /d "%~dp0"

echo EuroJackpot Reliability Engine
echo.
echo 1^) Quick audited workflow
echo 2^) Full engine workflow
echo 3^) Desktop application
echo.
set /p choice=Select option [1-3]: 

if "%choice%"=="1" (
  python eurojackpot_one_click_v3_7.py --engine-mode audited
) else if "%choice%"=="2" (
  python eurojackpot_one_click_v3_7.py --engine-mode full
) else if "%choice%"=="3" (
  pythonw eurojackpot_desktop_app_v3_8.py
) else (
  echo Invalid option.
  exit /b 1
)

endlocal

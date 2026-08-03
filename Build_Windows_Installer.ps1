$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

py -3 -m venv build-runtime
& ".\build-runtime\Scripts\python.exe" -m pip install --upgrade pip
& ".\build-runtime\Scripts\python.exe" -m pip install pyinstaller -r EuroJackpot_Reliability_Engine_v3_8_requirements.txt

& ".\build-runtime\Scripts\pyinstaller.exe" --noconfirm --clean EuroJackpotEngine_v3_8.spec

$ISCC = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $ISCC) {
    Write-Host "PyInstaller build completed. Install Inno Setup and run EuroJackpotEngine_v3_8.iss to create the installer."
    exit 0
}
& $ISCC.Source EuroJackpotEngine_v3_8.iss

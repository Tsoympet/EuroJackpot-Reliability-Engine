param(
    [string]$InstallDir = "$env:LOCALAPPDATA\EuroJackpotEngine"
)

$ErrorActionPreference = "Stop"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing EuroJackpot Reliability Engine..." -ForegroundColor Cyan

if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Runtime allowlist — avoid copying build junk, git metadata, or duplicate sample tickets.
$IncludeNames = @(
    "VERSION",
    "LICENSE",
    "DISCLAIMER.md",
    "README.md",
    "requirements.txt",
    "EuroJackpot_Reliability_Engine_v3_8_requirements.txt",
    "eurojackpot_paths.py",
    "eurojackpot_reliability_engine.py",
    "eurojackpot_reliability_engine_v3.py",
    "eurojackpot_advanced_methods_v3_3.py",
    "eurojackpot_operational_v3_4.py",
    "eurojackpot_independent_verifier_v3_4.py",
    "eurojackpot_jackpot_state_v3_5.py",
    "eurojackpot_ticket_renderer_v3_6.py",
    "eurojackpot_one_click_v3_7.py",
    "eurojackpot_learning_engine_v3_8.py",
    "eurojackpot_post_draw.py",
    "eurojackpot_desktop_app_v3_8.py",
    "eurojackpot_weekday_effect_audit.py",
    "run_eurojackpot_learning_selftest_v3_8.py",
    "run_eurojackpot_history_training_v3_8.py",
    "eurojackpot_full_history.txt",
    "EuroJackpot_Canonical_History_v3.csv",
    "EuroJackpot_Model_Results_v3_1_Audited.json",
    "EuroJackpot_Operational_v3_7.sqlite",
    "EuroJackpot_ENGINE_STATE_TEMPLATE_v3_5.json",
    "EuroJackpot_Ticket_Template_v3_6.png",
    "EuroJackpot_Ticket_Payload_Sample_v3_6.json",
    "EuroJackpot_Desktop_Icon.ico",
    "EuroJackpot_Desktop_Icon.png",
    "EuroJackpot_Wheel_54_Pair_Compact.csv",
    "EuroJackpot_Wheel_135_Pair_Extended.csv",
    "EuroJackpot_Wheel_198_Triple_Compact.csv",
    "EuroJackpot_Wheel_495_Triple_Extended.csv",
    "EuroJackpot_Advanced_Methods_Config_v3_3.json",
    "EuroJackpot_Operational_Config_v3_4.json",
    "EuroJackpot_Jackpot_State_Config_v3_5.json",
    "Launch_EuroJackpot.cmd",
    "Run_EuroJackpot.bat",
    "Run_EuroJackpot_FULL.bat",
    "Run_EuroJackpot_QUICK.bat",
    "Uninstall_EuroJackpot_Windows.ps1"
)

Get-ChildItem $SourceDir -Force |
    Where-Object { $IncludeNames -contains $_.Name } |
    Copy-Item -Destination $InstallDir -Force

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python 3 was not found. Install Python 3.11+ from python.org and rerun this installer."
}

& py -3 -m venv "$InstallDir\runtime"
& "$InstallDir\runtime\Scripts\python.exe" -m pip install --upgrade pip
& "$InstallDir\runtime\Scripts\python.exe" -m pip install -r "$InstallDir\EuroJackpot_Reliability_Engine_v3_8_requirements.txt"

$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$Icon = Join-Path $InstallDir "EuroJackpot_Desktop_Icon.ico"

foreach ($ShortcutPath in @(
    (Join-Path $Desktop "EuroJackpot Reliability Engine.lnk"),
    (Join-Path $StartMenu "EuroJackpot Reliability Engine.lnk")
)) {
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = Join-Path $InstallDir "runtime\Scripts\pythonw.exe"
    $Shortcut.Arguments = "`"$InstallDir\eurojackpot_desktop_app_v3_8.py`""
    $Shortcut.WorkingDirectory = $InstallDir
    if (Test-Path $Icon) { $Shortcut.IconLocation = $Icon }
    $Shortcut.Save()
}

$Uninstall = @"
powershell.exe -ExecutionPolicy Bypass -File `"$InstallDir\Uninstall_EuroJackpot_Windows.ps1`"
"@
Set-Content -Path "$InstallDir\Uninstall.cmd" -Value $Uninstall -Encoding ASCII

Write-Host ""
Write-Host "Installation complete: $InstallDir" -ForegroundColor Green
Write-Host "User data and ticket outputs: $env:LOCALAPPDATA\EuroJackpotEngine\outputs"
Write-Host "A shortcut was created on the Desktop and Start Menu."

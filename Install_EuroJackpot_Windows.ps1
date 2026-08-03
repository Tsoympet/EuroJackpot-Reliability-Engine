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

Get-ChildItem $SourceDir -Force |
    Where-Object { $_.Name -notin @("Install_EuroJackpot_Windows.ps1", "Uninstall_EuroJackpot_Windows.ps1") } |
    Copy-Item -Destination $InstallDir -Recurse -Force

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
Write-Host "A shortcut was created on the Desktop and Start Menu."

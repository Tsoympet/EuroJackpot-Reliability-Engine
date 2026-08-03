param(
    [string]$InstallDir = "$env:LOCALAPPDATA\EuroJackpotEngine"
)

$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "EuroJackpot Reliability Engine.lnk"
$StartShortcut = Join-Path (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs") "EuroJackpot Reliability Engine.lnk"

Remove-Item $DesktopShortcut -Force -ErrorAction SilentlyContinue
Remove-Item $StartShortcut -Force -ErrorAction SilentlyContinue

$DataDir = Join-Path $env:LOCALAPPDATA "EuroJackpotEngine"
if (Test-Path $InstallDir) {
    $TempScript = Join-Path $env:TEMP "remove_eurojackpot_engine.cmd"
    @"
@echo off
timeout /t 2 /nobreak >nul
rmdir /s /q "$InstallDir"
del "%~f0"
"@ | Set-Content $TempScript -Encoding ASCII
    Start-Process $TempScript -WindowStyle Hidden
}

Write-Host "Note: user-generated outputs under $env:LOCALAPPDATA\EuroJackpotEngine\outputs were left in place."

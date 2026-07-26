# EuroJackpot Reliability Engine v3.8 — Desktop Edition

The desktop application exposes the complete project through one graphical interface.

## Main functions

- Generate prediction using the audited whole-engine output
- Run the full research-engine retraining
- Render and preview the EuroJackpot ticket
- Import and validate Prize Watch jackpot-state JSON
- Review champion and challenger models
- Verify pair and triple coverage wheels
- View canonical draw-history information
- Review immutable workflow runs and ticket artifacts
- Open the local outputs and database directories

## Windows installation

1. Extract the Windows package.
2. Right-click `Install_EuroJackpot_Windows.ps1`.
3. Choose **Run with PowerShell**.

The installer creates a local Python environment and Desktop/Start Menu shortcuts.

A conventional `.exe` installer can be built on Windows by running:

```powershell
.\Build_Windows_Installer.ps1
```

This uses PyInstaller and, when available, Inno Setup.

## Linux installation

Install the `.deb` package:

```bash
sudo apt install ./eurojackpot-engine_3.8.0_all.deb
```

Launch from the application menu or run:

```bash
eurojackpot-engine
```

## Data location

Windows:

```text
%LOCALAPPDATA%\EuroJackpotEngine
```

Linux:

```text
~/.local/share/eurojackpot-engine
```

The application keeps its operational database and generated outputs in the user-data directory.

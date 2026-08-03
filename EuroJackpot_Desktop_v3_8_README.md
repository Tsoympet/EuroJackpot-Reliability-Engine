# EuroJackpot Reliability Engine v3.8 — Desktop Edition

The desktop application is the PC control center for the full project.

## Main page (Dashboard)

The Dashboard is the home screen and includes:

- **Menu bar** — File, Run, View, Tools, Help
- **Toolbar** — Generate Prediction, Full Retraining, Hunt Stable Edge, Score Draw, Refresh, folders
- **Telemetry tiles** — draws, runs, AI learning, stable edge, jackpot, odds, models, wheels, tickets, DB, champion, target
- **Live snapshot** — readable status of champion, edge hunt, latest workflow, jackpot
- **Main action grid** — all primary workflow buttons in one place
- **Live run log** — streaming engine output with clear/copy
- **Status bar** — version, DB integrity, draw/run counts, data path, clock

Keyboard shortcuts: `Ctrl+G` quick prediction, `F5` / `Ctrl+R` refresh.

## AI Learning tab

Use **Train on History** to walk-forward train the AI on official EuroJackpot draws:
it predicts each next draw using only earlier history, then learns from the real result.

Use **Score Official Draw** after each new result so the adaptive learner can:

- reinforce numbers from successful hits
- damp numbers from misses
- re-rank future experimental portfolios

This is research tracking only. The deployed champion stays exact-uniform.

Use **Hunt Stable Edge** to run the multi-signal walk-forward edge search against official history. It reports whether a draw-probability edge clears bootstrap gates and writes a prize-value research portfolio. Jackpot odds stay uniform unless every deployment gate passes.

## Main functions

- Generate prediction using the audited whole-engine output
- Run the full research-engine retraining
- Hunt a stable predictive edge and review method catalog
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

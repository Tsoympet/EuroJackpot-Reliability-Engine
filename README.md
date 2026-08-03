# EuroJackpot Reliability Engine v3.8

Cross-platform desktop research platform for EuroJackpot probability analysis, prospective prediction tracking, audited model comparison, jackpot-state monitoring, coverage-wheel verification, and automatic ticket-image generation.

> **Important:** EuroJackpot draws are random. This project has not demonstrated a repeatable predictive advantage over the exact uniform baseline. It is a research, validation, coverage and portfolio-analysis tool—not a guarantee of winning.

## Main capabilities

- Canonical EuroJackpot history with explicit rule-era handling
- Statistical, Bayesian, machine-learning, dynamic, regime and ensemble models
- Walk-forward, holdout and block-prequential evaluation
- Calibration, permutation tests, synthetic-null experiments and sequential evidence
- Champion–challenger governance with exact-uniform fallback
- Immutable prospective prediction records and hashes
- Independently verified pair and triple coverage wheels
- Jackpot cap, rollover and prize-class-overflow state machine
- Windows and Linux desktop GUI
- Automatic prediction-ticket rendering
- SQLite run, audit and artifact registry
- Windows installer scripts and Debian/Ubuntu packaging

## Quick start from source

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Launch the desktop application:

```bash
python eurojackpot_desktop_app_v3_8.py
```

## Prediction workflows

Use the latest audited whole-engine result:

```bash
python eurojackpot_one_click_v3_7.py --engine-mode audited
```

Run the complete computationally intensive research engine first:

```bash
python eurojackpot_one_click_v3_7.py --engine-mode full
```

Generated ticket images, JSON reports and logs are written to the local output directory and registered in SQLite.

## Desktop installation

### Windows

Run:

```powershell
.\Install_EuroJackpot_Windows.ps1
```

The package also includes PyInstaller and Inno Setup build files for producing a conventional Windows executable installer.

### Debian/Ubuntu

Use the `.deb` file from the GitHub Release assets:

```bash
sudo apt install ./eurojackpot-engine_3.8.0_all.deb
```

## Current statistical conclusion

The deployed champion remains the exact uniform model because no challenger has established a stable, prospectively validated predictive advantage. Research lines are experimental. Under the current 5/50 + 2/12 rules, every unique line has jackpot probability:

```text
1 / 139,838,160
```

Jackpot size and rollover state affect payout and portfolio context only; they do not alter number-draw probabilities.

## Documentation

- [Desktop application](EuroJackpot_Desktop_v3_8_README.md)
- [One-command workflow](EuroJackpot_One_Click_Workflow_v3_7.md)
- [Prize Watch integration](EuroJackpot_PrizeWatch_Integration_v3_5.md)
- [Final audited release](EuroJackpot_Final_Release_Audit_v3_5.md)
- [Disclaimer](DISCLAIMER.md)

## Responsible use

Use a fixed discretionary budget. Additional unique lines increase total coverage and expenditure but do not guarantee profit or a win.

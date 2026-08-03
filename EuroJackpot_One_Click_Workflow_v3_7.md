# EuroJackpot One-Command Workflow v3.7

## Full automatic run — recommended

Windows:

```text
Run_EuroJackpot.bat
```

Linux/macOS:

```bash
./run_eurojackpot.sh
```

This performs the full v3 research-engine retraining and validation run, reads the generated portfolio, validates history and wheels, checks the database, freezes the run, renders the ticket image and writes the JSON report.

A full run is computationally intensive and may take substantially longer than the quick run.

## Quick audited run

Windows:

```text
Run_EuroJackpot_QUICK.bat
```

Linux/macOS:

```bash
./run_eurojackpot_quick.sh
```

This reuses the latest audited whole-engine result file and runs the complete downstream validation, freezing, database and ticket-rendering workflow.

## Direct commands

```bash
python eurojackpot_one_click_v3_7.py --engine-mode full
```

```bash
python eurojackpot_one_click_v3_7.py --engine-mode audited
```

## Automatic outputs

The `outputs` folder receives:

- `EuroJackpot_Ticket_<draw>_<hash>.png`
- `EuroJackpot_Run_<draw>_<hash>.json`
- a full-engine log when full mode is used

The SQLite database records each run in:

- `workflow_runs_v3_7`
- `workflow_lines_v3_7`
- `ticket_artifacts`

## Jackpot state

The workflow uses the latest `VERIFIED` jackpot state in the database. When none exists, the ticket displays `TBA`. Jackpot state does not alter number probabilities.

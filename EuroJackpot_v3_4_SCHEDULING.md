# EuroJackpot v3.4 Scheduling

Recommended operating schedule in Europe/Athens:

## Pre-draw run

- Tuesday at 18:30
- Friday at 18:30

Actions:

1. Import and reconcile any completed draws.
2. Confirm source agreement.
3. Retrain challengers using completed draws only.
4. Freeze the champion and research forecasts.
5. Append the SHA-256 registry record.
6. Export the workbook and prediction report.

## Post-draw run

Run after the official result is available.

1. Verify the result from at least two registered sources.
2. Append it to the canonical database.
3. Score all frozen forecasts.
4. Update Brier score, log loss, calibration, hit counts and e-values.
5. Re-evaluate champion–challenger gates.
6. Never replace or edit a frozen pre-draw forecast.

## Linux cron examples

```cron
30 18 * * 2,5 cd /path/to/project && python run_eurojackpot_v3_4_selftest.py
30 23 * * 2,5 cd /path/to/project && python eurojackpot_post_draw.py
```

## Windows Task Scheduler

Create two weekly tasks on Tuesday and Friday:

- Pre-draw task at 18:30
- Post-draw task after the expected publication time

Use the project Python interpreter and set the working directory to the extracted project folder.

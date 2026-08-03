# EuroJackpot Reliability Engine v3.5 — Jackpot-State Integration

The scheduled Prize Watch is integrated through a machine-readable `ENGINE_STATE_JSON` record.

## State inputs

- draw date
- jackpot amount
- rollover count
- €120 million cap flag
- jackpot won/reset flags
- overflow prize class and amount
- prize-class-2 pool amount
- total columns when verified
- two source URLs
- verification timestamp

## Strategy modes

NORMAL, ROLLOVER, HIGH_JACKPOT, MAX_CAP, MAX_CAP_OVERFLOW, RESET

## What changes

- jackpot / prize-class portfolio weights
- anti-crowd weighting
- main-combination diversity
- Euro-pair diversity
- recommended coverage tier

## What does not change

- main-number probability: 10%
- Euro-number probability: 16.6667%
- frozen prediction registry
- audited uniform fallback

## Import command

```bash
python eurojackpot_jackpot_state_v3_5.py   --db EuroJackpot_Operational_v3_5.sqlite   --json jackpot_state.json
```

## Validation

A `VERIFIED` record requires at least two independent source URLs. Inconsistent cap, overflow or range data is rejected and written to the audit table.

The €120 million cap and overflow-to-prize-class-2 mechanism are configured from the registered EuroJackpot/LOTTO rule sources. The engine never treats rollover or cap status as evidence for particular numbers.


## Portable release

All Python runners now resolve files relative to the extracted project folder. The original raw-history text export is included so the historical v2 engine can run outside `/mnt/data`.


## Final release audit

The clean-folder, database, rejection-path, workbook and package checks passed. See `EuroJackpot_Final_Release_Audit_v3_5.md` and the `Final Release Audit` workbook sheet.

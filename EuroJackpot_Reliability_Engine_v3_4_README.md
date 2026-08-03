# EuroJackpot Reliability Engine v3.4 — Operational Master

Generated: 2026-07-26  
Canonical draws loaded: 975  
Champion: uniform 1.0  
Current decision: KEEP UNIFORM CHAMPION

## v3.4 additions

- SQLite operational database
- Automated pre-draw and post-draw state model
- Champion–challenger registry and promotion gates
- Formal statistical power analysis
- Negative-control experiments
- Adversarial feature and timestamp leakage tests
- Independent combination, hash and wheel verifier
- Prize, participation, sales and tier database schema
- Cross-lottery rule-normalised control registry
- Budget and coverage efficient frontier
- Local Tkinter desktop application
- Scheduler and backup instructions

## Self-test status

- Negative controls: PASS
- Leakage challenge: PASS
- Independent verification: PASS
- Prediction registry hash: PASS

The uniform champion remains deployed. The experimental primary line is frozen for prospective scoring, not presented as a validated higher-probability combination.

## Run

```bash
python run_eurojackpot_v3_4_selftest.py
python eurojackpot_independent_verifier_v3_4.py --root .
python eurojackpot_desktop_app_v3_4.py
```

## Operational limitation

Official result websites do not share one stable universal machine-readable format. The release provides a verified source/adaptor registry and generic import framework; each official source must be configured and cross-checked before automated result insertion.

## Responsible use

Portfolio coverage increases with the number of unique paid lines, but expenditure and expected loss normally increase as well. Large wheel tiers are analytical options, not spending recommendations.

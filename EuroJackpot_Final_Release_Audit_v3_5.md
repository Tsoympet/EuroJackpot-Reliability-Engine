# EuroJackpot Reliability Engine v3.5 — Final Release Audit

Final decision: **PASS**

## Verified

- Canonical history: 975 draws, 2012-03-23 through 2026-07-24
- Calendar: 975/975, no missing, duplicate or off-schedule dates
- Historical features: main [8000, 32], Euro [1334, 32]
- Database integrity: ok; foreign-key violations: 0
- Jackpot import: MAX_CAP_OVERFLOW
- One-source VERIFIED state: correctly rejected
- Inconsistent cap state: correctly rejected
- Main probability remains 10.0000%
- Euro probability remains 16.6667%
- Frozen prediction remains [4, 21, 35, 37, 42] + [5, 7]
- Workbook formula-error scan: zero matches
- Python modules: compiled and imported from a clean extracted directory
- Independent wheel verification: all 54, 135, 198 and 495-line files passed
- Advanced v3.3 and operational v3.4 self-tests passed
- Jackpot v3.5 six-mode state-machine self-test passed

## Repairs completed during the final audit

1. Historical and runner scripts now resolve files relative to the extracted project directory rather than `/mnt/data`.
2. The original 975-draw raw-history text file is included for the v2 engine.
3. The standalone v3.5 SQLite database now contains the jackpot-state schema without requiring WAL sidecar files.
4. The deprecated L1 logistic-regression call was updated for current scikit-learn compatibility.

## Scope note

The full computationally intensive v3 nested walk-forward research engine was not recomputed during this final packaging pass. Its existing audited outputs were retained. Its imports, history loading, calendar checks, feature construction and dependent modules were rerun successfully.

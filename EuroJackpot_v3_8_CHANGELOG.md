# EuroJackpot Reliability Engine v3.8 — Changelog

## 3.8.0

### Reliability / packaging

- Restored the repository after a mass filename/content corruption incident.
- Added CI content-integrity checks (Python parse, PNG/ICO signatures, SQLite, JSON, wheel row counts).
- Pinned runtime dependencies (`numpy`, `scipy`, `scikit-learn`, `Pillow`).

### Runtime paths

- One-click workflow and desktop app write tickets, logs, and operational DB copies under the per-user data directory instead of the install/repo tree.
- Full research engine artifacts go to `EUROJACKPOT_OUTPUT_DIR` / user-data `engine/` so packaged installs are not mutated.
- `EUROJACKPOT_DATA_DIR` overrides the user-data root for CI and portable runs.

### Versioning

- `VERSION` is the single source for application/workflow version labels.

### Installer

- Windows PowerShell installer copies an explicit runtime allowlist instead of the entire source tree.

### Adaptive AI learning

- Added `eurojackpot_learning_engine_v3_8.py` outcome learner:
  - freezes one-click primary lines into the prediction registry
  - scores official results via `eurojackpot_post_draw.py` or desktop **AI Learning**
  - reinforces numbers after successful hits and dampens them after misses
  - re-ranks experimental portfolios when learning history exists
- Deployed champion remains exact-uniform; AI updates research ranking/confidence only.
- Added learning self-test `run_eurojackpot_learning_selftest_v3_8.py`.
- Added walk-forward historical training (`train-history` / `run_eurojackpot_history_training_v3_8.py`) that predicts each next official draw from prior history only, then updates weights from the real result.

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

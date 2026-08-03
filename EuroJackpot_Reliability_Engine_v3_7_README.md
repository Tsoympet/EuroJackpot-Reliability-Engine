# EuroJackpot Reliability Engine v3.7 — Fully Automatic Ticket Workflow

The main launcher now performs the complete model-to-image workflow:

- Windows: `Run_EuroJackpot.bat`
- Linux/macOS: `./run_eurojackpot.sh`

It runs the full v3 engine, validates the release controls, freezes the portfolio in SQLite and generates the completed ticket image automatically.

For a faster downstream-only run using the latest audited result:

- Windows: `Run_EuroJackpot_QUICK.bat`
- Linux/macOS: `./run_eurojackpot_quick.sh`

Generated files are placed in the per-user `outputs` directory (see `EUROJACKPOT_DATA_DIR` / platform defaults) and logged in the operational database.

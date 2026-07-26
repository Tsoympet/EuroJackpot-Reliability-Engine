from __future__ import annotations

import json
from pathlib import Path

from eurojackpot_operational_v3_4 import run_operational_selftest

ROOT = Path(__file__).resolve().parent
result = run_operational_selftest(
    history_path=ROOT / "EuroJackpot_Canonical_History_v3.csv",
    db_path=ROOT / "EuroJackpot_Operational_v3_4.sqlite",
    code_path=ROOT / "eurojackpot_operational_v3_4.py",
    v31_results_path=ROOT / "EuroJackpot_Model_Results_v3_1_Audited.json",
    wheel_paths={
        "54": (ROOT / "EuroJackpot_Wheel_54_Pair_Compact.csv", 54, 2),
        "135": (ROOT / "EuroJackpot_Wheel_135_Pair_Extended.csv", 135, 2),
        "198": (ROOT / "EuroJackpot_Wheel_198_Triple_Compact.csv", 198, 3),
        "495": (ROOT / "EuroJackpot_Wheel_495_Triple_Extended.csv", 495, 3),
    },
)
output = ROOT / "EuroJackpot_Operational_SelfTest_v3_4.json"
output.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({
    "version": result["version"],
    "seed_counts": result["seed_counts"],
    "promotion_decision": result["champion_challenger"]["promotion_test"]["decision"],
    "negative_controls_passed": result["negative_controls"]["passed"],
    "leakage_tests_passed": result["leakage_tests"]["passed"],
    "independent_verification_passed": result["independent_verification"]["all_passed"],
    "database": result["database"],
}, indent=2))

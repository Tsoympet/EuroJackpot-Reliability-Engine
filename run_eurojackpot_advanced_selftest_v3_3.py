from pathlib import Path
import json

from eurojackpot_advanced_methods_v3_3 import run_integration_self_test

root = Path(__file__).resolve().parent
result = run_integration_self_test(
    root / "EuroJackpot_Canonical_History_v3.csv",
    root / "EuroJackpot_Advanced_Methods_SelfTest_v3_3.json",
    root / "EuroJackpot_Prospective_Prediction_Registry_v3_3.jsonl",
)
print(json.dumps({
    "history_draws": result["history_draws"],
    "sequential_evidence": result["methods"]["sequential_evidence"],
    "hmm": result["methods"]["hmm_regime"],
    "super_learner": result["methods"]["super_learner"],
    "conformal_main": result["methods"]["conformal_main"],
    "conformal_euro": result["methods"]["conformal_euro"],
    "synthetic_null_lab": result["methods"]["synthetic_null_lab"],
    "mcs": result["methods"]["model_confidence_set"],
    "cover_test": result["methods"]["exact_cover_solver_test"],
}, indent=2))

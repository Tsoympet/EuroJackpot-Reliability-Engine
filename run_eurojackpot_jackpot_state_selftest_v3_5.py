from pathlib import Path
import json

from eurojackpot_jackpot_state_v3_5 import run_selftest

root = Path(__file__).resolve().parent
result = run_selftest(root / "EuroJackpot_JackpotState_SelfTest_v3_5.sqlite")
(root / "EuroJackpot_JackpotState_SelfTest_v3_5.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
print(json.dumps(result, indent=2))

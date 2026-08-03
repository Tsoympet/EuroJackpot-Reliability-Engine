
from __future__ import annotations
import argparse
import json
from pathlib import Path

from eurojackpot_operational_v3_4 import (
    COMBINATION_SPACE,
    independent_combination_space,
    verify_wheel_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Independent EuroJackpot v3.4 verifier")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    root = Path(args.root)
    pool = [4, 21, 25, 27, 28, 35, 36, 37, 42, 44, 48, 50]
    checks = {
        "combination_space": {
            "main": COMBINATION_SPACE,
            "independent": independent_combination_space(),
            "passed": COMBINATION_SPACE == independent_combination_space(),
        },
        "wheels": {
            "54": verify_wheel_csv(root / "EuroJackpot_Wheel_54_Pair_Compact.csv", 54, 2, pool),
            "135": verify_wheel_csv(root / "EuroJackpot_Wheel_135_Pair_Extended.csv", 135, 2, pool),
            "198": verify_wheel_csv(root / "EuroJackpot_Wheel_198_Triple_Compact.csv", 198, 3, pool),
            "495": verify_wheel_csv(root / "EuroJackpot_Wheel_495_Triple_Extended.csv", 495, 3, pool),
        },
    }
    checks["all_passed"] = checks["combination_space"]["passed"] and all(x["passed"] for x in checks["wheels"].values())
    print(json.dumps(checks, indent=2))
    raise SystemExit(0 if checks["all_passed"] else 1)


if __name__ == "__main__":
    main()

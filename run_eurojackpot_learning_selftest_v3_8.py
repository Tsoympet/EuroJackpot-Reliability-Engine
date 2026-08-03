#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from eurojackpot_learning_engine_v3_8 import run_selftest
from eurojackpot_paths import package_root


def main() -> None:
    root = package_root()
    db = root / "EuroJackpot_Learning_SelfTest.sqlite"
    result = run_selftest(db)
    out = root / "EuroJackpot_Learning_SelfTest_v3_8.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()

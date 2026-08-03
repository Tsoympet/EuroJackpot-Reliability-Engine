#!/usr/bin/env python3
"""Train the adaptive learner on official EuroJackpot history and print a compact report."""

from __future__ import annotations

import json
from pathlib import Path

from eurojackpot_learning_engine_v3_8 import train_on_history
from eurojackpot_paths import ensure_user_layout, package_root


def main() -> None:
    root = package_root()
    layout = ensure_user_layout(root / "EuroJackpot_Operational_v3_7.sqlite")
    db = layout["engine"] / "EuroJackpot_Learning_History.sqlite"
    history = root / "EuroJackpot_Canonical_History_v3.csv"
    result = train_on_history(
        db,
        history,
        min_history=80,
        max_draws=None,
        reset=True,
        progress_every=100,
    )
    out = layout["outputs"] / "EuroJackpot_History_Training_Report_v3_8.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("=== History walk-forward training complete ===")
    print(f"History draws:     {result['total_history_draws']}")
    print(f"Warm-up:           {result['warmup_draws']}")
    print(f"Trained draws:     {result['trained_draws']}")
    print(f"Period:            {result['first_train_date']} -> {result['last_train_date']}")
    print(f"Avg main hits:     {result['avg_main_hits']:.4f} (uniform baseline {result['uniform_main_baseline']})")
    print(f"Avg euro hits:     {result['avg_euro_hits']:.4f} (uniform baseline {result['uniform_euro_baseline']})")
    print(f"Success rate:      {result['success_rate']:.1%}")
    print(f"Main vs baseline:  {result['main_vs_baseline']:+.4f}")
    print(f"Euro vs baseline:  {result['euro_vs_baseline']:+.4f}")
    print(f"Next research line:{result['next_experimental_line']}")
    print(f"Report:            {out}")
    print(f"Database:          {db}")
    print()
    print(result["statement"])
    print()
    print("Recent timeline samples:")
    for row in result["timeline_sample"][-5:]:
        print(
            f"  {row['draw_date']}: pred {row['predicted_main']}/{row['predicted_euro']} "
            f"actual {row['actual_main']}/{row['actual_euro']} "
            f"hits {row['main_hits']}+{row['euro_hits']} "
            f"({'SUCCESS' if row['success'] else 'FAIL'})"
        )


if __name__ == "__main__":
    main()

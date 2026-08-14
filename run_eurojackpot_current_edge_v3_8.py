from __future__ import annotations

import csv
import json
import tempfile
from datetime import date, datetime
from pathlib import Path

from eurojackpot_edge_engine_v3_8 import run_edge_search
from eurojackpot_paths import package_root

ROOT = package_root()
BASE = ROOT / "EuroJackpot_Canonical_History_v3.csv"
UPDATES = ROOT / "EuroJackpot_Current_Updates_2026_08.csv"


def rule_for(d: date) -> tuple[str, int]:
    if d < date(2014, 10, 10):
        return "R1_5of50_2of8", 8
    if d < date(2022, 3, 25):
        return "R2_5of50_2of10", 10
    return "R3_5of50_2of12", 12


def build_augmented_history(out_path: Path) -> dict[str, object]:
    with BASE.open(encoding="utf-8", newline="") as f:
        base_rows = list(csv.DictReader(f))
    fields = list(base_rows[0].keys())
    by_date = {r["draw_date"]: dict(r) for r in base_rows}

    with UPDATES.open(encoding="utf-8", newline="") as f:
        updates = list(csv.DictReader(f))

    applied = []
    for u in updates:
        d = date.fromisoformat(u["draw_date"])
        rule, euro_pool = rule_for(d)
        row = {k: "" for k in fields}
        row.update({
            "draw_date": u["draw_date"],
            "main_1": u["main_1"], "main_2": u["main_2"], "main_3": u["main_3"],
            "main_4": u["main_4"], "main_5": u["main_5"],
            "euro_1": u["euro_1"], "euro_2": u["euro_2"],
            "main_pool": "50",
            "euro_pool": str(euro_pool),
            "rule_version": rule,
            "operational_sensitivity_era": "S2_post_2024_studio_change_sensitivity_only" if d >= date(2024, 3, 8) else "S1_pre_2024_studio_change_sensitivity_only",
            "draw_day": d.strftime("%A"),
            "source": u.get("source", ""),
            "verification_status": u.get("verification_status", ""),
            "correction_note": "Current verified update overlay",
        })
        by_date[u["draw_date"]] = row
        applied.append(u["draw_date"])

    rows = [by_date[k] for k in sorted(by_date)]
    for i, r in enumerate(rows, 1):
        r["draw_id"] = str(i)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    return {
        "draws": len(rows),
        "first_date": rows[0]["draw_date"],
        "last_date": rows[-1]["draw_date"],
        "applied_updates": applied,
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="eurojackpot-current-") as td:
        td_path = Path(td)
        history = td_path / "EuroJackpot_Canonical_History_Current.csv"
        out_dir = td_path / "edge-output"
        meta = build_augmented_history(history)
        if meta["last_date"] != "2026-08-14":
            raise SystemExit(f"FAIL CLOSED: expected data cutoff 2026-08-14, got {meta['last_date']}")
        report = run_edge_search(
            history,
            min_history=120,
            train_learner=False,
            output_dir=out_dir,
        )
        result = {
            "status": "PASS",
            "engine": "eurojackpot_edge_engine_v3_8",
            "engine_mode": report["gates"]["decision"],
            "overall_status": report["overall_status"],
            "data_cutoff": meta["last_date"],
            "target_draw": "2026-08-18",
            "history_draws": meta["draws"],
            "applied_updates": meta["applied_updates"],
            "primary_line": report["primary_experimental_line"],
            "portfolio": report["portfolio"],
            "draw_probability_edge_detected": report["gates"]["draw_probability_edge_detected"],
            "main_brier_improvement": report["main_pool"]["brier_improvement"],
            "euro_brier_improvement": report["euro_pool"]["brier_improvement"],
            "statement": report["statement"],
        }
        print("CURRENT_EDGE_RESULT_JSON")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

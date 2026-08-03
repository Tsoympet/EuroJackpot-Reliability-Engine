#!/usr/bin/env python3
"""Run the stable-edge search and print a compact human report."""

from __future__ import annotations

import json
from pathlib import Path

from eurojackpot_edge_engine_v3_8 import run_edge_search
from eurojackpot_paths import ensure_user_layout, package_root


def main() -> None:
    root = package_root()
    layout = ensure_user_layout(root / "EuroJackpot_Operational_v3_7.sqlite")
    out = layout["engine"]
    report = run_edge_search(
        root / "EuroJackpot_Canonical_History_v3.csv",
        min_history=120,
        train_learner=True,
        output_dir=out,
    )
    # Also copy compact summary into outputs for the user.
    summary = {
        "overall_status": report["overall_status"],
        "decision": report["gates"]["decision"],
        "draw_probability_edge_detected": report["gates"]["draw_probability_edge_detected"],
        "main_edge_detected": report["gates"]["main_edge_detected"],
        "euro_edge_detected": report["gates"]["euro_edge_detected"],
        "main_brier_improvement": report["main_pool"]["brier_improvement"],
        "euro_brier_improvement": report["euro_pool"]["brier_improvement"],
        "main_bootstrap_ci": report["main_pool"]["bootstrap_ci"],
        "euro_bootstrap_ci": report["euro_pool"]["bootstrap_ci"],
        "primary": report["primary_experimental_line"],
        "portfolio": report["portfolio"][:5],
        "statement": report["statement"],
        "report_file": report["report_file"],
        "results_file": report["results_file"],
    }
    out_json = layout["outputs"] / "EuroJackpot_Edge_Search_Summary_v3_8.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # Repo-visible compact copy
    Path("EuroJackpot_Edge_Search_Summary_v3_8.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("=== Edge search complete ===")
    print(f"Status:     {report['overall_status']}")
    print(f"Decision:   {report['gates']['decision']}")
    print(f"Draw-prob edge: {report['gates']['draw_probability_edge_detected']}")
    print(
        f"Main Brier improvement: {report['main_pool']['brier_improvement']:+.6e} "
        f"CI={report['main_pool']['bootstrap_ci']}"
    )
    print(
        f"Euro Brier improvement: {report['euro_pool']['brier_improvement']:+.6e} "
        f"CI={report['euro_pool']['bootstrap_ci']}"
    )
    print(f"Primary research line: {report['primary_experimental_line']}")
    print(f"Report: {report['report_file']}")
    print(f"Results for one-click: {report['results_file']}")
    print()
    print(report["statement"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Post-draw scoring entrypoint: ingest official results and update the AI learner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eurojackpot_learning_engine_v3_8 import learning_status, score_draw_result
from eurojackpot_paths import ensure_user_layout, package_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Score frozen EuroJackpot predictions against an official draw result "
            "and update the adaptive research learner."
        )
    )
    parser.add_argument("--draw-date", required=True, help="Draw date YYYY-MM-DD")
    parser.add_argument("--main", required=True, help="Comma-separated 5 main numbers")
    parser.add_argument("--euro", required=True, help="Comma-separated 2 euro numbers")
    parser.add_argument(
        "--db",
        default=str(ensure_user_layout(package_root() / "EuroJackpot_Operational_v3_7.sqlite")["db"]),
        help="Operational SQLite database path",
    )
    parser.add_argument("--source", default="official-manual")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON report path (default: user-data outputs/)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    main_nums = [int(x.strip()) for x in args.main.split(",")]
    euro_nums = [int(x.strip()) for x in args.euro.split(",")]
    result = score_draw_result(
        args.db,
        draw_date=args.draw_date,
        result_main=main_nums,
        result_euro=euro_nums,
        source=args.source,
    )
    result["status_snapshot"] = learning_status(args.db)

    if args.output:
        out = Path(args.output).expanduser().resolve()
    else:
        out_dir = ensure_user_layout()["outputs"]
        out = out_dir / f"EuroJackpot_PostDraw_{args.draw_date}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": str(out), **{
        "draw_date": result["draw_date"],
        "predictions_scored": len(result["predictions_scored"]),
        "workflow_lines_scored": len(result["workflow_lines_scored"]),
        "learning_events": result["learning"]["events"],
        "successes": result["learning"]["successes"],
        "failures": result["learning"]["failures"],
        "statement": result["statement"],
    }}, indent=2))


if __name__ == "__main__":
    main()

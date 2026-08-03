
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from eurojackpot_learning_engine_v3_8 import (
    freeze_workflow_prediction,
    learning_status,
    rerank_portfolio_with_learning,
)
from eurojackpot_operational_v3_4 import independent_combination_space, verify_wheel_csv
from eurojackpot_paths import ensure_user_layout, package_root, read_version, short_version
from eurojackpot_ticket_renderer_v3_6 import TicketPayload, ensure_ticket_schema, render_ticket


ROOT = package_root()
VERSION = read_version(ROOT)
WORKFLOW_VERSION = short_version(VERSION)
BUNDLED_DB = ROOT / "EuroJackpot_Operational_v3_7.sqlite"
_USER = ensure_user_layout(BUNDLED_DB)
DEFAULT_DB = _USER["db"]
OUTPUT_DIR = _USER["outputs"]
ENGINE_OUT_DIR = _USER["engine"]
_EDGE_RESULTS = ENGINE_OUT_DIR / "EuroJackpot_Model_Results_Edge_v3_8.json"
DEFAULT_RESULTS = _EDGE_RESULTS if _EDGE_RESULTS.exists() else ROOT / "EuroJackpot_Model_Results_v3_1_Audited.json"
FULL_ENGINE = ROOT / "eurojackpot_reliability_engine_v3.py"
HISTORY = ROOT / "EuroJackpot_Canonical_History_v3.csv"
TEMPLATE = ROOT / "EuroJackpot_Ticket_Template_v3_6.png"
SELECTED_POOL = [4, 21, 25, 27, 28, 35, 36, 37, 42, 44, 48, 50]


class WorkflowError(RuntimeError):
    pass


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_history(path: str | Path) -> dict[str, Any]:
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if not rows:
        raise WorkflowError("Canonical history is empty.")
    dates = [r["draw_date"] for r in rows]
    if len(dates) != len(set(dates)):
        raise WorkflowError("Canonical history contains duplicate dates.")
    for row in rows:
        main = [int(row[f"main_{i}"]) for i in range(1, 6)]
        euro = [int(row[f"euro_{i}"]) for i in range(1, 3)]
        if len(set(main)) != 5 or not all(1 <= x <= 50 for x in main):
            raise WorkflowError(f"Invalid main numbers on {row['draw_date']}.")
        euro_pool = int(row.get("euro_pool") or 12)
        if len(set(euro)) != 2 or not all(1 <= x <= euro_pool for x in euro):
            raise WorkflowError(f"Invalid Euro numbers on {row['draw_date']}.")
    return {
        "draws": len(rows),
        "first_date": dates[0],
        "last_date": dates[-1],
        "history_hash": sha256_file(path),
    }


def ensure_workflow_schema(db_path: str | Path) -> None:
    ensure_ticket_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS workflow_runs_v3_7 (
                run_id TEXT PRIMARY KEY,
                created_at_utc TEXT NOT NULL,
                target_draw TEXT NOT NULL,
                data_cutoff TEXT NOT NULL,
                engine_mode TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                overall_status TEXT NOT NULL,
                jackpot_mode TEXT,
                jackpot_display TEXT NOT NULL,
                result_file TEXT NOT NULL,
                result_hash TEXT NOT NULL,
                history_hash TEXT NOT NULL,
                run_hash TEXT NOT NULL,
                output_image TEXT,
                output_summary TEXT,
                validation_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workflow_lines_v3_7 (
                run_id TEXT NOT NULL,
                line_no INTEGER NOT NULL,
                role TEXT NOT NULL,
                main_json TEXT NOT NULL,
                euro_json TEXT NOT NULL,
                portfolio_score REAL,
                anti_crowd_score REAL,
                PRIMARY KEY(run_id, line_no),
                FOREIGN KEY(run_id) REFERENCES workflow_runs_v3_7(run_id)
            );
            """
        )


def database_integrity(db_path: str | Path) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    return {"integrity": integrity, "foreign_key_violations": len(fk), "passed": integrity == "ok" and not fk}


def run_full_engine(log_path: Path, engine_out: Path) -> Path:
    if not FULL_ENGINE.exists():
        raise WorkflowError(f"Full engine file not found: {FULL_ENGINE}")
    engine_out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["EUROJACKPOT_OUTPUT_DIR"] = str(engine_out)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            [sys.executable, str(FULL_ENGINE)],
            cwd=str(ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
    if proc.returncode != 0:
        raise WorkflowError(f"Full engine failed. Review {log_path.name}.")
    results = engine_out / "EuroJackpot_Model_Results_v3.json"
    if not results.exists():
        # Backward-compatible fallback for older engine builds.
        legacy = ROOT / "EuroJackpot_Model_Results_v3.json"
        if legacy.exists():
            return legacy
        raise WorkflowError("Full engine completed without creating EuroJackpot_Model_Results_v3.json.")
    return results


def load_engine_results(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    portfolio = data.get("portfolio")
    primary = data.get("primary_experimental_line") or data.get("primary_line")
    if not portfolio and primary:
        portfolio = [primary]
    if not portfolio:
        raise WorkflowError("Engine results contain no portfolio or primary line.")
    normalized = []
    for idx, line in enumerate(portfolio[:5], 1):
        main = sorted(int(x) for x in line["main"])
        euro = sorted(int(x) for x in line["euro"])
        if len(main) != 5 or len(set(main)) != 5 or not all(1 <= x <= 50 for x in main):
            raise WorkflowError(f"Invalid main line {idx} in result file.")
        if len(euro) != 2 or len(set(euro)) != 2 or not all(1 <= x <= 12 for x in euro):
            raise WorkflowError(f"Invalid Euro line {idx} in result file.")
        normalized.append(
            {
                "line": idx,
                "main": main,
                "euro": euro,
                "portfolio_score": line.get("portfolio_score"),
                "anti_crowd_score": line.get("anti_crowd_score"),
            }
        )
    return {
        "raw": data,
        "portfolio": normalized,
        "engine_version": str(data.get("engine_version", "unknown")),
        "target_draw": str(data.get("next_draw_date") or data.get("target_draw")),
        "overall_status": str(data.get("overall_status", "Unknown")),
    }


def verify_wheels() -> dict[str, Any]:
    specifications = {
        "54": ("EuroJackpot_Wheel_54_Pair_Compact.csv", 54, 2),
        "135": ("EuroJackpot_Wheel_135_Pair_Extended.csv", 135, 2),
        "198": ("EuroJackpot_Wheel_198_Triple_Compact.csv", 198, 3),
        "495": ("EuroJackpot_Wheel_495_Triple_Extended.csv", 495, 3),
    }
    checks = {}
    for key, (name, expected, subset) in specifications.items():
        path = ROOT / name
        checks[key] = verify_wheel_csv(path, expected, subset, SELECTED_POOL)
    return {
        "combination_space": independent_combination_space(),
        "wheels": checks,
        "passed": all(x["passed"] for x in checks.values()),
    }


def latest_jackpot_state(db_path: str | Path, explicit: str | None = None) -> dict[str, Any]:
    if explicit:
        return {"display": explicit, "mode": "MANUAL"}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT s.jackpot_eur, s.verification_status, h.mode
                FROM jackpot_state s
                LEFT JOIN jackpot_strategy_history h USING(draw_date)
                WHERE UPPER(s.verification_status)='VERIFIED'
                ORDER BY s.draw_date DESC LIMIT 1
                """
            ).fetchone()
        except sqlite3.OperationalError:
            row = None
    if row:
        return {"display": f"€{float(row['jackpot_eur']):,.0f}", "mode": row["mode"] or "VERIFIED"}
    return {"display": "TBA", "mode": "NO VERIFIED STATE"}


def format_draw_date(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return value


def freeze_run(
    db_path: str | Path,
    run_id: str,
    metadata: dict[str, Any],
    lines: Sequence[dict[str, Any]],
) -> None:
    ensure_workflow_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """
            INSERT OR REPLACE INTO workflow_runs_v3_7 (
                run_id, created_at_utc, target_draw, data_cutoff, engine_mode,
                engine_version, overall_status, jackpot_mode, jackpot_display,
                result_file, result_hash, history_hash, run_hash,
                output_image, output_summary, validation_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                metadata["created_at_utc"],
                metadata["target_draw"],
                metadata["data_cutoff"],
                metadata["engine_mode"],
                metadata["engine_version"],
                metadata["overall_status"],
                metadata["jackpot_mode"],
                metadata["jackpot_display"],
                metadata["result_file"],
                metadata["result_hash"],
                metadata["history_hash"],
                metadata["run_hash"],
                metadata.get("output_image"),
                metadata.get("output_summary"),
                json.dumps(metadata["validation"], sort_keys=True),
            ),
        )
        conn.execute("DELETE FROM workflow_lines_v3_7 WHERE run_id=?", (run_id,))
        for line in lines:
            conn.execute(
                """
                INSERT INTO workflow_lines_v3_7 (
                    run_id, line_no, role, main_json, euro_json,
                    portfolio_score, anti_crowd_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    line["line"],
                    "PRIMARY" if line["line"] == 1 else f"ALT_{line['line']-1}",
                    json.dumps(line["main"]),
                    json.dumps(line["euro"]),
                    line.get("portfolio_score"),
                    line.get("anti_crowd_score"),
                ),
            )


def update_run_artifacts(db_path: str | Path, run_id: str, image: Path, summary: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE workflow_runs_v3_7 SET output_image=?, output_summary=? WHERE run_id=?",
            (str(image), str(summary), run_id),
        )


def execute(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    engine_out = Path(getattr(args, "engine_out", ENGINE_OUT_DIR)).expanduser().resolve()
    engine_out.mkdir(parents=True, exist_ok=True)
    db_path = Path(args.db).expanduser().resolve()
    history = validate_history(HISTORY)
    ensure_workflow_schema(db_path)

    timestamp = datetime.now(timezone.utc)
    if args.engine_mode == "full":
        log_path = output_dir / f"EuroJackpot_FullEngine_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.log"
        result_path = run_full_engine(log_path, engine_out)
    else:
        result_path = Path(args.results).expanduser().resolve()
        if not result_path.exists():
            raise WorkflowError(f"Audited result file not found: {result_path}")

    engine = load_engine_results(result_path)
    learning_before = learning_status(db_path)
    if getattr(args, "adaptive_rank", True) and (learning_before.get("events") or 0) > 0:
        engine["portfolio"] = rerank_portfolio_with_learning(db_path, engine["portfolio"])
        engine["adaptive_reranked"] = True
    else:
        engine["adaptive_reranked"] = False
    jackpot = latest_jackpot_state(db_path, args.jackpot)
    wheels = verify_wheels()
    db_check = database_integrity(db_path)

    validation = {
        "history": history,
        "wheels": wheels,
        "database_before": db_check,
        "learning_before": {
            "events": learning_before.get("events"),
            "successes": learning_before.get("successes"),
            "failures": learning_before.get("failures"),
            "success_rate": learning_before.get("success_rate"),
        },
        "adaptive_reranked": engine["adaptive_reranked"],
        "prediction_probabilities": {
            "main": 0.1,
            "euro": 1 / 6,
            "unchanged_by_jackpot": True,
        },
    }
    if not wheels["passed"]:
        raise WorkflowError("Independent wheel verification failed.")
    if not db_check["passed"]:
        raise WorkflowError("Database integrity check failed.")

    result_hash = sha256_file(result_path)
    run_core = {
        "target_draw": engine["target_draw"],
        "data_cutoff": history["last_date"],
        "engine_mode": args.engine_mode,
        "engine_version": engine["engine_version"],
        "overall_status": engine["overall_status"],
        "jackpot_mode": jackpot["mode"],
        "jackpot_display": jackpot["display"],
        "result_hash": result_hash,
        "history_hash": history["history_hash"],
        "portfolio": engine["portfolio"],
    }
    run_hash = canonical_hash(run_core)
    run_id = f"{engine['target_draw']}-{run_hash[:12]}"

    labels = ["Primary", "Alt 1", "Alt 2", "Alt 3", "Alt 4", "Reserve"]
    ticket_lines = [{"main": x["main"], "euro": x["euro"]} for x in engine["portfolio"]]
    while len(ticket_lines) < 6:
        ticket_lines.append({"main": [], "euro": []})

    header_mode = engine["overall_status"]
    if jackpot["mode"] not in ("NO VERIFIED STATE", "MANUAL"):
        header_mode += f" / {jackpot['mode']}"

    payload = TicketPayload(
        draw_date=format_draw_date(engine["target_draw"]),
        jackpot=jackpot["display"],
        engine_version=f"v{WORKFLOW_VERSION}",
        mode=header_mode,
        run_id=run_hash[:12],
        source_record_hash=run_hash,
        line_labels=labels,
        lines=ticket_lines[:6],
    )

    image_path = output_dir / f"EuroJackpot_Ticket_{engine['target_draw']}_{run_hash[:12]}.png"
    summary_path = output_dir / f"EuroJackpot_Run_{engine['target_draw']}_{run_hash[:12]}.json"

    metadata = {
        "created_at_utc": timestamp.isoformat(),
        "target_draw": engine["target_draw"],
        "data_cutoff": history["last_date"],
        "engine_mode": args.engine_mode,
        "engine_version": engine["engine_version"],
        "overall_status": engine["overall_status"],
        "jackpot_mode": jackpot["mode"],
        "jackpot_display": jackpot["display"],
        "result_file": str(result_path),
        "result_hash": result_hash,
        "history_hash": history["history_hash"],
        "run_hash": run_hash,
        "output_image": None,
        "output_summary": None,
        "validation": validation,
    }
    freeze_run(db_path, run_id, metadata, engine["portfolio"])
    frozen = freeze_workflow_prediction(
        db_path,
        target_draw=str(engine["target_draw"]),
        data_cutoff=history["last_date"],
        primary_main=engine["portfolio"][0]["main"],
        primary_euro=engine["portfolio"][0]["euro"],
        run_id=run_id,
        history_path=HISTORY,
        code_path=Path(__file__),
        confidence_state=(
            "Uniform champion deployed; adaptive research learner will score this "
            "prediction after the official draw"
        ),
    )
    render_ticket(payload, image_path, TEMPLATE, db_path=db_path)

    summary = {
        "workflow_version": WORKFLOW_VERSION,
        "app_version": VERSION,
        "run_id": run_id,
        "created_at_utc": timestamp.isoformat(),
        "target_draw": engine["target_draw"],
        "data_cutoff": history["last_date"],
        "engine_mode": args.engine_mode,
        "engine_version": engine["engine_version"],
        "overall_status": engine["overall_status"],
        "jackpot": jackpot,
        "primary": engine["portfolio"][0],
        "alternatives": engine["portfolio"][1:5],
        "ticket_image": str(image_path),
        "database": str(db_path),
        "result_file": str(result_path),
        "run_hash": run_hash,
        "prediction_record_hash": frozen.record_hash,
        "adaptive_reranked": engine["adaptive_reranked"],
        "learning": learning_status(db_path),
        "validation": validation,
        "statement": (
            "The engine selected an experimental portfolio. Adaptive AI will improve research "
            "ranking after future hits and misses. Deployed jackpot probabilities remain uniform; "
            "every unique EuroJackpot line has the same jackpot probability."
        ),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_run_artifacts(db_path, run_id, image_path, summary_path)

    final_db = database_integrity(db_path)
    if not final_db["passed"]:
        raise WorkflowError("Database failed integrity check after artifact insertion.")
    summary["validation"]["database_after"] = final_db
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-command EuroJackpot engine, validation, freeze and ticket rendering workflow."
    )
    parser.add_argument(
        "--engine-mode",
        choices=["audited", "full"],
        default="audited",
        help="audited uses the existing audited whole-engine results; full retrains the full v3 engine.",
    )
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Writable directory for ticket images and run summaries (default: user-data outputs).",
    )
    parser.add_argument(
        "--engine-out",
        default=str(ENGINE_OUT_DIR),
        help="Writable directory for full-engine research artifacts (default: user-data engine).",
    )
    parser.add_argument("--jackpot", default=None, help='Manual display value, e.g. "€120,000,000".')
    parser.add_argument(
        "--adaptive-rank",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Re-rank the experimental portfolio using adaptive learning weights when history exists.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        summary = execute(args)
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({
        "status": "PASS",
        "workflow_version": summary["workflow_version"],
        "run_id": summary["run_id"],
        "target_draw": summary["target_draw"],
        "overall_status": summary["overall_status"],
        "primary": summary["primary"],
        "ticket_image": summary["ticket_image"],
        "summary": str(Path(summary["ticket_image"]).with_name(
            Path(summary["ticket_image"]).name.replace("Ticket_", "Run_").replace(".png", ".json")
        )),
        "database": summary["database"],
    }, indent=2))


if __name__ == "__main__":
    main()

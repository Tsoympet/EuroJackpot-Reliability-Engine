"""
Adaptive research learning loop for EuroJackpot predictions.

After each scored draw:
- successes (above-baseline hits) reinforce the predicted numbers
- failures (at/below baseline) damp those numbers and boost exploration

Deployed jackpot probabilities remain exact-uniform. Learning only affects
experimental research ranking / confidence tracking.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from eurojackpot_advanced_methods_v3_3 import load_canonical_history
from eurojackpot_operational_v3_4 import (
    OperationalDatabase,
    PredictionRecord,
    canonical_json_hash,
    prospective_score_summary,
    sha256_file,
)
from eurojackpot_paths import package_root, read_version
from eurojackpot_ticket_renderer_v3_6 import ensure_ticket_schema


APP_VERSION = read_version()
MAIN_POOL = 50
EURO_POOL = 12
MAIN_BASELINE = 0.5  # expected main hits for one 5-number line under uniform
EURO_BASELINE = 1.0 / 3.0
SUCCESS_MAIN_THRESHOLD = 1  # >=1 main hit counts as partial success signal
STRONG_SUCCESS_MAIN = 2
LEARNING_RATE = 0.18
DECAY_ON_FAIL = 0.12
EXPLORATION_BOOST = 0.04
WEIGHT_FLOOR = 0.15
WEIGHT_CEILING = 4.0


@dataclass(frozen=True)
class OutcomeScore:
    record_hash: str
    target_draw: str
    main_hits: int
    euro_hits: int
    success: bool
    strong_success: bool
    reward: float


def ensure_learning_schema(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = OperationalDatabase(path)
    db.initialize()
    # Workflow/ticket tables are created by the one-click stack; create stubs if absent.
    ensure_ticket_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
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
                PRIMARY KEY(run_id, line_no)
            );
            """
        )
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS learning_number_weights (
                pool TEXT NOT NULL,
                number INTEGER NOT NULL,
                weight REAL NOT NULL,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                last_updated_utc TEXT NOT NULL,
                PRIMARY KEY(pool, number)
            );

            CREATE TABLE IF NOT EXISTS learning_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                target_draw TEXT NOT NULL,
                record_hash TEXT,
                run_id TEXT,
                main_hits INTEGER NOT NULL,
                euro_hits INTEGER NOT NULL,
                success INTEGER NOT NULL,
                reward REAL NOT NULL,
                note TEXT NOT NULL,
                details_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS learning_state (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workflow_line_outcomes (
                run_id TEXT NOT NULL,
                line_no INTEGER NOT NULL,
                main_hits INTEGER,
                euro_hits INTEGER,
                success INTEGER,
                scored_at_utc TEXT,
                PRIMARY KEY(run_id, line_no)
            );
            """
        )
        # Seed uniform priors once.
        now = datetime.now(timezone.utc).isoformat()
        for pool, size in (("main", MAIN_POOL), ("euro", EURO_POOL)):
            for n in range(1, size + 1):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO learning_number_weights
                    (pool, number, weight, success_count, failure_count, last_updated_utc)
                    VALUES (?, ?, 1.0, 0, 0, ?)
                    """,
                    (pool, n, now),
                )
        conn.execute(
            """
            INSERT OR IGNORE INTO learning_state(key, value_json, updated_at_utc)
            VALUES ('meta', ?, ?)
            """,
            (
                json.dumps(
                    {
                        "version": APP_VERSION,
                        "mode": "research-adaptive",
                        "deployed_champion": "uniform-1.0",
                        "learning_rate": LEARNING_RATE,
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )


def _clip(weight: float) -> float:
    return float(min(WEIGHT_CEILING, max(WEIGHT_FLOOR, weight)))


def get_weights(db_path: str | Path) -> dict[str, dict[int, float]]:
    ensure_learning_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT pool, number, weight FROM learning_number_weights ORDER BY pool, number"
        ).fetchall()
    out: dict[str, dict[int, float]] = {"main": {}, "euro": {}}
    for pool, number, weight in rows:
        out[str(pool)][int(number)] = float(weight)
    return out


def classify_outcome(main_hits: int, euro_hits: int) -> tuple[bool, bool, float]:
    """Return (success, strong_success, reward)."""
    # Reward combines main/euro surprise vs uniform baselines.
    main_delta = main_hits - MAIN_BASELINE
    euro_delta = euro_hits - EURO_BASELINE
    reward = main_delta + 0.75 * euro_delta
    strong = main_hits >= STRONG_SUCCESS_MAIN or (main_hits >= 1 and euro_hits >= 1)
    success = main_hits >= SUCCESS_MAIN_THRESHOLD or euro_hits >= 1 and reward > 0
    if main_hits == 0 and euro_hits == 0:
        success = False
        reward = -1.0
    return success, strong, float(reward)


def apply_weight_update(
    db_path: str | Path,
    predicted_main: Sequence[int],
    predicted_euro: Sequence[int],
    success: bool,
    strong_success: bool,
    reward: float,
) -> dict[str, Any]:
    ensure_learning_schema(db_path)
    now = datetime.now(timezone.utc).isoformat()
    updates: list[dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        def bump(pool: str, number: int, delta: float, success_inc: int, fail_inc: int) -> None:
            row = conn.execute(
                "SELECT weight, success_count, failure_count FROM learning_number_weights WHERE pool=? AND number=?",
                (pool, number),
            ).fetchone()
            if row is None:
                weight, sc, fc = 1.0, 0, 0
            else:
                weight, sc, fc = float(row[0]), int(row[1]), int(row[2])
            new_w = _clip(weight * math.exp(delta))
            conn.execute(
                """
                INSERT INTO learning_number_weights
                (pool, number, weight, success_count, failure_count, last_updated_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(pool, number) DO UPDATE SET
                    weight=excluded.weight,
                    success_count=excluded.success_count,
                    failure_count=excluded.failure_count,
                    last_updated_utc=excluded.last_updated_utc
                """,
                (pool, number, new_w, sc + success_inc, fc + fail_inc, now),
            )
            updates.append(
                {
                    "pool": pool,
                    "number": number,
                    "old_weight": weight,
                    "new_weight": new_w,
                    "delta": delta,
                }
            )

        if success:
            scale = LEARNING_RATE * (1.35 if strong_success else 1.0)
            scale *= max(0.35, min(1.8, 0.75 + abs(reward) / 2))
            for n in predicted_main:
                bump("main", int(n), scale, 1, 0)
            for n in predicted_euro:
                bump("euro", int(n), scale * 0.9, 1, 0)
        else:
            for n in predicted_main:
                bump("main", int(n), -DECAY_ON_FAIL, 0, 1)
            for n in predicted_euro:
                bump("euro", int(n), -DECAY_ON_FAIL * 0.9, 0, 1)
            # Mild exploration: boost numbers not in the failed ticket.
            predicted_main_set = {int(x) for x in predicted_main}
            predicted_euro_set = {int(x) for x in predicted_euro}
            for n in range(1, MAIN_POOL + 1):
                if n not in predicted_main_set:
                    bump("main", n, EXPLORATION_BOOST / 4, 0, 0)
            for n in range(1, EURO_POOL + 1):
                if n not in predicted_euro_set:
                    bump("euro", n, EXPLORATION_BOOST / 3, 0, 0)

        # Renormalize mean weight to 1.0 so drift stays bounded.
        for pool, size in (("main", MAIN_POOL), ("euro", EURO_POOL)):
            rows = conn.execute(
                "SELECT number, weight FROM learning_number_weights WHERE pool=?",
                (pool,),
            ).fetchall()
            if not rows:
                continue
            mean_w = sum(float(r[1]) for r in rows) / len(rows)
            if mean_w <= 0:
                continue
            for number, weight in rows:
                conn.execute(
                    "UPDATE learning_number_weights SET weight=?, last_updated_utc=? WHERE pool=? AND number=?",
                    (_clip(float(weight) / mean_w), now, pool, int(number)),
                )

        scored = conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE main_hits IS NOT NULL"
        ).fetchone()[0]
        successes = conn.execute(
            "SELECT COUNT(*) FROM learning_events WHERE success=1"
        ).fetchone()[0]
        failures = conn.execute(
            "SELECT COUNT(*) FROM learning_events WHERE success=0"
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO learning_state(key, value_json, updated_at_utc)
            VALUES ('summary', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at_utc=excluded.updated_at_utc
            """,
            (
                json.dumps(
                    {
                        "scored_predictions": int(scored),
                        "learning_successes": int(successes) + (1 if success else 0),
                        "learning_failures": int(failures) + (0 if success else 1),
                        "last_reward": reward,
                        "last_success": success,
                        "deployed_champion": "uniform-1.0",
                        "note": (
                            "Adaptive weights update research ranking only. "
                            "Jackpot draw probabilities remain uniform."
                        ),
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )
    return {"updates": updates, "success": success, "reward": reward}


def freeze_workflow_prediction(
    db_path: str | Path,
    *,
    target_draw: str,
    data_cutoff: str,
    primary_main: Sequence[int],
    primary_euro: Sequence[int],
    run_id: str,
    history_path: str | Path,
    code_path: str | Path,
    confidence_state: str | None = None,
) -> PredictionRecord:
    """Immutable freeze of the one-click primary line into predictions registry."""
    ensure_learning_schema(db_path)
    payload = {
        "target_draw": target_draw,
        "data_cutoff": data_cutoff,
        "model_version": APP_VERSION,
        "champion_model": "uniform-1.0",
        "research_model": "v3.8-adaptive-learning",
        "primary_main": tuple(sorted(int(x) for x in primary_main)),
        "primary_euro": tuple(sorted(int(x) for x in primary_euro)),
        "deployed_main_probability": 5 / 50,
        "deployed_euro_probability": 2 / 12,
        "confidence_state": confidence_state
        or "Uniform mode; adaptive research learner tracking outcomes",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_hash": sha256_file(code_path),
        "data_hash": sha256_file(history_path),
    }
    payload["record_hash"] = canonical_json_hash(payload)
    # Include run_id in audit only; hash stays content-based without run_id so
    # identical forecasts collapse, but we still log the run association.
    record = PredictionRecord(**payload)
    OperationalDatabase(db_path).freeze_prediction(record)
    OperationalDatabase(db_path).log(
        "learning_freeze",
        "INFO",
        f"Frozen adaptive-tracked prediction for {target_draw}",
        {"record_hash": record.record_hash, "run_id": run_id},
    )
    return record


def score_draw_result(
    db_path: str | Path,
    *,
    draw_date: str,
    result_main: Sequence[int],
    result_euro: Sequence[int],
    source: str = "manual",
) -> dict[str, Any]:
    """Score unscored predictions + workflow lines for a draw and update AI weights."""
    ensure_learning_schema(db_path)
    main = sorted(int(x) for x in result_main)
    euro = sorted(int(x) for x in result_euro)
    if len(main) != 5 or len(set(main)) != 5 or not all(1 <= x <= MAIN_POOL for x in main):
        raise ValueError("result_main must be 5 unique integers in 1..50")
    if len(euro) != 2 or len(set(euro)) != 2 or not all(1 <= x <= EURO_POOL for x in euro):
        raise ValueError("result_euro must be 2 unique integers in 1..12")

    db = OperationalDatabase(db_path)
    # Upsert draw into draws table when possible.
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute("SELECT draw_date FROM draws WHERE draw_date=?", (draw_date,)).fetchone()
        if existing is None:
            draw_id_row = conn.execute("SELECT COALESCE(MAX(draw_id), 0) + 1 AS n FROM draws").fetchone()
            draw_id = int(draw_id_row["n"])
            weekday = date.fromisoformat(draw_date).strftime("%A")
            conn.execute(
                """
                INSERT INTO draws (
                    draw_date, draw_id, main_1, main_2, main_3, main_4, main_5,
                    euro_1, euro_2, euro_pool, draw_day, source_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (draw_date, draw_id, *main, *euro, EURO_POOL, weekday, source),
            )

        prediction_rows = conn.execute(
            """
            SELECT record_hash, primary_main, primary_euro
            FROM predictions
            WHERE target_draw=? AND main_hits IS NULL
            """,
            (draw_date,),
        ).fetchall()

        workflow_rows = conn.execute(
            """
            SELECT r.run_id, l.line_no, l.main_json, l.euro_json
            FROM workflow_runs_v3_7 r
            JOIN workflow_lines_v3_7 l ON r.run_id = l.run_id
            LEFT JOIN workflow_line_outcomes o ON o.run_id = l.run_id AND o.line_no = l.line_no
            WHERE r.target_draw=? AND o.scored_at_utc IS NULL
            """,
            (draw_date,),
        ).fetchall()

    scored_predictions: list[OutcomeScore] = []
    for row in prediction_rows:
        hits = db.score_prediction(row["record_hash"], main, euro)
        success, strong, reward = classify_outcome(hits["main_hits"], hits["euro_hits"])
        predicted_main = json.loads(row["primary_main"])
        predicted_euro = json.loads(row["primary_euro"])
        apply_weight_update(db_path, predicted_main, predicted_euro, success, strong, reward)
        _log_learning_event(
            db_path,
            target_draw=draw_date,
            record_hash=row["record_hash"],
            run_id=None,
            main_hits=hits["main_hits"],
            euro_hits=hits["euro_hits"],
            success=success,
            reward=reward,
            note="prediction_registry",
        )
        scored_predictions.append(
            OutcomeScore(
                record_hash=row["record_hash"],
                target_draw=draw_date,
                main_hits=hits["main_hits"],
                euro_hits=hits["euro_hits"],
                success=success,
                strong_success=strong,
                reward=reward,
            )
        )

    scored_workflow = []
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        for row in workflow_rows:
            predicted_main = json.loads(row["main_json"] or "[]")
            predicted_euro = json.loads(row["euro_json"] or "[]")
            if len(predicted_main) != 5 or len(predicted_euro) != 2:
                continue
            main_hits = len(set(predicted_main).intersection(main))
            euro_hits = len(set(predicted_euro).intersection(euro))
            success, strong, reward = classify_outcome(main_hits, euro_hits)
            conn.execute(
                """
                INSERT INTO workflow_line_outcomes
                (run_id, line_no, main_hits, euro_hits, success, scored_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, line_no) DO UPDATE SET
                    main_hits=excluded.main_hits,
                    euro_hits=excluded.euro_hits,
                    success=excluded.success,
                    scored_at_utc=excluded.scored_at_utc
                """,
                (row["run_id"], row["line_no"], main_hits, euro_hits, int(success), now),
            )
            # Only the primary line drives adaptive weights to avoid double counting alts.
            if int(row["line_no"]) == 1 and not any(
                s.record_hash and s.target_draw == draw_date for s in scored_predictions
            ):
                apply_weight_update(db_path, predicted_main, predicted_euro, success, strong, reward)
                _log_learning_event(
                    db_path,
                    target_draw=draw_date,
                    record_hash=None,
                    run_id=row["run_id"],
                    main_hits=main_hits,
                    euro_hits=euro_hits,
                    success=success,
                    reward=reward,
                    note="workflow_primary",
                )
            scored_workflow.append(
                {
                    "run_id": row["run_id"],
                    "line_no": row["line_no"],
                    "main_hits": main_hits,
                    "euro_hits": euro_hits,
                    "success": success,
                    "reward": reward,
                }
            )

    # Update research model prospective counter.
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE models
            SET prospective_draws = (
                SELECT COUNT(*) FROM predictions WHERE main_hits IS NOT NULL
            )
            WHERE role='challenger'
            """
        )
        success_rate = None
        events = conn.execute("SELECT success FROM learning_events").fetchall()
        if events:
            success_rate = sum(int(r[0]) for r in events) / len(events)
        gate = "FAIL"
        if events and len(events) >= 200 and success_rate is not None and success_rate > 0.55:
            gate = "CANDIDATE"
        conn.execute(
            """
            UPDATE models
            SET gate_status=?, description=?
            WHERE model_id='super-learner'
            """,
            (
                gate,
                "Adaptive research learner (outcome-weighted). Experimental only; uniform remains champion.",
            ),
        )

    summary = prospective_score_summary(db_path)
    learning = learning_status(db_path)
    db.log(
        "learning_score",
        "PASS" if scored_predictions or scored_workflow else "INFO",
        f"Scored draw {draw_date}",
        {
            "predictions_scored": len(scored_predictions),
            "workflow_lines_scored": len(scored_workflow),
            "result_main": main,
            "result_euro": euro,
        },
    )
    return {
        "draw_date": draw_date,
        "result_main": main,
        "result_euro": euro,
        "predictions_scored": [s.__dict__ for s in scored_predictions],
        "workflow_lines_scored": scored_workflow,
        "prospective_summary": summary,
        "learning": learning,
        "statement": (
            "Learning updated experimental research weights from this outcome. "
            "Deployed jackpot probabilities remain uniform for every line."
        ),
    }


def _log_learning_event(
    db_path: str | Path,
    *,
    target_draw: str,
    record_hash: str | None,
    run_id: str | None,
    main_hits: int,
    euro_hits: int,
    success: bool,
    reward: float,
    note: str,
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO learning_events (
                created_at_utc, target_draw, record_hash, run_id,
                main_hits, euro_hits, success, reward, note, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                target_draw,
                record_hash,
                run_id,
                main_hits,
                euro_hits,
                int(success),
                reward,
                note,
                json.dumps({"app_version": APP_VERSION}, sort_keys=True),
            ),
        )


def learning_status(db_path: str | Path) -> dict[str, Any]:
    ensure_learning_schema(db_path)
    weights = get_weights(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        events = conn.execute(
            """
            SELECT target_draw, main_hits, euro_hits, success, reward, created_at_utc, note
            FROM learning_events
            ORDER BY event_id DESC
            LIMIT 20
            """
        ).fetchall()
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS n,
                SUM(success) AS successes,
                AVG(main_hits) AS avg_main,
                AVG(euro_hits) AS avg_euro,
                AVG(reward) AS avg_reward
            FROM learning_events
            """
        ).fetchone()
        state = conn.execute(
            "SELECT value_json FROM learning_state WHERE key='summary'"
        ).fetchone()

    def top_numbers(pool: str, k: int = 10) -> list[dict[str, Any]]:
        items = sorted(weights[pool].items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [{"number": n, "weight": round(w, 4)} for n, w in items]

    n = int(totals["n"] or 0)
    successes = int(totals["successes"] or 0)
    return {
        "app_version": APP_VERSION,
        "deployed_champion": "uniform-1.0",
        "events": n,
        "successes": successes,
        "failures": n - successes,
        "success_rate": (successes / n) if n else None,
        "avg_main_hits": totals["avg_main"],
        "avg_euro_hits": totals["avg_euro"],
        "avg_reward": totals["avg_reward"],
        "top_main": top_numbers("main"),
        "top_euro": top_numbers("euro"),
        "recent_events": [dict(r) for r in events],
        "summary_state": json.loads(state["value_json"]) if state else {},
        "research_only": True,
        "disclaimer": (
            "Adaptive AI updates experimental ranking from hits and misses. "
            "It does not change the mathematical jackpot odds of any unique line."
        ),
    }


def suggest_research_line(db_path: str | Path, *, main_k: int = 5, euro_k: int = 2) -> dict[str, Any]:
    """Suggest an experimental line from current adaptive weights."""
    weights = get_weights(db_path)
    main = [n for n, _ in sorted(weights["main"].items(), key=lambda kv: kv[1], reverse=True)[:main_k]]
    euro = [n for n, _ in sorted(weights["euro"].items(), key=lambda kv: kv[1], reverse=True)[:euro_k]]
    return {
        "main": sorted(main),
        "euro": sorted(euro),
        "source": "adaptive-learning-weights",
        "experimental": True,
    }


def _frequency_scores(past_draws: Sequence[Any], *, pool: str) -> dict[int, float]:
    """Recency-weighted frequency from past official draws only (no leakage)."""
    size = MAIN_POOL if pool == "main" else EURO_POOL
    scores = {n: 0.0 for n in range(1, size + 1)}
    if not past_draws:
        return {n: 1.0 for n in scores}
    n = len(past_draws)
    for idx, draw in enumerate(past_draws):
        # Newer draws count more.
        age_weight = 0.55 + 0.45 * ((idx + 1) / n)
        values = draw.main if pool == "main" else draw.euro
        euro_pool = getattr(draw, "euro_pool", EURO_POOL)
        for value in values:
            if pool == "euro" and value > euro_pool:
                continue
            scores[int(value)] += age_weight
    # Laplace smoothing toward uniform.
    for key in scores:
        scores[key] += 1.0
    mean = sum(scores.values()) / len(scores)
    return {k: (v / mean) if mean else 1.0 for k, v in scores.items()}


def _era_frequency_scores(
    past_draws: Sequence[Any],
    *,
    pool: str,
    target_euro_pool: int,
) -> dict[int, float]:
    """Era-aware frequency: for euro, prefer same euro-pool-size history."""
    size = MAIN_POOL if pool == "main" else min(EURO_POOL, target_euro_pool)
    if pool == "main" or not past_draws:
        return _frequency_scores(past_draws, pool=pool)
    era = [d for d in past_draws if int(getattr(d, "euro_pool", EURO_POOL)) == int(target_euro_pool)]
    use = era if len(era) >= 25 else list(past_draws)
    scores = {n: 0.0 for n in range(1, size + 1)}
    n = len(use)
    for idx, draw in enumerate(use):
        age_weight = 0.55 + 0.45 * ((idx + 1) / n)
        for value in draw.euro:
            if 1 <= int(value) <= size:
                scores[int(value)] += age_weight
    for key in scores:
        scores[key] += 1.0
    # Shrink era scores toward global frequency for stability.
    global_scores = _frequency_scores(past_draws, pool="euro")
    out = {}
    for n in scores:
        out[n] = 0.70 * scores[n] + 0.30 * global_scores.get(n, 1.0)
    mean = sum(out.values()) / len(out)
    return {k: (v / mean) if mean else 1.0 for k, v in out.items()}


def _ewma_scores(past_draws: Sequence[Any], *, pool: str, halflife: int = 25) -> dict[int, float]:
    """EWMA hit scores from past draws only."""
    size = MAIN_POOL if pool == "main" else EURO_POOL
    if not past_draws:
        return {n: 1.0 for n in range(1, size + 1)}
    decay = math.exp(math.log(0.5) / max(halflife, 1))
    acc = {n: 0.0 for n in range(1, size + 1)}
    w = 0.0
    for draw in past_draws:
        w = decay * w + 1.0
        for n in acc:
            acc[n] *= decay
        values = draw.main if pool == "main" else draw.euro
        for value in values:
            if 1 <= int(value) <= size:
                acc[int(value)] += 1.0
    for n in acc:
        acc[n] = (acc[n] + 1.0) / (w + 1.0)
    mean = sum(acc.values()) / len(acc)
    return {k: (v / mean) if mean else 1.0 for k, v in acc.items()}


def predict_from_past_draws(
    db_path: str | Path,
    past_draws: Sequence[Any],
    *,
    euro_pool: int = EURO_POOL,
) -> dict[str, Any]:
    """
    Build one experimental line using only information available before the next draw:
    blend of era-aware frequency, EWMA, and current adaptive weights.
    """
    ensure_learning_schema(db_path)
    adaptive = get_weights(db_path)
    freq_main = _frequency_scores(past_draws, pool="main")
    freq_euro = _era_frequency_scores(
        past_draws, pool="euro", target_euro_pool=euro_pool
    )
    ewma_main = _ewma_scores(past_draws, pool="main", halflife=40)
    ewma_euro = _ewma_scores(past_draws, pool="euro", halflife=25)

    main_score = {
        n: (
            0.35 * freq_main.get(n, 1.0)
            + 0.25 * ewma_main.get(n, 1.0)
            + 0.40 * adaptive["main"].get(n, 1.0)
        )
        for n in range(1, MAIN_POOL + 1)
    }
    euro_score = {
        n: (
            0.40 * freq_euro.get(n, 1.0)
            + 0.30 * ewma_euro.get(n, 1.0)
            + 0.30 * adaptive["euro"].get(n, 1.0)
        )
        for n in range(1, euro_pool + 1)
    }
    main = [n for n, _ in sorted(main_score.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
    euro = [n for n, _ in sorted(euro_score.items(), key=lambda kv: (-kv[1], kv[0]))[:2]]
    return {
        "main": sorted(main),
        "euro": sorted(euro),
        "main_score": {str(k): round(v, 4) for k, v in main_score.items()},
        "euro_score": {str(k): round(v, 4) for k, v in euro_score.items()},
        "source": "era-frequency+ewma+adaptive-weights",
        "past_draws_used": len(past_draws),
        "experimental": True,
    }


def train_on_history(
    db_path: str | Path,
    history_path: str | Path,
    *,
    min_history: int = 80,
    max_draws: int | None = None,
    reset: bool = True,
    progress_every: int = 50,
) -> dict[str, Any]:
    """
    Walk-forward train the adaptive learner on official EuroJackpot history.

    For each draw t (after warm-up):
      1. predict using only draws[:t]
      2. freeze that prediction for draw t
      3. score against the official result at t
      4. update adaptive weights from success/failure
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reset:
        for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
            if candidate.exists():
                candidate.unlink()
    ensure_learning_schema(path)
    draws = load_canonical_history(history_path)
    if len(draws) <= min_history:
        raise ValueError(f"Need more than {min_history} historical draws; found {len(draws)}")

    end = len(draws) if max_draws is None else min(len(draws), min_history + max_draws)
    code_path = Path(__file__)
    rolling_main: list[int] = []
    rolling_euro: list[int] = []
    rolling_success: list[int] = []
    timeline: list[dict[str, Any]] = []

    for t in range(min_history, end):
        past = draws[:t]
        target = draws[t]
        prediction = predict_from_past_draws(path, past, euro_pool=target.euro_pool)
        freeze_workflow_prediction(
            path,
            target_draw=target.draw_date,
            data_cutoff=past[-1].draw_date,
            primary_main=prediction["main"],
            primary_euro=prediction["euro"],
            run_id=f"history-train-{target.draw_date}",
            history_path=history_path,
            code_path=code_path,
            confidence_state="Walk-forward historical training; experimental research learner",
        )
        scored = score_draw_result(
            path,
            draw_date=target.draw_date,
            result_main=target.main,
            result_euro=target.euro,
            source="canonical-history",
        )
        event = scored["predictions_scored"][0] if scored["predictions_scored"] else None
        if event is None:
            continue
        rolling_main.append(int(event["main_hits"]))
        rolling_euro.append(int(event["euro_hits"]))
        rolling_success.append(1 if event["success"] else 0)
        if progress_every and ((t - min_history + 1) % progress_every == 0 or t == end - 1):
            timeline.append(
                {
                    "draw_index": t,
                    "draw_date": target.draw_date,
                    "predicted_main": prediction["main"],
                    "predicted_euro": prediction["euro"],
                    "actual_main": list(target.main),
                    "actual_euro": list(target.euro),
                    "main_hits": event["main_hits"],
                    "euro_hits": event["euro_hits"],
                    "success": event["success"],
                    "avg_main_hits_so_far": sum(rolling_main) / len(rolling_main),
                    "avg_euro_hits_so_far": sum(rolling_euro) / len(rolling_euro),
                    "success_rate_so_far": sum(rolling_success) / len(rolling_success),
                }
            )

    status = learning_status(path)
    trained = end - min_history
    result = {
        "status": "PASS",
        "history_file": str(history_path),
        "database": str(path.resolve()),
        "total_history_draws": len(draws),
        "warmup_draws": min_history,
        "trained_draws": trained,
        "first_train_date": draws[min_history].draw_date if trained else None,
        "last_train_date": draws[end - 1].draw_date if trained else None,
        "avg_main_hits": (sum(rolling_main) / trained) if trained else None,
        "avg_euro_hits": (sum(rolling_euro) / trained) if trained else None,
        "success_rate": (sum(rolling_success) / trained) if trained else None,
        "uniform_main_baseline": MAIN_BASELINE,
        "uniform_euro_baseline": EURO_BASELINE,
        "main_vs_baseline": (
            (sum(rolling_main) / trained) - MAIN_BASELINE if trained else None
        ),
        "euro_vs_baseline": (
            (sum(rolling_euro) / trained) - EURO_BASELINE if trained else None
        ),
        "timeline_sample": timeline[-12:],
        "learning": status,
        "next_experimental_line": suggest_research_line(path),
        "statement": (
            "Walk-forward training used only prior official draws to predict each next draw, "
            "then updated adaptive research weights from hits and misses. "
            "Deployed jackpot probabilities remain uniform."
        ),
    }
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO learning_state(key, value_json, updated_at_utc)
            VALUES ('history_training', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json=excluded.value_json,
                updated_at_utc=excluded.updated_at_utc
            """,
            (
                json.dumps(
                    {
                        "trained_draws": trained,
                        "avg_main_hits": result["avg_main_hits"],
                        "avg_euro_hits": result["avg_euro_hits"],
                        "success_rate": result["success_rate"],
                        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    },
                    sort_keys=True,
                ),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return result


def rerank_portfolio_with_learning(
    db_path: str | Path,
    portfolio: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Re-order an existing portfolio using adaptive weights (research signal only)."""
    weights = get_weights(db_path)
    ranked = []
    for idx, line in enumerate(portfolio):
        main = [int(x) for x in line["main"]]
        euro = [int(x) for x in line["euro"]]
        score = sum(weights["main"].get(n, 1.0) for n in main) + sum(
            weights["euro"].get(n, 1.0) for n in euro
        )
        item = dict(line)
        item["learning_score"] = float(score)
        item["original_index"] = idx
        ranked.append(item)
    ranked.sort(key=lambda x: (-x["learning_score"], x["original_index"]))
    for i, item in enumerate(ranked, 1):
        item["line"] = i
    return ranked


def run_selftest(db_path: str | Path) -> dict[str, Any]:
    """Deterministic learning-loop self-test using synthetic outcomes."""
    path = Path(db_path)
    for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if candidate.exists():
            candidate.unlink()
    ensure_learning_schema(path)
    root = package_root()
    history = root / "EuroJackpot_Canonical_History_v3.csv"
    code = root / "eurojackpot_learning_engine_v3_8.py"

    # Freeze two synthetic upcoming predictions.
    rec_success = freeze_workflow_prediction(
        path,
        target_draw="2099-01-02",
        data_cutoff="2099-01-01",
        primary_main=[1, 2, 3, 4, 5],
        primary_euro=[1, 2],
        run_id="selftest-success",
        history_path=history,
        code_path=code,
    )
    rec_fail = freeze_workflow_prediction(
        path,
        target_draw="2099-01-06",
        data_cutoff="2099-01-02",
        primary_main=[10, 11, 12, 13, 14],
        primary_euro=[3, 4],
        run_id="selftest-fail",
        history_path=history,
        code_path=code,
    )

    before = get_weights(path)
    # Success: 3 main hits + 1 euro hit
    ok = score_draw_result(
        path,
        draw_date="2099-01-02",
        result_main=[1, 2, 3, 20, 21],
        result_euro=[1, 9],
        source="selftest",
    )
    # Failure: zero hits
    bad = score_draw_result(
        path,
        draw_date="2099-01-06",
        result_main=[30, 31, 32, 33, 34],
        result_euro=[10, 11],
        source="selftest",
    )
    after = get_weights(path)
    status = learning_status(path)

    reinforced = after["main"][1] > before["main"][1] and after["main"][2] > before["main"][2]
    dampened = after["main"][10] < before["main"][10]
    passed = (
        reinforced
        and dampened
        and status["successes"] >= 1
        and status["failures"] >= 1
        and len(ok["predictions_scored"]) == 1
        and len(bad["predictions_scored"]) == 1
    )
    return {
        "passed": passed,
        "reinforced": reinforced,
        "dampened": dampened,
        "success_event": ok["predictions_scored"][0],
        "failure_event": bad["predictions_scored"][0],
        "learning": status,
        "records": [rec_success.record_hash, rec_fail.record_hash],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adaptive EuroJackpot research learner (score outcomes and update weights)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    score = sub.add_parser("score", help="Score a draw result and update learning weights")
    score.add_argument("--db", required=True)
    score.add_argument("--draw-date", required=True, help="YYYY-MM-DD")
    score.add_argument("--main", required=True, help="Comma-separated 5 main numbers")
    score.add_argument("--euro", required=True, help="Comma-separated 2 euro numbers")
    score.add_argument("--source", default="manual")

    status = sub.add_parser("status", help="Show learning status")
    status.add_argument("--db", required=True)

    suggest = sub.add_parser("suggest", help="Suggest experimental line from adaptive weights")
    suggest.add_argument("--db", required=True)

    train = sub.add_parser(
        "train-history",
        help="Walk-forward train on official EuroJackpot history (predict each next draw from the past only)",
    )
    train.add_argument("--db", default="EuroJackpot_Learning_History.sqlite")
    train.add_argument(
        "--history",
        default=str(package_root() / "EuroJackpot_Canonical_History_v3.csv"),
    )
    train.add_argument("--min-history", type=int, default=80, help="Warm-up draws before first prediction")
    train.add_argument("--max-draws", type=int, default=None, help="Optional cap on scored draws after warm-up")
    train.add_argument("--no-reset", action="store_true", help="Continue training existing DB instead of resetting")

    test = sub.add_parser("selftest", help="Run learning-loop self-test")
    test.add_argument("--db", default="EuroJackpot_Learning_SelfTest.sqlite")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "score":
        main_nums = [int(x.strip()) for x in args.main.split(",")]
        euro_nums = [int(x.strip()) for x in args.euro.split(",")]
        result = score_draw_result(
            args.db,
            draw_date=args.draw_date,
            result_main=main_nums,
            result_euro=euro_nums,
            source=args.source,
        )
        print(json.dumps(result, indent=2))
        return
    if args.command == "status":
        print(json.dumps(learning_status(args.db), indent=2))
        return
    if args.command == "suggest":
        print(json.dumps(suggest_research_line(args.db), indent=2))
        return
    if args.command == "train-history":
        result = train_on_history(
            args.db,
            args.history,
            min_history=args.min_history,
            max_draws=args.max_draws,
            reset=not args.no_reset,
        )
        print(json.dumps(result, indent=2))
        return
    if args.command == "selftest":
        result = run_selftest(args.db)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()

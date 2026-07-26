
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import sqlite3
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

from eurojackpot_advanced_methods_v3_3 import (
    Draw,
    anti_crowd_score,
    incidence_matrices,
    load_canonical_history,
    prize_tier_probability_table,
    safe_scale,
)


VERSION = "3.4"
DRAW_WEEKDAYS = {1, 4}  # Tuesday, Friday (Monday=0)
CURRENT_MAIN_POOL = 50
CURRENT_EURO_POOL = 12
MAIN_SELECTED = 5
EURO_SELECTED = 2
LINE_COST_EUR = 2.50
COMBINATION_SPACE = math.comb(50, 5) * math.comb(12, 2)


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    version: str
    role: str
    status: str
    description: str
    brier: float | None = None
    log_loss: float | None = None
    calibration_error: float | None = None
    prospective_draws: int = 0
    gate_status: str = "PENDING"


@dataclass(frozen=True)
class PredictionRecord:
    target_draw: str
    data_cutoff: str
    model_version: str
    champion_model: str
    research_model: str
    primary_main: tuple[int, ...]
    primary_euro: tuple[int, ...]
    deployed_main_probability: float
    deployed_euro_probability: float
    confidence_state: str
    created_at_utc: str
    code_hash: str
    data_hash: str
    record_hash: str


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def next_draw_date(after: date | None = None) -> date:
    current = after or date.today()
    candidate = current + timedelta(days=1)
    while candidate.weekday() not in DRAW_WEEKDAYS:
        candidate += timedelta(days=1)
    return candidate


def previous_draw_date(before: date | None = None) -> date:
    current = before or date.today()
    candidate = current - timedelta(days=1)
    while candidate.weekday() not in DRAW_WEEKDAYS:
        candidate -= timedelta(days=1)
    return candidate


class OperationalDatabase:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS draws (
            draw_date TEXT PRIMARY KEY,
            draw_id INTEGER NOT NULL,
            main_1 INTEGER NOT NULL, main_2 INTEGER NOT NULL, main_3 INTEGER NOT NULL,
            main_4 INTEGER NOT NULL, main_5 INTEGER NOT NULL,
            euro_1 INTEGER NOT NULL, euro_2 INTEGER NOT NULL,
            euro_pool INTEGER NOT NULL,
            draw_day TEXT NOT NULL,
            source_status TEXT NOT NULL DEFAULT 'canonical'
        );

        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            lottery TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            verification_role TEXT NOT NULL,
            adapter_status TEXT NOT NULL,
            last_checked_utc TEXT
        );

        CREATE TABLE IF NOT EXISTS models (
            model_id TEXT NOT NULL,
            version TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT NOT NULL,
            brier REAL,
            log_loss REAL,
            calibration_error REAL,
            prospective_draws INTEGER NOT NULL DEFAULT 0,
            gate_status TEXT NOT NULL DEFAULT 'PENDING',
            PRIMARY KEY (model_id, version)
        );

        CREATE TABLE IF NOT EXISTS predictions (
            record_hash TEXT PRIMARY KEY,
            target_draw TEXT NOT NULL,
            data_cutoff TEXT NOT NULL,
            model_version TEXT NOT NULL,
            champion_model TEXT NOT NULL,
            research_model TEXT NOT NULL,
            primary_main TEXT NOT NULL,
            primary_euro TEXT NOT NULL,
            deployed_main_probability REAL NOT NULL,
            deployed_euro_probability REAL NOT NULL,
            confidence_state TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            data_hash TEXT NOT NULL,
            result_main TEXT,
            result_euro TEXT,
            main_hits INTEGER,
            euro_hits INTEGER,
            scored_at_utc TEXT
        );

        CREATE TABLE IF NOT EXISTS prize_participation (
            draw_date TEXT PRIMARY KEY,
            advertised_jackpot_eur REAL,
            actual_prize_pool_eur REAL,
            rollover_count INTEGER,
            total_columns REAL,
            estimated_sales_eur REAL,
            jackpot_winners INTEGER,
            source_url TEXT,
            verification_status TEXT NOT NULL DEFAULT 'missing'
        );

        CREATE TABLE IF NOT EXISTS prize_tiers (
            draw_date TEXT NOT NULL,
            tier TEXT NOT NULL,
            winners INTEGER,
            prize_per_winner_eur REAL,
            source_url TEXT,
            verification_status TEXT NOT NULL DEFAULT 'missing',
            PRIMARY KEY(draw_date, tier)
        );

        CREATE TABLE IF NOT EXISTS cross_lottery_sources (
            lottery_id TEXT PRIMARY KEY,
            lottery_name TEXT NOT NULL,
            jurisdiction TEXT NOT NULL,
            official_url TEXT NOT NULL,
            main_pool INTEGER,
            main_selected INTEGER,
            bonus_pool INTEGER,
            bonus_selected INTEGER,
            normalisation_status TEXT NOT NULL,
            local_history_path TEXT
        );

        CREATE TABLE IF NOT EXISTS gate_results (
            evaluated_at_utc TEXT NOT NULL,
            model_id TEXT NOT NULL,
            gate_name TEXT NOT NULL,
            passed INTEGER NOT NULL,
            evidence TEXT NOT NULL,
            PRIMARY KEY(evaluated_at_utc, model_id, gate_name)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at_utc TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            details_json TEXT
        );
        """
        with self.connect() as conn:
            conn.executescript(schema)

    def seed_draws(self, draws: Sequence[Draw]) -> int:
        values = [
            (
                d.draw_date,
                d.draw_id,
                *d.main,
                *d.euro,
                d.euro_pool,
                d.draw_day,
                "canonical_history_v3",
            )
            for d in draws
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO draws (
                    draw_date, draw_id, main_1, main_2, main_3, main_4, main_5,
                    euro_1, euro_2, euro_pool, draw_day, source_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        return len(values)

    def seed_sources(self) -> int:
        rows = [
            ("ej-official", "EuroJackpot", "EuroJackpot official results", "https://www.eurojackpot.com/", "html", "primary-current", "manual/generic-adapter", None),
            ("ej-sachsen", "EuroJackpot", "Sachsenlotto archive", "https://www.sachsenlotto.de/portal/zahlen-quoten/gewinnzahlen/download-archiv/gewinnzahlen_download.jsp", "archive", "historical-cross-check", "manual/download", None),
            ("ej-opap", "EuroJackpot", "OPAP EuroJackpot", "https://www.opap.gr/en/how-to-play-eurojackpot", "html", "Greek rules/price", "manual/generic-adapter", None),
            ("powerball", "Powerball", "Powerball previous results", "https://www.powerball.com/previous-results?game=pb", "html", "cross-lottery control", "generic-import", None),
            ("megamillions", "Mega Millions", "Mega Millions winning numbers", "https://www.megamillions.com/Winning-Numbers.aspx", "html", "cross-lottery control", "generic-import", None),
            ("euromillions", "EuroMillions", "EuroMillions official results", "https://www.euro-millions.com/results", "html", "cross-lottery control", "generic-import", None),
            ("joker-opap", "Joker Greece", "OPAP draw results", "https://corporate.opap.gr/", "html", "cross-lottery control", "generic-import", None),
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO sources (
                    source_id, lottery, source_name, source_url, source_type,
                    verification_role, adapter_status, last_checked_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def seed_cross_lottery_registry(self) -> int:
        rows = [
            ("eurojackpot", "EuroJackpot", "Europe", "https://www.eurojackpot.com/", 50, 5, 12, 2, "canonical-local", None),
            ("euromillions", "EuroMillions", "Europe", "https://www.euro-millions.com/results", 50, 5, 12, 2, "adapter-ready", None),
            ("powerball", "Powerball", "United States", "https://www.powerball.com/previous-results?game=pb", 69, 5, 26, 1, "adapter-ready", None),
            ("megamillions", "Mega Millions", "United States", "https://www.megamillions.com/Winning-Numbers.aspx", None, 5, None, 1, "rule-version-import-required", None),
            ("joker-gr", "Joker", "Greece", "https://corporate.opap.gr/", 45, 5, 20, 1, "adapter-ready", None),
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO cross_lottery_sources (
                    lottery_id, lottery_name, jurisdiction, official_url,
                    main_pool, main_selected, bonus_pool, bonus_selected,
                    normalisation_status, local_history_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def seed_models(self, models: Sequence[ModelRecord]) -> int:
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO models (
                    model_id, version, role, status, description,
                    brier, log_loss, calibration_error, prospective_draws, gate_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        m.model_id, m.version, m.role, m.status, m.description,
                        m.brier, m.log_loss, m.calibration_error,
                        m.prospective_draws, m.gate_status,
                    )
                    for m in models
                ],
            )
        return len(models)

    def freeze_prediction(self, record: PredictionRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO predictions (
                    record_hash, target_draw, data_cutoff, model_version,
                    champion_model, research_model, primary_main, primary_euro,
                    deployed_main_probability, deployed_euro_probability,
                    confidence_state, created_at_utc, code_hash, data_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_hash, record.target_draw, record.data_cutoff,
                    record.model_version, record.champion_model, record.research_model,
                    json.dumps(record.primary_main), json.dumps(record.primary_euro),
                    record.deployed_main_probability, record.deployed_euro_probability,
                    record.confidence_state, record.created_at_utc,
                    record.code_hash, record.data_hash,
                ),
            )

    def score_prediction(self, record_hash: str, result_main: Sequence[int], result_euro: Sequence[int]) -> dict[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT primary_main, primary_euro FROM predictions WHERE record_hash=?",
                (record_hash,),
            ).fetchone()
            if row is None:
                raise KeyError("prediction record not found")
            predicted_main = set(json.loads(row["primary_main"]))
            predicted_euro = set(json.loads(row["primary_euro"]))
            main_hits = len(predicted_main.intersection(result_main))
            euro_hits = len(predicted_euro.intersection(result_euro))
            conn.execute(
                """
                UPDATE predictions
                SET result_main=?, result_euro=?, main_hits=?, euro_hits=?, scored_at_utc=?
                WHERE record_hash=?
                """,
                (
                    json.dumps(sorted(result_main)), json.dumps(sorted(result_euro)),
                    main_hits, euro_hits, datetime.now(timezone.utc).isoformat(),
                    record_hash,
                ),
            )
        return {"main_hits": main_hits, "euro_hits": euro_hits}

    def log(self, category: str, status: str, message: str, details: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log(created_at_utc, category, status, message, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    category,
                    status,
                    message,
                    json.dumps(details or {}, sort_keys=True),
                ),
            )


def default_model_registry(v31_results: dict[str, Any] | None = None) -> list[ModelRecord]:
    main = (v31_results or {}).get("main_pool", {})
    euro = (v31_results or {}).get("euro_pool", {})
    return [
        ModelRecord(
            "uniform",
            "1.0",
            "champion",
            "DEPLOYED",
            "Exact fair-draw inclusion probability; mandatory fallback.",
            0.09,
            0.3250829733914482,
            0.0,
            0,
            "PASS",
        ),
        ModelRecord("super-learner", "3.3", "challenger", "RESEARCH", "Cross-fitted nonnegative stacking with uniform floor.", gate_status="FAIL"),
        ModelRecord("robust-stacking", "3.3", "challenger", "RESEARCH", "Worst-period distributionally robust ensemble.", gate_status="FAIL"),
        ModelRecord("dynamic-bayes", "3.3", "challenger", "RESEARCH", "Logistic-normal dynamic Bayesian state model.", gate_status="FAIL"),
        ModelRecord("regime-hmm", "3.3", "challenger", "RESEARCH", "Hidden-regime Bernoulli model.", gate_status="FAIL"),
        ModelRecord("interaction-ising", "3.3", "challenger", "RESEARCH", "Regularised maximum-entropy pair interaction model.", gate_status="FAIL"),
        ModelRecord("survival-hazard", "3.3", "challenger", "RESEARCH", "Gap hazard model compared with geometric null.", gate_status="FAIL"),
        ModelRecord("gp-drift", "3.3", "challenger", "RESEARCH", "Low-amplitude Gaussian-process drift model.", gate_status="FAIL"),
    ]


def prepare_prediction_record(
    history_path: str | Path,
    code_path: str | Path,
    primary_main: Sequence[int] = (4, 21, 35, 37, 42),
    primary_euro: Sequence[int] = (5, 7),
    target: date | None = None,
) -> PredictionRecord:
    draws = load_canonical_history(history_path)
    cutoff = draws[-1].draw_date
    target_date = target or next_draw_date(date.fromisoformat(cutoff))
    payload = {
        "target_draw": target_date.isoformat(),
        "data_cutoff": cutoff,
        "model_version": VERSION,
        "champion_model": "uniform-1.0",
        "research_model": "v3.3-advanced-ensemble",
        "primary_main": tuple(sorted(primary_main)),
        "primary_euro": tuple(sorted(primary_euro)),
        "deployed_main_probability": 5 / 50,
        "deployed_euro_probability": 2 / 12,
        "confidence_state": "Uniform mode; experimental line frozen",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_hash": sha256_file(code_path),
        "data_hash": sha256_file(history_path),
    }
    payload["record_hash"] = canonical_json_hash(payload)
    return PredictionRecord(**payload)


def power_analysis_mean_hits(
    pool_size: int,
    selected_in_line: int,
    winning_selected: int,
    improvements: Sequence[float],
    alpha: float = 0.05,
    powers: Sequence[float] = (0.80, 0.90),
    draws_per_year: int = 104,
) -> list[dict[str, Any]]:
    p = winning_selected / pool_size
    variance = selected_in_line * p * (1 - p) * ((pool_size - selected_in_line) / (pool_size - 1))
    z_alpha = norm.ppf(1 - alpha / 2)
    rows = []
    for effect in improvements:
        row: dict[str, Any] = {
            "effect": effect,
            "baseline_mean": selected_in_line * p,
            "variance": variance,
        }
        for power in powers:
            z_power = norm.ppf(power)
            n = math.ceil(((z_alpha + z_power) ** 2 * variance) / (effect ** 2))
            row[f"draws_{int(power*100)}"] = n
            row[f"years_{int(power*100)}"] = n / draws_per_year
        rows.append(row)
    return rows


def prospective_score_summary(db_path: str | Path) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT target_draw, main_hits, euro_hits
            FROM predictions
            WHERE main_hits IS NOT NULL AND euro_hits IS NOT NULL
            ORDER BY target_draw
            """
        ).fetchall()
    if not rows:
        return {
            "scored_draws": 0,
            "avg_main_hits": None,
            "avg_euro_hits": None,
            "main_baseline": 0.5,
            "euro_baseline": 1/3,
        }
    return {
        "scored_draws": len(rows),
        "avg_main_hits": float(np.mean([r["main_hits"] for r in rows])),
        "avg_euro_hits": float(np.mean([r["euro_hits"] for r in rows])),
        "main_baseline": 0.5,
        "euro_baseline": 1/3,
    }


def build_online_features(Y: np.ndarray, t: int) -> np.ndarray:
    if t <= 0:
        raise ValueError("t must be positive")
    hist = Y[:t]
    d = Y.shape[1]
    full = hist.mean(axis=0)
    r10 = hist[max(0, t-10):].mean(axis=0)
    r40 = hist[max(0, t-40):].mean(axis=0)
    gaps = np.zeros(d)
    for j in range(d):
        prior = np.flatnonzero(hist[:, j] > 0.5)
        gaps[j] = t - 1 - prior[-1] if len(prior) else t
    return np.column_stack([
        np.arange(1, d+1) / d,
        full,
        r10,
        r40,
        gaps / max(t, 1),
    ])


def build_feature_audit(Y: np.ndarray, start: int = 120) -> list[dict[str, Any]]:
    rows = []
    for t in range(start, len(Y), max(1, (len(Y)-start)//12)):
        X = build_online_features(Y, t)
        rows.append({
            "target_index": t,
            "feature_rows": int(X.shape[0]),
            "feature_cols": int(X.shape[1]),
            "uses_future_rows": False,
            "max_history_index": t - 1,
        })
    return rows


def leakage_scan(feature_matrix: np.ndarray, target: np.ndarray, timestamps: Sequence[int] | None = None, target_timestamp: int | None = None) -> dict[str, Any]:
    X = np.asarray(feature_matrix, dtype=float)
    y = np.asarray(target, dtype=float)
    suspicious = []
    for j in range(X.shape[1]):
        col = X[:, j]
        if np.std(col) <= 1e-12:
            corr = 0.0
        else:
            corr = float(np.corrcoef(col, y)[0, 1])
        if np.isfinite(corr) and abs(corr) > 0.98:
            suspicious.append({"column": j, "correlation": corr, "reason": "near-target correlation"})
    future_timestamp = False
    if timestamps is not None and target_timestamp is not None:
        future_timestamp = any(ts >= target_timestamp for ts in timestamps)
        if future_timestamp:
            suspicious.append({"column": None, "correlation": None, "reason": "feature timestamp is not before target"})
    return {
        "passed": len(suspicious) == 0,
        "suspicious": suspicious,
        "future_timestamp_violation": future_timestamp,
    }


def negative_control_experiment(Y: np.ndarray, start: int = 220, seed: int = 20260726) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    X_real, X_noise, y = [], [], []
    for t in range(start, len(Y)):
        online = build_online_features(Y, t)
        # Flatten each candidate-number row into independent binary examples.
        X_real.append(online)
        X_noise.append(rng.normal(size=online.shape))
        y.append(Y[t])
    X_real_arr = np.vstack(X_real)
    X_noise_arr = np.vstack(X_noise)
    y_arr = np.concatenate(y).astype(int)

    split = int(len(y_arr) * 0.75)
    uniform = float(np.mean(y_arr[:split]))
    results = {}
    for name, X in [("real_features", X_real_arr), ("random_noise", X_noise_arr)]:
        model = LogisticRegression(C=0.05, max_iter=500, solver="lbfgs")
        model.fit(X[:split], y_arr[:split])
        p = model.predict_proba(X[split:])[:, 1]
        results[name] = {
            "brier": float(brier_score_loss(y_arr[split:], p)),
            "mean_probability": float(np.mean(p)),
        }
    uniform_pred = np.full(len(y_arr) - split, uniform)
    results["uniform"] = {
        "brier": float(brier_score_loss(y_arr[split:], uniform_pred)),
        "mean_probability": uniform,
    }
    results["passed"] = (
        results["random_noise"]["brier"] >= results["real_features"]["brier"] - 1e-6
        and abs(results["random_noise"]["mean_probability"] - uniform) < 0.02
    )
    return results


def independent_combination_space() -> int:
    def choose(n: int, k: int) -> int:
        k = min(k, n-k)
        numerator = 1
        denominator = 1
        for i in range(1, k+1):
            numerator *= n - k + i
            denominator *= i
        return numerator // denominator
    return choose(50, 5) * choose(12, 2)


def independent_prize_probability(main_hits: int, euro_hits: int) -> float:
    return (
        math.comb(5, main_hits) * math.comb(45, 5-main_hits) / math.comb(50, 5)
        * math.comb(2, euro_hits) * math.comb(10, 2-euro_hits) / math.comb(12, 2)
    )


def verify_wheel_csv(path: str | Path, expected_lines: int, subset_size: int, selected_main_pool: Sequence[int]) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    signatures = set()
    covered = set()
    for row in rows:
        main = tuple(sorted(int(row[f"main_{i}"]) for i in range(1, 6)))
        euro = tuple(sorted(int(row[f"euro_{i}"]) for i in range(1, 3)))
        signatures.add(main + euro)
        covered.update(combinations(main, subset_size))
    required = set(combinations(sorted(selected_main_pool), subset_size))
    return {
        "path": str(path),
        "rows": len(rows),
        "expected_lines": expected_lines,
        "unique_lines": len(signatures),
        "required_subsets": len(required),
        "covered_subsets": len(required.intersection(covered)),
        "missing_subsets": len(required - covered),
        "passed": len(rows) == expected_lines and len(signatures) == expected_lines and required.issubset(covered),
    }


def verify_registry_record(record: PredictionRecord) -> dict[str, Any]:
    payload = asdict(record)
    supplied = payload.pop("record_hash")
    computed = canonical_json_hash(payload)
    return {"supplied_hash": supplied, "computed_hash": computed, "passed": supplied == computed}


def portfolio_frontier(line_cost: float = LINE_COST_EUR) -> list[dict[str, Any]]:
    tiers = [
        ("Frozen original", 5, "Five frozen lines", "None"),
        ("Diversified 10", 10, "Low-overlap experimental portfolio", "None"),
        ("Diversified 20", 20, "Expanded low-overlap portfolio", "None"),
        ("Compact pair wheel", 54, "All selected-pool main pairs × 4-number Euro pairs", "Conditional ≥2+2"),
        ("Extended pair wheel", 135, "All selected-pool main pairs × 6-number Euro pairs", "Conditional ≥2+2"),
        ("Compact triple wheel", 198, "All selected-pool main triples × 4-number Euro pairs", "Conditional ≥3+2"),
        ("Extended triple wheel", 495, "All selected-pool main triples × 6-number Euro pairs", "Conditional ≥3+2"),
        ("Full selected-pool wheel", 11880, "All 5-subsets of 12 × all 2-subsets of 6", "Conditional exact 5+2"),
    ]
    return [
        {
            "tier": tier,
            "lines": lines,
            "cost_eur": lines * line_cost,
            "jackpot_probability": lines / COMBINATION_SPACE,
            "coverage_multiple": lines,
            "strategy": strategy,
            "guarantee": guarantee,
        }
        for tier, lines, strategy, guarantee in tiers
    ]


def cross_lottery_normalized_features(
    draws: Sequence[Sequence[int]],
    pool_size: int,
    selected: int,
) -> np.ndarray:
    features = []
    for draw in draws:
        vals = np.asarray(sorted(draw), dtype=float)
        features.append([
            vals.sum() / (selected * pool_size),
            np.sum(vals % 2) / selected,
            np.sum(vals <= pool_size / 2) / selected,
            (vals.max() - vals.min()) / max(pool_size - 1, 1),
            np.sum(np.diff(vals) == 1) / max(selected - 1, 1),
        ])
    return np.asarray(features, dtype=float)


def cross_lottery_control_comparison(
    eurojackpot_draws: Sequence[Draw],
    control_draws: Sequence[Sequence[int]] | None = None,
    control_pool: int = 69,
    control_selected: int = 5,
    seed: int = 20260726,
) -> dict[str, Any]:
    ej = cross_lottery_normalized_features([d.main for d in eurojackpot_draws], 50, 5)
    if control_draws is None:
        rng = np.random.default_rng(seed)
        control_draws = [sorted(rng.choice(control_pool, control_selected, replace=False) + 1) for _ in range(len(ej))]
        control_status = "synthetic-control"
    else:
        control_status = "imported-control"
    ctl = cross_lottery_normalized_features(control_draws, control_pool, control_selected)
    diff = ej.mean(axis=0) - ctl.mean(axis=0)
    return {
        "control_status": control_status,
        "features": ["normalised_sum", "odd_ratio", "low_ratio", "normalised_range", "consecutive_ratio"],
        "eurojackpot_mean": ej.mean(axis=0).tolist(),
        "control_mean": ctl.mean(axis=0).tolist(),
        "difference": diff.tolist(),
        "max_abs_difference": float(np.max(np.abs(diff))),
    }


def promotion_gate(
    prospective_draws: int,
    brier_better: bool,
    log_loss_better: bool,
    calibration_ok: bool,
    periods_positive: bool,
    bootstrap_positive: bool,
    corrected_p: float,
    uniform_excluded_mcs: bool,
    sequential_e_value: float,
    stable_future: bool,
) -> dict[str, Any]:
    gates = {
        "minimum_prospective_draws": prospective_draws >= 200,
        "brier_better": brier_better,
        "log_loss_better": log_loss_better,
        "calibration_ok": calibration_ok,
        "periods_positive": periods_positive,
        "bootstrap_positive": bootstrap_positive,
        "corrected_p_below_0_05": corrected_p < 0.05,
        "uniform_excluded_mcs": uniform_excluded_mcs,
        "sequential_e_value_at_least_20": sequential_e_value >= 20,
        "stable_future": stable_future,
    }
    return {
        "passed": all(gates.values()),
        "gates": gates,
        "decision": "PROMOTE" if all(gates.values()) else "KEEP UNIFORM CHAMPION",
    }


def run_operational_selftest(
    history_path: str | Path,
    db_path: str | Path,
    code_path: str | Path,
    v31_results_path: str | Path,
    wheel_paths: dict[str, tuple[str | Path, int, int]],
) -> dict[str, Any]:
    draws = load_canonical_history(history_path)
    main, euro, _ = incidence_matrices(draws)
    db = OperationalDatabase(db_path)
    db.initialize()
    seeded_draws = db.seed_draws(draws)
    seeded_sources = db.seed_sources()
    seeded_cross = db.seed_cross_lottery_registry()
    v31 = json.loads(Path(v31_results_path).read_text(encoding="utf-8"))
    models = default_model_registry(v31)
    seeded_models = db.seed_models(models)

    prediction = prepare_prediction_record(history_path, code_path, target=date(2026, 7, 28))
    db.freeze_prediction(prediction)
    registry_check = verify_registry_record(prediction)

    power_main = power_analysis_mean_hits(50, 5, 5, [0.005, 0.01, 0.015, 0.02, 0.03, 0.05])
    power_euro = power_analysis_mean_hits(12, 2, 2, [0.005, 0.01, 0.02, 0.03, 0.05])

    feature_audit = build_feature_audit(main)
    negative_controls = negative_control_experiment(main)

    safe_features = build_online_features(main, 300)
    safe_target = main[300]
    safe_scan = leakage_scan(safe_features, safe_target, timestamps=list(range(300)), target_timestamp=300)
    leaked_features = np.column_stack([safe_features, safe_target])
    leaked_scan = leakage_scan(leaked_features, safe_target, timestamps=list(range(301)), target_timestamp=300)

    wheels = {
        name: verify_wheel_csv(path, expected, subset, [4, 21, 25, 27, 28, 35, 36, 37, 42, 44, 48, 50])
        for name, (path, expected, subset) in wheel_paths.items()
    }

    independent = {
        "combination_space_main_engine": COMBINATION_SPACE,
        "combination_space_independent": independent_combination_space(),
        "combination_space_passed": COMBINATION_SPACE == independent_combination_space(),
        "jackpot_probability": independent_prize_probability(5, 2),
        "wheel_checks": wheels,
        "registry_check": registry_check,
        "all_passed": (
            COMBINATION_SPACE == independent_combination_space()
            and registry_check["passed"]
            and all(x["passed"] for x in wheels.values())
        ),
    }

    cross_control = cross_lottery_control_comparison(draws)
    frontier = portfolio_frontier()
    champion = promotion_gate(
        prospective_draws=0,
        brier_better=False,
        log_loss_better=False,
        calibration_ok=False,
        periods_positive=False,
        bootstrap_positive=False,
        corrected_p=0.7107,
        uniform_excluded_mcs=False,
        sequential_e_value=0.0525,
        stable_future=False,
    )

    db.log("selftest", "PASS" if independent["all_passed"] else "FAIL", "Independent verification completed", independent)
    db.log("leakage", "PASS" if (safe_scan["passed"] and not leaked_scan["passed"]) else "FAIL", "Leakage challenge suite", {"safe": safe_scan, "leaked": leaked_scan})
    db.log("negative-control", "PASS" if negative_controls["passed"] else "FAIL", "Negative-control experiment", negative_controls)

    result = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": str(db_path),
        "seed_counts": {
            "draws": seeded_draws,
            "sources": seeded_sources,
            "cross_lottery_sources": seeded_cross,
            "models": seeded_models,
        },
        "prediction": asdict(prediction),
        "prospective_summary": prospective_score_summary(db_path),
        "champion_challenger": {
            "champion": asdict(models[0]),
            "challengers": [asdict(x) for x in models[1:]],
            "promotion_test": champion,
        },
        "power_analysis": {"main": power_main, "euro": power_euro},
        "negative_controls": negative_controls,
        "leakage_tests": {
            "feature_cutoff_audit": feature_audit,
            "safe_pipeline_scan": safe_scan,
            "deliberately_leaked_scan": leaked_scan,
            "passed": safe_scan["passed"] and not leaked_scan["passed"],
        },
        "independent_verification": independent,
        "cross_lottery_control": cross_control,
        "portfolio_frontier": frontier,
        "prize_tier_probabilities": prize_tier_probability_table(),
        "next_draw_schedule": {
            "pre_draw_days": ["Tuesday", "Friday"],
            "pre_draw_local_time": "18:30 Europe/Athens",
            "post_draw_action": "Verify result from two sources, append, score frozen records, update e-values.",
        },
    }
    return result

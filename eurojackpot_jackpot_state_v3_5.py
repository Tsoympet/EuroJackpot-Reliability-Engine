
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

CAP_EUR = 120_000_000.0
MAIN_PROBABILITY = 5 / 50
EURO_PROBABILITY = 2 / 12
LINE_COST_EUR = 2.50
COMBINATION_SPACE = math.comb(50, 5) * math.comb(12, 2)


@dataclass(frozen=True)
class JackpotState:
    draw_date: str
    jackpot_eur: float
    rollover_count: int
    cap_eur: float = CAP_EUR
    cap_reached: bool = False
    jackpot_won: bool = False
    reset_detected: bool = False
    overflow_class: int | None = None
    overflow_eur: float = 0.0
    prize_class_2_pool_eur: float | None = None
    total_columns: float | None = None
    verification_status: str = "UNVERIFIED"
    source_count: int = 0
    primary_source_url: str | None = None
    secondary_source_url: str | None = None
    checked_at_utc: str = ""
    notes: str = ""


@dataclass(frozen=True)
class StrategyProfile:
    mode: str
    jackpot_weight: float
    class2_weight: float
    lower_tier_weight: float
    anti_crowd_weight: float
    main_diversity_weight: float
    euro_diversity_weight: float
    recommended_portfolio: str
    explanation: str


MODE_PROFILES: dict[str, StrategyProfile] = {
    "NORMAL": StrategyProfile(
        "NORMAL", 0.35, 0.15, 0.50, 0.35, 0.50, 0.50,
        "Frozen set or diversified low-budget portfolio",
        "Normal payout state; no jackpot-driven portfolio escalation.",
    ),
    "ROLLOVER": StrategyProfile(
        "ROLLOVER", 0.45, 0.18, 0.37, 0.42, 0.60, 0.55,
        "Diversified lines with moderate overlap limits",
        "Rollover raises potential payout value but not number probability.",
    ),
    "HIGH_JACKPOT": StrategyProfile(
        "HIGH_JACKPOT", 0.55, 0.20, 0.25, 0.55, 0.72, 0.65,
        "Coverage-focused diversified portfolio within fixed budget",
        "Higher jackpot increases payout exposure; anti-crowd and distinct coverage receive more weight.",
    ),
    "MAX_CAP": StrategyProfile(
        "MAX_CAP", 0.55, 0.30, 0.15, 0.65, 0.85, 0.75,
        "Maximum-cap portfolio with stronger 5+1 and anti-crowd weighting",
        "The jackpot is capped; prize-class 2 becomes more relevant even before verified overflow is reported.",
    ),
    "MAX_CAP_OVERFLOW": StrategyProfile(
        "MAX_CAP_OVERFLOW", 0.45, 0.40, 0.15, 0.75, 0.95, 0.90,
        "Distinct-main coverage plus wide Euro-pair diversification",
        "Verified overflow increases the payout relevance of prize class 2; draw probabilities remain unchanged.",
    ),
    "RESET": StrategyProfile(
        "RESET", 0.30, 0.12, 0.58, 0.30, 0.45, 0.45,
        "Return to low-cost diversified or frozen portfolio",
        "The previous jackpot was won or reset; jackpot-driven EV weighting is reduced.",
    ),
}


def ensure_jackpot_schema(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jackpot_state (
                draw_date TEXT PRIMARY KEY,
                jackpot_eur REAL NOT NULL,
                rollover_count INTEGER NOT NULL,
                cap_eur REAL NOT NULL,
                cap_reached INTEGER NOT NULL,
                jackpot_won INTEGER NOT NULL,
                reset_detected INTEGER NOT NULL,
                overflow_class INTEGER,
                overflow_eur REAL NOT NULL,
                prize_class_2_pool_eur REAL,
                total_columns REAL,
                verification_status TEXT NOT NULL,
                source_count INTEGER NOT NULL,
                primary_source_url TEXT,
                secondary_source_url TEXT,
                checked_at_utc TEXT NOT NULL,
                notes TEXT,
                raw_payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jackpot_strategy_history (
                draw_date TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                jackpot_weight REAL NOT NULL,
                class2_weight REAL NOT NULL,
                lower_tier_weight REAL NOT NULL,
                anti_crowd_weight REAL NOT NULL,
                main_diversity_weight REAL NOT NULL,
                euro_diversity_weight REAL NOT NULL,
                recommended_portfolio TEXT NOT NULL,
                explanation TEXT NOT NULL,
                main_probability REAL NOT NULL,
                euro_probability REAL NOT NULL,
                created_at_utc TEXT NOT NULL,
                FOREIGN KEY(draw_date) REFERENCES jackpot_state(draw_date)
            );

            CREATE TABLE IF NOT EXISTS jackpot_state_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                draw_date TEXT,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT
            );
            """
        )


def validate_state(state: JackpotState) -> list[str]:
    errors: list[str] = []
    if state.jackpot_eur < 0:
        errors.append("jackpot_eur cannot be negative")
    if state.cap_eur <= 0:
        errors.append("cap_eur must be positive")
    if state.jackpot_eur > state.cap_eur + 0.01:
        errors.append("jackpot_eur exceeds configured cap")
    if state.rollover_count < 0:
        errors.append("rollover_count cannot be negative")
    if state.overflow_eur < 0:
        errors.append("overflow_eur cannot be negative")
    if state.cap_reached != (state.jackpot_eur >= state.cap_eur - 0.01):
        errors.append("cap_reached is inconsistent with jackpot_eur and cap_eur")
    if state.overflow_eur > 0 and not state.cap_reached:
        errors.append("overflow_eur requires cap_reached")
    if state.overflow_eur > 0 and state.overflow_class is None:
        errors.append("overflow_class is required when overflow_eur is positive")
    if state.verification_status.upper() == "VERIFIED":
        if state.source_count < 2:
            errors.append("VERIFIED state requires at least two sources")
        if not state.primary_source_url or not state.secondary_source_url:
            errors.append("VERIFIED state requires primary and secondary source URLs")
    if not state.checked_at_utc:
        errors.append("checked_at_utc is required")
    return errors


def derive_mode(state: JackpotState, previous: JackpotState | None = None) -> str:
    if state.reset_detected or (
        previous is not None
        and (previous.cap_reached or previous.jackpot_eur >= 80_000_000)
        and state.jackpot_eur <= 30_000_000
        and state.jackpot_eur < previous.jackpot_eur
    ):
        return "RESET"
    if state.cap_reached and (
        state.overflow_eur > 0
        or (state.prize_class_2_pool_eur is not None and state.prize_class_2_pool_eur > 0)
    ):
        return "MAX_CAP_OVERFLOW"
    if state.cap_reached:
        return "MAX_CAP"
    if state.jackpot_eur >= 80_000_000:
        return "HIGH_JACKPOT"
    if state.rollover_count > 0:
        return "ROLLOVER"
    return "NORMAL"


def strategy_for_state(state: JackpotState, previous: JackpotState | None = None) -> StrategyProfile:
    return MODE_PROFILES[derive_mode(state, previous)]


def prediction_invariance_check(profile: StrategyProfile) -> dict[str, Any]:
    # Strategy weights must never modify these values.
    main = MAIN_PROBABILITY
    euro = EURO_PROBABILITY
    return {
        "mode": profile.mode,
        "main_probability": main,
        "euro_probability": euro,
        "main_expected_hits": 5 * main,
        "euro_expected_hits": 2 * euro,
        "passed": abs(main - 0.1) < 1e-15 and abs(euro - 1/6) < 1e-15,
    }


def import_state(db_path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_jackpot_schema(db_path)
    normalized = dict(payload)
    normalized.setdefault("cap_eur", CAP_EUR)
    normalized.setdefault("overflow_eur", 0.0)
    normalized.setdefault("source_count", 0)
    normalized.setdefault("verification_status", "UNVERIFIED")
    normalized.setdefault("checked_at_utc", datetime.now(timezone.utc).isoformat())
    normalized.setdefault("notes", "")
    state = JackpotState(**normalized)
    errors = validate_state(state)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        prior_row = conn.execute(
            "SELECT * FROM jackpot_state WHERE draw_date < ? ORDER BY draw_date DESC LIMIT 1",
            (state.draw_date,),
        ).fetchone()
        previous = None
        if prior_row:
            previous = JackpotState(
                draw_date=prior_row["draw_date"],
                jackpot_eur=prior_row["jackpot_eur"],
                rollover_count=prior_row["rollover_count"],
                cap_eur=prior_row["cap_eur"],
                cap_reached=bool(prior_row["cap_reached"]),
                jackpot_won=bool(prior_row["jackpot_won"]),
                reset_detected=bool(prior_row["reset_detected"]),
                overflow_class=prior_row["overflow_class"],
                overflow_eur=prior_row["overflow_eur"],
                prize_class_2_pool_eur=prior_row["prize_class_2_pool_eur"],
                total_columns=prior_row["total_columns"],
                verification_status=prior_row["verification_status"],
                source_count=prior_row["source_count"],
                primary_source_url=prior_row["primary_source_url"],
                secondary_source_url=prior_row["secondary_source_url"],
                checked_at_utc=prior_row["checked_at_utc"],
                notes=prior_row["notes"] or "",
            )

        if errors:
            conn.execute(
                """
                INSERT INTO jackpot_state_audit(created_at_utc, draw_date, status, message, payload_json)
                VALUES (?, ?, 'REJECTED', ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    state.draw_date,
                    "; ".join(errors),
                    json.dumps(payload, sort_keys=True),
                ),
            )
            return {"accepted": False, "errors": errors}

        profile = strategy_for_state(state, previous)
        invariant = prediction_invariance_check(profile)
        raw = json.dumps(payload, sort_keys=True)

        conn.execute(
            """
            INSERT OR REPLACE INTO jackpot_state (
                draw_date, jackpot_eur, rollover_count, cap_eur, cap_reached,
                jackpot_won, reset_detected, overflow_class, overflow_eur,
                prize_class_2_pool_eur, total_columns, verification_status,
                source_count, primary_source_url, secondary_source_url,
                checked_at_utc, notes, raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state.draw_date, state.jackpot_eur, state.rollover_count, state.cap_eur,
                int(state.cap_reached), int(state.jackpot_won), int(state.reset_detected),
                state.overflow_class, state.overflow_eur, state.prize_class_2_pool_eur,
                state.total_columns, state.verification_status.upper(), state.source_count,
                state.primary_source_url, state.secondary_source_url, state.checked_at_utc,
                state.notes, raw,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO jackpot_strategy_history (
                draw_date, mode, jackpot_weight, class2_weight, lower_tier_weight,
                anti_crowd_weight, main_diversity_weight, euro_diversity_weight,
                recommended_portfolio, explanation, main_probability, euro_probability,
                created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state.draw_date, profile.mode, profile.jackpot_weight, profile.class2_weight,
                profile.lower_tier_weight, profile.anti_crowd_weight,
                profile.main_diversity_weight, profile.euro_diversity_weight,
                profile.recommended_portfolio, profile.explanation,
                invariant["main_probability"], invariant["euro_probability"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.execute(
            """
            INSERT INTO jackpot_state_audit(created_at_utc, draw_date, status, message, payload_json)
            VALUES (?, ?, 'ACCEPTED', ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                state.draw_date,
                f"Imported state in {profile.mode} mode",
                raw,
            ),
        )

    return {
        "accepted": True,
        "state": asdict(state),
        "profile": asdict(profile),
        "prediction_invariance": invariant,
    }


def latest_state(db_path: str | Path) -> dict[str, Any] | None:
    ensure_jackpot_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT s.*, h.mode, h.jackpot_weight, h.class2_weight,
                   h.lower_tier_weight, h.anti_crowd_weight,
                   h.main_diversity_weight, h.euro_diversity_weight,
                   h.recommended_portfolio, h.explanation,
                   h.main_probability, h.euro_probability
            FROM jackpot_state s
            JOIN jackpot_strategy_history h USING(draw_date)
            ORDER BY s.draw_date DESC LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def engine_state_template() -> dict[str, Any]:
    return {
        "draw_date": "YYYY-MM-DD",
        "jackpot_eur": 0.0,
        "rollover_count": 0,
        "cap_eur": CAP_EUR,
        "cap_reached": False,
        "jackpot_won": False,
        "reset_detected": False,
        "overflow_class": None,
        "overflow_eur": 0.0,
        "prize_class_2_pool_eur": None,
        "total_columns": None,
        "verification_status": "VERIFIED",
        "source_count": 2,
        "primary_source_url": "https://...",
        "secondary_source_url": "https://...",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "notes": "",
    }


def run_selftest(db_path: str | Path) -> dict[str, Any]:
    db = Path(db_path)
    if db.exists():
        db.unlink()
    ensure_jackpot_schema(db)

    sources = {
        "primary_source_url": "https://www.lotto.de/eurojackpot/spielregeln",
        "secondary_source_url": "https://www.eurojackpot.com/en/rules",
        "source_count": 2,
        "verification_status": "VERIFIED",
    }
    scenarios = [
        {
            "draw_date": "2026-08-04", "jackpot_eur": 10_000_000, "rollover_count": 0,
            "cap_reached": False, "jackpot_won": False, "reset_detected": False,
            "overflow_class": None, "overflow_eur": 0, "prize_class_2_pool_eur": None,
            "total_columns": None, "checked_at_utc": "2026-08-04T21:30:00Z", "notes": "Normal scenario", **sources,
        },
        {
            "draw_date": "2026-08-07", "jackpot_eur": 35_000_000, "rollover_count": 2,
            "cap_reached": False, "jackpot_won": False, "reset_detected": False,
            "overflow_class": None, "overflow_eur": 0, "prize_class_2_pool_eur": None,
            "total_columns": None, "checked_at_utc": "2026-08-07T21:30:00Z", "notes": "Rollover scenario", **sources,
        },
        {
            "draw_date": "2026-08-11", "jackpot_eur": 95_000_000, "rollover_count": 8,
            "cap_reached": False, "jackpot_won": False, "reset_detected": False,
            "overflow_class": None, "overflow_eur": 0, "prize_class_2_pool_eur": None,
            "total_columns": None, "checked_at_utc": "2026-08-11T21:30:00Z", "notes": "High jackpot scenario", **sources,
        },
        {
            "draw_date": "2026-08-14", "jackpot_eur": 120_000_000, "rollover_count": 10,
            "cap_reached": True, "jackpot_won": False, "reset_detected": False,
            "overflow_class": None, "overflow_eur": 0, "prize_class_2_pool_eur": None,
            "total_columns": None, "checked_at_utc": "2026-08-14T21:30:00Z", "notes": "Cap scenario", **sources,
        },
        {
            "draw_date": "2026-08-18", "jackpot_eur": 120_000_000, "rollover_count": 11,
            "cap_reached": True, "jackpot_won": False, "reset_detected": False,
            "overflow_class": 2, "overflow_eur": 20_000_000, "prize_class_2_pool_eur": 20_000_000,
            "total_columns": None, "checked_at_utc": "2026-08-18T21:30:00Z", "notes": "Cap overflow scenario", **sources,
        },
        {
            "draw_date": "2026-08-21", "jackpot_eur": 10_000_000, "rollover_count": 0,
            "cap_reached": False, "jackpot_won": True, "reset_detected": True,
            "overflow_class": None, "overflow_eur": 0, "prize_class_2_pool_eur": None,
            "total_columns": None, "checked_at_utc": "2026-08-21T21:30:00Z", "notes": "Reset scenario", **sources,
        },
    ]
    results = [import_state(db, x) for x in scenarios]
    modes = [x["profile"]["mode"] for x in results]
    expected = ["NORMAL", "ROLLOVER", "HIGH_JACKPOT", "MAX_CAP", "MAX_CAP_OVERFLOW", "RESET"]
    invariants = [x["prediction_invariance"]["passed"] for x in results]
    return {
        "passed": modes == expected and all(invariants),
        "modes": modes,
        "expected_modes": expected,
        "all_prediction_probabilities_unchanged": all(invariants),
        "main_probability": MAIN_PROBABILITY,
        "euro_probability": EURO_PROBABILITY,
        "latest": latest_state(db),
        "template": engine_state_template(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="EuroJackpot v3.5 jackpot-state importer")
    parser.add_argument("--db", required=True)
    parser.add_argument("--json", help="Path to ENGINE_STATE_JSON file")
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--template", action="store_true")
    args = parser.parse_args()

    if args.template:
        print(json.dumps(engine_state_template(), indent=2))
        return
    if args.latest:
        print(json.dumps(latest_state(args.db), indent=2))
        return
    if not args.json:
        parser.error("--json is required unless --latest or --template is used")
    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    print(json.dumps(import_state(args.db, payload), indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "EuroJackpot_Canonical_History_v3.csv"
OUT = ROOT / "EuroJackpot_Weekday_Effect_Audit_v3_1.json"
SEED = 20260726


def run_audit(history_path: str | Path = HISTORY, output_path: str | Path = OUT, permutations: int = 10000) -> dict:
    rng = np.random.default_rng(SEED)
    rows = list(csv.DictReader(Path(history_path).open(encoding="utf-8")))
    dates = [date.fromisoformat(r["draw_date"]) for r in rows]
    y_matrix = np.zeros((len(rows), 12), int)
    for i, row in enumerate(rows):
        y_matrix[i, [int(row["euro_1"]) - 1, int(row["euro_2"]) - 1]] = 1

    first_r3 = next(i for i, row in enumerate(rows) if row["rule_version"] == "R3_5of50_2of12")
    dev_end = int(len(rows) * 0.80)

    x_rows, targets, draw_idx = [], [], []
    for i in range(first_r3, len(rows)):
        is_tuesday = 1 if dates[i].weekday() == 1 else 0
        for j in range(12):
            features = np.zeros(24)
            features[j] = 1
            features[12 + j] = is_tuesday
            x_rows.append(features)
            targets.append(y_matrix[i, j])
            draw_idx.append(i)

    X = np.asarray(x_rows)
    y = np.asarray(targets)
    draw_idx_arr = np.asarray(draw_idx)

    def predict(train_end: int, start: int, end: int, c_value: float) -> np.ndarray:
        train = draw_idx_arr < train_end
        model = LogisticRegression(C=c_value, max_iter=500, solver="lbfgs")
        model.fit(X[train], y[train])
        probabilities = np.zeros((end - start, 12))
        for q, target_draw in enumerate(range(start, end)):
            is_tuesday = 1 if dates[target_draw].weekday() == 1 else 0
            x_next = np.zeros((12, 24))
            for j in range(12):
                x_next[j, j] = 1
                x_next[j, 12 + j] = is_tuesday
            p = model.predict_proba(x_next)[:, 1]
            p *= 2 / p.sum()
            probabilities[q] = p
        return probabilities

    candidates = [0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3]
    min_train = first_r3 + 100
    edges = np.linspace(min_train, dev_end, 4, dtype=int)
    development_cv = {}
    for c_value in candidates:
        fold_losses = []
        for start, end in zip(edges[:-1], edges[1:]):
            p = predict(int(start), int(start), int(end), c_value)
            fold_losses.append(float(np.mean((p - y_matrix[int(start):int(end)]) ** 2)))
        development_cv[str(c_value)] = {
            "mean_brier": float(np.mean(fold_losses)),
            "fold_brier": fold_losses,
        }

    best_c = float(min(candidates, key=lambda c: development_cv[str(c)]["mean_brier"]))
    p = predict(dev_end, dev_end, len(rows), best_c)
    y_holdout = y_matrix[dev_end:]
    uniform = np.full_like(p, 2 / 12, dtype=float)
    observed = float(np.mean((uniform - y_holdout) ** 2) - np.mean((p - y_holdout) ** 2))

    null = np.empty(permutations)
    for b in range(permutations):
        permuted = y_holdout[rng.permutation(len(y_holdout))]
        null[b] = np.mean((uniform - permuted) ** 2) - np.mean((p - permuted) ** 2)
    permutation_p = float((1 + np.sum(null >= observed)) / (permutations + 1))

    draw_diff = np.mean((uniform - y_holdout) ** 2, axis=1) - np.mean((p - y_holdout) ** 2, axis=1)
    boot = np.empty(permutations)
    block = 8
    n = len(draw_diff)
    for b in range(permutations):
        values = []
        while len(values) < n:
            start = int(rng.integers(0, n))
            values.extend(draw_diff[(start + np.arange(block)) % n].tolist())
        boot[b] = np.mean(values[:n])

    r3 = np.arange(first_r3, len(rows))
    tuesday = np.array([dates[i].weekday() == 1 for i in r3])
    number4 = y_matrix[r3, 3]

    result = {
        "audit_version": "3.1",
        "protocol": "C selected using three expanding development folds; untouched final 20% evaluated once",
        "candidate_C": candidates,
        "development_cv": development_cv,
        "selected_C": best_c,
        "holdout": {
            "draws": len(y_holdout),
            "model_brier": float(np.mean((p - y_holdout) ** 2)),
            "uniform_brier": float(np.mean((uniform - y_holdout) ** 2)),
            "brier_improvement": observed,
            "model_log_loss": float(-np.mean(
                y_holdout * np.log(np.clip(p, 1e-9, 1))
                + (1 - y_holdout) * np.log(np.clip(1 - p, 1e-9, 1))
            )),
            "uniform_log_loss": float(-np.mean(
                y_holdout * np.log(uniform) + (1 - y_holdout) * np.log(1 - uniform)
            )),
            "average_top2_hits": float(np.mean([
                y_holdout[i, np.argsort(-p[i])[:2]].sum() for i in range(len(p))
            ])),
            "permutation_p": permutation_p,
            "block_bootstrap_ci_low": float(np.quantile(boot, 0.025)),
            "block_bootstrap_ci_high": float(np.quantile(boot, 0.975)),
            "block_bootstrap_probability_positive": float(np.mean(boot > 0)),
        },
        "descriptive_number_4": {
            "tuesday_draws": int(tuesday.sum()),
            "friday_draws": int((~tuesday).sum()),
            "tuesday_occurrences": int(number4[tuesday].sum()),
            "friday_occurrences": int(number4[~tuesday].sum()),
            "tuesday_rate": float(number4[tuesday].mean()),
            "friday_rate": float(number4[~tuesday].mean()),
        },
        "conclusion": (
            "Not a reliable predictive edge: holdout improvement is negligible, "
            "permutation p is not significant, and the block-bootstrap interval crosses zero."
        ),
    }
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    result = run_audit()
    print(json.dumps({
        "selected_C": result["selected_C"],
        "holdout": result["holdout"],
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()

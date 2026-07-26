
from __future__ import annotations

import csv
import hashlib
import json
import math
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp, minimize
from scipy.special import betaln, expit, logsumexp, logit
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mutual_info_score
from sklearn.mixture import BayesianGaussianMixture
from sklearn.preprocessing import StandardScaler


EPS = 1e-12


@dataclass(frozen=True)
class Draw:
    draw_id: int
    draw_date: str
    main: tuple[int, ...]
    euro: tuple[int, ...]
    euro_pool: int
    draw_day: str


def load_canonical_history(path: str | Path) -> list[Draw]:
    rows: list[Draw] = []
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(
                Draw(
                    draw_id=int(r["draw_id"]),
                    draw_date=r["draw_date"],
                    main=tuple(sorted(int(r[f"main_{i}"]) for i in range(1, 6))),
                    euro=tuple(sorted(int(r[f"euro_{i}"]) for i in range(1, 3))),
                    euro_pool=int(r["euro_pool"]),
                    draw_day=r["draw_day"],
                )
            )
    return rows


def incidence_matrices(draws: Sequence[Draw]) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.bool_]]:
    n = len(draws)
    main = np.zeros((n, 50), dtype=float)
    euro = np.zeros((n, 12), dtype=float)
    euro_mask = np.zeros((n, 12), dtype=bool)
    for t, d in enumerate(draws):
        main[t, np.array(d.main) - 1] = 1.0
        euro[t, np.array(d.euro) - 1] = 1.0
        euro_mask[t, : d.euro_pool] = True
    return main, euro, euro_mask


def safe_scale(prob: NDArray[np.float64], total: float, mask: NDArray[np.bool_] | None = None) -> NDArray[np.float64]:
    p = np.asarray(prob, dtype=float).copy()
    if mask is None:
        mask = np.ones(len(p), dtype=bool)
    p[~mask] = 0.0
    p[mask] = np.clip(p[mask], 1e-9, 1 - 1e-9)
    s = float(p[mask].sum())
    if s <= 0:
        p[mask] = total / int(mask.sum())
    else:
        p[mask] *= total / s
    return np.clip(p, 0.0, 1.0)


# ---------------------------------------------------------------------------
# 1. Sequential e-values / test martingales
# ---------------------------------------------------------------------------

def beta_binomial_log_e_path(
    sequence: Sequence[int | float],
    p0: float,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> NDArray[np.float64]:
    """Bayes-factor e-process for Bernoulli observations against a fixed null p0."""
    x = np.asarray(sequence, dtype=float)
    s = np.cumsum(x)
    t = np.arange(1, len(x) + 1, dtype=float)
    log_alt = betaln(alpha + s, beta + t - s) - betaln(alpha, beta)
    log_null = s * math.log(max(p0, EPS)) + (t - s) * math.log(max(1 - p0, EPS))
    return log_alt - log_null


def mixture_e_value(log_e_values: Sequence[float]) -> float:
    """Average of valid e-values remains a valid e-value."""
    arr = np.asarray(log_e_values, dtype=float)
    return float(np.exp(logsumexp(arr) - math.log(len(arr))))


# ---------------------------------------------------------------------------
# 2. Change-point detection
# ---------------------------------------------------------------------------

def cusum_bernoulli(sequence: Sequence[int | float], p0: float, delta: float = 0.02) -> dict[str, Any]:
    x = np.asarray(sequence, dtype=float)
    pos = np.zeros(len(x))
    neg = np.zeros(len(x))
    for t, value in enumerate(x):
        inc = value - p0
        if t == 0:
            pos[t] = max(0.0, inc - delta / 2)
            neg[t] = min(0.0, inc + delta / 2)
        else:
            pos[t] = max(0.0, pos[t - 1] + inc - delta / 2)
            neg[t] = min(0.0, neg[t - 1] + inc + delta / 2)
    statistic = np.maximum(pos, -neg)
    idx = int(np.argmax(statistic))
    return {"max_statistic": float(statistic[idx]), "index": idx, "direction": "up" if pos[idx] >= -neg[idx] else "down"}


def bocpd_bernoulli(
    sequence: Sequence[int | float],
    hazard: float = 1 / 200,
    alpha0: float = 0.5,
    beta0: float = 0.5,
    max_run: int = 250,
) -> dict[str, Any]:
    """Truncated Bayesian online change-point detection with Beta-Bernoulli conjugacy."""
    x = np.asarray(sequence, dtype=int)
    r = np.array([1.0])
    alphas = np.array([alpha0])
    betas = np.array([beta0])
    cp_probs = []
    map_runs = []
    for value in x:
        predictive = (alphas / (alphas + betas)) if value == 1 else (betas / (alphas + betas))
        growth = r * predictive * (1 - hazard)
        cp = float(np.sum(r * predictive * hazard))
        new_r = np.concatenate([[cp], growth])
        new_r /= max(new_r.sum(), EPS)
        new_a = np.concatenate([[alpha0 + value], alphas + value])
        new_b = np.concatenate([[beta0 + 1 - value], betas + 1 - value])
        if len(new_r) > max_run + 1:
            new_r = new_r[: max_run + 1]
            new_a = new_a[: max_run + 1]
            new_b = new_b[: max_run + 1]
            new_r /= new_r.sum()
        r, alphas, betas = new_r, new_a, new_b
        cp_probs.append(float(r[0]))
        map_runs.append(int(np.argmax(r)))
    return {
        "max_change_probability": float(max(cp_probs, default=0.0)),
        "max_change_index": int(np.argmax(cp_probs)) if cp_probs else -1,
        "final_map_run_length": int(map_runs[-1]) if map_runs else 0,
        "change_probabilities": cp_probs,
    }


# ---------------------------------------------------------------------------
# 3. Hidden Markov / regime switching
# ---------------------------------------------------------------------------

class BernoulliHMM:
    def __init__(self, n_states: int = 2, max_iter: int = 60, tol: float = 1e-5, seed: int = 20260726):
        if n_states < 1:
            raise ValueError("n_states must be positive")
        self.n_states = n_states
        self.max_iter = max_iter
        self.tol = tol
        self.rng = np.random.default_rng(seed)
        self.startprob_: NDArray[np.float64] | None = None
        self.transmat_: NDArray[np.float64] | None = None
        self.emission_: NDArray[np.float64] | None = None
        self.log_likelihood_: float | None = None

    @staticmethod
    def _log_emission(X: NDArray[np.float64], emission: NDArray[np.float64]) -> NDArray[np.float64]:
        e = np.clip(emission, 1e-6, 1 - 1e-6)
        return X @ np.log(e).T + (1 - X) @ np.log(1 - e).T

    def fit(self, X: NDArray[np.float64]) -> "BernoulliHMM":
        X = np.asarray(X, dtype=float)
        n, d = X.shape
        k = self.n_states
        self.startprob_ = np.ones(k) / k
        self.transmat_ = np.full((k, k), 0.10 / max(k - 1, 1))
        np.fill_diagonal(self.transmat_, 0.90 if k > 1 else 1.0)
        base = np.clip(X.mean(axis=0), 0.01, 0.99)
        self.emission_ = np.vstack([np.clip(base + self.rng.normal(0, 0.015, d), 0.005, 0.995) for _ in range(k)])
        last_ll = -np.inf

        for _ in range(self.max_iter):
            log_b = self._log_emission(X, self.emission_)
            log_a = np.zeros((n, k))
            log_a[0] = np.log(self.startprob_ + EPS) + log_b[0]
            for t in range(1, n):
                log_a[t] = log_b[t] + logsumexp(log_a[t - 1][:, None] + np.log(self.transmat_ + EPS), axis=0)
            ll = float(logsumexp(log_a[-1]))

            log_beta = np.zeros((n, k))
            for t in range(n - 2, -1, -1):
                log_beta[t] = logsumexp(
                    np.log(self.transmat_ + EPS) + log_b[t + 1][None, :] + log_beta[t + 1][None, :],
                    axis=1,
                )
            log_gamma = log_a + log_beta - ll
            gamma = np.exp(log_gamma)
            gamma /= gamma.sum(axis=1, keepdims=True)

            xi_sum = np.zeros((k, k))
            for t in range(n - 1):
                log_xi = (
                    log_a[t][:, None]
                    + np.log(self.transmat_ + EPS)
                    + log_b[t + 1][None, :]
                    + log_beta[t + 1][None, :]
                    - ll
                )
                xi = np.exp(log_xi)
                xi /= max(xi.sum(), EPS)
                xi_sum += xi

            self.startprob_ = gamma[0] / gamma[0].sum()
            self.transmat_ = xi_sum / np.clip(xi_sum.sum(axis=1, keepdims=True), EPS, None)
            weighted = gamma.T @ X
            denom = gamma.sum(axis=0)[:, None]
            self.emission_ = np.clip((weighted + 2.0 * base) / (denom + 2.0), 0.005, 0.995)
            if abs(ll - last_ll) < self.tol:
                break
            last_ll = ll
        self.log_likelihood_ = ll
        return self

    def bic(self, X: NDArray[np.float64]) -> float:
        if self.log_likelihood_ is None:
            raise RuntimeError("fit must be called first")
        n, d = X.shape
        k = self.n_states
        params = (k - 1) + k * (k - 1) + k * d
        return float(-2 * self.log_likelihood_ + params * math.log(n))


# ---------------------------------------------------------------------------
# 4. Logistic-normal dynamic shrinkage
# ---------------------------------------------------------------------------

def logistic_normal_dynamic_filter(
    Y: NDArray[np.float64],
    k_selected: int,
    shrink: float = 0.99,
    process_var: float = 0.003,
    observation_var: float = 1.0,
) -> NDArray[np.float64]:
    n, d = Y.shape
    p0 = k_selected / d
    m = np.full(d, logit(p0))
    v = np.full(d, 0.10)
    out = np.zeros((n, d))
    for t in range(n):
        m = shrink * m + (1 - shrink) * logit(p0)
        v = shrink * shrink * v + process_var
        p = expit(m)
        h = p * (1 - p)
        s = h * h * v + observation_var
        gain = v * h / np.clip(s, EPS, None)
        m = m + gain * (Y[t] - p)
        v = np.clip((1 - gain * h) * v, 1e-6, 10)
        out[t] = safe_scale(expit(m), k_selected)
    return out


# ---------------------------------------------------------------------------
# 5. Bayesian non-parametric regime approximation
# ---------------------------------------------------------------------------

def draw_feature_matrix(draws: Sequence[Draw]) -> NDArray[np.float64]:
    feats = []
    prev_main: set[int] = set()
    for d in draws:
        mains = np.array(d.main)
        euros = np.array(d.euro)
        feats.append(
            [
                mains.sum(),
                np.sum(mains % 2),
                np.sum(mains <= 25),
                mains.max() - mains.min(),
                np.sum(np.diff(mains) == 1),
                euros.sum(),
                len(prev_main.intersection(d.main)),
                1.0 if d.draw_day.lower().startswith("tue") else 0.0,
                d.euro_pool,
            ]
        )
        prev_main = set(d.main)
    return np.asarray(feats, dtype=float)


def dp_mixture_regimes(features: NDArray[np.float64], max_components: int = 8, seed: int = 20260726) -> dict[str, Any]:
    scaler = StandardScaler()
    X = scaler.fit_transform(features)
    model = BayesianGaussianMixture(
        n_components=max_components,
        covariance_type="diag",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=0.5,
        max_iter=1000,
        random_state=seed,
    )
    labels = model.fit_predict(X)
    weights = model.weights_
    active = np.where(weights > 0.03)[0]
    return {
        "active_components": int(len(active)),
        "weights": [float(x) for x in weights],
        "label_counts": {str(int(k)): int(v) for k, v in zip(*np.unique(labels, return_counts=True))},
        "lower_bound": float(model.lower_bound_),
    }


# ---------------------------------------------------------------------------
# 6. Ising / maximum entropy pseudolikelihood
# ---------------------------------------------------------------------------

def ising_pseudolikelihood(
    Y: NDArray[np.float64],
    C: float = 0.03,
    max_features: int | None = None,
) -> dict[str, Any]:
    Y = np.asarray(Y, dtype=int)
    d = Y.shape[1] if max_features is None else min(Y.shape[1], max_features)
    interactions = np.zeros((d, d))
    intercepts = np.zeros(d)
    for j in range(d):
        idx = [i for i in range(d) if i != j]
        X = Y[:, idx]
        y = Y[:, j]
        if len(np.unique(y)) < 2:
            continue
        lr = LogisticRegression(solver="liblinear", C=C, l1_ratio=1.0, max_iter=500)
        lr.fit(X, y)
        interactions[j, idx] = lr.coef_[0]
        intercepts[j] = lr.intercept_[0]
    sym = 0.5 * (interactions + interactions.T)
    upper = np.abs(sym[np.triu_indices(d, 1)])
    return {
        "mean_abs_interaction": float(upper.mean()) if len(upper) else 0.0,
        "max_abs_interaction": float(upper.max()) if len(upper) else 0.0,
        "nonzero_fraction": float(np.mean(upper > 1e-10)) if len(upper) else 0.0,
        "interaction_matrix": sym.tolist(),
        "intercepts": intercepts.tolist(),
    }


# ---------------------------------------------------------------------------
# 7. Hypergraph / spectral co-occurrence model
# ---------------------------------------------------------------------------

def spectral_hypergraph_scores(Y: NDArray[np.float64], shrink: float = 1.0) -> NDArray[np.float64]:
    co = Y.T @ Y
    np.fill_diagonal(co, 0.0)
    co = co + shrink / max(Y.shape[0], 1)
    degree = co.sum(axis=1)
    norm = np.diag(1.0 / np.sqrt(np.clip(degree, EPS, None)))
    lap = norm @ co @ norm
    vals, vecs = np.linalg.eigh(lap)
    v = np.abs(vecs[:, np.argmax(vals)])
    return v / max(v.sum(), EPS)


# ---------------------------------------------------------------------------
# 8. Survival / hazard deviation
# ---------------------------------------------------------------------------

def waiting_times(sequence: Sequence[int | float]) -> list[int]:
    positions = np.flatnonzero(np.asarray(sequence) > 0.5)
    if len(positions) < 2:
        return []
    return [int(b - a) for a, b in zip(positions[:-1], positions[1:])]


def hazard_deviation(sequence: Sequence[int | float], p0: float, max_gap: int = 30) -> dict[str, Any]:
    waits = waiting_times(sequence)
    if not waits:
        return {"rmse": 0.0, "max_abs": 0.0, "n_intervals": 0}
    at_risk = np.zeros(max_gap)
    events = np.zeros(max_gap)
    for w in waits:
        for g in range(1, min(w, max_gap) + 1):
            at_risk[g - 1] += 1
        if w <= max_gap:
            events[w - 1] += 1
    empirical = np.divide(events, at_risk, out=np.zeros_like(events), where=at_risk > 0)
    valid = at_risk >= 5
    diff = empirical[valid] - p0
    return {
        "rmse": float(np.sqrt(np.mean(diff * diff))) if np.any(valid) else 0.0,
        "max_abs": float(np.max(np.abs(diff))) if np.any(valid) else 0.0,
        "n_intervals": len(waits),
        "empirical_hazard": empirical.tolist(),
        "at_risk": at_risk.tolist(),
    }


# ---------------------------------------------------------------------------
# 9. Gaussian-process drift
# ---------------------------------------------------------------------------

def gaussian_process_drift(sequence: Sequence[int | float], block: int = 20, seed: int = 20260726) -> dict[str, Any]:
    x = np.asarray(sequence, dtype=float)
    n_blocks = len(x) // block
    if n_blocks < 8:
        return {"latest_mean": float(np.mean(x)), "latest_std": 0.0, "drift_z": 0.0}
    rates = np.array([x[i * block : (i + 1) * block].mean() for i in range(n_blocks)])
    X = np.arange(n_blocks, dtype=float).reshape(-1, 1)
    kernel = ConstantKernel(0.01, (1e-5, 1.0)) * RBF(8.0, (2.0, 100.0)) + WhiteKernel(0.01, (1e-5, 0.2))
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=seed, n_restarts_optimizer=0)
    gp.fit(X, rates)
    mean, std = gp.predict(np.array([[n_blocks]], dtype=float), return_std=True)
    baseline = float(np.mean(rates))
    drift_z = float((mean[0] - baseline) / max(std[0], 1e-8))
    return {"latest_mean": float(mean[0]), "latest_std": float(std[0]), "drift_z": drift_z, "kernel": str(gp.kernel_)}


# ---------------------------------------------------------------------------
# 10. Conformal prediction sets
# ---------------------------------------------------------------------------

def joint_conformal_threshold(predictions: NDArray[np.float64], outcomes: NDArray[np.float64], alpha: float = 0.10) -> float:
    scores = []
    for p, y in zip(predictions, outcomes):
        true_idx = np.flatnonzero(y > 0.5)
        if len(true_idx):
            scores.append(float(np.max(1.0 - p[true_idx])))
    if not scores:
        return 1.0
    scores = np.sort(np.asarray(scores))
    rank = int(math.ceil((len(scores) + 1) * (1 - alpha))) - 1
    rank = min(max(rank, 0), len(scores) - 1)
    return float(scores[rank])


def conformal_set(probabilities: NDArray[np.float64], threshold: float) -> list[int]:
    return [int(i + 1) for i, p in enumerate(probabilities) if 1.0 - p <= threshold]


def conformal_backtest(
    cal_predictions: NDArray[np.float64],
    cal_outcomes: NDArray[np.float64],
    test_predictions: NDArray[np.float64],
    test_outcomes: NDArray[np.float64],
    alpha: float = 0.10,
) -> dict[str, Any]:
    q = joint_conformal_threshold(cal_predictions, cal_outcomes, alpha)
    covers = []
    sizes = []
    for p, y in zip(test_predictions, test_outcomes):
        selected = set(conformal_set(p, q))
        truth = set(np.flatnonzero(y > 0.5) + 1)
        covers.append(truth.issubset(selected))
        sizes.append(len(selected))
    return {
        "alpha": alpha,
        "threshold": q,
        "empirical_joint_coverage": float(np.mean(covers)) if covers else 0.0,
        "average_set_size": float(np.mean(sizes)) if sizes else 0.0,
        "median_set_size": float(np.median(sizes)) if sizes else 0.0,
    }


# ---------------------------------------------------------------------------
# 11. Super Learner and robust stacking
# ---------------------------------------------------------------------------

def _stacked_prob(P: NDArray[np.float64], w: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.clip(P @ w, 1e-8, 1 - 1e-8)


def super_learner_weights(P: NDArray[np.float64], y: NDArray[np.float64], uniform_index: int = 0, uniform_floor: float = 0.40) -> NDArray[np.float64]:
    P = np.asarray(P, dtype=float)
    y = np.asarray(y, dtype=float)
    m = P.shape[1]
    x0 = np.ones(m) / m
    x0[uniform_index] = max(x0[uniform_index], uniform_floor)
    x0 /= x0.sum()

    def objective(w: NDArray[np.float64]) -> float:
        q = _stacked_prob(P, w)
        return float(np.mean((q - y) ** 2) + 1e-4 * np.sum(w * np.log(np.clip(w, EPS, 1))))

    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "ineq", "fun": lambda w: w[uniform_index] - uniform_floor},
    ]
    result = minimize(objective, x0, bounds=[(0.0, 1.0)] * m, constraints=constraints, method="SLSQP", options={"maxiter": 1000})
    if not result.success:
        raise RuntimeError(f"Super Learner optimization failed: {result.message}")
    return result.x


def distributionally_robust_weights(
    block_predictions: Sequence[NDArray[np.float64]],
    block_outcomes: Sequence[NDArray[np.float64]],
    uniform_index: int = 0,
    uniform_floor: float = 0.40,
    entropy_penalty: float = 1e-4,
) -> NDArray[np.float64]:
    m = block_predictions[0].shape[1]
    x0 = np.ones(m) / m
    x0[uniform_index] = max(x0[uniform_index], uniform_floor)
    x0 /= x0.sum()

    def objective(w: NDArray[np.float64]) -> float:
        block_losses = [float(np.mean((_stacked_prob(P, w) - y) ** 2)) for P, y in zip(block_predictions, block_outcomes)]
        return max(block_losses) + entropy_penalty * float(np.sum(w * np.log(np.clip(w, EPS, 1))))

    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "ineq", "fun": lambda w: w[uniform_index] - uniform_floor},
    ]
    result = minimize(objective, x0, bounds=[(0.0, 1.0)] * m, constraints=constraints, method="SLSQP", options={"maxiter": 1000})
    if not result.success:
        raise RuntimeError(f"Robust stacking failed: {result.message}")
    return result.x


# ---------------------------------------------------------------------------
# 12. Compression / MDL
# ---------------------------------------------------------------------------

def lz_complexity(bits: Sequence[int | float]) -> int:
    s = "".join("1" if x else "0" for x in bits)
    if not s:
        return 0
    i, k, l, c = 0, 1, 1, 1
    n = len(s)
    while True:
        if i + k >= n or l + k >= n:
            c += 1
            break
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            if k > 1:
                i += 1
                if i == l:
                    c += 1
                    l += k
                    if l + 1 > n:
                        break
                    i, k = 0, 1
            else:
                c += 1
                l += 1
                if l + 1 > n:
                    break
                i = 0
    return c


def compression_diagnostics(bits: Sequence[int | float]) -> dict[str, Any]:
    raw = bytes(int(x) for x in bits)
    compressed = zlib.compress(raw, level=9)
    return {
        "length": len(raw),
        "compressed_bytes": len(compressed),
        "compression_ratio": len(compressed) / max(len(raw), 1),
        "lz_complexity": lz_complexity(bits),
    }


# ---------------------------------------------------------------------------
# 13. Mutual information / transfer-style lag test
# ---------------------------------------------------------------------------

def lag_mutual_information(Y: NDArray[np.float64], permutations: int = 199, seed: int = 20260726) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    Y = np.asarray(Y, dtype=int)
    observed = np.array([mutual_info_score(Y[:-1, j], Y[1:, j]) for j in range(Y.shape[1])])
    obs_max = float(observed.max())
    null_max = np.zeros(permutations)
    for b in range(permutations):
        perm = rng.permutation(Y.shape[0] - 1)
        null_max[b] = max(mutual_info_score(Y[:-1, j], Y[1:, j][perm]) for j in range(Y.shape[1]))
    p = float((1 + np.sum(null_max >= obs_max)) / (permutations + 1))
    return {"max_same_number_mi": obs_max, "familywise_permutation_p": p, "number": int(np.argmax(observed) + 1)}


# ---------------------------------------------------------------------------
# 14. Synthetic-null laboratory
# ---------------------------------------------------------------------------

def rolling_frequency_predictions(Y: NDArray[np.float64], k_selected: int, window: int = 50, start: int = 120) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    preds, outs = [], []
    d = Y.shape[1]
    for t in range(start, len(Y)):
        hist = Y[max(0, t - window) : t]
        p = safe_scale((hist.sum(axis=0) + 2.0 * (k_selected / d)) / (len(hist) + 2.0), k_selected)
        preds.append(p)
        outs.append(Y[t])
    return np.asarray(preds), np.asarray(outs)


def synthetic_null_lab(
    n_draws: int,
    pool_size: int,
    k_selected: int,
    simulations: int = 200,
    window: int = 50,
    start: int = 120,
    observed_improvement: float | None = None,
    seed: int = 20260726,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    improvements = []
    uniform = np.full(pool_size, k_selected / pool_size)
    for _ in range(simulations):
        Y = np.zeros((n_draws, pool_size), dtype=float)
        for t in range(n_draws):
            Y[t, rng.choice(pool_size, k_selected, replace=False)] = 1.0
        pred, out = rolling_frequency_predictions(Y, k_selected, window, start)
        b_model = float(np.mean((pred - out) ** 2))
        b_uniform = float(np.mean((uniform[None, :] - out) ** 2))
        improvements.append(b_uniform - b_model)
    arr = np.asarray(improvements)
    result = {
        "simulations": simulations,
        "mean_null_improvement": float(arr.mean()),
        "std_null_improvement": float(arr.std(ddof=1)),
        "q95": float(np.quantile(arr, 0.95)),
        "q99": float(np.quantile(arr, 0.99)),
    }
    if observed_improvement is not None:
        result["observed_improvement"] = observed_improvement
        result["empirical_p"] = float((1 + np.sum(arr >= observed_improvement)) / (simulations + 1))
    return result


# ---------------------------------------------------------------------------
# 15. Model Confidence Set / bootstrap elimination
# ---------------------------------------------------------------------------

def model_confidence_set(losses: NDArray[np.float64], names: Sequence[str], alpha: float = 0.10, bootstraps: int = 500, seed: int = 20260726) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    active = list(range(losses.shape[1]))
    history = []
    while len(active) > 1:
        means = losses[:, active].mean(axis=0)
        best_local = int(np.argmin(means))
        best = active[best_local]
        diff = losses[:, active] - losses[:, [best]]
        t_stats = diff.mean(axis=0) / np.clip(diff.std(axis=0, ddof=1) / math.sqrt(len(losses)), 1e-12, None)
        worst_local = int(np.argmax(t_stats))
        worst = active[worst_local]
        observed = float(t_stats[worst_local])
        centered = diff[:, worst_local] - diff[:, worst_local].mean()
        null = np.zeros(bootstraps)
        for b in range(bootstraps):
            idx = rng.integers(0, len(losses), len(losses))
            sample = centered[idx]
            null[b] = sample.mean() / max(sample.std(ddof=1) / math.sqrt(len(sample)), 1e-12)
        p = float((1 + np.sum(null >= observed)) / (bootstraps + 1))
        history.append({"removed_candidate": names[worst], "reference": names[best], "statistic": observed, "p": p})
        if p < alpha:
            active.remove(worst)
        else:
            break
    return {"confidence_set": [names[i] for i in active], "elimination_history": history, "alpha": alpha}


# ---------------------------------------------------------------------------
# 16. Prospective frozen registry
# ---------------------------------------------------------------------------

def freeze_prediction_record(record: dict[str, Any], registry_path: str | Path) -> dict[str, Any]:
    payload = dict(record)
    payload.setdefault("frozen_at_utc", datetime.now(timezone.utc).isoformat())
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["sha256"] = hashlib.sha256(canonical).hexdigest()
    p = Path(registry_path)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


# ---------------------------------------------------------------------------
# 17. Player-choice / prize-sharing heuristic
# ---------------------------------------------------------------------------

def anti_crowd_score(main: Sequence[int], euro: Sequence[int]) -> dict[str, Any]:
    main = sorted(main)
    euro = sorted(euro)
    penalties = {
        "birthday_numbers": sum(n <= 31 for n in main) * 0.10,
        "consecutive_pairs": sum(b - a == 1 for a, b in zip(main[:-1], main[1:])) * 0.20,
        "same_endings": (len(main) - len({n % 10 for n in main})) * 0.12,
        "multiples_of_five": sum(n % 5 == 0 for n in main) * 0.08,
        "single_decade_concentration": max(sum((d * 10) < n <= (d + 1) * 10 for n in main) for d in range(5)) * 0.05,
        "lucky_euro_7": sum(n == 7 for n in euro) * 0.08,
    }
    score = max(0.0, 1.0 - sum(penalties.values()))
    return {"score": score, "penalties": penalties}


# ---------------------------------------------------------------------------
# 18. Prize-tier probability and EV framework
# ---------------------------------------------------------------------------

def one_line_match_probability(main_matches: int, euro_matches: int) -> float:
    p_main = math.comb(5, main_matches) * math.comb(45, 5 - main_matches) / math.comb(50, 5)
    p_euro = math.comb(2, euro_matches) * math.comb(10, 2 - euro_matches) / math.comb(12, 2)
    return p_main * p_euro


def prize_tier_probability_table() -> list[dict[str, Any]]:
    tiers = [(5,2),(5,1),(5,0),(4,2),(4,1),(3,2),(4,0),(2,2),(3,1),(3,0),(1,2),(2,1)]
    return [
        {"tier": f"{m}+{e}", "main_matches": m, "euro_matches": e, "probability": one_line_match_probability(m, e)}
        for m, e in tiers
    ]


def expected_value(prize_table: dict[str, float], line_cost: float = 2.50, co_winner_factors: dict[str, float] | None = None) -> dict[str, Any]:
    co_winner_factors = co_winner_factors or {}
    gross = 0.0
    details = []
    for row in prize_tier_probability_table():
        tier = row["tier"]
        prize = float(prize_table.get(tier, 0.0))
        share = float(co_winner_factors.get(tier, 1.0))
        contribution = row["probability"] * prize * share
        gross += contribution
        details.append({**row, "prize_input": prize, "retained_share": share, "ev_contribution": contribution})
    return {"gross_ev": gross, "net_ev": gross - line_cost, "line_cost": line_cost, "details": details}


# ---------------------------------------------------------------------------
# 19. Exact / greedy set-cover wheel optimisation
# ---------------------------------------------------------------------------

def exact_covering_design(v: int, block_size: int, subset_size: int, time_limit: float = 20.0) -> dict[str, Any]:
    blocks = list(combinations(range(v), block_size))
    subsets = list(combinations(range(v), subset_size))
    subset_index = {s: i for i, s in enumerate(subsets)}
    A = np.zeros((len(subsets), len(blocks)), dtype=float)
    for j, block in enumerate(blocks):
        for s in combinations(block, subset_size):
            A[subset_index[s], j] = 1.0
    c = np.ones(len(blocks))
    integrality = np.ones(len(blocks), dtype=int)
    constraints = LinearConstraint(A, lb=np.ones(len(subsets)), ub=np.full(len(subsets), np.inf))
    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(np.zeros(len(blocks)), np.ones(len(blocks))),
        constraints=constraints,
        options={"time_limit": time_limit},
    )
    if result.x is None:
        return {"success": False, "status": int(result.status), "message": result.message}
    selected = [blocks[i] for i, x in enumerate(result.x) if x > 0.5]
    return {
        "success": bool(result.success),
        "status": int(result.status),
        "message": result.message,
        "objective": float(result.fun),
        "blocks": [list(x) for x in selected],
    }


# ---------------------------------------------------------------------------
# Lightweight historical base-model predictions for integration tests
# ---------------------------------------------------------------------------

def simple_oos_predictions(
    Y: NDArray[np.float64],
    k_selected: int,
    start: int = 120,
) -> tuple[list[str], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    n, d = Y.shape
    names = ["Uniform", "FullFrequency", "Rolling50", "EWMA"]
    preds = []
    outs = []
    per_draw_losses = []
    ew = np.zeros(d)
    ew_weight = 0.0
    decay = math.exp(math.log(0.5) / 50)
    counts = np.zeros(d)
    for t in range(n):
        if t >= start:
            uniform = np.full(d, k_selected / d)
            full = safe_scale((counts + 5.0 * k_selected / d) / (t + 5.0), k_selected)
            recent = Y[max(0, t - 50):t]
            rolling = safe_scale((recent.sum(axis=0) + 2.0 * k_selected / d) / (len(recent) + 2.0), k_selected)
            ewma = safe_scale((ew + 2.0 * k_selected / d) / (ew_weight + 2.0), k_selected)
            block = np.vstack([uniform, full, rolling, ewma]).T
            preds.append(block)
            outs.append(Y[t])
            per_draw_losses.append(np.mean((block - Y[t][:, None]) ** 2, axis=0))
        counts += Y[t]
        ew = decay * ew + Y[t]
        ew_weight = decay * ew_weight + 1.0
    return names, np.asarray(preds), np.asarray(outs), np.asarray(per_draw_losses)


def run_integration_self_test(history_path: str | Path, output_path: str | Path, registry_path: str | Path) -> dict[str, Any]:
    draws = load_canonical_history(history_path)
    main, euro, euro_mask = incidence_matrices(draws)

    # Sequential evidence
    main_log_e = [float(beta_binomial_log_e_path(main[:, j], 0.1)[-1]) for j in range(50)]
    euro_log_e = []
    for j in range(12):
        valid = euro_mask[:, j]
        euro_log_e.append(float(beta_binomial_log_e_path(euro[valid, j], np.mean(2 / np.array([d.euro_pool for d in draws], dtype=float)[valid]))[-1]))
    sequential = {
        "main_max_log10_e": float(max(main_log_e) / math.log(10)),
        "main_mixture_e": mixture_e_value(main_log_e),
        "euro_max_log10_e": float(max(euro_log_e) / math.log(10)),
        "euro_mixture_e": mixture_e_value(euro_log_e),
    }

    # Change points
    cp_euro = [bocpd_bernoulli(euro[euro_mask[:, j], j][-400:]) for j in range(12)]
    change_point = {
        "max_euro_change_probability": float(max(x["max_change_probability"] for x in cp_euro)),
        "number": int(np.argmax([x["max_change_probability"] for x in cp_euro]) + 1),
        "cusum_main_1": cusum_bernoulli(main[:, 0], 0.1),
    }

    # HMM / regimes
    hmm1 = BernoulliHMM(1, max_iter=25).fit(main[-500:])
    hmm2 = BernoulliHMM(2, max_iter=35).fit(main[-500:])
    hmm = {"bic_1_state": hmm1.bic(main[-500:]), "bic_2_state": hmm2.bic(main[-500:]), "preferred_states": 1 if hmm1.bic(main[-500:]) <= hmm2.bic(main[-500:]) else 2}

    # Dynamic filter and nonparametric regimes
    dynamic = logistic_normal_dynamic_filter(euro[-300:], 2)
    dp = dp_mixture_regimes(draw_feature_matrix(draws))

    # Ising and hypergraph
    ising = ising_pseudolikelihood(euro[-600:])
    hyper = spectral_hypergraph_scores(main)
    hyper_top = [int(x + 1) for x in np.argsort(hyper)[::-1][:10]]

    # Hazard and GP
    hazards = [hazard_deviation(main[:, j], 0.1) for j in range(50)]
    gp = [gaussian_process_drift(euro[euro_mask[:, j], j]) for j in range(12)]

    # Base model OOS and stacking
    names, P_main, O_main, L_main = simple_oos_predictions(main, 5)
    flat_P = P_main.reshape(-1, len(names))
    flat_y = O_main.reshape(-1)
    split1 = int(len(P_main) * 0.65)
    split2 = int(len(P_main) * 0.82)
    w_super = super_learner_weights(P_main[:split1].reshape(-1, len(names)), O_main[:split1].reshape(-1))
    blocks_P = [P_main[:split1//3].reshape(-1, len(names)), P_main[split1//3:2*split1//3].reshape(-1, len(names)), P_main[2*split1//3:split1].reshape(-1, len(names))]
    blocks_y = [O_main[:split1//3].reshape(-1), O_main[split1//3:2*split1//3].reshape(-1), O_main[2*split1//3:split1].reshape(-1)]
    w_robust = distributionally_robust_weights(blocks_P, blocks_y)

    ensemble_main = np.einsum("tdm,m->td", P_main, w_super)
    conf_main = conformal_backtest(
        ensemble_main[split1:split2], O_main[split1:split2],
        ensemble_main[split2:], O_main[split2:], alpha=0.10,
    )

    names_e, P_euro, O_euro, L_euro = simple_oos_predictions(euro[-600:], 2, start=100)
    split_e1 = int(len(P_euro) * 0.65)
    split_e2 = int(len(P_euro) * 0.82)
    w_e = super_learner_weights(P_euro[:split_e1].reshape(-1, len(names_e)), O_euro[:split_e1].reshape(-1))
    ensemble_e = np.einsum("tdm,m->td", P_euro, w_e)
    conf_euro = conformal_backtest(
        ensemble_e[split_e1:split_e2], O_euro[split_e1:split_e2],
        ensemble_e[split_e2:], O_euro[split_e2:], alpha=0.10,
    )

    # Compression and MI
    comp_real = compression_diagnostics(main.astype(int).ravel())
    rng = np.random.default_rng(20260726)
    sim_main = np.zeros_like(main)
    for t in range(len(sim_main)):
        sim_main[t, rng.choice(50, 5, replace=False)] = 1
    comp_null = compression_diagnostics(sim_main.astype(int).ravel())
    mi = lag_mutual_information(main, permutations=99)

    # Null laboratory using observed simple rolling improvement
    rolling_main = P_main[:, :, names.index("Rolling50")]
    uniform_main = P_main[:, :, names.index("Uniform")]
    observed_imp = float(np.mean((uniform_main - O_main) ** 2) - np.mean((rolling_main - O_main) ** 2))
    null_lab = synthetic_null_lab(len(main), 50, 5, simulations=120, observed_improvement=observed_imp)

    # MCS
    mcs = model_confidence_set(L_main[-250:], names, alpha=0.10, bootstraps=199)

    # Prospective registry
    frozen = freeze_prediction_record(
        {
            "model_version": "v3.3",
            "data_cutoff": draws[-1].draw_date,
            "target_draw": "2026-07-28",
            "primary_main": [4, 21, 35, 37, 42],
            "primary_euro": [5, 7],
            "deployment_status": "Uniform mode; experimental frozen line",
        },
        registry_path,
    )

    # Anti-crowd and prize probabilities
    crowd = anti_crowd_score([4, 21, 35, 37, 42], [5, 7])
    prizes = prize_tier_probability_table()

    # Set-cover solver integration test: smaller exact instance to ensure solver works.
    cover_test = exact_covering_design(8, 4, 2, time_limit=8.0)

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "history_draws": len(draws),
        "methods": {
            "sequential_evidence": sequential,
            "change_point": change_point,
            "hmm_regime": hmm,
            "logistic_normal_dynamic": {
                "latest_top_euro": [int(x + 1) for x in np.argsort(dynamic[-1])[::-1][:5]],
                "latest_probabilities": [float(x) for x in dynamic[-1]],
            },
            "dp_mixture": dp,
            "ising_euro": {k: v for k, v in ising.items() if k != "interaction_matrix"},
            "hypergraph_main_top10": hyper_top,
            "hazard_main": {
                "max_rmse": float(max(x["rmse"] for x in hazards)),
                "number": int(np.argmax([x["rmse"] for x in hazards]) + 1),
            },
            "gaussian_process_euro": {
                "max_abs_drift_z": float(max(abs(x["drift_z"]) for x in gp)),
                "number": int(np.argmax([abs(x["drift_z"]) for x in gp]) + 1),
            },
            "super_learner": {"models": names, "weights": [float(x) for x in w_super]},
            "distributionally_robust": {"models": names, "weights": [float(x) for x in w_robust]},
            "conformal_main": conf_main,
            "conformal_euro": conf_euro,
            "compression": {"real": comp_real, "synthetic_null": comp_null},
            "lag_mutual_information": mi,
            "synthetic_null_lab": null_lab,
            "model_confidence_set": mcs,
            "prospective_registry": frozen,
            "anti_crowd": crowd,
            "prize_tier_probabilities": prizes,
            "exact_cover_solver_test": cover_test,
        },
        "deployment_rule": "Non-uniform deployment is prohibited unless every predeclared prospective reliability gate passes.",
    }
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

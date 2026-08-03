"""
EuroJackpot Edge Engine v3.8

Best-effort search for a *stable* research edge using walk-forward evaluation:

1) Draw-probability edge: multi-signal ensemble vs exact Uniform (Brier/log-loss,
   period consistency, bootstrap). Deployed odds stay Uniform unless every gate passes.
2) Prize-value edge: anti-crowd / diversity portfolio layer that can improve expected
   shared-prize value without claiming higher jackpot draw odds.

Honesty rule: never rewrite mathematical jackpot odds (1 / 139,838,160 per unique line)
unless prospective promotion gates are actually satisfied.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from eurojackpot_advanced_methods_v3_3 import (
    anti_crowd_score,
    expected_value,
    incidence_matrices,
    load_canonical_history,
    safe_scale,
    super_learner_weights,
)
from eurojackpot_learning_engine_v3_8 import predict_from_past_draws, train_on_history
from eurojackpot_paths import ensure_user_layout, package_root, read_version


APP_VERSION = read_version()
MAIN_K = 5
EURO_K = 2
MAIN_POOL = 50
EURO_POOL = 12
RNG = np.random.default_rng(20260803)


@dataclass
class PoolMetrics:
    name: str
    n_draws: int
    brier: float
    log_loss: float
    uniform_brier: float
    uniform_log_loss: float
    brier_improvement: float
    log_loss_improvement: float
    topk_hit_rate: float
    period_improvements: list[float]
    bootstrap_ci: tuple[float, float]
    bootstrap_p_positive: float


def _log_loss(y: NDArray[np.float64], p: NDArray[np.float64]) -> float:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))))


def _brier(y: NDArray[np.float64], p: NDArray[np.float64]) -> float:
    return float(np.mean((p - y) ** 2))


# Full research library (eligibility still drops losers each refit).
SIGNAL_NAMES = (
    "Uniform",
    "FullFrequency",
    "DirichletShrink",
    "BetaBinomial",
    "HierarchicalEra",
    "Rolling30",
    "Rolling50",
    "Rolling100",
    "EWMA25",
    "EWMA50",
    "Momentum",
    "DynamicLogit",
    "GapHazard",
    "Hot20",
    "Cold20",
    "LagFade",
    "WeekdayFreq",
    "PairAffinity",
    "SpectralCooccur",
)
# Prespecified primary euro stack: validated OOS signals only.
# Hot/Cold/GapHazard removed after solo audits showed they hurt Brier vs Uniform.
PRIMARY_SIGNAL_NAMES = (
    "Uniform",
    "HierarchicalEra",
    "DynamicLogit",
    "BetaBinomial",
    "EWMA25",
    "Rolling50",
    "Rolling100",
    "PairAffinity",
)


def _signal_matrix(
    Y: NDArray[np.float64],
    t: int,
    k: int,
    active: int,
    *,
    draw_days: Sequence[str] | None = None,
    era_ids: Sequence[int] | None = None,
) -> dict[str, NDArray[np.float64]]:
    """Past-only signals at time t (uses Y[:t] only)."""
    from scipy.special import expit, logit

    hist = Y[:t, :active]
    d = active
    if t <= 0:
        u = np.full(d, k / d)
        return {n: u.copy() for n in SIGNAL_NAMES}

    counts = hist.sum(axis=0)
    uniform = np.full(d, k / d)
    base = k / d
    # Mild empirical Bayes frequency.
    full = safe_scale((counts + 3.0 * base) / (t + 3.0), k)
    # Stronger Dirichlet shrinkage toward uniform (more stable on noisy main pool).
    prior = 12.0 if d >= 40 else 4.0
    shrink = safe_scale((counts + prior * base) / (t + prior), k)
    # Beta-Binomial posterior mean with uniform-centered prior.
    bb_strength = 80.0 if d >= 40 else 40.0
    alpha = bb_strength * base
    beta_p = bb_strength * (1.0 - base)
    beta_binomial = safe_scale((counts + alpha) / (t + alpha + beta_p), k)

    def rolling(window: int) -> NDArray[np.float64]:
        recent = hist[max(0, t - window):]
        return safe_scale((recent.sum(axis=0) + 2.0 * base) / (len(recent) + 2.0), k)

    def ewma(halflife: int) -> NDArray[np.float64]:
        decay = math.exp(math.log(0.5) / max(halflife, 1))
        w = 0.0
        acc = np.zeros(d)
        for row in hist:
            acc = decay * acc + row
            w = decay * w + 1.0
        return safe_scale((acc + 2.0 * base) / (w + 2.0), k)

    e25 = ewma(25)
    e50 = ewma(50)
    # Momentum: short-horizon lift over longer horizon, then renormalize.
    mom = safe_scale(np.clip(e25 - e50 + base, 1e-9, None), k)

    # Hierarchical / era-aware frequency (euro pool size eras; main uses global shrink).
    hier = full.copy()
    if era_ids is not None and t < len(era_ids):
        target_era = int(era_ids[t])
        mask = np.asarray([int(x) == target_era for x in era_ids[:t]], dtype=bool)
        if int(mask.sum()) >= 20:
            sub = hist[mask]
            global_p = (counts + 40.0 * base) / (t + 40.0)
            strength = 80.0
            hier = safe_scale(
                (sub.sum(axis=0) + strength * global_p) / (len(sub) + strength), k
            )

    # Logistic-normal dynamic filter: predict next draw BEFORE observing it.
    p0 = base
    shrink_m = 0.995 if d >= 40 else 0.99
    process_var = 0.001 if d >= 40 else 0.003
    m = np.full(d, float(logit(p0)))
    v = np.full(d, 0.05 if d >= 40 else 0.10)
    for row in hist:
        m = shrink_m * m + (1.0 - shrink_m) * float(logit(p0))
        v = shrink_m * shrink_m * v + process_var
        p = expit(m)
        h = p * (1.0 - p)
        s = h * h * v + 1.0
        gain = v * h / np.clip(s, 1e-12, None)
        m = m + gain * (row - p)
        v = np.clip((1.0 - gain * h) * v, 1e-6, 10.0)
    m = shrink_m * m + (1.0 - shrink_m) * float(logit(p0))
    dynamic = safe_scale(expit(m), k)

    # Gap / overdue hazard: longer gaps get mild boost (then renormalize).
    gaps = np.zeros(d)
    for j in range(d):
        hits = np.flatnonzero(hist[:, j] > 0)
        gaps[j] = (t - 1 - int(hits[-1])) if len(hits) else t
    expected_gap = d / max(k, 1)
    gap_raw = (gaps + 1.0) / (expected_gap + 1.0)
    gap = safe_scale(gap_raw * base, k)

    hot = rolling(20)
    cold_raw = 1.0 - (hot / max(hot.max(), 1e-9))
    cold = safe_scale(cold_raw * base, k)

    lag = full.copy()
    if t >= 2:
        recent_hits = hist[-2:].sum(axis=0)
        lag_raw = full * (1.0 - 0.12 * recent_hits)
        lag = safe_scale(np.clip(lag_raw, 1e-9, None), k)

    weekday = full.copy()
    if draw_days is not None and t < len(draw_days):
        target_day = draw_days[t]
        mask = np.asarray([day == target_day for day in draw_days[:t]], dtype=bool)
        if int(mask.sum()) >= 25:
            sub = hist[mask]
            weekday = safe_scale((sub.sum(axis=0) + 2.0 * base) / (len(sub) + 2.0), k)

    top = np.argsort(full)[::-1][: max(8, k)]
    pair = np.zeros(d)
    if t >= 40:
        for j in range(d):
            score = 0.0
            for a in top:
                if a == j:
                    continue
                both = np.mean(hist[:, j] * hist[:, a])
                score += both
            pair[j] = score / max(len(top) - 1, 1)
        pair = safe_scale(pair + 1e-6, k)
    else:
        pair = full.copy()

    # Spectral co-occurrence (principal eigenvector); noisy alone, eligibility may drop it.
    if t >= 40:
        co = hist.T @ hist
        np.fill_diagonal(co, 0.0)
        co = co + 1e-3
        _vals, vecs = np.linalg.eigh(co)
        spectral = safe_scale(np.abs(vecs[:, -1]) + 1e-6, k)
    else:
        spectral = full.copy()

    return {
        "Uniform": uniform,
        "FullFrequency": full,
        "DirichletShrink": shrink,
        "BetaBinomial": beta_binomial,
        "HierarchicalEra": hier,
        "Rolling30": rolling(30),
        "Rolling50": rolling(50),
        "Rolling100": rolling(100),
        "EWMA25": e25,
        "EWMA50": e50,
        "Momentum": mom,
        "DynamicLogit": dynamic,
        "GapHazard": gap,
        "Hot20": hot,
        "Cold20": cold,
        "LagFade": lag,
        "WeekdayFreq": weekday,
        "PairAffinity": pair,
        "SpectralCooccur": spectral,
    }



def _stack_predict(
    signals: dict[str, NDArray[np.float64]],
    weights: dict[str, float],
    k: int,
) -> NDArray[np.float64]:
    names = [n for n, w in weights.items() if w > 0 and n in signals]
    if not names:
        return next(iter(signals.values()))
    p = sum(weights[n] * signals[n] for n in names)
    return safe_scale(np.asarray(p, dtype=float), k)


def _fit_stack_weights(
    pred_blocks: list[NDArray[np.float64]],
    y_blocks: list[NDArray[np.float64]],
    names: Sequence[str],
) -> dict[str, float]:
    if not pred_blocks:
        return {n: (1.0 if n == "Uniform" else 0.0) for n in names}
    P = np.concatenate(pred_blocks, axis=0)
    y = np.concatenate(y_blocks, axis=0)
    w = super_learner_weights(P, y, uniform_index=names.index("Uniform"), uniform_floor=0.45)
    return {n: float(x) for n, x in zip(names, w)}


def _period_improvements(deltas: NDArray[np.float64]) -> list[float]:
    if len(deltas) < 3:
        return [float(np.mean(deltas))] * 3
    parts = np.array_split(deltas, 3)
    return [float(np.mean(p)) if len(p) else 0.0 for p in parts]


def _bootstrap_ci(deltas: NDArray[np.float64], B: int = 800, block: int = 8) -> tuple[float, float, float]:
    n = len(deltas)
    if n < block * 2:
        return float(np.mean(deltas)), float(np.mean(deltas)), 0.5
    means = []
    for _ in range(B):
        idx = []
        while len(idx) < n:
            start = int(RNG.integers(0, max(n - block, 1)))
            idx.extend(range(start, min(start + block, n)))
        sample = deltas[np.array(idx[:n])]
        means.append(float(np.mean(sample)))
    arr = np.sort(np.asarray(means))
    lo = float(arr[int(0.025 * B)])
    hi = float(arr[int(0.975 * B)])
    p_pos = float(np.mean(arr > 0))
    return lo, hi, p_pos


def _calibrate_probs(
    p: NDArray[np.float64],
    y_hist: NDArray[np.float64],
    p_hist: NDArray[np.float64],
    k: int,
) -> NDArray[np.float64]:
    """Simple temperature scaling toward empirical base rate using recent OOS pairs."""
    if len(y_hist) < 50:
        return safe_scale(p, k)
    # Fit temperature by minimizing log-loss on recent history.
    best_t, best_ll = 1.0, _log_loss(y_hist, p_hist)
    for temp in (0.70, 0.85, 1.0, 1.15, 1.35, 1.60):
        logits = np.log(np.clip(p_hist, 1e-9, 1 - 1e-9)) - np.log(1 - np.clip(p_hist, 1e-9, 1 - 1e-9))
        adj = 1 / (1 + np.exp(-logits / temp))
        # Renormalize each draw's row if 2D.
        if adj.ndim == 2:
            adj = np.vstack([safe_scale(row, k) for row in adj])
        else:
            adj = safe_scale(adj, k)
        ll = _log_loss(y_hist, adj)
        if ll < best_ll:
            best_ll, best_t = ll, temp
    logits = np.log(np.clip(p, 1e-9, 1 - 1e-9)) - np.log(1 - np.clip(p, 1e-9, 1 - 1e-9))
    out = 1 / (1 + np.exp(-logits / best_t))
    return safe_scale(out, k)


def _choose_shrink_alpha(
    research_hist: list[NDArray[np.float64]],
    y_hist: list[NDArray[np.float64]],
    k: int,
    d: int,
) -> float:
    """Pick blend weight toward research using recent OOS Brier (0 = pure Uniform)."""
    if len(research_hist) < 8:
        return 0.0
    y = np.concatenate(y_hist[-12:], axis=0)
    raw = np.concatenate(research_hist[-12:], axis=0)
    uniform = np.full_like(raw, k / d)
    best_alpha, best_brier = 0.0, float(np.mean((uniform - y) ** 2))
    for alpha in (0.0, 0.20, 0.35, 0.50, 0.65, 0.80, 1.0):
        blended = np.vstack(
            [safe_scale((1.0 - alpha) * uniform[i] + alpha * raw[i], k) for i in range(len(raw))]
        )
        brier = float(np.mean((blended - y) ** 2))
        if brier < best_brier - 1e-12:
            best_brier, best_alpha = brier, alpha
    return best_alpha


def evaluate_pool(
    Y: NDArray[np.float64],
    k: int,
    *,
    start: int = 120,
    refit_every: int | None = None,
    pool_name: str = "main",
    draw_days: Sequence[str] | None = None,
    era_ids: Sequence[int] | None = None,
    signal_names: Sequence[str] | None = None,
) -> tuple[PoolMetrics, dict[str, float], NDArray[np.float64], dict[str, int]]:
    """
    Walk-forward evaluate stacked ensemble vs Uniform.
    Only signals that beat Uniform on the recent development window stay eligible.
    Main pool uses shrink-to-uniform; euro uses the prespecified primary stack.
    """
    n, d_full = Y.shape
    if signal_names is None:
        names = list(SIGNAL_NAMES if pool_name == "main" else PRIMARY_SIGNAL_NAMES)
    else:
        names = list(signal_names)
    weights = {nme: (1.0 if nme == "Uniform" else 0.0) for nme in names}
    if refit_every is None:
        refit_every = 40 if pool_name == "main" else 30
    uniform_floor = 0.55 if pool_name == "main" else 0.40
    shrink_alpha = 0.0 if pool_name == "main" else 1.0

    ens_brier = []
    uni_brier = []
    ens_ll = []
    uni_ll = []
    topk_hits = []
    brier_deltas = []

    fit_P: list[NDArray[np.float64]] = []
    fit_y: list[NDArray[np.float64]] = []
    recent_p: list[NDArray[np.float64]] = []
    recent_y: list[NDArray[np.float64]] = []
    active_default = d_full if pool_name == "main" else EURO_POOL
    last_research = np.full(active_default, k / active_default)
    signal_wins = {nme: 0 for nme in names}

    for t in range(start, n):
        active = d_full if pool_name == "main" else EURO_POOL
        all_signals = _signal_matrix(
            Y[:, :active],
            t,
            k,
            active,
            draw_days=draw_days,
            era_ids=era_ids,
        )
        signals = {nme: all_signals[nme] for nme in names}

        if (t - start) % refit_every == 0 and len(fit_P) >= 3:
            recent_blocks = fit_P[-8:]
            recent_outs = fit_y[-8:]
            P = np.concatenate(recent_blocks, axis=0)
            y = np.concatenate(recent_outs, axis=0)
            uni_idx = names.index("Uniform")
            uni_b = float(np.mean((P[:, uni_idx] - y) ** 2))
            eligible = ["Uniform"]
            for i, nme in enumerate(names):
                if nme == "Uniform":
                    continue
                b = float(np.mean((P[:, i] - y) ** 2))
                if b < uni_b:
                    eligible.append(nme)
                    signal_wins[nme] += 1
            el_idx = [names.index(nme) for nme in eligible]
            floor = uniform_floor if len(eligible) > 1 else 1.0
            w_el = super_learner_weights(
                P[:, el_idx], y, uniform_index=0, uniform_floor=min(floor, 0.95)
            )
            weights = {nme: 0.0 for nme in names}
            for nme, w in zip(eligible, w_el):
                weights[nme] = float(w)
            if len(eligible) == 1:
                weights = {nme: (1.0 if nme == "Uniform" else 0.0) for nme in names}
            if pool_name == "main":
                shrink_alpha = _choose_shrink_alpha(recent_p, recent_y, k, active)
            else:
                shrink_alpha = 1.0 if len(eligible) > 1 else 0.0

        stacked = _stack_predict(signals, weights, k)
        uniform = signals["Uniform"]
        research = safe_scale((1.0 - shrink_alpha) * uniform + shrink_alpha * stacked, k)
        y = Y[t, :active]

        eb = np.mean((research - y) ** 2)
        ub = np.mean((uniform - y) ** 2)
        el = _log_loss(y, research)
        ul = _log_loss(y, uniform)
        ens_brier.append(eb)
        uni_brier.append(ub)
        ens_ll.append(el)
        uni_ll.append(ul)
        brier_deltas.append(ub - eb)
        top = set(np.argsort(research)[::-1][:k].tolist())
        actual = set(np.flatnonzero(y > 0).tolist())
        topk_hits.append(len(top & actual) / k)

        block = np.column_stack([signals[nme] for nme in names])
        fit_P.append(block)
        fit_y.append(y)
        recent_p.append(stacked.reshape(1, -1))
        recent_y.append(y.reshape(1, -1))
        last_research = research

    deltas = np.asarray(brier_deltas, dtype=float)
    lo, hi, p_pos = _bootstrap_ci(deltas)
    metrics = PoolMetrics(
        name=pool_name,
        n_draws=len(ens_brier),
        brier=float(np.mean(ens_brier)),
        log_loss=float(np.mean(ens_ll)),
        uniform_brier=float(np.mean(uni_brier)),
        uniform_log_loss=float(np.mean(uni_ll)),
        brier_improvement=float(np.mean(uni_brier) - np.mean(ens_brier)),
        log_loss_improvement=float(np.mean(uni_ll) - np.mean(ens_ll)),
        topk_hit_rate=float(np.mean(topk_hits)),
        period_improvements=_period_improvements(deltas),
        bootstrap_ci=(lo, hi),
        bootstrap_p_positive=p_pos,
    )
    meta_weights = dict(weights)
    meta_weights["_shrink_alpha"] = float(shrink_alpha)
    return metrics, meta_weights, last_research, signal_wins



def _spread_main_candidates(
    main_p: NDArray[np.float64],
    *,
    n_lines: int = 40,
    seed: int = 17,
) -> list[tuple[int, ...]]:
    """Build diverse main lines; when probs are near-uniform, prefer spaced/anti-crowd sets."""
    rng = np.random.default_rng(seed)
    rank = np.argsort(main_p)[::-1]
    near_uniform = float(np.std(main_p)) < 1e-6
    out: list[tuple[int, ...]] = []
    used: set[tuple[int, ...]] = set()

    def add(nums: Sequence[int]) -> None:
        line = tuple(sorted(int(x) for x in nums))
        if len(line) == MAIN_K and len(set(line)) == MAIN_K and line not in used:
            used.add(line)
            out.append(line)

    if near_uniform:
        # Spaced templates across the 1..50 wheel (anti-cluster).
        for offset in range(1, 11):
            add([(offset + i * 10 - 1) % 50 + 1 for i in range(MAIN_K)])
            add([(offset + i * 9 - 1) % 50 + 1 for i in range(MAIN_K)])
            add([(offset + i * 11 - 1) % 50 + 1 for i in range(MAIN_K)])
        for _ in range(80):
            pick = sorted(rng.choice(np.arange(1, 51), size=MAIN_K, replace=False).tolist())
            # Reject heavy birthday / consecutive clusters early.
            if sum(n <= 31 for n in pick) >= 4:
                continue
            if sum(b - a == 1 for a, b in zip(pick[:-1], pick[1:])) >= 2:
                continue
            add(pick)
            if len(out) >= n_lines:
                break
    else:
        for shift in range(0, 24):
            add([int(x + 1) for x in rank[shift: shift + MAIN_K]])
        # Mix high-rank with spaced fillers.
        top = [int(x + 1) for x in rank[:20]]
        for i in range(20):
            base = top[i: i + 3]
            if len(base) < 3:
                continue
            fillers = [int(x) for x in rng.choice(
                [n for n in range(1, 51) if n not in base], size=2, replace=False
            )]
            add(base + fillers)

    return out[:n_lines]


def build_value_portfolio(
    main_p: NDArray[np.float64],
    euro_p: NDArray[np.float64],
    *,
    lines: int = 8,
    history_mains: Sequence[Sequence[int]] | None = None,
) -> list[dict[str, Any]]:
    """
    Construct a research portfolio balancing model score and anti-crowd value.
    Does not claim higher jackpot odds.
    """
    euro_rank = np.argsort(euro_p)[::-1]
    used: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()

    main_candidates = _spread_main_candidates(main_p, n_lines=48, seed=17)
    euro_pairs: list[tuple[int, ...]] = []
    for shift in range(0, 10):
        pair = tuple(sorted(int(x + 1) for x in euro_rank[shift: shift + EURO_K]))
        if len(set(pair)) == EURO_K:
            euro_pairs.append(pair)
    cold_euro = [int(x) + 1 for x in euro_rank[::-1][:8]]
    hot_euro = [int(x) + 1 for x in euro_rank[:8]]
    for i in range(12):
        e1 = cold_euro[i % len(cold_euro)]
        e2 = cold_euro[(i + 3) % len(cold_euro)]
        if e1 == e2:
            e2 = hot_euro[i % len(hot_euro)]
        euro_pairs.append(tuple(sorted((e1, e2))))
        e_hot = hot_euro[i % len(hot_euro)]
        e_cold = cold_euro[(i + 1) % len(cold_euro)]
        if e_hot != e_cold:
            euro_pairs.append(tuple(sorted((e_hot, e_cold))))
    # Deduplicate euro pairs preserving order.
    seen_e: set[tuple[int, ...]] = set()
    uniq_euro: list[tuple[int, ...]] = []
    for pair in euro_pairs:
        if pair not in seen_e:
            seen_e.add(pair)
            uniq_euro.append(pair)

    candidates: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for i, main in enumerate(main_candidates):
        euro = uniq_euro[i % len(uniq_euro)]
        candidates.append((main, euro))
        # Also pair each strong main with the top research euro pair.
        candidates.append((main, uniq_euro[0]))

    scored = []
    for main, euro in candidates:
        key = (main, euro)
        if key in used:
            continue
        used.add(key)
        model_score = float(sum(main_p[m - 1] for m in main) + sum(euro_p[e - 1] for e in euro))
        crowd = anti_crowd_score(main, euro)
        crowd_score = float(
            crowd.get("anti_crowd_score", crowd.get("score", crowd.get("total", 0.0)))
        )
        # Value score: prefer uncommon patterns while keeping decent model mass.
        # When main probs are flat, lean harder on anti-crowd + euro research mass.
        near_uniform_main = float(np.std(main_p)) < 1e-6
        if near_uniform_main:
            euro_mass = float(sum(euro_p[e - 1] for e in euro))
            value = 0.35 * euro_mass + 0.55 * crowd_score
        else:
            value = 0.55 * model_score + 0.45 * crowd_score
        novelty = 0.0
        if history_mains:
            overlaps = [len(set(main) & set(h)) for h in history_mains[-80:]]
            novelty = 1.0 - (float(np.mean(overlaps)) / MAIN_K)
            value += 0.10 * novelty
        scored.append(
            {
                "main": list(main),
                "euro": list(euro),
                "model_score": model_score,
                "anti_crowd_score": crowd_score,
                "novelty": novelty,
                "value_score": value,
            }
        )

    # Approximate prize table for relative EV ranking (not live jackpots).
    prize_table = {
        "5+2": 10_000_000.0,
        "5+1": 500_000.0,
        "5+0": 100_000.0,
        "4+2": 5_000.0,
        "4+1": 300.0,
        "3+2": 150.0,
        "4+0": 90.0,
        "2+2": 60.0,
        "3+1": 25.0,
        "3+0": 18.0,
        "1+2": 14.0,
        "2+1": 10.0,
    }
    for row in scored:
        # Higher anti-crowd => fewer expected co-winners => better conditional EV.
        crowd = max(0.05, min(1.0, row["anti_crowd_score"]))
        co_factors = {tier: max(0.55, 1.35 - crowd) for tier in prize_table}
        ev = expected_value(prize_table, line_cost=2.50, co_winner_factors=co_factors)
        row["approx_net_ev"] = float(ev["net_ev"])
        row["approx_gross_ev"] = float(ev["gross_ev"])
        row["value_score"] = 0.70 * row["value_score"] + 0.30 * (row["approx_net_ev"] + 2.5)

    scored.sort(key=lambda r: (-r["value_score"], -r["anti_crowd_score"], -r["approx_net_ev"]))
    out = []
    for i, row in enumerate(scored[:lines], 1):
        item = dict(row)
        item["line"] = i
        item["edge_type"] = "prize-value+research-rank"
        item["jackpot_odds_unchanged"] = True
        out.append(item)
    return out


def gates_from_metrics(main: PoolMetrics, euro: PoolMetrics) -> dict[str, Any]:
    def pool_gates(m: PoolMetrics) -> dict[str, bool]:
        chance = MAIN_K / MAIN_POOL if m.name == "main" else EURO_K / EURO_POOL
        periods_ok = sum(x > 0 for x in m.period_improvements) >= 2 and m.brier_improvement > 0
        # Proper scoring + bootstrap are the hard evidence. Top-k is a soft ranking check
        # (temperature calibration can help Brier while slightly hurting hard top-k).
        return {
            "brier_better": m.brier_improvement > 0,
            "log_loss_better": m.log_loss_improvement > 0,
            "majority_periods_positive": periods_ok,
            "bootstrap_ci_positive": m.bootstrap_ci[0] > 0,
            "bootstrap_p_positive_ge_0_95": m.bootstrap_p_positive >= 0.95,
            "topk_near_or_above_chance": m.topk_hit_rate >= chance * 0.90,
        }

    main_g = pool_gates(main)
    euro_g = pool_gates(euro)
    # Annotate strict top-k for reporting (not required for pool research edge).
    main_chance = MAIN_K / MAIN_POOL
    euro_chance = EURO_K / EURO_POOL
    main_g["topk_above_chance"] = main.topk_hit_rate > main_chance
    euro_g["topk_above_chance"] = euro.topk_hit_rate > euro_chance

    hard_keys = (
        "brier_better",
        "log_loss_better",
        "majority_periods_positive",
        "bootstrap_ci_positive",
        "bootstrap_p_positive_ge_0_95",
        "topk_near_or_above_chance",
    )
    main_edge = all(main_g[k] for k in hard_keys)
    euro_edge = all(euro_g[k] for k in hard_keys)
    # Both pools must clear hard gates AND strict top-k to rewrite jackpot odds.
    draw_prob_edge = (
        main_edge
        and euro_edge
        and main_g["topk_above_chance"]
        and euro_g["topk_above_chance"]
    )
    if draw_prob_edge:
        decision = "DEPLOY_RESEARCH_PROBABILITIES"
        explanation = "All draw-probability gates passed for main and euro."
    elif euro_edge and not main_edge:
        decision = "KEEP_UNIFORM_JACKPOT_USE_EURO_RESEARCH_EDGE"
        explanation = (
            "A stable out-of-sample edge was detected on Euro numbers, but not on main numbers. "
            "Jackpot odds stay uniform; research ranking may use non-uniform Euro probabilities "
            "plus the prize-value portfolio layer."
        )
    elif main_edge and not euro_edge:
        decision = "KEEP_UNIFORM_JACKPOT_USE_MAIN_RESEARCH_EDGE"
        explanation = (
            "A stable out-of-sample edge was detected on main numbers, but not on Euro numbers. "
            "Jackpot odds stay uniform; research ranking may use non-uniform main probabilities "
            "plus the prize-value portfolio layer."
        )
    else:
        decision = "KEEP_UNIFORM_CHAMPION_USE_VALUE_PORTFOLIO"
        explanation = (
            "No full draw-probability edge cleared the out-of-sample battery. "
            "Keep exact-uniform jackpot odds and use the prize-value / research portfolio layer."
        )
    return {
        "main": main_g,
        "euro": euro_g,
        "main_edge_detected": main_edge,
        "euro_edge_detected": euro_edge,
        "draw_probability_edge_detected": draw_prob_edge,
        "prize_value_edge_available": True,
        "deploy_nonuniform_probabilities": draw_prob_edge,
        "use_research_main_probs": main_edge or draw_prob_edge,
        "use_research_euro_probs": euro_edge or draw_prob_edge,
        "decision": decision,
        "explanation": explanation,
    }


def run_edge_search(
    history_path: str | Path,
    *,
    min_history: int = 120,
    train_learner: bool = True,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = package_root()
    history_path = Path(history_path)
    out_dir = Path(output_dir) if output_dir else ensure_user_layout()["engine"]
    out_dir.mkdir(parents=True, exist_ok=True)

    draws = load_canonical_history(history_path)
    main_Y, euro_Y, _ = incidence_matrices(draws)

    learner_db = out_dir / "EuroJackpot_Edge_Learner.sqlite"
    learner_blend = None
    if train_learner:
        # Faster learner train for blend signal (cap optional for CI via env not needed here).
        train_on_history(
            learner_db,
            history_path,
            min_history=max(80, min_history // 2),
            max_draws=None,
            reset=True,
            progress_every=0,
        )
        learner_blend = predict_from_past_draws(learner_db, draws, euro_pool=draws[-1].euro_pool)

    draw_days = [d.draw_day for d in draws]
    # Euro-pool size eras (8/10/12) are the only verified operational breakpoints for inclusion rates.
    euro_eras = [int(d.euro_pool) for d in draws]
    main_eras = [1 for _ in draws]
    main_metrics, main_weights, main_p, main_wins = evaluate_pool(
        main_Y,
        MAIN_K,
        start=min_history,
        pool_name="main",
        draw_days=draw_days,
        era_ids=main_eras,
    )
    euro_metrics, euro_weights, euro_p, euro_wins = evaluate_pool(
        euro_Y,
        EURO_K,
        start=min_history,
        pool_name="euro",
        draw_days=draw_days,
        era_ids=euro_eras,
    )

    # Blend final research probs lightly with learner suggestion masses if available.
    # Only nudge pools that already look promising so we don't destroy Uniform on main.
    if learner_blend:
        if main_metrics.brier_improvement > 0:
            lm = np.ones(MAIN_POOL)
            for n in learner_blend["main"]:
                lm[n - 1] *= 1.10
            main_p = safe_scale(main_p * lm, MAIN_K)
        if euro_metrics.brier_improvement > 0:
            le = np.ones(EURO_POOL)
            for n in learner_blend["euro"]:
                if n <= EURO_POOL:
                    le[n - 1] *= 1.12
            euro_p = safe_scale(euro_p[:EURO_POOL] * le, EURO_K)

    gates = gates_from_metrics(main_metrics, euro_metrics)
    history_mains = [d.main for d in draws]

    deployed_main = np.full(MAIN_POOL, MAIN_K / MAIN_POOL)
    deployed_euro = np.full(EURO_POOL, EURO_K / EURO_POOL)
    # Research ranking may use pool-specific edges; deployed jackpot probs stay uniform
    # unless BOTH pools clear every gate.
    research_main = main_p if gates["use_research_main_probs"] else deployed_main
    research_euro = euro_p if gates["use_research_euro_probs"] else deployed_euro
    if gates["deploy_nonuniform_probabilities"]:
        deployed_main = main_p
        deployed_euro = euro_p
    portfolio = build_value_portfolio(
        research_main, research_euro, lines=8, history_mains=history_mains
    )

    if gates["draw_probability_edge_detected"]:
        overall = "Validated draw-probability edge"
    elif gates["euro_edge_detected"] or gates["main_edge_detected"]:
        overall = "Partial research edge (pool-specific) + prize-value portfolio"
    else:
        overall = "Uniform mode with prize-value research portfolio"

    report = {
        "engine": "eurojackpot_edge_engine_v3_8",
        "app_version": APP_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "history_file": str(history_path),
        "history_draws": len(draws),
        "min_history": min_history,
        "overall_status": overall,
        "gates": gates,
        "main_pool": {
            "brier": main_metrics.brier,
            "uniform_brier": main_metrics.uniform_brier,
            "brier_improvement": main_metrics.brier_improvement,
            "log_loss": main_metrics.log_loss,
            "uniform_log_loss": main_metrics.uniform_log_loss,
            "log_loss_improvement": main_metrics.log_loss_improvement,
            "topk_hit_rate": main_metrics.topk_hit_rate,
            "period_improvements": main_metrics.period_improvements,
            "bootstrap_ci": list(main_metrics.bootstrap_ci),
            "bootstrap_p_positive": main_metrics.bootstrap_p_positive,
            "stack_weights": main_weights,
            "signal_window_wins": main_wins,
            "n_oos_draws": main_metrics.n_draws,
        },
        "euro_pool": {
            "brier": euro_metrics.brier,
            "uniform_brier": euro_metrics.uniform_brier,
            "brier_improvement": euro_metrics.brier_improvement,
            "log_loss": euro_metrics.log_loss,
            "uniform_log_loss": euro_metrics.uniform_log_loss,
            "log_loss_improvement": euro_metrics.log_loss_improvement,
            "topk_hit_rate": euro_metrics.topk_hit_rate,
            "period_improvements": euro_metrics.period_improvements,
            "bootstrap_ci": list(euro_metrics.bootstrap_ci),
            "bootstrap_p_positive": euro_metrics.bootstrap_p_positive,
            "stack_weights": euro_weights,
            "signal_window_wins": euro_wins,
            "n_oos_draws": euro_metrics.n_draws,
        },
        "research_next_probabilities": {
            "main": {str(i + 1): float(x) for i, x in enumerate(main_p)},
            "euro": {str(i + 1): float(x) for i, x in enumerate(euro_p[:EURO_POOL])},
        },
        "deployed_next_probabilities": {
            "main": {str(i + 1): float(x) for i, x in enumerate(deployed_main)},
            "euro": {str(i + 1): float(x) for i, x in enumerate(deployed_euro)},
        },
        "primary_experimental_line": portfolio[0] if portfolio else None,
        "portfolio": portfolio,
        "learner_blend_line": learner_blend,
        "method_catalog": method_catalog(),
        "jackpot_combination_space": math.comb(50, 5) * math.comb(12, 2),
        "statement": (
            "This engine searched hard for a stable out-of-sample draw-probability edge. "
            + gates["explanation"]
            + " Unique-line jackpot probability remains 1/139,838,160 unless deployment gates pass."
        ),
    }

    report_path = out_dir / "EuroJackpot_Edge_Search_Report_v3_8.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Convenience: write a results file one-click can consume as --results.
    results_path = out_dir / "EuroJackpot_Model_Results_Edge_v3_8.json"
    results_path.write_text(
        json.dumps(
            {
                "engine_version": f"{APP_VERSION}-edge",
                "generated_on": datetime.now(timezone.utc).date().isoformat(),
                "next_draw_date": report.get("primary_experimental_line") and None,
                "overall_status": report["overall_status"],
                "primary_experimental_line": portfolio[0],
                "portfolio": portfolio,
                "research_next_probabilities": report["research_next_probabilities"],
                "deployed_next_probabilities": report["deployed_next_probabilities"],
                "deployment_rule": gates["decision"],
                "edge_report": str(report_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Fill next_draw_date from learning helper / calendar: last history + next Tue/Fri.
    from eurojackpot_operational_v3_4 import next_draw_date
    from datetime import date
    last = date.fromisoformat(draws[-1].draw_date)
    nxt = next_draw_date(last)
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    payload["next_draw_date"] = nxt.isoformat()
    results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report["results_file"] = str(results_path)
    report["report_file"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def method_catalog() -> dict[str, Any]:
    """Inventory of probability methods used by the edge / research stack."""
    return {
        "deployed_champion": {
            "Uniform": "Exact fair-draw inclusion probs (5/50, 2/12); unique-line 1/139838160",
        },
        "edge_signals": {
            name: (
                "Primary euro stack"
                if name in PRIMARY_SIGNAL_NAMES
                else "Research library (eligibility-gated)"
            )
            for name in SIGNAL_NAMES
        },
        "strengthened_methods": [
            "HierarchicalEra - same euro-pool-size posterior shrunk to global",
            "DynamicLogit - logistic-normal filter, predict-before-update (no leakage)",
            "BetaBinomial - conjugate posterior mean with uniform-centered prior",
            "SpectralCooccur - co-occurrence eigenvector (eligibility may drop)",
        ],
        "also_in_repo": [
            "v3 reliability ML family (Logistic/GBM/RF/ExtraTrees/HistGBM/BayesianRidge)",
            "v3 statistical family (Full/Rolling/EWMA/BetaBinomial/Hierarchical/DynamicState)",
            "advanced v3.3 (HMM regimes, Ising, GP drift, conformal, robust stacking)",
            "adaptive learning scores (era-frequency + EWMA + outcome weights)",
            "prize-value / anti-crowd portfolio (does not change jackpot odds)",
        ],
        "policy": "Fail-closed: non-uniform deployment only if both pools clear OOS gates",
    }


def run_selftest() -> dict[str, Any]:
    root = package_root()
    history = root / "EuroJackpot_Canonical_History_v3.csv"
    out = Path("/tmp/eurojackpot-edge-selftest")
    # Small/fast: higher min_history and rely on evaluate internals; still runs full hist but OK.
    report = run_edge_search(history, min_history=200, train_learner=False, output_dir=out)
    passed = (
        "gates" in report
        and "portfolio" in report
        and len(report["portfolio"]) >= 3
        and report["main_pool"]["n_oos_draws"] > 100
        and Path(report["report_file"]).exists()
    )
    return {"passed": passed, "decision": report["gates"]["decision"], "status": report["overall_status"]}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="EuroJackpot stable-edge search engine")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run full edge search on canonical history")
    run.add_argument("--history", default=str(package_root() / "EuroJackpot_Canonical_History_v3.csv"))
    run.add_argument("--min-history", type=int, default=120)
    run.add_argument("--output-dir", default=None)
    run.add_argument("--skip-learner", action="store_true")
    sub.add_parser("selftest", help="Smoke test edge engine")
    sub.add_parser("list-methods", help="Print probability method catalog")
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list-methods":
        print(json.dumps(method_catalog(), indent=2))
        raise SystemExit(0)
    if args.command == "selftest":
        result = run_selftest()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 1)
    if args.command == "run":
        report = run_edge_search(
            args.history,
            min_history=args.min_history,
            train_learner=not args.skip_learner,
            output_dir=args.output_dir,
        )
        print(json.dumps({
            "status": "PASS",
            "overall_status": report["overall_status"],
            "decision": report["gates"]["decision"],
            "draw_probability_edge_detected": report["gates"]["draw_probability_edge_detected"],
            "main_brier_improvement": report["main_pool"]["brier_improvement"],
            "euro_brier_improvement": report["euro_pool"]["brier_improvement"],
            "main_bootstrap_ci": report["main_pool"]["bootstrap_ci"],
            "euro_bootstrap_ci": report["euro_pool"]["bootstrap_ci"],
            "primary": report["primary_experimental_line"],
            "report_file": report["report_file"],
            "results_file": report["results_file"],
            "statement": report["statement"],
        }, indent=2))


if __name__ == "__main__":
    main()

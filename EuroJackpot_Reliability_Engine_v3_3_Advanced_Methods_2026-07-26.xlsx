from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import BayesianRidge, LogisticRegression, SGDClassifier
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RNG_SEED = 20260726
np.random.seed(RNG_SEED)
random.seed(RNG_SEED)

ROOT = Path(__file__).resolve().parent
RAW_HISTORY = ROOT / 'eurojackpot_full_history.txt'
OUT_DATA = ROOT / 'EuroJackpot_Canonical_History_2012_2026.csv'
OUT_RESULTS = ROOT / 'EuroJackpot_Model_Results.json'
OUT_PRED = ROOT / 'EuroJackpot_Next_Draw_Ranking.csv'
OUT_PORTFOLIO = ROOT / 'EuroJackpot_Diversified_Portfolio.csv'

LATEST_CORRECTIONS = {
    date(2025, 1, 24): ((2, 9, 16, 46, 47), (3, 9), 'Uploaded OPAP file + independent web verification'),
    date(2026, 1, 6): ((21, 23, 30, 33, 38), (8, 12), 'Uploaded OPAP file + independent web verification'),
    date(2026, 1, 9): ((1, 17, 19, 25, 41), (6, 12), 'Uploaded OPAP file + independent web verification'),
    date(2026, 1, 13): ((2, 16, 27, 33, 47), (6, 12), 'Uploaded OPAP file + independent web verification'),
    date(2026, 1, 20): ((16, 26, 32, 37, 45), (2, 3), 'Uploaded OPAP file + independent web verification'),
    date(2026, 1, 23): ((18, 36, 39, 45, 50), (6, 9), 'Uploaded OPAP file + independent web verification'),
    date(2026, 2, 3): ((3, 20, 27, 37, 44), (1, 2), 'Uploaded OPAP file + independent web verification'),
    date(2026, 7, 24): ((4, 6, 8, 17, 22), (7, 10), 'Official EuroJackpot website + independent web verification'),
}

SOURCE_URLS = {
    'history_export': 'https://www.lottometrics.app/api/export/draws/eurojackpot/all/txt',
    'official_latest': 'https://www.eurojackpot.com/',
    'latest_crosscheck': 'https://www.lotto.net/eurojackpot/results/july-24-2026',
    'rules_current': 'https://www.euro-jackpot.net/rules',
    'archive_download': 'https://www.sachsenlotto.de/portal/zahlen-quoten/gewinnzahlen/download-archiv/gewinnzahlen_download.jsp',
}

@dataclass(frozen=True)
class Draw:
    draw_id: int
    draw_date: date
    main: tuple[int, ...]
    euro: tuple[int, ...]
    rule_version: str
    euro_pool: int
    draw_day: str
    source: str
    verification_status: str
    correction_note: str


def rule_for(d: date) -> tuple[str, int]:
    if d < date(2014, 10, 10):
        return 'R1_5of50_2of8', 8
    if d < date(2022, 3, 25):
        return 'R2_5of50_2of10', 10
    return 'R3_5of50_2of12', 12


def load_draws() -> list[Draw]:
    recs: dict[date, tuple[tuple[int, ...], tuple[int, ...], str, str]] = {}
    pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\s+([0-9,]+)\s+([0-9,]+)\s*$')
    with RAW_HISTORY.open(encoding='utf-8') as f:
        for line in f:
            m = pattern.match(line)
            if not m:
                continue
            d = datetime.strptime(m.group(1), '%Y-%m-%d').date()
            main = tuple(sorted(int(x) for x in m.group(2).split(',')))
            euro = tuple(sorted(int(x) for x in m.group(3).split(',')))
            recs[d] = (main, euro, 'LottoMetrics full-history export', '')
    for d, (main, euro, source) in LATEST_CORRECTIONS.items():
        note = 'Added missing record' if d not in recs else ('Corrected source discrepancy' if recs[d][:2] != (main, euro) else 'Verified record')
        recs[d] = (tuple(main), tuple(euro), source, note)

    draws: list[Draw] = []
    for i, d in enumerate(sorted(recs), start=1):
        main, euro, source, note = recs[d]
        rule, epool = rule_for(d)
        valid = (
            len(main) == 5 and len(set(main)) == 5 and all(1 <= n <= 50 for n in main)
            and len(euro) == 2 and len(set(euro)) == 2 and all(1 <= n <= epool for n in euro)
        )
        if not valid:
            raise ValueError(f'Invalid draw {d}: {main} + {euro} under {rule}')
        draws.append(Draw(
            draw_id=i,
            draw_date=d,
            main=main,
            euro=euro,
            rule_version=rule,
            euro_pool=epool,
            draw_day=d.strftime('%A'),
            source=source,
            verification_status='Verified' if d in LATEST_CORRECTIONS else 'Cross-source archive',
            correction_note=note,
        ))
    return draws


def export_draws(draws: list[Draw]) -> None:
    with OUT_DATA.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['draw_id','draw_date','main_1','main_2','main_3','main_4','main_5','euro_1','euro_2','main_pool','euro_pool','rule_version','draw_day','source','verification_status','correction_note'])
        for d in draws:
            w.writerow([d.draw_id, d.draw_date.isoformat(), *d.main, *d.euro, 50, d.euro_pool, d.rule_version, d.draw_day, d.source, d.verification_status, d.correction_note])


def occurrence_matrix(draws: list[Draw], pool: str) -> tuple[np.ndarray, np.ndarray]:
    if pool == 'main':
        max_n, k = 50, 5
        arr = np.zeros((len(draws), max_n), dtype=np.int8)
        avail = np.ones_like(arr, dtype=bool)
        for i, d in enumerate(draws):
            arr[i, np.array(d.main)-1] = 1
    else:
        max_n, k = 12, 2
        arr = np.zeros((len(draws), max_n), dtype=np.int8)
        avail = np.zeros_like(arr, dtype=bool)
        for i, d in enumerate(draws):
            avail[i, :d.euro_pool] = True
            arr[i, np.array(d.euro)-1] = 1
    return arr, avail


def safe_prob_scale(p: np.ndarray, k: int, avail: np.ndarray | None = None) -> np.ndarray:
    p = np.asarray(p, dtype=float).copy()
    if avail is not None:
        p[~avail] = 0.0
    p = np.clip(p, 1e-8, 1-1e-8)
    s = p.sum()
    if s <= 0:
        count = int(avail.sum()) if avail is not None else len(p)
        p = np.where(avail, k/count, 0.0) if avail is not None else np.full(len(p), k/len(p))
    else:
        p *= k/s
    # cap and redistribute iteratively
    for _ in range(5):
        over = p > 0.999
        if not over.any():
            break
        excess = float((p[over]-0.999).sum())
        p[over] = 0.999
        eligible = (~over) & ((avail if avail is not None else np.ones(len(p), dtype=bool)))
        if eligible.any():
            p[eligible] += excess * p[eligible] / max(p[eligible].sum(), 1e-12)
    return np.clip(p, 1e-8, 0.999)


def uniform_prediction(pool: str, draw: Draw) -> np.ndarray:
    if pool == 'main':
        return np.full(50, 5/50)
    p = np.zeros(12)
    p[:draw.euro_pool] = 2/draw.euro_pool
    return p


def statistical_prediction(hist: np.ndarray, avail_hist: np.ndarray, target_draw: Draw, pool: str, method: str, param: float | int | None = None) -> np.ndarray:
    max_n = 50 if pool == 'main' else 12
    k = 5 if pool == 'main' else 2
    target_avail = np.ones(max_n, dtype=bool) if pool == 'main' else np.arange(max_n) < target_draw.euro_pool
    n_hist = len(hist)
    if n_hist == 0:
        return uniform_prediction(pool, target_draw)

    exposure = avail_hist.sum(axis=0).astype(float)
    counts = hist.sum(axis=0).astype(float)
    base = np.zeros(max_n)
    base[target_avail] = k / target_avail.sum()

    if method == 'full_frequency':
        strength = float(param or 20.0)
        p = (counts + strength*base) / np.maximum(exposure + strength, 1.0)
    elif method == 'rolling_frequency':
        window = int(param or 100)
        hh = hist[-window:]
        aa = avail_hist[-window:]
        ex = aa.sum(axis=0).astype(float)
        cc = hh.sum(axis=0).astype(float)
        strength = 10.0
        p = (cc + strength*base) / np.maximum(ex + strength, 1.0)
    elif method == 'ewma':
        halflife = float(param or 50.0)
        ages = np.arange(n_hist-1, -1, -1)
        w = np.exp(-math.log(2)*ages/halflife)
        wc = (hist*w[:,None]).sum(axis=0)
        we = (avail_hist*w[:,None]).sum(axis=0)
        strength = 4.0
        p = (wc + strength*base) / np.maximum(we + strength, 1e-12)
    elif method == 'beta_binomial':
        strength = float(param or 50.0)
        alpha = strength*base
        beta = strength*(1-base)
        p = (counts+alpha)/np.maximum(exposure+alpha+beta, 1.0)
    elif method == 'hierarchical_bayes':
        # Pool-era posterior shrunk to global posterior and theoretical uniform.
        strength = float(param or 80.0)
        if pool == 'main':
            era_mask = np.ones(n_hist, dtype=bool)
        else:
            era_pool = target_draw.euro_pool
            era_mask = np.array([int(a.sum()) == era_pool for a in avail_hist], dtype=bool)
        era_counts = hist[era_mask].sum(axis=0).astype(float) if era_mask.any() else counts
        era_exposure = avail_hist[era_mask].sum(axis=0).astype(float) if era_mask.any() else exposure
        global_p = (counts + 40*base)/np.maximum(exposure+40,1.0)
        p = (era_counts + strength*global_p)/np.maximum(era_exposure+strength,1.0)
    elif method == 'dynamic_state':
        decay = float(param or 0.96)
        p = base.copy()
        q = base.copy()
        # Robust dynamic update with shrinkage to theoretical baseline.
        for t in range(n_hist):
            active = avail_hist[t]
            obs = hist[t].astype(float)
            q[active] = decay*q[active] + (1-decay)*obs[active]
            q[active] = 0.92*q[active] + 0.08*base[active]
        p = q
    else:
        raise KeyError(method)
    p[~target_avail] = 0.0
    return safe_prob_scale(p, k, target_avail)


def build_features(draws: list[Draw], pool: str) -> dict[str, Any]:
    ymat, availmat = occurrence_matrix(draws, pool)
    max_n = ymat.shape[1]
    k = 5 if pool == 'main' else 2
    rows: list[list[float]] = []
    ys: list[int] = []
    draw_idx: list[int] = []
    number_idx: list[int] = []
    feature_names = [
        'number_norm','number_sin','number_cos','is_odd','is_high','decade_norm',
        'full_freq','roll10','roll25','roll50','roll100','roll200',
        'ewma10','ewma25','ewma50','gap_norm','gap_log','accel_10_50','accel_25_100',
        'repeat_last','neighbor_last','transition_score','pair_prev_score','triple_prev_score',
        'position_affinity','position_entropy','dow_freq','prev_sum_norm','prev_odd_ratio','distance_prev_mean',
        'rule_pool_norm','draw_is_tuesday'
    ]
    groups = {
        'identity': [0,1,2,3,4,5],
        'frequency': [6,7,8,9,10,11],
        'ewma': [12,13,14],
        'gap': [15,16],
        'trend': [17,18],
        'repeat_transition': [19,20,21],
        'pair_triple': [22,23],
        'position': [24,25],
        'draw_composition': [26,27,28,29],
        'rule_calendar': [30,31],
    }

    # Caches updated sequentially.
    counts = np.zeros(max_n, dtype=float)
    exposures = np.zeros(max_n, dtype=float)
    last_seen = np.full(max_n, -1, dtype=int)
    ewma = {10: np.zeros(max_n), 25: np.zeros(max_n), 50: np.zeros(max_n)}
    position_counts = np.zeros((max_n, k), dtype=float)
    dow_counts = {1: np.zeros(max_n), 4: np.zeros(max_n)}
    dow_exposure = {1: np.zeros(max_n), 4: np.zeros(max_n)}
    transition_counts = np.zeros((max_n, max_n), dtype=float)
    transition_exposure = np.zeros(max_n, dtype=float)
    pair_counts = np.zeros((max_n, max_n), dtype=float)
    triple_counts: dict[tuple[int,int,int], int] = defaultdict(int)

    for t, d in enumerate(draws):
        target_nums = d.main if pool == 'main' else d.euro
        target_pool = 50 if pool == 'main' else d.euro_pool
        active = np.arange(max_n) < target_pool
        prev_nums = () if t == 0 else (draws[t-1].main if pool == 'main' else draws[t-1].euro)
        prev_set = set(prev_nums)
        prev_sum = sum(prev_nums) if prev_nums else (k*(target_pool+1)/2)
        prev_mean = prev_sum/k
        prev_odd = sum(n%2 for n in prev_nums)/k if prev_nums else 0.5
        current_dow = d.draw_date.weekday()

        # Rolling counts from prior matrices.
        def roll_freq(w: int) -> np.ndarray:
            if t == 0:
                out = np.zeros(max_n)
            else:
                hh = ymat[max(0,t-w):t]
                aa = availmat[max(0,t-w):t]
                out = hh.sum(axis=0)/np.maximum(aa.sum(axis=0),1)
            return out
        r10,r25,r50,r100,r200 = (roll_freq(w) for w in (10,25,50,100,200))
        full = counts/np.maximum(exposures,1)

        # Update-free EWMA prior values are already in ewma.
        gaps = np.where(last_seen >= 0, t-last_seen, t+1)
        gap_scale = max(10.0, math.sqrt(t+1)*2)

        # Transition score from previous draw numbers to each candidate.
        trans = np.zeros(max_n)
        pair_prev = np.zeros(max_n)
        triple_prev = np.zeros(max_n)
        if prev_nums:
            prev_zero = [n-1 for n in prev_nums if n <= max_n]
            for n0 in range(max_n):
                vals=[]
                pvals=[]
                tvals=[]
                for p0 in prev_zero:
                    vals.append(transition_counts[p0,n0]/max(transition_exposure[p0],1.0))
                    pvals.append(pair_counts[p0,n0]/max(counts[p0],1.0))
                for a,b in combinations(prev_zero,2):
                    key=tuple(sorted((a,b,n0)))
                    denom=max(pair_counts[a,b],1.0)
                    tvals.append(triple_counts.get(key,0)/denom)
                trans[n0]=float(np.mean(vals)) if vals else 0.0
                pair_prev[n0]=float(np.mean(pvals)) if pvals else 0.0
                triple_prev[n0]=float(np.mean(tvals)) if tvals else 0.0

        for n in range(1,target_pool+1):
            j=n-1
            pos = position_counts[j]
            psum=pos.sum()
            pos_prob=(pos+1)/(psum+k)
            pos_aff=float(pos_prob.max())
            pos_ent=float(-(pos_prob*np.log(pos_prob)).sum()/math.log(k)) if k>1 else 0.0
            dowp=(dow_counts.get(current_dow,np.zeros(max_n))[j]+1)/(dow_exposure.get(current_dow,np.zeros(max_n))[j]+target_pool/k if current_dow in dow_counts else 2)
            row=[
                n/target_pool,
                math.sin(2*math.pi*n/target_pool),
                math.cos(2*math.pi*n/target_pool),
                float(n%2),
                float(n>target_pool/2),
                math.floor((n-1)/10)/max(1,math.floor((target_pool-1)/10)),
                full[j],r10[j],r25[j],r50[j],r100[j],r200[j],
                ewma[10][j],ewma[25][j],ewma[50][j],
                min(gaps[j]/gap_scale,5.0),math.log1p(gaps[j]),
                r10[j]-r50[j],r25[j]-r100[j],
                float(n in prev_set),float(any(abs(n-p)==1 for p in prev_nums)),trans[j],pair_prev[j],triple_prev[j],
                pos_aff,pos_ent,dowp,
                prev_sum/(k*target_pool),prev_odd,abs(n-prev_mean)/target_pool,
                target_pool/max_n,float(current_dow==1),
            ]
            rows.append(row)
            ys.append(int(n in target_nums))
            draw_idx.append(t)
            number_idx.append(j)

        # Update caches with current draw after feature extraction.
        exposures[active]+=1
        y=ymat[t].astype(float)
        counts+=y
        for h in ewma:
            alpha=1-math.exp(-math.log(2)/h)
            ewma[h][active]=(1-alpha)*ewma[h][active]+alpha*y[active]
        for n in target_nums:
            last_seen[n-1]=t
        for pos_i,n in enumerate(sorted(target_nums)):
            position_counts[n-1,pos_i]+=1
        if current_dow in dow_counts:
            dow_exposure[current_dow][active]+=1
            dow_counts[current_dow]+=y
        if prev_nums:
            for p in prev_nums:
                if p<=max_n:
                    transition_exposure[p-1]+=1
                    for n in target_nums:
                        transition_counts[p-1,n-1]+=1
        zero=[n-1 for n in target_nums]
        for a,b in combinations(zero,2):
            pair_counts[a,b]+=1; pair_counts[b,a]+=1
        for tri in combinations(zero,3):
            triple_counts[tuple(sorted(tri))]+=1

    return {
        'X': np.asarray(rows,dtype=np.float32),
        'y': np.asarray(ys,dtype=np.int8),
        'draw_idx': np.asarray(draw_idx,dtype=np.int32),
        'number_idx': np.asarray(number_idx,dtype=np.int16),
        'ymat': ymat,
        'availmat': availmat,
        'feature_names': feature_names,
        'groups': groups,
        'max_n': max_n,
        'k': k,
    }


def draw_rows(panel: dict[str,Any], start: int, end: int) -> np.ndarray:
    return (panel['draw_idx']>=start)&(panel['draw_idx']<end)


def normalize_panel_predictions(raw: np.ndarray, draw_indices: np.ndarray, number_indices: np.ndarray, draws: list[Draw], pool: str) -> np.ndarray:
    out=np.zeros_like(raw,dtype=float)
    k=5 if pool=='main' else 2
    for t in np.unique(draw_indices):
        m=draw_indices==t
        d=draws[int(t)]
        avail=np.ones(m.sum(),dtype=bool)
        out[m]=safe_prob_scale(raw[m],k,avail)
    return out


def predict_model(model: Any, X: np.ndarray) -> np.ndarray:
    if isinstance(model, BayesianRidge) or (hasattr(model,'steps') and isinstance(model.steps[-1][1],BayesianRidge)):
        z=model.predict(X)
        return 1/(1+np.exp(-np.clip(z,-20,20)))
    if hasattr(model,'predict_proba'):
        p=model.predict_proba(X)
        return p[:,1] if p.ndim==2 else p
    if hasattr(model,'decision_function'):
        z=model.decision_function(X)
        return 1/(1+np.exp(-np.clip(z,-20,20)))
    return np.clip(model.predict(X),1e-6,1-1e-6)


def model_factories() -> dict[str, list[tuple[str, Callable[[],Any]]]]:
    return {
        'Logistic_L2': [
            ('C0.1', lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1,max_iter=500,class_weight=None,solver='lbfgs'))),
            ('C1', lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0,max_iter=500,class_weight=None,solver='lbfgs'))),
            ('C10', lambda: make_pipeline(StandardScaler(), LogisticRegression(C=10.0,max_iter=500,class_weight=None,solver='lbfgs'))),
        ],
        'ElasticNet': [
            ('a0.0003_l0.15', lambda: make_pipeline(StandardScaler(), SGDClassifier(loss='log_loss',penalty='elasticnet',alpha=3e-4,l1_ratio=0.15,max_iter=700,tol=2e-4,random_state=RNG_SEED))),
            ('a0.001_l0.5', lambda: make_pipeline(StandardScaler(), SGDClassifier(loss='log_loss',penalty='elasticnet',alpha=1e-3,l1_ratio=0.5,max_iter=700,tol=2e-4,random_state=RNG_SEED))),
        ],
        'GradientBoosting': [
            ('d1_lr0.03', lambda: GradientBoostingClassifier(n_estimators=40,learning_rate=0.05,max_depth=1,random_state=RNG_SEED)),
            ('d2_lr0.03', lambda: GradientBoostingClassifier(n_estimators=40,learning_rate=0.05,max_depth=2,random_state=RNG_SEED)),
        ],
        'RandomForest': [
            ('leaf50', lambda: RandomForestClassifier(n_estimators=60,max_depth=7,min_samples_leaf=50,max_features='sqrt',n_jobs=-1,random_state=RNG_SEED)),
            ('leaf100', lambda: RandomForestClassifier(n_estimators=60,max_depth=7,min_samples_leaf=100,max_features='sqrt',n_jobs=-1,random_state=RNG_SEED)),
        ],
        'ExtraTrees': [
            ('leaf50', lambda: ExtraTreesClassifier(n_estimators=70,max_depth=8,min_samples_leaf=50,max_features='sqrt',n_jobs=-1,random_state=RNG_SEED)),
            ('leaf100', lambda: ExtraTreesClassifier(n_estimators=70,max_depth=8,min_samples_leaf=100,max_features='sqrt',n_jobs=-1,random_state=RNG_SEED)),
        ],
        'HistGradientBoosting': [
            ('leaf40_l2', lambda: HistGradientBoostingClassifier(max_iter=60,learning_rate=0.06,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=2.0,random_state=RNG_SEED)),
            ('leaf80_l5', lambda: HistGradientBoostingClassifier(max_iter=60,learning_rate=0.06,max_leaf_nodes=15,min_samples_leaf=80,l2_regularization=5.0,random_state=RNG_SEED)),
        ],
        'Bayesian_GLM_Laplace': [
            ('ridge1', lambda: make_pipeline(StandardScaler(), BayesianRidge(alpha_1=1e-6,alpha_2=1e-6,lambda_1=1e-4,lambda_2=1e-4))),
        ],
    }


def feature_screen(panel: dict[str,Any], draws: list[Draw], pool: str, dev_end: int, permutations: int=10) -> tuple[list[int],list[dict[str,Any]]]:
    split=max(120,int(dev_end*0.80))
    tr=draw_rows(panel,0,split)
    va=draw_rows(panel,split,dev_end)
    base=make_pipeline(StandardScaler(),LogisticRegression(C=0.2,max_iter=500,solver='lbfgs'))
    base.fit(panel['X'][tr],panel['y'][tr])
    pred=predict_model(base,panel['X'][va])
    pred=normalize_panel_predictions(pred,panel['draw_idx'][va],panel['number_idx'][va],draws,pool)
    y=panel['y'][va]
    base_brier=float(np.mean((pred-y)**2))
    rng=np.random.default_rng(RNG_SEED+1)
    results=[]
    keep=set(panel['groups']['identity'])
    unique_draws=np.unique(panel['draw_idx'][va])
    for g,cols in panel['groups'].items():
        if g=='identity':
            results.append({'group':g,'base_brier':base_brier,'mean_permutation_delta':0.0,'p_value':0.0,'keep':True})
            continue
        deltas=[]
        for _ in range(permutations):
            Xp=panel['X'][va].copy()
            for td in unique_draws:
                m=np.where(panel['draw_idx'][va]==td)[0]
                perm=rng.permutation(m)
                Xp[np.ix_(m,cols)]=Xp[np.ix_(perm,cols)]
            pp=predict_model(base,Xp)
            pp=normalize_panel_predictions(pp,panel['draw_idx'][va],panel['number_idx'][va],draws,pool)
            deltas.append(float(np.mean((pp-y)**2)-base_brier))
        mean_delta=float(np.mean(deltas))
        pval=float((1+sum(d<=0 for d in deltas))/(1+len(deltas)))
        keep_group=mean_delta>1e-6 and np.quantile(deltas,0.10)>0
        if keep_group: keep.update(cols)
        results.append({'group':g,'base_brier':base_brier,'mean_permutation_delta':mean_delta,'p_value':pval,'keep':bool(keep_group)})
    return sorted(keep),results


def score_panel(y: np.ndarray,p: np.ndarray,draw_idx: np.ndarray,number_idx: np.ndarray,k:int) -> dict[str,float]:
    p=np.clip(p,1e-8,1-1e-8)
    brier=float(np.mean((p-y)**2))
    ll=float(log_loss(y,p,labels=[0,1]))
    hits=[]; ranks=[]
    for t in np.unique(draw_idx):
        m=draw_idx==t
        pt=p[m]; yt=y[m]
        order=np.argsort(-pt)
        hits.append(int(yt[order[:k]].sum()))
        win_pos=np.where(yt[order]==1)[0]+1
        ranks.extend(win_pos.tolist())
    # ECE
    bins=np.linspace(0,1,11); ece=0.0
    for a,b in zip(bins[:-1],bins[1:]):
        m=(p>=a)&(p<(b if b<1 else b+1e-9))
        if m.any(): ece+=m.mean()*abs(float(y[m].mean()-p[m].mean()))
    return {'brier':brier,'log_loss':ll,'ece':float(ece),'avg_hits':float(np.mean(hits)),'precision_at_k':float(np.mean(hits)/k),'mean_winning_rank':float(np.mean(ranks)),'draws':int(len(hits))}


def choose_stat_params(draws:list[Draw],panel:dict[str,Any],pool:str,train_end:int,valid_start:int,valid_end:int) -> dict[str,tuple[Any,float]]:
    methods={
        'FullFrequency':[10,30,80],
        'RollingFrequency':[25,50,100,200],
        'EWMA':[15,30,60,120],
        'BetaBinomial':[20,50,100],
        'HierarchicalBayes':[30,80,150],
        'DynamicState':[0.90,0.95,0.98,0.99],
    }
    ymat,avail=panel['ymat'],panel['availmat']
    mapping={'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
    out={}
    for name,params in methods.items():
        best=(None,1e9)
        for param in params:
            ys=[];ps=[];ds=[];ns=[]
            for t in range(valid_start,valid_end):
                pred=statistical_prediction(ymat[:t],avail[:t],draws[t],pool,mapping[name],param)
                target_pool=50 if pool=='main' else draws[t].euro_pool
                for j in range(target_pool):
                    ys.append(int(ymat[t,j]));ps.append(pred[j]);ds.append(t);ns.append(j)
            sc=score_panel(np.asarray(ys),np.asarray(ps),np.asarray(ds),np.asarray(ns),panel['k'])
            if sc['brier']<best[1]: best=(param,sc['brier'])
        out[name]=best
    return out


def nested_oos(draws:list[Draw],panel:dict[str,Any],pool:str,selected_cols:list[int],dev_end:int) -> tuple[dict[str,dict[int,np.ndarray]],dict[str,list[dict[str,Any]]],dict[str,str],dict[str,Any]]:
    # Four expanding outer validation blocks wholly inside development set.
    min_train=max(220,int(dev_end*0.40))
    edges=np.linspace(min_train,dev_end,4,dtype=int)
    oos:dict[str,dict[int,np.ndarray]]=defaultdict(dict)
    fold_metrics:dict[str,list[dict[str,Any]]]=defaultdict(list)
    chosen_ml:dict[str,list[str]]=defaultdict(list)
    chosen_stat:dict[str,list[Any]]=defaultdict(list)
    factories=model_factories()
    ymat,avail=panel['ymat'],panel['availmat']
    uniform_name='Uniform'

    for fold in range(3):
        train_end=int(edges[fold]); valid_end=int(edges[fold+1]); valid_start=train_end
        inner_len=max(40,int(train_end*0.15)); inner_start=train_end-inner_len
        fit_end=inner_start
        # Uniform and statistical families.
        stat_params=choose_stat_params(draws,panel,pool,fit_end,inner_start,train_end)
        for n,(par,_) in stat_params.items(): chosen_stat[n].append(par)
        for t in range(valid_start,valid_end):
            oos[uniform_name][t]=uniform_prediction(pool,draws[t])
            mapping={'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
            for n,(par,_) in stat_params.items():
                oos[n][t]=statistical_prediction(ymat[:t],avail[:t],draws[t],pool,mapping[n],par)

        # Tune each ML family on internal validation, then fit on all outer training and predict outer block.
        tr_inner=draw_rows(panel,0,fit_end)
        va_inner=draw_rows(panel,inner_start,train_end)
        tr_outer=draw_rows(panel,0,train_end)
        va_outer=draw_rows(panel,valid_start,valid_end)
        X=panel['X'][:,selected_cols]
        for fam,variants in factories.items():
            best_label=None;best_factory=None;best_b=1e9
            for label,factory in variants:
                mdl=factory(); mdl.fit(X[tr_inner],panel['y'][tr_inner])
                pp=predict_model(mdl,X[va_inner])
                pp=normalize_panel_predictions(pp,panel['draw_idx'][va_inner],panel['number_idx'][va_inner],draws,pool)
                b=float(np.mean((pp-panel['y'][va_inner])**2))
                if b<best_b: best_b=b;best_label=label;best_factory=factory
            chosen_ml[fam].append(str(best_label))
            mdl=best_factory(); mdl.fit(X[tr_outer],panel['y'][tr_outer])
            pp=predict_model(mdl,X[va_outer])
            pp=normalize_panel_predictions(pp,panel['draw_idx'][va_outer],panel['number_idx'][va_outer],draws,pool)
            di=panel['draw_idx'][va_outer];ni=panel['number_idx'][va_outer]
            for t in range(valid_start,valid_end):
                m=di==t; arr=np.zeros(panel['max_n']); arr[ni[m]]=pp[m]; oos[fam][t]=arr

    # Aggregate fold metrics.
    for name,preds in oos.items():
        for fold in range(3):
            a=int(edges[fold]);b=int(edges[fold+1]);ys=[];ps=[];ds=[];ns=[]
            for t in range(a,b):
                if t not in preds: continue
                target_pool=50 if pool=='main' else draws[t].euro_pool
                for j in range(target_pool):
                    ys.append(int(ymat[t,j]));ps.append(float(preds[t][j]));ds.append(t);ns.append(j)
            fold_metrics[name].append(score_panel(np.asarray(ys),np.asarray(ps),np.asarray(ds),np.asarray(ns),panel['k']))

    # Consensus hyperparameters by mode.
    def mode(vals:list[Any])->Any:
        return max(set(vals),key=vals.count)
    consensus={fam:mode(vals) for fam,vals in chosen_ml.items()}
    consensus_stat={fam:mode(vals) for fam,vals in chosen_stat.items()}
    return oos,fold_metrics,consensus,consensus_stat


def final_holdout_predictions(draws:list[Draw],panel:dict[str,Any],pool:str,selected_cols:list[int],dev_end:int,consensus_ml:dict[str,str],consensus_stat:dict[str,Any]) -> tuple[dict[str,dict[int,np.ndarray]],dict[str,Any]]:
    factories=model_factories(); ymat,avail=panel['ymat'],panel['availmat']; X=panel['X'][:,selected_cols]
    preds:dict[str,dict[int,np.ndarray]]=defaultdict(dict); fitted={}
    for t in range(dev_end,len(draws)):
        preds['Uniform'][t]=uniform_prediction(pool,draws[t])
        mapping={'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
        for n,par in consensus_stat.items(): preds[n][t]=statistical_prediction(ymat[:t],avail[:t],draws[t],pool,mapping[n],par)
    tr=draw_rows(panel,0,dev_end);ho=draw_rows(panel,dev_end,len(draws))
    for fam,label in consensus_ml.items():
        factory=dict(factories[fam])[label]; mdl=factory(); mdl.fit(X[tr],panel['y'][tr]); fitted[fam]=mdl
        pp=predict_model(mdl,X[ho]);pp=normalize_panel_predictions(pp,panel['draw_idx'][ho],panel['number_idx'][ho],draws,pool)
        di=panel['draw_idx'][ho];ni=panel['number_idx'][ho]
        for t in range(dev_end,len(draws)):
            m=di==t;arr=np.zeros(panel['max_n']);arr[ni[m]]=pp[m];preds[fam][t]=arr
    return preds,fitted


def flatten_predictions(preds:dict[int,np.ndarray],draws:list[Draw],panel:dict[str,Any],pool:str,start:int,end:int)->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    ys=[];ps=[];ds=[];ns=[]
    for t in range(start,end):
        if t not in preds: continue
        target_pool=50 if pool=='main' else draws[t].euro_pool
        for j in range(target_pool):
            ys.append(int(panel['ymat'][t,j]));ps.append(float(preds[t][j]));ds.append(t);ns.append(j)
    return np.asarray(ys),np.asarray(ps),np.asarray(ds),np.asarray(ns)


def optimize_ensemble(oos:dict[str,dict[int,np.ndarray]],draws:list[Draw],panel:dict[str,Any],pool:str,start:int,end:int)->tuple[list[str],np.ndarray]:
    names=sorted(oos.keys(),key=lambda x:(x!='Uniform',x))
    common=[t for t in range(start,end) if all(t in oos[n] for n in names)]
    rows=[];y=[]
    for t in common:
        target_pool=50 if pool=='main' else draws[t].euro_pool
        for j in range(target_pool):
            rows.append([oos[n][t][j] for n in names]);y.append(panel['ymat'][t,j])
    P=np.asarray(rows);y=np.asarray(y)
    m=len(names);u=names.index('Uniform')
    def obj(w):
        p=np.clip(P@w,1e-8,1-1e-8)
        return np.mean((p-y)**2)+0.0005*np.sum(w*w)
    cons=[{'type':'eq','fun':lambda w:np.sum(w)-1},{'type':'ineq','fun':lambda w:w[u]-0.40}]
    bounds=[(0,0.35) for _ in names];bounds[u]=(0.40,1.0)
    x0=np.full(m,0.6/(m-1));x0[u]=0.4
    res=minimize(obj,x0,method='SLSQP',bounds=bounds,constraints=cons,options={'maxiter':500})
    w=res.x if res.success else x0
    return names,w/w.sum()


def ensemble_predictions(base:dict[str,dict[int,np.ndarray]],names:list[str],weights:np.ndarray,start:int,end:int)->dict[int,np.ndarray]:
    out={}
    for t in range(start,end):
        if all(t in base[n] for n in names):
            out[t]=sum(weights[i]*base[n][t] for i,n in enumerate(names))
    return out


def hit_p_value(avg_hits:float,n_draws:int,pool_size:int,k:int)->float:
    # Random overlap has mean k^2/N and variance from hypergeometric.
    mean=k*k/pool_size
    var=k*(k/pool_size)*(1-k/pool_size)*((pool_size-k)/(pool_size-1))
    z=(avg_hits-mean)/math.sqrt(var/max(n_draws,1))
    return float(norm.sf(z))


def bootstrap_improvement(draws:list[Draw],panel:dict[str,Any],pool:str,pred_a:dict[int,np.ndarray],pred_b:dict[int,np.ndarray],start:int,end:int,B:int=1500)->dict[str,float]:
    diffs=[]
    for t in range(start,end):
        if t not in pred_a or t not in pred_b: continue
        target_pool=50 if pool=='main' else draws[t].euro_pool
        y=panel['ymat'][t,:target_pool]
        da=np.mean((pred_a[t][:target_pool]-y)**2)
        db=np.mean((pred_b[t][:target_pool]-y)**2)
        diffs.append(db-da) # positive means a better than b
    rng=np.random.default_rng(RNG_SEED+4);arr=np.asarray(diffs);boots=[]
    for _ in range(B): boots.append(float(rng.choice(arr,size=len(arr),replace=True).mean()))
    return {'mean_brier_improvement':float(arr.mean()),'ci_low':float(np.quantile(boots,0.025)),'ci_high':float(np.quantile(boots,0.975)),'prob_positive':float(np.mean(np.asarray(boots)>0))}


def next_feature_rows(panel:dict[str,Any],draws:list[Draw],pool:str)->tuple[np.ndarray,np.ndarray]:
    # Build one dummy future draw to invoke same feature generator; target values are ignored.
    last=draws[-1]
    next_date=date(2026,7,28)
    dummy=Draw(len(draws)+1,next_date,(1,2,3,4,5),(1,2),'R3_5of50_2of12',12,next_date.strftime('%A'),'Synthetic target','N/A','Feature generation only')
    extended=draws+[dummy]
    p2=build_features(extended,pool)
    m=p2['draw_idx']==len(draws)
    return p2['X'][m],p2['number_idx'][m]


def next_prediction(draws:list[Draw],panel:dict[str,Any],pool:str,selected_cols:list[int],consensus_ml:dict[str,str],consensus_stat:dict[str,Any],ens_names:list[str],ens_weights:np.ndarray)->tuple[np.ndarray,dict[str,np.ndarray]]:
    ymat,avail=panel['ymat'],panel['availmat'];target_date=date(2026,7,28)
    dummy=Draw(len(draws)+1,target_date,(1,2,3,4,5),(1,2),'R3_5of50_2of12',12,target_date.strftime('%A'),'Synthetic target','N/A','')
    base={}
    base['Uniform']=uniform_prediction(pool,dummy)
    mapping={'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
    for n,par in consensus_stat.items():base[n]=statistical_prediction(ymat,avail,dummy,pool,mapping[n],par)
    Xnext,nidx=next_feature_rows(panel,draws,pool);Xall=panel['X'][:,selected_cols];Xn=Xnext[:,selected_cols]
    factories=model_factories()
    for fam,label in consensus_ml.items():
        mdl=dict(factories[fam])[label]();mdl.fit(Xall,panel['y']);p=predict_model(mdl,Xn);p=safe_prob_scale(p,panel['k'],np.ones(len(p),dtype=bool));arr=np.zeros(panel['max_n']);arr[nidx]=p;base[fam]=arr
    final=sum(ens_weights[i]*base[n] for i,n in enumerate(ens_names))
    final=safe_prob_scale(final,panel['k'],np.ones(panel['max_n'],dtype=bool))
    return final,base


def portfolio(main_p:np.ndarray,euro_p:np.ndarray,history:list[Draw],lines:int=10)->list[dict[str,Any]]:
    rng=np.random.default_rng(RNG_SEED+7)
    sums=np.array([sum(d.main) for d in history]);lo,hi=np.quantile(sums,[0.10,0.90])
    candidates=[];seen=set()
    # Mostly probability-weighted, partially uniform for robust coverage.
    mp=0.35*main_p/main_p.sum()+0.65*np.full(50,1/50)
    ep=0.35*euro_p/euro_p.sum()+0.65*np.full(12,1/12)
    for _ in range(30000):
        m=tuple(sorted((rng.choice(np.arange(1,51),size=5,replace=False,p=mp))))
        e=tuple(sorted((rng.choice(np.arange(1,13),size=2,replace=False,p=ep))))
        key=(m,e)
        if key in seen: continue
        seen.add(key)
        odd=sum(n%2 for n in m); high=sum(n>25 for n in m); s=sum(m)
        seq=sum(1 for a,b in zip(m,m[1:]) if b-a==1)
        birthday=sum(n<=31 for n in m)
        obvious=int(m in [(1,2,3,4,5),(5,10,15,20,25)])
        model_score=float(sum(math.log(max(main_p[n-1],1e-8)) for n in m)+sum(math.log(max(euro_p[n-1],1e-8)) for n in e))
        balance=-0.30*abs(odd-2.5)-0.25*abs(high-2.5)-0.004*abs(s-np.median(sums))
        anti_crowd=0.18*sum(n>31 for n in m)-0.22*seq-0.12*max(0,birthday-3)-1.0*obvious
        range_pen=-1.0 if not (lo<=s<=hi) else 0.0
        score=model_score+balance+anti_crowd+range_pen
        candidates.append((score,m,e))
    candidates.sort(reverse=True,key=lambda x:x[0])
    selected=[];used_pairs=defaultdict(int);used_e=defaultdict(int)
    for score,m,e in candidates:
        if len(selected)>=lines:break
        overlap_pen=0
        for _,sm,se in selected:
            overlap_pen+=0.9*len(set(m)&set(sm))+1.2*len(set(e)&set(se))
        pair_pen=sum(used_pairs[p] for p in combinations(m,2))*0.4
        euro_pen=used_e[e]*0.8
        adj=score-overlap_pen-pair_pen-euro_pen
        # Greedy with threshold relative to current candidates.
        if not selected or adj>candidates[min(len(selected)*300,len(candidates)-1)][0]-6:
            selected.append((adj,m,e))
            for p in combinations(m,2):used_pairs[p]+=1
            used_e[e]+=1
    return [{'line':i+1,'main':list(m),'euro':list(e),'portfolio_score':float(s)} for i,(s,m,e) in enumerate(selected)]


def run_pool(draws:list[Draw],pool:str)->dict[str,Any]:
    print(f'[{pool}] build_features', flush=True)
    panel=build_features(draws,pool)
    print(f'[{pool}] feature_screen', flush=True)
    dev_end=int(len(draws)*0.80)
    selected,screen=feature_screen(panel,draws,pool,dev_end)
    print(f'[{pool}] nested_oos selected={len(selected)}', flush=True)
    oos,fold_metrics,cons_ml,cons_stat=nested_oos(draws,panel,pool,selected,dev_end)
    print(f'[{pool}] final_holdout', flush=True)
    hold,fitted=final_holdout_predictions(draws,panel,pool,selected,dev_end,cons_ml,cons_stat)
    oos_start=min(min(v.keys()) for v in oos.values() if v)
    ens_names,ens_weights=optimize_ensemble(oos,draws,panel,pool,oos_start,dev_end)
    ens_hold=ensemble_predictions(hold,ens_names,ens_weights,dev_end,len(draws))
    hold_metrics={}
    for n,pd in hold.items():
        y,p,didx,nidx=flatten_predictions(pd,draws,panel,pool,dev_end,len(draws));hold_metrics[n]=score_panel(y,p,didx,nidx,panel['k'])
    y,p,didx,nidx=flatten_predictions(ens_hold,draws,panel,pool,dev_end,len(draws));hold_metrics['ConstrainedEnsemble']=score_panel(y,p,didx,nidx,panel['k'])
    # Period stability thirds on holdout.
    stability={}
    edges=np.linspace(dev_end,len(draws),4,dtype=int)
    for n,pd in {**hold,'ConstrainedEnsemble':ens_hold}.items():
        vals=[]
        for a,b in zip(edges[:-1],edges[1:]):
            yy,pp,dd,nn=flatten_predictions(pd,draws,panel,pool,int(a),int(b));vals.append(score_panel(yy,pp,dd,nn,panel['k'])['avg_hits'])
        stability[n]={'period_avg_hits':vals,'std':float(np.std(vals))}
    # Significance and multiple testing.
    pvals={n:hit_p_value(m['avg_hits'],m['draws'],50 if pool=='main' else 12,panel['k']) for n,m in hold_metrics.items()}
    mtests=len(pvals);adj={n:min(1.0,p*mtests) for n,p in pvals.items()}
    boot=bootstrap_improvement(draws,panel,pool,ens_hold,hold['Uniform'],dev_end,len(draws))
    criteria={
        'lower_brier_than_uniform':hold_metrics['ConstrainedEnsemble']['brier']<hold_metrics['Uniform']['brier'],
        'lower_log_loss_than_uniform':hold_metrics['ConstrainedEnsemble']['log_loss']<hold_metrics['Uniform']['log_loss'],
        'better_all_three_periods':all(a>b for a,b in zip(stability['ConstrainedEnsemble']['period_avg_hits'],stability['Uniform']['period_avg_hits'])),
        'adjusted_p_below_0_05':adj['ConstrainedEnsemble']<0.05,
        'bootstrap_ci_positive':boot['ci_low']>0,
        'stable_rankings':stability['ConstrainedEnsemble']['std']<=stability['Uniform']['std']+0.05,
    }
    if all(criteria.values()):status='Validated signal'
    elif criteria['lower_brier_than_uniform'] or criteria['lower_log_loss_than_uniform'] or boot['prob_positive']>0.80:status='Weak experimental signal'
    else:status='Uniform mode'
    print(f'[{pool}] next_prediction', flush=True)
    next_p,next_base=next_prediction(draws,panel,pool,selected,cons_ml,cons_stat,ens_names,ens_weights)
    return {
        'panel':panel,'dev_end':dev_end,'selected_cols':selected,'feature_screen':screen,
        'fold_metrics':fold_metrics,'consensus_ml':cons_ml,'consensus_stat':cons_stat,
        'ensemble_names':ens_names,'ensemble_weights':ens_weights.tolist(),
        'holdout_metrics':hold_metrics,'stability':stability,'raw_p_values':pvals,'bonferroni_p_values':adj,
        'bootstrap':boot,'acceptance_criteria':criteria,'status':status,'next_probability':next_p,'next_base':next_base,
    }


def main() -> None:
    draws=load_draws();export_draws(draws)
    main_res=run_pool(draws,'main');euro_res=run_pool(draws,'euro')
    main_p=main_res['next_probability'];euro_p=euro_res['next_probability']
    port=portfolio(main_p,euro_p,draws,10)
    with OUT_PRED.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['pool','number','ensemble_probability','uniform_probability','rank'])
        for pool,p,k in [('Main',main_p,5),('Euro',euro_p,2)]:
            order=np.argsort(-p)
            for rank,j in enumerate(order,1):w.writerow([pool,j+1,float(p[j]),k/len(p),rank])
    with OUT_PORTFOLIO.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['line','main_1','main_2','main_3','main_4','main_5','euro_1','euro_2','portfolio_score'])
        for r in port:w.writerow([r['line'],*r['main'],*r['euro'],r['portfolio_score']])

    def serializable_pool(r:dict[str,Any])->dict[str,Any]:
        return {
            'dev_draws':r['dev_end'],'holdout_draws':len(draws)-r['dev_end'],
            'feature_screen':r['feature_screen'],
            'selected_features':[r['panel']['feature_names'][i] for i in r['selected_cols']],
            'nested_fold_metrics':r['fold_metrics'],
            'consensus_ml_hyperparameters':r['consensus_ml'],'consensus_statistical_hyperparameters':r['consensus_stat'],
            'ensemble_weights':dict(zip(r['ensemble_names'],r['ensemble_weights'])),
            'holdout_metrics':r['holdout_metrics'],'stability':r['stability'],
            'raw_p_values':r['raw_p_values'],'bonferroni_p_values':r['bonferroni_p_values'],
            'bootstrap':r['bootstrap'],'acceptance_criteria':r['acceptance_criteria'],'status':r['status'],
            'next_probabilities':{str(i+1):float(v) for i,v in enumerate(r['next_probability'])},
        }
    total_combos=math.comb(50,5)*math.comb(12,2)
    result={
        'engine_version':'2.0.0','generated_on':'2026-07-26','next_draw_date':'2026-07-28','random_seed':RNG_SEED,
        'data':{'draws':len(draws),'first_date':draws[0].draw_date.isoformat(),'last_date':draws[-1].draw_date.isoformat(),'rule_counts':dict((rv,sum(d.rule_version==rv for d in draws)) for rv in sorted(set(d.rule_version for d in draws))),'corrections':sum(bool(d.correction_note) for d in draws),'source_urls':SOURCE_URLS},
        'mathematics':{'current_total_combinations':total_combos,'jackpot_probability_per_line':1/total_combos,'expected_main_hits_uniform':0.5,'expected_euro_hits_uniform':2*2/12,'portfolio_unique_lines':len(port),'portfolio_jackpot_probability_if_unique':len(port)/total_combos},
        'main_pool':serializable_pool(main_res),'euro_pool':serializable_pool(euro_res),
        'overall_status':'Validated signal' if main_res['status']=='Validated signal' and euro_res['status']=='Validated signal' else ('Weak experimental signal' if 'Weak experimental signal' in (main_res['status'],euro_res['status']) else 'Uniform mode'),
        'primary_line':port[0],'portfolio':port,
        'limitations':['Lottery draws are designed to be independent and random.','Historical fit cannot guarantee future predictive advantage.','Multiple-testing correction and untouched holdout results govern the confidence state.','Ticket diversification changes coverage and possible prize sharing, not the probability of a specific combination.'],
    }
    OUT_RESULTS.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'draws':len(draws),'main_status':main_res['status'],'euro_status':euro_res['status'],'overall':result['overall_status'],'primary_line':result['primary_line'],'files':[str(OUT_DATA),str(OUT_RESULTS),str(OUT_PRED),str(OUT_PORTFOLIO)]},indent=2))

if __name__=='__main__':
    main()

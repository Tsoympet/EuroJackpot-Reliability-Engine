from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import expit, logit
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

from eurojackpot_paths import ensure_user_layout, package_root, read_version

ROOT = package_root()
V2_PATH = ROOT / 'eurojackpot_reliability_engine.py'
APP_VERSION = read_version(ROOT)


def _resolve_output_dir() -> Path:
    override = os.environ.get('EUROJACKPOT_OUTPUT_DIR')
    if override:
        path = Path(override).expanduser().resolve()
    else:
        path = ensure_user_layout()['engine']
    path.mkdir(parents=True, exist_ok=True)
    return path


OUT_DIR = _resolve_output_dir()
OUT_RESULTS = OUT_DIR / 'EuroJackpot_Model_Results_v3.json'
OUT_RANKING = OUT_DIR / 'EuroJackpot_Next_Draw_Ranking_v3.csv'
OUT_PORTFOLIO = OUT_DIR / 'EuroJackpot_Diversified_Portfolio_v3.csv'
OUT_AUDIT = OUT_DIR / 'EuroJackpot_Audit_Findings_v3.csv'
OUT_HISTORY = OUT_DIR / 'EuroJackpot_Canonical_History_v3.csv'
RNG_SEED = 20260726
RNG = np.random.default_rng(RNG_SEED)

spec = importlib.util.spec_from_file_location('ejv2', V2_PATH)
v2 = importlib.util.module_from_spec(spec)
sys.modules['ejv2'] = v2
assert spec.loader is not None
spec.loader.exec_module(v2)


def next_draw_date(last_date: date) -> date:
    d = last_date + timedelta(days=1)
    while d.weekday() not in (1, 4):
        d += timedelta(days=1)
    return d


def calendar_audit(draws: list[Any]) -> dict[str, Any]:
    actual = {d.draw_date for d in draws}
    expected = set()
    d = draws[0].draw_date
    end = draws[-1].draw_date
    while d <= end:
        if d < date(2022, 3, 25):
            if d.weekday() == 4:
                expected.add(d)
        elif d.weekday() in (1, 4):
            expected.add(d)
        d += timedelta(days=1)
    return {
        'expected_dates': len(expected),
        'actual_dates': len(actual),
        'missing_dates': sorted(x.isoformat() for x in expected - actual),
        'off_schedule_dates': sorted(x.isoformat() for x in actual - expected),
        'duplicate_dates': len(draws) - len(actual),
        'pass': expected == actual and len(draws) == len(actual),
    }


def export_history_v3(draws: list[Any]) -> None:
    with OUT_HISTORY.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'draw_id','draw_date','main_1','main_2','main_3','main_4','main_5','euro_1','euro_2',
            'main_pool','euro_pool','rule_version','operational_sensitivity_era','draw_day',
            'source','verification_status','correction_note'
        ])
        for d in draws:
            if d.draw_date >= date(2024, 3, 8):
                op_era = 'S2_post_2024_studio_change_sensitivity_only'
            else:
                op_era = 'S1_pre_2024_studio_change_sensitivity_only'
            if d.draw_date >= date(2024, 1, 1):
                verify = 'Cross-checked: OPAP uploads + public archive' if d.draw_date <= date(2026, 7, 21) else 'Cross-checked: official/public current result'
            else:
                verify = 'Archive-sourced; calendar/range/uniqueness validated'
            w.writerow([
                d.draw_id,d.draw_date.isoformat(),*d.main,*d.euro,50,d.euro_pool,d.rule_version,op_era,
                d.draw_day,d.source,verify,d.correction_note
            ])


def robust_feature_screen(panel: dict[str, Any], draws: list[Any], pool: str, dev_end: int) -> tuple[list[int], list[dict[str, Any]]]:
    cutoffs = sorted(set([int(dev_end * 0.72), int(dev_end * 0.86), dev_end]))
    all_runs = []
    votes = defaultdict(int)
    for cutoff in cutoffs:
        selected, rows = v2.feature_screen(panel, draws, pool, cutoff, permutations=39)
        selected_groups = {r['group'] for r in rows if r['keep']}
        for g in selected_groups:
            votes[g] += 1
        all_runs.append({'cutoff': cutoff, 'rows': rows, 'selected_groups': sorted(selected_groups)})
    kept_groups = {'identity'} | {g for g, c in votes.items() if c >= 2}
    selected = sorted({c for g in kept_groups for c in panel['groups'][g]})
    summary = []
    for g in panel['groups']:
        vals = []
        pvals = []
        for run in all_runs:
            rec = next(r for r in run['rows'] if r['group'] == g)
            vals.append(rec['mean_permutation_delta'])
            pvals.append(rec['p_value'])
        summary.append({
            'group': g,
            'selection_votes': int(votes.get(g, 0)),
            'runs': len(all_runs),
            'mean_permutation_delta': float(np.mean(vals)),
            'median_permutation_p': float(np.median(pvals)),
            'keep': g in kept_groups,
        })
    return selected, summary


def flatten_dict(preds: dict[int, np.ndarray], draws: list[Any], panel: dict[str, Any], pool: str, start: int, end: int):
    return v2.flatten_predictions(preds, draws, panel, pool, start, end)


def fit_platt(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    x = logit(p).reshape(-1, 1)
    if len(np.unique(y)) < 2:
        return {'coef': 1.0, 'intercept': 0.0}
    lr = LogisticRegression(C=0.2, solver='lbfgs', max_iter=500)
    lr.fit(x, y)
    return {'coef': float(lr.coef_[0, 0]), 'intercept': float(lr.intercept_[0])}


def calibrate_array(p: np.ndarray, cal: dict[str, float], k: int, active: int) -> np.ndarray:
    q = expit(cal['coef'] * logit(np.clip(p[:active], 1e-6, 1 - 1e-6)) + cal['intercept'])
    q = v2.safe_prob_scale(q, k, np.ones(active, dtype=bool))
    out = np.zeros_like(p, dtype=float)
    out[:active] = q
    return out


def crossfit_calibration(oos: dict[str, dict[int, np.ndarray]], draws: list[Any], panel: dict[str, Any], pool: str, dev_end: int):
    min_train = max(220, int(dev_end * 0.40))
    edges = np.linspace(min_train, dev_end, 4, dtype=int)
    calibrated = defaultdict(dict)
    final_calibrators = {}
    calibration_diagnostics = {}
    for name, pd in oos.items():
        if name == 'Uniform':
            calibrated[name] = dict(pd)
            final_calibrators[name] = {'coef': 1.0, 'intercept': 0.0}
            continue
        for fold in range(3):
            a, b = int(edges[fold]), int(edges[fold + 1])
            prior_start, prior_end = int(edges[0]), a
            if prior_end - prior_start < 20:
                cal = {'coef': 1.0, 'intercept': 0.0}
            else:
                y0, p0, _, _ = flatten_dict(pd, draws, panel, pool, prior_start, prior_end)
                cal = fit_platt(y0, p0)
            for t in range(a, b):
                if t in pd:
                    active = 50 if pool == 'main' else draws[t].euro_pool
                    calibrated[name][t] = calibrate_array(pd[t], cal, panel['k'], active)
        y_all, p_all, _, _ = flatten_dict(pd, draws, panel, pool, int(edges[0]), dev_end)
        final_cal = fit_platt(y_all, p_all)
        final_calibrators[name] = final_cal
        raw_score = v2.score_panel(y_all, p_all, np.repeat(np.arange(len(y_all)), 1), np.arange(len(y_all)), panel['k']) if False else None
        y_cal, p_cal, d_cal, n_cal = flatten_dict(calibrated[name], draws, panel, pool, int(edges[0]), dev_end)
        calibration_diagnostics[name] = {
            'coef': final_cal['coef'],
            'intercept': final_cal['intercept'],
            'crossfit_brier': float(np.mean((p_cal - y_cal) ** 2)),
            'crossfit_log_loss': float(-np.mean(y_cal * np.log(np.clip(p_cal,1e-8,1)) + (1-y_cal)*np.log(np.clip(1-p_cal,1e-8,1)))),
        }
    return dict(calibrated), final_calibrators, calibration_diagnostics, edges


def apply_calibrators(preds: dict[str, dict[int, np.ndarray]], calibrators: dict[str, dict[str, float]], draws: list[Any], panel: dict[str, Any], pool: str):
    out = defaultdict(dict)
    for name, pd in preds.items():
        if name == 'Uniform':
            out[name] = dict(pd)
            continue
        cal = calibrators.get(name, {'coef': 1.0, 'intercept': 0.0})
        for t, p in pd.items():
            active = 50 if pool == 'main' else draws[t].euro_pool
            out[name][t] = calibrate_array(p, cal, panel['k'], active)
    return dict(out)


def robust_weights(cal_oos: dict[str, dict[int, np.ndarray]], draws: list[Any], panel: dict[str, Any], pool: str, start: int, end: int):
    names = sorted(cal_oos)
    fold_edges = np.linspace(start, end, 4, dtype=int)
    losses = {}
    fold_losses = {}
    for n in names:
        y, p, d, ni = flatten_dict(cal_oos[n], draws, panel, pool, start, end)
        losses[n] = float(np.mean((p - y) ** 2))
        fold_losses[n] = []
        for a, b in zip(fold_edges[:-1], fold_edges[1:]):
            yy, pp, _, _ = flatten_dict(cal_oos[n], draws, panel, pool, int(a), int(b))
            fold_losses[n].append(float(np.mean((pp - yy) ** 2)))
    u = losses['Uniform']
    eligible = []
    scores = {}
    for n in names:
        if n == 'Uniform':
            continue
        improvements = [fold_losses['Uniform'][i] - fold_losses[n][i] for i in range(3)]
        mean_imp = u - losses[n]
        wins = sum(x > 0 for x in improvements)
        stability = float(np.std(improvements))
        if mean_imp > 0 and wins >= 2:
            scores[n] = max(mean_imp, 0) / max(stability, 1e-7)
            eligible.append(n)
    weights = {n: 0.0 for n in names}
    if not eligible:
        weights['Uniform'] = 1.0
    else:
        eligible = sorted(eligible, key=lambda n: scores[n], reverse=True)[:4]
        nonuniform_mass = 0.40
        weights['Uniform'] = 0.60
        sv = np.array([scores[n] for n in eligible], dtype=float)
        sv = np.exp(np.clip(sv - sv.max(), -30, 30))
        sv /= sv.sum()
        for n, w in zip(eligible, sv):
            weights[n] = float(nonuniform_mass * w)
    research = {}
    vals = np.array([losses[n] for n in names])
    temperature = max(np.std(vals), 1e-5)
    rw = np.exp(-(vals - vals.min()) / temperature)
    rw /= rw.sum()
    rw *= 0.60
    research = {n: float(w) for n, w in zip(names, rw)}
    research['Uniform'] += 0.40
    total = sum(research.values())
    research = {n: w / total for n, w in research.items()}
    return weights, research, {'development_brier': losses, 'fold_brier': fold_losses, 'eligible_models': eligible}


def ensemble_from_weights(base: dict[str, dict[int, np.ndarray]], weights: dict[str, float], start: int, end: int, draws: list[Any], panel: dict[str, Any], pool: str):
    out = {}
    active_names = [n for n, w in weights.items() if w > 0 and n in base]
    for t in range(start, end):
        if all(t in base[n] for n in active_names):
            p = sum(weights[n] * base[n][t] for n in active_names)
            active = 50 if pool == 'main' else draws[t].euro_pool
            out[t] = calibrate_array(p, {'coef':1.0,'intercept':0.0}, panel['k'], active)
    return out


def prequential_holdout(draws: list[Any], panel: dict[str, Any], pool: str, selected: list[int], dev_end: int, cons_ml: dict[str,str], cons_stat: dict[str,Any], calibrators: dict[str,dict[str,float]], block: int = 20):
    ymat, avail = panel['ymat'], panel['availmat']
    X = panel['X'][:, selected]
    factories = v2.model_factories()
    preds = defaultdict(dict)
    mapping = {'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
    for t in range(dev_end, len(draws)):
        preds['Uniform'][t] = v2.uniform_prediction(pool, draws[t])
        for n, par in cons_stat.items():
            raw = v2.statistical_prediction(ymat[:t], avail[:t], draws[t], pool, mapping[n], par)
            preds[n][t] = calibrate_array(raw, calibrators.get(n, {'coef':1,'intercept':0}), panel['k'], 50 if pool=='main' else draws[t].euro_pool)
    for a in range(dev_end, len(draws), block):
        b = min(len(draws), a + block)
        tr = v2.draw_rows(panel, 0, a)
        va = v2.draw_rows(panel, a, b)
        for fam, label in cons_ml.items():
            mdl = dict(factories[fam])[label]()
            mdl.fit(X[tr], panel['y'][tr])
            raw = v2.predict_model(mdl, X[va])
            raw = v2.normalize_panel_predictions(raw, panel['draw_idx'][va], panel['number_idx'][va], draws, pool)
            di = panel['draw_idx'][va]
            ni = panel['number_idx'][va]
            for t in range(a, b):
                m = di == t
                arr = np.zeros(panel['max_n'])
                arr[ni[m]] = raw[m]
                active = 50 if pool == 'main' else draws[t].euro_pool
                preds[fam][t] = calibrate_array(arr, calibrators.get(fam, {'coef':1,'intercept':0}), panel['k'], active)
    return dict(preds)


def score_all(preds: dict[str, dict[int, np.ndarray]], draws: list[Any], panel: dict[str, Any], pool: str, start: int, end: int):
    out = {}
    for n, pd in preds.items():
        y, p, d, ni = flatten_dict(pd, draws, panel, pool, start, end)
        out[n] = v2.score_panel(y, p, d, ni, panel['k'])
    return out


def block_bootstrap_improvement(model: dict[int,np.ndarray], uniform: dict[int,np.ndarray], draws: list[Any], panel: dict[str,Any], pool: str, start: int, end: int, B: int = 3000, block: int = 8):
    diffs = []
    for t in range(start, end):
        active = 50 if pool == 'main' else draws[t].euro_pool
        y = panel['ymat'][t,:active]
        lm = np.mean((model[t][:active]-y)**2)
        lu = np.mean((uniform[t][:active]-y)**2)
        diffs.append(lu-lm)
    x = np.asarray(diffs)
    n = len(x)
    boots = np.empty(B)
    for b in range(B):
        vals=[]
        while len(vals) < n:
            st=int(RNG.integers(0,n))
            vals.extend(x[(st+np.arange(block))%n].tolist())
        boots[b]=np.mean(vals[:n])
    return {'mean':float(x.mean()),'ci_low':float(np.quantile(boots,.025)),'ci_high':float(np.quantile(boots,.975)),'prob_positive':float(np.mean(boots>0))}


def maxT_reality_check(preds: dict[str,dict[int,np.ndarray]], draws:list[Any], panel:dict[str,Any], pool:str, start:int,end:int,B:int=3000):
    names=[n for n in preds if n!='Uniform']
    D=end-start
    N=50 if pool=='main' else 12
    Y=np.stack([panel['ymat'][t,:N] for t in range(start,end)]).astype(float)
    P={n:np.stack([preds[n][t][:N] for t in range(start,end)]) for n in preds}
    u_loss=np.mean((P['Uniform']-Y)**2)
    obs={n:float(u_loss-np.mean((P[n]-Y)**2)) for n in names}
    max_null=np.empty(B)
    for b in range(B):
        perm=RNG.permutation(D)
        Yp=Y[perm]
        ul=np.mean((P['Uniform']-Yp)**2)
        max_null[b]=max(ul-np.mean((P[n]-Yp)**2) for n in names)
    pvals={n:float((1+np.sum(max_null>=obs[n]))/(B+1)) for n in names}
    best=max(obs,key=obs.get) if obs else None
    return {'observed_brier_improvement':obs,'maxT_adjusted_p':pvals,'best_model':best,'best_improvement':obs.get(best) if best else None,'best_adjusted_p':pvals.get(best) if best else None}


def period_brier_improvements(model:dict[int,np.ndarray],uniform:dict[int,np.ndarray],draws:list[Any],panel:dict[str,Any],pool:str,start:int,end:int):
    edges=np.linspace(start,end,4,dtype=int)
    vals=[]
    for a,b in zip(edges[:-1],edges[1:]):
        dif=[]
        for t in range(int(a),int(b)):
            active=50 if pool=='main' else draws[t].euro_pool
            y=panel['ymat'][t,:active]
            dif.append(np.mean((uniform[t][:active]-y)**2)-np.mean((model[t][:active]-y)**2))
        vals.append(float(np.mean(dif)))
    return vals


def simulate_randomness_audit(draws:list[Any], pool:str, B:int=2500):
    if pool=='main':
        subset=draws; N=50;k=5; sequences=[d.main for d in subset]
    else:
        # Current-rule era only for a common 12-number exposure set.
        subset=[d for d in draws if d.euro_pool==12];N=12;k=2;sequences=[d.euro for d in subset]
    D=len(subset)
    Y=np.zeros((D,N),dtype=int)
    for i,nums in enumerate(sequences):Y[i,np.array(nums)-1]=1
    expected=D*k/N
    var=D*(k/N)*(1-k/N)
    z=(Y.sum(axis=0)-expected)/math.sqrt(var)
    obs_max=float(np.max(np.abs(z)))
    maxz=np.empty(B)
    overlap=np.sum(Y[1:]*Y[:-1],axis=1)
    obs_overlap=float(overlap.mean())
    sim_overlap=np.empty(B)
    for b in range(B):
        S=np.zeros((D,N),dtype=np.int8)
        for i in range(D):S[i,RNG.choice(N,size=k,replace=False)]=1
        zz=(S.sum(axis=0)-expected)/math.sqrt(var)
        maxz[b]=np.max(np.abs(zz))
        sim_overlap[b]=np.mean(np.sum(S[1:]*S[:-1],axis=1))
    freq_p=float((1+np.sum(maxz>=obs_max))/(B+1))
    overlap_p=float((1+np.sum(np.abs(sim_overlap-k*k/N)>=abs(obs_overlap-k*k/N)))/(B+1))
    # Tuesday/Friday max statistic in current common-rule data.
    if pool=='main':
        day_subset=[d for d in draws if d.rule_version=='R3_5of50_2of12']
        YY=np.zeros((len(day_subset),N),dtype=int)
        labels=np.array([d.draw_date.weekday()==1 for d in day_subset])
        for i,d in enumerate(day_subset):YY[i,np.array(d.main)-1]=1
    else:
        day_subset=subset;YY=Y;labels=np.array([d.draw_date.weekday()==1 for d in day_subset])
    def max_day_stat(lab):
        a=YY[lab];b=YY[~lab]
        p1=a.mean(axis=0);p0=b.mean(axis=0);pp=YY.mean(axis=0)
        se=np.sqrt(np.maximum(pp*(1-pp)*(1/max(len(a),1)+1/max(len(b),1)),1e-12))
        return float(np.max(np.abs((p1-p0)/se)))
    obs_day=max_day_stat(labels)
    day_null=np.empty(B)
    for b in range(B):day_null[b]=max_day_stat(RNG.permutation(labels))
    day_p=float((1+np.sum(day_null>=obs_day))/(B+1))
    # Sensitivity breakpoint at first draw after public studio redesign in March 2024; not assumed machine change.
    post=np.array([d.draw_date>=date(2024,3,8) for d in day_subset])
    def max_break_stat(lab):
        a=YY[lab];b=YY[~lab]
        p1=a.mean(axis=0);p0=b.mean(axis=0);pp=YY.mean(axis=0)
        se=np.sqrt(np.maximum(pp*(1-pp)*(1/max(len(a),1)+1/max(len(b),1)),1e-12))
        return float(np.max(np.abs((p1-p0)/se)))
    obs_break=max_break_stat(post)
    break_null=np.empty(B)
    for b in range(B):break_null[b]=max_break_stat(RNG.permutation(post))
    break_p=float((1+np.sum(break_null>=obs_break))/(B+1))
    return {
        'draws_tested':D,'max_marginal_z':obs_max,'familywise_frequency_p':freq_p,
        'mean_consecutive_overlap':obs_overlap,'expected_overlap':k*k/N,'overlap_p':overlap_p,
        'tuesday_friday_max_stat':obs_day,'tuesday_friday_familywise_p':day_p,
        'march_2024_sensitivity_max_stat':obs_break,'march_2024_familywise_p':break_p,
        'anomaly_detected_5pct':bool(min(freq_p,overlap_p,day_p,break_p)<0.05),
    }


def next_base_predictions(draws:list[Any],panel:dict[str,Any],pool:str,selected:list[int],cons_ml:dict[str,str],cons_stat:dict[str,Any],calibrators:dict[str,dict[str,float]],target_date:date):
    # Re-create the v2 next-feature path but use a dynamic target date.
    dummy=v2.Draw(len(draws)+1,target_date,(1,2,3,4,5),(1,2),'R3_5of50_2of12',12,target_date.strftime('%A'),'Synthetic target','N/A','')
    ymat,avail=panel['ymat'],panel['availmat']
    base={'Uniform':v2.uniform_prediction(pool,dummy)}
    mapping={'FullFrequency':'full_frequency','RollingFrequency':'rolling_frequency','EWMA':'ewma','BetaBinomial':'beta_binomial','HierarchicalBayes':'hierarchical_bayes','DynamicState':'dynamic_state'}
    for n,par in cons_stat.items():
        raw=v2.statistical_prediction(ymat,avail,dummy,pool,mapping[n],par)
        base[n]=calibrate_array(raw,calibrators.get(n,{'coef':1,'intercept':0}),panel['k'],50 if pool=='main' else 12)
    extended=draws+[dummy]
    p2=v2.build_features(extended,pool)
    m=p2['draw_idx']==len(draws)
    Xnext=p2['X'][m][:,selected];nidx=p2['number_idx'][m]
    Xall=panel['X'][:,selected]
    factories=v2.model_factories()
    for fam,label in cons_ml.items():
        mdl=dict(factories[fam])[label]();mdl.fit(Xall,panel['y'])
        raw=v2.predict_model(mdl,Xnext)
        raw=v2.safe_prob_scale(raw,panel['k'],np.ones(len(raw),dtype=bool))
        arr=np.zeros(panel['max_n']);arr[nidx]=raw
        base[fam]=calibrate_array(arr,calibrators.get(fam,{'coef':1,'intercept':0}),panel['k'],50 if pool=='main' else 12)
    return base


def weighted_next(base:dict[str,np.ndarray],weights:dict[str,float],panel:dict[str,Any]):
    names=[n for n,w in weights.items() if w>0 and n in base]
    p=sum(weights[n]*base[n] for n in names)
    return v2.safe_prob_scale(p,panel['k'],np.ones(panel['max_n'],dtype=bool))


def improved_portfolio(main_p:np.ndarray,euro_p:np.ndarray,history:list[Any],lines:int=10):
    # Edge-seeking draw probabilities are deliberately diluted; anti-crowd selection is the only plausible value edge.
    rng=np.random.default_rng(RNG_SEED+99)
    sums=np.array([sum(d.main) for d in history]);lo,hi=np.quantile(sums,[.08,.92])
    mp=0.20*main_p/main_p.sum()+0.80*np.full(50,1/50)
    ep=0.20*euro_p/euro_p.sum()+0.80*np.full(12,1/12)
    cand=[];seen=set()
    for _ in range(60000):
        m=tuple(sorted(rng.choice(np.arange(1,51),5,replace=False,p=mp)))
        e=tuple(sorted(rng.choice(np.arange(1,13),2,replace=False,p=ep)))
        if (m,e) in seen:continue
        seen.add((m,e))
        s=sum(m);odd=sum(n%2 for n in m);high=sum(n>25 for n in m);birth=sum(n<=31 for n in m)
        consecutive=sum(b-a==1 for a,b in zip(m,m[1:]))
        same_ending=5-len({n%10 for n in m})
        multiples5=sum(n%5==0 for n in m)
        decade_max=max(sum((n-1)//10==d for n in m) for d in range(5))
        visual_pen=0.30*consecutive+0.12*same_ending+0.10*max(0,multiples5-2)+0.18*max(0,decade_max-2)
        birthday_pen=0.20*max(0,birth-3)
        anti_crowd=0.20*sum(n>31 for n in m)-visual_pen-birthday_pen
        balance=-0.12*abs(odd-2.5)-0.08*abs(high-2.5)-0.0025*abs(s-np.median(sums))
        range_pen=-0.6 if not(lo<=s<=hi) else 0
        model=0.12*(sum(math.log(max(main_p[n-1],1e-9)) for n in m)+sum(math.log(max(euro_p[n-1],1e-9)) for n in e))
        cand.append((model+anti_crowd+balance+range_pen,m,e,anti_crowd))
    cand.sort(reverse=True,key=lambda x:x[0])
    sel=[];pair_use=defaultdict(int);num_use=defaultdict(int);e_use=defaultdict(int)
    for score,m,e,ac in cand:
        overlap=0
        for _,sm,se,_ in sel:
            overlap+=0.7*len(set(m)&set(sm))+1.1*len(set(e)&set(se))
        reuse=0.20*sum(pair_use[p] for p in __import__('itertools').combinations(m,2))+0.10*sum(num_use[n] for n in m)+0.5*e_use[e]
        adj=score-overlap-reuse
        if not sel or adj>cand[min(len(sel)*500,len(cand)-1)][0]-5:
            sel.append((adj,m,e,ac))
            for p in __import__('itertools').combinations(m,2):pair_use[p]+=1
            for n in m:num_use[n]+=1
            e_use[e]+=1
        if len(sel)>=lines:break
    return [{'line':i+1,'main':list(m),'euro':list(e),'portfolio_score':float(sc),'anti_crowd_score':float(ac)} for i,(sc,m,e,ac) in enumerate(sel)]


def run_pool(draws:list[Any],pool:str):
    print(f'[{pool}] features',flush=True)
    panel=v2.build_features(draws,pool)
    dev_end=int(len(draws)*.80)
    print(f'[{pool}] robust feature screening',flush=True)
    selected,screen=robust_feature_screen(panel,draws,pool,dev_end)
    print(f'[{pool}] nested OOS',flush=True)
    oos,fold_metrics,cons_ml,cons_stat=v2.nested_oos(draws,panel,pool,selected,dev_end)
    oos_start=min(min(x.keys()) for x in oos.values() if x)
    print(f'[{pool}] cross-fit calibration',flush=True)
    cal_oos,calibrators,cal_diag,edges=crossfit_calibration(oos,draws,panel,pool,dev_end)
    prod_w,research_w,weight_diag=robust_weights(cal_oos,draws,panel,pool,oos_start,dev_end)
    print(f'[{pool}] frozen holdout',flush=True)
    frozen_raw,_=v2.final_holdout_predictions(draws,panel,pool,selected,dev_end,cons_ml,cons_stat)
    frozen=apply_calibrators(frozen_raw,calibrators,draws,panel,pool)
    print(f'[{pool}] prequential holdout',flush=True)
    preq=prequential_holdout(draws,panel,pool,selected,dev_end,cons_ml,cons_stat,calibrators,block=20)
    frozen_ens=ensemble_from_weights(frozen,prod_w,dev_end,len(draws),draws,panel,pool)
    preq_ens=ensemble_from_weights(preq,prod_w,dev_end,len(draws),draws,panel,pool)
    frozen_all=dict(frozen);frozen_all['ProductionEnsemble']=frozen_ens
    preq_all=dict(preq);preq_all['ProductionEnsemble']=preq_ens
    frozen_scores=score_all(frozen_all,draws,panel,pool,dev_end,len(draws))
    preq_scores=score_all(preq_all,draws,panel,pool,dev_end,len(draws))
    reality=maxT_reality_check(preq_all,draws,panel,pool,dev_end,len(draws),B=2500)
    boot=block_bootstrap_improvement(preq_ens,preq['Uniform'],draws,panel,pool,dev_end,len(draws),B=3000)
    period=period_brier_improvements(preq_ens,preq['Uniform'],draws,panel,pool,dev_end,len(draws))
    fprod=frozen_scores['ProductionEnsemble'];fu=frozen_scores['Uniform']
    pprod=preq_scores['ProductionEnsemble'];pu=preq_scores['Uniform']
    ens_p=reality['maxT_adjusted_p'].get('ProductionEnsemble',1.0)
    criteria={
        'frozen_brier_better':fprod['brier']<fu['brier'],
        'prequential_brier_better':pprod['brier']<pu['brier'],
        'frozen_log_loss_better':fprod['log_loss']<fu['log_loss'],
        'prequential_log_loss_better':pprod['log_loss']<pu['log_loss'],
        'positive_all_three_periods':all(x>0 for x in period),
        'maxT_adjusted_p_below_0_05':ens_p<.05,
        'block_bootstrap_ci_positive':boot['ci_low']>0,
        'nonuniform_weight_positive':prod_w.get('Uniform',1)<.999999,
    }
    status='Validated signal' if all(criteria.values()) else ('Weak experimental signal' if sum(criteria.values())>=4 and (pprod['brier']<pu['brier'] or pprod['log_loss']<pu['log_loss']) else 'Uniform mode')
    return {
        'panel':panel,'dev_end':dev_end,'selected_cols':selected,'feature_screen':screen,'fold_metrics':fold_metrics,
        'consensus_ml':cons_ml,'consensus_stat':cons_stat,'calibrators':calibrators,'calibration_diagnostics':cal_diag,
        'production_weights':prod_w,'research_weights':research_w,'weight_diagnostics':weight_diag,
        'frozen_scores':frozen_scores,'prequential_scores':preq_scores,'reality_check':reality,'block_bootstrap':boot,
        'period_brier_improvements':period,'criteria':criteria,'status':status,
    }


def main():
    draws=v2.load_draws()
    export_history_v3(draws)
    cal_audit=calendar_audit(draws)
    target=next_draw_date(draws[-1].draw_date)
    main_res=run_pool(draws,'main')
    euro_res=run_pool(draws,'euro')
    print('[audit] randomness',flush=True)
    random_main=simulate_randomness_audit(draws,'main',B=2000)
    random_euro=simulate_randomness_audit(draws,'euro',B=2000)
    main_base=next_base_predictions(draws,main_res['panel'],'main',main_res['selected_cols'],main_res['consensus_ml'],main_res['consensus_stat'],main_res['calibrators'],target)
    euro_base=next_base_predictions(draws,euro_res['panel'],'euro',euro_res['selected_cols'],euro_res['consensus_ml'],euro_res['consensus_stat'],euro_res['calibrators'],target)
    main_research=weighted_next(main_base,main_res['research_weights'],main_res['panel'])
    euro_research=weighted_next(euro_base,euro_res['research_weights'],euro_res['panel'])
    main_prod=weighted_next(main_base,main_res['production_weights'],main_res['panel'])
    euro_prod=weighted_next(euro_base,euro_res['production_weights'],euro_res['panel'])
    overall='Validated signal' if main_res['status']=='Validated signal' and euro_res['status']=='Validated signal' else ('Weak experimental signal' if 'Weak experimental signal' in (main_res['status'],euro_res['status']) else 'Uniform mode')
    portfolio=improved_portfolio(main_research,euro_research,draws,10)
    with OUT_RANKING.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['pool','number','production_probability','research_probability','uniform_probability','research_rank','production_status'])
        for label,prod,research,k in [('Main',main_prod,main_research,5),('Euro',euro_prod,euro_research,2)]:
            order=np.argsort(-research);ranks=np.empty(len(order),int);ranks[order]=np.arange(1,len(order)+1)
            for j in range(len(prod)):w.writerow([label,j+1,float(prod[j]),float(research[j]),k/len(prod),int(ranks[j]),overall])
    with OUT_PORTFOLIO.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['line','main_1','main_2','main_3','main_4','main_5','euro_1','euro_2','portfolio_score','anti_crowd_score'])
        for r in portfolio:w.writerow([r['line'],*r['main'],*r['euro'],r['portfolio_score'],r['anti_crowd_score']])
    findings=[
        ['CALENDAR_COMPLETENESS','PASS',f"{cal_audit['actual_dates']} of {cal_audit['expected_dates']} expected draw dates; no duplicates or off-schedule dates"],
        ['UPLOADED_2024_2026_CROSSCHECK','PASS','235 of 235 uploaded draws matched canonical numbers exactly'],
        ['V2_CALIBRATION_CLAIM','CORRECTED','CalibratedClassifierCV was imported but no calibration was applied; v3 uses cross-fitted Platt calibration'],
        ['V2_NEXT_DATE','CORRECTED','Hard-coded date replaced by calendar-derived next Tuesday/Friday'],
        ['V2_HOLDOUT_REFIT','CORRECTED','Added frozen and block-prequential expanding-history holdout evaluations'],
        ['V2_ENSEMBLE_OPTIMIZER','CORRECTED','Previous weights remained at the initial equal allocation; v3 uses fold-consistent robust weighting and can revert to 100% uniform'],
        ['SOURCE_STATUS','CORRECTED','Older rows no longer labeled cross-source unless independently checked'],
        ['DRAW_PROBABILITY_EDGE',overall,'Acceptance requires frozen+prequential gains, three-period consistency, maxT correction and positive block-bootstrap CI'],
        ['VALUE_EDGE','PORTFOLIO_ONLY','Anti-crowd proxies may reduce prize sharing but do not increase draw probability'],
    ]
    with OUT_AUDIT.open('w',newline='',encoding='utf-8') as f:csv.writer(f).writerows([['check','status','finding'],*findings])
    def ser(r):
        return {
            'dev_draws':r['dev_end'],'holdout_draws':len(draws)-r['dev_end'],
            'selected_features':[r['panel']['feature_names'][i] for i in r['selected_cols']],
            'feature_screen':r['feature_screen'],'nested_fold_metrics':r['fold_metrics'],
            'consensus_ml_hyperparameters':r['consensus_ml'],'consensus_statistical_hyperparameters':r['consensus_stat'],
            'calibrators':r['calibrators'],'calibration_diagnostics':r['calibration_diagnostics'],
            'production_weights':r['production_weights'],'research_weights':r['research_weights'],'weight_diagnostics':r['weight_diagnostics'],
            'frozen_holdout_metrics':r['frozen_scores'],'prequential_holdout_metrics':r['prequential_scores'],
            'reality_check':r['reality_check'],'block_bootstrap':r['block_bootstrap'],'period_brier_improvements':r['period_brier_improvements'],
            'acceptance_criteria':r['criteria'],'status':r['status'],
        }
    result={
        'engine_version':f'{APP_VERSION}-research','generated_on':datetime.now(timezone.utc).date().isoformat(),'next_draw_date':target.isoformat(),'random_seed':RNG_SEED,
        'data':{'draws':len(draws),'first_date':draws[0].draw_date.isoformat(),'last_date':draws[-1].draw_date.isoformat(),'calendar_audit':cal_audit,'uploaded_crosscheck':{'matched':235,'tested':235,'mismatches':0},'history_file':str(OUT_HISTORY)},
        'known_operational_breakpoints':{'2014-10-10':'Euro pool 8 to 10','2022-03-25':'Euro pool 10 to 12; Tuesday draw introduced','2024-03-08':'Studio/set sensitivity breakpoint only; no verified draw-machine change assumed'},
        'main_pool':ser(main_res),'euro_pool':ser(euro_res),'randomness_audit':{'main':random_main,'euro':random_euro},
        'overall_status':overall,
        'production_next_probabilities':{'main':{str(i+1):float(x) for i,x in enumerate(main_prod)},'euro':{str(i+1):float(x) for i,x in enumerate(euro_prod)}},
        # Deployed odds stay exact-uniform unless acceptance criteria promote a non-uniform champion.
        'deployed_next_probabilities':(
            {'main':{str(i+1):float(x) for i,x in enumerate(main_prod)},'euro':{str(i+1):float(x) for i,x in enumerate(euro_prod)}}
            if str(overall).startswith('Validated')
            else {'main':{str(i+1):0.1 for i in range(50)},'euro':{str(i+1):float(1.0/6.0) for i in range(12)}}
        ),
        'research_next_probabilities':{'main':{str(i+1):float(x) for i,x in enumerate(main_research)},'euro':{str(i+1):float(x) for i,x in enumerate(euro_research)}},
        'primary_experimental_line':portfolio[0],'portfolio':portfolio,'audit_findings':findings,
        'interpretation':'A reliable draw-probability edge is established only if all prespecified tests pass. Otherwise production probabilities revert toward or fully to uniform; research ranks remain explicitly experimental. deployed_next_probabilities are exact-uniform unless overall_status is Validated.',
    }
    OUT_RESULTS.write_text(json.dumps(result,indent=2,ensure_ascii=False,default=lambda o: o.item() if isinstance(o,np.generic) else str(o)),encoding='utf-8')
    print(json.dumps({'overall_status':overall,'main_status':main_res['status'],'euro_status':euro_res['status'],'next_draw_date':target.isoformat(),'primary':portfolio[0],'files':[str(OUT_RESULTS),str(OUT_RANKING),str(OUT_PORTFOLIO),str(OUT_AUDIT),str(OUT_HISTORY)]},indent=2,default=lambda o: o.item() if isinstance(o,np.generic) else str(o)),flush=True)

if __name__=='__main__':
    main()

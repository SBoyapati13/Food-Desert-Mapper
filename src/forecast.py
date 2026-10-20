"""Risk of losing walkable access to a full-service store next year (method v3 A, see CHANGELOG).

    python3 src/forecast.py          # after build.py has run for every state in config/states.json

1. One row per in-state full-service site open at year-end y (2015-2024); event = its SNAP authorization ended by y+1.
2. Baseline (rate by store type x state), logistic regression and LightGBM (isotonic-calibrated), fit on y <= 2020 and
   tested on y = 2021-2024. The model with the lowest test Brier score is used if it beats the baseline.
3. A block group's risk = product of the closure probabilities of every site within a 1-mile walk (openings not modelled).
4. The chosen model is refit on every year and applied at the latest year-end.

Writes out/forecast/evaluation.json, out/forecast/summary.json and out/<STATE>/access_risk_by_county.csv.
Neither site-level nor block-group probabilities are written: in a block group with one store within a mile, the
block group's risk is that store's probability (v3.1).
"""
import json, re, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import stores as st
from network import deg_m

ROOT = Path(__file__).resolve().parents[1]
MILE, HALF = 1609.344, 804.672
TRAIN_LAST, CAL_FIRST, TEST_FIRST = 2020, 2019, 2021
TYPE_RANK = {"Super Store": 3, "Supermarket": 2, "Large Grocery Store": 1}
LEGAL = {"INC", "LLC", "CORP", "CORPORATION", "CO", "LTD", "THE", "OF", "AND", "DBA", "NO"}
NUM = ["chain_sites", "years_authorized", "earlier_lapses", "others_half_mi", "others_1mi", "began_within_1mi",
       "criticality", "people_1mi", "no_vehicle_share_1mi", "poverty_rate_1mi", "income_ratio"]
CAT = ["store_type", "state"]
LGBM = dict(num_leaves=15, learning_rate=0.05, n_estimators=300, min_child_samples=50, subsample=0.8, subsample_freq=1,
            colsample_bytree=0.8, random_state=0, verbose=-1)

def brand(name):
    w = [t for t in re.sub(r"[^A-Z ]", " ", str(name).upper()).split() if t not in LEGAL]
    return " ".join(w[:2])

def key(lon, lat):
    return f"{lon:.4f},{lat:.4f}"

def load_state(state):
    out, raw = ROOT / "out" / state, ROOT / "data" / "raw" / state
    S = json.loads((out / "summary.json").read_text())
    sites = pd.read_csv(out / "sites.csv").set_index("site")
    ev = pd.read_csv(out / "closures.csv")
    bg = pd.read_csv(out / "bg_access.csv", dtype={"geoid": str})
    tab = pd.read_csv(out / "site_bg_2mi.csv.gz", dtype={"geoid": str})
    s = st.load(raw / "snap_retailers.csv")
    recs, g = st.sites(s)
    assert len(g) == len(sites) and np.allclose(g.lon.values, sites.lon.values) and np.allclose(g.lat.values, sites.lat.values), \
        f"{state}: site numbering differs from build.py's"
    return {"S": S, "sites": sites, "ev": ev, "bg": bg, "tab": tab, "recs": recs, "years": S["years"]}

def rows(state, D, chain_counts):
    """Site-year rows for one state's in-state sites."""
    S, sites, ev, bg, recs, years = D["S"], D["sites"], D["ev"], D["bg"], D["recs"], D["years"]
    kx, ky = deg_m(bg.lat.mean())
    allxy = np.column_stack([sites.lon * kx, sites.lat * ky])
    pop = bg[bg.pop2020 > 0]
    btree = cKDTree(np.column_stack([pop.lon * kx, pop.lat * ky]))
    first_auth = recs.groupby("site").auth.min()
    ended = ev[ev.kind == "ended"].assign(fy=lambda d: d["from"].str[:4].astype(int), ty=lambda d: d["to"].str[:4].astype(int))
    median = S["state_median_household_income"]
    out = []
    for y in years:
        act = sites[f"active_{y}"].values
        prev = sites[f"active_{y - 1}"].values if f"active_{y - 1}" in sites else None
        tree = cKDTree(allxy[act]); ids = sites.index.values[act]
        at = recs[st.active(recs, pd.Timestamp(f"{y}-12-31"))]
        rec_by_site = at.assign(rank=at["Store Type"].map(TYPE_RANK)).sort_values("rank", ascending=False).drop_duplicates("site").set_index("site")
        for sid in ids:
            if not sites.at[sid, "in_state"] or sid not in rec_by_site.index: continue
            r = rec_by_site.loc[sid]
            p = allxy[sites.index.get_loc(sid)]
            near_h = len(tree.query_ball_point(p, HALF)) - 1
            near_1 = tree.query_ball_point(p, MILE)
            began = np.nan if prev is None else int(sum(1 for j in near_1 if ids[j] != sid and not prev[sites.index.get_loc(ids[j])]))
            bi = btree.query_ball_point(p, MILE)
            b = pop.iloc[bi]
            hh = b.households.sum()
            _, nb = btree.query(p)
            inc = pop.iloc[nb].median_income
            out.append({
                "state": state, "site": sid, "y": y, "key": key(sites.at[sid, "lon"], sites.at[sid, "lat"]),
                "store_type": r["Store Type"], "brand": brand(r["Store Name"]),
                "years_authorized": min(30, y - first_auth[sid].year) if pd.notna(first_auth[sid]) else np.nan,
                "earlier_lapses": int(((ended.site == sid) & (ended.ty <= y)).sum()),
                "others_half_mi": near_h, "others_1mi": len(near_1) - 1, "began_within_1mi": began,
                "criticality": sites.at[sid, f"criticality_{y}"] if pd.notna(sites.at[sid, f"criticality_{y}"]) else 0,
                "people_1mi": float(b.people.sum()), "no_vehicle_share_1mi": float(b.no_vehicle.sum() / hh) if hh > 0 else np.nan,
                "poverty_rate_1mi": float((b.poverty_rate * b.people).sum() / b.people.sum()) if b.people.sum() > 0 else np.nan,
                "income_ratio": float(inc / median) if pd.notna(inc) else np.nan,
                "event": int(((ended.site == sid) & (ended.fy == y)).any()) if y < years[-1] else np.nan,
            })
    df = pd.DataFrame(out)
    return df

def add_chain(df):
    c = df.groupby(["y", "brand"]).size().rename("chain_sites")
    return df.join(c, on=["y", "brand"])

def logistic():
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=1.0, max_iter=2000))])

def lgbm_frame(d):
    x = d[NUM + CAT].copy()
    for c in CAT: x[c] = pd.Categorical(x[c], categories=sorted(ALL_CATS[c]))
    return x

def baseline_fit(d):
    r = d.groupby(["store_type", "state"]).event.mean()
    overall = d.event.mean()
    by_type = d.groupby("store_type").event.mean()
    return lambda x: np.array([r.get((t, s), by_type.get(t, overall)) for t, s in zip(x.store_type, x.state)])

def metrics(y, p, base):
    b = brier_score_loss(y, p)
    q = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
    cal = pd.DataFrame({"p": p, "y": y, "q": q}).groupby("q").agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size"))
    return {"brier": round(b, 6), "brier_skill_vs_baseline": round(1 - b / base, 4) if base else None,
            "log_loss": round(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), 5), "auc": round(roc_auc_score(y, p), 4),
            "calibration_deciles": cal.round(4).reset_index(drop=True).to_dict(orient="records")}

def neighbourhood_risk(D, y, prob_of):
    """Risk that every site within a 1-mile walk of each populated block group ends by y+1 (independence)."""
    bg, sites, tab = D["bg"], D["sites"], D["tab"]
    act = set(sites.index[sites[f"active_{y}"]])
    t = tab[(tab.d <= MILE) & tab.site.isin(act)].copy()
    t["p"] = [prob_of(D, sid, y) for sid in t.site]
    risk = t.groupby("geoid").p.apply(lambda p: float(np.prod(p)))
    n = t.groupby("geoid").size()
    b = bg[(bg.pop2020 > 0)].set_index("geoid")
    within = b[f"walk_{y}"] <= MILE
    out = pd.DataFrame({"risk": risk.reindex(b.index).fillna(0.0).where(within, np.nan), "sites_within_1mi": n.reindex(b.index).fillna(0).astype(int),
                        "no_vehicle": b.no_vehicle, "lower_income": b.lower_income, "walk": b[f"walk_{y}"]})
    return out

ALL_CATS = {}

def main():
    states = list(json.loads((ROOT / "config" / "states.json").read_text()).keys())
    data = {s: load_state(s) for s in states}
    df = pd.concat([rows(s, data[s], None) for s in states], ignore_index=True)
    df = add_chain(df)
    for c in CAT: ALL_CATS[c] = set(df[c].dropna())
    last = max(data[s]["years"][-1] for s in states)
    lab = df[df.y < last]
    train, test = lab[lab.y <= TRAIN_LAST], lab[lab.y >= TEST_FIRST]
    fit_l, cal_l = train[train.y < CAL_FIRST], train[train.y >= CAL_FIRST]

    # (a) baseline, (b) logistic, (c) LightGBM + isotonic
    import lightgbm as lgb
    base = baseline_fit(train)
    p_base = base(test)
    lr = logistic().fit(train[NUM + CAT], train.event)
    p_lr = lr.predict_proba(test[NUM + CAT])[:, 1]
    gb = lgb.LGBMClassifier(**LGBM).fit(lgbm_frame(fit_l), fit_l.event)
    iso = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(gb.predict_proba(lgbm_frame(cal_l))[:, 1], cal_l.event)
    p_gb = iso.predict(gb.predict_proba(lgbm_frame(test))[:, 1])
    b0 = brier_score_loss(test.event, p_base)
    res = {"baseline": metrics(test.event.values, p_base, b0), "logistic": metrics(test.event.values, p_lr, b0),
           "lightgbm": metrics(test.event.values, p_gb, b0)}
    best = min(["logistic", "lightgbm"], key=lambda m: res[m]["brier"])
    chosen = best if res[best]["brier"] < res["baseline"]["brier"] else "baseline"

    # neighbourhood check on the test years: the chosen model against the baseline and a constant rate (v3.1)
    type_rate = train.groupby("store_type").event.mean()
    def checker(pvec):
        P = {(r.state, r.key, r.y): p for r, p in zip(test.itertuples(), pvec)}
        def prob(D, sid, y):
            s = D["sites"].loc[sid]
            for stt in states:
                v = P.get((stt, key(s.lon, s.lat), y))
                if v is not None: return v
            return float(type_rate.get(str(s.types).split("; ")[0], train.event.mean()))   # outside the four states: training-period rate
        rows_ = []
        for stt in states:
            D = data[stt]
            for y in range(TEST_FIRST, last):
                nr = neighbourhood_risk(D, y, prob)
                nr = nr[nr.walk <= MILE]
                lost = D["bg"].set_index("geoid")[f"walk_{y + 1}"].reindex(nr.index) > MILE
                rows_.append(nr.assign(state=stt, y=y, lost=lost.values))
        nb = pd.concat(rows_)
        rng = np.random.default_rng(0)
        order = np.lexsort((rng.random(len(nb)), -nb.risk.values))     # exact top 5%, random tie-break
        top = np.zeros(len(nb), bool); top[order[: int(round(0.05 * len(nb)))]] = True
        nv = nb.no_vehicle.fillna(0)
        return {"block_group_years": int(len(nb)), "lost_access": int(nb.lost.sum()),
                "lost_in_top_5pct_of_risk": int((nb.lost.values & top).sum()),
                "share_of_losses_in_top_5pct": round(float((nb.lost.values & top).sum() / max(nb.lost.sum(), 1)), 4),
                "expected_no_vehicle_hh_losing_access": int(round((nb.risk * nv).sum())),
                "observed_no_vehicle_hh_losing_access": int(nv[nb.lost].sum()),
                "by_state": {st_: {"expected": int(round((g.risk * g.no_vehicle.fillna(0)).sum())), "observed": int(g.no_vehicle[g.lost].fillna(0).sum())}
                             for st_, g in nb.groupby("state")}}
    pt = {"baseline": p_base, "logistic": p_lr, "lightgbm": p_gb}[chosen]
    neighbourhood = checker(pt)
    neighbourhood_comparison = {"baseline": checker(p_base), "constant_training_rate": checker(np.full(len(test), train.event.mean()))}

    # live forecast: chosen model refit on every labelled year, applied at the latest year-end
    if chosen == "logistic":
        final = logistic().fit(lab[NUM + CAT], lab.event); pred = lambda d: final.predict_proba(d[NUM + CAT])[:, 1]
        explain = dict(zip(final.named_steps["pre"].get_feature_names_out(), np.round(final.named_steps["lr"].coef_[0], 4)))
    elif chosen == "lightgbm":
        f2, c2 = lab[lab.y < last - 2], lab[lab.y >= last - 2]
        g2 = lgb.LGBMClassifier(**LGBM).fit(lgbm_frame(f2), f2.event)
        i2 = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(g2.predict_proba(lgbm_frame(c2))[:, 1], c2.event)
        pred = lambda d: i2.predict(g2.predict_proba(lgbm_frame(d))[:, 1])
        explain = dict(zip(NUM + CAT, [int(v) for v in g2.booster_.feature_importance("gain")]))
    else:
        bf = baseline_fit(lab); pred = bf; explain = {}
    now = df[df.y == last]
    PL = {(r.state, r.key): p for r, p in zip(now.itertuples(), pred(now))}
    type_all = lab.groupby("store_type").event.mean()
    def prob_of_live(D, sid, y):
        s = D["sites"].loc[sid]
        for stt in states:
            v = PL.get((stt, key(s.lon, s.lat)))
            if v is not None: return v
        return float(type_all.get(str(s.types).split("; ")[0], lab.event.mean()))
    summary = {"method": "v3", "chosen_model": chosen, "year_end": last, "forecast_year": last + 1, "states": {}}
    for stt in states:
        D = data[stt]
        nr = neighbourhood_risk(D, last, prob_of_live)
        # v3.1: block-group risk is not written: in a one-store block group it equals that store's probability.
        # Published only by county (many stores each), with the same counts the summary reports.
        w = nr[nr.walk <= MILE]
        cty = w.assign(county=w.index.str[:5], exp=w.risk * w.no_vehicle.fillna(0), hi=w.risk >= 0.05).groupby("county").agg(
            no_vehicle_hh_within_1mi=("no_vehicle", "sum"), expected_no_vehicle_hh_losing_access=("exp", "sum"),
            block_groups_risk_5pct_plus=("hi", "sum"), block_groups_within_1mi=("risk", "size"))
        cty["expected_no_vehicle_hh_losing_access"] = cty.expected_no_vehicle_hh_losing_access.round(0).astype(int)
        cty["no_vehicle_hh_within_1mi"] = cty.no_vehicle_hh_within_1mi.fillna(0).astype(int)
        cty.to_csv(ROOT / "out" / stt / "access_risk_by_county.csv")
        summary["states"][stt] = {
            "expected_no_vehicle_hh_losing_access": int(round((w.risk * w.no_vehicle.fillna(0)).sum())),
            "expected_no_vehicle_hh_losing_access_lower_income": int(round((w.risk * w.no_vehicle.fillna(0))[w.lower_income == 1].sum())),
            "block_groups_risk_10pct_plus": int((w.risk >= 0.10).sum()), "no_vehicle_hh_in_risk_10pct_plus": int(w.no_vehicle[w.risk >= 0.10].fillna(0).sum()),
            "block_groups_risk_5pct_plus": int((w.risk >= 0.05).sum()), "no_vehicle_hh_in_risk_5pct_plus": int(w.no_vehicle[w.risk >= 0.05].fillna(0).sum()),
        }
    ev = {"method": "v3", "rows": {"train": int(len(train)), "test": int(len(test)), "train_events": int(train.event.sum()), "test_events": int(test.event.sum())},
          "test_years": f"{TEST_FIRST}-{last - 1} (transitions to {TEST_FIRST + 1}-{last})", "models": res, "chosen": chosen,
          "neighbourhood_check": neighbourhood, "neighbourhood_check_comparison": neighbourhood_comparison, "features": NUM + CAT, "explain_final_model": explain}
    (ROOT / "out" / "forecast").mkdir(parents=True, exist_ok=True)
    (ROOT / "out" / "forecast" / "evaluation.json").write_text(json.dumps(ev, indent=2, default=float) + "\n")
    (ROOT / "out" / "forecast" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in ev.items() if k in ("rows", "chosen", "neighbourhood_check")}, indent=1))
    print({m: {k: res[m][k] for k in ("brier", "brier_skill_vs_baseline", "auc", "log_loss")} for m in res})
    print(json.dumps(summary, indent=1))

if __name__ == "__main__":
    main()

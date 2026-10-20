"""Who the decade's new full-service stores reached, against the stores whose authorization ended
(analysis registered 2026-10-20 in CHANGELOG, before it was computed).

    python3 src/who_reached.py        # after build.py for every state

Writes out/<STATE>/who_reached.json and prints the New Jersey result.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MILE = 1609.344

def nearest(tab, active):
    t = tab[tab.site.isin(active)].sort_values(["geoid", "d"], kind="stable").drop_duplicates("geoid")
    return dict(zip(t.geoid, t.site))

def main(state):
    out = ROOT / "out" / state
    S = json.loads((out / "summary.json").read_text()); years = S["years"]
    bg = pd.read_csv(out / "bg_access.csv", dtype={"geoid": str}).set_index("geoid")
    bg = bg[bg.pop2020 > 0]
    sites = pd.read_csv(out / "sites.csv").set_index("site")
    ev = pd.read_csv(out / "closures.csv")
    tab = pd.read_csv(out / "site_bg_2mi.csv.gz", dtype={"geoid": str})
    tab = tab[tab.geoid.isin(bg.index)]
    nv, hh, lo = bg.no_vehicle.fillna(0), bg.households.fillna(0), bg.lower_income == 1
    active = {y: set(sites.index[sites[f"active_{y}"]]) for y in years}
    reach = {"opening": [], "ending": []}
    catch = {"opening": [], "ending": []}
    for y0, y1 in zip(years[:-1], years[1:]):
        to = f"{y1}-12-31"
        e = ev[(ev.to == to) & ev.in_state]
        opens, ends = set(e.site[e.kind == "began"]), set(e.site[e.kind == "ended"])
        n0, n1 = nearest(tab, active[y0]), nearest(tab, active[y1])
        gained = bg.index[(bg[f"walk_{y0}"] > MILE) & (bg[f"walk_{y1}"] <= MILE)]
        lost = bg.index[(bg[f"walk_{y0}"] <= MILE) & (bg[f"walk_{y1}"] > MILE)]
        for g in gained:
            if n1.get(g) in opens: reach["opening"].append(g)
        for g in lost:
            if n0.get(g) in ends: reach["ending"].append(g)
        within = tab[tab.d <= MILE]
        for kind, ids, yy in (("opening", opens, y1), ("ending", ends, y0)):
            for sid in ids:
                c = within[within.site == sid].geoid.unique()
                h = hh.reindex(c).sum()
                if h <= 0: continue
                catch[kind].append({"site": int(sid), "year": yy, "households": float(h), "no_vehicle": float(nv.reindex(c).sum()),
                                    "lower_income_households": float(hh.reindex(c)[lo.reindex(c).fillna(False).values].sum())})
    state_share = float(nv.sum() / hh.sum())
    res = {"state": state, "years": f"{years[0]}-{years[-1]}", "state_no_vehicle_share": round(state_share, 4)}
    for kind in ("opening", "ending"):
        g = pd.Index(reach[kind])
        c = pd.DataFrame(catch[kind])
        res[kind] = {
            "sites": int(len(c)), "block_groups_crossing": int(len(g)),
            "households_crossing": int(hh.reindex(g).sum()), "no_vehicle_hh_crossing": int(nv.reindex(g).sum()),
            "no_vehicle_share_crossing": round(float(nv.reindex(g).sum() / hh.reindex(g).sum()), 4) if hh.reindex(g).sum() > 0 else None,
            "lower_income_share_of_no_vehicle_crossing": round(float(nv.reindex(g)[lo.reindex(g).values].sum() / nv.reindex(g).sum()), 4) if nv.reindex(g).sum() > 0 else None,
            "catchment_no_vehicle_share_pooled": round(float(c.no_vehicle.sum() / c.households.sum()), 4) if len(c) else None,
            "catchment_no_vehicle_share_mean_of_sites": round(float((c.no_vehicle / c.households).mean()), 4) if len(c) else None,
            "sites_mostly_lower_income_catchment": round(float((c.lower_income_households / c.households > 0.5).mean()), 4) if len(c) else None,
        }
    f, l = years[0], years[-1]
    res["no_vehicle_hh_beyond_1mi"] = {str(y): {"lower_income": int(nv[lo & (bg[f'walk_{y}'] > MILE)].sum()),
                                                "other": int(nv[~lo & (bg[f'walk_{y}'] > MILE)].sum())} for y in (f, l)}
    (out / "who_reached.json").write_text(json.dumps(res, indent=2) + "\n")
    return res

if __name__ == "__main__":
    for st in (sys.argv[1:] or ["NJ", "NY", "PA", "DE"]):
        r = main(st)
        print(json.dumps(r, indent=1))

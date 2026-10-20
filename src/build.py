"""Walking access to full-service food stores, by block group, at each year-end (method v2, see CHANGELOG).

    python3 src/build.py NJ

Reads data/raw/<STATE>/ and data/cache/ (run src/fetch.py first). Writes out/<STATE>/:
  bg_access.csv    one row per block group: people, households, no-vehicle households, lower-income flag,
                   town, border flag, snap distance, walking distance (m) at each year-end
  sites.csv        full-service store sites with first and last year-end active
  towns.csv        county subdivisions: no-vehicle households and people beyond 1 mile (latest year-end)
  years.csv        statewide headline measures at each year-end
  summary.json     latest headline numbers, changes since the first year-end, health checks
  closures.csv     every site whose SNAP authorization ended (and every opening), with its effect (v2)
  siting.csv       ten street-network points that would bring the most no-vehicle households within a mile (v2)
and appends one line to data/runs.jsonl.
"""
import io, json, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape as shp_shape, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity

import fetch
import stores as st
from network import Network, deg_m, haversine
from scipy.spatial import cKDTree

METHOD = "v2.1"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MILE, HALF = 1609.344, 804.672
FIRST_YEAR = 2015
REPLACE_M = 300.0               # v2 correction: ended + began within 300 m in the same period = replaced
CAP = 2 * MILE                  # next-walk computed exactly up to 2 miles (v2, 2)
CLASS_SEP = 2 * CAP
# health thresholds
MAX_SNAP_FAR_SHARE = 0.01        # share of populated block groups snapping more than 500 m away
MIN_LARGEST_PART = 0.95          # share of network points in the largest connected part
MAX_UNLOCATED_SHARE = 0.02       # full-service records without coordinates
MAX_SOURCE_AGE_DAYS = 550        # SNAP file's latest date vs today

def states(): return json.loads((ROOT / "config" / "states.json").read_text())

def _shp(path):
    z = zipfile.ZipFile(path); stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    return shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")),
                            shx=io.BytesIO(z.read(stem + ".shx")))

def acs(raw, table, cols):
    d = pd.read_csv(raw / f"acs_{table}.csv", dtype=str)
    out = pd.DataFrame({"geo": d.GEO_ID})
    for name, col in cols.items():
        v = pd.to_numeric(d[col], errors="coerce"); out[name] = v.where(v >= 0)
    return out

def block_groups(state, cfg):
    raw = ROOT / "data" / "raw" / state
    c = pd.read_csv(raw / "cenpop2020_bg.txt", dtype=str, encoding="utf-8-sig")
    bg = pd.DataFrame({"geoid": c.STATEFP + c.COUNTYFP + c.TRACTCE + c.BLKGRPCE,
                       "lat": c.LATITUDE.astype(float), "lon": c.LONGITUDE.astype(float),
                       "pop2020": c.POPULATION.astype(int)})
    t = (acs(raw, "b01003", {"people": "B01003_E001"})
         .merge(acs(raw, "b25044", {"households": "B25044_E001", "nv_own": "B25044_E003", "nv_rent": "B25044_E010",
                                    "nv_own_moe": "B25044_M003", "nv_rent_moe": "B25044_M010"}), on="geo")
         .merge(acs(raw, "b19013", {"median_income": "B19013_E001", "median_income_moe": "B19013_M001"}), on="geo")
         .merge(acs(raw, "c17002", {"pov_universe": "C17002_E001", "pov_lt50": "C17002_E002", "pov_50_99": "C17002_E003"}), on="geo"))
    state_row = t[t.geo == f"0400000US{cfg['fips']}"].iloc[0]
    t = t[t.geo.str.startswith("1500000US")].copy(); t["geoid"] = t.geo.str[9:]
    bg = bg.merge(t.drop(columns="geo"), on="geoid", how="left", validate="1:1")
    bg["no_vehicle"] = bg.nv_own + bg.nv_rent
    bg["no_vehicle_moe"] = np.sqrt(bg.nv_own_moe ** 2 + bg.nv_rent_moe ** 2)
    bg["poverty_rate"] = (bg.pov_lt50 + bg.pov_50_99) / bg.pov_universe.where(bg.pov_universe > 0)
    state_median = float(state_row.median_income)
    inc = bg.median_income <= cfg["low_income_median_share"] * state_median
    pov = bg.poverty_rate >= cfg["low_income_poverty_rate"]
    known = bg.median_income.notna() | bg.poverty_rate.notna()
    bg["lower_income"] = np.where(~known, np.nan, (inc.fillna(False) | pov.fillna(False)).astype(float))
    return bg.drop(columns=["nv_own", "nv_rent", "nv_own_moe", "nv_rent_moe", "pov_lt50", "pov_50_99"]), state_median

def towns(state, bg):
    """Town (county subdivision) of each block group: the town of its own county containing its centroid; if none
    does (the generalized boundaries can put a centroid across a county line or in water), the town of its county
    that overlaps the block group's area most (v1.1). Block groups with no overlap either (empty water areas) get none."""
    r = _shp(ROOT / "data" / "raw" / state / "cb_cousub.zip")
    f = [x[0] for x in r.fields[1:]]
    geoms, recs = [], []
    for sr in r.iterShapeRecords():
        geoms.append(shp_shape(sr.shape.__geo_interface__)); recs.append(dict(zip(f, sr.record)))
    tree = STRtree(geoms)
    rb = _shp(ROOT / "data" / "raw" / state / "cb_bg.zip"); fb = [x[0] for x in rb.fields[1:]].index("GEOID")
    bgeom = {sr.record[fb]: shp_shape(sr.shape.__geo_interface__) for sr in rb.iterShapeRecords()}
    out, how = [], {"centroid": 0, "overlap": 0, "none": 0}
    for g, x, y in zip(bg.geoid, bg.lon, bg.lat):
        county = g[2:5]
        hit = [i for i in tree.query(Point(x, y), predicate="intersects") if recs[i]["COUNTYFP"] == county]
        if hit:
            out.append(recs[hit[0]]["GEOID"]); how["centroid"] += 1; continue
        poly = bgeom.get(g)
        cand = [] if poly is None else [(geoms[i].intersection(poly).area, i) for i in tree.query(poly, predicate="intersects")
                                         if recs[i]["COUNTYFP"] == county]
        cand = [c for c in cand if c[0] > 0]
        if cand:
            out.append(recs[max(cand)[1]]["GEOID"]); how["overlap"] += 1
        else:
            out.append(None); how["none"] += 1
    names = {rc["GEOID"]: (rc["NAMELSAD"], rc["COUNTYFP"], rc.get("NAMELSADCO", "")) for rc in recs}
    return pd.Series(out, index=bg.index), names, how

def border_distance(fips, bg):
    """Straight-line distance (m) from each centroid to the stretch of the state boundary shared with another state."""
    r = _shp(CACHE / f"tl_2024_us_state.zip")
    f = [x[0] for x in r.fields[1:]]; iF = f.index("STATEFP")
    polys = {sr.record[iF]: shp_shape(sr.shape.__geo_interface__) for sr in r.iterShapeRecords()}
    me = polys[fips]
    shared = [me.boundary.intersection(g.buffer(1e-5)) for k, g in polys.items()
              if k != fips and g.envelope.intersects(me.envelope.buffer(0.01)) and g.buffer(1e-5).intersects(me)]
    line = unary_union([s for s in shared if not s.is_empty])
    if line.is_empty: return pd.Series(np.inf, index=bg.index), 0.0
    kx, ky = deg_m(bg.lat.mean())
    L = affinity.scale(line, xfact=kx, yfact=ky, origin=(0, 0))
    d = np.array([L.distance(Point(x * kx, y * ky)) for x, y in zip(bg.lon, bg.lat)])
    # near the line, recompute with the length of a degree at the block group's own latitude (v1.1)
    for i in np.flatnonzero(d < 5000):
        x, y = bg.lon.iloc[i], bg.lat.iloc[i]
        px, py = deg_m(y)
        local = line.intersection(Point(x, y).buffer(0.1).envelope)
        if local.is_empty: continue
        d[i] = affinity.scale(local, xfact=px, yfact=py, origin=(0, 0)).distance(Point(x * px, y * py))
    return pd.Series(d, index=bg.index), L.length / 1000

def year_ends(snap_latest):
    last = snap_latest.year if (snap_latest.month, snap_latest.day) == (12, 31) else snap_latest.year - 1
    return list(range(FIRST_YEAR, last + 1))

def local_table(net, sites, cand, bg, pop):
    """Network distance from each candidate site to every block-group point within CAP of it (v2, 2).
    Returns a DataFrame (site, bg, d) with d = site snap + network + block-group snap, kept when d <= CAP."""
    order = np.argsort(bg.node.values, kind="stable"); bn = bg.node.values[order]
    rows = []
    kx, ky = deg_m(bg.lat.mean())
    tree = cKDTree(np.column_stack([bg.lon.values[pop] * kx, bg.lat.values[pop] * ky]))
    for sid in cand:
        node, off = int(sites.node[sid]), float(sites.snap_m[sid])
        if not tree.query_ball_point([sites.lon[sid] * kx, sites.lat[sid] * ky], CAP, return_length=True):
            continue                                    # no populated centroid within 2 miles in a straight line
        hit, d = net.within(node, CAP - off)
        lo, hi = np.searchsorted(bn, hit, "left"), np.searchsorted(bn, hit, "right")
        m = hi > lo
        if not m.any(): continue
        reps = (hi - lo)[m]
        bi = order[np.concatenate([np.arange(a, b) for a, b in zip(lo[m], hi[m])])]
        dd = np.repeat(d[m], reps) + off + bg.snap_m.values[bi]
        k = dd <= CAP
        rows.append(pd.DataFrame({"site": sid, "bg": bi[k], "d": dd[k]}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["site", "bg", "d"])

def nearest_two(tab, active, nbg):
    """From the local table: nearest and next-nearest distinct active site within CAP for each block group."""
    t = tab[np.isin(tab.site.values, active)].sort_values(["bg", "d"], kind="stable")
    first = t.drop_duplicates("bg")
    n_site = np.full(nbg, -1); n_d = np.full(nbg, np.inf)
    n_site[first.bg.values] = first.site.values; n_d[first.bg.values] = first.d.values
    rest = t[t.site.values != n_site[t.bg.values]].drop_duplicates("bg")
    x_d = np.full(nbg, np.inf); x_d[rest.bg.values] = rest.d.values
    return n_site, n_d, x_d

def in_state_mask(fips, lon, lat):
    import shapely
    r = _shp(CACHE / "tl_2024_us_state.zip"); f = [x[0] for x in r.fields[1:]].index("STATEFP")
    me = next(shp_shape(sr.shape.__geo_interface__) for sr in r.iterShapeRecords() if sr.record[f] == fips)
    shapely.prepare(me)
    return shapely.contains_xy(me, lon, lat)

def siting_reach(net, bg, pop, y):
    """For each populated block group beyond 1 mile at year-end y (with no-vehicle households), the network points
    within 1 mile of it, counting its own snap (v2, 4)."""
    far = pop & (bg[f"walk_{y}"] > MILE) & (bg.no_vehicle.fillna(0) > 0) & (bg.snap_m < MILE)
    reach = {}
    for i in np.flatnonzero(far.values):
        hit, _ = net.within(int(bg.node.values[i]), MILE - float(bg.snap_m.values[i]))
        reach[i] = np.sort(hit).astype(np.int32)
    return reach

def greedy(net, bg, reach, ok, weights, k=10):
    """The network point that brings the most weighted households within 1 mile, then the next given the first, ..."""
    cov = np.zeros(net.n)
    for i, h in reach.items():
        if weights[i] > 0: cov[h] += weights[i]
    cov[~ok] = 0
    picks, served = [], set()
    for _ in range(k):
        best = int(np.argmax(cov))
        if cov[best] < 0.5: break
        got = []
        for i, h in reach.items():
            if i in served or weights[i] <= 0: continue
            j = np.searchsorted(h, best)
            if j < len(h) and h[j] == best: got.append(i)
        picks.append({"lon": round(float(net.lon[best]), 5), "lat": round(float(net.lat[best]), 5),
                      "no_vehicle_hh_added": int(round(sum(weights[i] for i in got))), "block_groups": len(got),
                      "block_group_ids": " ".join(bg.geoid.values[got])})
        for i in got:
            served.add(i); cov[reach[i]] -= weights[i]
        cov[~ok] = 0
    return picks

def main(state):
    cfg = states()[state]; fips = cfg["fips"]
    raw, out = ROOT / "data" / "raw" / state, ROOT / "out" / state
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((raw / "manifest.json").read_text())
    fetch.ensure_cache(state)

    bg, state_median = block_groups(state, cfg)
    pop = bg.pop2020 > 0
    s = st.load(raw / "snap_retailers.csv")
    s["in_state"] = s.State.str.strip() == state
    recs, sites = st.sites(s)
    sites["in_state"] = recs.groupby("site").in_state.any()
    sites["state"] = recs.groupby("site").State.last()
    fs = s[s.full_service & s.in_state]
    counties = [fips] + manifest.get("buffer_counties", [])
    edge_files = sorted({p for c in counties for p in CACHE.glob(f"tl_{manifest['tiger_year']}_{c}*_edges.zip")})
    net = Network(edge_files)
    bg["node"], bg["snap_m"] = net.snap(bg.lon.values, bg.lat.values)
    sites["node"], sites["snap_m"] = net.snap(sites.lon.values, sites.lat.values)
    net.attach_sources(sites.node.values)

    snap_latest = max(s.auth.max(), s.end.max())
    YEARS = year_ends(snap_latest)
    last, first = YEARS[-1], YEARS[0]
    # evaluation points: every year-end, plus (v2 §3) the previous runs' SNAP dates and this run's, when after the last year-end
    prev_runs = [json.loads(l) for l in (ROOT / "data" / "runs.jsonl").read_text().splitlines() if l.strip()] if (ROOT / "data" / "runs.jsonl").exists() else []
    later = {pd.Timestamp(r["snap_latest_date"]) for r in prev_runs if r.get("state") == state and str(r.get("method", "")).startswith("v2") and r.get("snap_latest_date")}
    later.add(snap_latest)
    points = [(y, pd.Timestamp(f"{y}-12-31")) for y in YEARS] + [(str(d.date()), d) for d in sorted(later) if pd.Timestamp(f"{last}-12-31") < d <= snap_latest]
    dates = {y: pd.Timestamp(f"{y}-12-31") for y in YEARS}
    active = {lab: st.active_sites(recs, d) for lab, d in points}
    ever = np.unique(np.concatenate(list(active.values())))
    tab = local_table(net, sites, ever, bg, pop.values)
    kx, ky = deg_m(bg.lat.mean())
    nearest_site, crit, near_share, walk, mismatch = {}, {}, {}, {}, 0
    nv = bg.no_vehicle.fillna(0).values
    for lab, _ in points:
        a = active[lab]
        D, src = net.nearest(sites.node.values[a], sites.snap_m.values[a], with_source=True)
        w = np.round(D[bg.node.values] + bg.snap_m.values, 1)     # the published values are the ones measured (v1.1)
        walk[lab] = w
        n_site, n_d, x_d = nearest_two(tab, a, len(bg))
        # identity of the nearest site for every block group, from the shortest-path tree (ties: lowest snap distance)
        node_site = pd.Series(a, index=sites.node.values[a]).groupby(level=0).apply(lambda g: g.iloc[np.argmin(sites.snap_m.values[g.values])])
        tree_site = node_site.reindex(src[bg.node.values]).fillna(-1).astype(int).values
        within_cap = w <= CAP - 0.05
        mismatch += int((within_cap & (np.abs(n_d - (D[bg.node.values] + bg.snap_m.values)) > 0.01) & pop.values).sum())
        ns = np.where(within_cap & (n_site >= 0), n_site, tree_site)
        nearest_site[lab] = ns
        one = pop.values & (w <= MILE) & (x_d > MILE)
        crit[lab] = pd.Series(nv[one]).groupby(ns[one]).sum()
        near_share[lab] = pd.Series(nv[pop.values]).groupby(ns[pop.values]).sum()
        if isinstance(lab, int):
            y = lab
            bg[f"walk_{y}"] = w
            sites[f"active_{y}"] = sites.index.isin(a)
            _, j = cKDTree(np.column_stack([sites.lon.values[a] * kx, sites.lat.values[a] * ky])).query(np.column_stack([bg.lon * kx, bg.lat * ky]))
            bg[f"line_{y}"] = haversine(bg.lon.values, bg.lat.values, sites.lon.values[a][j], sites.lat.values[a][j])
            bg[f"next_{y}"] = np.round(np.minimum(x_d, CAP), 1)
            bg[f"one_store_{y}"] = one
            sites[f"criticality_{y}"] = crit[y].reindex(sites.index).fillna(0).astype(int).where(sites[f"active_{y}"])
    act = sites[[f"active_{y}" for y in YEARS]].to_numpy()
    sites["first_active"] = np.where(act.any(1), np.array(YEARS)[act.argmax(1)], np.nan)
    sites["last_active"] = np.where(act.any(1), np.array(YEARS)[len(YEARS) - 1 - act[:, ::-1].argmax(1)], np.nan)
    addr = recs.assign(a=st.address_key(recs)).groupby("site").a.apply(lambda x: set(v for v in x if v))

    bg["town"], names, town_how = towns(state, bg)
    bg["border_m"], border_km = border_distance(fips, bg)
    bg["near_border"] = bg.border_m <= MILE
    tname = lambda g: names.get(g, ("", "", ""))[0] if isinstance(g, str) else ""

    # ---- ended and new authorizations between consecutive evaluation points (v2, 3)
    dstr = lambda lab: f"{lab}-12-31" if isinstance(lab, int) else lab
    labels = [lab for lab, _ in points]
    ev = []
    for p0, p1 in zip(labels[:-1], labels[1:]):
        a0, a1 = set(active[p0]), set(active[p1])
        for sid in sorted(a0 - a1):
            back = next((l for l in labels[labels.index(p1) + 1:] if sid in set(active[l])), None)
            ev.append({"from": dstr(p0), "to": dstr(p1), "kind": "ended", "site": sid, "resumed": "" if back is None else dstr(back),
                       "only_store_within_1mi_no_vehicle_hh": int(crit[p0].get(sid, 0)), "nearest_store_no_vehicle_hh": int(near_share[p0].get(sid, 0))})
        crossed = pop.values & (walk[p0] > MILE) & (walk[p1] <= MILE)
        for sid in sorted(a1 - a0):
            m = crossed & (nearest_site[p1] == sid)
            ev.append({"from": dstr(p0), "to": dstr(p1), "kind": "began", "site": sid, "resumed": "",
                       "brought_within_1mi_no_vehicle_hh": int(nv[m].sum()), "nearest_store_no_vehicle_hh": int(near_share[p1].get(sid, 0))})
    closures = pd.DataFrame(ev)
    if len(closures):
        closures = closures.join(sites[["name", "city", "county", "state", "in_state", "lon", "lat", "types"]], on="site")
        closures = closures.fillna({"only_store_within_1mi_no_vehicle_hh": 0, "brought_within_1mi_no_vehicle_hh": 0})
        for c in ["only_store_within_1mi_no_vehicle_hh", "brought_within_1mi_no_vehicle_hh"]: closures[c] = closures[c].astype(int)
        # v2 corrections 2 and 5: an ended authorization paired with one that began in the same period at the same
        # street address, or within 300 m, is a re-authorization or change of operator, not a closure
        closures["paired_with"] = ""
        for to, g in closures.groupby("to"):
            e, b_ = g[g.kind == "ended"], g[g.kind == "began"]
            if not len(e) or not len(b_): continue
            d = haversine(e.lon.values[:, None], e.lat.values[:, None], b_.lon.values[None, :], b_.lat.values[None, :])
            used = set()
            for i in range(len(e)):
                same = [j for j in range(len(b_)) if j not in used and addr.get(e.site.values[i], set()) & addr.get(b_.site.values[j], set())]
                near = [j for j in np.argsort(d[i]) if j not in used and d[i][j] <= REPLACE_M]
                j = same[0] if same else (near[0] if near else None)
                if j is None: continue
                used.add(j)
                why = "same address" if same else f"{d[i][j]:.0f} m"
                closures.loc[e.index[i], ["kind", "paired_with"]] = ["replaced", f"{b_['name'].values[j]} ({why})"]
                closures.loc[b_.index[j], ["kind", "paired_with"]] = ["replacement", f"{e['name'].values[i]} ({why})"]
        # v2.1 re-review: an ended site sharing a street address with a site open at both dates (an overlapping
        # re-authorization) continued at that address
        lab_of = {dstr(l): l for l in labels}
        for i in closures.index[closures.kind == "ended"]:
            sid, p0, p1 = closures.at[i, "site"], lab_of[closures.at[i, "from"]], lab_of[closures.at[i, "to"]]
            key = addr.get(sid, set())
            if not key: continue
            both = (set(active[p0]) & set(active[p1])) - {sid}
            other = next((o for o in both if addr.get(o, set()) & key), None)
            if other is not None:
                closures.loc[i, ["kind", "paired_with"]] = ["replaced", f"{sites.at[other, 'name']} (same address, already open)"]
        # out-of-state sites are listed only when nearest for at least one of the state's populated block groups (v2.1 §6)
        nearest_bgs = {lab: set(np.unique(nearest_site[lab][pop.values])) for lab in labels}
        rel = closures.in_state | closures.apply(lambda r: r.site in nearest_bgs[lab_of[r["from"] if r.kind in ("ended", "replaced") else r["to"]]], axis=1)
        closures = closures[rel]
        closures = closures.sort_values(["to", "kind", "only_store_within_1mi_no_vehicle_hh"], ascending=[False, True, False])

    # ---- siting at the latest year-end (v2, 4)
    sit = []
    reach = siting_reach(net, bg, pop, last)
    ok = net.ok & in_state_mask(fips, net.lon, net.lat)
    for label, mask in [("all", np.ones(len(bg), bool)), ("lower_income", (bg.lower_income == 1).values)]:
        for rank, p in enumerate(greedy(net, bg, reach, ok, np.where(mask, nv, 0.0)), 1):
            sit.append({"list": label, "rank": rank, **p})
    del reach
    sit = pd.DataFrame(sit)
    if len(sit):
        r = _shp(ROOT / "data" / "raw" / state / "cb_cousub.zip"); fl = [x[0] for x in r.fields[1:]]
        polys = [(shp_shape(sr.shape.__geo_interface__), dict(zip(fl, sr.record))) for sr in r.iterShapeRecords()]
        def where(x, y):
            for g, rc in polys:
                if g.intersects(Point(x, y)): return rc["NAMELSAD"], rc["NAMELSADCO"]
            return "", ""
        sit["town"], sit["county"] = zip(*[where(x, y) for x, y in zip(sit.lon, sit.lat)])

    # ---- measures
    def measures(y):
        far, half = bg[f"walk_{y}"] > MILE, bg[f"walk_{y}"] > HALF
        lo = bg.lower_income == 1
        one = bg[f"one_store_{y}"]
        n_types = s[s.in_state & st.active(s, dates[y])]["Store Type"].value_counts()
        return {"year": y, "full_service_sites": int((sites[f"active_{y}"] & sites.in_state).sum()),
                "full_service_sites_incl_across_border": int(sites[f"active_{y}"].sum()),
                "no_vehicle_hh_beyond_1mi": int(bg.no_vehicle[pop & far].sum()),
                "no_vehicle_hh_beyond_1mi_lower_income": int(bg.no_vehicle[pop & far & lo].sum()),
                "no_vehicle_hh_beyond_half_mi": int(bg.no_vehicle[pop & half].sum()),
                "people_beyond_1mi": int(bg.people[pop & far].sum()),
                "people_beyond_1mi_lower_income": int(bg.people[pop & far & lo].sum()),
                "people_beyond_half_mi": int(bg.people[pop & half].sum()),
                "block_groups_beyond_1mi": int((pop & far).sum()),
                "no_vehicle_hh_beyond_1mi_not_near_border": int(bg.no_vehicle[pop & far & ~bg.near_border].sum()),
                "no_vehicle_hh_one_store": int(bg.no_vehicle[pop & one].sum()),
                "no_vehicle_hh_one_store_lower_income": int(bg.no_vehicle[pop & one & lo].sum()),
                "block_groups_one_store": int((pop & one).sum()),
                **{f"snap_{k.lower().replace(' ', '_').replace('/', '_').replace(chr(39), '')}": int(v) for k, v in n_types.items()}}
    years = pd.DataFrame([measures(y) for y in YEARS]).fillna(0)
    for c in years.columns: years[c] = years[c].astype(int)

    lost = pop & (bg[f"walk_{first}"] <= MILE) & (bg[f"walk_{last}"] > MILE)
    gained = pop & (bg[f"walk_{first}"] > MILE) & (bg[f"walk_{last}"] <= MILE)
    far = pop & (bg[f"walk_{last}"] > MILE)
    one = pop & bg[f"one_store_{last}"]
    tw = bg[pop].assign(far=far[pop], one=one[pop]).groupby("town").apply(lambda g: pd.Series({
        "households": g.households.sum(), "no_vehicle_hh": g.no_vehicle.sum(), "no_vehicle_hh_beyond_1mi": g.no_vehicle[g.far].sum(),
        "no_vehicle_hh_one_store": g.no_vehicle[g.one].sum(),
        "people": g.people.sum(), "people_beyond_1mi": g.people[g.far].sum(), "block_groups": len(g),
        "block_groups_near_border": int(g.near_border.sum())}), include_groups=False)
    tw["share_no_vehicle_hh_beyond_1mi"] = (tw.no_vehicle_hh_beyond_1mi / tw.no_vehicle_hh.where(tw.no_vehicle_hh > 0)).round(4)
    tw.insert(0, "name", [names.get(i, ("", ""))[0] for i in tw.index])
    tw.insert(1, "countyfp", [names.get(i, ("", ""))[1] for i in tw.index])
    tw.insert(2, "county", [names.get(i, ("", "", ""))[2] for i in tw.index])

    extras = {}
    if "njeda_fdc" in cfg.get("extras", []):
        extras["njeda_fdc"] = fdc_comparison(raw, bg, pop, YEARS, names)
    if "fourth_round" in cfg.get("extras", []):
        extras["fourth_round"] = housing_comparison(raw, tw, manifest)

    # ---- health
    snap_far = float((bg.snap_m[pop] > 500).mean())
    in_main = float((net.part[bg.node.values[pop.values]] == net.largest_part).mean())   # v2 correction: per state, not per network
    unreachable_ids = sorted(set(bg.geoid[pop & ~np.isfinite(bg[[f"walk_{y}" for y in YEARS]]).all(axis=1)]))
    unreachable = len(unreachable_ids)
    acs_ids = pd.read_csv(raw / "acs_b01003.csv", dtype=str, usecols=["GEO_ID"]).GEO_ID
    acs_ids = acs_ids[acs_ids.str.startswith("1500000US")].str[9:]
    # reported alongside the block-group checks (v2.1): the no-vehicle households in the block groups concerned
    snap_far_nv = float(bg.no_vehicle[pop & (bg.snap_m > 500)].sum() / bg.no_vehicle[pop].sum())
    unreachable_nv = int(bg.no_vehicle[bg.geoid.isin(unreachable_ids)].sum())
    shorter = int(sum(((bg[f"walk_{y}"] < bg[f"line_{y}"] - 1.0) & pop).sum() for y in YEARS))
    prev = [json.loads(l) for l in (ROOT / "data" / "runs.jsonl").read_text().splitlines() if l.strip()] if (ROOT / "data" / "runs.jsonl").exists() else []
    prev_km = next((r["network_km"] for r in reversed(prev) if r.get("state") == state and r.get("network_km") and str(r.get("method", "")).startswith("v2")), None)
    km_change = None if prev_km is None else abs(net.length_km - prev_km) / prev_km
    this_year = pd.Timestamp.now().year
    clubs = re.compile(r"COSTCO|B\.? ?J'?S WHOLESALE|SAM'?S CLUB", re.I)
    latest_active = recs[st.active(recs, dates[last]) & recs.in_state]
    club_only = int(latest_active.groupby("site")["Store Name"].apply(lambda x: all(clubs.search(str(n)) for n in x)).sum())
    unlocated = int((fs.lat.isna() | fs.lon.isna() | (fs.lat == 0) | (fs.lon == 0)).sum())
    age = (pd.Timestamp.now() - snap_latest).days
    checks = {
        "snap_far_share": {"value": round(snap_far, 4), "no_vehicle_hh_share": round(snap_far_nv, 4),
                           "limit": f"<= {MAX_SNAP_FAR_SHARE} of populated block groups", "ok": snap_far <= MAX_SNAP_FAR_SHARE},
        "block_groups_in_largest_network_part": {"value": round(in_main, 4), "network_share": round(net.largest_part_share, 4),
                                                 "limit": f">= {MIN_LARGEST_PART} of populated block groups", "ok": in_main >= MIN_LARGEST_PART},
        "unlocated_full_service_records": {"value": unlocated, "share": round(unlocated / max(len(fs), 1), 4), "limit": f"share <= {MAX_UNLOCATED_SHARE}", "ok": unlocated / max(len(fs), 1) <= MAX_UNLOCATED_SHARE},
        "unreachable_block_groups": {"value": unreachable, "no_vehicle_hh": unreachable_nv, "ids": unreachable_ids,
                                     "limit": "== 0", "ok": unreachable == 0},
        "walk_shorter_than_straight_line": {"value": shorter, "limit": "== 0 (block group-years, 1 m tolerance)", "ok": shorter == 0},
        "nearest_two_matches_walk": {"value": mismatch, "limit": "== 0 (block group-years within 2 miles, 1 cm tolerance)", "ok": mismatch == 0},
        "network_km_change_vs_previous_run": {"value": None if km_change is None else round(km_change, 4), "km": round(net.length_km),
                                               "limit": "<= 0.05 (same state, v2 border rule)", "ok": km_change is None or km_change <= 0.05},
        "acs_vintage": {"value": manifest["acs_year"], "limit": f">= {this_year - 3}", "ok": manifest["acs_year"] >= this_year - 3},
        "tiger_vintage": {"value": manifest["tiger_year"], "limit": f">= {this_year - 3}", "ok": manifest["tiger_year"] >= this_year - 3},
        "snap_file_latest_date": {"value": str(snap_latest.date()), "age_days": age, "limit": f"age <= {MAX_SOURCE_AGE_DAYS}", "ok": age <= MAX_SOURCE_AGE_DAYS},
        "acs_rows_matched": {"value": int(bg.people.notna().sum()), "of": len(bg), "ok": bool(bg.people.notna().all()),
                             "centroids_without_acs": sorted(bg.geoid[bg.people.isna()].tolist()),
                             "pop2020_without_acs": int(bg.pop2020[bg.people.isna()].sum()),
                             "acs_block_groups_without_centroid": int((~acs_ids.isin(bg.geoid)).sum())},
        "full_service_sites_latest": {"value": int((sites[f"active_{last}"] & sites.in_state).sum()), "limit": "> 0", "ok": bool((sites[f"active_{last}"] & sites.in_state).sum() > 0)},
    }
    L = years.set_index("year")
    summary = {
        "method": METHOD, "state": state, "state_name": cfg["name"], "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "years": YEARS, "latest_year_end": f"{last}-12-31", "first_year_end": f"{first}-12-31", "snap_latest_date": str(snap_latest.date()),
        "acs": f"{manifest['acs_year'] - 4}-{manifest['acs_year']} 5-year", "tiger": manifest["tiger_year"],
        "state_median_household_income": state_median,
        "block_groups": int(len(bg)), "populated_block_groups": int(pop.sum()),
        "no_vehicle_hh_total": int(bg.no_vehicle[pop].sum()), "people_total": int(bg.people[pop].sum()),
        "lower_income_block_groups": int((bg.lower_income == 1).sum()), "unclassified_income_block_groups": int(bg.lower_income.isna().sum()),
        "latest": {k: int(v) for k, v in L.loc[last].items()},
        "first": {k: int(v) for k, v in L.loc[first].items()},
        "crossed_1mi": {"to_beyond": int(lost.sum()), "to_within": int(gained.sum()),
                        "no_vehicle_hh_to_beyond": int(bg.no_vehicle[lost].sum()), "no_vehicle_hh_to_within": int(bg.no_vehicle[gained].sum())},
        "near_border_block_groups": int((bg.near_border & pop).sum()), "shared_border_km": round(border_km, 1),
        "buffer_counties": manifest.get("buffer_counties", []),
        "nearest_store_across_border_block_groups": int((pop & (pd.Series(nearest_site[last]).map(lambda i: i >= 0 and not sites.in_state.get(i, True)).values)).sum()),
        "network": {"points": net.n, "edges": net.edges_used, "km": round(net.length_km), "parts": net.parts},
        "populated_block_groups_snapped_outside_state": sorted(bg.geoid[pop & ~in_state_mask(fips, net.lon[bg.node.values], net.lat[bg.node.values])].tolist()),
        "walk_over_straight_line_latest": {q: round(float(np.nanquantile((bg[f"walk_{last}"] / bg[f"line_{last}"].where(bg[f"line_{last}"] > 100))[pop], v)), 3)
                                           for q, v in [("min", 0), ("median", .5), ("p90", .9), ("max", 1)]},
        "sites_ever": int(sites.in_state.sum()), "warehouse_club_only_sites_latest": club_only, "town_assignment": town_how,
        "full_service_records": int(len(fs)),
        "most_critical_sites_latest": sites[sites[f"active_{last}"]].nlargest(10, f"criticality_{last}")[["name", "city", "state", f"criticality_{last}"]]
                                      .rename(columns={f"criticality_{last}": "only_store_within_1mi_no_vehicle_hh"}).to_dict(orient="records"),
        "ended_since_first_year": ended_summary(closures),
        "siting": sit.to_dict(orient="records") if len(sit) else [],
        **extras,
        "health": checks, "healthy": all(c["ok"] for c in checks.values()),
    }
    cols = ["geoid", "lon", "lat", "pop2020", "people", "households", "no_vehicle", "no_vehicle_moe", "median_income", "median_income_moe",
            "poverty_rate", "lower_income", "town", "border_m", "near_border", "snap_m"] + [f"walk_{y}" for y in YEARS] + [f"next_{y}" for y in YEARS]
    bgo = bg[cols].copy()
    if "fdc" in bg: bgo["njeda_fdc"] = bg.fdc
    for c in ["border_m", "snap_m"]: bgo[c] = bgo[c].round(0)
    bgo["poverty_rate"] = bgo.poverty_rate.round(4)
    bgo["nearest_site_latest"] = nearest_site[last]
    bgo.to_csv(out / "bg_access.csv", index=False)
    sites.drop(columns="node").round({"snap_m": 0}).to_csv(out / "sites.csv", index_label="site")
    tw.to_csv(out / "towns.csv", index_label="town")
    years.to_csv(out / "years.csv", index=False)
    closures.to_csv(out / "closures.csv", index=False)
    sit.to_csv(out / "siting.csv", index=False)
    # v3 A.8: sites within 2 miles of each block group (for the access-risk forecast)
    tab.assign(geoid=bg.geoid.values[tab.bg.values.astype(int)], d=tab.d.round(1))[["site", "geoid", "d"]].to_csv(out / "site_bg_2mi.csv.gz", index=False)
    (out / "summary.json").write_text(json.dumps(clean_json(summary), indent=2, allow_nan=False) + "\n")
    run = {"utc": summary["built_utc"], "method": METHOD, "state": state, "healthy": summary["healthy"],
           "sources": {k: v.get("sha256", "")[:12] for k, v in manifest["files"].items() if not k.startswith("edges_")},
           "snap_latest_date": summary["snap_latest_date"], "network_km": round(net.length_km, 1),
           "latest": summary["latest"], "crossed_1mi": summary["crossed_1mi"]}
    with (ROOT / "data" / "runs.jsonl").open("a") as fh: fh.write(json.dumps(run) + "\n")
    print(json.dumps({k: summary[k] for k in ["latest", "crossed_1mi", "healthy"]}, indent=1))
    if not summary["healthy"]:
        print("HEALTH CHECK FAILED:", {k: v for k, v in checks.items() if not v["ok"]})
    return summary

def clean_json(o):
    """Strict JSON: numpy scalars to Python, non-finite numbers to null (e.g. the walk/straight-line maximum when a block group is unreachable)."""
    if isinstance(o, dict): return {k: clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean_json(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (float, np.floating)): return float(o) if np.isfinite(o) else None
    if isinstance(o, np.bool_): return bool(o)
    return o

def ended_summary(c):
    if not len(c): return {"sites": 0, "only_store_within_1mi_no_vehicle_hh": 0}
    e = c[(c.kind == "ended") & c.in_state]
    r = e[e.resumed.fillna("") != ""]; nr = e[e.resumed.fillna("") == ""]
    return {"entries": int(len(e)), "sites": int(e.site.nunique()), "only_store_within_1mi_no_vehicle_hh": int(e.only_store_within_1mi_no_vehicle_hh.sum()),
            "later_resumed_entries": int(len(r)), "later_resumed_sites": int(r.site.nunique()), "later_resumed_no_vehicle_hh": int(r.only_store_within_1mi_no_vehicle_hh.sum()),
            "not_resumed_entries": int(len(nr)), "not_resumed_sites": int(nr.site.nunique()), "not_resumed_no_vehicle_hh": int(nr.only_store_within_1mi_no_vehicle_hh.sum()),
            "replaced_in_state": int(((c.kind == "replaced") & c.in_state).sum())}

def fdc_comparison(raw, bg, pop, YEARS, names):
    """NJEDA Food Desert Communities vs walking access (v2, 5)."""
    f = pd.read_csv(raw / "fdc_block_groups.csv", dtype={"BG_FIPS": str})
    rel = pd.read_csv(raw / "bg_rel_2020_2010.csv", dtype={"GEOID_BLKGRP_20": str, "GEOID_BLKGRP_10": str})
    rel["des"] = rel.GEOID_BLKGRP_10.isin(set(f.BG_FIPS))
    part = rel.groupby("GEOID_BLKGRP_20").apply(lambda g: g.AREALAND_PART[g.des].sum() / g.AREALAND_BLKGRP_20.iloc[0] if g.AREALAND_BLKGRP_20.iloc[0] > 0 else 0.0, include_groups=False)
    bg["fdc"] = bg.geoid.map(part).fillna(0) >= 0.5
    lo = bg.lower_income == 1
    out = {"designated_2010_block_groups": int(len(f)), "matched_2020_block_groups": int(bg.fdc.sum()),
           "unmatched_2010_ids": int((~f.BG_FIPS.isin(rel.GEOID_BLKGRP_10)).sum())}
    for y in [2021, YEARS[-1]]:
        if y not in YEARS: continue
        far = pop & (bg[f"walk_{y}"] > MILE)
        nvf = bg.no_vehicle[far].sum()
        miss = bg[far & lo & ~bg.fdc & pop]
        top = miss.groupby("town").no_vehicle.sum().sort_values(ascending=False).head(15)
        out[str(y)] = {
            "share_of_no_vehicle_hh_beyond_1mi_in_designated": round(float(bg.no_vehicle[far & bg.fdc].sum() / nvf), 4),
            "no_vehicle_hh_beyond_1mi": int(nvf), "no_vehicle_hh_beyond_1mi_in_designated": int(bg.no_vehicle[far & bg.fdc].sum()),
            "share_of_designated_no_vehicle_hh_beyond_1mi": round(float(bg.no_vehicle[far & bg.fdc].sum() / bg.no_vehicle[pop & bg.fdc].sum()), 4),
            "lower_income_beyond_1mi_not_designated": {"block_groups": int(len(miss)), "no_vehicle_hh": int(miss.no_vehicle.sum())},
            "top_towns_lower_income_beyond_1mi_not_designated": [{"town": names.get(t, ("",))[0], "county": names.get(t, ("", "", ""))[2], "no_vehicle_hh": int(v)} for t, v in top.items()],
            "designated_within_half_mi": {"block_groups": int((pop & bg.fdc & (bg[f"walk_{y}"] <= HALF)).sum()),
                                          "no_vehicle_hh": int(bg.no_vehicle[pop & bg.fdc & (bg[f"walk_{y}"] <= HALF)].sum())},
        }
    return out

def housing_comparison(raw, tw, manifest):
    """Fourth Round prospective need vs town walking access (v2, 5)."""
    h = pd.read_csv(raw / "fourth_round_obligations.csv", dtype={"fips": str})
    h["prospective_need"] = pd.to_numeric(h.prospective_need, errors="coerce").fillna(0)
    t = tw.join(h.set_index("fips")[["prospective_need"]], how="outer")
    t["prospective_need"] = t.prospective_need.fillna(0)
    total = float(t.prospective_need.sum())
    grp = t.share_no_vehicle_hh_beyond_1mi >= 0.5
    top = t[grp & (t.prospective_need > 0)].sort_values("prospective_need", ascending=False).head(15)
    return {"source_commit": manifest["files"].get("fourth_round", {}).get("commit"),
            "towns_with_obligation": int((t.prospective_need > 0).sum()), "prospective_need_total": int(total),
            "unmatched_towns": int((~h.fips.isin(tw.index)).sum()),
            "towns_with_obligation_no_share": int(((t.prospective_need > 0) & t.share_no_vehicle_hh_beyond_1mi.isna()).sum()),
            "prospective_need_in_half_beyond_towns": int(t.prospective_need[grp].sum()),
            "share_in_half_beyond_towns": round(float(t.prospective_need[grp].sum() / total), 4),
            "households_share_in_half_beyond_towns": round(float(t.households[grp].sum() / t.households.sum()), 4),
            "towns_half_beyond": int(grp.sum()), "towns_with_households": int((t.households > 0).sum()),
            "towns_half_beyond_with_obligation": int((grp & (t.prospective_need > 0)).sum()),
            "top": [{"town": r["name"], "county": r.county, "prospective_need": int(r.prospective_need),
                     "share_no_vehicle_hh_beyond_1mi": float(r.share_no_vehicle_hh_beyond_1mi), "no_vehicle_hh": int(r.no_vehicle_hh)} for _, r in top.iterrows()]}

if __name__ == "__main__":
    for stt in (sys.argv[1:] or states().keys()):
        main(stt)

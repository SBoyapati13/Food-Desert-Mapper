"""Walking access to full-service food stores, by block group, at each year-end (method v1, see CHANGELOG).

    python3 src/build.py NJ

Reads data/raw/<STATE>/ and data/cache/ (run src/fetch.py first). Writes out/<STATE>/:
  bg_access.csv    one row per block group: people, households, no-vehicle households, lower-income flag,
                   town, border flag, snap distance, walking distance (m) at each year-end
  sites.csv        full-service store sites with first and last year-end active
  towns.csv        county subdivisions: no-vehicle households and people beyond 1 mile (latest year-end)
  years.csv        statewide headline measures at each year-end
  summary.json     latest headline numbers, changes since the first year-end, health checks
and appends one line to data/runs.jsonl.
"""
import io, json, sys, zipfile
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
from network import Network

METHOD = "v1"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MILE, HALF = 1609.344, 804.672
YEARS = list(range(2015, 2026))
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
    r = _shp(ROOT / "data" / "raw" / state / "cb_cousub.zip")
    f = [x[0] for x in r.fields[1:]]
    geoms, recs = [], []
    for sr in r.iterShapeRecords():
        geoms.append(shp_shape(sr.shape.__geo_interface__)); recs.append(dict(zip(f, sr.record)))
    tree = STRtree(geoms)
    out = []
    for x, y in zip(bg.lon, bg.lat):
        hit = list(tree.query(Point(x, y), predicate="intersects"))
        out.append(recs[hit[0]]["GEOID"] if hit else None)
    names = {rc["GEOID"]: (rc["NAMELSAD"], rc["COUNTYFP"]) for rc in recs}
    return pd.Series(out, index=bg.index), names

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
    lat0 = np.radians(bg.lat.mean()); kx, ky = np.cos(lat0) * 111320.0, 110574.0
    L = affinity.scale(line, xfact=kx, yfact=ky, origin=(0, 0))
    d = [L.distance(Point(x * kx, y * ky)) for x, y in zip(bg.lon, bg.lat)]
    return pd.Series(d, index=bg.index), L.length / 1000

def main(state):
    cfg = states()[state]; fips = cfg["fips"]
    raw, out = ROOT / "data" / "raw" / state, ROOT / "out" / state
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((raw / "manifest.json").read_text())
    fetch.ensure_cache(state)

    bg, state_median = block_groups(state, cfg)
    s = st.load(raw / "snap_retailers.csv")
    recs, sites = st.sites(s)
    fs = s[s.full_service]
    net = Network(sorted(CACHE.glob(f"tl_{manifest['tiger_year']}_{fips}*_edges.zip")))
    bg["node"], bg["snap_m"] = net.snap(bg.lon.values, bg.lat.values)
    sites["node"], sites["snap_m"] = net.snap(sites.lon.values, sites.lat.values)

    dates = [pd.Timestamp(f"{y}-12-31") for y in YEARS]
    for y, d in zip(YEARS, dates):
        a = st.active_sites(recs, d)
        D = net.nearest(sites.node.values[a], sites.snap_m.values[a])
        bg[f"walk_{y}"] = D[bg.node.values] + bg.snap_m.values
        sites[f"active_{y}"] = sites.index.isin(a)
    act = sites[[f"active_{y}" for y in YEARS]].to_numpy()
    sites["first_active"] = np.where(act.any(1), np.array(YEARS)[act.argmax(1)], np.nan)
    sites["last_active"] = np.where(act.any(1), np.array(YEARS)[len(YEARS) - 1 - act[:, ::-1].argmax(1)], np.nan)

    bg["town"], names = towns(state, bg)
    bg["border_m"], border_km = border_distance(fips, bg)
    bg["near_border"] = bg.border_m <= MILE

    # ---- measures
    pop = bg.pop2020 > 0
    last, first = YEARS[-1], YEARS[0]
    def measures(y):
        far, half = bg[f"walk_{y}"] > MILE, bg[f"walk_{y}"] > HALF
        lo = bg.lower_income == 1
        n_types = s[st.active(s, pd.Timestamp(f"{y}-12-31"))]["Store Type"].value_counts()
        return {"year": y, "full_service_sites": int(sites[f"active_{y}"].sum()),
                "no_vehicle_hh_beyond_1mi": int(bg.no_vehicle[pop & far].sum()),
                "no_vehicle_hh_beyond_1mi_lower_income": int(bg.no_vehicle[pop & far & lo].sum()),
                "no_vehicle_hh_beyond_half_mi": int(bg.no_vehicle[pop & half].sum()),
                "people_beyond_1mi": int(bg.people[pop & far].sum()),
                "people_beyond_1mi_lower_income": int(bg.people[pop & far & lo].sum()),
                "people_beyond_half_mi": int(bg.people[pop & half].sum()),
                "block_groups_beyond_1mi": int((pop & far).sum()),
                "no_vehicle_hh_beyond_1mi_not_near_border": int(bg.no_vehicle[pop & far & ~bg.near_border].sum()),
                **{f"snap_{k.lower().replace(' ', '_').replace('/', '_').replace(chr(39), '')}": int(v) for k, v in n_types.items()}}
    years = pd.DataFrame([measures(y) for y in YEARS]).fillna(0)
    for c in years.columns: years[c] = years[c].astype(int)

    lost = pop & (bg[f"walk_{first}"] <= MILE) & (bg[f"walk_{last}"] > MILE)
    gained = pop & (bg[f"walk_{first}"] > MILE) & (bg[f"walk_{last}"] <= MILE)
    far = pop & (bg[f"walk_{last}"] > MILE)
    tw = bg[pop].assign(far=far[pop]).groupby("town").apply(lambda g: pd.Series({
        "no_vehicle_hh": g.no_vehicle.sum(), "no_vehicle_hh_beyond_1mi": g.no_vehicle[g.far].sum(),
        "people": g.people.sum(), "people_beyond_1mi": g.people[g.far].sum(), "block_groups": len(g),
        "block_groups_near_border": int(g.near_border.sum())}), include_groups=False)
    tw["share_no_vehicle_hh_beyond_1mi"] = (tw.no_vehicle_hh_beyond_1mi / tw.no_vehicle_hh.where(tw.no_vehicle_hh > 0)).round(4)
    tw.insert(0, "name", [names.get(i, ("", ""))[0] for i in tw.index])
    tw.insert(1, "countyfp", [names.get(i, ("", ""))[1] for i in tw.index])

    # ---- health
    snap_far = float((bg.snap_m[pop] > 500).mean())
    unreachable = int((~np.isfinite(bg[f"walk_{last}"]) & pop).sum())
    unlocated = int((fs.lat.isna() | fs.lon.isna() | (fs.lat == 0) | (fs.lon == 0)).sum())
    snap_latest = max(s.auth.max(), s.end.max())
    age = (pd.Timestamp.now() - snap_latest).days
    checks = {
        "snap_far_share": {"value": round(snap_far, 4), "limit": f"<= {MAX_SNAP_FAR_SHARE}", "ok": snap_far <= MAX_SNAP_FAR_SHARE},
        "largest_network_part": {"value": round(net.largest_part_share, 4), "limit": f">= {MIN_LARGEST_PART}", "ok": net.largest_part_share >= MIN_LARGEST_PART},
        "unlocated_full_service_records": {"value": unlocated, "share": round(unlocated / len(fs), 4), "limit": f"share <= {MAX_UNLOCATED_SHARE}", "ok": unlocated / len(fs) <= MAX_UNLOCATED_SHARE},
        "unreachable_block_groups": {"value": unreachable, "limit": "== 0", "ok": unreachable == 0},
        "snap_file_latest_date": {"value": str(snap_latest.date()), "age_days": age, "limit": f"age <= {MAX_SOURCE_AGE_DAYS}", "ok": age <= MAX_SOURCE_AGE_DAYS},
        "acs_rows_matched": {"value": int(bg.people.notna().sum()), "of": len(bg), "ok": bool(bg.people.notna().all())},
        "full_service_sites_latest": {"value": int(sites[f"active_{last}"].sum()), "limit": "> 0", "ok": bool(sites[f"active_{last}"].sum() > 0)},
    }
    L = years.set_index("year")
    summary = {
        "method": METHOD, "state": state, "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_year_end": f"{last}-12-31", "first_year_end": f"{first}-12-31",
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
        "network": {"points": net.n, "edges": net.edges_used, "km": round(net.length_km), "parts": net.parts},
        "sites_ever": int(len(sites)), "full_service_records": int(len(fs)),
        "health": checks, "healthy": all(c["ok"] for c in checks.values()),
    }
    cols = ["geoid", "lon", "lat", "pop2020", "people", "households", "no_vehicle", "no_vehicle_moe", "median_income", "median_income_moe",
            "poverty_rate", "lower_income", "town", "border_m", "near_border", "snap_m"] + [f"walk_{y}" for y in YEARS]
    bgo = bg[cols].copy()
    for c in ["border_m", "snap_m"] + [f"walk_{y}" for y in YEARS]: bgo[c] = bgo[c].round(0)
    bgo["poverty_rate"] = bgo.poverty_rate.round(4)
    bgo.to_csv(out / "bg_access.csv", index=False)
    sites.drop(columns="node").round({"snap_m": 0}).to_csv(out / "sites.csv", index_label="site")
    tw.to_csv(out / "towns.csv", index_label="town")
    years.to_csv(out / "years.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    run = {"utc": summary["built_utc"], "method": METHOD, "state": state, "healthy": summary["healthy"],
           "sources": {k: v.get("sha256", "")[:12] for k, v in manifest["files"].items() if not k.startswith("edges_")},
           "latest": summary["latest"], "crossed_1mi": summary["crossed_1mi"]}
    with (ROOT / "data" / "runs.jsonl").open("a") as fh: fh.write(json.dumps(run) + "\n")
    print(json.dumps({k: summary[k] for k in ["latest", "first", "crossed_1mi", "healthy"]}, indent=1))
    if not summary["healthy"]:
        print("HEALTH CHECK FAILED:", {k: v for k, v in checks.items() if not v["ok"]})
    return summary

if __name__ == "__main__":
    for stt in (sys.argv[1:] or states().keys()):
        main(stt)

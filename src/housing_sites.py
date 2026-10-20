"""Walking access to full-service food stores from Fourth Round affordable-housing sites (method v3 B, see CHANGELOG).

    python3 src/housing_sites.py            # after build.py NJ

Input:  data/raw/NJ/fourth_round_sites.csv   sites extracted from towns' Housing Element and Fair Share Plans, each
                                             with its document, page and a verbatim quote, checked by a second pass
Cache:  data/raw/NJ/fourth_round_parcels.json parcel centroids from NJ's statewide parcel composite (fetched once,
                                             refreshed with --refetch)
Output: out/NJ/fourth_round_sites.csv and out/NJ/fourth_round_sites.json (town and overall summaries)
"""
import json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

import fetch, stores as st
from network import Network, haversine

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, CACHE = ROOT / "data" / "raw" / "NJ", ROOT / "out" / "NJ", ROOT / "data" / "cache"
PARCELS = "https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/Parcels_Composite_NJ_WM/FeatureServer/0/query"
MILE, HALF, CAP = 1609.344, 804.672, 2 * 1609.344
UA = {"User-Agent": "food-desert-mapper (public-data research; github.com/SBoyapati13/Food-Desert-Mapper)"}

def _num(t):
    return t.strip().lstrip("0") or "0"

def expand_lots(spec):
    """'17-25' -> 17..25; '13.01-13.05' -> 13.01..13.05; '9;9.01-9.21;31' -> list. Unparseable parts are skipped."""
    out = []
    for part in re.split(r"[;,&]| and ", str(spec)):
        part = part.strip()
        m = re.fullmatch(r"(\d+)(?:\.(\d+))?\s*-\s*(\d+)(?:\.(\d+))?", part)
        if m and m.group(2) is None and m.group(4) is None:
            a, b = int(m.group(1)), int(m.group(3))
            if 0 <= b - a <= 200: out += [str(i) for i in range(a, b + 1)]
            continue
        if m and m.group(2) is not None and m.group(4) is not None and m.group(1) == m.group(3):
            w = len(m.group(2)); a, b = int(m.group(2)), int(m.group(4))
            if 0 <= b - a <= 200: out += [f"{m.group(1)}.{str(i).zfill(w)}" for i in range(a, b + 1)]
            continue
        m = re.fullmatch(r"\d+(?:\.\d+)?", part)
        if m: out.append(part)
    return out

def pairs(block, lot):
    """(block, lot) pairs from the extraction's '101|102' / '101:2;3|102:7' cells."""
    if pd.isna(block) or pd.isna(lot): return []
    blocks = [b.strip() for b in str(block).split("|") if b.strip()]
    lots = [l.strip() for l in str(lot).split("|") if l.strip()]
    if len(blocks) == 1 and not re.match(r"^\d+(\.\d+)?:", lots[0] if lots else ""):
        return [(blocks[0], l) for l in expand_lots(";".join(lots))]
    out = []
    for item in lots:
        if ":" not in item: continue
        b, ls = item.split(":", 1)
        out += [(b.strip(), l) for l in expand_lots(ls)]
    return out

def query(where):
    q = urllib.parse.urlencode({"where": where, "outFields": "PAMS_PIN,PCL_MUN,PCLBLOCK,PCLLOT,PROP_LOC,Shape__Area", "returnGeometry": "false",
                                "returnCentroid": "true", "outSR": "4326", "f": "json"})
    for attempt in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(PARCELS, data=q.encode(), headers=UA), timeout=120).read())
            time.sleep(0.3)
            return [{"pin": f["attributes"]["PAMS_PIN"], "key": f"{f['attributes']['PCL_MUN']}_{f['attributes']['PCLBLOCK']}_{f['attributes']['PCLLOT']}",
                     "loc": f["attributes"]["PROP_LOC"], "area": f["attributes"]["Shape__Area"],
                     "lon": f["centroid"]["x"], "lat": f["centroid"]["y"]} for f in d.get("features", []) if f.get("centroid")]
        except Exception:
            time.sleep(3)
    raise RuntimeError(f"parcel query failed: {where[:80]}")

SKIP = {"N", "S", "E", "W", "NORTH", "SOUTH", "EAST", "WEST", "AVE", "AVENUE", "ST", "STREET", "RD", "ROAD", "DR", "DRIVE",
        "HWY", "HIGHWAY", "ROUTE", "RT", "US", "BLVD", "LN", "LANE", "PIKE", "THE", "OLD"}

def locate(sites, refetch=False):
    """Parcel centroids by municipality + block + lot (all qualifier codes of a lot are included); else by address."""
    cpath = RAW / "fourth_round_parcels.json"
    cache = {} if refetch or not cpath.exists() else json.loads(cpath.read_text())["parcels"]
    rows = []
    for _, r in sites.iterrows():
        want = [f"{r.pcl_mun}_{b}_{l}" for b, l in pairs(r.block, r.lot)]
        need = [k for k in want if k not in cache]
        for i in range(0, len(need), 40):
            chunk = need[i:i + 40]
            cond = " OR ".join(f"(PCLBLOCK='{k.split('_')[1]}' AND PCLLOT='{k.split('_')[2]}')" for k in chunk)
            got = query(f"PCL_MUN='{r.pcl_mun}' AND ({cond})")
            for k in chunk: cache[k] = [g for g in got if g["key"] == k] or None
        hits = [g for k in want if cache.get(k) for g in cache[k]]
        how = "block/lot"
        if not hits and isinstance(r.address, str) and re.match(r"\d+", r.address.strip()):
            k = f"addr:{r.pcl_mun}:{r.address.strip().upper()}"
            if k not in cache:
                m = re.match(r"(\d+)", r.address.strip())
                words = [w for w in re.sub(r"[^A-Z ]", " ", r.address.upper()).split() if w not in SKIP and len(w) > 2]
                route = re.findall(r"\d+", r.address.strip()[len(m.group(1)):])
                tail = words[0] if words else (route[0] if route else None)
                cache[k] = query(f"PCL_MUN='{r.pcl_mun}' AND PROP_LOC LIKE '{m.group(1)}[- ]%{tail}%'") if tail else []
            hits, how = cache[k], "address"
        if hits:
            a = np.array([h["area"] or 1.0 for h in hits]); lon = np.array([h["lon"] for h in hits]); lat = np.array([h["lat"] for h in hits])
            rows.append({"lon": float((lon * a).sum() / a.sum()), "lat": float((lat * a).sum() / a.sum()), "parcels_requested": len(want),
                         "parcels_matched": sum(1 for k in want if cache.get(k)), "located_by": how,
                         "matched_addresses": "; ".join(sorted({h["loc"] for h in hits if h["loc"]}))[:200]})
        else:
            rows.append({"lon": np.nan, "lat": np.nan, "parcels_requested": len(want), "parcels_matched": 0, "located_by": "unmatched", "matched_addresses": ""})
    cpath.write_text(json.dumps({"source": PARCELS, "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                 "parcels": cache}, indent=0, sort_keys=True) + "\n")
    return pd.concat([sites.reset_index(drop=True), pd.DataFrame(rows)], axis=1)

def main(refetch=False):
    sites = pd.read_csv(RAW / "fourth_round_sites.csv", dtype={"pcl_mun": str, "fips": str, "block": str, "lot": str})
    sites = locate(sites, refetch)
    manifest = json.loads((RAW / "manifest.json").read_text())
    S = json.loads((OUT / "summary.json").read_text()); last = S["years"][-1]
    fetch.ensure_cache("NJ")
    s = st.load(RAW / "snap_retailers.csv")
    recs, store = st.sites(s)
    a = st.active_sites(recs, pd.Timestamp(f"{last}-12-31"))
    counties = ["34"] + manifest.get("buffer_counties", [])
    net = Network(sorted({p for c in counties for p in CACHE.glob(f"tl_{manifest['tiger_year']}_{c}*_edges.zip")}))
    store["node"], store["snap_m"] = net.snap(store.lon.values, store.lat.values)
    ok = sites.lat.notna()
    sites.loc[ok, "node"], sites.loc[ok, "snap_m"] = net.snap(sites.lon[ok].values, sites.lat[ok].values)
    net.attach_sources(store.node.values)
    D = net.nearest(store.node.values[a], store.snap_m.values[a])
    snode = pd.Series(store.snap_m.values[a], index=store.node.values[a])
    walk, nxt, near_name = [], [], []
    for _, r in sites.iterrows():
        if not np.isfinite(r.get("snap_m", np.nan)):
            walk.append(np.nan); nxt.append(np.nan); near_name.append(""); continue
        w = D[int(r.node)] + r.snap_m
        hit, d = net.within(int(r.node), CAP)
        m = pd.Series(d, index=hit)
        cand = []
        for sid in a:
            n = int(store.node[sid])
            if n in m.index: cand.append((m[n] + store.snap_m[sid] + r.snap_m, sid))
        cand.sort()
        first = cand[0][1] if cand else None
        rest = [c for c in cand if c[1] != first]
        walk.append(round(float(w), 1)); nxt.append(round(float(min(rest[0][0], CAP)), 1) if rest else CAP)
        near_name.append(str(store.at[first, "name"]) if first is not None and cand[0][0] <= CAP else "")
    sites["walk_m"], sites["next_m"], sites["nearest_store"] = walk, nxt, near_name
    sites["beyond_1mi"] = sites.walk_m > MILE
    sites["within_half_mi"] = sites.walk_m <= HALF
    sites["one_store"] = (sites.walk_m <= MILE) & (sites.next_m > MILE)
    sites.to_csv(OUT / "fourth_round_sites.csv", index=False)

    tw = pd.read_csv(OUT / "towns.csv", dtype={"town": str}).set_index("town")
    inc = sites[sites.include.astype(str).str.lower().eq("yes") & sites.lat.notna()]
    def shares(g):
        u = g.affordable_units.fillna(0)
        tot = float(u.sum())
        return {"sites": int(len(g)), "units": int(tot),
                "units_beyond_1mi_share": round(float(u[g.beyond_1mi].sum() / tot), 4) if tot else None,
                "units_within_half_mi_share": round(float(u[g.within_half_mi].sum() / tot), 4) if tot else None,
                "units_one_store_share": round(float(u[g.one_store].sum() / tot), 4) if tot else None,
                "sites_beyond_1mi": int(g.beyond_1mi.sum())}
    towns = {}
    for t, g in inc.groupby("town"):
        f = g.fips.iloc[0]
        towns[t] = {**shares(g), "fips": f, "town_no_vehicle_hh_beyond_1mi_share": float(tw.share_no_vehicle_hh_beyond_1mi.get(f, np.nan))}
    allu = shares(inc)
    hh = tw.loc[[towns[t]["fips"] for t in towns]]
    yes = sites[sites.include.astype(str).str.lower().eq("yes")]
    out = {"method": "v3 B", "year_end": last, "towns_covered": sorted(towns), "overall": allu,
           "units_in_plan_rows": int(yes.affordable_units.fillna(0).sum()), "units_located": int(inc.affordable_units.fillna(0).sum()),
           "car_free_beyond_1mi_share_in_same_towns": round(float(hh.no_vehicle_hh_beyond_1mi.sum() / hh.no_vehicle_hh.sum()), 4),
           "town_mix_baseline": round(sum(towns[t]["units"] * towns[t]["town_no_vehicle_hh_beyond_1mi_share"] for t in towns) / sum(towns[t]["units"] for t in towns), 4),
           "towns_further_than_car_free": int(sum(1 for t in towns if towns[t]["units_beyond_1mi_share"] is not None and towns[t]["units_beyond_1mi_share"] > towns[t]["town_no_vehicle_hh_beyond_1mi_share"])),
           "towns": towns, "unmatched_sites": sites.loc[sites.lat.isna(), ["town", "site_name"]].to_dict(orient="records"),
           "excluded_rows": int((~sites.include.astype(str).str.lower().eq("yes")).sum())}
    (OUT / "fourth_round_sites.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps({k: out[k] for k in ("overall", "car_free_beyond_1mi_share_in_same_towns", "towns_covered")}, indent=1))

if __name__ == "__main__":
    main("--refetch" in sys.argv)

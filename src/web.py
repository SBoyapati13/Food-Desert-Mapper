"""Build the static site in docs/ from out/<STATE>/ (run after src/build.py).

    python3 src/web.py NJ

Writes docs/index.html (from src/web_template.html) and docs/data/<STATE>/{bg,sites,towns}.json.
"""
import io, json, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape as shp_shape, mapping

ROOT = Path(__file__).resolve().parents[1]
YEARS = list(range(2015, 2026))
SIMPLIFY = 0.00008   # degrees, about 7-9 m; display only

def _round(o, nd=5):
    if isinstance(o, float): return round(o, nd)
    if isinstance(o, (list, tuple)): return [_round(x, nd) for x in o]
    return o

def bg_geojson(state, bg, towns):
    z = zipfile.ZipFile(ROOT / "data" / "raw" / state / "cb_bg.zip")
    stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")), shx=io.BytesIO(z.read(stem + ".shx")))
    f = [x[0] for x in r.fields[1:]]; iG = f.index("GEOID")
    b = bg.set_index("geoid")
    feats = []
    for sr in r.iterShapeRecords():
        g = sr.record[iG]
        if g not in b.index: continue
        row = b.loc[g]
        if row.pop2020 <= 0: continue
        geom = mapping(shp_shape(sr.shape.__geo_interface__).simplify(SIMPLIFY, preserve_topology=True))
        tn = towns.get(row.town, "") if isinstance(row.town, str) else ""
        feats.append({"type": "Feature", "geometry": {"type": geom["type"], "coordinates": _round(geom["coordinates"])},
                      "properties": {"g": g, "t": tn, "p": int(row.people), "h": int(row.households), "n": int(row.no_vehicle),
                                     "nm": int(round(row.no_vehicle_moe)), "li": None if pd.isna(row.lower_income) else int(row.lower_income),
                                     "b": bool(row.near_border), "w": [None if not np.isfinite(row[f"walk_{y}"]) else int(row[f"walk_{y}"]) for y in YEARS]}})
    return {"type": "FeatureCollection", "features": feats}

def main(state):
    out, docs = ROOT / "out" / state, ROOT / "docs"
    (docs / "data" / state).mkdir(parents=True, exist_ok=True)
    s = json.loads((out / "summary.json").read_text())
    bg = pd.read_csv(out / "bg_access.csv", dtype={"geoid": str, "town": str})
    tw = pd.read_csv(out / "towns.csv", dtype={"town": str, "countyfp": str})
    si = pd.read_csv(out / "sites.csv")
    yr = pd.read_csv(out / "years.csv")
    towns = dict(zip(tw.town, tw.name))
    gj = bg_geojson(state, bg, towns)
    (docs / "data" / state / "bg.json").write_text(json.dumps(gj, separators=(",", ":")))
    act = si[[f"active_{y}" for y in YEARS]].to_numpy()
    keep = act.any(1)
    sites = [[round(r.lon, 5), round(r.lat, 5), str(r["name"]).title(), r.types, int(sum(1 << i for i, a in enumerate(act[k]) if a))]
             for k, (_, r) in enumerate(si.iterrows()) if keep[k]]
    (docs / "data" / state / "sites.json").write_text(json.dumps(sites, separators=(",", ":")))
    t = tw[tw.no_vehicle_hh > 0].copy()
    towns_out = [[r["name"], int(r.no_vehicle_hh), int(r.no_vehicle_hh_beyond_1mi), int(r.people), int(r.people_beyond_1mi), int(r.block_groups_near_border)]
                 for _, r in t.iterrows()]
    page = (ROOT / "src" / "web_template.html").read_text()
    data = {"summary": s, "years": yr.to_dict(orient="list"), "towns": towns_out, "yearList": YEARS, "state": state}
    page = page.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"), default=float))
    (docs / "index.html").write_text(page)
    print(f"site written: {len(gj['features'])} block groups, {len(sites)} sites, "
          f"bg.json {(docs / 'data' / state / 'bg.json').stat().st_size / 1e6:.1f} MB")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "NJ")

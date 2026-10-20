"""Build the static site in docs/ from out/<STATE>/ (run after src/build.py).

    python3 src/web.py            # every state with outputs
    python3 src/web.py NJ

Writes docs/index.html (from src/web_template.html; one page, state picked with ?s=XX) and, per state,
docs/data/<STATE>/{page.json, bg.json, sites.json, alerts.xml}.
"""
import hashlib, io, json, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape as shp_shape, mapping
from build import clean_json

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://sboyapati13.github.io/Food-Desert-Mapper/"
SIMPLIFY = 0.00008   # degrees, about 7-9 m; display only
ORDER = ["NJ", "NY", "PA", "DE"]

def _round(o, nd=5):
    if isinstance(o, float): return round(o, nd)
    if isinstance(o, (list, tuple)): return [_round(x, nd) for x in o]
    return o

def _num(v):
    try:
        return None if v is None or not np.isfinite(float(v)) else int(round(float(v)))
    except (TypeError, ValueError):
        return None

def bg_geojson(state, bg, years):
    z = zipfile.ZipFile(ROOT / "data" / "raw" / state / "cb_bg.zip")
    stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")), shx=io.BytesIO(z.read(stem + ".shx")))
    iG = [x[0] for x in r.fields[1:]].index("GEOID")
    b = bg.set_index("geoid")
    feats = []
    for sr in r.iterShapeRecords():
        g = sr.record[iG]
        if g not in b.index: continue
        row = b.loc[g]
        if row.pop2020 <= 0: continue
        geom = mapping(shp_shape(sr.shape.__geo_interface__).simplify(SIMPLIFY, preserve_topology=True))
        props = {"g": g, "t": row.town if isinstance(row.town, str) else "", "p": _num(row.people), "h": _num(row.households),
                 "n": _num(row.no_vehicle), "nm": _num(row.no_vehicle_moe), "li": None if pd.isna(row.lower_income) else int(row.lower_income),
                 "b": bool(row.near_border), "w": [_num(row[f"walk_{y}"]) for y in years], "x": [_num(row[f"next_{y}"]) for y in years],
                 "s": int(row.nearest_site_latest)}
        if "njeda_fdc" in b.columns: props["f"] = bool(row.njeda_fdc)
        if "risk_next" in b.columns and pd.notna(row.risk_next): props["r"] = round(float(row.risk_next), 4)
        feats.append({"type": "Feature", "geometry": {"type": geom["type"], "coordinates": _round(geom["coordinates"])}, "properties": props})
    return {"type": "FeatureCollection", "features": feats}

def atom(state, name, ev, built):
    """Atom feed of ended authorizations and new ones (replacements left out), newest first."""
    e = ev[ev.kind.isin(["ended", "began"])].sort_values(["to", "only_store_within_1mi_no_vehicle_hh", "brought_within_1mi_no_vehicle_hh"], ascending=False)
    items = []
    for _, r in e.iterrows():
        key = hashlib.sha1(f"{state}|{r.kind}|{r.to}|{r['name']}|{r.lat:.4f}|{r.lon:.4f}".encode()).hexdigest()[:16]
        place = f"{str(r.city).title()}, {r.state}"
        if r.kind == "ended":
            t = f"SNAP authorization ended: {str(r['name']).title()}, {place}"
            body = (f"Between {r['from']} and {r.to}, this full-service site's SNAP authorization ended. It was the only full-service store within a 1-mile walk "
                    f"for {r.only_store_within_1mi_no_vehicle_hh:,} households without a vehicle, and the nearest store for {r.nearest_store_no_vehicle_hh:,}. "
                    "An ended authorization usually, but not always, means the store closed.")
            if isinstance(r.resumed, str) and r.resumed:
                body += f" A new authorization at the same site was open again by {r.resumed}."
        else:
            t = f"New SNAP authorization: {str(r['name']).title()}, {place}"
            body = (f"Between {r['from']} and {r.to}, this full-service site was authorized. It brought {r.brought_within_1mi_no_vehicle_hh:,} households without a vehicle "
                    f"within a 1-mile walk of a full-service store, and is the nearest store for {r.nearest_store_no_vehicle_hh:,}.")
        items.append(f"""  <entry>
    <id>tag:sboyapati13.github.io,2026:food-access/{state}/{key}</id>
    <title>{escape(t)}</title>
    <updated>{r.to}T00:00:00Z</updated>
    <link href="{SITE}?s={state}"/>
    <summary>{escape(body)}</summary>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>tag:sboyapati13.github.io,2026:food-access/{state}</id>
  <title>{escape(name)}: full-service food store SNAP authorizations ended and begun</title>
  <updated>{built}</updated>
  <link href="{SITE}?s={state}"/>
  <link rel="self" href="{SITE}data/{state}/alerts.xml"/>
  <author><name>Food Access Tracker (github.com/SBoyapati13/Food-Desert-Mapper)</name></author>
{chr(10).join(items)}
</feed>
"""

def main(state):
    out, docs = ROOT / "out" / state, ROOT / "docs"
    (docs / "data" / state).mkdir(parents=True, exist_ok=True)
    s = json.loads((out / "summary.json").read_text())
    years = s["years"]
    bg = pd.read_csv(out / "bg_access.csv", dtype={"geoid": str, "town": str})
    tw = pd.read_csv(out / "towns.csv", dtype={"town": str, "countyfp": str})
    si = pd.read_csv(out / "sites.csv")
    yr = pd.read_csv(out / "years.csv")
    ev = pd.read_csv(out / "closures.csv")
    rk = ROOT / "out" / state / "access_risk.csv"
    if rk.exists():
        r = pd.read_csv(rk, dtype={"geoid": str}).set_index("geoid").risk
        bg["risk_next"] = bg.geoid.map(r)
    gj = bg_geojson(state, bg, years)
    (docs / "data" / state / "bg.json").write_text(json.dumps(gj, separators=(",", ":")))
    act = si[[f"active_{y}" for y in years]].to_numpy()
    sites = [[round(r.lon, 5), round(r.lat, 5), str(r["name"]), r.types, int(sum(1 << i for i, a in enumerate(act[k]) if a)), int(r.site)]
             for k, (_, r) in enumerate(si.iterrows()) if act[k].any()]
    (docs / "data" / state / "sites.json").write_text(json.dumps(sites, separators=(",", ":")))
    towns_out = [[r["name"], int(r.no_vehicle_hh), int(r.no_vehicle_hh_beyond_1mi), int(r.people), int(r.people_beyond_1mi),
                  int(r.block_groups_near_border), int(r.no_vehicle_hh_one_store), r.town, r.county] for _, r in tw.iterrows()]
    events = [{"to": r.to, "kind": r.kind, "name": r["name"], "city": r.city, "state": r.state,
               "only": int(r.only_store_within_1mi_no_vehicle_hh), "within": int(r.brought_within_1mi_no_vehicle_hh),
               "nearest": int(r.nearest_store_no_vehicle_hh), "paired": r.paired_with if isinstance(r.paired_with, str) else "",
               "resumed": r.resumed if isinstance(r.resumed, str) else ""} for _, r in ev.iterrows()]
    page = {"summary": s, "years": yr.to_dict(orient="list"), "towns": towns_out, "events": events}
    if "njeda_fdc" in s:
        page["nj"] = {"fdc": s["njeda_fdc"], "housing": s["fourth_round"]}
        hs = ROOT / "out" / state / "fourth_round_sites.json"
        if hs.exists():
            page["nj"]["sites"] = json.loads(hs.read_text())
            sc = pd.read_csv(ROOT / "out" / state / "fourth_round_sites.csv")
            sc = sc[sc.include.astype(str).str.lower().eq("yes") & sc.lat.notna()]
            page["nj"]["site_points"] = [[round(r.lon, 5), round(r.lat, 5), r.town, r.site_name, None if pd.isna(r.affordable_units) else int(r.affordable_units),
                                          round(float(r.walk_m))] for _, r in sc.iterrows()]
    fs, fe = ROOT / "out" / "forecast" / "summary.json", ROOT / "out" / "forecast" / "evaluation.json"
    if fs.exists() and fe.exists():
        F, E = json.loads(fs.read_text()), json.loads(fe.read_text())
        if state in F["states"]:
            page["risk"] = {**F["states"][state], "year": F["forecast_year"], "model": F["chosen_model"],
                            "eval": {m: {k: E["models"][m][k] for k in ("brier", "brier_skill_vs_baseline", "auc")} for m in E["models"]},
                            "neighbourhood": E["neighbourhood_check"], "test_years": E["test_years"]}
    (docs / "data" / state / "page.json").write_text(json.dumps(clean_json(page), separators=(",", ":"), allow_nan=False))
    (docs / "data" / state / "alerts.xml").write_text(atom(state, s["state_name"], ev, s["built_utc"].replace("+00:00", "Z")))
    print(f"{state}: {len(gj['features'])} block groups, {len(sites)} sites, {len(events)} events, "
          f"bg.json {(docs / 'data' / state / 'bg.json').stat().st_size / 1e6:.1f} MB")

def index():
    have = [st for st in ORDER if (ROOT / "out" / st / "summary.json").exists()]
    names = [{"code": st, "name": json.loads((ROOT / "out" / st / "summary.json").read_text())["state_name"]} for st in have]
    page = (ROOT / "src" / "web_template.html").read_text().replace("/*__STATES__*/null", json.dumps(names))
    (ROOT / "docs" / "index.html").write_text(page)

if __name__ == "__main__":
    for st in (sys.argv[1:] or [s for s in ORDER if (ROOT / "out" / s / "summary.json").exists()]):
        main(st)
    index()

"""Fetch new or revised source files for one state.

Large national files are downloaded to data/cache/ (not committed); small state extracts and a
manifest (URL, size, Last-Modified, SHA-256) are written to data/raw/<STATE>/ and committed, so every
run is auditable and a rebuild from the same sources gives the same numbers.

Sources
  SNAP retailers   USDA FNS Historical SNAP Retailer Locator Data (zip, all states)
  ACS 5-year       Census table-based summary files (national .dat per table) -> state block groups
  Centroids        Census 2020 population-weighted block-group centroids (per state)
  Streets          Census TIGER/Line all-lines edges (per county)
  Boundaries       Census cartographic boundary files: block groups, county subdivisions (per state);
                   TIGER/Line state polygons (national, unclipped) for the shared land-and-river border
A failed request keeps the previous copy and never writes an error into a manifest.
"""
import csv, hashlib, io, json, re, sys, time, urllib.error, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
UA = {"User-Agent": "food-desert-mapper (public-data research; github.com/SBoyapati13/Food-Desert-Mapper)"}
SNAP_PAGE = "https://www.fna.usda.gov/snap/retailer-locator/data"
ACS_YEAR = 2024
ACS_BASE = f"https://www2.census.gov/programs-surveys/acs/summary_file/{ACS_YEAR}/table-based-SF/data/5YRData/"
ACS_TABLES = ["b01003", "b25044", "b19013", "c17002"]
TIGER_YEAR = 2024
CENPOP = "https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/CenPop2020_Mean_BG{fips}.txt"
EDGES = f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/EDGES/"
STATES_TL = f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/STATE/tl_{TIGER_YEAR}_us_state.zip"
COUNTIES_TL = f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/COUNTY/tl_{TIGER_YEAR}_us_county.zip"
BG_REL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/blkgrp/tab20_blkgrp20_blkgrp10_natl.txt"
FDC_ITEM = "https://www.arcgis.com/sharing/rest/content/items/5b8fefb3883d41cfa9f51de8e5e61a84?f=json"
FDC_FIELDS = "BG_FIPS,COUNTY,POPULATION,FD_ID,DESERTNAME,FD_SCORE,LOW_ACC_SCR,LMT_SM_AREA"
HOUSING_RAW = "https://raw.githubusercontent.com/SBoyapati13/nj-housing-pace/main/data/raw/dca_final_summary.csv"
HOUSING_COMMIT = "https://api.github.com/repos/SBoyapati13/nj-housing-pace/commits?path=data/raw/dca_final_summary.csv&per_page=1"
BUFFER_KM = 10.0
SNAP_RULE = "v2: state's own records plus records inside buffer counties of other states"
CB = f"https://www2.census.gov/geo/tiger/GENZ{TIGER_YEAR}/shp/cb_{TIGER_YEAR}_{{fips}}_{{layer}}_500k.zip"

def states():
    return json.loads((ROOT / "config" / "states.json").read_text())

# postal code -> FIPS for every state, so store records of any neighbouring state can be recognised
ALL_STATES = {k: {"fips": v} for k, v in zip(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(),
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split())}

def _get(url, method="GET"):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=method), timeout=180)

def _head(url):
    h = _get(url, "HEAD")
    return {"size": h.headers.get("Content-Length"), "last_modified": h.headers.get("Last-Modified")}

def _sha(b): return hashlib.sha256(b).hexdigest()

def _cached(url, name, entry, errors):
    """Download url to data/cache/name when missing or changed upstream. Returns (path, entry, changed)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    try:
        remote = _head(url); time.sleep(0.5)
    except Exception as e:
        errors.append(f"{name}: {e}")
        return (path if path.exists() else None), entry, False
    if entry and entry.get("size") == remote["size"] and entry.get("last_modified") == remote["last_modified"]:
        return (path if path.exists() else None), entry, False      # unchanged upstream; ensure_cache() downloads it if a build needs it
    try:
        data = _get(url).read(); time.sleep(0.5)
    except Exception as e:
        errors.append(f"{name}: {e}")
        return (path if path.exists() else None), entry, False
    path.write_bytes(data)
    if entry and entry.get("sha256") == _sha(data):                    # re-served with new headers, same bytes
        return path, entry, False
    return path, {**remote, "url": url, "sha256": _sha(data),
                  "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}, True

def _cache_name(state, key, e):
    if key == "snap": return "snap_retailers.zip"
    if key.startswith("acs_"): return f"acs{ACS_YEAR}_{key[4:]}.dat"
    if key in ("cenpop", "cb_bg", "cb_cousub"):
        return f"{state}_" + {"cenpop": "cenpop2020_bg.txt", "cb_bg": "cb_bg.zip", "cb_cousub": "cb_cousub.zip"}[key]
    return e["url"].rsplit("/", 1)[-1]

def ensure_cache(state, only=None, files=None):
    """Download any cached source file the manifest lists but data/cache lacks (e.g. on a fresh runner),
    and check it against the recorded SHA-256 so a build never mixes vintages."""
    if files is None:
        files = json.loads((ROOT / "data" / "raw" / state / "manifest.json").read_text())["files"]
    CACHE.mkdir(parents=True, exist_ok=True)
    for key, e in files.items():
        if only and key not in only: continue
        if key in ("njeda_fdc", "fourth_round"): continue                # committed directly, not cached
        path = CACHE / _cache_name(state, key, e)
        if path.exists(): continue
        data = _get(e["url"]).read(); time.sleep(0.5)
        if _sha(data) != e["sha256"]:
            raise RuntimeError(f"{key}: upstream file changed since the last fetch; run fetch.py first")
        path.write_bytes(data)

def _shp(path):
    import shapefile
    z = zipfile.ZipFile(path); stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    return shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")),
                            shx=io.BytesIO(z.read(stem + ".shx")))

def buffer_counties(fips, counties_zip, states_zip):
    """Counties of other states whose boundary is within BUFFER_KM of the state's boundary (CHANGELOG v2, 1).
    Returns {county GEOID: shapely polygon (lon/lat)}."""
    from shapely.geometry import shape
    from shapely import affinity
    from network import deg_m
    r = _shp(states_zip); f = [x[0] for x in r.fields[1:]].index("STATEFP")
    me = next(shape(sr.shape.__geo_interface__) for sr in r.iterShapeRecords() if sr.record[f] == fips)
    kx, ky = deg_m(me.centroid.y)
    mep = affinity.scale(me, xfact=kx, yfact=ky, origin=(0, 0))
    pad = BUFFER_KM * 1000 / ky * 1.5
    x0, y0, x1, y1 = me.bounds
    r = _shp(counties_zip); fl = [x[0] for x in r.fields[1:]]
    iS, iG = fl.index("STATEFP"), fl.index("GEOID")
    out = {}
    for i, rec in enumerate(r.iterRecords(fields=["STATEFP", "GEOID"])):
        if rec[0] == fips: continue
        bx = r.shape(i).bbox
        if bx[2] < x0 - pad * 1.5 or bx[0] > x1 + pad * 1.5 or bx[3] < y0 - pad or bx[1] > y1 + pad: continue
        g = shape(r.shape(i).__geo_interface__)
        if affinity.scale(g, xfact=kx, yfact=ky, origin=(0, 0)).distance(mep) <= BUFFER_KM * 1000:
            out[rec[1]] = g
    return out

def _fdc(out, files, changed, errors):
    """NJEDA/NJDCA Food Desert Communities block groups (attributes only) -> data/raw/NJ/fdc_block_groups.csv."""
    try:
        item = json.loads(_get(FDC_ITEM).read())
        base = item["url"].rstrip("/") + "/1/query"
        rows = []
        for off in range(0, 5000, 1000):
            q = f"{base}?where=1%3D1&outFields={FDC_FIELDS}&returnGeometry=false&resultOffset={off}&resultRecordCount=1000&orderByFields=OBJECTID&f=json"
            feats = json.loads(_get(q).read())["features"]; time.sleep(0.5)
            rows += [ft["attributes"] for ft in feats]
            if len(feats) < 1000: break
        buf = io.StringIO(); w = csv.writer(buf); cols = FDC_FIELDS.split(",")
        w.writerow(cols); [w.writerow([r.get(c) for c in cols]) for r in sorted(rows, key=lambda r: r["BG_FIPS"])]
        data = buf.getvalue().encode()
        e = files.get("njeda_fdc")
        if not e or e["sha256"] != _sha(data) or not (out / "fdc_block_groups.csv").exists():
            (out / "fdc_block_groups.csv").write_bytes(data)
            files["njeda_fdc"] = {"url": item["url"], "item_modified": item.get("modified"), "rows": len(rows), "sha256": _sha(data),
                                  "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            changed.append("njeda_fdc")
    except Exception as e:
        errors.append(f"njeda_fdc: {e}")

def _housing(out, files, changed, errors):
    """Fourth Round prospective need by county subdivision (DCA calculation), from the nj-housing-pace repo."""
    try:
        data = _get(HOUSING_RAW).read()
        try:
            commit = json.loads(_get(HOUSING_COMMIT).read())[0]["sha"]
        except Exception:
            commit = None
        e = files.get("fourth_round")
        if not e or e["sha256"] != _sha(data) or not (out / "fourth_round_obligations.csv").exists():
            (out / "fourth_round_obligations.csv").write_bytes(data)
            files["fourth_round"] = {"url": HOUSING_RAW, "commit": commit, "sha256": _sha(data),
                                     "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            changed.append("fourth_round")
    except Exception as e:
        errors.append(f"fourth_round: {e}")

def snap_url():
    html = _get(SNAP_PAGE).read().decode("utf-8", "replace")
    m = re.search(r'href="([^"]*snap-retailer-locator-data[^"]*\.zip)"', html, re.I)
    if not m:
        raise RuntimeError("SNAP data link not found on the retailer-locator data page")
    href = m.group(1)
    return href if href.startswith("http") else "https://www.fna.usda.gov" + href

def edges_names(fips):
    html = _get(EDGES).read().decode("utf-8", "replace")
    return sorted(set(re.findall(rf"tl_{TIGER_YEAR}_{fips}\d{{3}}_edges\.zip", html)))

def sync(state):
    cfg = states()[state]; fips = cfg["fips"]
    out = ROOT / "data" / "raw" / state; out.mkdir(parents=True, exist_ok=True)
    mpath = out / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"files": {}}
    files, errors, changed = manifest["files"], [], []

    def track(key, url, name):
        p, entry, ch = _cached(url, name, files.get(key), errors)
        if entry: files[key] = entry
        if ch: changed.append(key)
        return p, ch

    # ACS: national tables -> state block-group extracts (committed)
    for t in ACS_TABLES:
        p, ch = track(f"acs_{t}", f"{ACS_BASE}acsdt5y{ACS_YEAR}-{t}.dat", f"acs{ACS_YEAR}_{t}.dat")
        ext = out / f"acs_{t}.csv"
        if p and p.exists() and (ch or not ext.exists()):
            prefixes = (f"1500000US{fips}", f"0400000US{fips}")     # block groups + the state row
            with p.open(encoding="utf-8", errors="replace") as fh, ext.open("w") as w:
                w.write(fh.readline().replace("|", ","))
                for line in fh:
                    if line.startswith(prefixes): w.write(line.replace("|", ","))
    # centroids and boundaries (small; committed as downloaded)
    for key, url, name in [("cenpop", CENPOP.format(fips=fips), "cenpop2020_bg.txt"),
                           ("cb_bg", CB.format(fips=fips, layer="bg"), "cb_bg.zip"),
                           ("cb_cousub", CB.format(fips=fips, layer="cousub"), "cb_cousub.zip")]:
        p, ch = track(key, url, f"{state}_{name}")
        if p and p.exists() and (ch or not (out / name).exists()):
            (out / name).write_bytes(p.read_bytes())
    # state and county polygons (cache only): border flag and the counties across the border (v2)
    track("tl_state", STATES_TL, f"tl_{TIGER_YEAR}_us_state.zip")
    track("tl_county", COUNTIES_TL, f"tl_{TIGER_YEAR}_us_county.zip")
    ensure_cache(state, only=("tl_state", "tl_county"), files=files)
    buf = buffer_counties(fips, CACHE / f"tl_{TIGER_YEAR}_us_county.zip", CACHE / f"tl_{TIGER_YEAR}_us_state.zip")
    rule_changed = manifest.get("buffer_counties") != sorted(buf) or manifest.get("snap_rule") != SNAP_RULE
    manifest["buffer_counties"], manifest["buffer_km"] = sorted(buf), BUFFER_KM
    # SNAP: national zip -> extract of the state's records plus records inside the buffer counties (committed)
    try:
        p, ch = track("snap", snap_url(), "snap_retailers.zip")
    except Exception as e:
        errors.append(f"SNAP page: {e}"); p, ch = (CACHE / "snap_retailers.zip"), False
    ext = out / "snap_retailers.csv"
    if ch or rule_changed or not ext.exists():
        ensure_cache(state, only=("snap",), files=files)
        p = CACHE / "snap_retailers.zip"
        from shapely.geometry import Point
        from shapely.strtree import STRtree
        polys = list(buf.values()); tree = STRtree(polys) if polys else None
        others = {g[:2] for g in buf}
        abbr = {v["fips"]: k for k, v in ALL_STATES.items()}
        other_abbr = {abbr[f] for f in others if f in abbr}
        with zipfile.ZipFile(p) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(name) as fh:
                rdr = csv.reader(io.TextIOWrapper(fh, encoding="latin-1"))
                head = [h.replace("\ufeff", "").replace("ï»¿", "").strip() for h in next(rdr)]
                si, la, lo = head.index("State"), head.index("Latitude"), head.index("Longitude")
                with ext.open("w", newline="") as w:
                    wr = csv.writer(w); wr.writerow(head)
                    for row in rdr:
                        stt = row[si].strip()
                        if stt == state:
                            wr.writerow([c.strip() for c in row]); continue
                        if tree is None or stt not in other_abbr: continue
                        try:
                            pt = Point(float(row[lo]), float(row[la]))
                        except ValueError:
                            continue
                        if len(tree.query(pt, predicate="intersects")):
                            wr.writerow([c.strip() for c in row])
        manifest["snap_rule"] = SNAP_RULE
        if "snap" not in changed: changed.append("snap_extract")
    # streets: one TIGER edges file per county, the state's and the buffer counties' (cache only; hashes in the manifest)
    try:
        names = edges_names(fips) + [f"tl_{TIGER_YEAR}_{g}_edges.zip" for g in sorted(buf)]
        for n in names:
            track(f"edges_{n[8:13]}", EDGES + n, n)
    except Exception as e:
        errors.append(f"TIGER edges index: {e}")
    # New Jersey comparisons (v2, 5)
    if "njeda_fdc" in cfg.get("extras", []):
        _fdc(out, files, changed, errors)
        p, ch = track("bg_rel", BG_REL, "tab20_blkgrp20_blkgrp10_natl.txt")
        rel = out / "bg_rel_2020_2010.csv"
        if ch or not rel.exists():
            ensure_cache(state, only=("bg_rel",), files=files)
            with (CACHE / "tab20_blkgrp20_blkgrp10_natl.txt").open(encoding="utf-8-sig") as fh, rel.open("w") as w:
                head = fh.readline(); w.write(head.replace("|", ","))
                cols = head.strip().split("|"); i20, i10 = cols.index("GEOID_BLKGRP_20"), cols.index("GEOID_BLKGRP_10")
                for line in fh:
                    c = line.split("|")
                    if c[i20].startswith(fips) or c[i10].startswith(fips): w.write(line.replace("|", ","))
    if "fourth_round" in cfg.get("extras", []):
        _housing(out, files, changed, errors)
    manifest["state"], manifest["acs_year"], manifest["tiger_year"] = state, ACS_YEAR, TIGER_YEAR
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return changed, errors

if __name__ == "__main__":
    for st in (sys.argv[1:] or states().keys()):
        ch, err = sync(st)
        print(f"{st}: new or revised {ch or 'none'}" + (f"; problems (previous copies kept): {err}" if err else ""))

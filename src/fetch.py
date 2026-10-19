"""Fetch new or revised source files for one state.

Large national files are downloaded to data/cache/ (not committed); small state extracts and a
manifest (URL, size, Last-Modified, SHA-256) are written to data/raw/<STATE>/ and committed, so every
run is auditable and a rebuild from the same sources gives the same numbers.

Sources
  SNAP retailers   USDA FNS Historical SNAP Retailer Locator Data (zip, all states)
  ACS 5-year       Census table-based summary files (national .dat per table) -> state block groups
  Centroids        Census 2020 population-weighted block-group centroids (per state)
  Streets          Census TIGER/Line all-lines edges (per county)
  Boundaries       Census cartographic boundary files: block groups, county subdivisions (per state)
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
CB = f"https://www2.census.gov/geo/tiger/GENZ{TIGER_YEAR}/shp/cb_{TIGER_YEAR}_{{fips}}_{{layer}}_500k.zip"

def states():
    return json.loads((ROOT / "config" / "states.json").read_text())

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
    if path.exists() and entry and entry.get("size") == remote["size"] and entry.get("last_modified") == remote["last_modified"]:
        return path, entry, False
    try:
        data = _get(url).read(); time.sleep(0.5)
    except Exception as e:
        errors.append(f"{name}: {e}")
        return (path if path.exists() else None), entry, False
    path.write_bytes(data)
    return path, {**remote, "url": url, "sha256": _sha(data),
                  "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}, True

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

    # SNAP: national zip -> state extract (committed)
    try:
        p, ch = track("snap", snap_url(), "snap_retailers.zip")
    except Exception as e:
        errors.append(f"SNAP page: {e}"); p, ch = (CACHE / "snap_retailers.zip"), False
    ext = out / "snap_retailers.csv"
    if p and p.exists() and (ch or not ext.exists()):
        with zipfile.ZipFile(p) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(name) as fh:
                rdr = csv.reader(io.TextIOWrapper(fh, encoding="latin-1"))
                head = [h.replace("﻿", "").replace("ï»¿", "").strip() for h in next(rdr)]
                si = head.index("State")
                with ext.open("w", newline="") as w:
                    wr = csv.writer(w); wr.writerow(head)
                    for row in rdr:
                        if row[si].strip() == state: wr.writerow([c.strip() for c in row])
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
    # streets: one TIGER edges file per county (cache only; hashes in the manifest)
    try:
        for n in edges_names(fips):
            track(f"edges_{n[8:13]}", EDGES + n, n)
    except Exception as e:
        errors.append(f"TIGER edges index: {e}")
    manifest["state"], manifest["acs_year"], manifest["tiger_year"] = state, ACS_YEAR, TIGER_YEAR
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return changed, errors

if __name__ == "__main__":
    for st in (sys.argv[1:] or states().keys()):
        ch, err = sync(st)
        print(f"{st}: new or revised {ch or 'none'}" + (f"; problems (previous copies kept): {err}" if err else ""))

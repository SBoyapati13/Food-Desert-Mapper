"""SNAP retailer records -> full-service store sites (CHANGELOG v1, definitions 1-3; implementation details 1-2)."""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from network import deg_m, haversine

FULL_SERVICE = ["Supermarket", "Super Store", "Large Grocery Store"]
MERGE_M = 50.0

def load(path):
    s = pd.read_csv(path, dtype=str)
    s["lat"] = pd.to_numeric(s.Latitude, errors="coerce")
    s["lon"] = pd.to_numeric(s.Longitude, errors="coerce")
    s["auth"] = pd.to_datetime(s["Authorization Date"], format="%m/%d/%Y", errors="coerce")
    s["end"] = pd.to_datetime(s["End Date"], format="%m/%d/%Y", errors="coerce")
    s["full_service"] = s["Store Type"].isin(FULL_SERVICE)
    s["located"] = s.lat.notna() & s.lon.notna() & (s.lat != 0) & (s.lon != 0)
    return s

def active(s, date):
    date = pd.Timestamp(date)
    return (s.auth <= date) & (s.end.isna() | (s.end > date))

def sites(s):
    """Full-service records with a location, grouped into sites: records within 50 m of each other (chained)
    are one site, by great-circle distance. Returns (records with a 'site' column, one row per site with its median location)."""
    f = s[s.full_service & s.located].copy().reset_index(drop=True)
    kx, ky = deg_m(f.lat.mean())
    xy = np.column_stack([f.lon * kx, f.lat * ky])
    lo, la = f.lon.to_numpy(), f.lat.to_numpy()
    parent = list(range(len(f)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a, b in cKDTree(xy).query_pairs(MERGE_M * 1.05):          # candidates; the rule itself is great-circle
        if haversine(lo[a], la[a], lo[b], la[b]) > MERGE_M: continue
        ra, rb = root(a), root(b)
        if ra != rb: parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([root(i) for i in range(len(f))])
    _, f["site"] = np.unique(roots, return_inverse=True)
    g = f.groupby("site").agg(lon=("lon", "median"), lat=("lat", "median"), records=("Record ID", "count"),
                              name=("Store Name", "last"), city=("City", "last"), county=("County", "last"),
                              types=("Store Type", lambda x: "; ".join(sorted(set(x)))))
    return f, g

def active_sites(f, date):
    return np.unique(f.loc[active(f, date), "site"].to_numpy())

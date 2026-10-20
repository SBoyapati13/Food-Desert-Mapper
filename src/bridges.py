"""v4: bridge walkways (CHANGELOG v4 and its clarifications).

    python3 src/bridges.py      # writes config/walkway_bridges.json

For each candidate with an operator-documented walkway (data/raw/bridges/candidates.json):
  criterion 2: walk between the two landings on the walkable TIGER edges, computed on the edges within
               4 x the straight-line distance of the landings (exact for any walk <= 2 x the straight line);
A bridge is added (v4 amendments 1 and 2, correction 1) when it has a walkway, there is no walking path between
its landings, and both landings are within 300 m of the network. The network adds it as one two-way link between the
landings' nearest network points (network.py); span edges are no longer used.
"""
import glob, heapq, json, math
from pathlib import Path
import numpy as np
from network import WALK, _reader, haversine, deg_m

ROOT = Path(__file__).resolve().parents[1]
UNCLEAR = {"North Grand Island Bridge"}

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def main():
    cand = json.loads((ROOT / "data" / "raw" / "bridges" / "candidates.json").read_text())
    todo = [c for c in cand if c["walkway"] == "yes" and not any(u in c["bridge"] for u in UNCLEAR)]
    boxes = []
    for c in todo:
        a, b = c["end_a"], c["end_b"]
        L = float(haversine(a["lon"], a["lat"], b["lon"], b["lat"]))
        r = 4 * L + 500
        kx, ky = deg_m((a["lat"] + b["lat"]) / 2)
        cx, cy = (a["lon"] + b["lon"]) / 2, (a["lat"] + b["lat"]) / 2
        boxes.append((cx - r / kx, cy - r / ky, cx + r / kx, cy + r / ky, L, kx, ky))
    B = np.array([bx[:4] for bx in boxes])
    kept = {i: [] for i in range(len(todo))}
    seen = set()
    for f in sorted(glob.glob(str(ROOT / "data" / "cache" / "tl_2024_*_edges.zip"))):
        r = _reader(f)
        fl = [x[0] for x in r.fields[1:]]
        iT, iM, iF, iTo = fl.index("TLID"), fl.index("MTFCC"), fl.index("TNIDF"), fl.index("TNIDT")
        for sr in r.iterShapeRecords():
            rec = sr.record
            if not rec[iM].startswith("S") or rec[iT] in seen: continue
            x0, y0, x1, y1 = sr.shape.bbox
            hit = np.flatnonzero((x1 >= B[:, 0]) & (x0 <= B[:, 2]) & (y1 >= B[:, 1]) & (y0 <= B[:, 3]))
            if not len(hit): continue
            seen.add(rec[iT])
            e = (rec[iT], rec[iM], int(rec[iF]), int(rec[iTo]), [tuple(p) for p in sr.shape.points])
            for i in hit: kept[i].append(e)
    out = []
    for i, c in enumerate(todo):
        a, b = c["end_a"], c["end_b"]
        L, kx, ky = boxes[i][4], boxes[i][5], boxes[i][6]
        # local walkable graph on TIGER nodes and shape points
        adj, xy = {}, {}
        def nid(key, p):
            xy.setdefault(key, p); return key
        for tl, m, f, t, pts in kept[i]:
            if m not in WALK: continue
            ids = [("n", f)] + [("p", tl, j) for j in range(1, len(pts) - 1)] + [("n", t)]
            for j, k in enumerate(ids): nid(k, pts[j])
            for u, v in zip(ids[:-1], ids[1:]):
                w = float(haversine(xy[u][0], xy[u][1], xy[v][0], xy[v][1]))
                adj.setdefault(u, []).append((v, w)); adj.setdefault(v, []).append((u, w))
        keys = list(xy); P = np.array([xy[k] for k in keys]) if keys else np.zeros((0, 2))
        def snap(pt):
            d = haversine(pt["lon"], pt["lat"], P[:, 0], P[:, 1]); j = int(np.argmin(d)); return keys[j], float(d[j])
        if len(keys):
            sa, da = snap(a); sb, db = snap(b)
            dist = {sa: 0.0}; pq = [(0.0, sa)]; best = math.inf
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist.get(u, math.inf): continue
                if u == sb: best = d; break
                if d > 2 * L + 2000: break
                for v, w in adj.get(u, []):
                    nd = d + w
                    if nd < dist.get(v, math.inf): dist[v] = nd; heapq.heappush(pq, (nd, v))
            walk = best + da + db
        else:
            walk, da, db = math.inf, None, None
        ratio = walk / L if L > 0 else math.inf
        # v4 amendment: walkable TIGER edge within 100 m of the midpoint of the landing line = a crossing already mapped
        mx, my = (a["lon"] + b["lon"]) / 2 * kx, (a["lat"] + b["lat"]) / 2 * ky
        mid_walk = min((seg_dist(mx, my, p[0] * kx, p[1] * ky, q[0] * kx, q[1] * ky)
                        for tl, m, f, t, pts in kept[i] if m in WALK for p, q in zip(pts[:-1], pts[1:])), default=math.inf)
        fails = (not math.isfinite(walk)) or ratio > 2
        near_net = da is not None and da <= 300 and db <= 300
        # v4 amendment 2: the midpoint check applies only when a walk exists; with no path, any TIGER crossing is unconnected
        mapped = math.isfinite(walk) and mid_walk <= 100
        # v4 correction 1 (after results): only a bridge with no walking path at all is added; every bridge that
        # failed with a finite detour turned out, on tracing the path, to be a crossing TIGER already maps
        added = fails and not math.isfinite(walk) and near_net
        span = []
        out.append({"bridge": c["bridge"], "operator": c["operator"], "crossing": c.get("crossing", ""), "hours": c.get("hours", ""),
                    "end_a": a, "end_b": b, "straight_m": round(L), "tiger_walk_m": None if not math.isfinite(walk) else round(walk),
                    "ratio": None if not math.isfinite(ratio) else round(ratio, 2), "fails_detour_test": fails,
                    "walkable_edge_from_midpoint_m": None if not math.isfinite(mid_walk) else round(mid_walk),
                    "landing_snaps_m": [None if da is None else round(da), None if db is None else round(db)],
                    "added": added, "reason": ("added" if added else "passes the detour test (ratio <= 2)" if not fails
                                               else "walkable crossing already in TIGER near the midpoint" if mapped
                                               else "a walking path exists (v4 correction 1: detour from approximate landings)" if math.isfinite(walk)
                                               else "landing more than 300 m from the network"),
                    "evidence": c["evidence"]})
        print(f"{c['bridge'][:46]:46s} L={L:5.0f} ratio={ratio:6.2f} mid={mid_walk:7.0f} snaps={da if da is None else round(da)}/{db if db is None else round(db)} added={added}")
    (ROOT / "config" / "walkway_bridges.json").write_text(json.dumps(out, indent=1) + "\n")
    print(sum(o["added"] for o in out), "bridges added of", len(out))

if __name__ == "__main__":
    main()

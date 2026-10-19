"""Walking network from Census TIGER/Line edges (CHANGELOG v1, definition 4; implementation details 3-6).

Edges of the walkable feature classes are combined across county files (de-duplicated by TLID), joined
where they share a TIGER node ID, split into pieces of at most 25 m, and treated as two-way. Points are
snapped to the nearest network point in a connected part of the network with at least 200 points.
"""
import io, zipfile
import numpy as np
import shapefile
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

WALK = {"S1200", "S1400", "S1640", "S1710", "S1720", "S1730", "S1740", "S1780", "S1820", "S1830"}
STEP = 25.0               # max piece length, m
MIN_PART = 200            # min points in a connected part used for snapping (about 5 km of streets)
R = 6371008.8             # mean Earth radius, m

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.minimum(a, 1.0)))

def _reader(path):
    z = zipfile.ZipFile(path)
    stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    return shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")),
                            shx=io.BytesIO(z.read(stem + ".shx")))

class Network:
    def __init__(self, edge_zips):
        tnid, lon, lat = {}, [], []
        A, B, seen, self.edges_used, self.length_km = [], [], set(), 0, 0.0

        def node(key, x, y):
            if key is None or key not in tnid:
                i = len(lon); lon.append(x); lat.append(y)
                if key is not None: tnid[key] = i
                return i
            return tnid[key]

        for path in edge_zips:
            r = _reader(path)
            f = [x[0] for x in r.fields[1:]]
            iT, iM, iF, iTo = f.index("TLID"), f.index("MTFCC"), f.index("TNIDF"), f.index("TNIDT")
            for sr in r.iterShapeRecords():
                rec = sr.record
                if rec[iM] not in WALK or rec[iT] in seen: continue
                seen.add(rec[iT]); pts = sr.shape.points
                if len(pts) < 2: continue
                ids = [node(("n", rec[iF]), *pts[0])] + [node(None, *p) for p in pts[1:-1]] + [node(("n", rec[iTo]), *pts[-1])]
                A += ids[:-1]; B += ids[1:]
                self.edges_used += 1
        lon, lat, A, B = np.array(lon), np.array(lat), np.array(A), np.array(B)
        keep = A != B; A, B = A[keep], B[keep]
        L = haversine(lon[A], lat[A], lon[B], lat[B])
        self.length_km = float(L.sum() / 1000)
        # split every segment into k equal pieces of at most STEP metres
        k = np.maximum(1, np.ceil(L / STEP)).astype(np.int64)
        n0, extra = len(lon), int((k - 1).sum())
        first_new = n0 + np.concatenate([[0], np.cumsum(k - 1)[:-1]])          # id of the first new point on each segment
        seg = np.repeat(np.arange(len(k)), k)
        j = np.arange(len(seg)) - np.repeat(np.concatenate([[0], np.cumsum(k)[:-1]]), k)   # piece index within segment
        kk = k[seg]
        start = np.where(j == 0, A[seg], first_new[seg] + j - 1)
        end = np.where(j == kk - 1, B[seg], first_new[seg] + j)
        w = L[seg] / kk
        inner = j > 0                                                          # new points sit at the start of pieces 1..k-1
        new_lon, new_lat = np.empty(extra), np.empty(extra)
        t = j[inner] / kk[inner]; s = seg[inner]
        new_lon[start[inner] - n0] = lon[A[s]] + (lon[B[s]] - lon[A[s]]) * t
        new_lat[start[inner] - n0] = lat[A[s]] + (lat[B[s]] - lat[A[s]]) * t
        self.lon, self.lat = np.concatenate([lon, new_lon]), np.concatenate([lat, new_lat])
        n = len(self.lon)
        # undirected: both directions; parallel edges between the same two points keep the shorter length
        u, v, ww = np.concatenate([start, end]), np.concatenate([end, start]), np.concatenate([w, w])
        order = np.lexsort((ww, v, u)); u, v, ww = u[order], v[order], ww[order]
        first = np.ones(len(u), bool); first[1:] = (u[1:] != u[:-1]) | (v[1:] != v[:-1])
        self.u, self.v, self.w, self.n = u[first], v[first], ww[first], n
        self.G = csr_matrix((self.w, (self.u, self.v)), shape=(n, n))
        ncomp, lab = connected_components(self.G, directed=False)
        size = np.bincount(lab)
        self.parts, self.largest_part_share = int(ncomp), float(size.max() / n)
        self.ok = size[lab] >= MIN_PART
        self.lat0 = float(np.mean(self.lat))
        self._ok_idx = np.flatnonzero(self.ok)
        self._tree = cKDTree(self._xy(self.lon[self._ok_idx], self.lat[self._ok_idx]))

    def _xy(self, lon, lat):
        c = np.cos(np.radians(self.lat0))
        return np.column_stack([np.asarray(lon) * c * 111320.0, np.asarray(lat) * 110574.0])

    def snap(self, lon, lat):
        """Nearest usable network point for each (lon, lat); returns (node index, great-circle snap distance m)."""
        _, i = self._tree.query(self._xy(lon, lat))
        idx = self._ok_idx[i]
        return idx, haversine(np.asarray(lon), np.asarray(lat), self.lon[idx], self.lat[idx])

    def nearest(self, src_nodes, src_offset):
        """Shortest network distance from every point to the nearest source, where reaching a source also
        costs its offset (the store's snap distance). One Dijkstra run from a virtual node."""
        n = self.n
        best = {}
        for a, o in zip(np.asarray(src_nodes).tolist(), np.asarray(src_offset).tolist()):
            if a not in best or o < best[a]: best[a] = o
        sn = np.fromiter(best.keys(), np.int64); so = np.fromiter(best.values(), float) + 1e-6   # 0 would be dropped by sparse
        rows = np.concatenate([self.u, np.full(len(sn), n)])
        cols = np.concatenate([self.v, sn])
        G = csr_matrix((np.concatenate([self.w, so]), (rows, cols)), shape=(n + 1, n + 1))
        return dijkstra(G, directed=True, indices=n)[:n]

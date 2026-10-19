"""Walking network from Census TIGER/Line edges (CHANGELOG v1, definition 4; implementation details 3-6).

Edges of the walkable feature classes are combined across county files (de-duplicated by TLID), joined
where they share a TIGER node ID, split into pieces of at most 25 m, and treated as two-way. Points are
snapped to the nearest network point in a connected part of the network with at least 200 points.
"""
import io, zipfile
from array import array
import numpy as np
import shapefile
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

WALK = {"S1200", "S1400", "S1640", "S1710", "S1720", "S1730", "S1740", "S1780", "S1820", "S1830"}
STEP = 25.0               # max piece length, m
MIN_PART = 200            # min points in a connected part used for snapping (about 5 km of streets)
R = 6371008.8             # mean Earth radius, m

def deg_m(lat):
    """Metres per degree of longitude and of latitude at a latitude (WGS 84 series)."""
    p = np.radians(lat)
    kx = 111412.84 * np.cos(p) - 93.5 * np.cos(3 * p) + 0.118 * np.cos(5 * p)
    ky = 111132.954 - 559.822 * np.cos(2 * p) + 1.175 * np.cos(4 * p)
    return kx, ky

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.minimum(a, 1.0)))

def _reader(path):
    z = zipfile.ZipFile(path)
    stem = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    return shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")),
                            shx=io.BytesIO(z.read(stem + ".shx")))

BIG = 1e15                # weight that switches a source off without changing the graph's structure

class Network:
    def __init__(self, edge_zips):
        tnid = {}
        lon, lat, A, B = array("d"), array("d"), array("q"), array("q")
        seen, self.edges_used = set(), 0

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
                ids = [node(int(rec[iF]), *pts[0])] + [node(None, *p) for p in pts[1:-1]] + [node(int(rec[iTo]), *pts[-1])]
                A.extend(ids[:-1]); B.extend(ids[1:])
                self.edges_used += 1
            del r
        del tnid, seen
        lon, lat = np.frombuffer(lon, float).copy(), np.frombuffer(lat, float).copy()
        A, B = np.frombuffer(A, np.int64).copy(), np.frombuffer(B, np.int64).copy()
        keep = A != B; A, B = A[keep], B[keep]
        L = haversine(lon[A], lat[A], lon[B], lat[B])
        self.length_km = float(L.sum() / 1000)
        k = np.maximum(1, np.ceil(L / STEP)).astype(np.int64)
        # a segment kept whole (k == 1) may duplicate another between the same two points: keep the shorter
        # (the only place parallel edges can occur, since points added by splitting are unique)
        one = k == 1
        a1, b1, l1 = np.minimum(A[one], B[one]), np.maximum(A[one], B[one]), L[one]
        o = np.lexsort((l1, b1, a1)); a1, b1, l1 = a1[o], b1[o], l1[o]
        f1 = np.ones(len(a1), bool); f1[1:] = (a1[1:] != a1[:-1]) | (b1[1:] != b1[:-1])
        a1, b1, l1 = a1[f1], b1[f1], l1[f1]
        del o, f1
        A, B, L, k = A[~one], B[~one], L[~one], k[~one]
        # split every other segment into k equal pieces of at most STEP metres
        n0, extra = len(lon), int((k - 1).sum())
        first_new = n0 + np.concatenate([[0], np.cumsum(k - 1)[:-1]]).astype(np.int64)
        seg = np.repeat(np.arange(len(k)), k)
        j = np.arange(len(seg)) - np.repeat(np.concatenate([[0], np.cumsum(k)[:-1]]), k)
        kk = k[seg]
        start = np.where(j == 0, A[seg], first_new[seg] + j - 1)
        end = np.where(j == kk - 1, B[seg], first_new[seg] + j)
        w = L[seg] / kk
        inner = j > 0
        new_lon, new_lat = np.empty(extra), np.empty(extra)
        t = j[inner] / kk[inner]; s = seg[inner]
        new_lon[start[inner] - n0] = lon[A[s]] + (lon[B[s]] - lon[A[s]]) * t
        new_lat[start[inner] - n0] = lat[A[s]] + (lat[B[s]] - lat[A[s]]) * t
        del seg, j, kk, inner, t, s, first_new, L, k, A, B
        self.lon, self.lat = np.concatenate([lon, new_lon]), np.concatenate([lat, new_lat])
        del lon, lat, new_lon, new_lat
        n = self.n = len(self.lon)
        rows = np.concatenate([start, a1]).astype(np.int32); cols = np.concatenate([end, b1]).astype(np.int32)
        ww = np.concatenate([w, l1])
        del start, end, w, a1, b1, l1
        M = csr_matrix((ww, (rows, cols)), shape=(n, n)); del rows, cols, ww
        self.G = (M + M.T).tocsr(); del M                # each unordered pair appears once, so the sum is a union
        self.G.indices = self.G.indices.astype(np.int32); self.G.indptr = self.G.indptr.astype(np.int32)
        ncomp, lab = connected_components(self.G, directed=False)
        size = np.bincount(lab)
        self.parts, self.largest_part_share = int(ncomp), float(size.max() / n)
        self.part, self.largest_part = lab.astype(np.int32), int(np.argmax(size))
        self.ok = size[lab] >= MIN_PART
        del lab
        self.lat0 = float(np.mean(self.lat))
        self._ok_idx = np.flatnonzero(self.ok)
        self._tree = cKDTree(self._xy(self.lon[self._ok_idx], self.lat[self._ok_idx]))
        self._src = None

    def _xy(self, lon, lat):
        kx, ky = deg_m(self.lat0)
        return np.column_stack([np.asarray(lon) * kx, np.asarray(lat) * ky])

    def snap(self, lon, lat):
        """Nearest usable network point for each (lon, lat); returns (node index, great-circle snap distance m)."""
        _, i = self._tree.query(self._xy(lon, lat))
        idx = self._ok_idx[i]
        return idx, haversine(np.asarray(lon), np.asarray(lat), self.lon[idx], self.lat[idx])

    def attach_sources(self, nodes):
        """Add a virtual node (index n) with an edge to every network point a store can snap to; each run of
        nearest() then sets those edges' weights. Frees the snapping index, which is no longer needed."""
        self._tree = None; self._ok_idx = None
        n = self.n
        u = np.unique(np.asarray(nodes)).astype(np.int32)
        G = self.G
        indptr = np.append(G.indptr, G.indptr[-1] + len(u)).astype(np.int32)
        self.G = csr_matrix((np.concatenate([G.data, np.full(len(u), BIG)]), np.concatenate([G.indices, u]), indptr), shape=(n + 1, n + 1))
        del G
        self._src = pd_index(u, np.arange(indptr[-2], indptr[-1]))

    def nearest(self, src_nodes, src_offset, with_source=False):
        """Shortest network distance from every point to the nearest source, where reaching a source also
        costs its offset (the store's snap distance). One Dijkstra run from the virtual node. With with_source,
        also returns, for every point, the source point its shortest path starts from (-1 if unreachable)."""
        n = self.n
        best = {}
        for a, o in zip(np.asarray(src_nodes).tolist(), np.asarray(src_offset).tolist()):
            if a not in best or o < best[a]: best[a] = o
        pos_of = self._src
        data = self.G.data
        data[pos_of["pos"]] = BIG
        sn = np.fromiter(best.keys(), np.int64); so = np.fromiter(best.values(), float) + 1e-6
        data[pos_of["pos"][np.searchsorted(pos_of["node"], sn)]] = so
        if not with_source:
            D = dijkstra(self.G, directed=True, indices=n)[:n]
            D[D >= BIG / 10] = np.inf
            return D
        D, pred = dijkstra(self.G, directed=True, indices=n, return_predecessors=True)
        D, pred = D[:n], pred[:n]
        bad = D >= BIG / 10
        D[bad] = np.inf
        idx = np.arange(n, dtype=pred.dtype)
        up = np.where(pred == n, idx, pred)
        unreached = (pred < 0) | bad
        up[unreached] = idx[unreached]
        while True:
            nxt = up[up]
            if np.array_equal(nxt, up): break
            up = nxt
        up[unreached] = -1
        return D, up

    def within(self, node, limit):
        """Network points within `limit` metres of one point: (point indices, distances)."""
        d = dijkstra(self.G, directed=True, indices=node, limit=limit)[:self.n]    # G holds both directions
        hit = np.flatnonzero(d <= limit)
        return hit, d[hit]

def pd_index(nodes, pos):
    return {"node": np.asarray(nodes), "pos": np.asarray(pos)}

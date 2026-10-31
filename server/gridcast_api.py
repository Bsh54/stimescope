import csv
import gzip
import json
import math
import os
import shutil
import struct
import urllib.parse
import urllib.request
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

BASE = os.environ.get("GRIDCAST_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TILES_DIR = os.path.join(BASE, "tiles")
INDEX_DIR = os.path.join(BASE, "index")
TILES_GEOJSON = os.path.join(BASE, "tiles.geojson")
POINTS_URL = "https://storage.googleapis.com/open-buildings-data/v3/points_s2_level_4_gzip/{id}_buildings.csv.gz"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MIN_AREA, MIN_CONF, LARGE_AREA = 15.0, 0.7, 400.0
HH_SHARE = 0.90
CELL = 0.1

app = FastAPI(title="stimescope building-count API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
_tiles = []
os.makedirs(INDEX_DIR, exist_ok=True)


@app.on_event("startup")
def _load_tiles():
    with open(TILES_GEOJSON) as f:
        gj = json.load(f)
    for ft in gj["features"]:
        g = ft["geometry"]
        ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
        xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
        _tiles.append((ft["properties"]["tile_id"], ring, min(xs), max(xs), min(ys), max(ys)))


def _point_in_ring(lat, lon, ring):
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]
        if ((y1 > lat) != (y2 > lat)) and (lon < (x2 - x1) * (lat - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside


def _resolve_tile(lat, lon):
    for tid, ring, x0, x1, y0, y1 in _tiles:
        if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_ring(lat, lon, ring):
            return tid
    return None


def _ensure_tile(tile_id):
    path = os.path.join(TILES_DIR, tile_id + "_buildings.csv.gz")
    if not os.path.exists(path):
        req = urllib.request.Request(POINTS_URL.format(id=tile_id), headers={"User-Agent": "stimescope/0.1"})
        tmp = path + ".part"
        with urllib.request.urlopen(req, timeout=900) as r, open(tmp, "wb") as out:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                out.write(b)
        os.rename(tmp, path)
    return path


def _cell(lat, lon):
    return "%d_%d" % (math.floor(lat / CELL), math.floor(lon / CELL))


def build_index(tile_id):
    # One-time: bucket confident footprints into 0.1deg cell files of packed (lat,lon,area) float32.
    done = os.path.join(INDEX_DIR, tile_id, ".done")
    if os.path.exists(done):
        return
    gz = _ensure_tile(tile_id)
    tmp = os.path.join(INDEX_DIR, tile_id + ".building")
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    buffers = {}; buffered = 0

    def flush():
        for cell, buf in buffers.items():
            with open(os.path.join(tmp, cell), "ab") as f:
                f.write(buf)
        buffers.clear()

    with gzip.open(gz, "rt") as fh:
        r = csv.reader(fh); next(r, None)
        for row in r:
            try:
                lat = float(row[0]); lon = float(row[1]); area = float(row[2]); conf = float(row[3])
            except (ValueError, IndexError):
                continue
            if conf < MIN_CONF or area < MIN_AREA:
                continue
            cell = _cell(lat, lon)
            b = buffers.get(cell)
            if b is None:
                b = buffers[cell] = bytearray()
            b += struct.pack("<fff", lat, lon, area)
            buffered += 12
            if buffered > 150_000_000:
                flush(); buffered = 0
    flush()
    final = os.path.join(INDEX_DIR, tile_id)
    shutil.rmtree(final, ignore_errors=True)
    os.rename(tmp, final)
    open(done, "w").close()


def query_index(tile_id, lat, lon, radius_m):
    outdir = os.path.join(INDEX_DIR, tile_id)
    lat_pad = radius_m / 110540.0
    lon_pad = radius_m / (111320.0 * math.cos(math.radians(lat)))
    mlon = 111320.0 * math.cos(math.radians(lat))
    i0 = math.floor((lat - lat_pad) / CELL); i1 = math.floor((lat + lat_pad) / CELL)
    j0 = math.floor((lon - lon_pad) / CELL); j1 = math.floor((lon + lon_pad) / CELL)
    total = large = 0
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            p = os.path.join(outdir, "%d_%d" % (i, j))
            try:
                with open(p, "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                continue
            for k in range(0, len(data), 12):
                la, lo, area = struct.unpack_from("<fff", data, k)
                if math.hypot((lo - lon) * mlon, (la - lat) * 110540.0) <= radius_m:
                    total += 1
                    if area >= LARGE_AREA:
                        large += 1
    return total, large


ANCHOR_TAGS = ['nwr["amenity"~"hospital|clinic|doctors|health_post|school|college|university|marketplace|fuel"]',
               'nwr["man_made"~"works|water_well|water_tower|communications_tower|mast|tower"]',
               'nwr["tower:type"="communication"]', 'nwr["building"~"industrial|warehouse"]',
               'nwr["craft"~"grain_mill|sawmill"]']


def _osm_count(selector):
    a = "".join(t + selector for t in ANCHOR_TAGS)
    q = "[out:json][timeout:20];(%s)->.a;.a out count;" % a
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": "stimescope/0.1 (research)"})
    try:
        with urllib.request.urlopen(req, timeout=22) as r:
            res = json.load(r)
        counts = [int(e["tags"]["total"]) for e in res["elements"] if e.get("type") == "count"]
        return counts[0], 0
    except Exception:
        return 0, 0


def _osm_anchors(lat, lon, radius_m):
    return _osm_count("(around:%d,%f,%f);" % (radius_m, lat, lon))


def _osm_anchors_bbox(s, w, n, e):
    return _osm_count("(%f,%f,%f,%f);" % (s, w, n, e))


def _osm_anchors_poly(poly):
    return _osm_count('(poly:"%s");' % " ".join("%f %f" % (la, lo) for la, lo in poly))


def _in_poly(lat, lon, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        la1, lo1 = poly[i]; la2, lo2 = poly[(i + 1) % n]
        if ((la1 > lat) != (la2 > lat)) and (lon < (lo2 - lo1) * (lat - la1) / (la2 - la1 + 1e-12) + lo1):
            inside = not inside
    return inside


def query_polygon(tile_id, poly):
    outdir = os.path.join(INDEX_DIR, tile_id)
    lats = [p[0] for p in poly]; lons = [p[1] for p in poly]
    s, n, w, e = min(lats), max(lats), min(lons), max(lons)
    i0 = math.floor(s / CELL); i1 = math.floor(n / CELL)
    j0 = math.floor(w / CELL); j1 = math.floor(e / CELL)
    total = large = 0
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            try:
                with open(os.path.join(outdir, "%d_%d" % (i, j)), "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                continue
            for k in range(0, len(data), 12):
                la, lo, area = struct.unpack_from("<fff", data, k)
                if s <= la <= n and w <= lo <= e and _in_poly(la, lo, poly):
                    total += 1
                    if area >= LARGE_AREA:
                        large += 1
    return total, large


def query_bbox(tile_id, s, w, n, e):
    outdir = os.path.join(INDEX_DIR, tile_id)
    i0 = math.floor(s / CELL); i1 = math.floor(n / CELL)
    j0 = math.floor(w / CELL); j1 = math.floor(e / CELL)
    total = large = 0
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            try:
                with open(os.path.join(outdir, "%d_%d" % (i, j)), "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                continue
            for k in range(0, len(data), 12):
                la, lo, area = struct.unpack_from("<fff", data, k)
                if s <= la <= n and w <= lo <= e:
                    total += 1
                    if area >= LARGE_AREA:
                        large += 1
    return total, large


@app.get("/health")
def health():
    return {"ok": True, "tiles_loaded": len(_tiles), "indexed": len([d for d in os.listdir(INDEX_DIR) if os.path.exists(os.path.join(INDEX_DIR, d, ".done"))])}


def _pack(buildings, large, osm_anchor, osm_buildings, extra):
    # Large footprints (>=400 m2) are a per-site satellite signal for productive/anchor loads.
    anchor = max(osm_anchor, large)
    ordinary = max(buildings - anchor, 0)
    out = {"buildings": buildings, "large": large, "osm_anchor": osm_anchor, "osm_buildings": osm_buildings,
           "counts": {"household": round(ordinary * HH_SHARE), "commercial": round(ordinary * (1 - HH_SHARE)), "anchor": anchor},
           "source": "open_buildings"}
    out.update(extra)
    return out


@app.get("/count")
def count(lat: float = Query(None), lon: float = Query(None), radius: int = Query(2000, ge=200, le=5000),
          minlat: float = Query(None), minlon: float = Query(None), maxlat: float = Query(None), maxlon: float = Query(None)):
    if None not in (minlat, minlon, maxlat, maxlon):
        s, n = sorted((minlat, maxlat)); w, e = sorted((minlon, maxlon))
        tile_id = _resolve_tile((s + n) / 2, (w + e) / 2)
        if tile_id is None:
            return {"error": "no Open Buildings tile covers this area", "bbox": [s, w, n, e]}
        build_index(tile_id)
        buildings, large = query_bbox(tile_id, s, w, n, e)
        anchor, osm_buildings = _osm_anchors_bbox(s, w, n, e)
        return _pack(buildings, large, anchor, osm_buildings, {"lat": (s + n) / 2, "lon": (w + e) / 2, "bbox": [s, w, n, e], "tile": tile_id})
    if lat is None or lon is None:
        return {"error": "provide lat/lon or a bounding box (minlat/minlon/maxlat/maxlon)"}
    tile_id = _resolve_tile(lat, lon)
    if tile_id is None:
        return {"error": "no Open Buildings tile covers this point", "lat": lat, "lon": lon}
    build_index(tile_id)
    buildings, large = query_index(tile_id, lat, lon, radius)
    anchor, osm_buildings = _osm_anchors(lat, lon, radius)
    return _pack(buildings, large, anchor, osm_buildings, {"lat": lat, "lon": lon, "radius_m": radius, "tile": tile_id})


def _poly_from_body(body):
    try:
        poly = [(float(p[0]), float(p[1])) for p in body.get("polygon", [])]
    except (TypeError, ValueError, IndexError):
        return None
    return poly if len(poly) >= 3 else None


@app.post("/count_polygon")
async def count_polygon(req: Request):
    poly = _poly_from_body(await req.json())
    if poly is None:
        return {"error": "need at least 3 polygon points as [lat, lon] pairs"}
    with_anchors = req.query_params.get("anchors", "1") != "0"
    clat = sum(p[0] for p in poly) / len(poly)
    clon = sum(p[1] for p in poly) / len(poly)
    tile_id = _resolve_tile(clat, clon)
    if tile_id is None:
        return {"error": "no Open Buildings tile covers this area"}
    build_index(tile_id)
    buildings, large = query_polygon(tile_id, poly)
    anchor, osm_buildings = _osm_anchors_poly(poly) if with_anchors else (0, 0)
    return _pack(buildings, large, anchor, osm_buildings, {"lat": clat, "lon": clon, "tile": tile_id, "points": len(poly)})


@app.post("/anchors_polygon")
async def anchors_polygon(req: Request):
    poly = _poly_from_body(await req.json())
    if poly is None:
        return {"error": "need at least 3 polygon points as [lat, lon] pairs"}
    anchor, osm_buildings = _osm_anchors_poly(poly)
    return {"anchor": anchor, "osm_buildings": osm_buildings}

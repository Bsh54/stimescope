import math
from pathlib import Path

import numpy as np
import pandas as pd

from .geo import _overpass_counts

HOUSEHOLD_SHARE = 0.90
COMMERCIAL_SHARE = 0.10
LARGE_AREA_M2 = 400.0


def _scan(csv_gz_path: Path, lat: float, lon: float, radius_m: int,
          min_area: float = 15.0, min_confidence: float = 0.7) -> tuple[int, int]:
    # Stream the tile once; return (confident footprints in radius, large structures >= LARGE_AREA).
    lat_pad = radius_m / 110540.0
    lon_pad = radius_m / (111320.0 * math.cos(math.radians(lat)))
    total = large = 0
    for chunk in pd.read_csv(csv_gz_path, compression="gzip", chunksize=500_000,
                             usecols=["latitude", "longitude", "area_in_meters", "confidence"]):
        near = chunk[(chunk["confidence"] >= min_confidence) & (chunk["area_in_meters"] >= min_area)
                     & chunk["latitude"].between(lat - lat_pad, lat + lat_pad)
                     & chunk["longitude"].between(lon - lon_pad, lon + lon_pad)]
        if near.empty:
            continue
        dx = (near["longitude"] - lon) * 111320.0 * math.cos(math.radians(lat))
        dy = (near["latitude"] - lat) * 110540.0
        inside = near[np.hypot(dx, dy) <= radius_m]
        total += len(inside)
        large += int((inside["area_in_meters"] >= LARGE_AREA_M2).sum())
    return total, large


def count_buildings(csv_gz_path: Path, lat: float, lon: float, radius_m: int = 2000) -> int:
    return _scan(csv_gz_path, lat, lon, radius_m)[0]


def segment_counts(csv_gz_path: Path, lat: float, lon: float, radius_m: int = 2000,
                   commercial_share: float = COMMERCIAL_SHARE) -> tuple[dict, int, int, int]:
    # The business share is driven by the local economy (2-25% by count across our validated sites:
    # Sitolo 2%, Tum 9%, Omorate 25%), not by footprint size -- so it is an adjustable input, with
    # OSM anchors and the large-structure count as priors rather than a definitive count from above.
    buildings, large = _scan(csv_gz_path, lat, lon, radius_m)
    osm_buildings, _, anchor = _overpass_counts(lat, lon, radius_m)
    ordinary = max(buildings - anchor, 0)
    counts = {
        "household": round(ordinary * (1.0 - commercial_share)),
        "commercial": round(ordinary * commercial_share),
        "anchor": anchor,
    }
    return counts, buildings, large, osm_buildings

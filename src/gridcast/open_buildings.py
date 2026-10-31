import math
from pathlib import Path

import numpy as np
import pandas as pd

from .geo import _overpass_counts

HOUSEHOLD_SHARE = 0.90
COMMERCIAL_SHARE = 0.10


def count_buildings(csv_gz_path: Path, lat: float, lon: float, radius_m: int = 2000,
                    min_area: float = 15.0, min_confidence: float = 0.7) -> int:
    # Count confident Open Buildings footprints (>= min_area) within the radius, streaming the tile.
    lat_pad = radius_m / 110540.0
    lon_pad = radius_m / (111320.0 * math.cos(math.radians(lat)))
    total = 0
    for chunk in pd.read_csv(csv_gz_path, compression="gzip", chunksize=500_000,
                             usecols=["latitude", "longitude", "area_in_meters", "confidence"]):
        near = chunk[(chunk["confidence"] >= min_confidence) & (chunk["area_in_meters"] >= min_area)
                     & chunk["latitude"].between(lat - lat_pad, lat + lat_pad)
                     & chunk["longitude"].between(lon - lon_pad, lon + lon_pad)]
        if near.empty:
            continue
        dx = (near["longitude"] - lon) * 111320.0 * math.cos(math.radians(lat))
        dy = (near["latitude"] - lat) * 110540.0
        total += int((np.hypot(dx, dy) <= radius_m).sum())
    return total


def segment_counts(csv_gz_path: Path, lat: float, lon: float, radius_m: int = 2000) -> tuple[dict, int]:
    # Buildings split into households + commercial by sector share; anchors from OSM points of interest.
    buildings = count_buildings(csv_gz_path, lat, lon, radius_m)
    _, _, anchor = _overpass_counts(lat, lon, radius_m)
    counts = {
        "household": round(buildings * HOUSEHOLD_SHARE),
        "commercial": round(buildings * COMMERCIAL_SHARE),
        "anchor": anchor,
    }
    return counts, buildings

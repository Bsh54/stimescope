import math
from pathlib import Path

import numpy as np
import pandas as pd


def rwi_at(csv_path: Path, lat: float, lon: float, radius_km: float = 8.0) -> tuple[float, int]:
    # Mean Relative Wealth Index (Meta Data for Good) of the ~2.4 km grid cells within the radius.
    d = pd.read_csv(csv_path, usecols=["latitude", "longitude", "rwi"])
    dx = (d["longitude"] - lon) * 111.32 * math.cos(math.radians(lat))
    dy = (d["latitude"] - lat) * 110.54
    near = d[np.hypot(dx, dy) <= radius_km]
    return (float(near["rwi"].mean()), len(near)) if len(near) else (float("nan"), 0)

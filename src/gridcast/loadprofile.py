import numpy as np

# Normalized 24 h shapes (local time, index = hour). Commercial/anchor shape is MEASURED from
# A2EI inverter-output telemetry (82 systems). Household shape is NREL's "all households" rural
# Sub-Saharan Africa profile (Microgrid Load Profile Explorer, OEDI); its load factor (~0.24) is a
# property of that real profile, not a tuned target.
A2EI_COMMERCIAL = np.array([
    0.227, 0.193, 0.176, 0.165, 0.123, 0.122, 0.132, 0.227, 0.457, 0.678, 0.807, 0.934,
    0.998, 1.000, 0.995, 0.985, 0.916, 0.864, 0.844, 0.903, 0.867, 0.709, 0.468, 0.293])
HOUSEHOLD = np.array([
    0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.070, 0.070, 0.207, 0.207, 0.207, 0.228,
    0.126, 0.126, 0.126, 0.074, 0.074, 0.234, 0.365, 0.673, 1.000, 0.939, 0.481, 0.124])

SEGMENT_SHAPES = {"household": HOUSEHOLD, "commercial": A2EI_COMMERCIAL, "anchor": A2EI_COMMERCIAL}


def site_hourly_kwh(segment_energy_kwh: dict) -> np.ndarray:
    hourly = np.zeros(24)
    for segment, energy in segment_energy_kwh.items():
        shape = SEGMENT_SHAPES[segment]
        hourly += energy * shape / shape.sum()
    return hourly


def profile_metrics(segment_energy_kwh: dict) -> dict:
    hourly = site_hourly_kwh(segment_energy_kwh)
    peak_kw = float(hourly.max())
    mean_kw = float(hourly.mean())
    return {"hourly_kwh": hourly, "peak_kw": peak_kw,
            "load_factor": mean_kw / peak_kw if peak_kw else 0.0,
            "peak_hour": int(hourly.argmax())}

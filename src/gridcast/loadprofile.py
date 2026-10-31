import numpy as np

# Normalized 24 h shapes (local time, index = hour). Commercial/anchor shape is measured
# from A2EI telemetry (82 systems); household shape is the rural evening-peak pattern
# reported by Blodgett 2017, Hartvigsson 2018 and MDPI RESILIENT (minimal at night, small
# morning bump, low midday, strong evening peak ~19h).
A2EI_COMMERCIAL = np.array([
    0.227, 0.193, 0.176, 0.165, 0.123, 0.122, 0.132, 0.227, 0.457, 0.678, 0.807, 0.934,
    0.998, 1.000, 0.995, 0.985, 0.916, 0.864, 0.844, 0.903, 0.867, 0.709, 0.468, 0.293])
HOUSEHOLD = np.array([
    0.06, 0.05, 0.05, 0.05, 0.05, 0.07, 0.14, 0.20, 0.14, 0.10, 0.08, 0.08,
    0.08, 0.08, 0.10, 0.12, 0.22, 0.45, 0.80, 1.00, 0.90, 0.60, 0.30, 0.12])

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

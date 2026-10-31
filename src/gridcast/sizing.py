import numpy as np

from .loadprofile import site_hourly_kwh

SOLAR_HOURS = range(7, 17)


def size_system(segment_energy_kwh: dict, peak_sun_hours: float = 5.3,
                performance_ratio: float = 0.75, depth_of_discharge: float = 0.8) -> dict:
    # First-order PV + battery sizing: PV covers daily energy at the site's peak-sun-hours;
    # the battery stores the energy consumed outside solar hours (evening/night load).
    hourly = site_hourly_kwh(segment_energy_kwh)
    daily = float(hourly.sum())
    peak_kw = float(hourly.max())
    off_solar = float(sum(hourly[h] for h in range(24) if h not in SOLAR_HOURS))

    return {
        "peak_kw": round(peak_kw, 1),
        "load_factor": round(hourly.mean() / peak_kw, 3) if peak_kw else 0.0,
        "daily_energy_kwh": round(daily, 1),
        "pv_kwp": round(daily / (peak_sun_hours * performance_ratio), 1),
        "battery_kwh": round(off_solar / depth_of_discharge, 1),
    }

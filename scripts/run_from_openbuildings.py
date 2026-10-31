from pathlib import Path

from gridcast.confidence import confidence
from gridcast.estimate import estimate_site_demand, segment_medians
from gridcast.loadprofile import profile_metrics
from gridcast.open_buildings import segment_counts
from gridcast.sizing import size_system

TILE = Path("data/open_buildings/103_points.csv.gz")


def run(lat: float, lon: float, name: str, radius: int = 2500) -> None:
    counts, buildings, large, osm_buildings = segment_counts(TILE, lat, lon, radius)
    demand = estimate_site_demand(counts)
    connected = 0.7 * (counts["household"] + counts["commercial"]) + counts["anchor"]
    per_customer = demand[0.5] / max(connected, 1)
    conf = confidence(buildings, "open_buildings", counts["anchor"], per_customer, large, osm_buildings)
    daily = {s: e / 30.4 for s, e in segment_medians(counts).items()}
    system = size_system(daily)

    print(f"{name} ({lat}, {lon}, {radius} m)")
    print(f"  Open Buildings = {buildings}  ({large} large structures)  ->  {counts}")
    print(f"  demand  P10={demand[0.1]:,.0f}  P50={demand[0.5]:,.0f}  P90={demand[0.9]:,.0f} kWh/month")
    print(f"  ~{per_customer:.0f} kWh/customer/month   confidence: {conf['level']} ({conf['score']}) -- {conf['reasons'][0]}")
    print(f"  system  peak {system['peak_kw']} kW  PV {system['pv_kwp']} kWp  battery {system['battery_kwh']} kWh\n")


def main() -> None:
    run(6.980, 2.665, "Pobe (town)")
    run(7.080, 2.665, "Rural point where OSM returned 0 buildings")


if __name__ == "__main__":
    main()

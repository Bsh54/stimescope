from pathlib import Path

from gridcast.estimate import estimate_site_demand
from gridcast.open_buildings import segment_counts

TILE = Path("data/open_buildings/103_points.csv.gz")


def run(lat: float, lon: float, name: str, radius: int = 2500) -> None:
    counts, buildings = segment_counts(TILE, lat, lon, radius)
    demand = estimate_site_demand(counts)
    connected = 0.7 * (counts["household"] + counts["commercial"]) + counts["anchor"]
    print(f"{name} ({lat}, {lon}, {radius} m)")
    print(f"  Open Buildings = {buildings}  ->  {counts}")
    print(f"  demand  P10={demand[0.1]:,.0f}  P50={demand[0.5]:,.0f}  P90={demand[0.9]:,.0f} kWh/month")
    print(f"  ~{demand[0.5] / max(connected, 1):.0f} kWh/customer/month\n")


def main() -> None:
    run(6.980, 2.665, "Pobe (town)")
    run(7.080, 2.665, "Rural point where OSM returned 0 buildings")


if __name__ == "__main__":
    main()

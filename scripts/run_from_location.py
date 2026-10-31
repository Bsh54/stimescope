from pathlib import Path

from gridcast.estimate import estimate_site_demand
from gridcast.geo import segment_counts_from_osm
from gridcast.growth import load_growth_curve, project_demand

CURVE = Path("src/gridcast/growth_curve.csv")


def main() -> None:
    lat, lon, name, radius = 6.980, 2.665, "Pobe, Benin", 3000
    counts, n_buildings = segment_counts_from_osm(lat, lon, radius)
    print(f"{name} ({lat}, {lon}, {radius} m)")
    print(f"OSM buildings={n_buildings}  ->  segments={counts}")

    mature = estimate_site_demand(counts)
    print(f"\nMature site demand  P10={mature[0.1]:,.0f}  P50={mature[0.5]:,.0f}  "
          f"P90={mature[0.9]:,.0f} kWh/month")

    projection = project_demand(mature, load_growth_curve(CURVE)).round(0).astype(int)
    projection.columns = ["P10", "P50", "P90"]
    print("\nRamp-up after connection (kWh/month):")
    print(projection.to_string())


if __name__ == "__main__":
    main()

from pathlib import Path

from gridcast.growth import growth_curve, project_demand

LOGS = Path("data/a2ei_skgs/A2EI_SKGS_data_release_April2022/skgs_data_LOGS_2021_82_systems.csv")


def main() -> None:
    curve = growth_curve(LOGS)
    print("Demand growth since connection (real A2EI telemetry, 82 systems):")
    print(curve.to_string())

    mature = {0.1: 38600, 0.5: 47900, 0.9: 92500}
    print("\nProjected site demand ramp-up (kWh/month) for a mature P50=47,900 site:")
    projection = project_demand(mature, curve).round(0).astype(int)
    projection.columns = ["P10", "P50", "P90"]
    print(projection.to_string())


if __name__ == "__main__":
    main()

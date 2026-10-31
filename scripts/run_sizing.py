from gridcast.estimate import estimate_site_demand, segment_medians
from gridcast.loadprofile import profile_metrics
from gridcast.sizing import size_system


def main() -> None:
    village = {"household": 150, "commercial": 20, "anchor": 2}
    demand = estimate_site_demand(village)
    monthly = segment_medians(village)
    daily = {s: e / 30.4 for s, e in monthly.items()}

    metrics = profile_metrics(daily)
    system = size_system(daily)

    print(f"Village {village}, mature P50 = {demand[0.5]:,.0f} kWh/month")
    print(f"\nLoad profile: peak {system['peak_kw']} kW at {metrics['peak_hour']}h, "
          f"load factor {system['load_factor']} (household-only ~0.22, rises with productive use)")
    print(f"System sizing (5.3 peak-sun-hours, PR 0.75, DoD 0.8):")
    print(f"  PV      {system['pv_kwp']} kWp")
    print(f"  battery {system['battery_kwh']} kWh")
    print(f"  daily energy {system['daily_energy_kwh']} kWh")

    hourly = metrics["hourly_kwh"]
    print("\n24 h load shape (kWh/h):")
    print("  " + " ".join(f"{h:02d}" for h in range(24)))
    print("  " + " ".join(f"{v:02.0f}" for v in hourly))


if __name__ == "__main__":
    main()

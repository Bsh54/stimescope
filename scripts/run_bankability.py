from gridcast.bankability import bankability
from gridcast.estimate import estimate_site_demand


def main() -> None:
    village = {"household": 150, "commercial": 20, "anchor": 2}
    demand = estimate_site_demand(village)
    irr, floor = bankability(demand)

    print(f"Village {village}, system sized to P50 = {demand[0.5]:,.0f} kWh/month")
    for q in (0.1, 0.5, 0.9):
        print(f"  if actual demand = P{int(q * 100):02d} ({demand[q]:,.0f} kWh/mo)  ->  IRR {irr[q]:.1f}%")
    print(f"\nViability floor (IRR >= 6%): {floor:,.0f} kWh/month "
          f"= {100 * floor / demand[0.5]:.0f}% of the P50 forecast.")
    print("Below that, the project does not clear a 6% IRR.")


if __name__ == "__main__":
    main()

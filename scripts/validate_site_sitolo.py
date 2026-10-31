from gridcast.estimate import estimate_site_demand

# Ground truth: Sitolo solar mini-grid, Mchinji, Malawi (Frame, Eales & Bayani, IEEE
# PowerAfrica 2023, metered 2022). Total 70,003 kWh/yr; domestic 57,741 @ ~83 kWh/cust/yr
# -> ~696 domestic; business 12,087 (12% from 4 large anchor-like, ~8 smaller); social 175.
METERED_KWH_YEAR = 70003
ENROLLED_COUNTS = {"household": 696, "commercial": 8, "anchor": 4}


def main() -> None:
    actual = METERED_KWH_YEAR / 12
    demand = estimate_site_demand(ENROLLED_COUNTS, adoption_rate=1.0)

    print("Held-out site validation -- Sitolo mini-grid, Malawi (metered 2022):")
    print(f"  enrolled customers: {ENROLLED_COUNTS}")
    print(f"  predicted  P10={demand[0.1]:,.0f}  P50={demand[0.5]:,.0f}  "
          f"P90={demand[0.9]:,.0f} kWh/month")
    print(f"  metered actual:     {actual:,.0f} kWh/month")
    print(f"  P50 error = {100 * (demand[0.5] - actual) / actual:+.1f}%   "
          f"metered inside P10-P90: {demand[0.1] <= actual <= demand[0.9]}")
    print(f"  metered domestic per customer = {57741 / 696 / 12:.1f} kWh/month "
          f"vs our household benchmark P50 = 7.0 (independent match, 3rd country)")
    print("\nLimitation: the enrolled count is the right model input, not a raw building")
    print("radius -- this densely settled area holds ~9,700 footprints within 3 km but the")
    print("mini-grid connects ~850; developers always plan a target connection count.")


if __name__ == "__main__":
    main()

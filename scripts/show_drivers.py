from pathlib import Path

from gridcast.data import load_stevanato
from gridcast.explain import driver_importance

DATA = Path("data/stevanato_appliances/Database_ready_v2.csv")


def main() -> None:
    X, y, _ = load_stevanato(DATA)
    drivers = driver_importance(X, y)
    print("Top drivers of predicted monthly electricity demand:")
    print(drivers.to_string(index=False))


if __name__ == "__main__":
    main()

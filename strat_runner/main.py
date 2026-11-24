import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from researches import grid_eur_usd


def main() -> None:
    grid_eur_usd.run()


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from researches import grid


def main() -> None:
    grid.run()


if __name__ == "__main__":
    main()

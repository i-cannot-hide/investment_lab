from pathlib import Path

from engine import Experiment, Research
from strategies.grid import GridStrategy


def run() -> str:
    """Run a GridStrategy experiment. Returns its research id."""
    research = Research(
        name="Grid",
        experiments=[
            Experiment(
                GridStrategy(
                    min_price=100,
                    max_price=400,
                    num_of_lines=4,
                    ticker="EUR",
                ),
                name="grid",
            ),
        ],
    )

    strat_runner_dir = Path(__file__).resolve().parent.parent
    data_dir = strat_runner_dir / "data" / "preprocessed"
    data_files = sorted(
        str(path.relative_to(strat_runner_dir)) for path in data_dir.glob("SPX.csv")
    )

    if not data_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    research_id = research.run(
        data_files,
        full_debug_outcomes=False,
        initial_usd=10_000,
    )
    print(f"Research finished: {research.name} ({research_id})")
    return research_id

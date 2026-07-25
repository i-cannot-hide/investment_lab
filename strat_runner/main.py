from pathlib import Path

from engine import Experiment, MoneySpawner, Research, SpawnInterval, Staker
from strategies.do_nothing import DoNothingStrategy
from strategies.hold import HoldStrategy
from strategies.invest_everything import InvestEverythingStrategy
from strategies.buy_below import BuyBelowStrategy


research = Research(
    name="Investing at ATH",
    experiments=[
        Experiment(
            strategy=DoNothingStrategy(),
            name="do-nothing",
        ),
        Experiment(
            strategy=DoNothingStrategy(),
            name="do-nothing_with_salary",
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
            ],
        ),
        Experiment(HoldStrategy("SPX"),
            name="hold_spx",
        ),
        Experiment(HoldStrategy("SPX"),
            name="hold_spx_with_salary",
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
            ],
        ),
        Experiment(InvestEverythingStrategy("SPX"),
            name="invest_everything_spx"
        ),
        Experiment(InvestEverythingStrategy("SPX"),
            name="invest_everything_spx_with_salary",
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
            ],
        ),
    ],
)

data_dir = Path(__file__).parent / "data" / "preprocessed"
data_files = sorted(str(path.relative_to(Path(__file__).parent)) for path in data_dir.glob("SPX.csv"))

if not data_files:
    raise FileNotFoundError(f"No CSV files found in {data_dir}")

research_id = research.run(
    data_files,
    full_debug_outcomes=False,
    start_date="1980-02-20",
    end_date="2024-12-31",
    initial_usd=10_000,
)
print(f"Research finished: {research.name} ({research_id})")

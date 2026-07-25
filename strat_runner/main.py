from pathlib import Path
from decimal import Decimal

from engine import Experiment, Research
from indicators import IsAth
from modifiers import MoneySpawner, SpawnInterval, Staker
from strategies.do_nothing import DoNothingStrategy
from strategies.hold import HoldStrategy
from strategies.invest_everything import InvestEverythingStrategy
from strategies.buy_when_ath import BuyWhenAthStrategy

ath_drop = 0.1

research = Research(
    name="Investing at ATH",
    experiments=[
        Experiment(
            InvestEverythingStrategy("SPX"),
            name="invest_salary",
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
            ],
        ),
        Experiment(
            BuyWhenAthStrategy("SPX", should_buy=False),
            name="skip_ath_staking",
            indicators=[IsAth(ticker="SPX", acceptable_drop=ath_drop)],
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
                Staker("USD", rate=Decimal(0.004), interval=SpawnInterval.MONTH)
            ],
        ),
        Experiment(
            BuyWhenAthStrategy("SPX"),
            name="buy_ath_staking",
            indicators=[IsAth(ticker="SPX", acceptable_drop=ath_drop)],
            modifiers=[
                MoneySpawner(
                    currency="USD",
                    amount=1000,
                    interval=SpawnInterval.MONTH,
                ),
                Staker("USD", rate=Decimal(0.004), interval=SpawnInterval.MONTH)
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
    #start_date="1980-02-20",
    #end_date="2024-12-31",
    initial_usd=10_000,
)
print(f"Research finished: {research.name} ({research_id})")

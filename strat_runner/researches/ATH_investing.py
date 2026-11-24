from decimal import Decimal
from pathlib import Path

from engine import Experiment, Research
from indicators import IsAth
from modifiers import ActionInterval, MoneySpawner, Staker
from strategies.buy_when_ath import BuyWhenAthStrategy
from strategies.invest_everything import InvestEverythingStrategy


def run() -> str:
    """Run the Investing at ATH batch. Returns its research id."""
    ath_drop = 0.2

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
                        interval=ActionInterval.MONTH,
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
                        interval=ActionInterval.MONTH,
                    ),
                    Staker("USD", rate=Decimal("0.004"), interval=ActionInterval.MONTH),
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
                        interval=ActionInterval.MONTH,
                    ),
                    Staker("USD", rate=Decimal("0.004"), interval=ActionInterval.MONTH),
                ],
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
        # start_date="2020-02-01",
        # end_date="2024-12-31",
        initial_usd=10_000,
    )
    print(f"Research finished: {research.name} ({research_id})")
    return research_id

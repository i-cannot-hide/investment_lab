from pathlib import Path

from engine import Environment, Experiment, MoneySpawner, SpawnInterval
from executors.mock_executor import MockExecutor
from strategies.hold import HoldStrategy
from strategies.buy_below import BuyBelowStrategy


experiments = [
    Experiment(
        strategy=HoldStrategy(ticker="BTC"),
        name="hold",
    ),
    Experiment(
        strategy=BuyBelowStrategy(target_price=20000, ticker="BTC"),
        name="buybelow",
    ),
    Experiment(
        strategy=BuyBelowStrategy(target_price=20000, ticker="BTC"),
        money_spawner=MoneySpawner(
            currency="USD",
            amount=1000,
            interval=SpawnInterval.MONTH,
        ),
        name="buybelow+spawn",
    ),
]

data_dir = Path(__file__).parent / "data" / "preprocessed"
data_files = sorted(str(path.relative_to(Path(__file__).parent)) for path in data_dir.glob("*.csv"))

if not data_files:
    raise FileNotFoundError(f"No CSV files found in {data_dir}")

for experiment in experiments:
    environment = Environment(
        experiment,
        MockExecutor(),
        data_files,
        full_debug_outcomes=False,
        start_date="2023-01-01",
        end_date="2024-12-31",
    )
    environment.run()
    print(f"Finished {experiment.name or type(experiment.strategy).__name__}")

print("Simulation finished")

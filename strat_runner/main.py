from environment import Environment
from executors.mock_executor import MockExecutor
from strategies.hold import HoldStrategy


strategy = HoldStrategy()

mock_executor = MockExecutor()

environment = Environment(
    strategy,
    mock_executor,
    "data/btc.csv"
)

environment.run()

print("Simulation finished")
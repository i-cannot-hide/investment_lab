import csv
from datetime import datetime
from decimal import Decimal

from models import Candle, Account, Context
from recorder import Recorder


class Environment:

    def __init__(
        self,
        strategy,
        mock_executor,
        data_file: str
    ):
        self.strategy = strategy
        self.mock_executor = mock_executor
        self.data_file = data_file

        self.account = Account(
            balances={
                "USD": Decimal("10000")
            }
        )

        self.positions = []

        self.recorder = Recorder(
            "runs/run_001"
        )


    def load_candles(self):
        candles = []

        with open(self.data_file) as f:
            reader = csv.DictReader(f)

            for row in reader:
                candles.append(
                    Candle(
                        time=datetime.fromisoformat(row["time"]),
                        ticker=row["ticker"],
                        open=Decimal(row["open"]),
                        high=Decimal(row["high"]),
                        low=Decimal(row["low"]),
                        close=Decimal(row["close"]),
                        volume=Decimal(row["volume"]),
                    )
                )

        return candles


    def run(self):
        candles = self.load_candles()

        history = []

        for step, candle in enumerate(candles):

            history.append(candle)

            context = Context(
                time=candle.time,
                candles=history.copy(),
                account=self.account,
                positions=self.positions,
                open_orders=[]
            )

            snapshot_path = self.recorder.save_snapshot(
                step,
                context
            )

            orders = self.strategy.decide(context)

            self.recorder.record_event(
                "STRATEGY_DECISION",
                {
                    "orders": str(orders),
                    "source_snapshot": str(snapshot_path),
                }
            )

            self.mock_executor.execute(
                orders,
                self.account,
                self.positions,
                {
                    candle.ticker: candle.close
                }
            )
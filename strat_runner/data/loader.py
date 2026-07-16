import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from models import Candle


def load_candles(data_file: Path | str) -> list[Candle]:
    candles = []

    with open(data_file) as f:
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

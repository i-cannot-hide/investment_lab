import time
from pathlib import Path

import pandas as pd
import requests


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_KLINES_LIMIT = 1000
DEFAULT_DATA_DIR = Path(__file__).parent / "raw"

DEFAULT_COINS = [
    "BTC", "ETH", "BNB", "SOL", "PAXG",
    "XRP", "ADA", "DOGE", "TRX", "AAVE",
    "SHIB", "AVAX", "DOT", "LINK", "HBAR",
    "BCH", "NEAR", "MATIC", "LTC", "POL",
    "UNI", "ZEC", "XLM", "SUI", "TAO",
    "ATOM", "ARB",
]


def _fetch_klines(symbol: str, interval: str, start_ms: int) -> list:
    all_rows = []
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "limit": BINANCE_KLINES_LIMIT,
        }
        response = requests.get(BINANCE_KLINES_URL, params=params, timeout=10)
        response.raise_for_status()
        rows = response.json()

        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < BINANCE_KLINES_LIMIT:
            break

        start_ms = rows[-1][0] + 1
        time.sleep(0.1)

    return all_rows


def _klines_to_dataframe(rows: list) -> pd.DataFrame:
    columns = [
        "Open time", "Open", "High", "Low", "Close", "Volume",
        "Close time", "Quote asset volume", "Number of trades",
        "Taker buy base volume", "Taker buy quote volume", "Ignore",
    ]
    df = pd.DataFrame(rows, columns=columns)
    df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
    df.set_index("Open time", inplace=True)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col])
    return df[["Open", "High", "Low", "Close", "Volume"]]


def download_prices(
    coins: list[str] | None = None,
    interval: str = "1d",
    folder: Path | str | None = None,
    start_date: str = "2020-01-01",
) -> None:
    coins = coins or DEFAULT_COINS
    out_dir = Path(folder) if folder is not None else DEFAULT_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)

    print(
        f"Downloading {len(coins)} coins from Binance "
        f"(interval={interval}, start={start_date}, folder={out_dir})..."
    )
    for coin in coins:
        symbol = f"{coin}USDT"
        try:
            rows = _fetch_klines(symbol, interval, start_ms)
            if rows:
                df = _klines_to_dataframe(rows)
                filepath = out_dir / f"{coin}.csv"
                df.to_csv(filepath)
                print(f"  -> Saved {filepath} ({len(df)} rows)")
            else:
                print(f"  -> No data found for {symbol}")
        except requests.HTTPError as e:
            print(f"  -> HTTP error for {symbol}: {e}")
        except Exception as e:
            print(f"  -> Error downloading {symbol}: {e}")

    print("Download complete.")

from pathlib import Path

import pandas as pd
import yfinance as yf


DEFAULT_DATA_DIR = Path(__file__).parent / "raw"

# Tradable S&P 500 proxy (Yahoo symbol == local ticker filename stem).
DEFAULT_TICKERS = ["SPY"]

# Friendly aliases -> Yahoo Finance symbol (file saved under the alias / mapped stem).
_YAHOO_SYMBOLS = {
    "SPY": "SPY",
    "SPX": "^GSPC",
    "GSPC": "^GSPC",
    "SNP500": "^GSPC",
    "^GSPC": "^GSPC",
}

_FILE_STEM = {
    "^GSPC": "SPX",
    "GSPC": "SPX",
    "SNP500": "SPX",
}


def _yahoo_symbol(ticker: str) -> str:
    key = ticker.strip().upper()
    if key in _YAHOO_SYMBOLS:
        return _YAHOO_SYMBOLS[key]
    return ticker.strip()


def _file_stem(ticker: str) -> str:
    key = ticker.strip().upper()
    return _FILE_STEM.get(key, key.lstrip("^"))


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Match Binance raw CSV shape: Open-time index + Open/High/Low/Close/Volume."""
    if df.empty:
        return df

    frame = df.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        # yfinance may return (Price, Ticker) columns for a single symbol.
        if "Close" in frame.columns.get_level_values(0):
            frame.columns = frame.columns.get_level_values(0)
        else:
            frame.columns = frame.columns.get_level_values(-1)

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Yahoo response missing columns: {missing}")

    out = frame[required].copy()
    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out.index = pd.to_datetime(out.index)
    out.index.name = "Open time"
    return out.dropna(how="any")


def download_prices(
    tickers: list[str] | None = None,
    interval: str = "1mo",
    folder: Path | str | None = None,
    start_date: str = "2020-01-01",
    end_date: str | None = None,
) -> None:
    """Download Yahoo Finance OHLCV into the same raw CSV layout as Binance.

    Default interval is monthly (``1mo``) for S&P 500-style research.
    Files are written under ``data/raw/{STEM}.csv`` so
    ``preprocessor.preprocess_and_save`` works unchanged.
    """
    tickers = tickers or DEFAULT_TICKERS
    out_dir = Path(folder) if folder is not None else DEFAULT_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if interval != "1mo":
        raise ValueError(
            f"yahoo_downloader only supports monthly bars (interval='1mo'), got {interval!r}"
        )

    print(
        f"Downloading {len(tickers)} tickers from Yahoo "
        f"(interval={interval}, start={start_date}, folder={out_dir})..."
    )
    for ticker in tickers:
        symbol = _yahoo_symbol(ticker)
        stem = _file_stem(ticker)
        try:
            raw = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False,
                progress=False,
            )
            if raw is None or raw.empty:
                print(f"  -> No data found for {symbol}")
                continue

            df = _normalize_ohlcv(raw)
            filepath = out_dir / f"{stem}.csv"
            df.to_csv(filepath)
            print(f"  -> Saved {filepath} ({len(df)} rows) [{symbol}]")
        except Exception as e:
            print(f"  -> Error downloading {symbol}: {e}")

    print("Download complete.")

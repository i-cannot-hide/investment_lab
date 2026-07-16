from pathlib import Path

import pandas as pd

from data.reader import read_raw


PREPROCESSED_DIR = Path(__file__).parent / "preprocessed"


def preprocess(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "time": pd.to_datetime(df.index).strftime("%Y-%m-%d"),
            "ticker": ticker.upper(),
            "open": df["Open"].astype(float),
            "high": df["High"].astype(float),
            "low": df["Low"].astype(float),
            "close": df["Close"].astype(float),
            "volume": df["Volume"].astype(float),
        }
    )
    return out.dropna().reset_index(drop=True)


def preprocess_and_save(
    tickers: str | list[str],
    raw_folder: Path | str | None = None,
    out_folder: Path | str | None = None,
) -> list[Path]:
    if isinstance(tickers, str):
        tickers = [tickers]

    out_dir = Path(out_folder) if out_folder is not None else PREPROCESSED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    out_paths = []
    for ticker in tickers:
        raw = read_raw(ticker, raw_folder)
        processed = preprocess(raw, ticker)

        out_path = out_dir / f"{ticker.lower()}.csv"
        processed.to_csv(out_path, index=False)
        print(f"Saved {out_path} ({len(processed)} rows)")
        out_paths.append(out_path)

    return out_paths

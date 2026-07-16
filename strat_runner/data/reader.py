from pathlib import Path

import pandas as pd


RAW_DIR = Path(__file__).parent / "raw"


def read_raw(ticker: str = "BTC", folder: Path | str | None = None) -> pd.DataFrame:
    folder = Path(folder) if folder is not None else RAW_DIR
    path = _resolve_csv_path(folder, ticker)

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "Open time"

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    return df[list(required)]


def read_all_raw(folder: Path | str | None = None) -> dict[str, pd.DataFrame]:
    folder = Path(folder) if folder is not None else RAW_DIR
    if not folder.exists():
        print(f"No raw folder found at '{folder}'.")
        return {}

    data = {}
    for path in sorted(folder.glob("*.csv")):
        ticker = path.stem.upper()
        try:
            data[ticker] = read_raw(ticker, folder)
        except Exception as e:
            print(f"Error reading {path.name}: {e}")

    if not data:
        print(f"No CSV files found in '{folder}'.")

    return data


def _resolve_csv_path(folder: Path, ticker: str) -> Path:
    candidates = [
        folder / f"{ticker.upper()}.csv",
        folder / f"{ticker.lower()}.csv",
        folder / f"{ticker}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"No raw CSV found for {ticker!r} in {folder} "
        f"(tried: {', '.join(p.name for p in candidates)})"
    )

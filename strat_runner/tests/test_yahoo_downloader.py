from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from data.yahoo_downloader import (
    _file_stem,
    _normalize_ohlcv,
    _yahoo_symbol,
    download_prices,
)


def test_symbol_and_stem_aliases():
    assert _yahoo_symbol("SPY") == "SPY"
    assert _yahoo_symbol("snp500") == "^GSPC"
    assert _yahoo_symbol("SPX") == "^GSPC"
    assert _file_stem("SNP500") == "SPX"
    assert _file_stem("SPY") == "SPY"
    assert _file_stem("^GSPC") == "SPX"


def test_normalize_ohlcv_matches_binance_shape():
    idx = pd.to_datetime(["2021-01-01", "2021-02-01"])
    raw = pd.DataFrame(
        {
            "Open": [100.0, 110.0],
            "High": [120.0, 130.0],
            "Low": [90.0, 100.0],
            "Close": [115.0, 125.0],
            "Volume": [1_000.0, 2_000.0],
            "Adj Close": [115.0, 125.0],
        },
        index=idx,
    )
    out = _normalize_ohlcv(raw)
    assert list(out.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert out.index.name == "Open time"
    assert len(out) == 2


def test_normalize_ohlcv_flattens_multiindex_columns():
    idx = pd.to_datetime(["2021-01-01"])
    raw = pd.DataFrame(
        {
            ("Open", "SPY"): [100.0],
            ("High", "SPY"): [110.0],
            ("Low", "SPY"): [90.0],
            ("Close", "SPY"): [105.0],
            ("Volume", "SPY"): [1_000.0],
        },
        index=idx,
    )
    raw.columns = pd.MultiIndex.from_tuples(raw.columns)
    out = _normalize_ohlcv(raw)
    assert list(out.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_rejects_non_monthly_interval():
    with pytest.raises(ValueError, match="1mo"):
        download_prices(tickers=["SPY"], interval="1d")


def test_download_prices_writes_raw_csv(tmp_path: Path):
    idx = pd.to_datetime(["2021-01-01", "2021-02-01"])
    fake = pd.DataFrame(
        {
            "Open": [100.0, 110.0],
            "High": [120.0, 130.0],
            "Low": [90.0, 100.0],
            "Close": [115.0, 125.0],
            "Adj Close": [115.0, 125.0],
            "Volume": [1_000.0, 2_000.0],
        },
        index=idx,
    )

    with patch("data.yahoo_downloader.yf.download", return_value=fake) as mocked:
        download_prices(
            tickers=["SPY"],
            interval="1mo",
            folder=tmp_path,
            start_date="2021-01-01",
        )

    mocked.assert_called_once()
    assert mocked.call_args.kwargs["interval"] == "1mo"
    path = tmp_path / "SPY.csv"
    assert path.exists()

    loaded = pd.read_csv(path, index_col=0, parse_dates=True)
    assert list(loaded.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(loaded) == 2

    # Preprocessor path works unchanged.
    from data.preprocessor import preprocess_and_save

    out_paths = preprocess_and_save("SPY", raw_folder=tmp_path, out_folder=tmp_path / "out")
    processed = pd.read_csv(out_paths[0])
    assert list(processed.columns) == [
        "time",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert processed["ticker"].iloc[0] == "SPY"


def test_snp500_alias_saves_as_spx(tmp_path: Path):
    idx = pd.to_datetime(["2021-01-01"])
    fake = pd.DataFrame(
        {
            "Open": [3800.0],
            "High": [3900.0],
            "Low": [3700.0],
            "Close": [3850.0],
            "Adj Close": [3850.0],
            "Volume": [0.0],
        },
        index=idx,
    )
    with patch("data.yahoo_downloader.yf.download", return_value=fake) as mocked:
        download_prices(tickers=["SNP500"], folder=tmp_path, start_date="2021-01-01")

    assert mocked.call_args.args[0] == "^GSPC"
    assert (tmp_path / "SPX.csv").exists()

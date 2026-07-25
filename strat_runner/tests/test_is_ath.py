from datetime import datetime
from decimal import Decimal

import pytest

from engine import IndicatorContext, IsAth
from engine.journal import EntryType
from models import Candle


def _ctx(
    high: str,
    *,
    low: str | None = None,
    ticker: str = "SPX",
) -> IndicatorContext:
    high_d = Decimal(high)
    low_d = Decimal(low) if low is not None else high_d
    candle = Candle(
        time=datetime(2020, 1, 1),
        ticker=ticker,
        open=high_d,
        high=high_d,
        low=low_d,
        close=high_d,
        volume=Decimal("0"),
    )
    return IndicatorContext(
        time=candle.time,
        bar_candles={ticker: candle},
        history={},
        is_last_bar=False,
    )


def test_rejects_empty_ticker():
    with pytest.raises(ValueError, match="ticker"):
        IsAth(ticker="")


def test_rejects_invalid_acceptable_drop():
    with pytest.raises(ValueError, match="acceptable_drop"):
        IsAth(ticker="SPX", acceptable_drop="-0.01")
    with pytest.raises(ValueError, match="acceptable_drop"):
        IsAth(ticker="SPX", acceptable_drop="1")


def test_first_bar_is_ath_and_sets_peak():
    marker = IsAth(ticker="SPX", acceptable_drop="0.02")
    entries = marker.update(_ctx("100"))
    assert marker.is_ath is True
    assert entries == [
        {
            "type": EntryType.IS_ATH.value,
            "ticker": "SPX",
            "IsATH": True,
            "high": "100",
            "peak": "100",
            "acceptable_drop": "0.02",
        }
    ]


def test_acceptable_drop_band_uses_low():
    marker = IsAth(ticker="SPX", acceptable_drop="0.02")
    marker.update(_ctx("100"))

    # high in band but low below threshold → not ATH
    dipped = marker.update(_ctx("98", low="97"))
    assert marker.is_ath is False
    assert dipped[0]["IsATH"] is False
    assert dipped[0]["peak"] == "100"

    near = marker.update(_ctx("99", low="98"))
    assert marker.is_ath is True
    assert near[0]["IsATH"] is True
    assert near[0]["peak"] == "100"

    below = marker.update(_ctx("98", low="97.99"))
    assert marker.is_ath is False
    assert below[0]["IsATH"] is False
    assert below[0]["peak"] == "100"


def test_new_high_updates_peak():
    marker = IsAth(ticker="SPX", acceptable_drop="0.04")
    marker.update(_ctx("100"))
    marker.update(_ctx("110"))

    near_new_peak = marker.update(_ctx("105.6"))
    assert marker.is_ath is True
    assert near_new_peak[0]["IsATH"] is True
    assert near_new_peak[0]["peak"] == "110"

    below_new_peak = marker.update(_ctx("105.5"))
    assert marker.is_ath is False
    assert below_new_peak[0]["IsATH"] is False


def test_skips_missing_ticker():
    marker = IsAth(ticker="SPX")
    ctx = _ctx("100", ticker="BTC")
    assert marker.update(ctx) == []
    assert marker.is_ath is None


def test_registry_record():
    marker = IsAth(ticker="SPX", acceptable_drop="0.02")
    assert marker.registry_record() == {
        "type": "IsAth",
        "ticker": "SPX",
        "acceptable_drop": "0.02",
    }

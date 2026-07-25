from datetime import datetime
from decimal import Decimal

import pytest

from engine import IsAth, ModifierContext
from engine.journal import EntryType
from models import Account, Candle


def _ctx(high: str, *, ticker: str = "SPX") -> ModifierContext:
    candle = Candle(
        time=datetime(2020, 1, 1),
        ticker=ticker,
        open=Decimal(high),
        high=Decimal(high),
        low=Decimal(high),
        close=Decimal(high),
        volume=Decimal("0"),
    )
    return ModifierContext(
        time=candle.time,
        account=Account(balances={"USD": Decimal("0")}),
        positions=[],
        open_orders=[],
        bar_candles={ticker: candle},
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
    entries = marker.on_bar_end(_ctx("100"))
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


def test_acceptable_drop_band():
    marker = IsAth(ticker="SPX", acceptable_drop="0.02")
    marker.on_bar_end(_ctx("100"))

    near = marker.on_bar_end(_ctx("98"))
    assert near[0]["IsATH"] is True
    assert near[0]["peak"] == "100"

    below = marker.on_bar_end(_ctx("97.99"))
    assert below[0]["IsATH"] is False
    assert below[0]["peak"] == "100"


def test_new_high_updates_peak():
    marker = IsAth(ticker="SPX", acceptable_drop="0.04")
    marker.on_bar_end(_ctx("100"))
    marker.on_bar_end(_ctx("110"))

    near_new_peak = marker.on_bar_end(_ctx("105.6"))
    assert near_new_peak[0]["IsATH"] is True
    assert near_new_peak[0]["peak"] == "110"

    below_new_peak = marker.on_bar_end(_ctx("105.5"))
    assert below_new_peak[0]["IsATH"] is False


def test_skips_missing_ticker():
    marker = IsAth(ticker="SPX")
    ctx = _ctx("100", ticker="BTC")
    assert marker.on_bar_end(ctx) == []


def test_registry_record():
    marker = IsAth(ticker="SPX", acceptable_drop="0.02")
    assert marker.registry_record() == {
        "type": "IsAth",
        "ticker": "SPX",
        "acceptable_drop": "0.02",
    }

from datetime import datetime
from decimal import Decimal

import pytest

from indicators import IsAth
from models import Account, Context, OrderSide, OrderType
from strategies.buy_when_ath import BuyWhenAthStrategy, MIN_USD


def make_context(
    *,
    usd="10000",
    open_price="25000",
    indicators: list | None = None,
):
    return Context(
        time=datetime(2021, 1, 1),
        history={},
        current_open_prices={"BTC": Decimal(str(open_price))},
        account=Account(balances={"USD": Decimal(usd)}),
        positions=[],
        indicators=indicators or [],
    )


def _ath(*, is_ath: bool | None, ticker: str = "BTC") -> IsAth:
    indicator = IsAth(ticker=ticker, acceptable_drop="0.02")
    indicator.is_ath = is_ath
    return indicator


def test_raises_without_is_ath_indicator():
    strategy = BuyWhenAthStrategy()
    with pytest.raises(ValueError, match="requires an IsAth indicator"):
        strategy.decide(make_context())


def test_raises_when_is_ath_value_missing():
    strategy = BuyWhenAthStrategy()
    with pytest.raises(ValueError, match="has no value"):
        strategy.decide(make_context(indicators=[_ath(is_ath=None)]))


def test_returns_none_when_not_ath():
    strategy = BuyWhenAthStrategy()
    assert strategy.decide(make_context(indicators=[_ath(is_ath=False)])) is None


def test_buys_market_when_ath():
    strategy = BuyWhenAthStrategy()
    decision = strategy.decide(make_context(indicators=[_ath(is_ath=True)]))
    assert decision is not None
    assert len(decision.orders) == 1
    order = decision.orders[0]
    assert order.side == OrderSide.BUY
    assert order.order_type == OrderType.MARKET
    assert order.total_value == Decimal("10000")


def test_returns_none_when_below_min_usd_even_if_ath():
    strategy = BuyWhenAthStrategy()
    just_below = MIN_USD - Decimal("0.01")
    assert (
        strategy.decide(
            make_context(usd=str(just_below), indicators=[_ath(is_ath=True)])
        )
        is None
    )

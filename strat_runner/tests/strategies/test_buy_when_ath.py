from datetime import datetime
from decimal import Decimal

import pytest

from indicators import IsAth
from models import Account, Context, Order, OrderSide, OrderType
from strategies.buy_when_ath import BuyWhenAthStrategy, MIN_USD


def make_context(
    *,
    usd="10000",
    open_price="25000",
    indicators: list | None = None,
    open_prices: dict[str, Decimal] | None = None,
    open_orders: list[Order] | None = None,
):
    if open_prices is not None:
        price_map = open_prices
    else:
        price_map = {"BTC": Decimal(str(open_price))}

    return Context(
        time=datetime(2021, 1, 1),
        history={},
        current_open_prices=price_map,
        account=Account(balances={"USD": Decimal(usd)}),
        positions=[],
        open_orders=open_orders or [],
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


def test_raises_when_is_ath_for_other_ticker_only():
    strategy = BuyWhenAthStrategy(ticker="BTC")
    with pytest.raises(ValueError, match="requires an IsAth indicator"):
        strategy.decide(make_context(indicators=[_ath(is_ath=True, ticker="ETH")]))


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
    assert order.ticker == "BTC"
    assert order.side == OrderSide.BUY
    assert order.order_type == OrderType.MARKET
    assert order.total_value == Decimal("10000")
    assert order.quantity is None


def test_should_buy_false_buys_only_when_not_ath():
    strategy = BuyWhenAthStrategy(should_buy=False)
    assert strategy.decide(make_context(indicators=[_ath(is_ath=True)])) is None

    decision = strategy.decide(make_context(indicators=[_ath(is_ath=False)]))
    assert decision is not None
    assert decision.orders[0].ticker == "BTC"
    assert decision.orders[0].total_value == Decimal("10000")
    assert decision.orders[0].quantity is None


def test_returns_none_when_below_min_usd_even_if_ath():
    strategy = BuyWhenAthStrategy()
    just_below = MIN_USD - Decimal("0.01")
    assert (
        strategy.decide(
            make_context(usd=str(just_below), indicators=[_ath(is_ath=True)])
        )
        is None
    )


def test_should_buy_false_returns_none_when_below_min_usd_even_if_not_ath():
    strategy = BuyWhenAthStrategy(should_buy=False)
    just_below = MIN_USD - Decimal("0.01")
    assert (
        strategy.decide(
            make_context(usd=str(just_below), indicators=[_ath(is_ath=False)])
        )
        is None
    )


def test_buys_when_usd_equals_minimum():
    strategy = BuyWhenAthStrategy()
    decision = strategy.decide(
        make_context(usd=str(MIN_USD), indicators=[_ath(is_ath=True)])
    )
    assert decision is not None
    assert decision.orders[0].total_value == MIN_USD


def test_skips_when_no_open_price():
    strategy = BuyWhenAthStrategy()
    assert (
        strategy.decide(
            make_context(open_prices={}, indicators=[_ath(is_ath=True)])
        )
        is None
    )


def test_skips_when_open_price_missing_for_ticker():
    strategy = BuyWhenAthStrategy()
    assert (
        strategy.decide(
            make_context(
                open_prices={"ETH": Decimal("2000")},
                indicators=[_ath(is_ath=True)],
            )
        )
        is None
    )


def test_skips_when_open_order_exists_for_ticker():
    strategy = BuyWhenAthStrategy()
    resting = Order(
        ticker="BTC",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        price=Decimal("20000"),
    )
    assert (
        strategy.decide(
            make_context(
                indicators=[_ath(is_ath=True)],
                open_orders=[resting],
            )
        )
        is None
    )


def test_buys_configured_ticker():
    strategy = BuyWhenAthStrategy(ticker="ETH")
    decision = strategy.decide(
        make_context(
            usd="1000",
            open_prices={"BTC": Decimal("25000"), "ETH": Decimal("2000")},
            indicators=[_ath(is_ath=True, ticker="ETH")],
        )
    )
    assert decision is not None
    order = decision.orders[0]
    assert order.ticker == "ETH"
    assert order.side == OrderSide.BUY
    assert order.order_type == OrderType.MARKET
    assert order.total_value == Decimal("1000")
    assert order.quantity is None

from datetime import datetime
from decimal import Decimal

import pytest

from models import Account, Context, Order, OrderSide, OrderType, Position


def make_context(
    *,
    usd: str = "10000",
    open_prices: dict[str, Decimal] | None = None,
    positions: list[Position] | None = None,
    open_orders: list[Order] | None = None,
) -> Context:
    return Context(
        time=datetime(2021, 1, 1),
        history={},
        current_open_prices=open_prices or {"EUR": Decimal("1.2")},
        account=Account(balances={"USD": Decimal(usd)}),
        positions=positions or [],
        open_orders=open_orders or [],
    )


def test_position_price_is_quantity_times_open():
    context = make_context()
    position = Position(
        ticker="EUR",
        quantity=Decimal("10"),
        average_price=Decimal("1.1"),
    )

    assert context.position_price(position) == Decimal("12.0")


def test_position_price_uses_current_open_not_average():
    context = make_context(open_prices={"BTC": Decimal("25000")})
    position = Position(
        ticker="BTC",
        quantity=Decimal("2"),
        average_price=Decimal("20000"),
    )

    assert context.position_price(position) == Decimal("50000")


def test_position_price_raises_when_open_missing():
    context = make_context()
    position = Position(
        ticker="BTC",
        quantity=Decimal("1"),
        average_price=Decimal("20000"),
    )

    with pytest.raises(ValueError, match="BTC"):
        context.position_price(position)


def test_position_price_by_ticker_looks_up_holding():
    position = Position(
        ticker="EUR",
        quantity=Decimal("10"),
        average_price=Decimal("1.1"),
    )
    context = make_context(positions=[position])

    assert context.position_price("EUR") == context.position_price(position)


def test_position_price_by_ticker_raises_when_missing():
    context = make_context()

    with pytest.raises(ValueError, match="EUR"):
        context.position_price("EUR")


def test_position_value_matches_quantity_times_open():
    context = make_context()
    position = Position(
        ticker="EUR",
        quantity=Decimal("10"),
        average_price=Decimal("1.1"),
    )

    assert context.position_value(position) == Decimal("12.0")


def test_position_value_by_ticker():
    position = Position(
        ticker="EUR",
        quantity=Decimal("10"),
        average_price=Decimal("1.1"),
    )
    context = make_context(positions=[position])

    assert context.position_value("EUR") == context.position_value(position)


def test_portfolio_value_is_cash_when_flat():
    context = make_context(usd="10000")

    assert context.portfolio_value() == Decimal("10000")


def test_portfolio_value_adds_marked_positions():
    position = Position(
        ticker="EUR",
        quantity=Decimal("10"),
        average_price=Decimal("1.1"),
    )
    context = make_context(usd="10000", positions=[position])

    assert context.portfolio_value() == Decimal("10012.0")


def test_portfolio_value_includes_reserved_cash():
    order = Order(
        ticker="EUR",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("5"),
        price=Decimal("1.2"),
        reserved_cash=Decimal("6"),
    )
    context = make_context(usd="9994", open_orders=[order])

    assert context.portfolio_value() == Decimal("10000")


def test_portfolio_value_includes_reserved_coins():
    order = Order(
        ticker="EUR",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=Decimal("4"),
        price=Decimal("1.3"),
        reserved_quantity=Decimal("4"),
    )
    context = make_context(usd="10000", open_orders=[order])

    assert context.portfolio_value() == Decimal("10004.8")

from datetime import datetime
from decimal import Decimal

from models import Account, Context, Position


def make_context(positions: list[Position] | None = None) -> Context:
    return Context(
        time=datetime(2021, 1, 1),
        history={},
        current_open_prices={"EUR": Decimal("1.2")},
        account=Account(balances={"USD": Decimal("10000")}),
        positions=positions or [],
    )


def test_position_returns_matching_holding():
    held = Position(ticker="EUR", quantity=Decimal("10"), average_price=Decimal("1.1"))
    context = make_context([held])

    assert context.position("EUR") is held


def test_position_returns_none_when_missing():
    context = make_context(
        [Position(ticker="BTC", quantity=Decimal("1"), average_price=Decimal("20000"))]
    )

    assert context.position("EUR") is None


def test_position_price_returns_average_price():
    context = make_context(
        [
            Position(
                ticker="EUR",
                quantity=Decimal("10"),
                average_price=Decimal("1.1"),
            )
        ]
    )

    assert context.position_price("EUR") == Decimal("1.1")


def test_position_price_returns_none_when_missing():
    context = make_context()

    assert context.position_price("EUR") is None

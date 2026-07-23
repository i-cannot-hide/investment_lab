from datetime import datetime
from decimal import Decimal

from models import Account, Context
from strategies.do_nothing import DoNothingStrategy


def test_do_nothing_returns_none():
    strategy = DoNothingStrategy()
    context = Context(
        time=datetime(2023, 1, 1),
        history={},
        current_open_prices={"BTC": Decimal("25000")},
        account=Account(balances={"USD": Decimal("10000")}),
        positions=[],
        open_orders=[],
    )

    assert strategy.decide(context) is None

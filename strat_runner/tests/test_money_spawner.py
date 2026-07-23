from datetime import datetime
from decimal import Decimal

import pytest

from models import Account
from money_spawner import MoneySpawner, SpawnInterval


def test_rejects_non_positive_amount():
    with pytest.raises(ValueError, match="positive"):
        MoneySpawner(currency="USD", amount=0, interval=SpawnInterval.MONTH)


def test_rejects_non_enum_interval():
    with pytest.raises(TypeError, match="SpawnInterval"):
        MoneySpawner(currency="USD", amount=100, interval="1M")  # type: ignore[arg-type]


def test_period_keys():
    spawner = MoneySpawner(currency="USD", amount=100, interval=SpawnInterval.DAY)
    assert spawner.period_key(datetime(2023, 1, 15)) == "2023-01-15"

    spawner = MoneySpawner(currency="USD", amount=100, interval=SpawnInterval.WEEK)
    assert spawner.period_key(datetime(2023, 1, 2)) == "2023-W01"  # Monday

    spawner = MoneySpawner(currency="USD", amount=100, interval=SpawnInterval.MONTH)
    assert spawner.period_key(datetime(2023, 1, 15)) == "2023-01"


def test_monthly_spawns_once_per_month():
    account = Account(balances={"USD": Decimal("0")})
    spawner = MoneySpawner(
        currency="USD",
        amount=1000,
        interval=SpawnInterval.MONTH,
    )

    assert spawner.spawn(datetime(2023, 1, 1), account) == Decimal("1000")
    assert account.balances["USD"] == Decimal("1000")

    assert spawner.spawn(datetime(2023, 1, 15), account) is None
    assert account.balances["USD"] == Decimal("1000")

    assert spawner.spawn(datetime(2023, 2, 1), account) == Decimal("1000")
    assert account.balances["USD"] == Decimal("2000")


def test_daily_spawns_each_day():
    account = Account(balances={"USD": Decimal("0")})
    spawner = MoneySpawner(
        currency="USD",
        amount=50,
        interval=SpawnInterval.DAY,
    )

    assert spawner.spawn(datetime(2023, 1, 1), account) == Decimal("50")
    assert spawner.spawn(datetime(2023, 1, 1, 12), account) is None
    assert spawner.spawn(datetime(2023, 1, 2), account) == Decimal("50")
    assert account.balances["USD"] == Decimal("100")


def test_creates_currency_balance_if_missing():
    account = Account(balances={})
    spawner = MoneySpawner(
        currency="EUR",
        amount=25,
        interval=SpawnInterval.DAY,
    )

    assert spawner.spawn(datetime(2023, 1, 1), account) == Decimal("25")
    assert account.balances["EUR"] == Decimal("25")

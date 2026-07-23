from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from models import Account


class SpawnInterval(Enum):
    DAY = "1D"
    WEEK = "1W"
    MONTH = "1M"


@dataclass
class MoneySpawner:
    currency: str
    amount: Decimal | float | str | int
    interval: SpawnInterval
    _last_period: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.amount = Decimal(str(self.amount))
        if self.amount <= 0:
            raise ValueError("MoneySpawner amount must be positive")
        if not isinstance(self.interval, SpawnInterval):
            raise TypeError(
                f"interval must be SpawnInterval, got {type(self.interval)!r}"
            )

    def period_key(self, time: datetime) -> str:
        if self.interval == SpawnInterval.DAY:
            return time.strftime("%Y-%m-%d")
        if self.interval == SpawnInterval.WEEK:
            iso = time.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        if self.interval == SpawnInterval.MONTH:
            return time.strftime("%Y-%m")
        raise ValueError(f"Unsupported interval: {self.interval}")

    def spawn(self, time: datetime, account: Account) -> Decimal | None:
        key = self.period_key(time)
        if key == self._last_period:
            return None

        self._last_period = key
        account.balances[self.currency] = (
            account.balances.get(self.currency, Decimal("0")) + self.amount
        )
        return self.amount

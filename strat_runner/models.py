from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from decimal import Decimal
from itertools import count
from typing import overload


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


_order_ids = count(1)


def _next_order_id() -> str:
    return f"o{next(_order_ids)}"


@dataclass
class Candle:
    time: datetime
    ticker: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass
class Order:
    ticker: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal | None = None
    total_value: Decimal | None = None
    price: Decimal | None = None
    id: str = field(default_factory=_next_order_id)
    # Set by Environment when a limit is accepted; not set by strategies.
    reserved_cash: Decimal | None = None
    reserved_quantity: Decimal | None = None

    def __post_init__(self):
        has_quantity = self.quantity is not None
        has_value = self.total_value is not None

        if has_quantity == has_value:
            raise ValueError(
                "Order must specify exactly one of quantity or total_value"
            )

        if (self.order_type == OrderType.MARKET) and (self.price is not None):
            raise ValueError("Market orders must not include price")
        elif (self.order_type == OrderType.LIMIT) and (self.price is None):
            raise ValueError("Limit orders must include price")

        if self.reserved_cash is not None:
            self.reserved_cash = Decimal(str(self.reserved_cash))
            if self.reserved_cash < 0:
                raise ValueError("reserved_cash must be non-negative")

        if self.reserved_quantity is not None:
            self.reserved_quantity = Decimal(str(self.reserved_quantity))
            if self.reserved_quantity < 0:
                raise ValueError("reserved_quantity must be non-negative")


@dataclass
class Decision:
    orders: list[Order] = field(default_factory=list)
    cancel_order_ids: list[str] = field(default_factory=list)


@dataclass
class Position:
    ticker: str
    quantity: Decimal
    average_price: Decimal


@dataclass
class Account:
    balances: dict[str, Decimal]


@dataclass
class Context:
    time: datetime
    history: dict[str, list[Candle]]
    current_open_prices: dict[str, Decimal]
    account: Account
    positions: list[Position]
    open_orders: list[Order] = field(default_factory=list)
    indicators: list = field(default_factory=list)

    @overload
    def position_price(self, position: Position) -> Decimal: ...

    @overload
    def position_price(self, position: str) -> Decimal: ...

    def _held_position(self, ticker: str) -> Position:
        held = next(
            (item for item in self.positions if item.ticker == ticker),
            None,
        )
        if held is None:
            raise ValueError(f"No position for {ticker}")
        return held

    def _reserved_quantity(self, ticker: str) -> Decimal:
        total = Decimal("0")
        for order in self.open_orders:
            if order.ticker == ticker and order.reserved_quantity is not None:
                total += order.reserved_quantity
        return total

    def position_price(self, position: Position | str) -> Decimal:
        """Mark-to-market value: quantity times the current open price."""
        if isinstance(position, str):
            return self.position_price(self._held_position(position))

        price = self.current_open_prices.get(position.ticker)
        if price is None:
            raise ValueError(f"No current open price for {position.ticker}")
        return position.quantity * price

    @overload
    def position_value(self, position: Position) -> Decimal: ...

    @overload
    def position_value(self, position: str) -> Decimal: ...

    def position_value(self, position: Position | str) -> Decimal:
        """USD value of a position at the current open."""
        return self.position_price(position)

    @overload
    def position_qty(self, position: Position) -> Decimal: ...

    @overload
    def position_qty(self, position: str) -> Decimal: ...

    def position_qty(self, position: Position | str) -> Decimal:
        """Owned quantity, including coins reserved on open sell orders."""
        if isinstance(position, str):
            ticker = position
            held = next(
                (item for item in self.positions if item.ticker == ticker),
                None,
            )
            reserved = self._reserved_quantity(ticker)
            if held is None and reserved == 0:
                raise ValueError(f"No position for {ticker}")
            free = held.quantity if held is not None else Decimal("0")
            return free + reserved
        return position.quantity + self._reserved_quantity(position.ticker)

    def portfolio_value(self) -> Decimal:
        """USD value of cash, holdings, and reserved coins at the current open."""
        total = self.account.balances.get("USD", Decimal("0"))
        for order in self.open_orders:
            if order.reserved_cash is not None:
                total += order.reserved_cash
            if order.reserved_quantity is not None:
                price = self.current_open_prices.get(order.ticker)
                if price is None:
                    raise ValueError(f"No current open price for {order.ticker}")
                total += order.reserved_quantity * price
        for held in self.positions:
            total += self.position_value(held)
        return total

"""Journal entries: chronological record of what the environment applied."""

from decimal import Decimal
from enum import Enum

from models import Order


class EntryType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"


def deposit_entry(*, currency: str, amount: Decimal) -> dict:
    return {
        "type": EntryType.DEPOSIT.value,
        "currency": currency,
        "amount": str(amount),
    }


def withdrawal_entry(*, currency: str, amount: Decimal) -> dict:
    return {
        "type": EntryType.WITHDRAWAL.value,
        "currency": currency,
        "amount": str(amount),
    }


def order_filled_entry(
    *,
    order: Order,
    quantity: Decimal,
    price: Decimal,
) -> dict:
    return {
        "type": EntryType.ORDER_FILLED.value,
        "order_id": order.id,
        "ticker": order.ticker,
        "side": order.side.value,
        "order_type": order.order_type.value,
        "quantity": str(quantity),
        "price": str(price),
    }


def order_cancelled_entry(*, order: Order) -> dict:
    return {
        "type": EntryType.ORDER_CANCELLED.value,
        "order_id": order.id,
        "ticker": order.ticker,
        "side": order.side.value,
        "order_type": order.order_type.value,
        "quantity": str(order.quantity) if order.quantity is not None else None,
        "total_value": (
            str(order.total_value) if order.total_value is not None else None
        ),
        "price": str(order.price) if order.price is not None else None,
    }

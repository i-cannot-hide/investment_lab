from decimal import Decimal

from models import Context, Order, OrderSide, OrderType


MIN_USD = Decimal("10.00")


class HoldStrategy:
    def __init__(self, ticker: str = "BTC"):
        self.ticker = ticker

    def decide(self, context: Context) -> list[Order]:
        usd = context.account.balances.get("USD", Decimal("0"))
        if usd < MIN_USD:
            return []

        candles = context.candles.get(self.ticker, [])
        if not candles:
            return []

        price = candles[-1].close
        if price <= 0:
            return []

        quantity = usd / price

        return [
            Order(
                ticker=self.ticker,
                side=OrderSide.BUY,
                quantity=quantity,
                order_type=OrderType.MARKET,
            )
        ]

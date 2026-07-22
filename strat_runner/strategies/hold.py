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

        price = context.current_open_prices.get(self.ticker)
        if price is None or price <= 0:
            return []

        return [
            Order(
                ticker=self.ticker,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                total_value=usd,
            )
        ]

from decimal import Decimal

from models import Context, Decision, Order, OrderSide, OrderType
from strategies.strategy import Strategy


MIN_USD = Decimal("10.00")


class BuyWhenAthStrategy(Strategy):
    def __init__(
        self,
        ticker: str = "BTC",
    ):
        self.ticker = ticker

    def decide(self, context: Context) -> Decision | None:
        usd = context.account.balances.get("USD", Decimal("0"))
        if usd < MIN_USD:
            return None

        if self.ticker not in context.current_open_prices:
            return None

        if any(order.ticker == self.ticker for order in context.open_orders):
            return None

        return Decision(
            orders=[
                Order(
                    ticker=self.ticker,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    total_value=usd
                )
            ]
        )

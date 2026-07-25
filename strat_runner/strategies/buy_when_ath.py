from decimal import Decimal

from indicators import IsAth
from models import Context, Decision, Order, OrderSide, OrderType
from strategies.strategy import Strategy


MIN_USD = Decimal("10.00")


class BuyWhenAthStrategy(Strategy):
    def __init__(
        self,
        ticker: str = "BTC",
        should_buy: bool = True,
    ):
        self.ticker = ticker
        self.should_buy = bool(should_buy)

    def _require_is_ath(self, context: Context) -> bool:
        for indicator in context.indicators:
            if isinstance(indicator, IsAth) and indicator.ticker == self.ticker:
                if indicator.is_ath is None:
                    raise ValueError(
                        f"IsAth indicator for {self.ticker!r} has no value this bar"
                    )
                return indicator.is_ath
        raise ValueError(
            f"BuyWhenAthStrategy requires an IsAth indicator for {self.ticker!r}"
        )

    def decide(self, context: Context) -> Decision | None:
        is_ath = self._require_is_ath(context)
        # should_buy=True  → buy only on ATH
        # should_buy=False → buy only when not ATH
        if is_ath != self.should_buy:
            return None

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
                    total_value=usd,
                )
            ]
        )

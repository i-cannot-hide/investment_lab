from decimal import Decimal

from strategies.strategy import Strategy


class GridStrategy(Strategy):
    """Grid trading strategy. Not implemented yet."""

    def __init__(
        self,
        min_price: Decimal | float | str | int,
        max_price: Decimal | float | str | int,
        num_of_lines: int = 2,
        ticker: str = "BTC",
    ):
        self.min_price = Decimal(str(min_price))
        self.max_price = Decimal(str(max_price))
        self.num_of_lines = num_of_lines
        self.ticker = ticker
        self.order_prices = self._calculate_order_prices()
        v = 2

    def _calculate_order_prices(self) -> list[Decimal]:

        total_multiplier = self.max_price / self.min_price
        step = total_multiplier ** (Decimal(1) / Decimal(self.num_of_lines))
        return [self.min_price * step**i for i in range(self.num_of_lines + 1)]

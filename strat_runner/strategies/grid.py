from decimal import Decimal

from strategies.strategy import Strategy


class GridStrategy(Strategy):
    """Grid trading strategy. Not implemented yet."""

    def __init__(
        self,
        min_price: Decimal | float | str | int,
        max_price: Decimal | float | str | int,
        num_of_lines: int,
        ticker: str = "BTC",
    ):
        self.min_price = Decimal(str(min_price))
        self.max_price = Decimal(str(max_price))
        self.num_of_lines = num_of_lines
        self.ticker = ticker
        self.order_prices = self._calculate_order_prices()

    def _calculate_order_prices(self) -> list[Decimal]:
        """Evenly spaced prices between min_price and max_price."""
        return []

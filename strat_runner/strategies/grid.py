from decimal import Decimal
import re

from strategies.strategy import Strategy
from models import Context, Decision, Order, OrderSide, OrderType


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

        self.buy_orde: Order = None
        self.sell_order: Order = None

    def _calculate_order_prices(self) -> list[Decimal]:

        total_multiplier = self.max_price / self.min_price
        step = total_multiplier ** (Decimal(1) / Decimal(self.num_of_lines))
        return [self.min_price * step**i for i in range(self.num_of_lines + 1)]

    def decide(self, context: Context) -> Decision | None:

        price = context.current_open_prices.get(self.ticker)
        if price is None or price <= 0:
            return None

        # считает на какой мы сейчас линии
        line_index = 0
        for order_price in self.order_prices:
            if price >= order_price:
                line_index += 1
            else:
                break

        # определяет какие должны быть пропорции в портфеле
        portfolio_percentage_step = Decimal(1 / self.num_of_lines)
        target_usd_share = portfolio_percentage_step * (self.num_of_lines - line_index)
        target_asset_share = 1 - target_usd_share

        # сколько должно быть usd
        target_usd_amount = context.account.balances["USD"] * Decimal(target_usd_share)

        # сколько должно быть asset (в usd)
        target_asset_value = (
            (1 / target_usd_share) * target_asset_share * target_usd_amount
        )

        # сколько это по текущей цене
        target_asset_amount = target_asset_value / price

        asset_position = next(
            (p for p in context.positions if p.ticker == self.ticker), None
        )

        # если нет asset в портфеле, то покупаем по рынку
        if asset_position is None:
            return Decision(
                orders=[
                    Order(
                        ticker=self.ticker,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=target_asset_amount,
                    )
                ]
            )

        asset_amount = context.positions[context.positions.index(self.ticker)].quantity

        # if self.buy_order is None or not context.open_orders.contains(
        #     self.buy_order.id
        # ):
        #     self.buy_order = Order(
        #         ticker=self.ticker,
        #         side=OrderSide.BUY,
        #         order_type=OrderType.LIMIT,
        #         price=order_price,
        #     )

        # return None

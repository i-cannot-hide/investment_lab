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

        self.buy_order: Order = None
        self.sell_order: Order = None

    def _calculate_order_prices(self) -> list[Decimal]:

        total_multiplier = self.max_price / self.min_price
        step = total_multiplier ** (Decimal(1) / Decimal(self.num_of_lines))
        return [self.min_price * step**i for i in range(self.num_of_lines + 1)]

    def _calculate_current_price_line(self, price: Decimal) -> int:

        # считает на какой мы сейчас линии
        line_index = 0
        for order_price in self.order_prices:
            if price > order_price:
                line_index += 1
            else:
                break

        return line_index

    def _calculate_target_amount(
        self, context: Context, line_index: int, price: Decimal
    ):

        # определяет какие должны быть пропорции в портфеле
        portfolio_percentage_step = Decimal(1 / self.num_of_lines)
        target_usd_share = portfolio_percentage_step * line_index
        target_asset_share = 1 - target_usd_share

        # сколько должно быть asset (в usd)
        target_asset_value = context.portfolio_value() * target_asset_share

        # сколько это по текущей цене
        target_asset_amount = target_asset_value / price

        return target_asset_amount

    def decide(self, context: Context) -> Decision | None:
        current_price = context.current_open_prices.get(self.ticker)
        line_index = self._calculate_current_price_line(current_price)
        target_asset_amount = self._calculate_target_amount(
            context, line_index, current_price
        )

        asset_position = next(
            (p for p in context.positions if p.ticker == self.ticker), None
        )

        orders = []
        # если нет asset в портфеле, то покупаем по рынку
        if asset_position is None:
            orders.append(
                Order(
                    ticker=self.ticker,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=target_asset_amount,
                )
            )

            return Decision(orders=orders)

        if self.buy_order is None and line_index > 0:
            buy_limit_price_index = line_index - 1 if line_index > 0 else line_index
            buy_limit_price = self.order_prices[buy_limit_price_index]

            new_buy_target_asset_amount = self._calculate_target_amount(
                context, buy_limit_price_index, buy_limit_price
            )

            buy_limit_asset_amount = new_buy_target_asset_amount - context.position_qty(
                self.ticker
            )

            self.buy_order = Order(
                ticker=self.ticker,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=buy_limit_price,
                quantity=buy_limit_asset_amount,
            )

            orders.append(self.buy_order)

        if self.sell_order is None:
            sell_limit_price_index = (
                line_index + 1
                if line_index < len(self.order_prices) - 1
                else line_index
            )
            sell_limit_price = self.order_prices[sell_limit_price_index]

            new_sell_target_asset_amount = self._calculate_target_amount(
                context, sell_limit_price_index, sell_limit_price
            )

            sell_limit_asset_amount = (
                context.position_qty(self.ticker) - new_sell_target_asset_amount
            )

            self.sell_order = Order(
                ticker=self.ticker,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=sell_limit_price,
                quantity=sell_limit_asset_amount,
            )

            orders.append(self.sell_order)

            if len(orders) > 0:
                return Decision(orders=orders)

        orders = []
        cancel_order_ids = []
        if (
            self.buy_order is not None and self.buy_order not in context.open_orders
        ) or (
            self.sell_order is not None and self.sell_order not in context.open_orders
        ):
            pass
            # if self.buy_order not in context.open_orders:
            #     cancel_order_ids.append(self.buy_order.id)
            # if self.sell_order not in context.open_orders:
            #     cancel_order_ids.append(self.sell_order.id)

            # old_price_line_index = self._calculate_current_price_line(current_price)

            # new_price_line_index = (
            #     old_price_line_index - 1 if old_price_line_index > 0 else 0
            # )

            # new_buy_limit_price = self.order_prices[new_price_line_index]
            # new_buy_target_asset_amount = self._calculate_target_amount(
            #     context, new_price_line_index, new_buy_limit_price
            # )

            # new_buy_limit_order_asset_amount = (
            #     new_buy_target_asset_amount - context.position_qty(self.ticker)
            # )

            # self.buy_order = Order(
            #     ticker=self.ticker,
            #     side=OrderSide.BUY,
            #     order_type=OrderType.LIMIT,
            #     price=new_buy_limit_price,
            #     quantity=new_buy_limit_order_asset_amount,
            # )

            # orders.append(self.buy_order)

            # old_sell_price_line_index = self._calculate_current_price_line(
            #     current_price
            # )

            # new_sell_price_line_index = (
            #     old_sell_price_line_index + 1
            #     if old_sell_price_line_index < self.num_of_lines
            #     else self.num_of_lines
            # )

            # new_sell_limit_price = self.order_prices[new_sell_price_line_index]
            # new_sell_target_asset_amount = self._calculate_target_amount(
            #     context, new_sell_price_line_index, new_buy_limit_price
            # )

            # new_sell_limit_order_asset_amount = (
            #     context.position_qty(self.ticker) - new_sell_target_asset_amount
            # )

            # self.sell_order = Order(
            #     ticker=self.ticker,
            #     side=OrderSide.SELL,
            #     order_type=OrderType.LIMIT,
            #     price=new_sell_limit_price,
            #     quantity=new_sell_limit_order_asset_amount,
            # )

            # orders.append(self.sell_order)

        return Decision(orders=orders, cancel_order_ids=cancel_order_ids)

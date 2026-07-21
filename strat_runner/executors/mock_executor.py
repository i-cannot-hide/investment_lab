from decimal import Decimal

from models import Account, Candle, Order, OrderSide, Position, OrderType


class MockExecutor:
    def execute(
        self,
        orders: list[Order],
        account: Account,
        positions: list[Position],
        candles: dict[str, Candle],
    ):

        for order in orders:
            candle = candles[order.ticker]

            if order.order_type == OrderType.LIMIT:
                raise NotImplementedError("Limit orders are not implemented")

            price = candle.close
            
            if order.side == OrderSide.BUY:
                self._buy(order, price, account, positions)

            elif order.side == OrderSide.SELL:
                self._sell(order, price, account, positions)

    def _find_position(
        self, positions: list[Position], ticker: str
    ) -> tuple[int | None, Position | None]:
        for index, position in enumerate(positions):
            if position.ticker == ticker:
                return index, position
        return None, None

    def _buy(
        self, order: Order, price: Decimal, account: Account, positions: list[Position]
    ):
        cost = order.quantity * price

        if account.balances["USD"] < cost:
            raise ValueError(f"Not enough balance to buy {order.quantity} {order.ticker}")

        account.balances["USD"] -= cost

        _, position = self._find_position(positions, order.ticker)
        if position is None:
            positions.append(
                Position(
                    ticker=order.ticker,
                    quantity=order.quantity,
                    average_price=price,
                )
            )
            return

        new_quantity = position.quantity + order.quantity
        position.average_price = (
            position.quantity * position.average_price + order.quantity * price
        ) / new_quantity
        position.quantity = new_quantity

    def _sell(
        self, order: Order, price: Decimal, account: Account, positions: list[Position]
    ):
        index, position = self._find_position(positions, order.ticker)
        if position is None or position.quantity < order.quantity:
            raise ValueError(
                f"Not enough quantity to sell {order.quantity} {order.ticker}"
            )

        position.quantity -= order.quantity
        account.balances["USD"] += order.quantity * price

        if position.quantity == 0:
            positions.pop(index)

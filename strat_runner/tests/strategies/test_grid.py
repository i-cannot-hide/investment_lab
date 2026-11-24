from decimal import Decimal

from strategies.grid import GridStrategy


def test_order_prices_count_is_one_more_than_num_of_lines():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=2)

    assert len(strategy.order_prices) == 3


def test_order_prices_start_at_min_price():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=2)

    assert strategy.order_prices[0] == Decimal("100")


def test_order_prices_end_at_max_price():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=2)

    assert strategy.order_prices[-1] == Decimal("400")


def test_order_prices_are_geometric():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=2)

    assert strategy.order_prices == [
        Decimal("100"),
        Decimal("200"),
        Decimal("400"),
    ]


def test_three_lines_are_geometric():
    strategy = GridStrategy(min_price=100, max_price=800, num_of_lines=3)

    assert strategy.order_prices == [
        Decimal("100"),
        Decimal("200"),
        Decimal("400"),
        Decimal("800"),
    ]


def test_four_lines_are_geometric():
    strategy = GridStrategy(min_price=1, max_price=16, num_of_lines=4)

    assert strategy.order_prices == [
        Decimal("1"),
        Decimal("2"),
        Decimal("4"),
        Decimal("8"),
        Decimal("16"),
    ]


def test_one_line_is_min_and_max():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=1)

    assert strategy.order_prices == [Decimal("100"), Decimal("400")]


def test_equal_min_and_max_repeats_the_price():
    strategy = GridStrategy(min_price=100, max_price=100, num_of_lines=3)

    assert strategy.order_prices == [
        Decimal("100"),
        Decimal("100"),
        Decimal("100"),
        Decimal("100"),
    ]


def test_order_prices_are_decimals():
    strategy = GridStrategy(min_price="100", max_price="400", num_of_lines=2)

    assert all(isinstance(price, Decimal) for price in strategy.order_prices)


def test_constructor_uses_calculate_order_prices():
    strategy = GridStrategy(min_price=100, max_price=400, num_of_lines=2)

    assert strategy.order_prices == strategy._calculate_order_prices()

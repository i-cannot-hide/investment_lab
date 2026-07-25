from datetime import datetime

import pandas as pd

from analysis.plotter import aggregate_journal_markers, flatten_journal
from engine.journal import EntryType


def _steps(*journals_by_day: list[dict]) -> pd.DataFrame:
    rows = []
    for index, journal in enumerate(journals_by_day):
        rows.append(
            {
                "time": datetime(2023, 1, 1 + index),
                "equity": 10000 + index,
                "journal": journal,
            }
        )
    return pd.DataFrame(rows)


def test_flatten_and_aggregate_keeps_single_entry_style():
    steps = _steps(
        [
            {
                "type": EntryType.DEPOSIT.value,
                "currency": "USD",
                "amount": "1000",
            }
        ]
    )
    frame = steps.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    journal = flatten_journal(frame)
    markers = aggregate_journal_markers(journal, frame, "equity")

    assert len(markers) == 1
    assert markers[0]["style"]["name"] == "deposit"
    assert markers[0]["text"] == ""
    assert markers[0]["hover"] == "DEPOSIT 1000 USD"
    assert markers[0]["count"] == 1


def test_false_is_ath_entries_are_not_plotted():
    steps = _steps(
        [
            {
                "type": EntryType.IS_ATH.value,
                "ticker": "SPX",
                "IsATH": False,
            }
        ],
        [
            {
                "type": EntryType.IS_ATH.value,
                "ticker": "SPX",
                "IsATH": True,
            }
        ],
    )
    frame = steps.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    journal = flatten_journal(frame)
    markers = aggregate_journal_markers(journal, frame, "equity")

    assert len(markers) == 1
    assert markers[0]["style"]["name"] == "ath"
    assert markers[0]["hover"] == "ATH SPX"


def test_same_day_entries_each_keep_their_marker():
    steps = _steps(
        [
            {
                "type": EntryType.DEPOSIT.value,
                "currency": "USD",
                "amount": "1000",
            },
            {
                "type": EntryType.INTEREST.value,
                "ticker": "USD",
                "amount": "40",
                "principal": "4000",
                "rate": "0.01",
            },
            {
                "type": EntryType.ORDER_FILLED.value,
                "side": "BUY",
                "quantity": "0.5",
                "price": "100",
                "order_id": "o1",
                "ticker": "BTC",
                "order_type": "MARKET",
            },
        ]
    )
    frame = steps.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    journal = flatten_journal(frame)
    markers = aggregate_journal_markers(journal, frame, "equity")

    assert len(markers) == 3
    assert [marker["style"]["name"] for marker in markers] == [
        "deposit",
        "interest",
        "buy",
    ]
    assert [marker["hover"] for marker in markers] == [
        "DEPOSIT 1000 USD",
        "INTEREST 40 USD",
        "BUY BTC 0.5 @ 100",
    ]
    # Same base series y, staggered so all three remain visible.
    ys = [marker["y"] for marker in markers]
    assert len(set(ys)) == 3
    assert min(ys) < 10000.0 < max(ys)


def test_different_days_stay_separate():
    steps = _steps(
        [{"type": EntryType.DEPOSIT.value, "currency": "USD", "amount": "1000"}],
        [{"type": EntryType.INTEREST.value, "ticker": "USD", "amount": "10"}],
    )
    frame = steps.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    journal = flatten_journal(frame)
    markers = aggregate_journal_markers(journal, frame, "equity")

    assert len(markers) == 2
    assert markers[0]["style"]["name"] == "deposit"
    assert markers[1]["style"]["name"] == "interest"


def test_series_journal_customdata_only_on_event_days():
    from analysis.plotter import series_journal_customdata

    times = list(pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]))
    markers = [
        {
            "time": times[1],
            "y": 100.0,
            "style": {"name": "deposit"},
            "text": "",
            "hover": "DEPOSIT 1",
            "count": 1,
        },
        {
            "time": times[1],
            "y": 103.0,
            "style": {"name": "interest"},
            "text": "",
            "hover": "INTEREST 2",
            "count": 1,
        },
    ]
    customdata = series_journal_customdata(times, markers)
    assert customdata == ["", "<br>DEPOSIT 1<br>INTEREST 2", ""]


def test_hover_number_decimals():
    from analysis.plotter import _format_asset_amount, _format_number, _hover_line

    assert _format_asset_amount("1000.129", asset="USD") == "1000.13"
    assert _format_asset_amount("1000.10", asset="USD") == "1000.1"
    assert _format_asset_amount("0.123456", asset="BTC") == "0.1235"
    assert _format_number("25000.12345", max_decimals=4) == "25000.1235"

    fill = pd.Series(
        {
            "type": EntryType.ORDER_FILLED.value,
            "side": "BUY",
            "ticker": "BTC",
            "quantity": "0.123456789",
            "price": "25000.123456",
        }
    )
    assert _hover_line(fill) == "BUY BTC 0.1235 @ 25000.1235"

    interest = pd.Series(
        {
            "type": EntryType.INTEREST.value,
            "ticker": "USD",
            "amount": "40.129",
        }
    )
    assert _hover_line(interest) == "INTEREST 40.13 USD"

    ath = pd.Series(
        {
            "type": EntryType.IS_ATH.value,
            "ticker": "SPX",
            "IsATH": True,
        }
    )
    assert _hover_line(ath) == "ATH SPX"


def test_hover_line_prefixes_experiment():
    from analysis.plotter import _hover_line

    entry = pd.Series(
        {
            "type": EntryType.DEPOSIT.value,
            "currency": "USD",
            "amount": "1000",
            "experiment": "do-nothing_with_salary",
        }
    )
    assert _hover_line(entry) == "do-nothing_with_salary: DEPOSIT 1000 USD"


def test_collect_research_journal_and_price_attach():
    from analysis.plotter import (
        attach_journal_to_price,
        collect_research_journal,
        extract_ticker_ohlc,
    )

    def steps_with(ticker: str, journal: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "time": datetime(2023, 1, 1),
                    "candles": {
                        ticker: {
                            "open": "100",
                            "high": "110",
                            "low": "90",
                            "close": "105",
                        }
                    },
                    "journal": journal,
                },
                {
                    "time": datetime(2023, 2, 1),
                    "candles": {
                        ticker: {
                            "open": "105",
                            "high": "120",
                            "low": "100",
                            "close": "115",
                        }
                    },
                    "journal": [],
                },
            ]
        )

    outcomes = {
        "a": steps_with(
            "SPX",
            [{"type": EntryType.DEPOSIT.value, "currency": "USD", "amount": "1000"}],
        ),
        "b": steps_with(
            "SPX",
            [
                {
                    "type": EntryType.ORDER_FILLED.value,
                    "side": "BUY",
                    "ticker": "SPX",
                    "quantity": "1",
                    "price": "105",
                }
            ],
        ),
    }
    journal = collect_research_journal(
        outcomes,
        [EntryType.DEPOSIT.value, EntryType.ORDER_FILLED.value],
    )
    assert set(journal["experiment"]) == {"a", "b"}
    assert len(journal) == 2

    price = extract_ticker_ohlc(outcomes["a"], "SPX")
    assert len(price) == 2
    assert list(price.columns) == ["time", "open", "high", "low", "close"]

    attached = attach_journal_to_price(price, journal)
    assert len(attached.loc[0, "journal"]) == 2
    assert attached.loc[1, "journal"] == []

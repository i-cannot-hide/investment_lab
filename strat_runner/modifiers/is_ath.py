from dataclasses import dataclass, field
from decimal import Decimal

from engine.journal import is_ath_entry
from modifiers.modifier import ExperimentModifier, ModifierContext


@dataclass
class IsAth(ExperimentModifier):
    """Mark bars near the running all-time high for one ticker.

    Uses each bar's **high**. A bar counts as ATH when::

        high >= peak * (1 - acceptable_drop)

    where ``peak`` is the highest high seen on prior bars (or this bar's high
    on the first observation). ``acceptable_drop`` is a fraction (0.02 → 2%).

    Writes an ``is_ath`` journal entry every bar with boolean field ``IsATH``.
    """

    ticker: str
    acceptable_drop: Decimal | float | str | int = 0
    _peak_high: Decimal | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.ticker = str(self.ticker)
        if not self.ticker:
            raise ValueError("IsAth ticker must be non-empty")
        self.acceptable_drop = Decimal(str(self.acceptable_drop))
        if self.acceptable_drop < 0 or self.acceptable_drop >= 1:
            raise ValueError(
                "acceptable_drop must be in [0, 1), "
                f"got {self.acceptable_drop}"
            )

    def on_bar_end(self, ctx: ModifierContext) -> list[dict]:
        candle = ctx.bar_candles.get(self.ticker)
        if candle is None:
            return []

        high = Decimal(str(candle.high))
        if self._peak_high is None:
            peak = high
            is_ath = True
        else:
            peak = self._peak_high
            threshold = peak * (Decimal("1") - self.acceptable_drop)
            is_ath = high >= threshold

        if self._peak_high is None or high > self._peak_high:
            self._peak_high = high

        return [
            is_ath_entry(
                ticker=self.ticker,
                is_ath=is_ath,
                high=high,
                peak=peak,
                acceptable_drop=self.acceptable_drop,
            )
        ]

    def registry_record(self) -> dict:
        return {
            "type": "IsAth",
            "ticker": self.ticker,
            "acceptable_drop": str(self.acceptable_drop),
        }

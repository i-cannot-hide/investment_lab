from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models import Candle


@dataclass
class IndicatorContext:
    """Market state visible to indicators when they update for a bar."""

    time: datetime
    bar_candles: dict[str, Candle]
    history: dict[str, list[Candle]]
    is_last_bar: bool


class Indicator:
    """Bar signal computed before ``decide``. Override ``update``."""

    def update(self, ctx: IndicatorContext) -> list[dict]:
        """Refresh this bar's value. Return journal entries (may be empty)."""
        return []

    def registry_record(self) -> dict:
        """Serializable config snippet for the outcomes registry."""
        return {"type": type(self).__name__}

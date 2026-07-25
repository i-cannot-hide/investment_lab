from models import Context, Decision
from strategies.strategy import Strategy


class DoNothingStrategy(Strategy):
    """Keep cash as cash — never place or cancel orders."""

    def decide(self, context: Context) -> Decision | None:
        return None

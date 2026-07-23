from models import Context, Decision


class DoNothingStrategy:
    """Keep cash as cash — never place or cancel orders."""

    def decide(self, context: Context) -> Decision | None:
        return None

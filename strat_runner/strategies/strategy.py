from models import Context, Decision


class Strategy:
    """Bar-by-bar trading policy. Override ``decide``."""

    def decide(self, context: Context) -> Decision | None:
        """Return orders / cancels for this bar, or None for no action."""
        return None

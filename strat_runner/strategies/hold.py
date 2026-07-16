from models import Context, Order


class HoldStrategy:
    def decide(self, context: Context) -> list[Order]:
        return []

from dataclasses import dataclass

from engine.money_spawner import MoneySpawner


@dataclass
class Experiment:
    """A strategy plus optional account elements for one simulation outcome."""

    strategy: object
    money_spawner: MoneySpawner | None = None
    name: str | None = None

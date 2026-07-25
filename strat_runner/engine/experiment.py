from dataclasses import dataclass, field

from modifiers.modifier import ExperimentModifier
from strategies.strategy import Strategy


@dataclass
class Experiment:
    """A strategy plus optional account modifiers for one simulation outcome."""

    strategy: Strategy
    modifiers: list[ExperimentModifier] = field(default_factory=list)
    name: str | None = None

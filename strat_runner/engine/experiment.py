from dataclasses import dataclass, field

from indicators.indicator import Indicator
from modifiers.modifier import ExperimentModifier
from strategies.strategy import Strategy


@dataclass
class Experiment:
    """A strategy plus optional indicators and account modifiers."""

    strategy: Strategy
    modifiers: list[ExperimentModifier] = field(default_factory=list)
    indicators: list[Indicator] = field(default_factory=list)
    name: str | None = None

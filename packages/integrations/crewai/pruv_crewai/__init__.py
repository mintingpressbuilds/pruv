"""pruv-crewai — automatic verification for CrewAI agents."""

from .observer import PruvCrewObserver
from .wrapper import CrewAIWrapper

__version__ = "0.1.0"

__all__ = [
    "CrewAIWrapper",
    "PruvCrewObserver",
]

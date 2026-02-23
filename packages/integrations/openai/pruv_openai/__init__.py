"""pruv-openai — automatic verification for OpenAI Agents SDK."""

from .tracing import PruvTraceProcessor
from .wrapper import OpenAIAgentWrapper

__version__ = "0.1.0"

__all__ = [
    "OpenAIAgentWrapper",
    "PruvTraceProcessor",
]

"""pruv-openclaw — automatic verification for OpenClaw agents."""

from .interceptor import PruvActionInterceptor
from .plugin import PruvOpenClawPlugin

__version__ = "0.1.0"

__all__ = [
    "PruvOpenClawPlugin",
    "PruvActionInterceptor",
]

"""pruv — Prove what happened. Full SDK with scanner, wrappers, checkpoints, and cloud sync."""

# Re-export from xycore
from xycore import XYEntry, XYChain, XYReceipt, ThinkingPhase

# Scanner
from .scanner import scan
from .graph import Graph, GraphDiff

# Wrapper
from .wrap import xy_wrap, WrappedResult

# Checkpoints
from .checkpoint import Checkpoint, CheckpointManager

# Approval
from .approval import ApprovalGate

# Cloud
from .cloud import CloudClient, CloudStorage

# Agent
from .client import PruvClient
from .agent import Agent, ActionError
from .decorators import init, verified

# Payment
from .payment import PaymentChain, PaymentReceipt, PaymentVerification

__version__ = "1.0.0"

__all__ = [
    # xycore re-exports
    "XYEntry",
    "XYChain",
    "XYReceipt",
    "ThinkingPhase",
    # Scanner
    "scan",
    "Graph",
    "GraphDiff",
    # Wrapper
    "xy_wrap",
    "WrappedResult",
    # Checkpoints
    "Checkpoint",
    "CheckpointManager",
    # Approval
    "ApprovalGate",
    # Cloud
    "CloudClient",
    "CloudStorage",
    # Agent
    "PruvClient",
    "Agent",
    "ActionError",
    "init",
    "verified",
    # Payment
    "PaymentChain",
    "PaymentReceipt",
    "PaymentVerification",
]

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

# Identity
from .identity import Identity, AgentIdentity, IdentityVerification


class _IdentityProxy:
    """Proxy that initializes Identity on first use."""

    _instance = None

    def register(self, *args, api_key=None, **kwargs):
        if api_key:
            self._instance = Identity(api_key=api_key)
        if not self._instance:
            raise RuntimeError("Call with api_key= on first use")
        return self._instance.register(*args, **kwargs)

    def act(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.act(*args, **kwargs)

    def verify(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.verify(*args, **kwargs)

    def receipt(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.receipt(*args, **kwargs)

    def history(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.history(*args, **kwargs)

    def lookup(self, *args, **kwargs):
        if not self._instance:
            raise RuntimeError("Register an identity first")
        return self._instance.lookup(*args, **kwargs)


identity = _IdentityProxy()

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
    # Identity
    "Identity",
    "AgentIdentity",
    "IdentityVerification",
    "identity",
]

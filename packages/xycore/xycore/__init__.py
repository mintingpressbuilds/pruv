"""xycore — The XY primitive. Zero dependencies. Cryptographic verification for any system."""

from .balance import BalanceProof
from .chain import XYChain
from .crypto import compute_xy, hash_state, verify_chain, verify_entry
from .entry import XYEntry
from .receipt import ThinkingPhase, XYReceipt
from .redact import redact_state
from .signature import generate_keypair, sign_entry, verify_signature
from .storage import LocalStorage

__version__ = "1.0.0"

__all__ = [
    "BalanceProof",
    "XYEntry",
    "XYChain",
    "XYReceipt",
    "ThinkingPhase",
    "hash_state",
    "compute_xy",
    "verify_entry",
    "verify_chain",
    "generate_keypair",
    "sign_entry",
    "verify_signature",
    "redact_state",
    "LocalStorage",
]

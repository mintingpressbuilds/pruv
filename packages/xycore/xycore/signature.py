"""Ed25519 digital signatures for XY entries."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry import XYEntry


def _load_crypto():
    """Lazily load cryptography module."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            PublicFormat,
        )
        return Ed25519PrivateKey, Ed25519PublicKey, Encoding, NoEncryption, PrivateFormat, PublicFormat
    except (ImportError, Exception):
        return None


def _require_crypto():
    result = _load_crypto()
    if result is None:
        raise ImportError(
            "Ed25519 signatures require the 'cryptography' package. "
            "Install with: pip install cryptography"
        )
    return result


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate an Ed25519 keypair.

    Returns (private_key_bytes, public_key_bytes).
    """
    Ed25519PrivateKey, _, Encoding, NoEncryption, PrivateFormat, PublicFormat = _require_crypto()
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    public_bytes = private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    return private_bytes, public_bytes


def sign_entry(entry: "XYEntry", private_key: bytes, signer_id: str | None = None) -> "XYEntry":
    """Sign an entry with an Ed25519 private key.

    Modifies the entry in place and returns it.
    """
    Ed25519PrivateKey, _, Encoding, NoEncryption, _, PublicFormat = _require_crypto()
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    message = f"{entry.x}:{entry.operation}:{entry.y}:{entry.xy}".encode("utf-8")
    sig = key.sign(message)
    entry.signature = base64.b64encode(sig).decode("ascii")
    public_bytes = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    entry.public_key = base64.b64encode(public_bytes).decode("ascii")
    if signer_id is not None:
        entry.signer_id = signer_id
    return entry


def verify_signature(entry: "XYEntry") -> bool:
    """Verify the Ed25519 signature on an entry."""
    result = _load_crypto()
    if result is None:
        raise ImportError(
            "Ed25519 signatures require the 'cryptography' package. "
            "Install with: pip install cryptography"
        )
    _, Ed25519PublicKey, *_ = result
    if entry.signature is None or entry.public_key is None:
        return False
    try:
        pub_bytes = base64.b64decode(entry.public_key)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        sig = base64.b64decode(entry.signature)
        message = f"{entry.x}:{entry.operation}:{entry.y}:{entry.xy}".encode("utf-8")
        pub_key.verify(sig, message)
        return True
    except Exception:
        return False

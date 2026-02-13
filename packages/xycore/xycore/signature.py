"""Ed25519 digital signatures for XY entries.

Uses PyNaCl (libsodium) as the primary backend, with fallback to
the cryptography package if PyNaCl is unavailable.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry import XYEntry


def _load_nacl():
    """Try to load PyNaCl (libsodium)."""
    try:
        from nacl.signing import SigningKey, VerifyKey
        from nacl.exceptions import BadSignatureError
        return SigningKey, VerifyKey, BadSignatureError
    except ImportError:
        return None


def _load_crypto():
    """Try to load cryptography package as fallback."""
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


def _get_backend():
    """Get the best available Ed25519 backend."""
    nacl = _load_nacl()
    if nacl is not None:
        return "nacl", nacl
    crypto = _load_crypto()
    if crypto is not None:
        return "cryptography", crypto
    return None, None


def _require_backend():
    name, backend = _get_backend()
    if backend is None:
        raise ImportError(
            "Ed25519 signatures require 'PyNaCl' or 'cryptography'. "
            "Install with: pip install PyNaCl"
        )
    return name, backend


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate an Ed25519 keypair.

    Returns (private_key_bytes, public_key_bytes) — both 32 bytes.
    """
    name, backend = _require_backend()

    if name == "nacl":
        SigningKey = backend[0]
        sk = SigningKey.generate()
        return bytes(sk), bytes(sk.verify_key)

    Ed25519PrivateKey, _, Encoding, NoEncryption, PrivateFormat, PublicFormat = backend
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
    name, backend = _require_backend()
    message = f"{entry.x}:{entry.operation}:{entry.y}:{entry.xy}".encode("utf-8")

    if name == "nacl":
        SigningKey = backend[0]
        sk = SigningKey(private_key)
        signed = sk.sign(message)
        sig = signed.signature
        pub = bytes(sk.verify_key)
    else:
        Ed25519PrivateKey, _, Encoding, _, _, PublicFormat = backend
        key = Ed25519PrivateKey.from_private_bytes(private_key)
        sig = key.sign(message)
        pub = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    entry.signature = base64.b64encode(sig).decode("ascii")
    entry.public_key = base64.b64encode(pub).decode("ascii")
    if signer_id is not None:
        entry.signer_id = signer_id
    return entry


def verify_signature(entry: "XYEntry") -> bool:
    """Verify the Ed25519 signature on an entry."""
    name, backend = _get_backend()
    if backend is None:
        raise ImportError(
            "Ed25519 signatures require 'PyNaCl' or 'cryptography'. "
            "Install with: pip install PyNaCl"
        )
    if entry.signature is None or entry.public_key is None:
        return False

    message = f"{entry.x}:{entry.operation}:{entry.y}:{entry.xy}".encode("utf-8")

    try:
        sig = base64.b64decode(entry.signature)
        pub_bytes = base64.b64decode(entry.public_key)

        if name == "nacl":
            VerifyKey = backend[1]
            vk = VerifyKey(pub_bytes)
            vk.verify(message, sig)
            return True
        else:
            _, Ed25519PublicKey, *_ = backend
            pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig, message)
            return True
    except Exception:
        return False

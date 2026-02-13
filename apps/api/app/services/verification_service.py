"""Verification service for the pruv API.

Provides chain verification, certificate generation,
and verification history tracking.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationResult:
    """Result of a chain verification."""
    id: str
    chain_id: str
    verified: bool
    entries_checked: int
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    duration_ms: float
    verified_at: float = field(default_factory=time.time)
    certificate_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chain_id": self.chain_id,
            "verified": self.verified,
            "entries_checked": self.entries_checked,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_ms": round(self.duration_ms, 2),
            "verified_at": self.verified_at,
            "certificate_id": self.certificate_id,
        }


@dataclass
class VerificationCertificate:
    """A verification certificate for a chain."""
    id: str
    chain_id: str
    chain_name: str
    verification_id: str
    entries_count: int
    root_xy: str
    head_xy: str
    verified: bool
    issued_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    share_token: str | None = None

    def __post_init__(self) -> None:
        if self.expires_at == 0.0:
            self.expires_at = self.issued_at + (365 * 24 * 3600)  # 1 year

    @property
    def fingerprint(self) -> str:
        """Compute certificate fingerprint."""
        content = f"{self.chain_id}:{self.root_xy}:{self.head_xy}:{self.entries_count}:{self.issued_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chain_id": self.chain_id,
            "chain_name": self.chain_name,
            "verification_id": self.verification_id,
            "entries_count": self.entries_count,
            "root_xy": self.root_xy,
            "head_xy": self.head_xy,
            "verified": self.verified,
            "fingerprint": self.fingerprint,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "is_expired": self.is_expired,
            "share_token": self.share_token,
        }


class VerificationService:
    """Service for chain verification and certificate management."""

    def __init__(self) -> None:
        self._results: dict[str, VerificationResult] = {}
        self._certificates: dict[str, VerificationCertificate] = {}
        self._shared_certificates: dict[str, str] = {}  # token -> cert_id

    def verify_chain(
        self,
        chain_id: str,
        entries: list[dict[str, Any]],
    ) -> VerificationResult:
        """Verify a chain's integrity."""
        start = time.monotonic()
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        if not entries:
            errors.append({
                "type": "empty_chain",
                "message": "Chain has no entries to verify",
            })
            duration = (time.monotonic() - start) * 1000
            result = VerificationResult(
                id=f"vrf_{uuid.uuid4().hex[:24]}",
                chain_id=chain_id,
                verified=False,
                entries_checked=0,
                errors=errors,
                warnings=warnings,
                duration_ms=duration,
            )
            self._results[result.id] = result
            return result

        # Check first entry
        first = entries[0]
        if first.get("x") != "GENESIS":
            errors.append({
                "type": "invalid_genesis",
                "index": 0,
                "message": "First entry x must be 'GENESIS'",
                "actual": first.get("x"),
            })

        # Check chain rule: Entry[N].x == Entry[N-1].y
        for i in range(1, len(entries)):
            prev_y = entries[i - 1].get("y")
            curr_x = entries[i].get("x")

            if curr_x != prev_y:
                errors.append({
                    "type": "chain_break",
                    "index": i,
                    "message": f"Entry[{i}].x != Entry[{i-1}].y",
                    "expected": prev_y,
                    "actual": curr_x,
                })

        # Check for missing XY hashes
        for i, entry in enumerate(entries):
            if not entry.get("xy"):
                warnings.append({
                    "type": "missing_xy",
                    "index": i,
                    "message": f"Entry[{i}] has no XY proof hash",
                })

        # Check timestamp ordering
        for i in range(1, len(entries)):
            prev_ts = entries[i - 1].get("timestamp", 0)
            curr_ts = entries[i].get("timestamp", 0)
            if curr_ts < prev_ts:
                warnings.append({
                    "type": "timestamp_order",
                    "index": i,
                    "message": f"Entry[{i}] timestamp is before Entry[{i-1}]",
                })

        # Check for duplicate XY hashes
        xy_set: set[str] = set()
        for i, entry in enumerate(entries):
            xy = entry.get("xy", "")
            if xy and xy in xy_set:
                warnings.append({
                    "type": "duplicate_xy",
                    "index": i,
                    "message": f"Entry[{i}] has duplicate XY hash",
                })
            xy_set.add(xy)

        duration = (time.monotonic() - start) * 1000
        verified = len(errors) == 0

        result = VerificationResult(
            id=f"vrf_{uuid.uuid4().hex[:24]}",
            chain_id=chain_id,
            verified=verified,
            entries_checked=len(entries),
            errors=errors,
            warnings=warnings,
            duration_ms=duration,
        )
        self._results[result.id] = result
        return result

    def issue_certificate(
        self,
        verification_id: str,
        chain_id: str,
        chain_name: str,
        entries: list[dict[str, Any]],
    ) -> VerificationCertificate | None:
        """Issue a verification certificate for a verified chain."""
        result = self._results.get(verification_id)
        if not result or not result.verified:
            return None

        root_xy = entries[0].get("xy", "") if entries else ""
        head_xy = entries[-1].get("xy", "") if entries else ""

        cert = VerificationCertificate(
            id=f"cert_{uuid.uuid4().hex[:24]}",
            chain_id=chain_id,
            chain_name=chain_name,
            verification_id=verification_id,
            entries_count=len(entries),
            root_xy=root_xy,
            head_xy=head_xy,
            verified=True,
        )
        cert.certificate_id = cert.id
        result.certificate_id = cert.id
        self._certificates[cert.id] = cert
        return cert

    def get_certificate(self, certificate_id: str) -> VerificationCertificate | None:
        """Get a certificate by ID."""
        return self._certificates.get(certificate_id)

    def share_certificate(self, certificate_id: str) -> str | None:
        """Generate a share token for a certificate."""
        cert = self._certificates.get(certificate_id)
        if not cert:
            return None

        token = uuid.uuid4().hex[:16]
        cert.share_token = token
        self._shared_certificates[token] = certificate_id
        return token

    def get_shared_certificate(self, token: str) -> VerificationCertificate | None:
        """Get a certificate by share token."""
        cert_id = self._shared_certificates.get(token)
        if not cert_id:
            return None
        return self._certificates.get(cert_id)

    def get_verification_history(
        self,
        chain_id: str,
        limit: int = 20,
    ) -> list[VerificationResult]:
        """Get verification history for a chain."""
        results = [
            r for r in self._results.values()
            if r.chain_id == chain_id
        ]
        results.sort(key=lambda r: r.verified_at, reverse=True)
        return results[:limit]

    def get_certificates_for_chain(
        self,
        chain_id: str,
    ) -> list[VerificationCertificate]:
        """Get all certificates for a chain."""
        return [
            c for c in self._certificates.values()
            if c.chain_id == chain_id
        ]

    def revoke_certificate(self, certificate_id: str) -> bool:
        """Revoke a verification certificate."""
        cert = self._certificates.get(certificate_id)
        if not cert:
            return False

        # Remove share token if exists
        if cert.share_token and cert.share_token in self._shared_certificates:
            del self._shared_certificates[cert.share_token]

        del self._certificates[certificate_id]
        return True

    def generate_badge_svg(
        self,
        certificate_id: str,
        style: str = "flat",
    ) -> str | None:
        """Generate an SVG verification badge."""
        cert = self._certificates.get(certificate_id)
        if not cert:
            return None

        status = "verified" if cert.verified and not cert.is_expired else "unverified"
        color = "#10b981" if status == "verified" else "#ef4444"
        label_width = 48
        status_width = 62 if status == "verified" else 72
        total_width = label_width + status_width

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="pruv: {status}">
  <title>pruv: {status}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{status_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="{label_width/2}" y="15" fill="#010101" fill-opacity=".3">pruv</text>
    <text x="{label_width/2}" y="14">pruv</text>
    <text aria-hidden="true" x="{label_width + status_width/2}" y="15" fill="#010101" fill-opacity=".3">{status}</text>
    <text x="{label_width + status_width/2}" y="14">{status}</text>
  </g>
</svg>"""


# Global service instance
_verification_service: VerificationService | None = None


def get_verification_service() -> VerificationService:
    """Get or create the global verification service."""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service

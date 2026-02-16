"""Scan service — verify chain data from uploaded JSON files or chain IDs."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from .chain_service import chain_service


class ScanService:
    """Handles scan requests: parses uploaded chain JSON and verifies integrity."""

    def __init__(self) -> None:
        self._scans: dict[str, dict[str, Any]] = {}

    def scan_file(
        self,
        file_content: bytes,
        chain_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Scan an uploaded JSON file containing chain data."""
        scan_id = f"scan_{uuid.uuid4().hex[:24]}"
        started_at = time.time()
        opts = options or {}
        deep_verify = opts.get("deep_verify", True)
        check_signatures = opts.get("check_signatures", True)
        findings: list[dict[str, Any]] = []

        # Parse the uploaded JSON
        try:
            data = json.loads(file_content)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return self._build_result(
                scan_id=scan_id,
                status="failed",
                chain_id=chain_id,
                started_at=started_at,
                findings=[{
                    "severity": "critical",
                    "type": "parse_error",
                    "message": f"Invalid JSON: {exc}",
                }],
            )

        # Extract entries from various formats
        entries = self._extract_entries(data)
        if not entries:
            return self._build_result(
                scan_id=scan_id,
                status="failed",
                chain_id=chain_id,
                started_at=started_at,
                findings=[{
                    "severity": "critical",
                    "type": "no_entries",
                    "message": "No chain entries found in uploaded file",
                }],
            )

        # Check genesis
        first = entries[0]
        if first.get("x") != "GENESIS":
            findings.append({
                "severity": "critical",
                "type": "invalid_genesis",
                "message": "First entry x must be 'GENESIS'",
                "entry_index": 0,
            })

        # Check chain rule
        for i in range(1, len(entries)):
            prev_y = entries[i - 1].get("y")
            curr_x = entries[i].get("x")
            if curr_x != prev_y:
                findings.append({
                    "severity": "critical",
                    "type": "chain_break",
                    "message": f"Entry[{i}].x != Entry[{i-1}].y — chain is broken",
                    "entry_index": i,
                    "details": {"expected": prev_y, "actual": curr_x},
                })

        if deep_verify:
            # Check XY proof hashes
            for i, entry in enumerate(entries):
                if not entry.get("xy"):
                    findings.append({
                        "severity": "warning",
                        "type": "missing_xy",
                        "message": f"Entry[{i}] has no XY proof hash",
                        "entry_index": i,
                    })

            # Check timestamp ordering
            for i in range(1, len(entries)):
                prev_ts = entries[i - 1].get("timestamp", 0)
                curr_ts = entries[i].get("timestamp", 0)
                if curr_ts < prev_ts:
                    findings.append({
                        "severity": "warning",
                        "type": "timestamp_order",
                        "message": f"Entry[{i}] timestamp precedes Entry[{i-1}]",
                        "entry_index": i,
                    })

        if check_signatures:
            for i, entry in enumerate(entries):
                if entry.get("signature") and not entry.get("public_key"):
                    findings.append({
                        "severity": "warning",
                        "type": "missing_public_key",
                        "message": f"Entry[{i}] has signature but no public key",
                        "entry_index": i,
                    })

        has_critical = any(f["severity"] == "critical" for f in findings)
        if not has_critical and not findings:
            findings.append({
                "severity": "info",
                "type": "chain_valid",
                "message": f"Chain integrity verified — {len(entries)} entries valid",
            })

        return self._build_result(
            scan_id=scan_id,
            status="completed",
            chain_id=chain_id,
            started_at=started_at,
            findings=findings,
        )

    def scan_chain_id(
        self,
        chain_id: str,
        user_id: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Scan an existing chain by its ID."""
        scan_id = f"scan_{uuid.uuid4().hex[:24]}"
        started_at = time.time()

        chain = chain_service.get_chain(chain_id, user_id)
        if not chain:
            return self._build_result(
                scan_id=scan_id,
                status="failed",
                chain_id=chain_id,
                started_at=started_at,
                findings=[{
                    "severity": "critical",
                    "type": "chain_not_found",
                    "message": f"Chain '{chain_id}' not found",
                }],
            )

        entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
        if not entries:
            return self._build_result(
                scan_id=scan_id,
                status="completed",
                chain_id=chain_id,
                started_at=started_at,
                findings=[{
                    "severity": "warning",
                    "type": "empty_chain",
                    "message": "Chain has no entries",
                }],
            )

        # Reuse file-based scan logic by converting entries to bytes
        import json as _json
        content = _json.dumps({"entries": entries}).encode()
        result = self.scan_file(content, chain_id=chain_id, options=options)
        result["id"] = scan_id  # keep this scan's own ID
        return result

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        """Retrieve a previous scan result."""
        return self._scans.get(scan_id)

    def _extract_entries(self, data: Any) -> list[dict[str, Any]]:
        """Extract entries list from various JSON structures."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "entries" in data:
                return data["entries"]
            if "chain" in data and isinstance(data["chain"], dict):
                return data["chain"].get("entries", [])
        return []

    def _build_result(
        self,
        *,
        scan_id: str,
        status: str,
        chain_id: str | None,
        started_at: float,
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        from datetime import datetime, timezone

        result = {
            "id": scan_id,
            "status": status,
            "chain_id": chain_id,
            "started_at": datetime.fromtimestamp(started_at, tz=timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings,
            "receipt_id": None,
        }
        self._scans[scan_id] = result
        return result


scan_service = ScanService()

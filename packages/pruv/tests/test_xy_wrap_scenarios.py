"""Five targeted integration tests for xy_wrap.

1. File operations: create 3, modify 1, delete 1 — verify before/after hashes
2. HTTP calls: 3 URLs — verify method, URL, status code
3. Partial failure: 4 of 6 steps succeed, then exception
4. Cloud sync: test API key — verify chain uploaded to API
5. Approval gate: file.write gated — verify pause/resume on webhook
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xycore import XYChain
from pruv import xy_wrap, WrappedResult
from pruv.wrap.observers import FileObserver, APIObserver
from pruv.approval.gate import ApprovalGate, ApprovalResponse
from pruv.cloud.client import CloudClient


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FILE OPERATIONS — create 3, modify 1, delete 1
# ═══════════════════════════════════════════════════════════════════════════════


class TestFileOperationsFiveActions:
    """Wrap a function that creates 3 files, modifies 1 existing, deletes 1.

    Verify the receipt captures all 5 file operations with correct
    before and after hashes.
    """

    def test_five_file_ops_with_before_after_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-create 1 existing file to modify later
            existing = Path(tmpdir) / "existing.txt"
            existing.write_text("original content")

            def file_agent(task, file_observer=None):
                """Agent that creates 3 files, modifies 1, deletes 1."""
                # Create 3 new files
                f1 = Path(tmpdir) / "report.json"
                f1.write_text(json.dumps({"status": "ok"}))
                if file_observer:
                    file_observer.file_write(str(f1), size=f1.stat().st_size)

                f2 = Path(tmpdir) / "data.csv"
                f2.write_text("col_a,col_b\n1,2\n3,4\n")
                if file_observer:
                    file_observer.file_write(str(f2), size=f2.stat().st_size)

                f3 = Path(tmpdir) / "notes.md"
                f3.write_text("# Notes\n- item 1\n")
                if file_observer:
                    file_observer.file_write(str(f3), size=f3.stat().st_size)

                # Modify the existing file
                existing.write_text("modified content")
                if file_observer:
                    file_observer.file_write(str(existing), size=existing.stat().st_size)

                # Delete one of the new files
                f2.unlink()
                if file_observer:
                    file_observer.file_delete(str(f2))

                return {
                    "created": [str(f1), str(f2), str(f3)],
                    "modified": [str(existing)],
                    "deleted": [str(f2)],
                }

            wrapped = xy_wrap(file_agent, scan_dir=tmpdir)
            result = wrapped("five file ops")

            # ── Result structure ──
            assert isinstance(result, WrappedResult)
            assert result.output is not None

            # ── Chain length: start + 5 file ops + complete = 7 ──
            assert result.chain.length == 7

            # ── Chain is cryptographically valid ──
            assert result.verified

            # ── Receipt captures all 7 entries ──
            assert result.receipt.entry_count == 7
            assert result.receipt.all_verified
            assert result.receipt.task == "five file ops"

            # ── Observer tracked exactly 5 operations ──
            obs = result.observer
            assert isinstance(obs, FileObserver)
            assert obs.count == 5
            assert len(obs.files_written) == 4   # 3 creates + 1 modify
            assert len(obs.files_deleted) == 1

            # ── Chain operations in correct order ──
            ops = [e.operation for e in result.chain.entries]
            assert ops == [
                "start",
                "file.write", "file.write", "file.write",  # 3 creates
                "file.write",   # modify
                "file.delete",  # delete
                "complete",
            ]

            # ── Before/after graph hashes differ (files changed) ──
            assert result.graph_before is not None
            assert result.graph_after is not None
            assert result.graph_before.hash != result.graph_after.hash

            # ── Diff shows net file changes ──
            diff = result.diff
            assert diff is not None
            assert diff.total_changes > 0

            # ── Chain rule: Entry[N].x == Entry[N-1].y ──
            entries = result.chain.entries
            assert entries[0].x == "GENESIS"
            for i in range(1, len(entries)):
                assert entries[i].x == entries[i - 1].y, (
                    f"Chain break at {i}: "
                    f"entry[{i}].x != entry[{i-1}].y"
                )

            # ── Every entry has a valid xy_ proof hash ──
            for entry in entries:
                assert entry.xy.startswith("xy_")

            # ── File paths recorded in y_state.args ──
            for entry in entries[1:6]:  # The 5 file operation entries
                assert "path" in entry.y_state["args"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HTTP CALLS — 3 URLs with method, URL, status code
# ═══════════════════════════════════════════════════════════════════════════════


class TestHTTPCallsThreeURLs:
    """Wrap a function that makes 3 HTTP calls to different URLs.

    Verify the receipt logs all 3 requests with method, URL, and status code.
    """

    def test_three_http_calls_logged(self):
        def api_agent(task, api_observer=None):
            """Agent that makes 3 HTTP calls (simulated via observer)."""
            responses = []

            # Call 1: GET users
            responses.append({"users": ["alice", "bob"]})
            if api_observer:
                api_observer.api_call(
                    "GET", "https://api.example.com/users", 200, 0.05,
                )

            # Call 2: POST order
            responses.append({"order_id": "ord_001"})
            if api_observer:
                api_observer.api_call(
                    "POST", "https://api.example.com/orders", 201, 0.12,
                )

            # Call 3: DELETE order
            responses.append({"deleted": True})
            if api_observer:
                api_observer.api_call(
                    "DELETE", "https://api.example.com/orders/123", 204, 0.03,
                )

            return responses

        wrapped = xy_wrap(api_agent)
        result = wrapped("three http calls")

        # ── Result structure ──
        assert isinstance(result, WrappedResult)
        assert len(result.output) == 3

        # ── Chain length: start + 3 api calls + complete = 5 ──
        assert result.chain.length == 5
        assert result.verified

        # ── Receipt ──
        assert result.receipt.entry_count == 5
        assert result.receipt.all_verified

        # ── Observer tracked 3 requests ──
        obs = result.observer
        assert isinstance(obs, APIObserver)
        assert obs.count == 3
        assert len(obs.requests) == 3

        # ── Verify each request's method, URL, status code ──
        r1, r2, r3 = obs.requests
        assert r1["method"] == "GET"
        assert r1["url"] == "https://api.example.com/users"
        assert r1["status_code"] == 200

        assert r2["method"] == "POST"
        assert r2["url"] == "https://api.example.com/orders"
        assert r2["status_code"] == 201

        assert r3["method"] == "DELETE"
        assert r3["url"] == "https://api.example.com/orders/123"
        assert r3["status_code"] == 204

        # ── Chain operations match API methods ──
        ops = [e.operation for e in result.chain.entries]
        assert ops == ["start", "api.get", "api.post", "api.delete", "complete"]

        # ── Each API entry's y_state.args includes url and status_code ──
        for entry in result.chain.entries[1:4]:
            assert "url" in entry.y_state["args"]
            assert "status_code" in entry.y_state["args"]

        # ── API summary in completion entry ──
        complete = result.chain.entries[-1]
        assert "api_summary" in complete.y_state
        summary = complete.y_state["api_summary"]
        assert summary["total_requests"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PARTIAL FAILURE — step 4 of 6, then exception
# ═══════════════════════════════════════════════════════════════════════════════


class TestPartialFailureFourOfSix:
    """Wrap a function that succeeds on step 4 of 6 then raises.

    Verify: 4 successful entries + 1 failed entry in the chain.
    """

    def test_four_steps_then_crash(self):
        def six_step_agent(task, file_observer=None, api_observer=None):
            """Agent with 6 planned steps. Crashes on step 5."""
            # Step 1: Read config
            if file_observer:
                file_observer.file_read("/etc/app/config.yaml", size=512)

            # Step 2: Call health check API
            if api_observer:
                api_observer.api_call("GET", "https://svc.internal/health", 200, 0.02)

            # Step 3: Write temp file
            if file_observer:
                file_observer.file_write("/tmp/staging/batch.json", size=2048)

            # Step 4: Call processing API (last successful step)
            if api_observer:
                api_observer.api_call("POST", "https://svc.internal/process", 200, 1.5)

            # Step 5: CRASH — simulates a real failure
            raise ConnectionError("upstream service reset connection during upload")

            # Step 6: (never reached)
            # if file_observer:
            #     file_observer.file_write("/data/output/result.json", size=4096)

        wrapped = xy_wrap(six_step_agent)
        result = wrapped("six step pipeline")

        # ── Output is None because the function failed ──
        assert result.output is None

        # ── Chain: start + 4 successful ops + complete(failed) = 6 ──
        assert result.chain.length == 6

        # ── Chain integrity is still valid (failure is recorded, not corrupted) ──
        assert result.verified

        # ── 4 intermediate entries have status=success ──
        intermediate = result.chain.entries[1:5]  # entries 1-4
        assert len(intermediate) == 4
        for entry in intermediate:
            assert entry.status == "success", (
                f"entry {entry.index} ({entry.operation}) should be success, "
                f"got {entry.status}"
            )

        # ── Complete entry has status=failed ──
        complete = result.chain.entries[-1]
        assert complete.operation == "complete"
        assert complete.status == "failed"

        # ── Error message captured ──
        assert "upstream service reset connection" in complete.y_state["error"]

        # ── Operations in order ──
        ops = [e.operation for e in result.chain.entries]
        assert ops == [
            "start",
            "file.read",
            "api.get",
            "file.write",
            "api.post",
            "complete",
        ]

        # ── Receipt entry count reflects all entries including failure ──
        assert result.receipt.entry_count == 6

        # ── Chain rule preserved even through failure ──
        entries = result.chain.entries
        assert entries[0].x == "GENESIS"
        for i in range(1, len(entries)):
            assert entries[i].x == entries[i - 1].y

        # ── Receipt all_verified reflects chain integrity (True),
        #    not function success. The failure is recorded in the
        #    complete entry's status field. ──
        assert result.receipt.all_verified


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CLOUD SYNC — test API key, verify chain appears in API
# ═══════════════════════════════════════════════════════════════════════════════


class TestCloudSyncWithTestKey:
    """Wrap a function with cloud sync using a test API key.

    Verify the chain appears in the API after the wrapped function completes.
    """

    def test_chain_uploaded_to_api(self):
        requests_made = []

        async def mock_request(method, path, body=None):
            requests_made.append({"method": method, "path": path, "body": body})
            if path == "/v1/chains" and method == "POST":
                return {"id": "cloud_chain_001", "name": body["name"]}
            if "/entries/batch" in path:
                return {"entries": [], "total": 0}
            return {}

        def deploy_agent(task, file_observer=None):
            """Agent that does work then syncs to cloud."""
            if file_observer:
                file_observer.file_write("/deploy/app.tar.gz", size=5_000_000)
                file_observer.file_write("/deploy/manifest.json", size=256)
            return {"deployed": True, "version": "2.1.0"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch CloudClient._request to capture API calls
            with patch.object(CloudClient, "_request", side_effect=mock_request):
                # Patch queue_dir so it doesn't create dirs in real filesystem
                with patch.object(
                    CloudClient, "__init__",
                    lambda self, **kw: (
                        setattr(self, "api_key", kw.get("api_key", "")),
                        setattr(self, "base_url", kw.get("base_url", "https://api.pruv.dev").rstrip("/")),
                        setattr(self, "queue_dir", Path(tmpdir) / "queue"),
                        setattr(self, "max_retries", 3),
                        setattr(self, "_offline_queue", []),
                        (Path(tmpdir) / "queue").mkdir(parents=True, exist_ok=True),
                    ) and None,
                ):
                    wrapped = xy_wrap(deploy_agent, api_key="pv_test_cloud_sync_abc123")
                    result = wrapped("deploy v2.1.0")

        # ── Function result intact ──
        assert result.output == {"deployed": True, "version": "2.1.0"}
        assert result.verified

        # ── Cloud sync made 2 requests ──
        assert len(requests_made) == 2

        # ── Request 1: POST /v1/chains ──
        create_req = requests_made[0]
        assert create_req["method"] == "POST"
        assert create_req["path"] == "/v1/chains"
        assert create_req["body"]["name"] == "deploy_agent"
        assert create_req["body"]["auto_redact"] is True

        # ── Request 2: POST /v1/chains/{id}/entries/batch ──
        batch_req = requests_made[1]
        assert batch_req["method"] == "POST"
        assert "/entries/batch" in batch_req["path"]
        assert "cloud_chain_001" in batch_req["path"]

        # ── Batch includes all chain entries ──
        entries = batch_req["body"]["entries"]
        assert len(entries) == result.chain.length  # start + 2 file.write + complete = 4

        # ── Entry operations match chain ──
        assert entries[0]["operation"] == "start"
        assert entries[1]["operation"] == "file.write"
        assert entries[2]["operation"] == "file.write"
        assert entries[-1]["operation"] == "complete"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. APPROVAL GATE — file.write pauses until webhook approves
# ═══════════════════════════════════════════════════════════════════════════════


class TestApprovalGateFileWrite:
    """Wrap a function with an approval gate on file.write.

    Verify the function pauses when it attempts a file write and resumes
    only after the approval webhook returns approved.
    """

    def test_file_write_gated_by_approval(self):
        webhook_calls = []

        async def gated_deploy(task, file_observer=None, approval_gate=None):
            """Agent that reads freely but needs approval for writes."""
            # Step 1: Read config — no approval needed
            if file_observer:
                file_observer.file_read("/etc/deploy/config.yaml", size=400)

            # Step 2: file.write — requires approval via gate
            if approval_gate:
                response = await approval_gate.gate(
                    chain_id="test_chain",
                    entry_index=2,
                    operation="file.write",
                    x_state={"current_version": "2.0"},
                    proposed_y_state={"new_version": "2.1"},
                )
                webhook_calls.append(response)
                if not response.is_approved:
                    raise PermissionError(f"Write denied: {response.reason}")

            if file_observer:
                file_observer.file_write("/deploy/app.tar.gz", size=5_000_000)

            # Step 3: Another read — no approval needed
            if file_observer:
                file_observer.file_read("/deploy/app.tar.gz", size=5_000_000)

            return {"deployed": True}

        # Mock httpx to return "approved" from the webhook
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "approved",
                "approved_by": "ops-lead@company.com",
                "reason": "deployment approved for production",
            }
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            wrapped = xy_wrap(
                gated_deploy,
                approval_webhook="https://approvals.company.com/hook",
                approval_operations=["file.write"],
            )
            result = asyncio.run(wrapped("deploy with approval"))

            # ── Webhook was called exactly once (for file.write, not file.read) ──
            mock_instance.post.assert_called_once()

            # ── Webhook payload contains the operation and states ──
            call_kwargs = mock_instance.post.call_args[1]
            payload = call_kwargs["json"]
            assert payload["operation"] == "file.write"
            assert payload["chain_id"] == "test_chain"
            assert payload["x_state"] == {"current_version": "2.0"}
            assert payload["proposed_y_state"] == {"new_version": "2.1"}

        # ── Approval was received and function continued ──
        assert len(webhook_calls) == 1
        assert webhook_calls[0].is_approved
        assert webhook_calls[0].approved_by == "ops-lead@company.com"

        # ── Function completed successfully after approval ──
        assert result.output == {"deployed": True}
        assert result.verified

        # ── Chain: start + file.read + file.write + file.read + complete = 5 ──
        assert result.chain.length == 5

        ops = [e.operation for e in result.chain.entries]
        assert ops == ["start", "file.read", "file.write", "file.read", "complete"]

        # ── Receipt intact ──
        assert result.receipt.all_verified
        assert result.receipt.entry_count == 5

    def test_file_write_denied_stops_execution(self):
        """When the approval webhook denies, the function raises and the chain
        records the failure."""

        async def gated_agent(task, file_observer=None, approval_gate=None):
            if file_observer:
                file_observer.file_read("/etc/config.yaml", size=100)

            if approval_gate:
                response = await approval_gate.gate(
                    chain_id="denied_chain",
                    entry_index=1,
                    operation="file.write",
                )
                if not response.is_approved:
                    raise PermissionError(f"Denied: {response.reason}")

            if file_observer:
                file_observer.file_write("/deploy/app.tar.gz", size=1000)
            return "should not reach here"

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "denied",
                "reason": "deployment freeze in effect",
            }
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            wrapped = xy_wrap(
                gated_agent,
                approval_webhook="https://approvals.company.com/hook",
                approval_operations=["file.write"],
            )
            result = asyncio.run(wrapped("denied deploy"))

        # ── Function was stopped by denial ──
        assert result.output is None

        # ── Chain records the read + failure ──
        assert result.chain.length == 3  # start + file.read + complete(failed)
        assert result.chain.entries[-1].status == "failed"
        assert "deployment freeze" in result.chain.entries[-1].y_state["error"]

        # ── Chain integrity still valid ──
        assert result.verified

    def test_read_operations_skip_gate(self):
        """file.read should NOT trigger the approval gate."""

        gate_invocations = []

        async def read_only_agent(task, file_observer=None, approval_gate=None):
            # Check that gate auto-approves reads
            if approval_gate:
                resp = await approval_gate.gate("c1", 0, "file.read")
                gate_invocations.append(resp)
                assert resp.is_approved
                assert resp.reason == "no-approval-required"

            if file_observer:
                file_observer.file_read("/data/report.csv", size=1000)

            return "read complete"

        # No httpx mock needed — gate.gate auto-approves non-matching operations
        wrapped = xy_wrap(
            read_only_agent,
            approval_webhook="https://approvals.company.com/hook",
            approval_operations=["file.write"],
        )
        result = asyncio.run(wrapped("read only"))

        assert result.output == "read complete"
        assert result.verified
        assert len(gate_invocations) == 1
        assert gate_invocations[0].reason == "no-approval-required"

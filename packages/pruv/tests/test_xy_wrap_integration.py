"""Integration tests for xy_wrap with real agent scenarios.

Tests:
1. Wrap a function that modifies files — verify the receipt captures every change
2. Wrap a function that makes HTTP calls — verify the receipt logs every call
3. Wrap a function that fails halfway — verify the chain records the failure
4. Test cloud sync — wrap an agent with api_key, verify the chain appears in the dashboard
5. Test approval gate — wrap an agent with approval webhook, verify it pauses and waits
"""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xycore import XYChain
from pruv import xy_wrap, WrappedResult, Graph
from pruv.wrap.observers import FileObserver, APIObserver, ActionObserver
from pruv.approval.gate import ApprovalGate, ApprovalResponse
from pruv.cloud.client import CloudClient


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FILE MODIFICATION AGENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestFileModificationAgent:
    """Wrap a function that modifies files. Verify the receipt captures every change."""

    def test_file_writes_tracked_by_observer(self):
        """A function that writes files should produce chain entries for each write."""

        def file_agent(task, file_observer=None):
            """Agent that creates and modifies files."""
            tmpdir = tempfile.mkdtemp()
            # Write file 1
            path1 = os.path.join(tmpdir, "config.json")
            with open(path1, "w") as f:
                json.dump({"key": "value"}, f)
            if file_observer:
                file_observer.file_write(path1, size=len('{"key": "value"}'))

            # Write file 2
            path2 = os.path.join(tmpdir, "data.csv")
            with open(path2, "w") as f:
                f.write("a,b,c\n1,2,3\n")
            if file_observer:
                file_observer.file_write(path2, size=len("a,b,c\n1,2,3\n"))

            # Read file 1 back
            with open(path1) as f:
                content = f.read()
            if file_observer:
                file_observer.file_read(path1, size=len(content))

            # Delete file 2
            os.remove(path2)
            if file_observer:
                file_observer.file_delete(path2)

            return {"created": [path1], "deleted": [path2]}

        wrapped = xy_wrap(file_agent)
        result = wrapped("modify files")

        assert isinstance(result, WrappedResult)
        assert result.output is not None
        assert result.output["created"]
        assert result.output["deleted"]

        # Chain should have: start + 4 observer entries + complete = 6 entries
        assert result.chain.length == 6

        # Verify the chain is cryptographically valid
        assert result.verified

        # Check receipt
        assert result.receipt.all_verified
        assert result.receipt.entry_count == 6
        assert result.receipt.task == "modify files"

        # Check observer captured all actions
        assert result.observer is not None
        assert isinstance(result.observer, FileObserver)
        assert result.observer.count == 4
        assert len(result.observer.files_written) == 2
        assert len(result.observer.files_read) == 1
        assert len(result.observer.files_deleted) == 1

        # Verify individual chain entries
        ops = [e.operation for e in result.chain.entries]
        assert ops[0] == "start"
        assert ops[1] == "file.write"
        assert ops[2] == "file.write"
        assert ops[3] == "file.read"
        assert ops[4] == "file.delete"
        assert ops[-1] == "complete"

    def test_file_agent_with_scan_dir(self):
        """File agent with scan_dir should capture before/after graph hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial files
            (Path(tmpdir) / "existing.txt").write_text("hello")

            def file_agent(task, file_observer=None):
                (Path(tmpdir) / "new_file.py").write_text("x = 1\n")
                if file_observer:
                    file_observer.file_write(str(Path(tmpdir) / "new_file.py"), size=6)
                return "created new_file.py"

            wrapped = xy_wrap(file_agent, scan_dir=tmpdir)
            result = wrapped("add file")

            assert result.graph_before is not None
            assert result.graph_after is not None
            assert result.graph_before.hash != result.graph_after.hash

            diff = result.diff
            assert diff is not None
            assert diff.total_changes > 0
            assert any(c.path == "new_file.py" for c in diff.added)

    def test_file_agent_no_observer_param(self):
        """Function without file_observer param still works, just no intermediate entries."""

        def simple_agent(task):
            return f"done: {task}"

        wrapped = xy_wrap(simple_agent)
        result = wrapped("simple task")

        assert result.output == "done: simple task"
        assert result.chain.length == 2  # start + complete only
        assert result.verified


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HTTP CALL AGENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestHTTPCallAgent:
    """Wrap a function that makes HTTP calls. Verify the receipt logs every call."""

    def test_api_calls_tracked_by_observer(self):
        """A function that makes API calls should produce chain entries for each call."""

        def api_agent(task, api_observer=None):
            """Agent that makes API calls (simulated)."""
            results = []

            # Simulate GET request
            results.append({"status": 200, "body": {"users": []}})
            if api_observer:
                api_observer.api_call("GET", "https://api.example.com/users", 200, 0.05)

            # Simulate POST request
            results.append({"status": 201, "body": {"id": "u123"}})
            if api_observer:
                api_observer.api_call("POST", "https://api.example.com/users", 201, 0.12)

            # Simulate failed request
            results.append({"status": 500, "body": None})
            if api_observer:
                api_observer.api_call("GET", "https://api.example.com/health", 500, 0.02)

            return results

        wrapped = xy_wrap(api_agent)
        result = wrapped("make api calls")

        assert isinstance(result, WrappedResult)
        assert len(result.output) == 3

        # Chain: start + 3 API entries + complete = 5
        assert result.chain.length == 5
        assert result.verified

        # Check observer
        assert result.observer is not None
        assert isinstance(result.observer, APIObserver)
        assert result.observer.count == 3
        assert len(result.observer.requests) == 3

        # Check failed requests tracked
        assert len(result.observer.failed_actions) == 1

        # Verify chain operations
        ops = [e.operation for e in result.chain.entries]
        assert ops[0] == "start"
        assert ops[1] == "api.get"
        assert ops[2] == "api.post"
        assert ops[3] == "api.get"
        assert ops[-1] == "complete"

        # Check receipt captures total
        assert result.receipt.entry_count == 5
        assert result.receipt.all_verified

        # Check summary in completion entry
        complete_entry = result.chain.entries[-1]
        assert complete_entry.y_state is not None
        assert "api_summary" in complete_entry.y_state

    def test_api_observer_summary(self):
        """API observer summary should aggregate request stats."""

        def api_agent(task, api_observer=None):
            if api_observer:
                api_observer.api_call("GET", "https://api.com/a", 200, 0.01)
                api_observer.api_call("GET", "https://api.com/b", 200, 0.02)
                api_observer.api_call("POST", "https://api.com/c", 400, 0.03)
            return "done"

        wrapped = xy_wrap(api_agent)
        result = wrapped("api summary test")

        summary = result.observer.summary()
        assert summary["total_actions"] == 3
        assert summary["total_requests"] == 3
        assert summary["failed_requests"] == 1

    def test_async_api_agent(self):
        """Async function with API observer should work correctly."""

        async def async_api_agent(task, api_observer=None):
            if api_observer:
                api_observer.api_call("GET", "https://api.com/data", 200, 0.05)
                api_observer.api_call("PUT", "https://api.com/data/1", 200, 0.1)
            return {"updated": True}

        wrapped = xy_wrap(async_api_agent)
        result = asyncio.run(wrapped("async api"))

        assert result.output == {"updated": True}
        assert result.chain.length == 4  # start + 2 api + complete
        assert result.verified
        assert result.observer.count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FAILURE HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


class TestFailureHandling:
    """Wrap a function that fails halfway. Verify the chain records the failure."""

    def test_exception_captured_in_chain(self):
        """When the wrapped function raises, the chain should record the failure."""

        def failing_agent(task, file_observer=None):
            # First action succeeds
            if file_observer:
                file_observer.file_write("/tmp/success.txt", size=100)

            # Then it fails
            raise RuntimeError("disk full — cannot write")

        wrapped = xy_wrap(failing_agent)
        result = wrapped("risky operation")

        # Output is None because the function failed
        assert result.output is None

        # Chain should still have: start + file.write + complete(failed) = 3
        assert result.chain.length == 3

        # Chain is still cryptographically valid
        assert result.verified

        # Complete entry should record the failure
        complete = result.chain.entries[-1]
        assert complete.status == "failed"
        assert complete.y_state is not None
        assert complete.y_state["status"] == "failed"
        assert "disk full" in complete.y_state["error"]

        # Receipt should reflect the entry count
        assert result.receipt.entry_count == 3

    def test_partial_work_before_failure(self):
        """Chain captures all work done before failure."""

        def multi_step_agent(task, file_observer=None, api_observer=None):
            # Step 1: Read config
            if file_observer:
                file_observer.file_read("/etc/config.yaml", size=512)

            # Step 2: Call API
            if api_observer:
                api_observer.api_call("GET", "https://api.example.com/check", 200, 0.1)

            # Step 3: Write result
            if file_observer:
                file_observer.file_write("/tmp/result.json", size=256)

            # Step 4: FAIL
            raise ConnectionError("network timeout during upload")

        wrapped = xy_wrap(multi_step_agent)
        result = wrapped("multi step")

        # start + file.read + api.get + file.write + complete = 5
        assert result.chain.length == 5
        assert result.verified

        # Last entry records the failure
        assert result.chain.entries[-1].status == "failed"
        assert "network timeout" in result.chain.entries[-1].y_state["error"]

        # All intermediate entries are success
        for entry in result.chain.entries[1:-1]:
            assert entry.status == "success"

    def test_async_failure(self):
        """Async function failure should be captured the same way."""

        async def async_failing(task, observer=None):
            if observer:
                observer.observe("step1", {"data": "ok"})
            raise ValueError("async error")

        wrapped = xy_wrap(async_failing)
        result = asyncio.run(wrapped("async fail"))

        assert result.output is None
        assert result.chain.length == 3  # start + step1 + complete(failed)
        assert result.verified
        assert result.chain.entries[-1].status == "failed"
        assert "async error" in result.chain.entries[-1].y_state["error"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CLOUD SYNC
# ═══════════════════════════════════════════════════════════════════════════════


class TestCloudSync:
    """Test cloud sync — wrap an agent with api_key, verify the chain uploads."""

    def test_cloud_sync_called_with_api_key(self):
        """When api_key is provided, cloud sync should be attempted after completion."""

        def simple_agent(task):
            return f"done: {task}"

        with patch("pruv.wrap.wrapper.WrappedAgent._cloud_sync", new_callable=AsyncMock) as mock_sync:
            wrapped = xy_wrap(simple_agent, api_key="pv_test_abc123")
            result = wrapped("cloud test")

            assert result.output == "done: cloud test"
            assert result.verified

            # Cloud sync should have been called
            mock_sync.assert_called_once()
            call_args = mock_sync.call_args
            chain = call_args[0][0]
            receipt = call_args[0][1]
            assert isinstance(chain, XYChain)
            assert chain.name == "simple_agent"

    def test_no_cloud_sync_without_api_key(self):
        """Without api_key, cloud sync should NOT be called."""

        def simple_agent(task):
            return "done"

        with patch("pruv.wrap.wrapper.WrappedAgent._cloud_sync", new_callable=AsyncMock) as mock_sync:
            wrapped = xy_wrap(simple_agent)
            result = wrapped("no cloud")

            mock_sync.assert_not_called()

    def test_cloud_client_upload_chain_format(self):
        """CloudClient.upload_chain should send correct body format to backend."""

        async def run_test():
            chain = XYChain(name="test-chain", auto_redact=True)
            chain.append(operation="start", y_state={"task": "test"})
            chain.append(operation="complete", y_state={"status": "success"})

            with tempfile.TemporaryDirectory() as tmpdir:
                client = CloudClient(
                    api_key="pv_test_key",
                    base_url="http://localhost:8000",
                    queue_dir=os.path.join(tmpdir, "queue"),
                )

                requests_made = []

                async def mock_request(method, path, body=None):
                    requests_made.append({"method": method, "path": path, "body": body})
                    if path == "/v1/chains" and method == "POST":
                        return {"id": "remote123", "name": "test-chain"}
                    if "/entries/batch" in path:
                        return {"entries": [], "total": 0}
                    return {}

                client._request = mock_request
                await client.upload_chain(chain)

            # Should make 2 requests: create chain, then batch append
            assert len(requests_made) == 2

            # First request: create chain
            assert requests_made[0]["method"] == "POST"
            assert requests_made[0]["path"] == "/v1/chains"
            assert requests_made[0]["body"] == {"name": "test-chain", "auto_redact": True}

            # Second request: batch append entries
            assert requests_made[1]["method"] == "POST"
            assert "/entries/batch" in requests_made[1]["path"]
            entries_body = requests_made[1]["body"]
            assert "entries" in entries_body
            assert len(entries_body["entries"]) == 2
            assert entries_body["entries"][0]["operation"] == "start"
            assert entries_body["entries"][1]["operation"] == "complete"

        asyncio.run(run_test())

    def test_cloud_client_append_entry_format(self):
        """CloudClient.append_entry should send correct body to backend."""

        async def run_test():
            from xycore import XYEntry
            entry = XYEntry.create(
                index=0,
                operation="test-op",
                x="GENESIS",
                y="abc123",
                y_state={"key": "value"},
                status="success",
                metadata={"source": "test"},
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                client = CloudClient(
                    api_key="pv_test_key",
                    base_url="http://localhost:8000",
                    queue_dir=os.path.join(tmpdir, "queue"),
                )

                captured_body = {}

                async def mock_request(method, path, body=None):
                    captured_body.update(body or {})
                    return {"id": "e1", "index": 0}

                client._request = mock_request
                await client.append_entry("chain123", entry)

            # Should send operation and states, NOT raw hashes
            assert captured_body["operation"] == "test-op"
            assert captured_body["y_state"] == {"key": "value"}
            assert captured_body["status"] == "success"
            assert captured_body["metadata"] == {"source": "test"}
            # Should NOT contain computed fields
            assert "x" not in captured_body
            assert "y" not in captured_body
            assert "xy" not in captured_body
            assert "index" not in captured_body

        asyncio.run(run_test())

    def test_cloud_sync_failure_non_fatal(self):
        """Cloud sync failures should not break the wrapped function result."""

        def simple_agent(task):
            return "success"

        async def failing_sync(chain, receipt):
            raise ConnectionError("network down")

        wrapped = xy_wrap(simple_agent, api_key="pv_test_x")
        # Patch the instance method directly on the agent
        wrapped._agent._cloud_sync = failing_sync

        result = wrapped("cloud fail test")

        # Result should still be valid despite sync failure
        assert result.output == "success"
        assert result.verified

    def test_async_cloud_sync(self):
        """Async wrapped agent should call cloud sync."""

        async def async_agent(task):
            return f"async: {task}"

        with patch("pruv.wrap.wrapper.WrappedAgent._cloud_sync", new_callable=AsyncMock) as mock_sync:
            wrapped = xy_wrap(async_agent, api_key="pv_test_async")
            result = asyncio.run(wrapped("async cloud"))

            assert result.output == "async: async cloud"
            mock_sync.assert_called_once()

    def test_cloud_client_upload_receipt_format(self):
        """CloudClient.upload_receipt should send correct body."""

        async def run_test():
            from xycore import XYReceipt
            receipt = XYReceipt(
                id="r123",
                task="test task",
                started=time.time(),
                completed=time.time(),
                duration=1.5,
                chain_id="c123",
                entry_count=3,
                first_x="GENESIS",
                final_y="abc",
                root_xy="xy_root",
                head_xy="xy_head",
                all_verified=True,
                agent_type="test-agent",
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                client = CloudClient(
                    api_key="pv_test_key",
                    base_url="http://localhost:8000",
                    queue_dir=os.path.join(tmpdir, "queue"),
                )

                captured_body = {}

                async def mock_request(method, path, body=None):
                    captured_body.update(body or {})
                    return {"id": "r123"}

                client._request = mock_request
                await client.upload_receipt(receipt)

            assert captured_body["chain_id"] == "c123"
            assert captured_body["task"] == "test task"
            assert captured_body["agent_type"] == "test-agent"

        asyncio.run(run_test())


# ═══════════════════════════════════════════════════════════════════════════════
# 5. APPROVAL GATE
# ═══════════════════════════════════════════════════════════════════════════════


class TestApprovalGate:
    """Test approval gate — wrap an agent with approval webhook, verify it pauses."""

    def test_approval_gate_injected(self):
        """When approval_webhook is set, the gate should be injected."""

        def gated_agent(task, approval_gate=None):
            assert approval_gate is not None
            assert isinstance(approval_gate, ApprovalGate)
            return f"gated: {task}"

        wrapped = xy_wrap(
            gated_agent,
            approval_webhook="https://example.com/approve",
            approval_operations=["deploy", "file.write"],
        )
        result = wrapped("deploy something")

        assert result.output == "gated: deploy something"
        assert result.verified

    def test_approval_gate_requires_approval(self):
        """Gate should identify operations that require approval."""

        def gated_agent(task, approval_gate=None):
            if approval_gate:
                assert approval_gate.requires_approval("deploy")
                assert approval_gate.requires_approval("file.write")
                assert not approval_gate.requires_approval("file.read")
            return "checked"

        wrapped = xy_wrap(
            gated_agent,
            approval_webhook="https://example.com/approve",
            approval_operations=["deploy", "file.write"],
        )
        result = wrapped("check gate")
        assert result.output == "checked"

    def test_approval_gate_auto_approves_non_matching(self):
        """Operations not in the approval set should be auto-approved."""

        async def run_test():
            gate = ApprovalGate(
                webhook_url="https://example.com/approve",
                operations={"deploy"},
            )
            response = await gate.gate("chain1", 0, "file.read")
            assert response.is_approved
            assert response.reason == "no-approval-required"

        asyncio.run(run_test())

    def test_approval_gate_calls_webhook(self):
        """Gate should call webhook for matching operations."""

        async def run_test():
            gate = ApprovalGate(
                webhook_url="https://example.com/approve",
                operations={"deploy"},
                timeout=5,
            )

            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "approved",
                    "approved_by": "admin@test.com",
                }
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                MockClient.return_value = mock_instance

                response = await gate.gate(
                    chain_id="chain1",
                    entry_index=5,
                    operation="deploy",
                    x_state={"version": "1.0"},
                    proposed_y_state={"version": "2.0"},
                )

                assert response.is_approved
                assert response.approved_by == "admin@test.com"

                # Verify webhook was called with correct payload
                mock_instance.post.assert_called_once()
                call_args = mock_instance.post.call_args
                payload = call_args[1]["json"]
                assert payload["chain_id"] == "chain1"
                assert payload["operation"] == "deploy"

        asyncio.run(run_test())

    def test_approval_gate_denial(self):
        """Gate should handle denial from webhook."""

        async def run_test():
            gate = ApprovalGate(
                webhook_url="https://example.com/approve",
                operations={"deploy"},
                timeout=5,
            )

            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "denied",
                    "reason": "not authorized",
                }
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                MockClient.return_value = mock_instance

                response = await gate.gate("chain1", 5, "deploy")

                assert not response.is_approved
                assert response.status == "denied"

        asyncio.run(run_test())

    def test_approval_gate_timeout_deny(self):
        """Gate should deny on timeout by default."""

        async def run_test():
            gate = ApprovalGate(
                webhook_url="https://unreachable.example.com/approve",
                operations={"deploy"},
                timeout=1,
                on_timeout="deny",
            )

            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(side_effect=Exception("connection timeout"))
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                MockClient.return_value = mock_instance

                response = await gate.gate("chain1", 0, "deploy")

                assert not response.is_approved
                assert response.status == "timeout"

        asyncio.run(run_test())

    def test_approval_gate_timeout_auto_approve(self):
        """Gate can be configured to auto-approve on timeout."""

        async def run_test():
            gate = ApprovalGate(
                webhook_url="https://unreachable.example.com/approve",
                operations={"deploy"},
                timeout=1,
                on_timeout="approve",
            )

            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(side_effect=Exception("connection timeout"))
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                MockClient.return_value = mock_instance

                response = await gate.gate("chain1", 0, "deploy")

                assert response.is_approved
                assert "timeout-auto-approved" in response.reason

        asyncio.run(run_test())

    def test_agent_uses_gate_to_guard_operations(self):
        """Real scenario: async agent checks gate before risky operations."""

        async def deploy_agent(task, file_observer=None, approval_gate=None):
            results = []

            # Safe operation — no approval needed
            if file_observer:
                file_observer.file_read("/etc/config.yaml", size=100)
            results.append("read config")

            # Risky operation — check gate (async)
            if approval_gate:
                response = await approval_gate.gate("chain1", 1, "deploy")
                if not response.is_approved:
                    raise PermissionError(f"Deploy denied: {response.reason}")

            if file_observer:
                file_observer.file_write("/deploy/app.tar.gz", size=5000)
            results.append("deployed")

            return results

        # Mock the gate to approve
        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "approved", "approved_by": "admin"}
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            wrapped = xy_wrap(
                deploy_agent,
                approval_webhook="https://example.com/approve",
                approval_operations=["deploy"],
            )
            result = asyncio.run(wrapped("deploy v2"))

        assert result.output == ["read config", "deployed"]
        assert result.verified
        # start + file.read + file.write + complete = 4
        assert result.chain.length == 4

    def test_no_gate_without_webhook(self):
        """Without approval_webhook, gate should not be injected."""

        def agent(task, approval_gate=None):
            assert approval_gate is None
            return "no gate"

        wrapped = xy_wrap(agent)
        result = wrapped("no webhook")
        assert result.output == "no gate"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. COMBINED SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════


class TestCombinedScenarios:
    """Test combinations of file + API + failure + observers."""

    def test_mixed_file_and_api_operations(self):
        """Agent that does both file and API operations."""

        def mixed_agent(task, file_observer=None, api_observer=None):
            # Read config file
            if file_observer:
                file_observer.file_read("/etc/app.conf", size=200)

            # Call API
            if api_observer:
                api_observer.api_call("GET", "https://api.com/data", 200, 0.1)

            # Write result
            if file_observer:
                file_observer.file_write("/tmp/result.json", size=500)

            # Call another API
            if api_observer:
                api_observer.api_call("POST", "https://api.com/notify", 201, 0.05)

            return "mixed done"

        wrapped = xy_wrap(mixed_agent)
        result = wrapped("mixed ops")

        # start + read + get + write + post + complete = 6
        assert result.chain.length == 6
        assert result.verified

        ops = [e.operation for e in result.chain.entries]
        assert ops == ["start", "file.read", "api.get", "file.write", "api.post", "complete"]

    def test_decorator_with_options(self):
        """@xy_wrap(sign=True) should work correctly."""
        from nacl.signing import SigningKey

        key = SigningKey.generate()

        @xy_wrap(sign=True, private_key=bytes(key), signer_id="test-signer")
        def signed_agent(task):
            return f"signed: {task}"

        result = signed_agent("test")
        assert result.output == "signed: test"
        assert result.verified

        # Last entry should be signed
        last = result.chain.entries[-1]
        assert last.signature is not None
        assert last.signer_id == "test-signer"

    def test_chain_rule_preserved(self):
        """Every chain entry must satisfy: Entry[N].x == Entry[N-1].y"""

        def multi_step(task, observer=None):
            if observer:
                observer.observe("step1", {"data": "a"})
                observer.observe("step2", {"data": "b"})
                observer.observe("step3", {"data": "c"})
            return "done"

        wrapped = xy_wrap(multi_step)
        result = wrapped("chain rule test")

        # Verify chain rule manually
        entries = result.chain.entries
        assert entries[0].x == "GENESIS"
        for i in range(1, len(entries)):
            assert entries[i].x == entries[i - 1].y, (
                f"Chain rule broken at index {i}: "
                f"entry[{i}].x={entries[i].x} != entry[{i-1}].y={entries[i-1].y}"
            )

    def test_observer_hooks(self):
        """Observer hooks should fire on matching operations."""
        hook_calls = []

        def hook_agent(task, observer=None):
            if observer:
                observer.on("step.important", lambda a: hook_calls.append(a.operation))
                observer.observe("step.normal", {"v": 1})
                observer.observe("step.important", {"v": 2})
                observer.observe("step.normal", {"v": 3})
                observer.observe("step.important", {"v": 4})
            return "hooked"

        wrapped = xy_wrap(hook_agent)
        result = wrapped("hook test")

        assert len(hook_calls) == 2
        assert all(h == "step.important" for h in hook_calls)

    def test_wildcard_hook(self):
        """Wildcard hook should fire on all operations."""
        all_ops = []

        def hook_agent(task, observer=None):
            if observer:
                observer.on("*", lambda a: all_ops.append(a.operation))
                observer.observe("a")
                observer.observe("b")
                observer.observe("c")
            return "done"

        wrapped = xy_wrap(hook_agent)
        result = wrapped("wildcard")

        assert all_ops == ["a", "b", "c"]

    def test_actions_property(self):
        """WrappedResult.actions should return all observed actions."""

        def agent_with_actions(task, observer=None):
            if observer:
                observer.observe("load", {"file": "data.csv"})
                observer.observe("process", {"rows": 100})
                observer.observe("save", {"file": "output.csv"})
            return "processed"

        wrapped = xy_wrap(agent_with_actions)
        result = wrapped("process data")

        assert len(result.actions) == 3
        assert result.actions[0].operation == "load"
        assert result.actions[1].operation == "process"
        assert result.actions[2].operation == "save"

    def test_receipt_hash_deterministic(self):
        """Receipt hash should be deterministic for the same chain."""

        def simple(task):
            return task

        wrapped = xy_wrap(simple)
        r1 = wrapped("test")
        assert isinstance(r1.receipt.hash, str)
        assert len(r1.receipt.hash) == 64

    def test_xy_proof_format(self):
        """All XY proof hashes should start with xy_."""

        def agent(task, observer=None):
            if observer:
                observer.observe("op1")
                observer.observe("op2")
            return "done"

        wrapped = xy_wrap(agent)
        result = wrapped("proof format")

        for entry in result.chain.entries:
            assert entry.xy.startswith("xy_"), f"Entry {entry.index} xy={entry.xy} does not start with xy_"

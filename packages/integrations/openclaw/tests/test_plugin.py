"""Tests for the OpenClaw pruv plugin and interceptor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_client():
    """Create a mock PruvClient."""
    client = MagicMock()
    client.act.return_value = {"id": "entry_1", "status": "ok"}
    client.get_identity_receipt.return_value = "<html>receipt</html>"
    client.verify_identity.return_value = {"valid": True, "action_count": 6}
    return client


class TestPruvOpenClawPlugin:
    def test_before_action_file_read(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")
            plugin.before_action("read_file", {"path": "/app/data.json"})

            call_kwargs = mock_client.act.call_args.kwargs
            assert call_kwargs["action_scope"] == "file.read"
            assert "read_file" in call_kwargs["action"]
            assert "/app/data.json" in call_kwargs["action"]

    def test_after_action_file_write(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")
            plugin.after_action("write_file", {"path": "/app/out.txt", "bytes": 1024})

            call_kwargs = mock_client.act.call_args.kwargs
            assert call_kwargs["action_scope"] == "file.write"
            assert "write_file_complete" in call_kwargs["action"]

    def test_on_error(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")
            plugin.on_error("execute", RuntimeError("permission denied"))

            call_kwargs = mock_client.act.call_args.kwargs
            assert call_kwargs["action_scope"] == "system.execute"
            assert "error" in call_kwargs["action"]
            assert "permission denied" in call_kwargs["action"]

    def test_scope_mapping(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")

            test_cases = {
                "read_file": "file.read",
                "write_file": "file.write",
                "delete_file": "file.delete",
                "send_email": "email.send",
                "read_email": "email.read",
                "browse": "browser.interact",
                "execute": "system.execute",
                "send_message": "messaging.send",
                "unknown_action": "agent.action",
            }

            for action_type, expected_scope in test_cases.items():
                mock_client.act.reset_mock()
                plugin.before_action(action_type, {})
                call_kwargs = mock_client.act.call_args.kwargs
                assert call_kwargs["action_scope"] == expected_scope, (
                    f"Expected {expected_scope} for {action_type}, "
                    f"got {call_kwargs['action_scope']}"
                )

    def test_receipt(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")
            receipt = plugin.receipt()

            assert "receipt" in receipt
            mock_client.get_identity_receipt.assert_called_once_with("pi_test_oc")

    def test_verify(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvOpenClawPlugin

            plugin = PruvOpenClawPlugin(agent_id="pi_test_oc", api_key="pv_test_key")
            result = plugin.verify()

            assert result["valid"] is True
            mock_client.verify_identity.assert_called_once_with("pi_test_oc")


class TestPruvActionInterceptor:
    def test_wrap_records_before_and_after(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvActionInterceptor

            interceptor = PruvActionInterceptor(
                agent_id="pi_test_oc", api_key="pv_test_key"
            )

            original_fn = MagicMock(return_value={"content": "file data"})
            wrapped = interceptor.wrap(original_fn)

            result = wrapped("read_file", {"path": "/app/data.json"})

            # Original function was called
            original_fn.assert_called_once_with("read_file", {"path": "/app/data.json"})
            assert result == {"content": "file data"}

            # Two act() calls: before + after
            assert mock_client.act.call_count == 2
            before_kwargs = mock_client.act.call_args_list[0].kwargs
            after_kwargs = mock_client.act.call_args_list[1].kwargs
            assert "read_file:" in before_kwargs["action"]
            assert "read_file_complete:" in after_kwargs["action"]

    def test_wrap_records_error(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvActionInterceptor

            interceptor = PruvActionInterceptor(
                agent_id="pi_test_oc", api_key="pv_test_key"
            )

            original_fn = MagicMock(side_effect=PermissionError("access denied"))
            wrapped = interceptor.wrap(original_fn)

            with pytest.raises(PermissionError):
                wrapped("write_file", {"path": "/etc/passwd"})

            # Two act() calls: before + error
            assert mock_client.act.call_count == 2
            error_kwargs = mock_client.act.call_args_list[1].kwargs
            assert "error" in error_kwargs["action"]
            assert "access denied" in error_kwargs["action"]

    def test_wrap_does_not_break_original(self, mock_client):
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvActionInterceptor

            interceptor = PruvActionInterceptor(
                agent_id="pi_test_oc", api_key="pv_test_key"
            )

            call_log = []

            def original_fn(action_type, payload, **kwargs):
                call_log.append((action_type, payload))
                return {"status": "ok", "action": action_type}

            wrapped = interceptor.wrap(original_fn)

            result = wrapped("send_email", {"to": "user@co.com", "subject": "test"})

            assert result == {"status": "ok", "action": "send_email"}
            assert len(call_log) == 1
            assert call_log[0] == ("send_email", {"to": "user@co.com", "subject": "test"})

    def test_full_lifecycle(self, mock_client):
        """Full lifecycle: multiple actions, then receipt."""
        with patch("pruv_openclaw.plugin.PruvClient", return_value=mock_client):
            from pruv_openclaw import PruvActionInterceptor

            interceptor = PruvActionInterceptor(
                agent_id="pi_test_oc", api_key="pv_test_key"
            )

            original_fn = MagicMock(return_value={"ok": True})
            wrapped = interceptor.wrap(original_fn)

            wrapped("read_file", {"path": "/app/config.yaml"})
            wrapped("execute", {"cmd": "deploy"})
            wrapped("send_email", {"to": "ops@co.com", "body": "deployed"})

            # 3 actions x 2 calls each (before + after) = 6
            assert mock_client.act.call_count == 6

            receipt = interceptor.receipt()
            assert "receipt" in receipt

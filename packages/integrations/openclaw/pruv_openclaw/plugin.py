"""OpenClaw plugin that records every agent action to the pruv identity chain."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient

# Scope map from OpenClaw action types to pruv identity scope vocabulary
OPENCLAW_ACTION_SCOPE_MAP: dict[str, str] = {
    "read_file": "file.read",
    "write_file": "file.write",
    "delete_file": "file.delete",
    "send_email": "email.send",
    "read_email": "email.read",
    "browse": "browser.interact",
    "browser_read": "browser.read",
    "execute": "system.execute",
    "send_message": "messaging.send",
    "read_message": "messaging.read",
    "calendar_read": "calendar.read",
    "calendar_write": "calendar.write",
    "network": "network.external",
}


class PruvOpenClawPlugin:
    """OpenClaw plugin interface for pruv cryptographic accountability.

    Config-driven usage (openclaw.config.yaml)::

        agent_id: pv_agent_7f3a1c2e
        pruv_api_key: pv_live_...

        plugins:
          - pruv_openclaw.PruvOpenClawPlugin

    Programmatic usage::

        from pruv_openclaw import PruvOpenClawPlugin

        plugin = PruvOpenClawPlugin(agent_id="pi_abc123", api_key="pv_live_...")
        plugin.before_action("read_file", {"path": "/app/data.json"})
        plugin.after_action("read_file", {"content": "..."})
        receipt = plugin.receipt()
    """

    name = "pruv"
    description = "Cryptographic accountability layer for OpenClaw agents"

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
    ) -> None:
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)

    def before_action(self, action_type: str, payload: dict[str, Any]) -> None:
        """Called before an OpenClaw skill executes."""
        self.client.act(
            agent_id=self.agent_id,
            action=f"{action_type}: {str(payload)[:200]}",
            action_scope=self._scope(action_type),
        )

    def after_action(self, action_type: str, result: dict[str, Any]) -> None:
        """Called after an OpenClaw skill completes."""
        self.client.act(
            agent_id=self.agent_id,
            action=f"{action_type}_complete: {str(result)[:200]}",
            action_scope=self._scope(action_type),
        )

    def on_error(self, action_type: str, error: BaseException) -> None:
        """Called when an OpenClaw skill fails."""
        self.client.act(
            agent_id=self.agent_id,
            action=f"{action_type}_error: {str(error)[:200]}",
            action_scope=self._scope(action_type),
        )

    def receipt(self) -> str:
        """Get the self-verifying HTML receipt for this agent."""
        return self.client.get_identity_receipt(self.agent_id)

    def verify(self) -> dict[str, Any]:
        """Verify the agent's chain integrity."""
        return self.client.verify_identity(self.agent_id)

    @staticmethod
    def _scope(action_type: str) -> str:
        return OPENCLAW_ACTION_SCOPE_MAP.get(action_type, "agent.action")

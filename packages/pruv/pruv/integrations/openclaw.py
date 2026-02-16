"""OpenClaw integration for pruv.

Middleware that intercepts OpenClaw skill executions and records them
to a pruv verification chain.

Usage::

    from pruv.integrations.openclaw import OpenClawVerifier

    verifier = OpenClawVerifier(
        api_key="pv_live_xxx",
        agent_name="my-openclaw",
    )

    # Record skill execution
    verifier.before_skill("send_email", {"to": "boss@co.com"})
    result = some_skill.run()
    verifier.after_skill("send_email", result)

    # Get verification chain
    chain = verifier.get_chain()
"""

from __future__ import annotations

import time
from typing import Any

from pruv.agent import Agent


class OpenClawVerifier:
    """Middleware that records OpenClaw skill executions to a pruv chain.

    Provides helper methods for common event types — skill execution,
    messages, file access, and API calls.  Sensitive content (message
    bodies, passwords, tokens) is redacted by default.
    """

    _DEFAULT_SENSITIVE = [
        "body", "content", "message", "text", "password", "token",
    ]

    def __init__(
        self,
        api_key: str,
        agent_name: str = "openclaw-agent",
        endpoint: str = "https://api.pruv.dev",
        redact_content: bool = True,
    ) -> None:
        self.agent = Agent(
            name=agent_name,
            api_key=api_key,
            endpoint=endpoint,
            metadata={
                "framework": "openclaw",
                "started": time.time(),
            },
        )
        self.redact_content = redact_content
        self._sensitive = list(self._DEFAULT_SENSITIVE)

    # ------------------------------------------------------------------
    # Skill lifecycle
    # ------------------------------------------------------------------

    def before_skill(
        self, skill_name: str, params: dict[str, Any],
    ) -> dict[str, Any]:
        """Record intent before skill execution."""
        sensitive = self._sensitive if self.redact_content else []
        return self.agent.action("skill.start", {
            "skill": skill_name,
            "params": params,
        }, sensitive)

    def after_skill(
        self,
        skill_name: str,
        result: Any,
        success: bool = True,
    ) -> dict[str, Any]:
        """Record skill completion or failure."""
        if success:
            return self.agent.action("skill.complete", {
                "skill": skill_name,
                "result_type": type(result).__name__,
            })
        return self.agent.action("skill.error", {
            "skill": skill_name,
            "error": str(result),
        })

    # ------------------------------------------------------------------
    # Message events
    # ------------------------------------------------------------------

    def message_received(
        self, channel: str, sender: str, content: str,
    ) -> dict[str, Any]:
        """Record incoming message."""
        sensitive = ["content"] if self.redact_content else []
        return self.agent.action("message.received", {
            "channel": channel,
            "sender": sender,
            "content": content,
        }, sensitive)

    def message_sent(
        self, channel: str, recipient: str, content: str,
    ) -> dict[str, Any]:
        """Record outgoing message."""
        sensitive = ["content"] if self.redact_content else []
        return self.agent.action("message.sent", {
            "channel": channel,
            "recipient": recipient,
            "content": content,
        }, sensitive)

    # ------------------------------------------------------------------
    # Resource events
    # ------------------------------------------------------------------

    def file_accessed(
        self, path: str, operation: str,
    ) -> dict[str, Any]:
        """Record file access."""
        return self.agent.action("file.access", {
            "path": path,
            "operation": operation,
        })

    def api_called(
        self, url: str, method: str, status: int,
    ) -> dict[str, Any]:
        """Record external API call."""
        return self.agent.action("api.call", {
            "url": url,
            "method": method,
            "status": status,
        })

    # ------------------------------------------------------------------
    # Chain access
    # ------------------------------------------------------------------

    def get_chain(self) -> dict[str, Any]:
        """Get the full verification chain."""
        return self.agent.chain()

    def verify(self) -> dict[str, Any]:
        """Verify the chain integrity."""
        return self.agent.verify()

    def export(self) -> str:
        """Export as self-verifying HTML artifact."""
        return self.agent.export()

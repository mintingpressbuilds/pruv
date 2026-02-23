"""One-line wrapper for any OpenAI Agents SDK agent."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient

from .tracing import PruvTraceProcessor


class OpenAIAgentWrapper:
    """Wrap any OpenAI Agents SDK agent with automatic pruv verification.

    Usage::

        from pruv_openai import OpenAIAgentWrapper

        agent = Agent(name="assistant", instructions="...", tools=[...])
        verified = OpenAIAgentWrapper(agent, agent_id="pi_abc123", api_key="pv_live_...")
        result = await verified.run("Analyze this document")
        receipt = verified.receipt()
    """

    def __init__(
        self,
        agent: Any,
        agent_id: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
    ) -> None:
        self.agent = agent
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self.processor = PruvTraceProcessor(agent_id=agent_id, client=self.client)
        self._register_processor()

    def _register_processor(self) -> None:
        """Register the pruv trace processor with the OpenAI Agents SDK."""
        try:
            from agents import add_trace_processor
            add_trace_processor(self.processor)
        except ImportError:
            # SDK not installed — processor will be available for manual use
            pass

    async def run(self, input: str, **kwargs: Any) -> Any:
        """Run the wrapped agent asynchronously."""
        from agents import Runner
        return await Runner.run(self.agent, input, **kwargs)

    def run_sync(self, input: str, **kwargs: Any) -> Any:
        """Run the wrapped agent synchronously."""
        from agents import Runner
        return Runner.run_sync(self.agent, input, **kwargs)

    def receipt(self) -> str:
        """Get the self-verifying HTML receipt for this agent."""
        return self.client.get_identity_receipt(self.agent_id)

    def verify(self) -> dict[str, Any]:
        """Verify the agent's chain integrity."""
        return self.client.verify_identity(self.agent_id)

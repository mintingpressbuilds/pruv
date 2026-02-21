"""One-line wrapper for any LangChain agent."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient

from .callback import PruvCallbackHandler


# Framework-specific scope vocabulary
LANGCHAIN_SCOPE_OPTIONS = [
    "tool.execute",
    "llm.call",
    "agent.action",
    "agent.complete",
    "chain.run",
    "retriever.query",
    "memory.read",
    "memory.write",
]


class LangChainWrapper:
    """Wrap any LangChain agent with automatic pruv verification.

    Usage::

        from pruv_langchain import LangChainWrapper

        agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
        verified = LangChainWrapper(agent, agent_id="pi_abc123", api_key="pv_live_...")
        result = verified.run("Summarize the Q3 report")
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
        self.handler = PruvCallbackHandler(
            agent_id=agent_id,
            client=self.client,
        )

    def run(self, input: str, **kwargs: Any) -> Any:
        """Run the wrapped agent. Every action is recorded automatically."""
        callbacks = kwargs.pop("callbacks", None) or []
        callbacks.append(self.handler)
        return self.agent.run(input, callbacks=callbacks, **kwargs)

    async def arun(self, input: str, **kwargs: Any) -> Any:
        """Run the wrapped agent asynchronously."""
        callbacks = kwargs.pop("callbacks", None) or []
        callbacks.append(self.handler)
        return await self.agent.arun(input, callbacks=callbacks, **kwargs)

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        """Invoke the wrapped agent (LCEL interface)."""
        config = kwargs.pop("config", {})
        existing = config.get("callbacks", [])
        config["callbacks"] = existing + [self.handler]
        return self.agent.invoke(input, config=config, **kwargs)

    async def ainvoke(self, input: Any, **kwargs: Any) -> Any:
        """Invoke the wrapped agent asynchronously (LCEL interface)."""
        config = kwargs.pop("config", {})
        existing = config.get("callbacks", [])
        config["callbacks"] = existing + [self.handler]
        return await self.agent.ainvoke(input, config=config, **kwargs)

    def receipt(self) -> str:
        """Get the self-verifying HTML receipt for this agent."""
        return self.client.get_identity_receipt(self.agent_id)

    def verify(self) -> dict[str, Any]:
        """Verify the agent's chain integrity."""
        return self.client.verify_identity(self.agent_id)

"""LangChain callback handler that records every action to the pruv identity chain."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from pruv import PruvClient


class PruvCallbackHandler(BaseCallbackHandler):
    """LangChain callback that posts every agent action to pruv.

    Uses LangChain's native callback system. Does not monkey-patch.
    """

    def __init__(
        self,
        agent_id: str,
        client: PruvClient,
    ) -> None:
        self.agent_id = agent_id
        self.client = client

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_start: {serialized.get('name', 'unknown')} \u2014 {input_str[:200]}",
            action_scope="tool.execute",
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_end: {str(output)[:200]}",
            action_scope="tool.execute",
        )

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_error: {str(error)[:200]}",
            action_scope="tool.execute",
        )

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"agent_action: {action.tool} \u2014 {str(action.tool_input)[:200]}",
            action_scope="agent.action",
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"llm_start: {serialized.get('name', serialized.get('id', ['unknown'])[-1])}",
            action_scope="llm.call",
        )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"chain_start: {serialized.get('name', serialized.get('id', ['unknown'])[-1])}",
            action_scope="chain.run",
        )

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"chain_end: {str(outputs)[:200]}",
            action_scope="agent.complete",
        )

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        **kwargs: Any,
    ) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"retriever_query: {query[:200]}",
            action_scope="retriever.query",
        )

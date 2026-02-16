"""LangChain integration for pruv.

Records every LLM call, tool usage, chain execution, and agent action
to a pruv verification chain.

Usage::

    from pruv.integrations.langchain import PruvCallbackHandler

    handler = PruvCallbackHandler(
        agent_name="my-langchain-agent",
        api_key="pv_live_xxx",
    )

    # Add to any LangChain agent/chain
    agent = initialize_agent(tools, llm, callbacks=[handler])
    agent.run("do something")

    # Get the verification chain
    chain = handler.pruv_agent.chain()
"""

from __future__ import annotations

from typing import Any

from pruv.agent import Agent

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError as exc:
    raise ImportError(
        "LangChain is not installed. Install it with: pip install langchain-core"
    ) from exc


class PruvCallbackHandler(BaseCallbackHandler):
    """LangChain callback that records every action to a pruv chain."""

    def __init__(
        self,
        agent_name: str = "langchain-agent",
        api_key: str = "",
        endpoint: str = "https://api.pruv.dev",
        record_prompts: bool = False,
        sensitive_keys: list[str] | None = None,
    ) -> None:
        self.pruv_agent = Agent(
            name=agent_name,
            api_key=api_key,
            endpoint=endpoint,
        )
        self.record_prompts = record_prompts
        self.sensitive_keys = sensitive_keys or []
        if not record_prompts:
            self.sensitive_keys.extend(["prompts", "prompt", "input"])

    # ------------------------------------------------------------------
    # LLM events
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        model_id = serialized.get("id", ["unknown"])
        model = model_id[-1] if isinstance(model_id, list) and model_id else "unknown"
        data: dict[str, Any] = {
            "model": model,
            "prompt_count": len(prompts),
        }
        if self.record_prompts:
            data["prompts"] = prompts
        self.pruv_agent.action("llm.start", data, self.sensitive_keys)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        self.pruv_agent.action("llm.complete", {
            "generations": (
                len(response.generations) if response.generations else 0
            ),
        })

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self.pruv_agent.action("llm.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    # ------------------------------------------------------------------
    # Tool events
    # ------------------------------------------------------------------

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        tool_data: dict[str, Any] = {
            "tool": serialized.get("name", "unknown"),
        }
        if self.record_prompts:
            tool_data["input"] = input_str
        else:
            tool_data["input_hash"] = self.pruv_agent._redact(
                {"input": input_str}, ["input"],
            )["input"]
        self.pruv_agent.action("tool.start", tool_data, self.sensitive_keys)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        self.pruv_agent.action("tool.complete", {
            "output_length": len(output) if output else 0,
        })

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        self.pruv_agent.action("tool.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    # ------------------------------------------------------------------
    # Chain events (LangChain "chain", not pruv chain)
    # ------------------------------------------------------------------

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        chain_id = serialized.get("id", ["unknown"])
        chain_name = chain_id[-1] if isinstance(chain_id, list) and chain_id else "unknown"
        self.pruv_agent.action("chain.start", {
            "chain": chain_name,
            "input_keys": list(inputs.keys()),
        })

    def on_chain_end(
        self, outputs: dict[str, Any], **kwargs: Any,
    ) -> None:
        self.pruv_agent.action("chain.complete", {
            "output_keys": list(outputs.keys()),
        })

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        self.pruv_agent.action("chain.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    # ------------------------------------------------------------------
    # Agent events
    # ------------------------------------------------------------------

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        self.pruv_agent.action("agent.action", {
            "tool": action.tool,
            "log": action.log[:200] if action.log else "",
        })

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        output_len = 0
        if finish.return_values:
            output_len = len(finish.return_values.get("output", ""))
        self.pruv_agent.action("agent.finish", {
            "output_length": output_len,
        })

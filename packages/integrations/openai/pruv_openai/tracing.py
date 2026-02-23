"""OpenAI Agents trace processor that records every action to the pruv identity chain."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient


# Framework-specific scope vocabulary
OPENAI_AGENTS_SCOPE_OPTIONS = [
    "agent.start",
    "agent.action",
    "agent.handoff",
    "agent.complete",
    "tool.execute",
    "llm.call",
    "guardrail.check",
]


class PruvTraceProcessor:
    """Trace processor for the OpenAI Agents SDK.

    Implements the TracingProcessor protocol: on_trace_start,
    on_span_start, on_span_end, on_trace_end.
    """

    def __init__(self, agent_id: str, client: PruvClient) -> None:
        self.agent_id = agent_id
        self.client = client

    def on_trace_start(self, trace: Any) -> None:
        name = getattr(trace, "name", "unknown")
        self.client.act(
            agent_id=self.agent_id,
            action=f"trace_start: {name}",
            action_scope="agent.start",
        )

    def on_span_start(self, span: Any) -> None:
        # Lightweight — we record detail on span_end when we have results
        pass

    def on_span_end(self, span: Any) -> None:
        span_data = getattr(span, "span_data", None)
        scope = self._scope_from_span(span)
        span_type = "unknown"
        detail = ""

        if span_data is not None:
            span_type = getattr(span_data, "type", str(type(span_data).__name__))
            detail = str(span_data)[:200]

        self.client.act(
            agent_id=self.agent_id,
            action=f"span_end: {span_type} \u2014 {detail}",
            action_scope=scope,
        )

    def on_trace_end(self, trace: Any) -> None:
        name = getattr(trace, "name", "unknown")
        self.client.act(
            agent_id=self.agent_id,
            action=f"trace_end: {name}",
            action_scope="agent.complete",
        )

    def shutdown(self) -> None:
        """Called when the processor is removed. No-op for pruv."""

    def force_flush(self) -> None:
        """Called to flush pending data. No-op — pruv posts synchronously."""

    @staticmethod
    def _scope_from_span(span: Any) -> str:
        span_data = getattr(span, "span_data", None)
        if span_data is None:
            return "agent.action"

        span_type = getattr(span_data, "type", "")
        if not isinstance(span_type, str):
            span_type = str(type(span_data).__name__).lower()

        if "tool" in span_type or "function" in span_type:
            return "tool.execute"
        if "handoff" in span_type:
            return "agent.handoff"
        if "llm" in span_type or "model" in span_type or "generation" in span_type:
            return "llm.call"
        if "guardrail" in span_type:
            return "guardrail.check"
        return "agent.action"

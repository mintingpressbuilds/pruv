"""Tests for the OpenAI Agents pruv wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_client():
    """Create a mock PruvClient."""
    client = MagicMock()
    client.act.return_value = {"id": "entry_1", "status": "ok"}
    client.get_identity_receipt.return_value = "<html>receipt</html>"
    client.verify_identity.return_value = {"valid": True, "action_count": 4}
    return client


class TestPruvTraceProcessor:
    def test_on_trace_start(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        trace = MagicMock()
        trace.name = "assistant-run"
        processor.on_trace_start(trace)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.start"
        assert "assistant-run" in call_kwargs["action"]

    def test_on_trace_end(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        trace = MagicMock()
        trace.name = "assistant-run"
        processor.on_trace_end(trace)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.complete"
        assert "assistant-run" in call_kwargs["action"]

    def test_on_span_end_tool(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        span = MagicMock()
        span.span_data.type = "function_tool_call"
        processor.on_span_end(span)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "tool.execute"

    def test_on_span_end_llm(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        span = MagicMock()
        span.span_data.type = "llm_generation"
        processor.on_span_end(span)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "llm.call"

    def test_on_span_end_handoff(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        span = MagicMock()
        span.span_data.type = "handoff"
        processor.on_span_end(span)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.handoff"

    def test_on_span_end_guardrail(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        span = MagicMock()
        span.span_data.type = "guardrail_check"
        processor.on_span_end(span)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "guardrail.check"

    def test_on_span_end_unknown(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        span = MagicMock()
        span.span_data.type = "something_else"
        processor.on_span_end(span)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.action"

    def test_on_span_start_is_noop(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        processor.on_span_start(MagicMock())
        mock_client.act.assert_not_called()

    def test_shutdown_and_flush_are_noop(self, mock_client):
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)
        processor.shutdown()
        processor.force_flush()
        mock_client.act.assert_not_called()

    def test_full_trace_lifecycle(self, mock_client):
        """Full trace lifecycle: start -> span_end (tool) -> span_end (llm) -> end."""
        from pruv_openai import PruvTraceProcessor

        processor = PruvTraceProcessor(agent_id="pi_test_oai", client=mock_client)

        trace = MagicMock()
        trace.name = "my-agent"

        tool_span = MagicMock()
        tool_span.span_data.type = "function_tool_call"

        llm_span = MagicMock()
        llm_span.span_data.type = "llm_generation"

        processor.on_trace_start(trace)
        processor.on_span_end(tool_span)
        processor.on_span_end(llm_span)
        processor.on_trace_end(trace)

        assert mock_client.act.call_count == 4
        scopes = [c.kwargs["action_scope"] for c in mock_client.act.call_args_list]
        assert scopes == ["agent.start", "tool.execute", "llm.call", "agent.complete"]


class TestOpenAIAgentWrapper:
    def test_wrapper_receipt(self, mock_client):
        with patch("pruv_openai.wrapper.PruvClient", return_value=mock_client):
            # Patch add_trace_processor to avoid ImportError
            with patch("pruv_openai.wrapper.OpenAIAgentWrapper._register_processor"):
                from pruv_openai import OpenAIAgentWrapper

                agent = MagicMock()
                wrapped = OpenAIAgentWrapper(
                    agent,
                    agent_id="pi_test_oai",
                    api_key="pv_test_key",
                )

                receipt = wrapped.receipt()

                assert "receipt" in receipt
                mock_client.get_identity_receipt.assert_called_once_with("pi_test_oai")

    def test_wrapper_verify(self, mock_client):
        with patch("pruv_openai.wrapper.PruvClient", return_value=mock_client):
            with patch("pruv_openai.wrapper.OpenAIAgentWrapper._register_processor"):
                from pruv_openai import OpenAIAgentWrapper

                agent = MagicMock()
                wrapped = OpenAIAgentWrapper(
                    agent,
                    agent_id="pi_test_oai",
                    api_key="pv_test_key",
                )

                result = wrapped.verify()

                assert result["valid"] is True
                mock_client.verify_identity.assert_called_once_with("pi_test_oai")

    def test_wrapper_stores_processor(self, mock_client):
        with patch("pruv_openai.wrapper.PruvClient", return_value=mock_client):
            with patch("pruv_openai.wrapper.OpenAIAgentWrapper._register_processor"):
                from pruv_openai import OpenAIAgentWrapper

                agent = MagicMock()
                wrapped = OpenAIAgentWrapper(
                    agent,
                    agent_id="pi_test_oai",
                    api_key="pv_test_key",
                )

                assert wrapped.processor is not None
                assert wrapped.processor.agent_id == "pi_test_oai"

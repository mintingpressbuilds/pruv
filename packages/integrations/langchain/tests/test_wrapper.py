"""Tests for the LangChain pruv wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_client():
    """Create a mock PruvClient."""
    client = MagicMock()
    client.act.return_value = {"id": "entry_1", "status": "ok"}
    client.get_identity_receipt.return_value = "<html>receipt</html>"
    client.verify_identity.return_value = {"valid": True, "action_count": 3}
    return client


@pytest.fixture()
def mock_agent():
    """Create a mock LangChain agent."""
    agent = MagicMock()
    agent.run.return_value = "The Q3 report shows revenue up 12%."
    return agent


class TestLangChainWrapper:
    def test_wrapper_records_actions(self, mock_client, mock_agent):
        """Wrapping and running an agent calls act() on the pruv client."""
        with patch("pruv_langchain.wrapper.PruvClient", return_value=mock_client):
            from pruv_langchain import LangChainWrapper

            wrapped = LangChainWrapper(
                mock_agent,
                agent_id="pi_test123",
                api_key="pv_test_key",
            )

            # Simulate the callback firing during agent.run
            wrapped.handler.on_llm_start({"name": "gpt-4"}, ["prompt"])
            wrapped.handler.on_chain_end({"output": "done"})

            assert mock_client.act.call_count == 2
            first_call = mock_client.act.call_args_list[0]
            assert first_call.kwargs["agent_id"] == "pi_test123"
            assert first_call.kwargs["action_scope"] == "llm.call"

    def test_wrapper_does_not_break_agent(self, mock_client, mock_agent):
        """The wrapper returns the same output as the unwrapped agent."""
        with patch("pruv_langchain.wrapper.PruvClient", return_value=mock_client):
            from pruv_langchain import LangChainWrapper

            wrapped = LangChainWrapper(
                mock_agent,
                agent_id="pi_test123",
                api_key="pv_test_key",
            )

            result = wrapped.run("Summarize the Q3 report")

            assert result == "The Q3 report shows revenue up 12%."
            mock_agent.run.assert_called_once()

    def test_wrapper_receipt(self, mock_client, mock_agent):
        """Calling receipt() returns the HTML receipt."""
        with patch("pruv_langchain.wrapper.PruvClient", return_value=mock_client):
            from pruv_langchain import LangChainWrapper

            wrapped = LangChainWrapper(
                mock_agent,
                agent_id="pi_test123",
                api_key="pv_test_key",
            )

            receipt = wrapped.receipt()

            assert "receipt" in receipt
            mock_client.get_identity_receipt.assert_called_once_with("pi_test123")

    def test_wrapper_verify(self, mock_client, mock_agent):
        """Calling verify() returns chain verification result."""
        with patch("pruv_langchain.wrapper.PruvClient", return_value=mock_client):
            from pruv_langchain import LangChainWrapper

            wrapped = LangChainWrapper(
                mock_agent,
                agent_id="pi_test123",
                api_key="pv_test_key",
            )

            result = wrapped.verify()

            assert result["valid"] is True
            mock_client.verify_identity.assert_called_once_with("pi_test123")


class TestPruvCallbackHandler:
    def test_on_tool_start(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_tool_start({"name": "calculator"}, "2 + 2")

        mock_client.act.assert_called_once()
        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "tool.execute"
        assert "calculator" in call_kwargs["action"]

    def test_on_tool_end(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_tool_end("4")

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "tool.execute"
        assert "4" in call_kwargs["action"]

    def test_on_tool_error(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_tool_error(ValueError("bad input"))

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "tool.execute"
        assert "bad input" in call_kwargs["action"]

    def test_on_agent_action(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        action = MagicMock()
        action.tool = "search"
        action.tool_input = "latest news"
        handler.on_agent_action(action)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.action"
        assert "search" in call_kwargs["action"]

    def test_on_llm_start(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_llm_start({"name": "gpt-4o"}, ["What is 2+2?"])

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "llm.call"
        assert "gpt-4o" in call_kwargs["action"]

    def test_on_chain_end(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_chain_end({"output": "final answer"})

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.complete"

    def test_on_retriever_start(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        handler.on_retriever_start({"name": "vector_store"}, "find relevant docs")

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "retriever.query"
        assert "find relevant docs" in call_kwargs["action"]

    def test_long_output_truncated(self, mock_client):
        from pruv_langchain import PruvCallbackHandler

        handler = PruvCallbackHandler(agent_id="pi_test123", client=mock_client)
        long_output = "x" * 500
        handler.on_tool_end(long_output)

        call_kwargs = mock_client.act.call_args.kwargs
        # Action string should be truncated (200 char limit on output portion)
        assert len(call_kwargs["action"]) < 250

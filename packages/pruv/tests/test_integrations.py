"""Tests for pruv integrations — LangChain, CrewAI, OpenClaw."""

import hashlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pruv.agent import Agent
from pruv.client import PruvClient


# ================================================================== #
# Shared helpers
# ================================================================== #


def _mock_client() -> MagicMock:
    mock = MagicMock(spec=PruvClient)
    mock.create_chain.return_value = {"id": "chain-001", "name": "test"}
    mock.add_entry.return_value = {"id": "entry-001", "hash": "xy_" + "a" * 64}
    mock.verify_chain.return_value = {"verified": True}
    mock.get_chain.return_value = {"id": "chain-001", "entries": []}
    mock.export_chain.return_value = "<html></html>"
    return mock


def _patch_agent():
    """Context manager that patches PruvClient so Agent never hits the network."""
    return patch("pruv.agent.PruvClient", return_value=_mock_client())


# ================================================================== #
# LangChain — PruvCallbackHandler
# ================================================================== #


@pytest.fixture(autouse=True)
def _stub_langchain_core():
    """Provide a minimal BaseCallbackHandler if langchain_core is missing."""
    if "langchain_core" not in sys.modules:
        stub = type(sys)("langchain_core")
        callbacks_mod = type(sys)("langchain_core.callbacks")

        class _BaseCallbackHandler:
            pass

        callbacks_mod.BaseCallbackHandler = _BaseCallbackHandler
        stub.callbacks = callbacks_mod
        sys.modules["langchain_core"] = stub
        sys.modules["langchain_core.callbacks"] = callbacks_mod

        # Force reimport so the integration picks up the stub
        if "pruv.integrations.langchain" in sys.modules:
            del sys.modules["pruv.integrations.langchain"]

    yield


class TestLangChainHandler:
    def _make_handler(self, record_prompts: bool = False):
        with _patch_agent():
            from pruv.integrations.langchain import PruvCallbackHandler

            return PruvCallbackHandler(
                agent_name="lc-test",
                api_key="pv_test_lc",
                record_prompts=record_prompts,
            )

    # -- init -------------------------------------------------------

    def test_init_creates_pruv_agent(self):
        handler = self._make_handler()
        assert isinstance(handler.pruv_agent, Agent)
        assert handler.pruv_agent.name == "lc-test"

    def test_default_sensitive_keys(self):
        handler = self._make_handler(record_prompts=False)
        assert "prompts" in handler.sensitive_keys
        assert "prompt" in handler.sensitive_keys
        assert "input" in handler.sensitive_keys

    def test_record_prompts_clears_sensitive(self):
        handler = self._make_handler(record_prompts=True)
        assert "prompts" not in handler.sensitive_keys

    # -- LLM events -------------------------------------------------

    def test_on_llm_start(self):
        handler = self._make_handler(record_prompts=True)
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_llm_start(
                serialized={"id": ["langchain", "llms", "gpt-4"]},
                prompts=["hello", "world"],
            )
            mock_action.assert_called_once()
            args = mock_action.call_args
            assert args[0][0] == "llm.start"
            assert args[0][1]["model"] == "gpt-4"
            assert args[0][1]["prompt_count"] == 2
            assert args[0][1]["prompts"] == ["hello", "world"]

    def test_on_llm_start_no_prompts_recorded(self):
        handler = self._make_handler(record_prompts=False)
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_llm_start(
                serialized={"id": ["langchain", "llms", "gpt-4"]},
                prompts=["secret"],
            )
            data = mock_action.call_args[0][1]
            assert "prompts" not in data

    def test_on_llm_end(self):
        handler = self._make_handler()
        response = SimpleNamespace(generations=[["gen1"], ["gen2"]])
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_llm_end(response)
            data = mock_action.call_args[0][1]
            assert data["generations"] == 2

    def test_on_llm_error(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_llm_error(ValueError("bad prompt"))
            args = mock_action.call_args[0]
            assert args[0] == "llm.error"
            assert args[1]["error_type"] == "ValueError"

    # -- tool events ------------------------------------------------

    def test_on_tool_start_with_prompts(self):
        handler = self._make_handler(record_prompts=True)
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_tool_start(
                serialized={"name": "calculator"},
                input_str="2+2",
            )
            data = mock_action.call_args[0][1]
            assert data["tool"] == "calculator"
            assert data["input"] == "2+2"

    def test_on_tool_end(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_tool_end("result text")
            data = mock_action.call_args[0][1]
            assert data["output_length"] == len("result text")

    def test_on_tool_error(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_tool_error(RuntimeError("timeout"))
            data = mock_action.call_args[0][1]
            assert data["error_type"] == "RuntimeError"

    # -- chain events -----------------------------------------------

    def test_on_chain_start(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_chain_start(
                serialized={"id": ["langchain", "chains", "qa"]},
                inputs={"question": "what?"},
            )
            data = mock_action.call_args[0][1]
            assert data["chain"] == "qa"
            assert data["input_keys"] == ["question"]

    def test_on_chain_end(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_chain_end(outputs={"answer": "42"})
            data = mock_action.call_args[0][1]
            assert data["output_keys"] == ["answer"]

    def test_on_chain_error(self):
        handler = self._make_handler()
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_chain_error(KeyError("missing"))
            args = mock_action.call_args[0]
            assert args[0] == "chain.error"

    # -- agent events -----------------------------------------------

    def test_on_agent_action(self):
        handler = self._make_handler()
        action = SimpleNamespace(tool="search", log="searching for docs")
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_agent_action(action)
            data = mock_action.call_args[0][1]
            assert data["tool"] == "search"

    def test_on_agent_finish(self):
        handler = self._make_handler()
        finish = SimpleNamespace(return_values={"output": "done"})
        with patch.object(handler.pruv_agent, "action") as mock_action:
            handler.on_agent_finish(finish)
            data = mock_action.call_args[0][1]
            assert data["output_length"] == 4  # len("done")


# ================================================================== #
# CrewAI — pruv_wrap_crew
# ================================================================== #


class TestCrewAIIntegration:
    def _make_crew(self):
        """Fake crew object that looks enough like a CrewAI Crew."""
        agent1 = SimpleNamespace(role="researcher")
        agent1.execute_task = MagicMock(return_value="research done")

        agent2 = SimpleNamespace(role="writer")
        agent2.execute_task = MagicMock(return_value="writing done")

        crew = SimpleNamespace(
            agents=[agent1, agent2],
            tasks=["t1", "t2", "t3"],
            kickoff=MagicMock(return_value="crew result"),
        )
        return crew

    def test_wrap_attaches_pruv_agent(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        assert hasattr(wrapped, "_pruv_agent")
        assert isinstance(wrapped._pruv_agent, Agent)

    def test_kickoff_records_start_and_complete(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        with patch.object(wrapped._pruv_agent, "action") as mock_action:
            result = wrapped.kickoff()
            assert result == "crew result"
            action_types = [c[0][0] for c in mock_action.call_args_list]
            assert "crew.kickoff" in action_types
            assert "crew.complete" in action_types

    def test_kickoff_records_error(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        crew.kickoff = MagicMock(side_effect=RuntimeError("boom"))
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        with patch.object(wrapped._pruv_agent, "action") as mock_action:
            with pytest.raises(RuntimeError, match="boom"):
                wrapped.kickoff()
            action_types = [c[0][0] for c in mock_action.call_args_list]
            assert "crew.kickoff" in action_types
            assert "crew.error" in action_types

    def test_agent_execute_task_wrapped(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        task = SimpleNamespace(description="Write a report on AI trends")
        with patch.object(wrapped._pruv_agent, "action") as mock_action:
            result = wrapped.agents[0].execute_task(task)
            assert result == "research done"
            action_types = [c[0][0] for c in mock_action.call_args_list]
            assert "agent.task.start" in action_types
            assert "agent.task.complete" in action_types

    def test_agent_execute_task_error(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        crew.agents[0].execute_task = MagicMock(side_effect=ValueError("failed"))
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        task = SimpleNamespace(description="bad task")
        with patch.object(wrapped._pruv_agent, "action") as mock_action:
            with pytest.raises(ValueError, match="failed"):
                wrapped.agents[0].execute_task(task)
            action_types = [c[0][0] for c in mock_action.call_args_list]
            assert "agent.task.error" in action_types

    def test_kickoff_data_includes_counts(self):
        from pruv.integrations.crewai import pruv_wrap_crew

        crew = self._make_crew()
        with _patch_agent():
            wrapped = pruv_wrap_crew(crew, agent_name="crew-test", api_key="pv_test_cr")
        with patch.object(wrapped._pruv_agent, "action") as mock_action:
            wrapped.kickoff()
            kickoff_data = mock_action.call_args_list[0][0][1]
            assert kickoff_data["agent_count"] == 2
            assert kickoff_data["task_count"] == 3


# ================================================================== #
# OpenClaw — OpenClawVerifier
# ================================================================== #


class TestOpenClawVerifier:
    def _make_verifier(self, redact: bool = True):
        with _patch_agent():
            from pruv.integrations.openclaw import OpenClawVerifier

            return OpenClawVerifier(
                api_key="pv_test_oc",
                agent_name="oc-test",
                redact_content=redact,
            )

    # -- init -------------------------------------------------------

    def test_init(self):
        v = self._make_verifier()
        assert isinstance(v.agent, Agent)
        assert v.redact_content is True

    def test_default_sensitive_keys(self):
        v = self._make_verifier()
        assert "body" in v._sensitive
        assert "password" in v._sensitive
        assert "token" in v._sensitive

    # -- skill lifecycle -------------------------------------------

    def test_before_skill(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.before_skill("send_email", {"to": "user@test.com"})
            args = mock_action.call_args[0]
            assert args[0] == "skill.start"
            assert args[1]["skill"] == "send_email"

    def test_after_skill_success(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.after_skill("send_email", "ok", success=True)
            data = mock_action.call_args[0][1]
            assert data["skill"] == "send_email"
            assert data["result_type"] == "str"

    def test_after_skill_failure(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.after_skill("send_email", RuntimeError("timeout"), success=False)
            args = mock_action.call_args[0]
            assert args[0] == "skill.error"
            assert "timeout" in args[1]["error"]

    # -- message events --------------------------------------------

    def test_message_received(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.message_received("slack", "alice", "hello")
            args = mock_action.call_args[0]
            assert args[0] == "message.received"
            assert args[1]["channel"] == "slack"
            assert args[1]["sender"] == "alice"

    def test_message_sent(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.message_sent("email", "bob@co.com", "hi")
            data = mock_action.call_args[0][1]
            assert data["recipient"] == "bob@co.com"

    def test_message_redaction_when_enabled(self):
        v = self._make_verifier(redact=True)
        with patch.object(v.agent, "action") as mock_action:
            v.message_received("slack", "alice", "secret message")
            sensitive_keys = mock_action.call_args[0][2]
            assert "content" in sensitive_keys

    def test_no_redaction_when_disabled(self):
        v = self._make_verifier(redact=False)
        with patch.object(v.agent, "action") as mock_action:
            v.message_received("slack", "alice", "open message")
            sensitive_keys = mock_action.call_args[0][2]
            assert sensitive_keys == []

    # -- resource events -------------------------------------------

    def test_file_accessed(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.file_accessed("/tmp/data.csv", "read")
            data = mock_action.call_args[0][1]
            assert data["path"] == "/tmp/data.csv"
            assert data["operation"] == "read"

    def test_api_called(self):
        v = self._make_verifier()
        with patch.object(v.agent, "action") as mock_action:
            v.api_called("https://api.example.com/data", "GET", 200)
            data = mock_action.call_args[0][1]
            assert data["url"] == "https://api.example.com/data"
            assert data["method"] == "GET"
            assert data["status"] == 200

    # -- chain access ----------------------------------------------

    def test_get_chain(self):
        v = self._make_verifier()
        with patch.object(v.agent, "chain", return_value={"id": "c1"}) as mock:
            result = v.get_chain()
            mock.assert_called_once()
            assert result["id"] == "c1"

    def test_verify(self):
        v = self._make_verifier()
        with patch.object(v.agent, "verify", return_value={"verified": True}) as mock:
            result = v.verify()
            assert result["verified"] is True

    def test_export(self):
        v = self._make_verifier()
        with patch.object(v.agent, "export", return_value="<html>") as mock:
            result = v.export()
            assert result == "<html>"

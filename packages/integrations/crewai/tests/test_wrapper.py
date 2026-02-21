"""Tests for the CrewAI pruv wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_client():
    """Create a mock PruvClient."""
    client = MagicMock()
    client.act.return_value = {"id": "entry_1", "status": "ok"}
    client.get_identity_receipt.return_value = "<html>receipt</html>"
    client.verify_identity.return_value = {"valid": True, "action_count": 5}
    return client


@pytest.fixture()
def mock_crew():
    """Create a mock CrewAI Crew."""
    crew = MagicMock()
    crew.name = "research-crew"
    crew.step_callback = None
    crew.task_callback = None
    crew.kickoff.return_value = "Research complete. AI accountability requires..."
    return crew


class TestCrewAIWrapper:
    def test_wrapper_records_kickoff_and_complete(self, mock_client, mock_crew):
        """Wrapping and running a crew records kickoff and complete."""
        with patch("pruv_crewai.wrapper.PruvClient", return_value=mock_client):
            from pruv_crewai import CrewAIWrapper

            wrapped = CrewAIWrapper(
                mock_crew,
                agent_id="pi_test_crew",
                api_key="pv_test_key",
            )

            result = wrapped.kickoff(inputs={"topic": "AI accountability"})

            # Should have at least crew_kickoff and crew_complete
            assert mock_client.act.call_count >= 2

            # First call is crew_kickoff
            first_call = mock_client.act.call_args_list[0]
            assert first_call.kwargs["action_scope"] == "crew.kickoff"
            assert "research-crew" in first_call.kwargs["action"]

            # Last call is crew_complete
            last_call = mock_client.act.call_args_list[-1]
            assert last_call.kwargs["action_scope"] == "crew.complete"

    def test_wrapper_does_not_break_crew(self, mock_client, mock_crew):
        """The wrapper returns the same output as the unwrapped crew."""
        with patch("pruv_crewai.wrapper.PruvClient", return_value=mock_client):
            from pruv_crewai import CrewAIWrapper

            wrapped = CrewAIWrapper(
                mock_crew,
                agent_id="pi_test_crew",
                api_key="pv_test_key",
            )

            result = wrapped.kickoff(inputs={"topic": "AI"})

            assert result == "Research complete. AI accountability requires..."
            mock_crew.kickoff.assert_called_once_with(inputs={"topic": "AI"})

    def test_wrapper_receipt(self, mock_client, mock_crew):
        """Calling receipt() returns the HTML receipt."""
        with patch("pruv_crewai.wrapper.PruvClient", return_value=mock_client):
            from pruv_crewai import CrewAIWrapper

            wrapped = CrewAIWrapper(
                mock_crew,
                agent_id="pi_test_crew",
                api_key="pv_test_key",
            )

            receipt = wrapped.receipt()

            assert "receipt" in receipt
            mock_client.get_identity_receipt.assert_called_once_with("pi_test_crew")

    def test_wrapper_verify(self, mock_client, mock_crew):
        """Calling verify() returns chain verification result."""
        with patch("pruv_crewai.wrapper.PruvClient", return_value=mock_client):
            from pruv_crewai import CrewAIWrapper

            wrapped = CrewAIWrapper(
                mock_crew,
                agent_id="pi_test_crew",
                api_key="pv_test_key",
            )

            result = wrapped.verify()

            assert result["valid"] is True
            mock_client.verify_identity.assert_called_once_with("pi_test_crew")


class TestPruvCrewObserver:
    def test_on_crew_start(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        observer.on_crew_start("my-crew")

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "crew.kickoff"
        assert "my-crew" in call_kwargs["action"]

    def test_on_crew_end(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        observer.on_crew_end("final output")

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "crew.complete"

    def test_on_task_start(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        task = MagicMock()
        task.description = "Research AI accountability frameworks"
        agent = MagicMock()
        agent.role = "researcher"
        observer.on_task_start(task, agent)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "task.execute"
        assert "researcher" in call_kwargs["action"]
        assert "Research AI" in call_kwargs["action"]

    def test_on_task_end(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        task = MagicMock()
        task.description = "Write summary"
        agent = MagicMock()
        agent.role = "writer"
        observer.on_task_end(task, "Summary written successfully", agent)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "task.execute"
        assert "writer" in call_kwargs["action"]

    def test_on_tool_use(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        agent = MagicMock()
        agent.role = "researcher"
        observer.on_tool_use(agent, "web_search", {"query": "AI frameworks"})

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "tool.execute"
        assert "web_search" in call_kwargs["action"]
        assert "researcher" in call_kwargs["action"]

    def test_on_agent_handoff(self, mock_client):
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)
        from_agent = MagicMock()
        from_agent.role = "researcher"
        to_agent = MagicMock()
        to_agent.role = "writer"
        observer.on_agent_handoff(from_agent, to_agent)

        call_kwargs = mock_client.act.call_args.kwargs
        assert call_kwargs["action_scope"] == "agent.handoff"
        assert "researcher" in call_kwargs["action"]
        assert "writer" in call_kwargs["action"]

    def test_multi_agent_handoff_chain(self, mock_client):
        """Multiple handoffs are all recorded in sequence."""
        from pruv_crewai import PruvCrewObserver

        observer = PruvCrewObserver(agent_id="pi_test_crew", client=mock_client)

        agents = []
        for role in ["planner", "researcher", "writer", "editor"]:
            a = MagicMock()
            a.role = role
            agents.append(a)

        # Simulate handoff chain: planner -> researcher -> writer -> editor
        for i in range(len(agents) - 1):
            observer.on_agent_handoff(agents[i], agents[i + 1])

        assert mock_client.act.call_count == 3
        for call in mock_client.act.call_args_list:
            assert call.kwargs["action_scope"] == "agent.handoff"

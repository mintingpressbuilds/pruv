"""CrewAI observer that records every action to the pruv identity chain."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient


# Framework-specific scope vocabulary
CREWAI_SCOPE_OPTIONS = [
    "task.execute",
    "tool.execute",
    "agent.handoff",
    "crew.kickoff",
    "crew.complete",
    "llm.call",
    "memory.read",
    "memory.write",
]


class PruvCrewObserver:
    """Observer that intercepts CrewAI lifecycle events and posts to pruv.

    CrewAI does not use LangChain's callback system. It has its own
    task execution lifecycle. This observer integrates at the crew level.
    """

    def __init__(self, agent_id: str, client: PruvClient) -> None:
        self.agent_id = agent_id
        self.client = client

    def on_crew_start(self, crew_name: str | None = None) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"crew_kickoff: {crew_name or 'unnamed'}",
            action_scope="crew.kickoff",
        )

    def on_crew_end(self, output: Any = None) -> None:
        self.client.act(
            agent_id=self.agent_id,
            action=f"crew_complete: {str(output)[:200]}",
            action_scope="crew.complete",
        )

    def on_task_start(self, task: Any, agent: Any) -> None:
        task_desc = getattr(task, "description", str(task))[:200]
        agent_role = getattr(agent, "role", str(agent))
        self.client.act(
            agent_id=self.agent_id,
            action=f"task_start: {task_desc} \u2014 agent: {agent_role}",
            action_scope="task.execute",
        )

    def on_task_end(self, task: Any, output: Any, agent: Any) -> None:
        task_desc = getattr(task, "description", str(task))[:100]
        agent_role = getattr(agent, "role", str(agent))
        self.client.act(
            agent_id=self.agent_id,
            action=f"task_end: {task_desc} \u2014 agent: {agent_role} \u2014 output: {str(output)[:200]}",
            action_scope="task.execute",
        )

    def on_tool_use(self, agent: Any, tool: str, input_data: Any) -> None:
        agent_role = getattr(agent, "role", str(agent))
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_use: {tool} \u2014 agent: {agent_role} \u2014 input: {str(input_data)[:200]}",
            action_scope="tool.execute",
        )

    def on_agent_handoff(
        self, from_agent: Any, to_agent: Any, context: Any = None,
    ) -> None:
        from_role = getattr(from_agent, "role", str(from_agent))
        to_role = getattr(to_agent, "role", str(to_agent))
        self.client.act(
            agent_id=self.agent_id,
            action=f"handoff: {from_role} \u2192 {to_role}",
            action_scope="agent.handoff",
        )

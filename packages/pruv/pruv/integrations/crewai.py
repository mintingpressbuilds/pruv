"""CrewAI integration for pruv.

Wraps a CrewAI Crew so that every kickoff, agent task start, and
task completion is recorded in a pruv verification chain.

Usage::

    from pruv.integrations.crewai import pruv_wrap_crew

    crew = Crew(agents=[...], tasks=[...])
    verified_crew = pruv_wrap_crew(
        crew,
        agent_name="my-crew",
        api_key="pv_live_xxx",
    )
    result = verified_crew.kickoff()

    # Get verification chain
    chain = verified_crew._pruv_agent.chain()
"""

from __future__ import annotations

from typing import Any

from pruv.agent import Agent


def pruv_wrap_crew(
    crew: Any,
    agent_name: str = "crewai-agent",
    api_key: str = "",
    endpoint: str = "https://api.pruv.dev",
) -> Any:
    """Wrap a CrewAI Crew with pruv verification.

    Returns the same crew object with its ``kickoff`` and per-agent
    ``execute_task`` methods wrapped to record entries.
    """
    pruv_agent = Agent(
        name=agent_name,
        api_key=api_key,
        endpoint=endpoint,
        metadata={"framework": "crewai"},
    )

    # Store reference so callers can access the pruv agent
    crew._pruv_agent = pruv_agent  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Wrap kickoff
    # ------------------------------------------------------------------
    original_kickoff = crew.kickoff

    def verified_kickoff(*args: Any, **kwargs: Any) -> Any:
        pruv_agent.action("crew.kickoff", {
            "agent_count": len(crew.agents) if hasattr(crew, "agents") else 0,
            "task_count": len(crew.tasks) if hasattr(crew, "tasks") else 0,
        })

        try:
            result = original_kickoff(*args, **kwargs)
            pruv_agent.action("crew.complete", {
                "status": "success",
                "result_length": len(str(result)) if result else 0,
            })
            return result
        except Exception as e:
            pruv_agent.action("crew.error", {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            })
            raise

    crew.kickoff = verified_kickoff

    # ------------------------------------------------------------------
    # Wrap each agent's execute_task if accessible
    # ------------------------------------------------------------------
    if hasattr(crew, "agents"):
        for ag in crew.agents:
            _wrap_crew_agent(ag, pruv_agent)

    return crew


def _wrap_crew_agent(crew_agent: Any, pruv_agent: Agent) -> None:
    """Wrap a single CrewAI agent's task execution."""
    if not hasattr(crew_agent, "execute_task"):
        return

    original_execute = crew_agent.execute_task

    def verified_execute(task: Any, *args: Any, **kwargs: Any) -> Any:
        role = getattr(crew_agent, "role", "unknown")
        task_desc = getattr(task, "description", "")[:200]

        pruv_agent.action("agent.task.start", {
            "agent": role,
            "task": task_desc,
        })

        try:
            result = original_execute(task, *args, **kwargs)
            pruv_agent.action("agent.task.complete", {
                "agent": role,
                "status": "success",
            })
            return result
        except Exception as e:
            pruv_agent.action("agent.task.error", {
                "agent": role,
                "status": "error",
                "error": str(e),
            })
            raise

    crew_agent.execute_task = verified_execute

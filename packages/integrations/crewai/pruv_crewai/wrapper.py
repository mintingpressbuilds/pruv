"""One-line wrapper for any CrewAI crew."""

from __future__ import annotations

from typing import Any

from pruv import PruvClient

from .observer import PruvCrewObserver


class CrewAIWrapper:
    """Wrap any CrewAI crew with automatic pruv verification.

    Usage::

        from pruv_crewai import CrewAIWrapper

        crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
        verified = CrewAIWrapper(crew, agent_id="pi_abc123", api_key="pv_live_...")
        result = verified.kickoff(inputs={"topic": "AI accountability"})
        receipt = verified.receipt()
    """

    def __init__(
        self,
        crew: Any,
        agent_id: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
    ) -> None:
        self.crew = crew
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self.observer = PruvCrewObserver(agent_id=agent_id, client=self.client)
        self._inject_observer()

    def _inject_observer(self) -> None:
        """Attach the observer to the crew's execution lifecycle."""
        if hasattr(self.crew, "step_callback"):
            original = self.crew.step_callback

            def wrapped_callback(step: Any) -> Any:
                task = getattr(step, "task", None)
                output = getattr(step, "output", None)
                agent = getattr(step, "agent", None)
                if task and agent:
                    self.observer.on_task_end(task, output, agent)
                if original:
                    return original(step)
                return None

            self.crew.step_callback = wrapped_callback

        if hasattr(self.crew, "task_callback"):
            original_task = self.crew.task_callback

            def wrapped_task_callback(task_output: Any) -> Any:
                self.observer.on_task_end(
                    task_output,
                    getattr(task_output, "raw", str(task_output)[:200]),
                    getattr(task_output, "agent", "unknown"),
                )
                if original_task:
                    return original_task(task_output)
                return None

            self.crew.task_callback = wrapped_task_callback

    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        """Run the crew. Every action is recorded automatically."""
        crew_name = getattr(self.crew, "name", None) or "crew"
        self.observer.on_crew_start(crew_name)
        result = self.crew.kickoff(inputs=inputs)
        self.observer.on_crew_end(str(result)[:200] if result else None)
        return result

    def receipt(self) -> str:
        """Get the self-verifying HTML receipt for this crew."""
        return self.client.get_identity_receipt(self.agent_id)

    def verify(self) -> dict[str, Any]:
        """Verify the crew's chain integrity."""
        return self.client.verify_identity(self.agent_id)

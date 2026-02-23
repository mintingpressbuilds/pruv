"""Action interceptor that wraps OpenClaw skill execution with pruv recording."""

from __future__ import annotations

from typing import Any, Callable

from .plugin import PruvOpenClawPlugin


class PruvActionInterceptor:
    """Wraps an OpenClaw agent's execute method to automatically record actions.

    Usage::

        from pruv_openclaw import PruvActionInterceptor

        interceptor = PruvActionInterceptor(agent_id="pi_abc123", api_key="pv_live_...")
        wrapped_execute = interceptor.wrap(original_execute_fn)
        result = wrapped_execute("read_file", {"path": "/app/data.json"})
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
    ) -> None:
        self.plugin = PruvOpenClawPlugin(
            agent_id=agent_id,
            api_key=api_key,
            endpoint=endpoint,
        )

    def wrap(self, execute_fn: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap an execute function with automatic before/after recording."""
        plugin = self.plugin

        def wrapped(action_type: str, payload: dict[str, Any] | None = None, **kwargs: Any) -> Any:
            payload = payload or {}
            plugin.before_action(action_type, payload)
            try:
                result = execute_fn(action_type, payload, **kwargs)
                plugin.after_action(action_type, result if isinstance(result, dict) else {"result": str(result)[:200]})
                return result
            except Exception as exc:
                plugin.on_error(action_type, exc)
                raise

        return wrapped

    def receipt(self) -> str:
        """Get the self-verifying HTML receipt."""
        return self.plugin.receipt()

    def verify(self) -> dict[str, Any]:
        """Verify the agent's chain integrity."""
        return self.plugin.verify()

"""Basic example: use the pruv OpenClaw plugin."""

from pruv_openclaw import PruvOpenClawPlugin, PruvActionInterceptor

# Option 1: Direct plugin usage
# plugin = PruvOpenClawPlugin(agent_id="pi_abc123", api_key="pv_live_...")
# plugin.before_action("read_file", {"path": "/app/data.json"})
# plugin.after_action("read_file", {"content": "..."})
# receipt = plugin.receipt()

# Option 2: Interceptor wraps an execute function
# interceptor = PruvActionInterceptor(agent_id="pi_abc123", api_key="pv_live_...")
# wrapped_execute = interceptor.wrap(original_execute_fn)
# result = wrapped_execute("read_file", {"path": "/app/data.json"})
# receipt = interceptor.receipt()

# Option 3: Config-driven (openclaw.config.yaml)
# agent_id: pv_agent_7f3a1c2e
# pruv_api_key: pv_live_...
# plugins:
#   - pruv_openclaw.PruvOpenClawPlugin

"""Basic example: wrap an OpenAI Agents SDK agent with pruv verification."""

from pruv_openai import OpenAIAgentWrapper

# 1. Build your agent as usual
# from agents import Agent, function_tool
#
# @function_tool
# def search(query: str) -> str:
#     return f"Results for: {query}"
#
# agent = Agent(
#     name="assistant",
#     instructions="You are a helpful assistant",
#     tools=[search],
# )

# 2. Wrap with pruv — one line
# verified = OpenAIAgentWrapper(agent, agent_id="pi_abc123", api_key="pv_live_...")

# 3. Run as normal — every action is automatically recorded
# result = await verified.run("Analyze this document")

# 4. Get the receipt
# receipt = verified.receipt()
# print(receipt)

# 5. Verify chain integrity
# verification = verified.verify()
# print(verification)

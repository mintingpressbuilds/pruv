"""Basic example: wrap a LangChain agent with pruv verification."""

from pruv_langchain import LangChainWrapper

# 1. Build your agent as usual
# from langchain.agents import initialize_agent, AgentType
# from langchain_openai import ChatOpenAI
# from langchain.tools import Tool
#
# llm = ChatOpenAI(model="gpt-4o")
# tools = [Tool(name="search", func=search_fn, description="Search the web")]
# agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

# 2. Wrap with pruv — one line
# verified = LangChainWrapper(agent, agent_id="pi_abc123", api_key="pv_live_...")

# 3. Run as normal — every action is automatically recorded
# result = verified.run("Summarize the Q3 report")

# 4. Get the receipt
# receipt = verified.receipt()
# print(receipt)

# 5. Verify chain integrity
# verification = verified.verify()
# print(verification)

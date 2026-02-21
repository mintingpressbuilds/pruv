"""Basic example: wrap a CrewAI crew with pruv verification."""

from pruv_crewai import CrewAIWrapper

# 1. Build your crew as usual
# from crewai import Agent, Crew, Task
#
# researcher = Agent(role="researcher", goal="Find information", backstory="...")
# writer = Agent(role="writer", goal="Write reports", backstory="...")
# research_task = Task(description="Research AI accountability", agent=researcher)
# write_task = Task(description="Write summary", agent=writer)
# crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])

# 2. Wrap with pruv — one line
# verified = CrewAIWrapper(crew, agent_id="pi_abc123", api_key="pv_live_...")

# 3. Run as normal — every action is automatically recorded
# result = verified.kickoff(inputs={"topic": "AI accountability"})

# 4. Get the receipt
# receipt = verified.receipt()
# print(receipt)

# 5. Verify chain integrity
# verification = verified.verify()
# print(verification)

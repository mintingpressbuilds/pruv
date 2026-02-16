"use client";

import { useState } from "react";
import { CodeBlock } from "./code-block";

const INTEGRATIONS = [
  {
    name: "LangChain",
    code: `from pruv.integrations.langchain import PruvCallbackHandler

handler = PruvCallbackHandler(api_key="pv_live_xxx")
agent = initialize_agent(tools, llm, callbacks=[handler])
agent.run("Summarize the quarterly report")

# Every LLM call, tool use, and agent action is now verified`,
  },
  {
    name: "CrewAI",
    code: `from pruv.integrations.crewai import pruv_wrap_crew

crew = Crew(agents=[researcher, writer], tasks=[...])
verified_crew = pruv_wrap_crew(crew, api_key="pv_live_xxx")
result = verified_crew.kickoff()

# Crew kickoff, agent tasks, and results are all recorded`,
  },
  {
    name: "OpenClaw",
    code: `from pruv.integrations.openclaw import OpenClawVerifier

verifier = OpenClawVerifier(api_key="pv_live_xxx")
verifier.before_skill("search", {"query": "latest news"})
verifier.after_skill("search", results, success=True)

# Every skill execution is now verified`,
  },
];

export function IntegrationTabs() {
  const [active, setActive] = useState(0);

  return (
    <div className="int-tabs">
      <div className="int-tab-bar">
        {INTEGRATIONS.map((intg, i) => (
          <button
            key={intg.name}
            className={`int-tab${i === active ? " active" : ""}`}
            onClick={() => setActive(i)}
          >
            {intg.name}
          </button>
        ))}
      </div>
      <CodeBlock code={INTEGRATIONS[active].code} label="python" />
    </div>
  );
}

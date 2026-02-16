"use client";

import { useState } from "react";
import { CodeBlock } from "./code-block";

const INTEGRATIONS = [
  {
    name: "LangChain",
    code: `from pruv.integrations.langchain import PruvCallbackHandler

handler = PruvCallbackHandler(api_key="pv_live_xxx")
agent = initialize_agent(tools, llm, callbacks=[handler])
# every LLM call, tool use, and chain step — receipted.`,
  },
  {
    name: "CrewAI",
    code: `from pruv.integrations.crewai import pruv_wrap_crew

verified_crew = pruv_wrap_crew(crew, api_key="pv_live_xxx")
result = verified_crew.kickoff()
# every agent task — receipted.`,
  },
  {
    name: "OpenClaw",
    code: `from pruv.integrations.openclaw import OpenClawVerifier

verifier = OpenClawVerifier(api_key="pv_live_xxx")
# every skill execution — receipted.`,
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
      <p className="int-subtext">
        More integrations coming. Any system that performs actions can be verified.
      </p>
    </div>
  );
}

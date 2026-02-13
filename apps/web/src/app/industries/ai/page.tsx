"use client";

import { IndustryPage } from "@/components/industry-page";

export default function AIIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
        </svg>
      }
      title="AI & Autonomous Systems"
      subtitle="When agents act autonomously, you need proof of what they did, what data they accessed, and what decisions they made. pruv brings cryptographic accountability to AI systems."
      problem={{
        title: "The accountability gap",
        description:
          "AI agents make decisions and take actions without human oversight. When something goes wrong, there is no reliable way to reconstruct what happened. Traditional logging is insufficient because logs can be modified, are unstructured, and do not capture the full context of state transitions.",
        points: [
          "Agent actions are opaque and difficult to audit after the fact",
          "LLM outputs are non-deterministic and hard to reproduce",
          "Tool calls and API interactions leave fragmented, inconsistent trails",
          "Regulatory frameworks (EU AI Act, NIST AI RMF) demand explainability",
          "Multi-agent systems create complex, interleaved action sequences",
          "Traditional observability tools were not designed for autonomous decision-making",
        ],
      }}
      solution={{
        title: "Prove what agents did.",
        description:
          "With pruv, every agent action becomes a verifiable state transition. The input prompt, retrieved context, model output, and downstream effects are all captured as X \u2192 Y records with cryptographic proof.",
        xLabel: "Agent input + context",
        yLabel: "Agent output + actions",
        example:
          'Example: X = {prompt: "Analyze Q3 revenue", context: [doc1, doc2]} \u2192 Y = {response: "Revenue increased 15%...", actions: [query_db, generate_chart]}',
      }}
      codeExample={{
        filename: "agent.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(chain="customer_support_agent")
async def handle_ticket(ticket: dict) -> dict:
    # X = ticket (customer request + metadata)

    # Retrieve context
    context = await vector_db.search(ticket["description"])
    checkpoint("context_retrieved", context)

    # Generate response
    response = await llm.complete(
        prompt=ticket["description"],
        context=context,
        tools=["search_kb", "create_jira", "send_email"]
    )
    checkpoint("llm_response", response)

    # Execute tool calls
    results = []
    for tool_call in response.tool_calls:
        result = await execute_tool(tool_call)
        results.append(result)
        checkpoint(f"tool_{tool_call.name}", result)

    return {
        "response": response.text,
        "tool_results": results,
        "confidence": response.confidence
    }
    # Y = full agent output with all actions taken
    # XY = verifiable proof of the entire agent workflow`,
      }}
      useCases={[
        {
          title: "LLM output verification",
          description:
            "Capture the exact prompt, context, and model output for every LLM call. When a model produces unexpected results, you can prove exactly what inputs led to that output and whether the context was appropriate.",
        },
        {
          title: "Tool call audit trails",
          description:
            "Every tool call an agent makes (database queries, API calls, file operations) becomes a verified state transition. Reconstruct the full sequence of actions any agent took, with cryptographic proof that the record has not been tampered with.",
        },
        {
          title: "Multi-agent coordination",
          description:
            "When multiple agents collaborate, pruv's chain rule links their actions into a single verifiable sequence. Prove which agent did what, in what order, and how they influenced each other's decisions.",
        },
        {
          title: "Regulatory compliance",
          description:
            "Meet EU AI Act and NIST AI RMF requirements for AI explainability and auditability. Generate compliance reports showing the complete decision history of any AI system, backed by cryptographic proof.",
        },
        {
          title: "RAG pipeline verification",
          description:
            "Verify the complete retrieval-augmented generation pipeline: what documents were retrieved, what context was provided to the model, and what output was generated. Prove that the model was given appropriate context.",
        },
        {
          title: "Agent safety monitoring",
          description:
            "Set up real-time verification of agent actions against safety constraints. If an agent takes an action that violates a policy, the XY record provides irrefutable proof of what happened for post-incident analysis.",
        },
      ]}
    />
  );
}

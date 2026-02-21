# pruv Agent Framework Integration — Complete Build Document

## Overview

This document instructs Claude Code to build complete, tested, production-ready integrations between pruv and four AI agent frameworks: LangChain, CrewAI, OpenAI Agents, and OpenClaw.

Each integration automatically records every agent action into the pruv identity chain without requiring manual logging. The developer wraps their existing agent in one line. Everything else is automatic.

-----

## Architecture

Every integration follows the same pattern:

```
Developer's agent (any framework)
        │
pruv wrapper (framework-specific)
        │
POST /api/identity/act  ←— automatic on every action
        │
pruv identity chain
        │
Receipt
```

The wrapper intercepts every agent action before and after execution, extracts the relevant state, and posts to the pruv act endpoint. The developer's code is unchanged. pruv runs underneath it.

-----

## Shared Requirements

Before building any integration, confirm these exist and work correctly:

- `POST /api/identity/act` endpoint — accepts agent_id, action string, action_scope
- `GET /api/identity/receipt/{agent_id}` endpoint — returns full receipt
- `POST /api/identity/register` endpoint — creates new agent identity
- API key authentication with write scope on act endpoint
- Postgres persistence confirmed (chains do not disappear on redeploy)
- Receipt export working without authorization errors

**Do not build any integration until all four endpoints above are confirmed working end to end.**

-----

## Phase 1 — LangChain Integration

### Why LangChain first

Largest surface area. Most widely used agent framework. Millions of downloads per month. If only one integration ships, this is the one.

### What to build

A Python package `pruv-langchain` that wraps any LangChain agent or chain and automatically records every action to the pruv identity chain.

### File structure

```
packages/integrations/langchain/
├── pruv_langchain/
│   ├── __init__.py
│   ├── wrapper.py          ← main wrapper class
│   ├── callback.py         ← LangChain callback handler
│   ├── middleware.py       ← action interceptor
│   └── receipt.py         ← receipt retrieval and formatting
├── tests/
│   ├── __init__.py
│   ├── test_wrapper.py
│   ├── test_callback.py
│   └── test_receipt.py
├── examples/
│   └── basic_agent.py
├── pyproject.toml
└── README.md
```

### Core implementation

**callback.py** — LangChain has a native callback system. Use it. Do not monkey-patch.

```python
from langchain.callbacks.base import BaseCallbackHandler
from pruv import PruvClient

class PruvCallbackHandler(BaseCallbackHandler):
    def __init__(self, agent_id: str, api_key: str, client: PruvClient):
        self.agent_id = agent_id
        self.api_key = api_key
        self.client = client

    def on_tool_start(self, serialized, input_str, **kwargs):
        # Record tool invocation — scope: tool.execute
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_start: {serialized.get('name', 'unknown')} — {input_str[:200]}",
            action_scope="tool.execute"
        )

    def on_tool_end(self, output, **kwargs):
        # Record tool completion
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_end: {str(output)[:200]}",
            action_scope="tool.execute"
        )

    def on_agent_action(self, action, **kwargs):
        # Record agent decision
        self.client.act(
            agent_id=self.agent_id,
            action=f"agent_action: {action.tool} — {str(action.tool_input)[:200]}",
            action_scope="agent.action"
        )

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.client.act(
            agent_id=self.agent_id,
            action=f"llm_start: {serialized.get('name', 'unknown')}",
            action_scope="llm.call"
        )

    def on_chain_end(self, outputs, **kwargs):
        self.client.act(
            agent_id=self.agent_id,
            action=f"chain_end: {str(outputs)[:200]}",
            action_scope="agent.complete"
        )
```

**wrapper.py** — The developer-facing interface. One class, one method.

```python
from pruv import PruvClient
from .callback import PruvCallbackHandler
from .receipt import get_receipt

class LangChainWrapper:
    def __init__(self, agent, agent_id: str, api_key: str):
        self.agent = agent
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key)
        self.handler = PruvCallbackHandler(
            agent_id=agent_id,
            api_key=api_key,
            client=self.client
        )
        # Inject callback into agent
        if hasattr(agent, 'callbacks'):
            agent.callbacks = (agent.callbacks or []) + [self.handler]

    def run(self, input: str, **kwargs):
        return self.agent.run(input, callbacks=[self.handler], **kwargs)

    def receipt(self):
        return get_receipt(self.agent_id, self.client)
```

**Developer usage — must work exactly like this:**

```python
from pruv_langchain import LangChainWrapper

# Existing agent — zero changes
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

# One line
verified = LangChainWrapper(agent, agent_id="pv_agent_abc123", api_key="pv_live_...")

# Runs exactly as before
result = verified.run("Summarize the Q3 report")

# Receipt
receipt = verified.receipt()
print(receipt)
```

### Scope vocabulary for LangChain

Add these to the pruv framework scope options for LangChain:

```python
LANGCHAIN_SCOPE_OPTIONS = [
    "tool.execute",       # agent uses a tool
    "llm.call",           # agent calls the language model
    "agent.action",       # agent makes a decision
    "agent.complete",     # agent finishes a run
    "chain.run",          # a chain executes
    "retriever.query",    # retrieval augmented generation query
    "memory.read",        # agent reads from memory
    "memory.write",       # agent writes to memory
]
```

### Tests required

```python
# test_wrapper.py

def test_wrapper_records_actions():
    # Mock pruv client
    # Create minimal LangChain agent
    # Wrap with LangChainWrapper
    # Run agent
    # Assert act() was called at least once
    # Assert agent_id matches

def test_wrapper_receipt():
    # Wrap agent
    # Run agent
    # Call receipt()
    # Assert receipt contains action entries
    # Assert receipt.verified is True

def test_wrapper_does_not_break_agent():
    # Wrap agent
    # Assert agent still returns correct output
    # Assert wrapping adds zero breaking changes

def test_out_of_scope_action_recorded():
    # Register agent with limited scope
    # Attempt action outside scope
    # Assert action is recorded as out_of_scope in chain
```

### pyproject.toml

```toml
[project]
name = "pruv-langchain"
version = "0.1.0"
description = "pruv verification layer for LangChain agents"
dependencies = [
    "pruv>=1.0.0",
    "langchain>=0.1.0",
]

[project.urls]
Homepage = "https://pruv.dev"
Repository = "https://github.com/mintingpressbuilds/pruv"
```

### Publish to PyPI

After tests pass, publish as `pruv-langchain` using the GitHub Actions workflow pattern established for xycore. Tag `v0.1.0` to trigger publish.

-----

## Phase 2 — CrewAI Integration

### What to build

`pruv-crewai` — wraps any CrewAI crew or agent and records every task execution, tool use, and agent handoff to the pruv identity chain.

### File structure

```
packages/integrations/crewai/
├── pruv_crewai/
│   ├── __init__.py
│   ├── wrapper.py
│   ├── observer.py        ← CrewAI uses observers not callbacks
│   └── receipt.py
├── tests/
│   ├── __init__.py
│   └── test_wrapper.py
├── examples/
│   └── basic_crew.py
├── pyproject.toml
└── README.md
```

### Core implementation

CrewAI does not use LangChain's callback system. It has its own task execution lifecycle. The integration intercepts at the crew level.

**observer.py**

```python
from pruv import PruvClient

class PruvCrewObserver:
    def __init__(self, agent_id: str, client: PruvClient):
        self.agent_id = agent_id
        self.client = client

    def on_task_start(self, task, agent):
        self.client.act(
            agent_id=self.agent_id,
            action=f"task_start: {task.description[:200]} — agent: {agent.role}",
            action_scope="task.execute"
        )

    def on_task_end(self, task, output, agent):
        self.client.act(
            agent_id=self.agent_id,
            action=f"task_end: {task.description[:100]} — output: {str(output)[:200]}",
            action_scope="task.execute"
        )

    def on_tool_use(self, agent, tool, input_data):
        self.client.act(
            agent_id=self.agent_id,
            action=f"tool_use: {tool} — agent: {agent.role} — input: {str(input_data)[:200]}",
            action_scope="tool.execute"
        )

    def on_agent_handoff(self, from_agent, to_agent, context):
        self.client.act(
            agent_id=self.agent_id,
            action=f"handoff: {from_agent.role} → {to_agent.role}",
            action_scope="agent.handoff"
        )
```

**wrapper.py**

```python
from pruv import PruvClient
from .observer import PruvCrewObserver
from .receipt import get_receipt

class CrewAIWrapper:
    def __init__(self, crew, agent_id: str, api_key: str):
        self.crew = crew
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key)
        self.observer = PruvCrewObserver(agent_id=agent_id, client=self.client)
        # Inject observer into crew
        self._inject_observer()

    def _inject_observer(self):
        # Attach observer to crew's execution lifecycle
        if hasattr(self.crew, 'step_callback'):
            original = self.crew.step_callback
            def wrapped_callback(step):
                self.observer.on_task_end(step.task, step.output, step.agent)
                if original:
                    original(step)
            self.crew.step_callback = wrapped_callback

    def kickoff(self, inputs=None):
        return self.crew.kickoff(inputs=inputs)

    def receipt(self):
        return get_receipt(self.agent_id, self.client)
```

**Developer usage:**

```python
from pruv_crewai import CrewAIWrapper

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])

verified = CrewAIWrapper(crew, agent_id="pv_agent_abc123", api_key="pv_live_...")

result = verified.kickoff(inputs={"topic": "AI accountability"})

receipt = verified.receipt()
```

### Scope vocabulary for CrewAI

```python
CREWAI_SCOPE_OPTIONS = [
    "task.execute",       # agent executes a task
    "tool.execute",       # agent uses a tool
    "agent.handoff",      # task handed from one agent to another
    "crew.kickoff",       # crew starts execution
    "crew.complete",      # crew finishes
    "llm.call",           # underlying LLM called
    "memory.read",        # agent reads crew memory
    "memory.write",       # agent writes to crew memory
]
```

### Tests required

```python
def test_crewai_wrapper_records_task_execution()
def test_crewai_wrapper_records_agent_handoffs()
def test_crewai_wrapper_receipt_contains_all_agents()
def test_crewai_wrapper_does_not_break_crew()
def test_multi_agent_handoff_chain()
```

-----

## Phase 3 — OpenAI Agents Integration

### What to build

`pruv-openai` — wraps OpenAI Agents SDK and records every agent action, tool call, handoff, and completion.

### File structure

```
packages/integrations/openai/
├── pruv_openai/
│   ├── __init__.py
│   ├── wrapper.py
│   ├── tracing.py         ← OpenAI Agents has a tracing system
│   └── receipt.py
├── tests/
│   ├── __init__.py
│   └── test_wrapper.py
├── examples/
│   └── basic_agent.py
├── pyproject.toml
└── README.md
```

### Core implementation

OpenAI Agents SDK has a native tracing system via `add_trace_processor`. Use it.

**tracing.py**

```python
from agents import TracingProcessor, Trace, Span
from pruv import PruvClient

class PruvTraceProcessor(TracingProcessor):
    def __init__(self, agent_id: str, client: PruvClient):
        self.agent_id = agent_id
        self.client = client

    def on_trace_start(self, trace: Trace):
        self.client.act(
            agent_id=self.agent_id,
            action=f"trace_start: {trace.name}",
            action_scope="agent.start"
        )

    def on_span_end(self, span: Span):
        self.client.act(
            agent_id=self.agent_id,
            action=f"span_end: {span.span_data.type if hasattr(span.span_data, 'type') else 'unknown'} — {str(span.span_data)[:200]}",
            action_scope=self._scope_from_span(span)
        )

    def on_trace_end(self, trace: Trace):
        self.client.act(
            agent_id=self.agent_id,
            action=f"trace_end: {trace.name}",
            action_scope="agent.complete"
        )

    def _scope_from_span(self, span):
        if hasattr(span.span_data, 'type'):
            t = span.span_data.type
            if 'tool' in t: return "tool.execute"
            if 'handoff' in t: return "agent.handoff"
            if 'llm' in t or 'model' in t: return "llm.call"
        return "agent.action"
```

**wrapper.py**

```python
from agents import add_trace_processor
from pruv import PruvClient
from .tracing import PruvTraceProcessor
from .receipt import get_receipt

class OpenAIAgentWrapper:
    def __init__(self, agent, agent_id: str, api_key: str):
        self.agent = agent
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key)
        self.processor = PruvTraceProcessor(agent_id=agent_id, client=self.client)
        add_trace_processor(self.processor)

    async def run(self, input: str, **kwargs):
        from agents import Runner
        return await Runner.run(self.agent, input, **kwargs)

    def receipt(self):
        return get_receipt(self.agent_id, self.client)
```

**Developer usage:**

```python
from pruv_openai import OpenAIAgentWrapper

agent = Agent(name="assistant", instructions="You are a helpful assistant", tools=[...])

verified = OpenAIAgentWrapper(agent, agent_id="pv_agent_abc123", api_key="pv_live_...")

result = await verified.run("Analyze this document")

receipt = verified.receipt()
```

### Scope vocabulary for OpenAI Agents

```python
OPENAI_AGENTS_SCOPE_OPTIONS = [
    "agent.start",        # agent run begins
    "agent.action",       # agent takes action
    "agent.handoff",      # handoff to another agent
    "agent.complete",     # agent run completes
    "tool.execute",       # tool called
    "llm.call",           # model called
    "guardrail.check",    # input/output guardrail runs
]
```

-----

## Phase 4 — OpenClaw Integration (Complete the wiring)

### Current state

The OpenClaw integration is partially built:

- Agent type exists in the dashboard
- Scope vocabulary defined
- Toggle UI live
- `POST /api/identity/act` endpoint live
- Agent ID + API key config documented

### What is missing

The automatic action recording. Right now the developer must manually call the act endpoint for each action. This needs to be automatic.

### What to build

`pruv-openclaw` — an OpenClaw plugin that intercepts every agent action and posts to the pruv act endpoint automatically.

### File structure

```
packages/integrations/openclaw/
├── pruv_openclaw/
│   ├── __init__.py
│   ├── plugin.py          ← OpenClaw plugin interface
│   ├── interceptor.py     ← action interceptor
│   └── receipt.py
├── tests/
│   ├── __init__.py
│   └── test_plugin.py
├── examples/
│   └── basic_config.py
├── pyproject.toml
└── README.md
```

### Core implementation

OpenClaw is open source Python. It supports plugins via a config-defined plugin system.

**plugin.py**

```python
from pruv import PruvClient

class PruvOpenClawPlugin:
    name = "pruv"
    description = "Cryptographic accountability layer for OpenClaw agents"

    def __init__(self, agent_id: str, api_key: str):
        self.agent_id = agent_id
        self.client = PruvClient(api_key=api_key)

    def before_action(self, action_type: str, payload: dict):
        self.client.act(
            agent_id=self.agent_id,
            action=f"{action_type}: {str(payload)[:200]}",
            action_scope=self._scope(action_type)
        )

    def after_action(self, action_type: str, result: dict):
        self.client.act(
            agent_id=self.agent_id,
            action=f"{action_type}_complete: {str(result)[:200]}",
            action_scope=self._scope(action_type)
        )

    def _scope(self, action_type: str) -> str:
        scope_map = {
            "read_file": "file.read",
            "write_file": "file.write",
            "delete_file": "file.delete",
            "send_email": "email.send",
            "read_email": "email.read",
            "browse": "browser.interact",
            "execute": "system.execute",
            "send_message": "messaging.send",
        }
        return scope_map.get(action_type, "agent.action")

    def receipt(self):
        from .receipt import get_receipt
        return get_receipt(self.agent_id, self.client)
```

**Developer config — must work exactly like this:**

```yaml
# openclaw.config.yaml
agent_id: pv_agent_7f3a1c2e
pruv_api_key: pv_live_...

plugins:
  - pruv_openclaw.PruvOpenClawPlugin
```

-----

## Shared receipt.py (used by all integrations)

Every integration uses the same receipt retrieval pattern. Build this once as a shared utility.

```python
# pruv/integrations/shared/receipt.py

def get_receipt(agent_id: str, client) -> dict:
    response = client.get(f"/api/identity/receipt/{agent_id}")
    if response.status_code != 200:
        raise Exception(f"Receipt retrieval failed: {response.status_code}")
    return response.json()

def format_receipt(receipt: dict) -> str:
    lines = [
        f"pruv receipt",
        f"{'─' * 45}",
        f"Agent:     {receipt.get('name', 'unknown')}",
        f"Framework: {receipt.get('framework', 'unknown')}",
        f"Owner:     {receipt.get('owner', 'unknown')}",
        f"",
        f"Actions:   {receipt.get('action_count', 0)}",
        f"Verified:  {receipt.get('verified_count', 0)}/{receipt.get('action_count', 0)}",
        f"In scope:  {receipt.get('in_scope_count', 0)}/{receipt.get('action_count', 0)}",
        f"",
        f"Chain:     {'intact ✓' if receipt.get('chain_valid') else 'BROKEN ✗'}",
        f"{'─' * 45}",
        f"XY:  {receipt.get('xy_hash', 'unknown')}",
    ]
    return "\n".join(lines)
```

-----

## Integration into the pruv dashboard

After all four integrations are built, update the dashboard to reflect the connection state.

When an agent is registered with a framework type and has logged at least one action via the act endpoint — show a green connected indicator next to the framework name.

```
Framework:  LangChain  ● Connected
Last action: 4 minutes ago
Actions today: 47
```

When no actions have been logged since registration — show pending:

```
Framework:  LangChain  ○ Pending
Copy agent ID → add to your LangChain config to begin
```

-----

## Build sequence

Execute in this exact order. Do not begin a phase until the previous phase is fully tested.

```
Phase 0 — Confirm all API endpoints work correctly
Phase 1 — LangChain integration (pruv-langchain on PyPI)
Phase 2 — CrewAI integration (pruv-crewai on PyPI)
Phase 3 — OpenAI Agents integration (pruv-openai on PyPI)
Phase 4 — OpenClaw integration complete (pruv-openclaw on PyPI)
Phase 5 — Dashboard connected/pending indicators
```

-----

## Testing standard for every integration

Every integration must pass all four test categories before it is considered complete:

**1. Connection test** — integration posts to act endpoint successfully
**2. Non-breaking test** — wrapped agent returns identical output to unwrapped agent
**3. Receipt test** — receipt is retrievable and contains all recorded actions
**4. Scope test** — out-of-scope actions are recorded and flagged correctly

No integration ships without all four passing.

-----

## After all four integrations are live

These four commands need to work for any developer:

```bash
pip install pruv-langchain
pip install pruv-crewai
pip install pruv-openai
pip install pruv-openclaw
```

Each one wraps the respective framework in one line. Every action automatically chained. Every receipt available on demand.

When all four are live — the GitHub issue to LangChain, the DM to Harrison Chase, and the Hacker News post are all executable from a position of already having shipped working integrations for every major framework.

That is the position to be in before any outreach begins.

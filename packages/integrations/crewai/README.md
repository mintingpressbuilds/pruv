# pruv-crewai

[![pruv-crewai](https://img.shields.io/badge/pruv--crewai-v0.1.0-green)](https://pypi.org/project/pruv-crewai/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv-crewai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Cryptographic verification for CrewAI agents. Every crew kickoff, task execution, agent handoff, and tool usage — automatically recorded into a pruv identity chain.

```bash
pip install pruv-crewai
```

## Usage

```python
from pruv_crewai import CrewAIWrapper

wrapped = CrewAIWrapper(crew, agent_id="agent-id", api_key="pv_live_...")
result = wrapped.kickoff()
receipt = wrapped.receipt()
```

Wraps CrewAI's `kickoff()` with automatic recording. Your crew code stays unchanged. pruv runs underneath it.

## How it works

`PruvCrewObserver` intercepts CrewAI lifecycle events:

- `on_crew_start` / `on_crew_end` — crew lifecycle
- `on_task_start` / `on_task_end` — individual task execution
- `on_tool_use` — tool invocations
- `on_agent_handoff` — agent-to-agent handoffs

Every event is posted to the pruv identity chain via `POST /api/identity/act`. The chain is tamper-evident — modify one entry and verification detects exactly where.

## Links

- [pruv.dev](https://pruv.dev)
- [Documentation](https://docs.pruv.dev)
- [GitHub](https://github.com/mintingpressbuilds/pruv)

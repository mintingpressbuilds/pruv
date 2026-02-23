# pruv-openai

[![pruv-openai](https://img.shields.io/badge/pruv--openai-v0.1.0-green)](https://pypi.org/project/pruv-openai/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv-openai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Cryptographic verification for OpenAI Agents SDK. Every tool call, guardrail check, agent handoff, and LLM call — automatically recorded into a pruv identity chain.

```bash
pip install pruv-openai
```

## Usage

```python
from pruv_openai import OpenAIAgentWrapper

wrapped = OpenAIAgentWrapper(agent, agent_id="agent-id", api_key="pv_live_...")
result = await wrapped.run("analyze the quarterly report")
receipt = wrapped.receipt()
```

Implements the OpenAI Agents SDK `TracingProcessor` protocol. Your agent code stays unchanged. pruv runs underneath it.

## How it works

`PruvTraceProcessor` implements the `TracingProcessor` protocol with automatic scope detection:

- `tool` spans → `tool.execute` scope
- `handoff` spans → `agent.handoff` scope
- `llm` / `model` / `generation` spans → `llm.call` scope
- `guardrail` spans → `guardrail.check` scope

Every span is posted to the pruv identity chain via `POST /api/identity/act`. The chain is tamper-evident — modify one entry and verification detects exactly where.

## Links

- [pruv.dev](https://pruv.dev)
- [Documentation](https://docs.pruv.dev)
- [GitHub](https://github.com/mintingpressbuilds/pruv)

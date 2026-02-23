# pruv-langchain

[![pruv-langchain](https://img.shields.io/badge/pruv--langchain-v0.1.0-green)](https://pypi.org/project/pruv-langchain/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv-langchain/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Cryptographic verification for LangChain agents. Every tool call, LLM invocation, chain execution, and agent action — automatically recorded into a pruv identity chain.

```bash
pip install pruv-langchain
```

## Usage

```python
from pruv_langchain import LangChainWrapper

wrapped = LangChainWrapper(agent, agent_id="agent-id", api_key="pv_live_...")
result = wrapped.invoke({"input": "deploy to production"})
receipt = wrapped.receipt()
```

Hooks into LangChain's native `BaseCallbackHandler`. Your agent code stays unchanged. pruv runs underneath it.

## How it works

`PruvCallbackHandler` intercepts LangChain lifecycle events:

- `on_tool_start` / `on_tool_end` — tool executions
- `on_llm_start` — LLM invocations
- `on_agent_action` — agent decisions
- `on_chain_start` / `on_chain_end` — chain executions
- `on_retriever_start` — retriever queries

Every event is posted to the pruv identity chain via `POST /api/identity/act`. The chain is tamper-evident — modify one entry and verification detects exactly where.

## Links

- [pruv.dev](https://pruv.dev)
- [Documentation](https://docs.pruv.dev)
- [GitHub](https://github.com/mintingpressbuilds/pruv)

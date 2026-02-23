# pruv

[![pruv](https://img.shields.io/badge/pruv-v1.0.1-green)](https://pypi.org/project/pruv/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Prove what happened. Cryptographic verification for any system.

```bash
pip install pruv
```

## Quick Start

Wrap any AI agent in 3 lines. Every action gets hashed, chained, and verified.

```python
import pruv

agent = pruv.Agent("my-agent", api_key="pv_live_xxx")
agent.action("read_email", {"from": "boss@co.com"})
agent.action("send_reply", {"to": "boss@co.com", "body": "done"})

chain = agent.chain()       # full verified history
result = agent.verify()     # cryptographic verification
```

## @verified Decorator

Automatically record every function call as a verified action.

```python
import pruv

pruv.init("my-agent", api_key="pv_live_xxx")

@pruv.verified
def send_email(to, subject, body):
    smtp.send(to, subject, body)

@pruv.verified(action_type="email.send", sensitive_keys=["body"])
def send_private(to, subject, body):
    smtp.send(to, subject, body)
```

Each call records `action.start` and `action.complete` (or `action.error` on failure).

## LangChain

```bash
pip install pruv-langchain
```

```python
from pruv_langchain import LangChainWrapper

wrapped = LangChainWrapper(agent, agent_id="agent-id", api_key="pv_live_xxx")
result = wrapped.invoke({"input": "deploy to production"})
receipt = wrapped.receipt()
```

Hooks into LangChain's native callback system. Records every tool call, LLM invocation, chain execution, and agent action.

## CrewAI

```bash
pip install pruv-crewai
```

```python
from pruv_crewai import CrewAIWrapper

wrapped = CrewAIWrapper(crew, agent_id="agent-id", api_key="pv_live_xxx")
result = wrapped.kickoff()
receipt = wrapped.receipt()
```

Intercepts CrewAI lifecycle events — crew kickoff, task execution, agent handoffs, tool usage.

## OpenAI Agents

```bash
pip install pruv-openai
```

```python
from pruv_openai import OpenAIAgentWrapper

wrapped = OpenAIAgentWrapper(agent, agent_id="agent-id", api_key="pv_live_xxx")
result = await wrapped.run("analyze the quarterly report")
receipt = wrapped.receipt()
```

Implements the OpenAI Agents SDK TracingProcessor protocol. Records tool calls, guardrail checks, agent handoffs, and LLM calls.

## OpenClaw

```bash
pip install pruv-openclaw
```

```python
from pruv_openclaw import PruvOpenClawPlugin

plugin = PruvOpenClawPlugin(agent_id="agent-id", api_key="pv_live_xxx")
# Config-driven — hooks into before_action / after_action automatically
receipt = plugin.receipt()
```

Config-driven plugin with automatic scope mapping. File reads, writes, executions — all scope-checked and chained.

## Sensitive Data

Sensitive fields are automatically hashed (SHA-256) instead of stored raw:

```python
agent.action("send_email", {"to": "user@co.com", "body": "secret"}, sensitive_keys=["body"])
# body stored as: {"_redacted": true, "_hash": "a3f8..."}
```

## Products

- **pruv.scan** — Hash every file in a directory or repository. Produces a deterministic project state fingerprint. Prove exactly what your codebase looked like at any moment.
- **pruv.identity** — A passport for AI agents. Register with declared owner, permissions, and validity period. Every action checked against scope. Receipt shows what it did and whether it stayed in bounds.
- **pruv.provenance** — Chain of custody for any digital artifact. Origin captured. Every modification recorded — who touched it, why, what it looked like before and after. Tamper-evident. Independently verifiable.
- **pruv.checkpoint** — Time travel for any system state. Every chain entry captures what your system was at that exact moment. Open any entry, see state before and after, restore to any prior verified state. Recovery is no longer expensive or uncertain.
- **pruv.receipts** — Every operation produces a receipt. Not a log. Not an assertion. Proof anyone can verify independently — no account required, no trust required in pruv. Export as PDF. Share via link. Embed as badge.

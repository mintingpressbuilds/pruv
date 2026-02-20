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
pip install pruv[langchain]
```

```python
from pruv.integrations.langchain import PruvCallbackHandler

handler = PruvCallbackHandler(
    agent_name="my-langchain-agent",
    api_key="pv_live_xxx",
)

agent = initialize_agent(tools, llm, callbacks=[handler])
agent.run("do something")

chain = handler.pruv_agent.chain()
```

Records all LLM calls, tool usage, chain execution, and agent actions.

## CrewAI

```bash
pip install pruv[crewai]
```

```python
from pruv.integrations.crewai import pruv_wrap_crew

crew = Crew(agents=[...], tasks=[...])
verified_crew = pruv_wrap_crew(crew, agent_name="my-crew", api_key="pv_live_xxx")
result = verified_crew.kickoff()

chain = verified_crew._pruv_agent.chain()
```

Records crew kickoff, individual agent task execution, and results.

## OpenClaw

```python
from pruv.integrations.openclaw import OpenClawVerifier

verifier = OpenClawVerifier(api_key="pv_live_xxx", agent_name="my-openclaw")

verifier.before_skill("search", {"query": "latest news"})
verifier.after_skill("search", results, success=True)
verifier.file_accessed("/app/data.json", "read")
verifier.api_called("https://api.example.com/v1", "GET", 200)

chain = verifier.get_chain()
```

Records skill execution, messages, file access, and API calls.

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

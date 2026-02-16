# pruv — Agent Verification Layer Build

pruv already exists as a working verification API at api.pruv.dev. xycore already exists as a working cryptographic primitive. Do not rebuild either. This build adds the developer experience layer on top — the SDK, integrations, dashboard improvements, and alerting.

Read all existing code in packages/xycore and packages/pruv before starting. Understand how chains, entries, and receipts work. Then build.

-----

## 1. PYTHON SDK — Agent Wrapper

Location: `packages/pruv/pruv/agent.py`

This is the core product. A Python class that wraps any AI agent and automatically chains every action through pruv.

### Agent class:

```python
# pruv/agent.py

import time
import hashlib
import json
from typing import Any, Optional, Callable
from functools import wraps
from pruv.client import PruvClient


class Agent:
    """
    Wraps any AI agent with automatic action verification.
    Every action is hashed, chained, and stored as a pruv receipt.

    Usage:
        agent = Agent("email-assistant", api_key="pv_live_xxx")
        agent.action("read_email", {"from": "boss@co.com"})
        agent.action("send_reply", {"to": "boss@co.com", "body": "done"})
        chain = agent.chain()  # full verified history
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        endpoint: str = "https://api.pruv.dev",
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.client = PruvClient(api_key=api_key, endpoint=endpoint)
        self.metadata = metadata or {}
        self._chain = None
        self._action_count = 0
        self._init_chain()

    def _init_chain(self):
        """Create a new pruv chain for this agent session."""
        self._chain = self.client.create_chain(
            name=f"{self.name}-{int(time.time())}",
            metadata={
                "agent": self.name,
                "started_at": time.time(),
                **self.metadata,
            }
        )

    def action(
        self,
        action_type: str,
        data: dict,
        sensitive_keys: Optional[list] = None,
    ) -> dict:
        """
        Record a verified action.

        Args:
            action_type: What the agent did ("read_email", "send_message", etc.)
            data: Action payload (parameters, results, context)
            sensitive_keys: Keys in data to hash instead of storing raw
                           (e.g. ["body", "password"] — values are SHA-256 hashed
                            so you can verify without exposing content)

        Returns:
            Receipt dict with hash, chain position, timestamp
        """
        self._action_count += 1

        # Redact sensitive fields — hash them instead of storing raw
        safe_data = self._redact(data, sensitive_keys or [])

        entry_data = {
            "action": action_type,
            "seq": self._action_count,
            "ts": time.time(),
            "data": safe_data,
        }

        receipt = self.client.add_entry(
            chain_id=self._chain["id"],
            data=entry_data,
        )

        return receipt

    def verify(self) -> dict:
        """
        Verify the entire action chain.
        Returns verification result with status and any broken links.
        """
        return self.client.verify_chain(self._chain["id"])

    def chain(self) -> dict:
        """Get the full chain with all entries."""
        return self.client.get_chain(self._chain["id"])

    def receipt(self, entry_id: str) -> dict:
        """Get a single action receipt by ID."""
        return self.client.get_entry(self._chain["id"], entry_id)

    def export(self) -> str:
        """
        Export the chain as a self-verifying artifact.
        Returns HTML file content (same as pruv's genesis artifact system).
        """
        return self.client.export_chain(self._chain["id"])

    def _redact(self, data: dict, sensitive_keys: list) -> dict:
        """Replace sensitive values with their SHA-256 hash."""
        if not sensitive_keys:
            return data

        redacted = {}
        for k, v in data.items():
            if k in sensitive_keys:
                raw = json.dumps(v, sort_keys=True) if not isinstance(v, str) else v
                redacted[k] = {
                    "_redacted": True,
                    "_hash": hashlib.sha256(raw.encode()).hexdigest(),
                }
            else:
                redacted[k] = v
        return redacted


class ActionError(Exception):
    """Raised when an action fails verification."""
    pass
```

### Decorator:

```python
# pruv/decorators.py

from functools import wraps
from typing import Optional
from pruv.agent import Agent


# Module-level default agent
_default_agent: Optional[Agent] = None


def init(name: str, api_key: str, **kwargs):
    """Initialize the default pruv agent."""
    global _default_agent
    _default_agent = Agent(name=name, api_key=api_key, **kwargs)
    return _default_agent


def verified(
    action_type: Optional[str] = None,
    sensitive_keys: Optional[list] = None,
    agent: Optional[Agent] = None,
):
    """
    Decorator that automatically records function calls as verified actions.

    Usage:
        import pruv
        pruv.init("my-agent", api_key="pv_live_xxx")

        @pruv.verified
        def send_email(to, subject, body):
            smtp.send(to, subject, body)

        # Or with options:
        @pruv.verified(action_type="email.send", sensitive_keys=["body"])
        def send_email(to, subject, body):
            smtp.send(to, subject, body)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            target = agent or _default_agent
            if target is None:
                raise RuntimeError(
                    "No pruv agent initialized. Call pruv.init() first."
                )

            act = action_type or f"{func.__module__}.{func.__name__}"

            # Record the action BEFORE execution (intent)
            data = {
                "function": func.__name__,
                "args": _safe_serialize(args),
                "kwargs": _safe_serialize(kwargs),
                "status": "started",
            }
            target.action(f"{act}.start", data, sensitive_keys)

            # Execute
            try:
                result = func(*args, **kwargs)

                # Record success
                target.action(f"{act}.complete", {
                    "function": func.__name__,
                    "status": "success",
                    "result_hash": _hash_result(result),
                }, sensitive_keys)

                return result

            except Exception as e:
                # Record failure
                target.action(f"{act}.error", {
                    "function": func.__name__,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                })
                raise

        return wrapper

    # Handle @pruv.verified without parentheses
    if callable(action_type):
        func = action_type
        action_type = None
        return decorator(func)

    return decorator


def _safe_serialize(obj):
    """Serialize args/kwargs safely, replacing non-serializable objects."""
    try:
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _hash_result(result):
    """Hash the result for verification without storing raw content."""
    import hashlib
    import json
    try:
        raw = json.dumps(result, sort_keys=True, default=str)
    except (TypeError, ValueError):
        raw = str(result)
    return hashlib.sha256(raw.encode()).hexdigest()
```

### Package init:

```python
# pruv/__init__.py
# Add these to the existing __init__.py

from pruv.agent import Agent
from pruv.decorators import init, verified

__all__ = [
    # ... existing exports ...
    "Agent",
    "init",
    "verified",
]
```

### PruvClient updates:

If `pruv/client.py` doesn't exist or doesn't have these methods, add them. The client is a thin HTTP wrapper around the pruv API:

```python
# pruv/client.py

import httpx
import json
from typing import Optional


class PruvClient:
    """HTTP client for the pruv API."""

    def __init__(self, api_key: str, endpoint: str = "https://api.pruv.dev"):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self._http = httpx.Client(
            base_url=self.endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def create_chain(self, name: str, metadata: Optional[dict] = None) -> dict:
        resp = self._http.post("/v1/chains", json={
            "name": name,
            "metadata": metadata or {},
        })
        resp.raise_for_status()
        return resp.json()

    def add_entry(self, chain_id: str, data: dict) -> dict:
        resp = self._http.post(f"/v1/chains/{chain_id}/entries", json={
            "data": data,
        })
        resp.raise_for_status()
        return resp.json()

    def get_chain(self, chain_id: str) -> dict:
        resp = self._http.get(f"/v1/chains/{chain_id}")
        resp.raise_for_status()
        return resp.json()

    def get_entry(self, chain_id: str, entry_id: str) -> dict:
        resp = self._http.get(f"/v1/chains/{chain_id}/entries/{entry_id}")
        resp.raise_for_status()
        return resp.json()

    def verify_chain(self, chain_id: str) -> dict:
        resp = self._http.get(f"/v1/chains/{chain_id}/verify")
        resp.raise_for_status()
        return resp.json()

    def export_chain(self, chain_id: str) -> str:
        resp = self._http.get(f"/v1/chains/{chain_id}/export")
        resp.raise_for_status()
        return resp.text

    def list_chains(self, limit: int = 50, offset: int = 0) -> dict:
        resp = self._http.get("/v1/chains", params={
            "limit": limit, "offset": offset,
        })
        resp.raise_for_status()
        return resp.json()
```

**Acceptance criteria for Section 1:**

- [ ] `from pruv import Agent` works
- [ ] `Agent("name", api_key="key")` creates a chain on init
- [ ] `agent.action("type", {"key": "val"})` adds entry and returns receipt
- [ ] `agent.verify()` returns verification result
- [ ] `agent.chain()` returns full chain with all entries
- [ ] Sensitive key redaction works — values replaced with SHA-256 hashes
- [ ] `@pruv.verified` decorator records start + complete/error for each call
- [ ] Decorator handles both `@pruv.verified` and `@pruv.verified(action_type="x")`
- [ ] Failed function calls record the error in the chain
- [ ] All methods handle API errors gracefully

-----

## 2. FRAMEWORK INTEGRATIONS

### LangChain Integration

Location: `packages/pruv/pruv/integrations/langchain.py`

```python
# pruv/integrations/langchain.py

"""
LangChain integration for pruv.

Usage:
    from pruv.integrations.langchain import PruvCallbackHandler

    handler = PruvCallbackHandler(
        agent_name="my-langchain-agent",
        api_key="pv_live_xxx",
    )

    # Add to any LangChain agent/chain
    agent = initialize_agent(tools, llm, callbacks=[handler])
    agent.run("do something")

    # Get the verification chain
    chain = handler.pruv_agent.chain()
"""

from typing import Any, Dict, List, Optional, Union
from pruv.agent import Agent

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    raise ImportError(
        "LangChain not installed. Run: pip install langchain-core"
    )


class PruvCallbackHandler(BaseCallbackHandler):
    """LangChain callback that records every action to a pruv chain."""

    def __init__(
        self,
        agent_name: str = "langchain-agent",
        api_key: str = "",
        endpoint: str = "https://api.pruv.dev",
        record_prompts: bool = False,
        sensitive_keys: Optional[List[str]] = None,
    ):
        self.pruv_agent = Agent(
            name=agent_name,
            api_key=api_key,
            endpoint=endpoint,
        )
        self.record_prompts = record_prompts
        self.sensitive_keys = sensitive_keys or []
        if not record_prompts:
            self.sensitive_keys.extend(["prompts", "prompt", "input"])

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs
    ):
        data = {
            "model": serialized.get("id", ["unknown"])[-1] if serialized.get("id") else "unknown",
            "prompt_count": len(prompts),
        }
        if self.record_prompts:
            data["prompts"] = prompts
        self.pruv_agent.action("llm.start", data, self.sensitive_keys)

    def on_llm_end(self, response, **kwargs):
        self.pruv_agent.action("llm.complete", {
            "generations": len(response.generations) if response.generations else 0,
        })

    def on_llm_error(self, error: BaseException, **kwargs):
        self.pruv_agent.action("llm.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs
    ):
        self.pruv_agent.action("tool.start", {
            "tool": serialized.get("name", "unknown"),
            "input_hash": self.pruv_agent._redact(
                {"input": input_str}, ["input"]
            )["input"] if not self.record_prompts else input_str,
        })

    def on_tool_end(self, output: str, **kwargs):
        self.pruv_agent.action("tool.complete", {
            "output_length": len(output) if output else 0,
        })

    def on_tool_error(self, error: BaseException, **kwargs):
        self.pruv_agent.action("tool.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs
    ):
        self.pruv_agent.action("chain.start", {
            "chain": serialized.get("id", ["unknown"])[-1] if serialized.get("id") else "unknown",
            "input_keys": list(inputs.keys()),
        })

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        self.pruv_agent.action("chain.complete", {
            "output_keys": list(outputs.keys()),
        })

    def on_chain_error(self, error: BaseException, **kwargs):
        self.pruv_agent.action("chain.error", {
            "error": str(error),
            "error_type": type(error).__name__,
        })

    def on_agent_action(self, action, **kwargs):
        self.pruv_agent.action("agent.action", {
            "tool": action.tool,
            "log": action.log[:200] if action.log else "",
        })

    def on_agent_finish(self, finish, **kwargs):
        self.pruv_agent.action("agent.finish", {
            "output_length": len(finish.return_values.get("output", "")) if finish.return_values else 0,
        })
```

### CrewAI Integration

Location: `packages/pruv/pruv/integrations/crewai.py`

```python
# pruv/integrations/crewai.py

"""
CrewAI integration for pruv.

Usage:
    from pruv.integrations.crewai import pruv_wrap_crew

    crew = Crew(agents=[...], tasks=[...])
    verified_crew = pruv_wrap_crew(
        crew,
        agent_name="my-crew",
        api_key="pv_live_xxx",
    )
    result = verified_crew.kickoff()

    # Get verification chain
    chain = verified_crew._pruv_agent.chain()
"""

from typing import Optional
from pruv.agent import Agent


def pruv_wrap_crew(
    crew,
    agent_name: str = "crewai-agent",
    api_key: str = "",
    endpoint: str = "https://api.pruv.dev",
):
    """Wrap a CrewAI Crew with pruv verification."""

    pruv_agent = Agent(
        name=agent_name,
        api_key=api_key,
        endpoint=endpoint,
        metadata={"framework": "crewai"},
    )

    # Store reference
    crew._pruv_agent = pruv_agent

    # Wrap kickoff
    original_kickoff = crew.kickoff

    def verified_kickoff(*args, **kwargs):
        pruv_agent.action("crew.kickoff", {
            "agent_count": len(crew.agents) if hasattr(crew, 'agents') else 0,
            "task_count": len(crew.tasks) if hasattr(crew, 'tasks') else 0,
        })

        try:
            result = original_kickoff(*args, **kwargs)
            pruv_agent.action("crew.complete", {
                "status": "success",
                "result_length": len(str(result)) if result else 0,
            })
            return result
        except Exception as e:
            pruv_agent.action("crew.error", {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            })
            raise

    crew.kickoff = verified_kickoff

    # Wrap each agent's execute_task if accessible
    if hasattr(crew, 'agents'):
        for ag in crew.agents:
            _wrap_crew_agent(ag, pruv_agent)

    return crew


def _wrap_crew_agent(crew_agent, pruv_agent: Agent):
    """Wrap a single CrewAI agent's task execution."""

    if hasattr(crew_agent, 'execute_task'):
        original_execute = crew_agent.execute_task

        def verified_execute(task, *args, **kwargs):
            agent_name = getattr(crew_agent, 'role', 'unknown')
            task_desc = getattr(task, 'description', '')[:200]

            pruv_agent.action("agent.task.start", {
                "agent": agent_name,
                "task": task_desc,
            })

            try:
                result = original_execute(task, *args, **kwargs)
                pruv_agent.action("agent.task.complete", {
                    "agent": agent_name,
                    "status": "success",
                })
                return result
            except Exception as e:
                pruv_agent.action("agent.task.error", {
                    "agent": agent_name,
                    "status": "error",
                    "error": str(e),
                })
                raise

        crew_agent.execute_task = verified_execute
```

### OpenClaw Integration

Location: `packages/pruv/pruv/integrations/openclaw.py`

```python
# pruv/integrations/openclaw.py

"""
OpenClaw integration for pruv.

This works as an OpenClaw skill that wraps all other skill executions
with pruv verification.

Usage:
    Install this as an OpenClaw skill, then every action by every
    other skill is recorded in a pruv verification chain.

    Configuration (openclaw config):
        pruv:
          api_key: pv_live_xxx
          endpoint: https://api.pruv.dev
          agent_name: my-openclaw
"""

import json
import time
from typing import Any, Dict, Optional
from pruv.agent import Agent


class OpenClawVerifier:
    """
    Middleware that intercepts OpenClaw skill executions
    and records them to a pruv chain.
    """

    def __init__(
        self,
        api_key: str,
        agent_name: str = "openclaw-agent",
        endpoint: str = "https://api.pruv.dev",
        redact_content: bool = True,
    ):
        self.agent = Agent(
            name=agent_name,
            api_key=api_key,
            endpoint=endpoint,
            metadata={
                "framework": "openclaw",
                "started": time.time(),
            },
        )
        self.redact_content = redact_content
        self._sensitive = ["body", "content", "message", "text", "password", "token"]

    def before_skill(self, skill_name: str, params: Dict[str, Any]):
        """Call before any skill execution."""
        sensitive = self._sensitive if self.redact_content else []
        self.agent.action("skill.start", {
            "skill": skill_name,
            "params": params,
        }, sensitive)

    def after_skill(self, skill_name: str, result: Any, success: bool = True):
        """Call after skill execution completes."""
        if success:
            self.agent.action("skill.complete", {
                "skill": skill_name,
                "result_type": type(result).__name__,
            })
        else:
            self.agent.action("skill.error", {
                "skill": skill_name,
                "error": str(result),
            })

    def message_received(self, channel: str, sender: str, content: str):
        """Record incoming message."""
        sensitive = ["content"] if self.redact_content else []
        self.agent.action("message.received", {
            "channel": channel,
            "sender": sender,
            "content": content,
        }, sensitive)

    def message_sent(self, channel: str, recipient: str, content: str):
        """Record outgoing message."""
        sensitive = ["content"] if self.redact_content else []
        self.agent.action("message.sent", {
            "channel": channel,
            "recipient": recipient,
            "content": content,
        }, sensitive)

    def file_accessed(self, path: str, operation: str):
        """Record file access."""
        self.agent.action("file.access", {
            "path": path,
            "operation": operation,
        })

    def api_called(self, url: str, method: str, status: int):
        """Record external API call."""
        self.agent.action("api.call", {
            "url": url,
            "method": method,
            "status": status,
        })

    def get_chain(self) -> dict:
        """Get the full verification chain."""
        return self.agent.chain()

    def verify(self) -> dict:
        """Verify the chain integrity."""
        return self.agent.verify()

    def export(self) -> str:
        """Export as self-verifying HTML artifact."""
        return self.agent.export()
```

### Integration init:

```python
# pruv/integrations/__init__.py

"""
Framework integrations for pruv.

Supported frameworks:
    - LangChain: from pruv.integrations.langchain import PruvCallbackHandler
    - CrewAI: from pruv.integrations.crewai import pruv_wrap_crew
    - OpenClaw: from pruv.integrations.openclaw import OpenClawVerifier
"""
```

**Acceptance criteria for Section 2:**

- [ ] LangChain callback handler records LLM calls, tool usage, chain execution, agent actions
- [ ] CrewAI wrapper records crew kickoff, individual agent tasks
- [ ] OpenClaw verifier records skill execution, messages, file access, API calls
- [ ] All integrations create proper pruv chains with sequential entries
- [ ] Sensitive data is redacted by default (prompts, message content)
- [ ] Each integration works with a single import + 2-3 lines of setup
- [ ] ImportError with helpful message if framework isn't installed

-----

## 3. DASHBOARD — CHAIN EXPLORER

Location: `apps/dashboard` — add new pages/components

### Chain explorer page: `/chains/[id]`

A visual timeline of every action in a chain.

Layout:

```
┌─────────────────────────────────────────────────────┐
│  email-assistant-1739644800                          │
│  Created: Feb 15, 2026 · 47 actions · ✓ Verified   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ● 12:00:01  llm.start                             │
│  │           model: claude-sonnet-4-5               │
│  │           hash: a3f8...2b1c                      │
│  │                                                  │
│  ● 12:00:03  llm.complete                          │
│  │           generations: 1                         │
│  │           hash: 7d2e...9a4f                      │
│  │                                                  │
│  ● 12:00:03  tool.start                            │
│  │           tool: send_email                       │
│  │           hash: b1c4...3e7d                      │
│  │                                                  │
│  ● 12:00:04  tool.complete                         │
│  │           hash: e5f2...1a8b                      │
│  │                                                  │
│  ⚠ 12:00:05  tool.error                            │
│  │           error: ConnectionTimeout               │
│  │           hash: 9c3d...4f2e                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Implementation:

```tsx
// app/chains/[id]/page.tsx

// Fetch chain data from API
// Render timeline with:
//   - Vertical line on left
//   - Dot at each action (color-coded: green=success, red=error, blue=info)
//   - Timestamp
//   - Action type (bold)
//   - Key data fields (muted)
//   - Hash (monospace, truncated, click to copy full)
//   - Expandable detail panel (click action to expand)

// Top bar:
//   - Chain name
//   - Created date
//   - Action count
//   - Verification status (green checkmark or red X)
//   - "Verify Now" button — re-runs verification
//   - "Export" button — downloads self-verifying HTML

// Filters:
//   - Filter by action type
//   - Filter by status (success/error)
//   - Search by content
//   - Time range
```

### Action detail panel:

When clicking an action in the timeline, expand to show:

```
┌─────────────────────────────────────┐
│  tool.start                         │
│  ──────────────────────────────     │
│  Time:      12:00:03.421            │
│  Sequence:  #15                     │
│  Hash:      b1c4e7d2...3e7d9a4f    │
│  Prev hash: 7d2e1a8b...9a4f3c2e    │
│                                     │
│  Data:                              │
│  {                                  │
│    "tool": "send_email",            │
│    "input": {                       │
│      "_redacted": true,             │
│      "_hash": "a3f8..."             │
│    }                                │
│  }                                  │
│                                     │
│  [Copy Hash] [Verify Entry]         │
└─────────────────────────────────────┘
```

### Chain list page update: `/chains`

Add columns:

- Agent name (from metadata)
- Framework (langchain/crewai/openclaw/custom)
- Action count
- Last action timestamp
- Status icon (verified/unverified/broken)

### Styling:

Follow the existing dashboard design language. Dark theme. Monospace for hashes. Color coding:

- Green dot: successful action
- Red dot: error
- Blue dot: informational (start events)
- Yellow dot: warning (anomaly detected)
- Gray dot: redacted content

**Acceptance criteria for Section 3:**

- [ ] Chain explorer page renders timeline of all actions
- [ ] Each action shows timestamp, type, key data, truncated hash
- [ ] Clicking an action expands to show full detail
- [ ] Verification status shown at top (runs on page load)
- [ ] "Verify Now" button re-checks chain integrity
- [ ] "Export" button downloads self-verifying HTML
- [ ] Chain list page shows agent name, framework, action count
- [ ] Error actions are visually distinct (red)
- [ ] Redacted fields show hash indicator, not raw data
- [ ] Responsive on mobile

-----

## 4. ALERTING — ANOMALY DETECTION

Location: `apps/api/app/services/alerts.py`

Simple rule-based anomaly detection on action chains. Not ML. Just rules that catch obvious problems.

### Rules:

```python
# app/services/alerts.py

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    rule: str
    severity: AlertSeverity
    message: str
    chain_id: str
    entry_id: Optional[str] = None
    data: Optional[dict] = None


def analyze_chain(chain: dict, entries: List[dict]) -> List[Alert]:
    """Run all rules against a chain and return alerts."""
    alerts = []

    # Rule 1: High error rate
    errors = [e for e in entries if ".error" in e.get("data", {}).get("action", "")]
    total = len(entries)
    if total > 5 and len(errors) / total > 0.3:
        alerts.append(Alert(
            rule="high_error_rate",
            severity=AlertSeverity.WARNING,
            message=f"Error rate is {len(errors)}/{total} ({len(errors)/total:.0%})",
            chain_id=chain["id"],
        ))

    # Rule 2: Unusual action volume
    if total > 100:
        # Calculate time span
        first_ts = entries[0].get("data", {}).get("ts", 0)
        last_ts = entries[-1].get("data", {}).get("ts", 0)
        duration = last_ts - first_ts
        if duration > 0:
            rate = total / (duration / 60)  # actions per minute
            if rate > 30:
                alerts.append(Alert(
                    rule="high_action_rate",
                    severity=AlertSeverity.WARNING,
                    message=f"Agent performing {rate:.0f} actions/minute",
                    chain_id=chain["id"],
                ))

    # Rule 3: New tool/skill usage
    tools_seen = set()
    for entry in entries:
        action = entry.get("data", {}).get("action", "")
        if "tool.start" in action or "skill.start" in action:
            tool_name = entry.get("data", {}).get("data", {}).get("tool", "") or \
                       entry.get("data", {}).get("data", {}).get("skill", "")
            if tool_name and tool_name not in tools_seen and len(tools_seen) > 3:
                alerts.append(Alert(
                    rule="new_tool",
                    severity=AlertSeverity.INFO,
                    message=f"Agent used new tool: {tool_name}",
                    chain_id=chain["id"],
                    entry_id=entry.get("id"),
                ))
            tools_seen.add(tool_name)

    # Rule 4: File access outside expected paths
    for entry in entries:
        action = entry.get("data", {}).get("action", "")
        if "file.access" in action:
            path = entry.get("data", {}).get("data", {}).get("path", "")
            if any(sensitive in path.lower() for sensitive in [
                ".env", "credentials", "secrets", ".ssh",
                "private", "password", "/etc/shadow"
            ]):
                alerts.append(Alert(
                    rule="sensitive_file_access",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Agent accessed sensitive file: {path}",
                    chain_id=chain["id"],
                    entry_id=entry.get("id"),
                ))

    # Rule 5: External API calls to unknown domains
    known_domains = set()
    for entry in entries:
        action = entry.get("data", {}).get("action", "")
        if "api.call" in action:
            url = entry.get("data", {}).get("data", {}).get("url", "")
            domain = _extract_domain(url)
            if domain and domain not in known_domains and len(known_domains) > 2:
                alerts.append(Alert(
                    rule="new_api_domain",
                    severity=AlertSeverity.INFO,
                    message=f"Agent contacted new domain: {domain}",
                    chain_id=chain["id"],
                    entry_id=entry.get("id"),
                ))
            known_domains.add(domain)

    # Rule 6: Chain verification failure
    # This is checked separately via the verify endpoint

    return alerts


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""
```

### API endpoint:

```python
# Add to apps/api/app/routes/chains.py

@router.get("/v1/chains/{chain_id}/alerts")
async def get_chain_alerts(chain_id: str, auth=Depends(require_auth)):
    chain = await get_chain(chain_id)
    entries = await get_chain_entries(chain_id)
    alerts = analyze_chain(chain, entries)
    return {
        "chain_id": chain_id,
        "alerts": [
            {
                "rule": a.rule,
                "severity": a.severity.value,
                "message": a.message,
                "entry_id": a.entry_id,
            }
            for a in alerts
        ],
        "analyzed_at": time.time(),
    }
```

### Webhook notifications:

```python
# app/services/webhooks.py

import httpx
from typing import List
from app.services.alerts import Alert, AlertSeverity


async def send_alert_webhooks(
    chain_id: str,
    alerts: List[Alert],
    webhook_url: str,
    min_severity: AlertSeverity = AlertSeverity.WARNING,
):
    """Send alerts to a user-configured webhook."""

    filtered = [a for a in alerts if _severity_rank(a.severity) >= _severity_rank(min_severity)]
    if not filtered:
        return

    payload = {
        "chain_id": chain_id,
        "alert_count": len(filtered),
        "alerts": [
            {
                "rule": a.rule,
                "severity": a.severity.value,
                "message": a.message,
            }
            for a in filtered
        ],
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=10.0)


def _severity_rank(s: AlertSeverity) -> int:
    return {"info": 0, "warning": 1, "critical": 2}[s.value]
```

### Dashboard integration:

On the chain explorer page, show alerts as colored badges inline with the timeline:

```
  ● 12:00:05  tool.error
  │           error: ConnectionTimeout
  │           ⚠ HIGH ERROR RATE — 30% of actions failing
```

And a summary at the top:

```
┌──────────────────────────────────┐
│  2 warnings · 1 critical alert  │
└──────────────────────────────────┘
```

**Acceptance criteria for Section 4:**

- [ ] GET /v1/chains/{id}/alerts returns analyzed alerts
- [ ] High error rate detection works (>30% errors)
- [ ] High action rate detection works (>30/min)
- [ ] Sensitive file access flagged as critical
- [ ] New tool/domain usage flagged as info
- [ ] Alerts shown on chain explorer page
- [ ] Webhook notification sends correctly
- [ ] Alert severity color coding: info=blue, warning=yellow, critical=red

-----

## Build Order

1. **Python SDK** (Agent class + decorator + client) — this is the product. Everything else is optional. TEST: write a simple script that creates an agent, performs 5 actions, verifies the chain. Does it work end-to-end against api.pruv.dev?
1. **LangChain integration** — the most popular framework. TEST: create a simple LangChain agent with the PruvCallbackHandler. Run it. Check the chain — are all LLM calls and tool usages recorded?
1. **CrewAI integration** — TEST: wrap a CrewAI crew. Kick it off. Check the chain.
1. **OpenClaw integration** — TEST: instantiate the verifier, call its methods manually. Check the chain.
1. **Chain explorer dashboard** — TEST: open a chain in the dashboard. Is the timeline clear? Can you click actions to expand? Does verification status show?
1. **Alerting** — TEST: create a chain with intentional anomalies (high error rate, sensitive file access). Does the alerts endpoint catch them?
1. **Update pyproject.toml** — add httpx as a dependency. Add optional deps for integrations: `langchain = ["langchain-core"]`, `crewai = ["crewai"]`. Update version.
1. **Update docs** — README with quickstart examples for each integration. Keep it simple: 10 lines to get started.

# pruv-openclaw

[![pruv-openclaw](https://img.shields.io/badge/pruv--openclaw-v0.1.0-green)](https://pypi.org/project/pruv-openclaw/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/pruv-openclaw/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Cryptographic verification for OpenClaw agents. Every file read, file write, system execution, and API call — automatically recorded into a pruv identity chain with scope checking.

```bash
pip install pruv-openclaw
```

## Usage

```python
from pruv_openclaw import PruvOpenClawPlugin

plugin = PruvOpenClawPlugin(agent_id="agent-id", api_key="pv_live_...")
# Config-driven — hooks into before_action / after_action automatically
receipt = plugin.receipt()
```

Config-driven plugin with automatic scope mapping. Your OpenClaw config stays unchanged. pruv runs underneath it.

## How it works

`PruvOpenClawPlugin` hooks into OpenClaw's action lifecycle with automatic scope mapping:

- `read_file` → `file.read` scope
- `write_file` → `file.write` scope
- `execute` → `system.execute` scope
- `api_call` → `api.call` scope
- `search` → `search.query` scope

Every action is posted to the pruv identity chain via `POST /api/identity/act`. The chain is tamper-evident — modify one entry and verification detects exactly where.

## Links

- [pruv.dev](https://pruv.dev)
- [Documentation](https://docs.pruv.dev)
- [GitHub](https://github.com/mintingpressbuilds/pruv)

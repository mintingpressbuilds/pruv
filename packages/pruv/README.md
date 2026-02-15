# pruv

[![PyPI](https://img.shields.io/pypi/v/pruv)](https://pypi.org/project/pruv/)
[![Python](https://img.shields.io/pypi/pyversions/pruv)](https://pypi.org/project/pruv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

Prove what happened. Cryptographic verification for any system.

```bash
pip install pruv
```

## Quick Start

```python
from pruv import xy_wrap

wrapped = xy_wrap(my_agent)
result = await wrapped.run("Fix the bug")
print(result.receipt.hash)
```

## Features

- **Scanner**: Scan any project for files, imports, env vars, frameworks, and services
- **xy_wrap()**: Universal wrapper for any agent, function, or workflow
- **Checkpoints**: Create snapshots, preview restore diffs, quick undo
- **Approval Gates**: Webhook-based human approval for high-risk operations
- **Cloud Sync**: Sync chains to api.pruv.dev
- **CLI**: `pruv scan`, `pruv verify`, `pruv export`, `pruv undo`, `pruv upload`

# xycore

[![xycore](https://img.shields.io/badge/xycore-v1.0.1-green)](https://pypi.org/project/xycore/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/xycore/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mintingpressbuilds/pruv/blob/main/LICENSE)

The XY primitive. Cryptographic verification for any system.

```bash
pip install xycore
```

## Usage

```python
from xycore import XYChain

chain = XYChain(name="my-chain")
chain.append("deploy", x_state={"version": "1.0"}, y_state={"version": "1.1"})
chain.append("configure", x_state={"version": "1.1"}, y_state={"version": "1.1", "configured": True})

valid, break_index = chain.verify()
assert valid
```

## Zero Dependencies

xycore uses only the Python standard library. Ed25519 signatures require the optional `cryptography` package:

```bash
pip install xycore[signatures]
```

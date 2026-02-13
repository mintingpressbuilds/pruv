# xycore

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

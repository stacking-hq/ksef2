---
title: Installation
description: Install the KSeF2 SDK and optional extras.
---

KSeF2 requires Python 3.12 or newer.

```bash
pip install ksef2
```

With `uv`:

```bash
uv add ksef2
```

## Optional extras

Install PDF support only when you need local invoice visualization:

```bash
pip install "ksef2[pdf]"
uv add "ksef2[pdf]"
```

Runtime type checks are optional and disabled by default. Enable them during
development or debugging with the `runtime-checks` extra:

```bash
pip install "ksef2[runtime-checks]"
KSEF2_RUNTIME_CHECKS=1 python -c "import ksef2"
```

## Verify the install

```python
import ksef2

print(ksef2.__version__)
print(ksef2.Client)
print(ksef2.AsyncClient)
```

## Next steps

- [Quickstart](quickstart.md)
- [Authentication](authentication.md)
- [Invoices guide](../guides/invoices.md)

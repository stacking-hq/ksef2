---
title: Instalacja
description: Instalacja KSeF2 SDK i opcjonalnych dodatków.
---

KSeF2 wymaga Pythona 3.12 lub nowszego.

```bash
pip install ksef2
```

Z `uv`:

```bash
uv add ksef2
```

## Opcjonalne dodatki

Obsługę PDF instaluj tylko wtedy, gdy potrzebujesz lokalnej wizualizacji faktur:

```bash
pip install "ksef2[pdf]"
uv add "ksef2[pdf]"
```

Sprawdzanie typów w runtime jest opcjonalne i domyślnie wyłączone:

```bash
pip install "ksef2[runtime-checks]"
KSEF2_RUNTIME_CHECKS=1 python -c "import ksef2"
```

## Sprawdzenie instalacji

```python
import ksef2

print(ksef2.__version__)
print(ksef2.Client)
print(ksef2.AsyncClient)
```

## Dalej

- [Quickstart](quickstart.md)
- [Uwierzytelnianie](authentication.md)
- [Faktury](../guides/invoices.md)

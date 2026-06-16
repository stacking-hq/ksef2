---
title: PEPPOL
description: Zapytania do publicznego rejestru dostawców PEPPOL.
---

Zapytania PEPPOL nie wymagają uwierzytelnienia.

```python
providers = client.peppol.query()
for provider in providers.providers:
    print(provider.name)
```

Iteracja po wszystkich stronach:

```python
for provider in client.peppol.all():
    print(provider.name)
```

W kliencie async użyj `await client.peppol.query()` oraz `async for`.

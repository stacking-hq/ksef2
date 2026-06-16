---
title: Dane TEST
description: Tworzenie i sprzątanie podmiotów oraz osób w środowisku TEST.
---

`client.testdata` działa tylko w `Environment.TEST`. Używaj go do przygotowania
tymczasowych podmiotów, osób i uprawnień w testach oraz przykładach.

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)

with client.testdata.temporal() as testdata:
    subject = testdata.create_subject(
        nip="1234567890",
        subject_type="vat_group",
        description="temporary subject",
    )
    print(subject)
```

`temporal()` sprząta zasoby po wyjściu z bloku.

## Async

```python
async with AsyncClient(Environment.TEST) as client:
    async with client.testdata.temporal() as testdata:
        await testdata.create_subject(...)
```

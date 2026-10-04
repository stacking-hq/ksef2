---
title: Konfiguracja klienta
description: Utwórz klienta sync albo async, skonfiguruj transport i wybierz moduły po uwierzytelnieniu.
---

Klient bazowy `Client` przechowuje konfigurację transportu HTTP i udostępnia
publiczne moduły bez uwierzytelnienia. Uwierzytelnij się raz dla kontekstu KSeF,
a potem przekaż klienta uwierzytelnionego do kodu przepływu.

## Wybierz sync albo async

`Client` to synchroniczny klient główny, a `AsyncClient` to jego asynchroniczny
odpowiednik. Oba mają to samo API; z `AsyncClient` używasz `async with` i `await`
przy wywołaniach.

### Sync

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip="5261040828")
```

### Async

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
```

Poza lokalnymi przepływami TEST używaj `Environment.DEMO` albo
`Environment.PRODUCTION`.

## Zarządzanie zasobami

Klient bazowy przechowuje zasoby HTTP zarządzane przez SDK. W skryptach i
zadaniach preferuj menedżer kontekstu:

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip="5261040828")
```

Jeżeli framework oczekuje zależności opartej o `yield`, umieść `yield` w
funkcji zależności i zamknij klienta w `finally`:

```python
from collections.abc import Iterator

from ksef2 import Client, Environment

def get_client() -> Iterator[Client]:
    client = Client(Environment.TEST)
    try:
        yield client
    finally:
        client.close()
```

Aplikacje async używają tej samej granicy przez `async with`:

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
```

Sesje online i batch też są granicami cyklu życia. Używaj context managera
sesji, żeby SDK zamknęło zdalną sesję po wyjściu z bloku:

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice(invoice_xml).wait()
```

Gdy dane uwierzytelniające są zapisane w profilu kompatybilnym z CLI, utwórz
klienta bazowego dla środowiska profilu i uwierzytelnij się przez
`with_profile()`:

```python
from ksef2 import Client, Environment

client = Client(Environment.PRODUCTION)
auth = client.authentication.with_profile("prod-token")
```

## Publiczne moduły klienta bazowego

Klient bazowy przydaje się przed uwierzytelnieniem:

```python
certificates = client.encryption.get_certificates()
providers = client.peppol.list().first_page()
```

Moduł tylko dla TEST także jest na kliencie bazowym:

```python
client.testdata.create_subject(
    nip="5261040828",
    subject_type="vat_group",
    description="Sandbox company",
)
```

## Gałęzie uwierzytelnione

Po uwierzytelnieniu użyj modułu pasującego do zadania:

```python
invoices = auth.invoices
batch = auth.batch
tokens = auth.tokens
permissions = auth.permissions
certificates = auth.certificates
limits = auth.limits
sessions = auth.sessions
invoice_sessions = auth.invoice_sessions
```

:::note[Oddziel klienta bazowego od uwierzytelnionego]
Klient bazowy wybiera środowisko i transport. Klient uwierzytelniony trzyma
tokeny bearer i moduły zależne od kontekstu. Przekazywanie
uwierzytelnionego klienta do kodu przepływów trzyma stan auth poza kodem
konfiguracji.
:::

## Zalecany przepływ

1. Odczytaj środowisko i ustawienia transportu na granicy aplikacji.

2. Utwórz jednego klienta bazowego dla wybranego środowiska KSeF.

3. Używaj modułów bazowych tylko do publicznych odczytów albo przygotowania
   danych TEST.

4. Uwierzytelnij się raz dla kontekstu, który wykonuje operację.

5. Przekaż uwierzytelnionego klienta do przepływów faktur, tokenów, uprawnień,
   certyfikatów, limitów i sesji.

## Referencja

- [Uwierzytelnianie](authenticate.md): Uwierzytelnij się tokenem, XAdES, certyfikatem TEST albo profilem.
- [Operacje](../reference/operations.md): Mapuj typowe workflow na wysokopoziomowe wejścia SDK.
- [Magazyn certyfikatów](configure-certificate-store.md): Skonfiguruj odświeżanie cache certyfikatów albo przekaż własny magazyn.
- [Certyfikaty szyfrowania](inspect-encryption-certificates.md): Sprawdź publiczne certyfikaty szyfrowania KSeF przed zaszyfrowanymi workflow.
- [Dostawcy PEPPOL](query-peppol-providers.md): Odczytuj publiczne dane dostawców PEPPOL z klienta bazowego.
- [Dane TEST](use-test-data.md): Twórz i zarządzaj podmiotami oraz uprawnieniami TEST.
- [Cykl życia klienta](../reference/client-lifecycle.md): Tworzenie, zamykanie i własność zasobów klientów bazowych i uwierzytelnionych.

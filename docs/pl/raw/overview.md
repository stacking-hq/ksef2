---
title: Low-level API
description: Używaj schema-native wywołań endpointów, gdy integracja KSeF wymaga niższego poziomu kontroli.
---

Low-level API to zaawansowana warstwa SDK dla kodu, który potrzebuje kontroli
na poziomie endpointów bez wychodzenia poza transport SDK. W kodzie jest
dostępna przez gałąź `raw`. Użyj jej przy własnym podpisywaniu, custody kluczy,
dokładnych payloadach OpenAPI albo debugowaniu tego, co trafia do KSeF.

Większość kodu aplikacyjnego powinna nadal zaczynać od klientów workflow.
Low-level API jest jawnie niższym poziomem: żądania i odpowiedzi używają nazw
pól KSeF/OpenAPI, takich jak `referenceNumber`, `publicKeyId` i
`authenticationToken`.

## Trzy poziomy

```python
# Workflow: SDK wykonuje całe zadanie.
status = session.send_invoice_and_wait(invoice_xml=invoice_xml)

# Step level: SDK zna szczegóły protokołu, caller decyduje o kolejności.
result = session.send_invoice(invoice_xml=invoice_xml)
status = session.wait_for_invoice_ready(
    invoice_reference_number=result.reference_number,
)

# Low-level API: caller decyduje o endpointach i schema-native payloadach.
sent = auth.raw.invoices.send(reference_number, send_request)
```

Low-level API nadal jest wyżej niż `httpx`: zachowuje retry SDK, lifecycle
checks, bearer-token middleware, parsowanie odpowiedzi i mapowanie wyjątków
KSeF.

## Import modeli

Importuj modele schema-native z `ksef2.raw`, nie z wewnętrznego pakietu `infra`.

```python
from ksef2.raw import spec

request = spec.GenerateTokenRequest(...)
response = auth.raw.tokens.generate_token(request)
```

Część metod low-level używa supplemental schema models SDK, gdy wygenerowany
model OpenAPI nie jest przyjazny dla Pythona. Te modele są re-eksportowane z
`ksef2.raw.spec` dla typowej ścieżki, a `ksef2.raw.supp` jest dostępne, gdy
potrzebujesz bezpośredniego pakietu supplemental.

## Mieszanie low-level i workflow

Możesz przechodzić między poziomami. Typowy wzorzec to ręczne low-level
uwierzytelnianie, a potem normalne workflow:

```python
from ksef2.raw.mappers import auth as auth_mapper

raw_tokens = client.raw.auth.redeem_token(auth_token)
auth = client.authenticated(auth_mapper.from_spec(raw_tokens))

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(invoice_xml=invoice_xml)
```

Główna zasada dotyczy właściciela sesji. Jeśli low-level API otwiera sesję, ten
sam poziom zwykle powinien też ją zamknąć i odpytywać. Jeśli sesję otwiera
wysoki poziom, używaj klienta sesji zwróconego przez SDK.

## Sekcja Low-level API

- [Ręczne uwierzytelnianie](authentication.md)
- [Sesje i faktury](sessions-invoices.md)
- [Mapa endpointów](endpoint-map.md)

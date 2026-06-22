---
title: Mapa endpointów low-level
description: Znajdź grupę endpointów low-level ksef2 dla wybranego obszaru KSeF.
---

Grupy low-level są cienkimi fasadami nad wrapperami endpointów SDK. Są dostępne
przez `client.raw` i `auth.raw`, używają schema-native modeli żądań i odpowiedzi
oraz tego samego transportu co klienci workflow.

## Przed uwierzytelnieniem

| Gałąź low-level | Zastosowanie |
| --- | --- |
| `client.raw.auth` | Challenge, token auth, XAdES auth, status auth i redeem tokena. |
| `client.raw.encryption` | Publiczne certyfikaty szyfrowania KSeF. |
| `client.raw.peppol` | Publiczny lookup dostawców PEPPOL. |
| `client.raw.testdata` | Endpointy TEST dla podmiotów, osób, uprawnień, załączników i kontekstu. |

## Po uwierzytelnieniu

| Gałąź low-level | Zastosowanie |
| --- | --- |
| `auth.raw.auth` | Listowanie i zamykanie sesji auth. |
| `auth.raw.certificates` | Limity, rejestracja, pobieranie, wyszukiwanie i cofanie certyfikatów. |
| `auth.raw.encryption` | Publiczne certyfikaty szyfrowania KSeF. |
| `auth.raw.invoices` | Metadane, eksport, pobieranie, wysyłka online, status faktur sesji i UPO. |
| `auth.raw.limits` | Limity kontekstu, podmiotu i API. |
| `auth.raw.peppol` | Publiczny lookup dostawców PEPPOL. |
| `auth.raw.permissions.grant` | Endpointy nadawania uprawnień. |
| `auth.raw.permissions.revoke` | Endpointy cofania uprawnień. |
| `auth.raw.permissions.query` | Wyszukiwanie uprawnień i status załączników. |
| `auth.raw.permissions.status` | Status operacji uprawnień i role podmiotu. |
| `auth.raw.session` | Otwieranie/zamykanie sesji online i batch, UPO sesji, listowanie sesji. |
| `auth.raw.testdata` | Endpointy fixture'ów TEST. |
| `auth.raw.tokens` | Generowanie, listowanie, status i cofanie tokenów. |

## Importy

```python
from ksef2.raw import (
    encrypt_invoice,
    encrypt_symmetric_key,
    encrypt_token,
    generate_session_key,
    prepare_batch_package,
    sha256_b64,
    spec,
    supp,
)
from ksef2.raw.mappers import auth as auth_mapper
```

Eksportowane utility low-level pozostają ograniczone do mechaniki KSeF:
szyfrowania i hashy. Body żądań pozostają jawne przez modele `spec.*`.
Publiczne mappery, takie jak `auth_mapper.from_spec(...)`, są jawnym mostem z
modeli odpowiedzi low-level do modeli domenowych SDK.

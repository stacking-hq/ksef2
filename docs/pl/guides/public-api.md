---
title: Kontrakt publicznego API
description: Stabilne ścieżki importu i granice internal dla ksef2 1.0.
---

W kodzie aplikacyjnym używaj ścieżek importu z tej strony. To one mają pozostać
stabilne w linii 1.x.

## Stabilne importy aplikacyjne

| Ścieżka importu | Do czego służy |
| --- | --- |
| `ksef2` | Klienci root, konfiguracja środowiska i transportu, `FormSchema`, `__version__` oraz publiczne wyjątki. |
| `ksef2.clients` | Konkretne klasy klientów sync i async, gdy potrzebujesz ich w adnotacjach typów. |
| `ksef2.domain.models` | Modele żądań, odpowiedzi, filtrów, paginacji, tokenów, uprawnień, sesji i batchy. |
| `ksef2.xades` | Ładowanie certyfikatów, generowanie certyfikatów TEST, lokalne podpisy XAdES i `LocalSigner`. |
| `ksef2.profiles` | Helpery konfiguracji profili zgodnych z `ksef2-cli`. |
| `ksef2.raw` | Low-level klienty endpointów, schema-native modele `spec` i `supp` oraz helpery kryptograficzne. |
| `ksef2.raw.mappers` | Publiczne mappery między modelami raw i modelami SDK. |
| `ksef2.services` | Wysokopoziomowe klasy serwisów, gdy tworzysz je ręcznie zamiast używać gałęzi klienta. |
| `ksef2.services.renderers` | Opcjonalne helpery renderowania faktur XSLT/PDF. |

Preferuj najwyższy poziom importu pasujący do workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem
```

## Eksporty pakietu root

Pakiet root `ksef2` jest publiczną fasadą dla typowego kodu aplikacyjnego:

- `Client`, `AsyncClient`;
- `Environment`, `TransportConfig`, `TimeoutConfig`, `RetryConfig`,
  `TlsConfig`, `ConnectionPoolConfig`;
- `FormSchema`;
- `ExceptionCode` i wszystkie publiczne klasy wyjątków `KSeF*`;
- `__version__`.

Dla tych nazw używaj importów z root zamiast sięgać do modułów implementacyjnych.

## Stabilność low-level API

`ksef2.raw` jest publiczne, ale celowo niższopoziomowe. Ścieżka importu jest
stabilna, natomiast kształt schema-native modeli podąża za sprawdzoną wersją
OpenAPI KSeF.

```python
from ksef2.raw import spec
from ksef2.raw.mappers import auth as auth_mapper
```

Nie importuj wygenerowanych modeli OpenAPI z `ksef2.infra.schema.api`. Używaj
`ksef2.raw.spec` i `ksef2.raw.supp`, żeby kod aplikacyjny pozostał na wspieranej
powierzchni.

## Ścieżki internal

Unikaj tych ścieżek w kodzie aplikacyjnym:

- `ksef2.infra.*`: wygenerowane schemy i wewnętrzne mappery;
- `ksef2.endpoints.*`: implementacja endpointów i transportu;
- `ksef2.core.*`: wewnętrzne moduły protokołu, transportu, middleware i helperów;
- `scripts/*`: narzędzia repozytorium, nie API pakietu.

Część ścieżek internal może być importowalna dla implementacji SDK albo testów,
ale nie jest kontraktem kompatybilności dla kodu aplikacyjnego.

## Reguła kompatybilności

Po 1.0 usunięcie albo zmiana nazwy stabilnej ścieżki importu wymaga major
version bump. Dodatkowe API może wejść w minor release. Patch release powinien
zachować udokumentowane importy i zachowanie poza poprawkami błędów.

## Referencja

- [Klient](client.md)
- [Low-level API](../raw/overview.md)
- [Generowanie kodu sync](../contributing/sync-generation.md)

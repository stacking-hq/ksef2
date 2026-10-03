---
title: Skonfiguruj magazyn certyfikatów
description: Skonfiguruj cache certyfikatów SDK używany przez uwierzytelnianie tokenem, sesje i eksporty faktur.
---

SDK przechowuje publiczne certyfikaty szyfrowania KSeF na kliencie głównym.
Uwierzytelnianie tokenem, sesje online i batch oraz eksporty faktur używają tego
magazynu, gdy muszą zaszyfrować materiał klucza dla KSeF.

Użyj domyślnego magazynu pamięciowego dla skryptów i workerów, które mogą
odświeżać certyfikaty z KSeF. Przekaż własny magazyn, gdy certyfikaty muszą być
współdzielone między procesami albo zapisane w magazynie aplikacji.

## Użyj domyślnego magazynu

`Client` i `AsyncClient` tworzą `CertificateStore` automatycznie. Domyślny
magazyn odświeża ważne certyfikaty po 24 godzinach i odświeża je natychmiast,
gdy brakuje wymaganego zastosowania certyfikatu.

Ustaw inny interwał odświeżania podczas tworzenia klienta głównego:

```python
from datetime import timedelta

from ksef2 import CertificateStore, Client, Environment

store = CertificateStore(refresh_after=timedelta(hours=6))

with Client(Environment.PRODUCTION, certificate_store=store) as client:
    auth = client.authentication.with_profile("prod-token")
```

`AsyncClient` przyjmuje ten sam argument `certificate_store`. Użyj
`async with AsyncClient(...)` i `await` przy wywołaniu uwierzytelniania; nic
więcej się nie zmienia.

Użyj `refresh_after=None` tylko dla krótkotrwałych klientów, w których
zachowanie "pobierz raz" jest zamierzone:

```python
from ksef2 import CertificateStore

store = CertificateStore(refresh_after=None)
```

:::note[Brak zastosowania nadal wymusza odświeżenie]
`refresh_after=None` nie blokuje odświeżenia, gdy w magazynie brakuje
zastosowania wymaganego przez przepływ. SDK ponownie sprawdza KSeF przed
zgłoszeniem `NoCertificateAvailableError`.
:::

## Przekaż własny magazyn

Własne magazyny implementują `CertificateStoreProtocol`. SDK odpowiada za
zdalne pobieranie, a magazyn odpowiada za trwałość, wybór ważnego certyfikatu i
decyzje o świeżości.

```python
from collections.abc import Iterable
from datetime import datetime

from ksef2 import CertificateStoreProtocol, Client, Environment
from ksef2.models import CertUsage, CertUsageEnum, PublicKeyCertificate

class DatabaseCertificateStore:
    def load(self, certs: Iterable[PublicKeyCertificate]) -> None:
        """Zastąp zapisane certyfikaty po pobraniu ich przez SDK."""
        ...

    def get_valid(
        self,
        usage: CertUsage | CertUsageEnum | str,
    ) -> PublicKeyCertificate:
        """Zwróć aktualnie ważny certyfikat dla wymaganego zastosowania."""
        ...

    def needs_refresh(
        self,
        usage: CertUsage | CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool:
        """Zwróć True, gdy SDK powinno pobrać certyfikaty z KSeF."""
        ...

store: CertificateStoreProtocol = DatabaseCertificateStore()
client = Client(Environment.PRODUCTION, certificate_store=store)
```

## Zalecany przepływ

1. Zacznij od domyślnego `CertificateStore`.

2. Ustaw `refresh_after`, gdy aplikacja ma bardziej rygorystyczną politykę
   rotacji certyfikatów albo startu.

3. Implementuj `CertificateStoreProtocol` tylko wtedy, gdy certyfikaty muszą
   przetrwać restart procesu albo być współdzielone przez wiele workerów.

4. Zdalne pobieranie z KSeF zostaw klientowi SDK, a trwałość danych magazynowi.

## Powiązane strony

- [Sprawdź certyfikaty szyfrowania](inspect-encryption-certificates.md): Odczytaj i sprawdź publiczne certyfikaty szyfrowania KSeF bezpośrednio.
- [Konfiguracja klienta](client-setup.md): Skonfiguruj klientów głównych, transport, cykl życia i gałęzie uwierzytelnione.
- [Szyfrowanie](../concepts/encryption.md): Zrozum, jak publiczne certyfikaty chronią materiał kluczy tokenów, sesji i eksportów.

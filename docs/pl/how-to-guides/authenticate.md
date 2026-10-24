---
title: Uwierzytelnij się
description: Skonfiguruj dane uwierzytelniające ksef2 przez zmienne środowiskowe, tokeny KSeF, certyfikaty XAdES albo profile kompatybilne z CLI.
---

Uwierzytelnianie zamienia głównego `Client` w klienta uwierzytelnionego. Klient
główny wybiera środowisko KSeF, a metoda uwierzytelnienia wybiera kontekst, w
którym działa aplikacja.

:::caution[Sekrety trzymaj w środowisku]
Nie zapisuj tokenów KSeF, haseł certyfikatów ani haseł kluczy prywatnych w
repozytorium. Ścieżki i nazwy profili mogą trafić do lokalnej konfiguracji,
ale wartości sekretów powinny pochodzić ze zmiennych środowiskowych.
:::

## Zmienne środowiskowe

Te nazwy są używane w przykładach i przez profile `ksef2-cli`:

| Zmienna | Znaczenie |
| --- | --- |
| `KSEF2_ENV` | `test`, `demo` albo `production` w przykładach SDK. |
| `KSEF2_NIP` | NIP podatnika/kontekstu używany przy uwierzytelnianiu. |
| `KSEF2_TOKEN` | Token KSeF dla uwierzytelniania tokenem. |
| `KSEF2_PROFILE` | Nazwa profilu wybierana przez `ksef2-cli` i uwierzytelnianie profilami w SDK. |
| `KSEF2_CONFIG` | Opcjonalna ścieżka do pliku konfiguracji profili CLI. |
| `KSEF2_KEY_PASSWORD` | Opcjonalne hasło zaszyfrowanego klucza PEM. |
| `KSEF2_P12_PASSWORD` | Opcjonalne hasło archiwum PKCS#12/PFX. |

```bash
export KSEF2_ENV=test
export KSEF2_NIP=5261040828
export KSEF2_TOKEN=podmien-na-prawdziwy-token-ksef
```

SDK czyta `KSEF2_PROFILE` i `KSEF2_CONFIG`, gdy używasz
`client.authentication.with_profile()`. Przy bezpośrednim uwierzytelnianiu
tokenem albo certyfikatem trzymaj granicę konfiguracji jawną w aplikacji:

```python
import os

from ksef2 import Environment

environment_name = os.environ.get("KSEF2_ENV", "test").upper()
environment = Environment[environment_name]
```

Poniższe przykłady metod zakładają, że `client` jest otwartym klientem bazowym
dla wybranego środowiska. W skryptach preferuj context manager, na przykład
`with Client(Environment.TEST) as client:`.

## Wybierz metodę

### Z tokenem KSeF

Użyj tokenu KSeF, gdy aplikacja ma już ważny token dla danego kontekstu. Token
działa w TEST, DEMO i PRODUCTION.

```python
import os

auth = client.authentication.with_token(
    ksef_token=os.environ["KSEF2_TOKEN"],
    nip=os.environ["KSEF2_NIP"],
    context_type="nip",
)
```

### Certyfikat TEST

Certyfikat generowany przez SDK jest przeznaczony do lokalnego developmentu i
działa tylko z `Environment.TEST`.

```python
import os

auth = client.authentication.with_test_certificate(
    nip=os.environ["KSEF2_NIP"],
)
```

### Z PEM XAdES

Użyj bajtów certyfikatu i klucza prywatnego w formacie PEM, gdy materiał certyfikatu
jest przechowywany oddzielnie. `XAdESCredentials.from_pem` przyjmuje same bajty, więc
SDK nie otwiera pliku za Ciebie, a kod trzymający materiał gdzie indziej może go
przekazać bezpośrednio.

```python
import os
from pathlib import Path

from ksef2.xades import XAdESCredentials

password = os.environ.get("KSEF2_KEY_PASSWORD")
credentials = XAdESCredentials.from_pem(
    Path("company.pem").read_bytes(),
    Path("company.key").read_bytes(),
    key_password=password.encode() if password else None,
)

auth = client.authentication.with_xades(
    nip=os.environ["KSEF2_NIP"],
    credentials=credentials,
)
```

Hasło odszyfrowuje klucz tylko podczas tworzenia poświadczeń i nie jest potem
przechowywane. Odszyfrowany klucz istnieje w pamięci wewnątrz `credentials`, więc
traktuj ten obiekt jak sekret: nie loguj go, nie zapisuj w cache ani na dysku, a po
uwierzytelnieniu usuń do niego odwołanie. `repr()` ukrywa obiekty certyfikatu i klucza.
Obiekt poświadczeń nie ma schematu Pydantic ani API serializacji JSON. Przechowuje załadowane obiekty,
sprawdza typ klucza i zgodność z certyfikatem tylko raz, a następnie używa ich do
podpisywania.

Forma z obiektami pozostaje wspierana. Załaduj materiał samodzielnie i przekaż
zwrócone certyfikat oraz klucz.

```python
import os

from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem

password = os.environ.get("KSEF2_KEY_PASSWORD")
cert = load_certificate_from_pem("company.pem")
private_key = load_private_key_from_pem(
    "company.key",
    password=password.encode() if password else None,
)

auth = client.authentication.with_xades(
    nip=os.environ["KSEF2_NIP"],
    cert=cert,
    private_key=private_key,
)
```

### Z PKCS#12

Użyj archiwum PKCS#12/PFX, gdy certyfikat i klucz prywatny są w jednym pliku.

```python
import os
from pathlib import Path

from ksef2.xades import XAdESCredentials

password = os.environ.get("KSEF2_P12_PASSWORD")
credentials = XAdESCredentials.from_pkcs12(
    Path("company.p12").read_bytes(),
    password=password.encode() if password else None,
)

auth = client.authentication.with_xades(
    nip=os.environ["KSEF2_NIP"],
    credentials=credentials,
)
```

`XAdESCredentials.from_der` robi to samo dla bajtów certyfikatu i klucza w kodowaniu
DER. Przekazanie `credentials` razem z `cert` albo `private_key`, albo nieprzekazanie
żadnej pary, podnosi `KSeFArgumentError` przed wysłaniem jakiegokolwiek żądania.

Forma z obiektami pozostaje wspierana:

```python
import os

from ksef2.xades import load_certificate_and_key_from_p12

password = os.environ.get("KSEF2_P12_PASSWORD")
cert, private_key = load_certificate_and_key_from_p12(
    "company.p12",
    password=password.encode() if password else None,
)

auth = client.authentication.with_xades(
    nip=os.environ["KSEF2_NIP"],
    cert=cert,
    private_key=private_key,
)
```

## Profile kompatybilne z CLI

`ksef2-cli` i SDK używają tego samego lokalnego pliku profili. Profil
przechowuje niesekretne ustawienia: środowisko, NIP, metodę uwierzytelnienia,
ścieżki certyfikatów, ustawienia pollingu i nazwę zmiennej środowiskowej z
sekretem. Nie zapisuje wartości tokenów ani haseł certyfikatów.

```bash
ksef2 profile create test-company \
  --env test \
  --nip 5261040828 \
  --test-cert

ksef2 profile create prod-token \
  --env production \
  --nip "$KSEF2_NIP" \
  --token-env KSEF2_TOKEN
```

Wybierz aktywny profil dla kolejnych komend CLI:

```bash
ksef2 profile use prod-token
ksef2 --json profile current
```

Albo wybierz profil dla jednej powłoki lub jednej komendy:

```bash
export KSEF2_PROFILE=prod-token
ksef2 --json auth login

ksef2 --profile test-company --json auth login
```

Kolejność wyboru profilu jest taka sama w CLI i SDK:

1. Jawna nazwa profilu.
2. `KSEF2_PROFILE`.
3. `active_profile` w lokalnym pliku konfiguracji.

Użyj `KSEF2_CONFIG` albo `config_path="..."`, gdy plik profili nie znajduje się
w domyślnej lokalizacji `~/.config/ksef2/config.toml`. Istniejące pliki
`~/.config/ksef2-cli/config.toml` nadal są odczytywane jako zgodność wsteczna.

Użyj istniejącego profilu w kodzie SDK:

```python
from ksef2 import Client, Environment

with Client(Environment.PRODUCTION) as client:
    auth = client.authentication.with_profile()

    # Aby zamiast tego jawnie wybrać profil:
    # auth = client.authentication.with_profile("prod-token")
```

Środowisko klienta bazowego musi zgadzać się ze środowiskiem wybranego profilu.

Utwórz albo zaktualizuj ten sam plik profili z kodu SDK:

```python
from ksef2 import Environment
from ksef2.profiles import Profile, ProfileStore, TokenProfileAuth

store = ProfileStore.default()
store.save(
    "prod-token",
    Profile(
        environment=Environment.PRODUCTION,
        nip="5261040828",
        auth=TokenProfileAuth(token_env="KSEF2_TOKEN"),
    ),
    activate=True,
    overwrite=True,
)
```

Klient asynchroniczny używa tego samego pliku profili i tej samej kolejności
wyboru. Ten fragment należy umieścić wewnątrz funkcji `async def main()`:

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.PRODUCTION) as client:
    auth = await client.authentication.with_profile("prod-token")
```

**Zobacz też:**

- [Użyj profili](profiles.md): Twórz profile przez ksef2-cli, uwierzytelniaj się przez with_profile() i zarządzaj profilami przez ProfileStore.
- [Uwierzytelnianie w CLI](../../cli/guides/authentication.md): Użyj tych samych przepływów tokenu, certyfikatu TEST, PEM XAdES, PKCS#12 i profili z poziomu ksef2-cli.

## Zalecany przepływ

1. Umieść sekrety w zmiennych środowiskowych.

   Użyj `KSEF2_TOKEN`, `KSEF2_KEY_PASSWORD` albo `KSEF2_P12_PASSWORD`.

2. Trzymaj niesekretne ustawienia w jednym miejscu.

   Dla w pełni własnych konfiguracji użyj konfiguracji aplikacji. Jeśli to samo
   środowisko obsługujesz też z terminala, skorzystaj z profili `ksef2-cli`.

3. Utwórz klienta bazowego dla środowiska.

   Użyj `Client(Environment.TEST)`, `Client(Environment.DEMO)` albo
   `Client(Environment.PRODUCTION)`.

4. Uwierzytelnij się raz i przekaż klienta do przepływów.

   Klient uwierzytelniony przechowuje tokeny dostępu i udostępnia moduły
   przepływów.

## Błędy

Każdy błąd zgłaszany przez SDK jest podklasą `KSeFException`, błędy żądań HTTP
też. Łap najpierw `KSeFTransportError`, gdy brak użytecznej odpowiedzi zmienia to,
co robisz dalej.

```python
from ksef2 import Client, Environment, KSeFException, KSeFTransportError

try:
    with Client(Environment.TEST) as client:
        auth = client.authentication.with_test_certificate(nip="5261040828")
except KSeFTransportError as exc:
    print(f"No usable response: {exc.method} {exc.path}")
except KSeFException as exc:
    print(exc)
```

## Następne przepływy

- [Wysyłanie faktur](send-invoices.md): Otwórz sesję online albo batch po uwierzytelnieniu.
- [Wyszukiwanie faktur](query-invoices.md): Pobierz metadane faktur z filtrami i paginacją.
- [Pobieranie faktur](download-invoices.md): Pobierz przetworzone faktury albo szyfrowane paczki eksportu.

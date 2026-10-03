---
title: Użyj profili
description: Współdziel lokalną konfigurację profili ksef2-cli z uwierzytelnianiem SDK.
---

Profile to lokalne, nazwane ustawienia uwierzytelniania współdzielone przez
`ksef2-cli` i SDK. Używaj ich wtedy, gdy ta sama stacja developerska wykonuje
komendy w terminalu i skrypty Pythona dla tego samego kontekstu KSeF.

Profil przechowuje ustawienia niesekretne: środowisko, NIP, metodę
uwierzytelnienia, ścieżki certyfikatów, ustawienia pollingu i nazwę zmiennej
środowiskowej z sekretem. Nie powinien przechowywać wartości tokenów KSeF,
haseł kluczy prywatnych ani haseł PKCS#12.

:::tip[Profile są do pracy lokalnej]
Profile są warstwą wygody dla powtarzalnych lokalnych workflow. W CI i
aplikacjach hostowanych zwykle czytelniej jest przekazać konfigurację przez
system wdrożeniowy, a sekrety czytać bezpośrednio ze zmiennych
środowiskowych.
:::

## Utwórz profil w CLI

CLI jest najwygodniejszą drogą do tworzenia i sprawdzania pliku profili.

```bash
ksef2 profile create test-company \
  --env test \
  --nip 5261040828 \
  --test-cert

ksef2 profile current
ksef2 profile show test-company
```

Profile tokenowe i certyfikatowe zapisują nazwę zmiennej środowiskowej, która
zawiera sekret, a nie samą wartość sekretu:

```bash
export KSEF2_TOKEN=podmien-na-prawdziwy-token-ksef

ksef2 profile create prod-token \
  --env production \
  --nip 5261040828 \
  --token-env KSEF2_TOKEN
```

**Zobacz też:**

- [Konfiguracja CLI](../../cli/guides/configuration.md): Twórz, wybieraj, sprawdzaj i usuwaj profile w ksef2-cli.
- [Uwierzytelnianie CLI](../../cli/guides/authentication.md): Wybierz profil tokenowy, certyfikat TEST, PEM XAdES albo PKCS#12 z poziomu komendy.

## Uwierzytelnij się profilem

`with_profile()` czyta ten sam plik profili co CLI. Wywołanie bez nazwy używa
wybranego profilu.

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_profile()
```

Przekaż nazwę, żeby pominąć aktywny profil dla jednego wywołania:

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_profile("test-company")
```

Środowisko klienta głównego musi zgadzać się ze środowiskiem wybranego profilu.
Profil `test` musi być użyty z `Client(Environment.TEST)`, profil `demo` z
`Client(Environment.DEMO)`, a profil `production` z
`Client(Environment.PRODUCTION)`.

Jeżeli profil ma wybrać środowisko klienta, wczytaj go najpierw:

```python
from ksef2 import Client
from ksef2.profiles import load_cli_profile

profile_name, profile = load_cli_profile("prod-token")

with Client(profile.sdk_environment) as client:
    auth = client.authentication.with_profile(profile_name)
```

Klient async używa tego samego pliku profili i tej samej kolejności wyboru:

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_profile("test-company")
```

## Kolejność wyboru profilu

SDK wybiera profil w tej samej kolejności co `ksef2-cli`:

1. Jawna nazwa przekazana do `with_profile("name")`.
2. `KSEF2_PROFILE` w środowisku procesu.
3. `active_profile` w lokalnym pliku konfiguracji profili.

Domyślny plik profili to:

```text
~/.config/ksef2/config.toml
```

Istniejące pliki `~/.config/ksef2-cli/config.toml` nadal są odczytywane jako
zgodność wsteczna.

Ustaw `KSEF2_CONFIG` albo przekaż `config_path`, gdy plik profili znajduje się
w innym miejscu:

```python
from ksef2 import Client, Environment

with Client(Environment.PRODUCTION) as client:
    auth = client.authentication.with_profile(
        "prod-token",
        config_path="./local.ksef2.toml",
    )
```

## Zarządzaj profilami z kodu SDK

Użyj `ProfileStore`, gdy narzędzie w Pythonie ma tworzyć, aktualizować,
wybierać albo sprawdzać ten sam plik profili co CLI. Użyj `with_profile()`,
gdy potrzebujesz tylko uwierzytelnienia.

```python
from ksef2 import Environment
from ksef2.profiles import Profile, ProfileStore, TokenProfileAuth

store = ProfileStore.default()
store.save(
    "prod-token",
    Profile(
        environment=Environment.PRODUCTION,
        nip="5261040828",
        auth=TokenProfileAuth(
            token_env="KSEF2_TOKEN",
            context_type="nip",
        ),
        poll_interval=2.0,
        max_poll_attempts=90,
    ),
    activate=True,
    overwrite=True,
)
```

Dla profilu z certyfikatem TEST:

```python
from ksef2 import Environment
from ksef2.profiles import Profile, ProfileStore, TestCertificateProfileAuth

store = ProfileStore.default()
store.save(
    "test-company",
    Profile(
        environment=Environment.TEST,
        nip="5261040828",
        auth=TestCertificateProfileAuth(),
    ),
    activate=True,
    overwrite=True,
)
```

Sprawdzaj i wybieraj profile przez store:

```python
from ksef2.profiles import ProfileStore

store = ProfileStore.default()

profiles = store.list()
current = store.current()
profile = store.get("prod-token")
store.use("prod-token")
store.delete("old-profile")
```

`current` to `None` albo krotka `(name, profile)`.

## Co zawiera konfiguracja

Wyrenderowany plik używa tych samych nazw pól co publiczne modele profili SDK:

```toml
active_profile = "prod-token"

[profiles.prod-token]
environment = "production"
nip = "5261040828"
poll_interval = 2.0
max_poll_attempts = 90

[profiles.prod-token.auth]
type = "token"
token_env = "KSEF2_TOKEN"
context_type = "nip"
```

Profile XAdES zapisują ścieżki i nazwy zmiennych środowiskowych z hasłami:

```python
from ksef2 import Environment
from ksef2.profiles import Profile, ProfileStore, XadesP12ProfileAuth

store = ProfileStore.default()
store.save(
    "prod-p12",
    Profile(
        environment=Environment.PRODUCTION,
        nip="5261040828",
        auth=XadesP12ProfileAuth(
            p12="signing-credentials.p12",
            p12_password_env="KSEF2_P12_PASSWORD",
        ),
    ),
    activate=False,
    overwrite=True,
)
```

## Starsze i nieznane klucze

Profile zapisane przez ksef2-cli 0.0.2 mogą zawierać płaski klucz `auth_timeout`
(sekundy). SDK nadal go akceptuje, zamienia na `max_poll_attempts` wzorem, którego
używa `with_profile()` (`timeout = max_poll_attempts * poll_interval`, czyli
`max_poll_attempts = ceil(auth_timeout / poll_interval)`, domyślny interwał to
1 sekunda) i emituje `DeprecationWarning`. Jawnie podane `max_poll_attempts` ma
pierwszeństwo. `auth_timeout` zostanie usunięty w ksef2 2.0; zastąp go kluczem
`max_poll_attempts` i opcjonalnie `poll_interval`.

Każdy inny nieznany klucz w profilu jest ignorowany bez ostrzeżenia, więc
ustawienia specyficzne dla narzędzi zapisane obok pól SDK nie psują wczytywania.

## Zalecany przepływ

1. Umieść wartości sekretów w zmiennych środowiskowych.

   Przykłady: `KSEF2_TOKEN`, `KSEF2_KEY_PASSWORD` i `KSEF2_P12_PASSWORD`.

2. Utwórz albo wybierz profil przez `ksef2-cli`.

   Dzięki temu workflow w terminalu i skrypty Pythona używają tych samych
   ustawień.

3. Utwórz klienta SDK dla tego samego środowiska co profil.

   SDK sprawdza to przed uwierzytelnieniem.

4. Wywołaj `client.authentication.with_profile()`.

   Zwrócony klient uwierzytelniony jest używany tak samo jak przy innych
   metodach uwierzytelnienia SDK.

## Powiązane strony

- [Quickstart](../getting-started/quickstart.md): Uruchom pierwszy workflow wysyłki i pobrania, a potem dostosuj go do profilu.
- [Uwierzytelnij się](authenticate.md): Porównaj profile z bezpośrednim tokenem, certyfikatem TEST i uwierzytelnianiem XAdES.

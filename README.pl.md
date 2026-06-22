<h1 align="center">ksef2 SDK</h1>

<h3 align="center">
  Typowane SDK Pythona do automatyzacji przepływów fakturowania w KSeF 2.0.
</h3>

<p align="center">
  Budowane na podstawie opublikowanej specyfikacji OpenAPI KSeF i sprawdzane
  codziennie, żeby SDK nie rozjeżdżało się ze zmianami API.<br>
  100% pokrycia endpointów, klienci sync i async, low-level dostęp do endpointów
  oraz narzędzia do uwierzytelniania, sesji, eksportów, tokenów, uprawnień i
  certyfikatów.
</p>

<div align="center">
  <br>
  <a href="https://docs.stacking.me/ksef2/pl/sdk/intro/" title="dokumentacja ksef2">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-light.png">
      <img src="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-dark.png" alt="ksef2" width="320">
    </picture>
  </a>
  <br>
  <br>
  <p>
    <img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/coverage.json&query=$.message&label=KSeF%20API%20coverage&color=$.color" alt="Pokrycie API KSeF">
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/test-coverage.yml"><img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/test-coverage.json&query=$.message&label=Unit%20test%20coverage&color=$.color" alt="Pokrycie testami jednostkowymi"></a>
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml"><img src="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml/badge.svg" alt="Testy integracyjne"></a>
    <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit enabled"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="Licencja MIT"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  </p>
  <p>
    Języki:
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.md">English</a> ·
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.pl.md">Polski</a>
  </p>
</div>

## Czym jest ksef2?

`ksef2` to społecznościowo utrzymywane SDK Pythona dla polskiego API KSeF v2.
Jest przeznaczone dla developerów budujących integracje, automatyzacje, narzędzia
back-office i pipeline'y przetwarzania faktur wokół KSeF bez ręcznego pisania
żądań HTTP, pętli pollingu albo obsługi szyfrowania.

Projekt nie jest publikowany, zatwierdzany ani wspierany przez Ministerstwo
Finansów. Oficjalna [dokumentacja KSeF](https://api-test.ksef.mf.gov.pl/docs/v2/)
pozostaje źródłem prawdy dla zachowania API.

SDK obecnie celuje w wersję OpenAPI KSeF `2.6.1`.

## Instalacja

```bash
# standardowa instalacja przez pip
pip install ksef2

# instalacja przez uv w projekcie aplikacji
uv add ksef2
```

Wymagany jest Python 3.12 lub nowszy.

Opcjonalne dodatki:

```bash
pip install "ksef2[pdf]"             # lokalne renderowanie faktur do PDF
pip install "ksef2[runtime-checks]"  # opcjonalne sprawdzanie typów przez beartype
```

Sprawdzanie typów w runtime jest wyłączone, dopóki nie ustawisz
`KSEF2_RUNTIME_CHECKS=1`.

CLI jest dystrybuowane osobno jako
[`stacking-hq/ksef2-cli`](https://github.com/stacking-hq/ksef2-cli).
Zainstaluj je, gdy chcesz używać przepływów terminalowych, komend skryptowalnych
albo lokalnych profili:

```bash
uv tool install ksef2-cli
# albo
pipx install ksef2-cli
```

## Uwierzytelnianie

Wybierz metodę uwierzytelnienia pasującą do środowiska, z którym pracujesz.

```python
from ksef2 import Client, Environment
from ksef2.core.xades import (
    load_certificate_from_pem,
    load_private_key_from_pem,
)

client = Client(Environment.TEST)

# lokalne przepływy TEST mogą używać certyfikatu wygenerowanego przez SDK.
test = client.authentication.with_test_certificate(nip="5261040828")

# token działa, gdy masz już token KSeF dla kontekstu.
token = client.authentication.with_token(
    ksef_token="twoj-token-ksef",
    nip="5261040828",
)

# DEMO i PRODUKCJA mogą uwierzytelniać się certyfikatem XAdES wydanym przez MCU.
cert = load_certificate_from_pem("company.pem")
key = load_private_key_from_pem("company.key")

xades = Client(Environment.DEMO).authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=key,
)

# możesz też użyć profili CLI, żeby nie obsługiwać tokenów i certyfikatów
# bezpośrednio w kodzie aplikacji.
profile = client.authentication.with_profile("test-company")
```

### Profile ksef2-cli

Osobny pakiet [`ksef2-cli`](https://github.com/stacking-hq/ksef2-cli)
udostępnia lokalne profile do powtarzalnej pracy w CLI. Profile przechowują
niesekretne domyślne ustawienia: środowisko, NIP, metodę uwierzytelnienia,
ścieżki certyfikatów oraz nazwę zmiennej środowiskowej z sekretem.

Konfiguracja profilu w CLI:

```bash
ksef2 profile create prod-token \
  --env production \
  --nip 5261040828 \
  --token-env KSEF2_TOKEN

# profile create aktywuje nowy profil domyślnie; tej komendy użyj do zmiany kontekstu
ksef2 profile use prod-token

# przykładowe użycie CLI
ksef2 --profile prod-token invoices metadata \
  --role seller \
  --date-from 2026-01-01T00:00:00Z
```

Te komendy dodają profil do lokalnej konfiguracji `ksef2-cli` w
`~/.config/ksef2-cli/config.toml`:

```toml
# ksef2-cli local profiles
# CLI options override the selected profile for one invocation.
# Store token and password secrets in environment variables.
active_profile = "prod-token"

[profiles.prod-token]
environment = "production"
nip = "5261040828"

[profiles.prod-token.auth]
type = "token"
token_env = "KSEF2_TOKEN"
```

Użycie zdefiniowanych profili w SDK:

```python
from ksef2 import Client, Environment
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

# środowisko klienta musi zgadzać się ze środowiskiem profilu.
client = Client(Environment.PRODUCTION)

# domyślnie używa aktywnego profilu z konfiguracji CLI.
active = client.authentication.with_profile()

# albo profilu wskazanego jawnie.
seller = client.authentication.with_profile("prod-token")
```

## Wysyłanie i pobieranie faktury

```python
from pathlib import Path

from ksef2 import Client, Environment, FormSchema

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )

invoice_xml = auth.invoices.wait_for_invoice_download(
    ksef_number=status.ksef_number,
    timeout=120.0,
)

Path("downloads").mkdir(exist_ok=True)
Path("downloads/invoice.xml").write_bytes(invoice_xml)
print(status.ksef_number)
```

Po nadaniu numeru KSeF używaj `auth.invoices` do zapytań metadanych, eksportów,
pobierania paczek i bezpośredniego pobierania faktur.

## Dokumentacja

- Dokumentacja online: <https://docs.stacking.me/ksef2/pl/sdk/intro/>
- Quickstart: <https://docs.stacking.me/ksef2/pl/sdk/getting-started/quickstart/>
- Przepływy: <https://docs.stacking.me/ksef2/pl/sdk/workflows/overview/>
- API reference (EN): <https://docs.stacking.me/ksef2/sdk/reference/api-signatures/>
- Źródła dokumentacji: [`docs/en`](https://github.com/stacking-hq/ksef2/tree/main/docs/en) i [`docs/pl`](https://github.com/stacking-hq/ksef2/tree/main/docs/pl)
- Uruchamialne przykłady: [`scripts/examples`](https://github.com/stacking-hq/ksef2/tree/main/scripts/examples)

## Development

```bash
just sync
just test
just release-check
```

Dodatkowe zadania developerskie są w `justfile`, w tym testy integracyjne,
sprawdzanie pokrycia API, regenerowanie modeli OpenAPI i narzędzia release.

## Licencja

[MIT](https://github.com/stacking-hq/ksef2/blob/main/LICENSE.md)

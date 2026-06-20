<div align="center">
  <a href="https://ksef2.stacking.me/pl/sdk/intro/" title="dokumentacja ksef2">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-light.png">
      <img src="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-dark.png" alt="ksef2" width="320">
    </picture>
  </a>

  <p><strong>SDK Pythona dla polskiego API KSeF v2.</strong></p>

  <p>
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.md">English</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/coverage.json&query=$.message&label=KSeF%20API%20coverage&color=$.color" alt="Pokrycie API KSeF">
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/test-coverage.yml"><img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/test-coverage.json&query=$.message&label=Unit%20test%20coverage&color=$.color" alt="Pokrycie testami jednostkowymi"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml"><img src="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml/badge.svg" alt="Testy integracyjne"></a>
    <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="Licencja MIT"></a>
  </p>
</div>

## Przegląd

`ksef2` to społecznościowo utrzymywane SDK Pythona dla polskiego API KSeF v2.
Udostępnia klientów sync i async, typowane modele żądań i odpowiedzi, pomocniki
sesji faktur, budowanie faktur FA(3) oraz narzędzia dla typowych przepływów w
środowisku TEST.

Projekt nie jest publikowany, zatwierdzany ani wspierany przez Ministerstwo
Finansów. Oficjalna dokumentacja KSeF pozostaje źródłem prawdy dla zachowania
API.

SDK obecnie celuje w wersję OpenAPI KSeF `2.6.0`.

## Instalacja

```bash
pip install ksef2
```

albo:

```bash
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

## Szybki start

```python
from pathlib import Path

from ksef2 import Client, Environment, FormSchema

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    print(result.reference_number)
```

Dla integracji DEMO albo PRODUKCYJNYCH uwierzytelnij się tokenem KSeF albo
certyfikatem wydanym przez MCU. Szczegóły są w przepływie uwierzytelniania w
dokumentacji.

## Dokumentacja

- Dokumentacja online: <https://ksef2.stacking.me/pl/sdk/intro/>
- Quickstart: <https://ksef2.stacking.me/pl/sdk/getting-started/quickstart/>
- Przepływy: <https://ksef2.stacking.me/pl/sdk/workflows/overview/>
- API reference (EN): <https://ksef2.stacking.me/sdk/reference/api-signatures/>
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

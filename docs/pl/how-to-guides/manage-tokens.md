---
title: Zarządzaj tokenami
description: Generuj, listuj, sprawdzaj i cofaj tokeny KSeF przez ksef2.
---

Użyj `auth.tokens`, gdy uwierzytelniony kontekst ma tworzyć albo wycofywać
tokeny KSeF dla automatyzacji. Przykłady zakładają, że masz już
uwierzytelnionego klienta `auth`.

## Wygeneruj token

Wybierz najmniejszy zestaw uprawnień wymagany przez automatyzację, która będzie
używać tokena.

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="nightly invoice export",
)

token_reference = token.reference_number
token_secret = token.token
```

`generate()` wraca, gdy tylko KSeF udostępni jednorazową wartość credentiala.
Zwrócone pole `token` jest sekretem, którego automatyzacja użyje później do
uwierzytelniania tokenem.

Domyślny `repr` i ogólne zrzuty Pydantic pomijają sekret. Odczytuj `.token`
tylko na granicy chronionego magazynu albo użyj `to_sensitive_dict()`, gdy
potrzebujesz jawnej mapy zawierającej sekret.

:::caution[Wartość tokena jest pokazana raz]
Zapisz zwróconą wartość tokena od razu w magazynie sekretów. Późniejsze
wywołania statusu i listowania identyfikują token po `reference_number`, ale
nie odzyskują sekretnej wartości tokena.
:::

Po zapisaniu credentiala poczekaj jawnie, gdy następna operacja wymaga już
aktywnego tokena:

```python
status = auth.tokens.wait_for_activation(
    reference_number=token.reference_number,
    timeout=60.0,
    poll_interval=1.0,
)
```

Timeout albo błąd transportu z `wait_for_activation()` nie odrzuca zapisanego
wcześniej credentiala. Wznów sprawdzanie później z tym samym
`reference_number`.

## Listuj tokeny

Użyj `list_page()` dla jednej strony albo `list_all()` dla pełnego przebiegu
audytowego.

### Jedna strona

```python
page = auth.tokens.list_page()

# QueryTokensResponse
# {
#   "continuation_token": null,
#   "tokens": [
#     {
#       "reference_number": "20260625-TOKEN-...",
#       "description": "nightly invoice export",
#       "requested_permissions": ["invoice_read"],
#       "status": "active"
#     }
#   ]
# }

for item in page.tokens:
    print(item.reference_number, item.status, item.description)
```

### Wszystkie strony

```python
for page in auth.tokens.list_all():
    for item in page.tokens:
        print(item.reference_number, item.status, item.description)
```

## Sprawdź albo cofnij jeden token

Do późniejszych operacji cyklu życia użyj numeru referencyjnego tokena.

```python
status = auth.tokens.status(reference_number="20260625-TOKEN-...")

# TokenStatusResponse
# {
#   "reference_number": "20260625-TOKEN-...",
#   "status": "active"
# }
```

```python
auth.tokens.revoke(reference_number="20260625-TOKEN-...")
```

:::tip[Oddziel referencję od sekretu]
Sekret tokena trzymaj w managerze sekretów. `reference_number` zapisz w
metadanych operacyjnych, żeby później sprawdzić albo cofnąć token bez
ujawniania sekretu.
:::

## Zalecany przepływ

1. Wybierz najmniejszy zestaw uprawnień wymagany przez automatyzację.

2. Wygeneruj token w uwierzytelnionym kontekście, który ma być jego właścicielem.

3. Zapisz wartość tokena w magazynie sekretów, a numer referencyjny w metadanych.

4. Poczekaj na aktywację, gdy token musi być od razu gotowy do użycia.

5. Listuj albo sprawdzaj referencje tokenów podczas audytów.

6. Cofaj tokeny nieużywane, wygasłe albo naruszone.

## Następne przepływy

- [Uwierzytelnianie](authenticate.md): Użyj wygenerowanego tokena KSeF jako jednej z metod uwierzytelniania SDK.
- [Metody uwierzytelniania](../concepts/authentication-methods.md): Zrozum uwierzytelnianie tokenem KSeF, XAdES, certyfikatem TEST i profilami.
- [Konfiguracja klienta](client-setup.md): Utwórz klienta sync albo async przed użyciem gałęzi uwierzytelnionych.

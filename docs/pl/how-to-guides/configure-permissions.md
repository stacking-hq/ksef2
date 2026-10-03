---
title: Skonfiguruj uprawnienia
description: Nadawaj, wyszukuj, odbieraj i monitoruj uprawnienia KSeF z ksef2.
---

Użyj `auth.permissions`, gdy uwierzytelniony kontekst ma nadawać, sprawdzać albo
cofać uprawnienia KSeF. Zmiany uprawnień są asynchroniczne: metody grant i
revoke najpierw zwracają referencję operacji.

## Nadaj uprawnienia

Wybierz metodę nadania pasującą do docelowego podmiotu. Utrzymuj zakres
uprawnień tak mały, jak pozwala na to przepływ.

### Osoba

```python
operation = auth.permissions.grant_person(
    subject_type="pesel",
    subject_value="90010112345",
    permissions=["invoice_read"],
    description="Read invoices",
    first_name="Jan",
    last_name="Kowalski",
)

# GrantPermissionsResponse
# {
#   "reference_number": "20260625-PERM-..."
# }
```

### Podmiot

```python
from ksef2.models import EntityPermission

operation = auth.permissions.grant_entity(
    subject_value="1234567890",
    permissions=[
        EntityPermission(type="invoice_read", can_delegate=False),
    ],
    description="Accounting office read access",
    entity_name="Accounting Sp. z o.o.",
)
```

### Autoryzacja

```python
operation = auth.permissions.grant_authorization(
    subject_type="nip",
    subject_value="1234567890",
    permission="self_invoicing",
    description="Self-invoicing agreement",
    entity_name="Partner Sp. z o.o.",
)
```

## Poczekaj na operację

Każde wywołanie `grant_*()` i `revoke*()` zwraca uchwyt `PermissionOperation`.
Czekaj na niego, aż KSeF zgłosi wynik operacji uprawnień.

```python
status = operation.wait(timeout=60.0, poll_interval=1.0)
```

`wait()` zgłasza `KSeFPermissionOperationFailedError`, gdy KSeF zakończy
operację bez zastosowania uprawnienia, oraz `KSeFPermissionOperationTimeoutError`,
gdy nie zakończy się na czas. Aby sprawdzić jednorazowo bez czekania, wywołaj
`operation.get_status()` albo `get_operation_status()`, gdy zapisałeś tylko
numer referencyjny:

```python
status = auth.permissions.get_operation_status(
    reference_number=operation.reference_number,
)

# PermissionOperationStatusResponse
# {
#   "status": {
#     "code": 200,
#     "description": "Completed"
#   }
# }
```

:::caution[Nie pokazuj uprawnienia przed zakończeniem statusu]
Odpowiedź grant oznacza, że KSeF przyjął żądanie operacji. Poczekaj na
operację, zanim potraktujesz uprawnienie jako aktywne w aplikacji.
:::

## Wyszukaj uprawnienia

Metody `list_*()` mają osobne kształty, ponieważ KSeF rozróżnia rekordy personal,
person, entity, authorization, EU entity, subordinate entity i subunit. Każda
zwraca `Pager`: iteruj po nim, by dostać każdy rekord, wywołaj `.pages()` dla
list wielkości strony albo `.first_page()`, by wykonać jedno żądanie.

### Moje uprawnienia

```python
from ksef2.models import PersonalPermissionsQuery

permissions = auth.permissions.list_personal(
    PersonalPermissionsQuery(
        permission_types=["invoice_read"],
        permission_state="active",
    ),
)

for permission in permissions:
    print(permission.id, permission.permission_type, permission.permission_state)
```

### Nadania entity

```python
from ksef2.models import EntityPermissionsQuery

permissions = auth.permissions.list_entities(
    EntityPermissionsQuery(context_type="nip", context_value="5261040828"),
)

for permission in permissions:
    print(permission.id, permission.permission_type, permission.can_delegate)
```

### Autoryzacje

```python
from ksef2.models import AuthorizationPermissionsQuery

grants = auth.permissions.list_authorizations(
    AuthorizationPermissionsQuery(
        query_type="granted",
        permission_types=["self_invoicing"],
    ),
)

for grant in grants:
    print(grant.id, grant.authorization_scope, grant.authorized_entity_value)
```

## Cofnij uprawnienia

Użyj identyfikatora uprawnienia zwróconego przez listę. Cofnięcie też zwraca
uchwyt `PermissionOperation`.

```python
operation = auth.permissions.revoke(permission_id="permission-id")
status = operation.wait()
print(status.status.code, status.status.description)
```

Dla nadań autoryzacji użyj metody cofania autoryzacji:

```python
operation = auth.permissions.revoke_authorization(
    permission_id="authorization-id",
)
```

## Sprawdź uprawnienie do załączników

```python
status = auth.permissions.get_attachment_permission_status()

# AttachmentPermissionStatus
# {
#   "is_attachment_allowed": true,
#   "revoked_date": null
# }
```

## Zalecany przepływ

1. Nadaj najmniejszy zestaw uprawnień wymagany przez docelowy podmiot.

2. Zapisz `reference_number` operacji.

3. Poczekaj na operację przed pokazaniem uprawnienia jako aktywnego.

4. Wyszukaj uprawnienia, aby zebrać identyfikatory do audytu albo cofnięcia.

5. Cofnij po identyfikatorze uprawnienia, gdy dostęp ma się zakończyć, a potem
   poczekaj na operację cofnięcia.

## Następne przepływy

- [Uprawnienia](../concepts/permissions.md): Zrozum rodziny uprawnień KSeF i powód różnych kształtów zapytań.
- [Zarządzaj tokenami](manage-tokens.md): Generuj i cofaj tokeny automatyzacji z ograniczonym zakresem uprawnień.
- [Użyj danych TEST](use-test-data.md): Twórz sandboxowe podmioty i nadania dla testów integracyjnych.

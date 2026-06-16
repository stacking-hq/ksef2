---
title: Uprawnienia
description: Nadawanie, odbieranie i sprawdzanie uprawnień.
---

Operacje uprawnień są dostępne przez `auth.permissions`. SDK rozdziela modele
grantów, zapytań i statusów operacji.

## Nadawanie uprawnień

```python
from ksef2.domain.models import GrantPersonPermissionsRequest

result = auth.permissions.grant_person_permissions(
    request=GrantPersonPermissionsRequest(...)
)
print(result.operation_reference_number)
```

## Status operacji

```python
status = auth.permissions.get_operation_status(
    operation_reference_number="operation-reference"
)
print(status.status)
```

## Zapytania

```python
for page in auth.permissions.query_person_permissions(...):
    print(page)
```

Szczegółowe pola zależą od rodzaju identyfikatora i typu uprawnienia. Modele
publiczne importuj z `ksef2.domain.models`.

---
title: Wyszukaj dostawców PEPPOL
description: Wyszukuj dostawców usług PEPPOL zarejestrowanych w KSeF.
---

Użyj `client.peppol`, gdy potrzebujesz publicznej listy dostawców usług PEPPOL
zarejestrowanych w KSeF. To gałąź klienta głównego i nie wymaga
uwierzytelniania.

## Wyszukaj dostawców

### Jedna strona

```python
page = client.peppol.query()

# ListPeppolProvidersResponse
# {
#   "has_more": false,
#   "providers": [
#     {
#       "id": "PPL123456",
#       "name": "Example PEPPOL Provider",
#       "date_created": "2026-06-25T10:00:00Z"
#     }
#   ]
# }

for provider in page.providers:
    print(provider.id, provider.name)
```

### Wszyscy dostawcy

```python
for provider in client.peppol.all():
    print(provider.id, provider.name, provider.date_created)
```

## Cache'uj wybory dostawców

Rekordy dostawców są danymi referencyjnymi. Odpytaj je z KSeF, a potem cache'uj
id i nazwę wyświetlaną do wyboru użytkownika albo walidacji w produkcie.

```python
providers_by_id = {
    provider.id: provider.name
    for provider in client.peppol.all()
}
```

## Zalecany przepływ

1. Wyszukaj dostawców z klienta głównego.

2. Zapisz id i nazwy dostawców w cache'u danych referencyjnych aplikacji.

3. Używaj id dostawców przy walidacji wyborów użytkownika albo danych
   związanych z PEPPOL.

4. Odświeżaj cache zgodnie z wymaganiami świeżości danych w produkcie.

## Następne przepływy

- [Konfiguracja klienta](client-setup.md): Utwórz klienta głównego używanego do publicznych zapytań o dostawców PEPPOL.
- [PEPPOL](../concepts/peppol.md): Zrozum, gdzie dane dostawców PEPPOL pasują do powierzchni SDK.

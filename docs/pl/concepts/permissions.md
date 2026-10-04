---
title: Tokeny i uprawnienia
description: Zrozum tokeny, zakresy uprawnień, nadania, cofnięcia i status operacji w KSeF.
---

Uwierzytelnienie potwierdza tożsamość. Uprawnienia określają, co ta tożsamość
może zrobić. Tokeny pakują wybrane uprawnienia w wielokrotnego użytku materiał
credential. Credential może uwierzytelnić się poprawnie, a potem nie mieć prawa
do następnej operacji.

Uprawnienia określają, co podmiot, osoba, jednostka, jednostka UE, autoryzacja
albo subunit mogą zrobić w kontekście KSeF. Wiele zmian uprawnień jest
operacjami asynchronicznymi: wywołanie nadania albo cofnięcia zwraca referencję
operacji, a aplikacja potem sprawdza jej status.

Kod uprawnień powinien jawnie wskazywać identyfikator celu, zakres uprawnienia i
kontekst. Ułatwia to późniejszy audyt i odtwarzanie po błędach.

## Tokeny

`auth.tokens` tworzy, listuje, sprawdza i cofa tokeny KSeF. Generowanie tokenu
od razu zwraca uchwyt `GeneratedToken` z jednorazowym tokenem i numerem
referencyjnym. Zapisz credential przed jawnym wywołaniem `wait()` na uchwycie.
Dzięki temu timeout albo błąd transportu podczas pollingu nie odrzuci jedynej
kopii tokenu.

Wygenerowany token ma stały zestaw uprawnień. Jeśli uprawnienia mają się
zmienić, wygeneruj nowy token i cofnij stary po migracji. Generowanie tokenu
jest dostępne tylko w obsługiwanych kontekstach jednostki, takich jak NIP albo
internal ID, i wymaga wcześniejszego uwierzytelnienia XAdES zanim powstanie
wielokrotnego użytku credential tokenu.

Tokeny traktuj jako sekrety. Przechowuj wartość tokenu poza kontrolą wersji i
preferuj zmienne środowiskowe albo secret manager. Profile mogą wskazywać
zmienne środowiskowe tokenów, aby CLI i Python używały wspólnej konfiguracji bez
commitowania sekretu.

:::caution[Credential to nie autoryzacja]
Token albo certyfikat może uwierzytelnić się poprawnie i nadal dostać odmowę,
jeśli kontekst, identyfikator celu albo zakres uprawnień nie pasuje do
operacji.
:::

## Uprawnienia

API uprawnień jest celowo szczegółowe, bo KSeF odróżnia typy celów i zakresy.
SDK ma osobne metody dla nadań osoby, jednostki, autoryzacji, pośrednich,
subunit i jednostek UE oraz odpowiadające im zapytania i cofnięcia.

Oficjalny model uprawnień łączy identyfikatory celów, typy uprawnień i reguły
delegowania:

| Pojęcie | Skutek projektowy |
| --- | --- |
| Identyfikator celu | Użyj właściwego rodzaju identyfikatora, takiego jak NIP, PESEL, fingerprint certyfikatu, NIP VAT UE albo internal ID. |
| Typ uprawnienia | Trzymaj skończone wybory jawnie, na przykład odczyt faktur, zapis faktur, odczyt credentiali, zarządzanie credentialami, zarządzanie subunit, czynności egzekucyjne albo introspekcja. |
| Uprawnienia bezpośrednie i pośrednie | Pytaj i cofaj przez gałąź zgodną ze sposobem nadania uprawnienia. |
| Delegowanie | `can_delegate` ma sens tylko tam, gdzie KSeF pozwala na delegowanie w danej ścieżce uprawnień. |
| Status operacji | Nadania i cofnięcia zwracają uchwyt `PermissionOperation`; wywołaj `wait()` zanim uznasz, że uprawnienie się zmieniło. |

```python
from ksef2.models import EntityPermission

operation = auth.permissions.grant_entity(
    subject_value="1234567890",
    permissions=[EntityPermission(type="invoice_read", can_delegate=False)],
    description="Accounting office read access",
    entity_name="Accounting Sp. z o.o.",
)

status = operation.wait()
print(status.status.code, status.status.description)
```

Przy błędzie autoryzacji sprawdź:

- wybrane środowisko;
- uwierzytelniony identyfikator podatnika albo kontekstu;
- nazwę profilu i typ credentiali;
- zestaw uprawnień tokenu;
- identyfikator celu i zakres uprawnień;
- czy operacja nadania albo cofnięcia została zakończona.

## Powiązane strony

- [Zarządzaj tokenami](../how-to-guides/manage-tokens.md): Generuj, listuj, sprawdzaj i unieważniaj tokeny KSeF.
- [Skonfiguruj uprawnienia](../how-to-guides/configure-permissions.md): Nadawaj, wyszukuj, sprawdzaj i cofaj uprawnienia.
- [Operacje](../reference/operations.md): Zrozum referencje operacji, polling, retry i statusy.
- [Metody uwierzytelniania](authentication-methods.md): Oddziel tożsamość uwierzytelniania od uprawnień sprawdzanych podczas operacji chronionych.

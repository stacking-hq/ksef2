---
title: Zarządzanie tokenami
description: Generuj, listuj, sprawdzaj i unieważniaj tokeny KSeF przez ksef2.
---

Użyj `auth.tokens`, gdy uwierzytelniony kontekst logowania ma tworzyć albo unieważniać tokeny KSeF dla automatyzacji. Przykłady zakładają, że masz już uwierzytelnionego klienta `auth`.

Przekaż co najmniej jedno uprawnienie do `generate()`. Wartości tekstowe używają zapisu `snake_case`, na przykład `"invoice_read"`. Możesz też podać `TokenPermissionEnum.INVOICE_READ`. Wartość API, na przykład `"InvoiceRead"`, zgłasza wyjątek `KSeFArgumentError` z sugestią `did you mean "invoice_read"?`. Puste listy uprawnień, puste numery referencyjne w `revoke()` i puste wartości `ksef_token` w `with_token()` zgłaszają lokalnie `KSeFArgumentError` przed żądaniem HTTP.

## Wygeneruj token

Wybierz najmniejszy zestaw uprawnień wymagany przez automatyzację, która będzie używać tokena.

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="nightly invoice export",
)

token_reference = token.reference_number
token_secret = token.token
```

`generate()` zwraca obiekt `GeneratedToken`, gdy tylko KSeF udostępni jednorazową wartość sekretu. Pole `token` jest sekretem, którego automatyzacja użyje później do uwierzytelniania tokenem KSeF. Obiekt udostępnia każde pole odpowiedzi generowania.

Domyślny `repr` i ogólne zrzuty Pydantic pomijają sekret. Odczytuj `.token` tylko przy zapisie do chronionego magazynu albo użyj `to_sensitive_dict()`, gdy potrzebujesz jawnej mapy zawierającej sekret.

:::caution[Wartość tokena jest pokazana raz]
Zapisz zwróconą wartość tokena od razu w magazynie sekretów. Późniejsze wywołania statusu i listy identyfikują token po `reference_number`, ale nie odzyskują sekretu.
:::

Po zapisaniu sekretu poczekaj jawnie, gdy następna operacja wymaga już aktywnego tokena:

```python
status = token.wait(timeout=60.0, poll_interval=1.0)
```

Limit czasu albo błąd połączenia z `wait()` nie kasuje sekretu zapisanego wcześniej. Wznów sprawdzanie później przez `auth.tokens.get_status(reference_number=...)`.

### Zatwierdź oczekujący token

Jeśli `get_status()` zwraca `awaiting_approval`, zatwierdź token w uprawnionej
sesji uwierzytelnionej akceptowanym podpisem XAdES lub przez Węzeł Krajowy.

```python
approval_auth.tokens.approve(reference_number=token.reference_number)
status = token.wait(timeout=60.0)
```

Aby zaplanować okres ważności, podaj w `generate()` daty `valid_from` i
`valid_to` ze strefą czasową. Token ze statusem `not_yet_active` można użyć,
gdy KSeF zwróci `active`. Metoda `get_status()` i wyniki listowania udostępniają
`valid_from`, `valid_to` oraz ewentualne informacje o błędzie w polu `failure`.

### Wznów obiekt po restarcie

`token.resume_state()` zwraca `GeneratedTokenResumeState`: numer referencyjny tokena i nic więcej. Zapisz go przez `to_json()` i przekaż do `auth.tokens.generation()`, gdy proces roboczy kolejki albo proces po restarcie przejmuje zadanie ponownie.

```python
zapisany_stan = token.resume_state().to_json()

# Później, w tym samym lub innym procesie:
token = auth.tokens.generation(zapisany_stan)
status = token.wait(timeout=60.0, poll_interval=1.0)
```

`generation()` przyjmuje obiekt stanu albo jego JSON i zwraca obiekt, który sprawdza ten sam numer referencyjny. Jednorazowa wartość tokena nigdy nie trafia do stanu: ani w `to_json()`, ani w `to_dict()`, `model_dump()` czy `repr()`. Dlatego wznowiony obiekt nie ma `token` ani `response`. Ten sekret zapisuj osobno.

## Listuj tokeny

`list()` zwraca `Pager`. Iteruj po nim, żeby dostać każdy token, wywołaj `.pages()` dla list wielkości strony albo `.first_page()`, żeby wykonać jedno żądanie. Nic nie jest pobierane, dopóki go nie użyjesz.

### Wszystkie tokeny

```python
for item in auth.tokens.list():
    print(item.reference_number, item.status, item.description)

# TokenInfo
# {
#   "reference_number": "20260625-EC-0123456789-ABCDEF0123-45",
#   "description": "nightly invoice export",
#   "requested_permissions": ["invoice_read"],
#   "status": "active"
# }
```

### Jedna strona

```python
first = auth.tokens.list().first_page()
```

### Strona po stronie

```python
for page in auth.tokens.list().pages():
    print(len(page), "tokens on this page")
```

### Wznów od kursora

`.page()` zwraca jedną stronę `Page`: jej `items` oraz `next_cursor`, czyli napis wskazujący następną stronę. Zapisz ten napis i przekaż go później do `.page()`, w tym albo w nowym procesie, aby kontynuować bez ponownego pobierania tokenów już odczytanych.

```python
first = auth.tokens.list().page()
cursor = first.next_cursor

# Later, after a restart.
if cursor is not None:
    second = auth.tokens.list().page(cursor)
```

Odtwórz obiekt stronicowania z tymi samymi parametrami. Ten kursor zawiera stan kontynuacji KSeF dla tej kolekcji, a nie filtry. `.pages()` oraz zwykła iteracja korzystają z tego samego łańcucha kursorów, a `next_cursor` ma wartość `None` dopiero po ostatniej stronie. Sama pusta strona nie kończy przechodzenia po kolekcji. W kodzie asynchronicznym to samo odczytanie to `second = await auth.tokens.list().page(cursor)`.

## Sprawdź albo unieważnij jeden token

Do późniejszych operacji użyj numeru referencyjnego tokena.

```python
status = auth.tokens.get_status(reference_number="20260625-EC-0123456789-ABCDEF0123-45")

# TokenStatusResponse
# {
#   "reference_number": "20260625-EC-0123456789-ABCDEF0123-45",
#   "status": "active"
# }
```

```python
auth.tokens.revoke(reference_number="20260625-EC-0123456789-ABCDEF0123-45")
```

:::tip[Oddziel numer referencyjny od sekretu]
Sekret tokena trzymaj w menedżerze sekretów. `reference_number` zapisz w metadanych operacyjnych, żeby później sprawdzić albo unieważnić token bez ujawniania sekretu.
:::

## Zalecany przebieg

1. Wybierz najmniejszy zestaw uprawnień wymagany przez automatyzację.

2. Wygeneruj token w uwierzytelnionym kontekście logowania, który ma być jego właścicielem.

3. Zapisz wartość tokena w magazynie sekretów, a numer referencyjny w metadanych.

4. Poczekaj na aktywację, gdy token musi być od razu gotowy do użycia.

5. Listuj albo sprawdzaj numery referencyjne tokenów podczas audytów.

6. Unieważniaj tokeny nieużywane, wygasłe albo takie, które mogły wyciec.

## Następne strony

- [Uwierzytelnianie](authenticate.md): wygenerowany token KSeF jako jedna z metod uwierzytelniania SDK.
- [Metody uwierzytelniania](../concepts/authentication-methods.md): token KSeF, XAdES, certyfikat testowy i profile.
- [Konfiguracja klienta](client-setup.md): klient synchroniczny albo asynchroniczny, zanim użyjesz modułów uwierzytelnionych.

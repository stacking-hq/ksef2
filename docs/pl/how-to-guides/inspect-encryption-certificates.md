---
title: Sprawdź certyfikaty szyfrowania
description: Odczytuj publiczne certyfikaty szyfrowania KSeF używane przez zaszyfrowane przepływy faktur i eksportów.
---

Użyj `client.encryption`, gdy potrzebujesz kontroli startowej, diagnostyki albo
własnego cache certyfikatów. Większość przepływów faktur ładuje publiczne
certyfikaty szyfrowania automatycznie.

## Pobierz certyfikaty

`client.encryption` jest gałęzią klienta głównego, więc nie wymaga klienta
uwierzytelnionego.

### Wszystkie zastosowania

```python
certificates = client.encryption.get_certificates()

# PublicKeyCertificate
# {
#   "public_key_id": "12345",
#   "certificate_id": "abcde",
#   "valid_from": "2026-06-01T00:00:00Z",
#   "valid_to": "2026-12-01T00:00:00Z",
#   "usage": ["ksef_token_encryption", "symmetric_key_encryption"]
# }

for certificate in certificates:
    print(certificate.public_key_id, certificate.usage, certificate.valid_to)
```

### Klucze sesji/eksportu

```python
certificates = client.encryption.get_certificates(
    usage=["symmetric_key_encryption"],
)

for certificate in certificates:
    print(certificate.public_key_id, certificate.valid_to)
```

### Token auth

```python
certificates = client.encryption.get_certificates(
    usage=["ksef_token_encryption"],
)

for certificate in certificates:
    print(certificate.public_key_id, certificate.valid_to)
```

## Wstępnie załaduj przed szyfrowanymi przepływami

Wysokopoziomowe helpery sesji online, batch, uwierzytelniania tokenem i eksportu
używają tych publicznych certyfikatów, gdy szyfrują lokalny materiał klucza dla
KSeF. Wstępne ładowanie jest przydatne, gdy chcesz diagnostyki startowej zanim
worker zacznie przyjmować zadania.

```python
required_usage = "symmetric_key_encryption"
certificates = client.encryption.get_certificates(usage=[required_usage])

if not certificates:
    raise RuntimeError(f"No KSeF certificate supports {required_usage}.")
```

:::tip[Nie przypinaj treści certyfikatu w kodzie]
Pobieraj aktualne certyfikaty KSeF i cache'uj je zgodnie z potrzebami
operacyjnymi. Hardcodowane dane certyfikatu kiedyś wygasną.
:::

## Zalecany przepływ

1. Domyślnie pozwól przepływom faktur ładować certyfikaty leniwie.

2. Dodaj kontrolę startową tylko wtedy, gdy brak certyfikatu ma zatrzymać
   proces przed przyjęciem pracy.

3. Sprawdź zastosowanie wymagane przez przepływ: szyfrowanie tokenów albo
   szyfrowanie kluczy symetrycznych.

4. Alarmuj i ponów później, jeśli nie ma ważnego certyfikatu.

## Następne przepływy

- [Szyfrowanie](../concepts/encryption.md): Zrozum, gdzie publiczne certyfikaty KSeF pojawiają się w przepływach SDK.
- [Magazyn certyfikatów](configure-certificate-store.md): Kontroluj odświeżanie cache certyfikatów albo podłącz magazyn aplikacji.
- [Wyślij faktury](send-invoices.md): Użyj certyfikatów szyfrowania przez wysokopoziomowe sesje online i batch.
- [Pobierz faktury](download-invoices.md): Użyj helperów eksportu, które szyfrują i deszyfrują materiał paczek za Ciebie.

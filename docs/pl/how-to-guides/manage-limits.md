---
title: Zarządzaj limitami
description: Odczytuj i nadpisuj limity kontekstu, podmiotu i API rate limitów KSeF przez ksef2.
---

Użyj `auth.limits`, żeby sprawdzić efektywne limity, które KSeF stosuje do
bieżącego uwierzytelnionego kontekstu. Metod nadpisywania używaj tylko w jawnych
przepływach administracyjnych.

## Odczytaj efektywne limity

Odczytaj bieżące limity przed wyborem wielkości batcha, częstotliwości pollingu
albo przepływów wystawiania certyfikatów.

### Limity sesji

```python
context = auth.limits.get_context_limits()

# ContextLimits
# {
#   "online_session": {
#     "max_invoice_size_mb": 10,
#     "max_invoice_with_attachment_size_mb": 20,
#     "max_invoices": 100
#   },
#   "batch_session": {
#     "max_invoice_size_mb": 10,
#     "max_invoice_with_attachment_size_mb": 20,
#     "max_invoices": 1000
#   }
# }

print(context.online_session.max_invoices)
print(context.batch_session.max_invoice_size_mb)
```

### Limity podmiotu

```python
subject = auth.limits.get_subject_limits()

print(subject.certificate)
print(subject.enrollment)
```

### Rate limity API

```python
rate = auth.limits.get_api_rate_limits()

print(rate.invoice_send.per_minute)
print(rate.invoice_metadata.per_minute)
print(rate.invoice_download.per_hour)
```

## Nadpisz limity sesji

Nadpisań limitów sesji używaj tylko wtedy, gdy uwierzytelniony kontekst może
zarządzać limitami, a zmiana jest częścią kontrolowanego testu albo procedury
administracyjnej.

```python
from ksef2.models import ContextLimits, SessionLimits

limits = ContextLimits(
    online_session=SessionLimits(
        max_invoice_size_mb=10,
        max_invoice_with_attachment_size_mb=20,
        max_invoices=100,
    ),
    batch_session=SessionLimits(
        max_invoice_size_mb=10,
        max_invoice_with_attachment_size_mb=20,
        max_invoices=1000,
    ),
)

auth.limits.set_session_limits(limits=limits)
```

Zresetuj nadpisanie po zakończeniu testu albo zmiany tymczasowej:

```python
auth.limits.reset_session_limits()
```

## Użyj produkcyjnych domyślnych rate limitów

Użyj `set_production_rate_limits()`, gdy środowisko podobne do TEST ma skopiować
produkcyjne domyślne rate limity API.

```python
auth.limits.set_production_rate_limits()

rate = auth.limits.get_api_rate_limits()
print(rate.invoice_send.per_minute)
```

:::caution[Nie ukrywaj zmian limitów]
Nadpisania limitów wpływają na inne procesy używające tego samego kontekstu
KSeF. Trzymaj je w runbookach operacyjnych, dopisuj oczekiwany reset i nie
ukrywaj ich w zwykłym kodzie wysyłki faktur.
:::

## Zalecany przepływ

1. Odczytaj efektywne limity przed wyborem wielkości batcha, strategii uploadu
   albo częstotliwości pollingu.

2. Zachowuj produkcyjne domyślne wartości, chyba że kontrolowany test albo
   przepływ administratora wymaga nadpisania.

3. Stosuj nadpisania z jawnego kodu operacyjnego.

4. Zweryfikuj nowe limity po ich zastosowaniu.

5. Resetuj tymczasowe nadpisania po teście albo oknie utrzymaniowym.

## Następne przepływy

- [Wyślij faktury](send-invoices.md): Dobierz wysyłkę online i batch z uwzględnieniem bieżących limitów.
- [Limity](../concepts/limits.md): Zrozum, jak limity KSeF wpływają na batch, polling i ponowienia.
- [Konfiguracja klienta](client-setup.md): Skonfiguruj timeouty i retry klienta z uwzględnieniem limitów KSeF.

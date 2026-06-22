---
title: Low-level sesje i faktury
description: Otwieraj sesje KSeF i wysyłaj faktury przez schema-native endpointy low-level.
---

Użyj low-level sesji i faktur, gdy integracja musi sama posiadać materiał
szyfrowania, otwieranie sesji, wysyłkę faktury albo kolejność pollingu.

## Otwórz sesję online

```python
import base64

from ksef2.raw import (
    encrypt_symmetric_key,
    generate_session_key,
    spec,
)

cert = next(
    cert
    for cert in auth.raw.encryption.fetch_public_certificates()
    if spec.PublicKeyCertificateUsage.SymmetricKeyEncryption in cert.usage
)
aes_key, iv = generate_session_key()
encrypted_key = encrypt_symmetric_key(aes_key, cert.certificate)

opened = auth.raw.session.open_online(
    spec.OpenOnlineSessionRequest(
        formCode=spec.FormCode(
            systemCode="FA (3)",
            schemaVersion="1-0E",
            value="FA",
        ),
        encryption=spec.EncryptionInfo(
            encryptedSymmetricKey=base64.b64encode(encrypted_key).decode(),
            initializationVector=base64.b64encode(iv).decode(),
            publicKeyId=cert.publicKeyId,
        ),
    )
)
```

Zachowaj `aes_key`, `iv` i `opened.referenceNumber`; low-level wysyłka faktury
potrzebuje wszystkich trzech wartości.

## Wyślij jedną fakturę

```python
import base64

from ksef2.raw import encrypt_invoice, sha256_b64, spec

encrypted = encrypt_invoice(xml_bytes=invoice_xml, key=aes_key, iv=iv)
request = spec.SendInvoiceRequest(
    invoiceHash=sha256_b64(invoice_xml),
    invoiceSize=len(invoice_xml),
    encryptedInvoiceHash=sha256_b64(encrypted),
    encryptedInvoiceSize=len(encrypted),
    encryptedInvoiceContent=base64.b64encode(encrypted).decode(),
)

sent = auth.raw.invoices.send(opened.referenceNumber, request)
status = auth.raw.invoices.get_session_invoice_status(
    opened.referenceNumber,
    sent.referenceNumber,
)
```

Low-level API nie polluje za ciebie. Odpytuj `get_session_invoice_status()`, aż
odpowiedź zawiera numer KSeF albo końcowy status błędu.

## Zaplanuj eksport z własnym szyfrowaniem

```python
import base64
from datetime import datetime, timezone

from ksef2.raw import spec

request = spec.InvoiceExportRequest(
    encryption=spec.EncryptionInfo(
        encryptedSymmetricKey=base64.b64encode(encrypted_key).decode(),
        initializationVector=base64.b64encode(iv).decode(),
        publicKeyId=cert.publicKeyId,
    ),
    filters=spec.InvoiceQueryFilters(
        subjectType=spec.InvoiceQuerySubjectType.Subject1,
        dateRange=spec.InvoiceQueryDateRange(
            dateType=spec.InvoiceQueryDateType.Issue,
            **{"from": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        ),
    ),
    compressionType=spec.CompressionType.Zip,
)

export = auth.raw.invoices.export(request)
package = auth.raw.invoices.get_export_status(export.referenceNumber)
```

Użyj wyższego poziomu `auth.invoices.fetch_package_bytes(...)` tylko wtedy, gdy
masz też `aes_key` i `iv` wymagane do odszyfrowania paczki.

## Przygotowanie batcha

`ksef2.raw.prepare_batch_package` re-eksportuje niższopoziomowy builder paczki
batch. Możesz przekazać `aes_key`, `iv`, `encrypted_key` i `public_key_id`, a
potem otworzyć sesję przez `auth.raw.session.open_batch()` albo step-level
`auth.open_batch_session(...)`.

---
title: Low-level sessions and invoices
description: Open KSeF sessions and submit invoice payloads through schema-native low-level endpoints.
---

Use low-level session and invoice calls when your integration needs to own
encryption material, session opening, invoice submission, or polling order.

## Open an online session

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

Keep `aes_key`, `iv`, and `opened.referenceNumber`; low-level invoice submission
needs all three.

## Send one invoice

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

Low-level calls do not poll for you. Poll `get_session_invoice_status()` until
the response contains a KSeF number or reaches a failed terminal status.

## Schedule an export with caller-owned encryption

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

Use the higher-level `auth.invoices.fetch_package_bytes(...)` only when you also
have the `aes_key` and `iv` required to decrypt the package.

## Batch preparation

`ksef2.raw.prepare_batch_package` re-exports the lower-level batch package
builder. It lets you provide `aes_key`, `iv`, `encrypted_key`, and
`public_key_id`, then open the batch session with `auth.raw.session.open_batch()`
or the step-level `auth.open_batch_session(...)`.

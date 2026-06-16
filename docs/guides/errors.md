---
title: Error Handling
description: Understand SDK exceptions, transport errors, and KSeF API errors.
---

The SDK raises `KSeFException` subclasses for errors it can classify: KSeF API
error responses, SDK-side validation failures, polling timeouts, encryption and
session state errors, and other typed SDK failures.

Transport and network failures from HTTP clients may still propagate as
`httpx.HTTPError`. Keep that class in your catch list when you want one boundary
around both SDK-classified errors and connection, DNS, timeout, or protocol
failures.

Import stable exception classes from the package root:

```python
from ksef2 import KSeFApiError, KSeFRateLimitError, KSeFTokenStatusTimeoutError
```

`ksef2.core.exceptions` remains importable for applications that already use
that compatibility path.

## Exception Hierarchy

```text
KSeFException
├── KSeFApiError
│   ├── KSeFAuthError
│   └── KSeFRateLimitError
├── KSeFValidationError
├── KSeFEncryptionError
├── KSeFSessionError
├── KSeFClientClosedError
├── KSeFUnsupportedEnvironmentError
├── NoCertificateAvailableError
├── KSeFMetadataPaginationError
├── KSeFExportTimeoutError
├── KSeFInvoiceQueryTimeoutError
├── KSeFInvoiceDownloadTimeoutError
├── KSeFInvoiceProcessingTimeoutError
├── KSeFBatchSessionTimeoutError
├── KSeFAuthPollingTimeoutError
└── KSeFTokenStatusTimeoutError
```

## Catch Order

Catch the most specific SDK subclasses before broader base classes, then catch
`httpx.HTTPError` for transport failures that were not converted into
`KSeFException`:

```python
import httpx

from ksef2 import (
    KSeFApiError,
    KSeFAuthError,
    KSeFException,
    KSeFRateLimitError,
)

try:
    page = auth.tokens.list_page()
except KSeFRateLimitError as exc:
    print(f"Retry after {exc.retry_after} seconds")
except KSeFAuthError:
    print("Authentication or authorization failed")
except KSeFApiError as exc:
    print(exc.status_code, exc.exception_code)
except KSeFException as exc:
    print(f"SDK-classified error: {exc}")
except httpx.HTTPError as exc:
    print(f"Transport error: {exc}")
```

## API Errors

`KSeFApiError` represents an error response from KSeF. It exposes:

- `status_code`: the HTTP status code returned by KSeF
- `exception_code`: an `ExceptionCode` value
- `response`: the parsed response model when one was available

`KSeFAuthError` is used for authentication and authorization responses such as
401 and 403. `KSeFRateLimitError` is used for 429 responses and includes
`retry_after`, populated from the response headers when KSeF provides it.

## Exception Codes

`ExceptionCode` contains SDK-known KSeF exception codes, including
`NOT_PROCESSED_YET`. When KSeF returns a code unknown to this SDK version, it is
mapped to `ExceptionCode.UNKNOWN_ERROR` so callers always receive a valid enum
value.

For invoice downloads, KSeF can return `NOT_PROCESSED_YET` while the invoice is
still being prepared. The SDK's invoice service uses that code as a retry signal:

```python
from ksef2 import ExceptionCode, KSeFApiError

try:
    xml = auth.invoices.download_invoice(ksef_number="KSeF-number")
except KSeFApiError as exc:
    if exc.exception_code is ExceptionCode.NOT_PROCESSED_YET:
        # Wait and retry, or call wait_for_invoice_download(...).
        ...
    else:
        raise
```

For that workflow, prefer the built-in helper when possible:

```python
xml = auth.invoices.wait_for_invoice_download(ksef_number="KSeF-number")
```

## Polling Timeouts

Timeout exceptions raised by SDK-side polling helpers do not represent HTTP
responses and do not expose `status_code`.

- `KSeFAuthPollingTimeoutError`: authentication status polling exceeded
  `timeout`
- `KSeFTokenStatusTimeoutError`: generated token status polling exceeded
  `timeout`
- `KSeFInvoiceDownloadTimeoutError`: invoice download polling exceeded
  `timeout`
- `KSeFInvoiceQueryTimeoutError`: invoice metadata polling exceeded `timeout`
- `KSeFExportTimeoutError`: export package polling exceeded `timeout`
- `KSeFInvoiceProcessingTimeoutError`: session invoice processing exceeded
  `timeout`
- `KSeFBatchSessionTimeoutError`: batch session processing exceeded `timeout`

Timeout errors expose their relevant reference fields and `timeout`.

```python
from ksef2 import KSeFTokenStatusTimeoutError

try:
    token = auth.tokens.generate(
        permissions=["invoice_read"],
        description="Reporting",
        timeout=10.0,
    )
except KSeFTokenStatusTimeoutError as exc:
    print(exc.reference_number, exc.timeout)
```

## Validation and SDK State Errors

`KSeFValidationError` covers SDK-side validation failures. Endpoint and client
methods can raise it when a KSeF response body is malformed or no longer matches
the response model the SDK expects.

State and capability errors use narrower subclasses such as `KSeFSessionError`,
`KSeFClientClosedError`, `KSeFUnsupportedEnvironmentError`, and
`NoCertificateAvailableError`.

## Non-SDK Exceptions

Some helpers intentionally keep non-SDK exceptions visible when those exceptions
come from the underlying local operation rather than from KSeF. File, render,
and export-package helpers may surface exceptions such as `FileNotFoundError`
or `OSError` for local filesystem work, `ValueError` for unsafe package part
names, `ImportError` for missing optional PDF dependencies, `RuntimeError` when
the PDF backend returns no bytes, and `httpx.HTTPStatusError` for presigned
export package downloads that return an error status.

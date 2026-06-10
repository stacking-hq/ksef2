# Error Handling

The SDK raises `KSeFException` subclasses for errors it can classify. Import
stable exception classes from the package root:

```python
from ksef2 import KSeFApiError, KSeFRateLimitError, KSeFTokenStatusTimeoutError
```

`ksef2.core.exceptions` remains importable for applications that already use
that path.

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

## API Errors

`KSeFApiError` represents an error response from KSeF. It exposes:

- `status_code`: the HTTP status code returned by KSeF
- `exception_code`: an `ExceptionCode` value
- `response`: the parsed response model when one was available

`KSeFAuthError` is used for authentication and authorization responses such as
401 and 403. `KSeFRateLimitError` is used for 429 responses and includes
`retry_after`, populated from the response headers when KSeF provides it.

```python
from ksef2 import KSeFApiError, KSeFRateLimitError

try:
    page = auth.tokens.list_page()
except KSeFRateLimitError as exc:
    print(f"Retry after {exc.retry_after} seconds")
except KSeFApiError as exc:
    print(exc.status_code, exc.exception_code)
```

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
  `max_poll_attempts`
- `KSeFTokenStatusTimeoutError`: generated token status polling exceeded
  `max_poll_attempts`
- `KSeFInvoiceDownloadTimeoutError`: invoice download polling exceeded
  `timeout`
- `KSeFInvoiceQueryTimeoutError`: invoice metadata polling exceeded `timeout`
- `KSeFExportTimeoutError`: export package polling exceeded `timeout`
- `KSeFInvoiceProcessingTimeoutError`: session invoice processing exceeded
  `timeout`
- `KSeFBatchSessionTimeoutError`: batch session processing exceeded `timeout`

The attempt-based timeout errors expose `reference_number`, `attempts`,
`poll_interval`, and `elapsed`. Time-based timeout errors expose their relevant
reference fields and `timeout`.

```python
from ksef2 import KSeFTokenStatusTimeoutError

try:
    token = auth.tokens.generate(
        permissions=["invoice_read"],
        description="Reporting",
        max_poll_attempts=10,
    )
except KSeFTokenStatusTimeoutError as exc:
    print(exc.reference_number, exc.attempts, exc.elapsed)
```

## Validation and SDK State Errors

`KSeFValidationError` covers SDK-side validation failures. State and capability
errors use narrower subclasses such as `KSeFSessionError`,
`KSeFClientClosedError`, `KSeFUnsupportedEnvironmentError`, and
`NoCertificateAvailableError`.

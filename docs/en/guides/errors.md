---
title: Error Handling
description: Catch SDK exceptions, inspect KSeF responses, and handle polling timeouts.
---

Use SDK exceptions for failures that KSeF returns or that the SDK can classify.
Use `httpx.HTTPError` for transport failures where no KSeF response was parsed.

## Catch SDK and transport errors separately

```python
import httpx

from ksef2 import KSeFApiError, KSeFException

try:
    result = auth.invoices.query_metadata(filters=filters)
except KSeFApiError as exc:
    print(exc.status_code)
    print(exc.exception_code)
except KSeFException as exc:
    print(exc.context)
except httpx.HTTPError as exc:
    print(f"Network or transport failure: {exc}")
```

Catch specific SDK exceptions before `KSeFException`. `KSeFException` is the
base class for SDK-classified errors, including API responses, validation,
encryption, session lifecycle, and polling timeout failures.

## Inspect API response details

`KSeFApiError` is raised for KSeF 4xx and 5xx responses. It exposes:

- `status_code`: the HTTP status code returned by KSeF;
- `exception_code`: the normalized `ExceptionCode` when KSeF returned a known
  exception code;
- `response`: the parsed KSeF error model when the response body could be
  parsed.

```python
from ksef2 import ExceptionCode, KSeFApiError

try:
    xml = auth.invoices.download_invoice(ksef_number=ksef_number)
except KSeFApiError as exc:
    if exc.exception_code is ExceptionCode.NOT_PROCESSED_YET:
        print("KSeF knows the invoice, but it is not ready yet.")
    if exc.response is not None:
        print(exc.response.model_dump_json(indent=2))
```

The parsed `response` model preserves the KSeF payload shape. Use
`model_dump()` or `model_dump_json()` when logging structured diagnostics.

## Handle rate limits

KSeF `429` responses raise `KSeFRateLimitError`. When KSeF sends a
`Retry-After` header, the SDK exposes it as `retry_after`.

```python
from time import sleep

from ksef2 import KSeFRateLimitError

try:
    page = auth.invoices.query_metadata(filters=filters)
except KSeFRateLimitError as exc:
    delay = exc.retry_after if exc.retry_after is not None else 5
    sleep(delay)
```

For background workers, combine `retry_after` with your queue or retry policy
instead of sleeping inside request handlers.

## Handle polling timeouts

Operations that poll KSeF raise SDK timeout exceptions when the configured
`timeout` expires. These exceptions are not HTTP timeouts. They mean the SDK
kept polling successfully, but KSeF did not reach the expected state in time.

| Operation | Timeout exception |
| --- | --- |
| Authentication polling | `KSeFAuthPollingTimeoutError` |
| Token activation polling | `KSeFTokenStatusTimeoutError` |
| Online invoice processing | `KSeFInvoiceProcessingTimeoutError` |
| Invoice metadata visibility | `KSeFInvoiceQueryTimeoutError` |
| Direct invoice download readiness | `KSeFInvoiceDownloadTimeoutError` |
| Export package readiness | `KSeFExportTimeoutError` |
| Batch session completion | `KSeFBatchSessionTimeoutError` |

Most timeout exceptions expose the relevant reference number plus `timeout`.

```python
from ksef2 import KSeFInvoiceProcessingTimeoutError

try:
    status = session.wait_for_invoice_ready(
        invoice_reference_number=reference_number,
        timeout=60.0,
    )
except KSeFInvoiceProcessingTimeoutError as exc:
    print(exc.invoice_reference_number)
    print(exc.timeout)
```

Persist session and invoice references before polling. A later worker can resume
status checks even if the first process times out.

## Retry `NOT_PROCESSED_YET`

Some lower-level KSeF calls can return `ExceptionCode.NOT_PROCESSED_YET` while a
resource exists but is not ready. High-level wait helpers already handle this
where it is part of the workflow, for example `wait_for_invoice_download()`.

```python
xml = auth.invoices.wait_for_invoice_download(
    ksef_number=ksef_number,
    timeout=120.0,
    poll_interval=2.0,
)
```

If you call lower-level methods directly, treat `NOT_PROCESSED_YET` as a
retryable state only for operations where KSeF documents asynchronous
availability. Do not retry validation or authorization failures as if they were
processing delays.

## Recommended flow

1. Catch the narrow SDK exception that your workflow can act on.
2. Use `KSeFApiError.response` for structured diagnostics.
3. Use `KSeFRateLimitError.retry_after` to schedule retries.
4. Treat SDK polling timeouts as resumable workflow state, not as lost work.
5. Catch `httpx.HTTPError` separately for network, TLS, DNS, and connection
   failures.

## Reference

- [Client guide](client.md)
- [Status and UPO workflow](../workflows/status-upo.mdx)
- [Errors reference](../reference/api/errors.md)

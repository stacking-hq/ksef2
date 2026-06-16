---
title: Sessions
description: Work with authentication sessions, invoice sessions, and resumable state.
---

The SDK exposes two different session concepts:

1. Authentication sessions through `auth.sessions`
2. Invoice sessions through `auth.online_session()`, `auth.batch_session()`, and historical listings on `auth.invoice_sessions`

This guide focuses on invoice sessions.

## Open an Online Session

```python
from pathlib import Path

from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    print(result.reference_number)
```

Manual lifecycle is also supported:

```python
session = auth.online_session(form_code=FormSchema.FA3)
try:
    result = session.send_invoice(invoice_xml=b"<Invoice />")
finally:
    session.close()
```

SDK endpoints:
- `POST /sessions/online`
- `POST /sessions/online/{referenceNumber}/close`

## Prepare and Send a Batch

```python
from pathlib import Path

from ksef2.domain.models import BatchInvoice

prepared_batch = auth.batch.prepare_batch(
    invoices=[
        BatchInvoice(
            file_name="invoice-1.xml",
            content=Path("invoice-1.xml").read_bytes(),
        ),
        BatchInvoice(
            file_name="invoice-2.xml",
            content=Path("invoice-2.xml").read_bytes(),
        ),
    ]
)

with auth.batch_session(prepared_batch=prepared_batch) as session:
    session.upload_parts()
    reference_number = session.reference_number

status = auth.batch.wait_for_completion(session=reference_number)
print(status.status.code, status.status.description)
```

For staged workflows, `auth.batch` also exposes:
- `prepare_batch()` / `prepare_batch_from_paths()`
- `open_session()`
- `get_status()`, `list_invoices()`, `list_failed_invoices()`, `get_upo()`

`session.upload_parts()` lives on the opened batch session because uploads are only
valid while the session is open. Closing the session triggers KSeF batch processing,
so `wait_for_completion()` happens after the `with` block.

For the one-shot workflow:

```python
state = auth.batch.submit_batch(invoices=[...])
status = auth.batch.wait_for_completion(session=state)
```

If you already prepared the package separately, `auth.batch.submit_prepared_batch()`
opens, uploads, and closes the session in one call.

Low-level SDK endpoints used by the batch workflow:
- `POST /sessions/batch`
- `POST /sessions/batch/{referenceNumber}/close`
- presigned part uploads returned in `partUploadRequests`
- `GET /sessions/{referenceNumber}`

## Session Status and Contents

```python
status = session.get_status()
print(status.status.code, status.status.description)

state = session.get_state()
print(state.reference_number, state.valid_until)

invoices = session.list_invoices()
failed = session.list_failed_invoices()
print(len(invoices.invoices), len(failed.invoices))
```

## Resume an Online Session

```python
from ksef2.domain.models.session import OnlineSessionState

state = session.get_state()
payload = state.model_dump_json()

restored_state = OnlineSessionState.model_validate_json(payload)
resumed = auth.resume_online_session(state=restored_state)
resumed.close()
```

Resuming a session reconstructs the local SDK object from stored state. It does
not validate the session with KSeF at construction time, and it does not refresh
the stored `access_token`. If the token is stale, the next API call will fail and
the caller should authenticate again before resuming work.

Example:
- [`scripts/examples/session/session_resume.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/session/session_resume.py)

## Resume a Batch Session

```python
from ksef2.domain.models import BatchSessionState

state = session.get_state()
payload = state.model_dump_json()

restored_state = BatchSessionState.model_validate_json(payload)
resumed = auth.resume_batch_session(state=restored_state)
print(resumed.reference_number)
```

The same caveat applies to batch sessions: resume restores local state only. KSeF
server-side validation happens when the resumed session makes a request.

## Query Historical Invoice Sessions

Use `auth.invoice_sessions` to inspect previously opened invoice sessions.
`session_type` is required and accepts `"online"` or `"batch"`.

```python
sessions = auth.invoice_sessions.query(session_type="online")
for item in sessions.sessions:
    print(item.reference_number, item.status.description)
```

To iterate all pages:

```python
for page in auth.invoice_sessions.all(session_type="online"):
    print(len(page.sessions))
```

SDK endpoint: `GET /sessions`

## Examples

- [`scripts/examples/scenarios/session_workflow.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/scenarios/session_workflow.py)
- [`scripts/examples/session/session_resume.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/session/session_resume.py)
- [`scripts/examples/session/session_management.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/session/session_management.py)
- [`scripts/examples/invoices/send_batch.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/send_batch.py)
- [`scripts/examples/invoices/submit_batch.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/submit_batch.py)

## Related

- [Invoices](invoices.md)
- [Authentication](authentication.md)

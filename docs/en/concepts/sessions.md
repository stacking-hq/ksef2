---
title: Sessions
description: Understand online, batch, authentication, and historical session state in ksef2.
---

A KSeF session is a remote workflow container. It groups several API calls under
one reference number so KSeF can process encrypted invoices, expose status, and
produce UPO documents after the work is finished.

In the SDK, a session object is a handle to that remote workflow. It is not the
source of truth. The source of truth is the session reference and the status
that KSeF returns for that reference.

```text
authenticated client
  -> open online or batch session
    -> session reference number
      -> send/upload encrypted invoice data
        -> status, invoice results, UPO
```

## Session families

KSeF has several session-like surfaces. They answer different questions and
live on different SDK branches.

| Session family | SDK branch | What it represents |
| --- | --- | --- |
| Online invoice session | `auth.online_session()` | A short-lived interactive workflow for sending one or a few invoices. |
| Batch invoice session | `auth.batch_session()` or `auth.batch` | A workflow for uploading an encrypted ZIP package split into parts. |
| Authentication session | `auth.sessions` | Active bearer-token sessions created by authentication. |
| Invoice session history | `auth.invoice_sessions` | Historical online and batch invoice sessions that can be queried after the original process exits. |

The first two are invoice-sending workflows. Authentication sessions and invoice
session history are inspection/administration surfaces.

## Online sessions

An online session is the interactive sending path. It is opened for a form
schema such as `FormSchema.FA3`, then invoices are sent one at a time into that
session.

Opening the session is lightweight. The SDK loads the public KSeF encryption
certificate, creates session encryption material, opens the remote session, and
returns an `OnlineSessionClient` bound to the returned `reference_number`.

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    state = session.resume_state()
    print(state.reference_number, state.valid_until)
```

Use the online session client for calls that are scoped to invoices sent in that
session: sending, listing session invoices, checking one session invoice, and
fetching invoice UPO by invoice reference or KSeF number.

The context manager calls `close()` when the block exits. Closing an online
session tells KSeF that no more invoices will be sent and allows collective UPO
generation for the session.

:::tip[Persist before the process boundary]
Store the session reference and invoice reference numbers before long polling,
queue handoff, or process exit. The Python object is replaceable; the KSeF
references are what let another worker resume inspection.
:::

## Resume a session

`online_session()` and `batch_session()` start a session or resume one, with the
same method. Pass exactly one form: `form_code=` (or `prepared_batch=` /
`batch_file=`) to open, or `state=` to resume. `state=` takes the resume-state
object or its JSON string, and everything (form code, keys, expiry, upload
requests) comes from the state.

```python
with auth.online_session(form_code=FormSchema.FA3) as session:
    saved = session.resume_state().to_json()      # store as a credential
    reference = session.send_invoice(xml).reference_number

# later, possibly in another process
with auth.online_session(state=saved) as session:
    status = session.submission(reference).wait()  # handle for an earlier invoice
```

Leaving the `with` block closes the session in both cases. Closing a session
that is already closed is a no-op: a resumed client first asks KSeF, so it never
sends a second close request. Batch sessions work the same way with
`auth.batch_session(state=saved)`, then `session.wait()` and `session.download_upo()`.
Both `resume_online_session()` and `resume_batch_session()` are deprecated
aliases. Session state holds encryption keys: never log it.

Resumed session handles, `invoices.export(state=...)` jobs and the rest of the
authenticated client share one transport, so they all use the client's current
access token and refresh it as needed (see
[Access tokens refresh themselves](authentication-methods.md#access-tokens-refresh-themselves)).
A resumed client whose access token has expired still works while its refresh
token is valid. If the refresh token has expired too, the call raises
`KSeFAuthenticationExpiredError`: authenticate again, then resume the session
from its saved state.

## Batch sessions

A batch session is the bulk sending path. The unit sent to KSeF is not one XML
file. It is a prepared ZIP package that contains invoice XML files, split into
parts and encrypted before upload.

The high-level `auth.batch` service owns the normal workflow:

1. Build a ZIP package from invoice XML files or in-memory invoice bytes.

2. Split the package into parts before encryption.

3. Encrypt each part and calculate metadata for the package and parts.

4. Open a batch session and receive upload instructions.

5. Upload all parts, close the session, then poll status.

```python
prepared = auth.batch.prepare([Path("invoice-1.xml"), Path("invoice-2.xml")])

session = auth.batch.submit(prepared)
print(session.reference_number)
```

For batch workflows, keep the mapping between local source files and the
prepared invoice metadata. KSeF reports per-invoice batch results through
session invoice fields such as `invoice_hash`, `invoice_file_name`,
`reference_number`, and eventually `ksef_number`.

## State, status, and history

These three concepts are easy to mix up:

| Concept | Meaning | SDK shape |
| --- | --- | --- |
| State | Local data needed to resume a session handle. It includes sensitive session encryption material and, for batch, upload URLs. | `OnlineSessionResumeState`, `BatchSessionResumeState` |
| Status | KSeF's current view of the remote workflow. This is what tells you whether processing succeeded, failed, or is still running. | `SessionStatusResponse`, `SessionInvoiceStatusResponse` |
| History | Queryable list of previous online or batch sessions. Use it when you no longer have the original local object. | `auth.invoice_sessions` |

Session state is useful for resuming SDK operations, but it is sensitive. Do not
print it or store it in logs. Status and history responses are the safe objects
to persist for audit and support.

```python
status = session.get_status()
print(
    status.status.code,
    status.invoice_count,
    status.successful_invoice_count,
    status.failed_invoice_count,
)
```

## What to store

At minimum, store:

- session reference number;
- invoice reference number returned after sending;
- KSeF number after acceptance;
- invoice hash or file name for batch correlation;
- UPO reference or downloaded UPO bytes when available;
- local correlation id from your own system.

The KSeF session can outlive the Python process that opened it. A durable record
of those identifiers is what makes retries, later UPO download, and support
investigation possible.

## Related pages

- [Send invoices](../how-to-guides/send-invoices.md): Open online or batch sessions and submit invoice XML.
- [Get status and UPO](../how-to-guides/get-status-and-upo.md): Poll session and invoice status, then download UPO documents.
- [Invoice lifecycle](invoice-lifecycle.md): Follow an invoice from XML submission to KSeF number, metadata, download, and UPO.
- [Low-level sessions and invoices](../reference/low-level/sessions-invoices.md): Inspect the underlying low-level session and invoice endpoints.

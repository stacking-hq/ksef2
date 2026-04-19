# KSeF SDK Documentation

This directory contains the maintained human-facing documentation for the current `ksef2` public API.

## Guides

| Area | What it covers |
|------|----------------|
| [Authentication](guides/authentication.md) | XAdES auth, KSeF token auth, refresh, auth-session management |
| [Async Client](guides/async-client.md) | Async authentication, sessions, invoice exports, batch work, pagination, and testdata |
| [Encryption](guides/encryption.md) | Public KSeF encryption certificates used for token and session encryption |
| [Invoices](guides/invoices.md) | Sending invoices, session invoice status, metadata queries, exports, downloads |
| [FA(3) Builder](guides/fa3-builder.md) | Building typed FA(3) invoices and rendering XML through `ksef2.fa3` |
| [Sessions](guides/sessions.md) | Online session lifecycle, session resume, invoice session history |
| [Tokens](guides/tokens.md) | Generating, listing, checking, and revoking KSeF tokens |
| [Permissions](guides/permissions.md) | Grant, revoke, query, and operation-status flows |
| [Certificates](guides/certificates.md) | Limits, enrollment, query, retrieval, and revocation |
| [Limits](guides/limits.md) | Querying and modifying TEST-environment limits |
| [PEPPOL](guides/peppol.md) | Querying the public PEPPOL provider registry |
| [Test Data](guides/testdata.md) | TEST-environment subjects, people, permissions, attachments, and blocked contexts |

## Example Scripts

Runnable examples live in [`scripts/examples`](../scripts/examples).
Run them as modules with `uv run -m ...`; direct execution by file path is not supported.
The guide pages above link to the most relevant scripts for each area.
The structure and conventions for maintaining them are documented in
[`scripts/examples/README.md`](../scripts/examples/README.md).

Good starting points:

- [`scripts/examples/quickstart.py`](../scripts/examples/quickstart.py)
- [`scripts/examples/invoices/build_fa3_invoice.py`](../scripts/examples/invoices/build_fa3_invoice.py)
- [`scripts/examples/invoices/send_batch.py`](../scripts/examples/invoices/send_batch.py)
- [`scripts/examples/invoices/submit_batch.py`](../scripts/examples/invoices/submit_batch.py)
- [`scripts/examples/invoices/send_query_export_download.py`](../scripts/examples/invoices/send_query_export_download.py)
- [`scripts/examples/peppol/query_providers.py`](../scripts/examples/peppol/query_providers.py)
- [`scripts/examples/scenarios/session_workflow.py`](../scripts/examples/scenarios/session_workflow.py)

## Reference Material

- [KSeF API docs](https://api-test.ksef.mf.gov.pl/docs/v2)
- [Project changelog](../CHANGELOG.md)

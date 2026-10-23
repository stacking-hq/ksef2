---
title: Public API Contract
description: Stable import paths and internal boundaries for ksef2 1.0.
---

Use the documented import paths on this page when building application code.
They are the paths intended to remain stable through the 1.x line.

## Stable application imports

| Import path | Use it for |
| --- | --- |
| `ksef2` | Root clients, environment and transport config, `FormSchema`, `__version__`, and public exceptions. |
| `ksef2.clients` | Concrete sync/async clients, the stable `InvoicesService` / `BatchService` workflow types, and the handle, paging and export result types (`InvoiceSubmission`, `ExportJob`, `GeneratedToken`, `PermissionOperation`, `CertificateEnrollment`, `ExportedInvoices`, `Pager`, `OperationHandle`), plus async twins, for type annotations. |
| `ksef2.models` | SDK request, response, filter, pagination (including `Page`), token, permission, session, batch, export and resume-state (`ExportResumeState`, `GeneratedTokenResumeState`, `CertificateEnrollmentResumeState`, `PermissionOperationResumeState`, `InvoiceSubmissionResumeState`) models, plus the XAdES credential holder (`XAdESCredentials`). |
| `ksef2.fa3` | FA(3) invoice builder, draft snapshots, and public FA(3) domain models used by builder workflows. |
| `ksef2.xades` | Certificate loading, TEST certificate generation, local XAdES signing helpers, `LocalSigner`, and the `XAdESCredentials` holder accepted by `with_xades()`. |
| `ksef2.testdata` | TEST-only helpers that generate valid NIP and PESEL numbers (`generate_nip`, `generate_pesel`). |
| `ksef2.profiles` | Local `ksef2-cli` compatible profile config helpers. |
| `ksef2.renderers` | Optional local XSLT/PDF invoice rendering helpers. |
| `ksef2.raw` | Low-level endpoint clients, schema-native `spec` and `supp` models, and low-level crypto helpers. |
| `ksef2.raw.mappers` | Public mappers for crossing between raw schema models and SDK models. |

Prefer the highest-level import that fits the workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.fa3 import InvoiceBuilder, KsefInvoiceDraft, VatRate
from ksef2.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.renderers import InvoicePDFExporter, InvoiceXSLTRenderer
from ksef2.xades import XAdESCredentials, load_certificate_from_pem
```

## Root package exports

The root `ksef2` package is the public facade for common application code:

- `Client`, `AsyncClient`;
- `Environment`, `TransportConfig`, `TimeoutConfig`, `RetryConfig`,
  `TlsConfig`, `ConnectionPoolConfig`;
- `FormSchema`;
- `ExceptionCode` and all public `KSeF*` exception classes;
- `__version__`.

Use root imports for these names instead of reaching into implementation
modules.

## Low-level API stability

`ksef2.raw` is public, but intentionally lower level. Its import path is stable;
its schema-native model shapes follow the checked KSeF OpenAPI version.

```python
from ksef2.raw import spec
from ksef2.raw.mappers import auth as auth_mapper
```

Do not import generated OpenAPI models from the SDK's private schema package.
Use `ksef2.raw.spec` and `ksef2.raw.supp` so application code stays on the
supported surface.

## Private paths

The rule is simple: **a module path with no underscore is public; anything with
an underscore is private.** `ksef2._core`, `ksef2._clients.base` and
`ksef2.raw._facade` are private, and so is every module below them.

Private modules can change without a major release. The former `core`, `domain`,
`infra` and `services` paths remain as deprecated aliases throughout 1.x.
They warn once per package family with replacement paths and reuse canonical
modules and classes. Removal may happen no earlier than 2.0.0.

See the [1.0 migration guide](migration-1-0.md) for before/after examples.

`scripts/*` is repository tooling, not package API.

## Secrets and serialization

Models that carry secrets or signed URLs (access and refresh tokens, AES keys
and IVs, presigned download and upload URLs, one-time tokens) redact them in
`model_dump()`, `model_dump_json()` and `repr()`. These methods are for
logging and display. They are **not a persistence format**: the redacted output
cannot be loaded back, and validating it can fail. For example,
`UpoPage.model_validate(page.model_dump())` raises because `download_url` is
excluded from the dump but required by the model.

Persist and restore state with the explicit methods instead:

- `to_dict()` and `to_json()` on the resume-state models
  (`AuthenticationResumeState`, `OnlineSessionResumeState`,
  `BatchSessionResumeState`) export credentials in full; restore them with
  `from_dict()` or `from_json()`.
- `to_sensitive_dict()` on secret-bearing response models such as `UpoPage`,
  `GenerateTokenResponse` and `ExportHandle` exports the secret fields for
  deliberate, protected handling.
- `to_sensitive_dict()` and `to_sensitive_json()` on `PreparedBatch` export the
  encrypted parts and AES material in full for protected storage. Restore the
  batch with `PreparedBatch.from_sensitive_dict()` or `from_sensitive_json()` and pass
  it with the saved session state to recover an upload after a restart. Generic
  dumps and repr keep the payload and keys hidden.

`XAdESCredentials` holds loaded cryptography certificate and private-key objects
exposed through `certificate` and `private_key`. It retains no password or input
bytes, hides both objects in `repr()`, and has no Pydantic schema or JSON
serialization API.

Treat anything produced by these methods as a credential: store it encrypted,
never log it, and never commit it.

Persist completed invoice exports as plain `ExportedInvoices.archive` bytes.
Restore with `ExportedInvoices.from_archive(archive, compression="zip")`, or use
`compression="tar_gz"` for TarGz. Metadata is read lazily from the archive;
package status and download URLs are not restored. Protect the decrypted invoice
data in storage. See [Download invoices](../how-to-guides/download-invoices.md).

## Compatibility rule

Removing or renaming stable SDK imports requires a major version bump.
Deprecated APIs keep working throughout 1.x. Additive APIs can ship in minor
releases. Patch releases preserve documented behavior except for bug fixes.

### KSeF-driven changes

When KSeF removes or changes an endpoint in a way the SDK cannot absorb, the
resulting change may ship in a minor release. It is listed in the changelog
under a "KSeF API changes" heading so it is not mistaken for an SDK decision.
Breaking changes the SDK initiates itself still require a major version bump.

### Deprecation policy

SDK deprecations use PEP 702 `@deprecated`, or an import warning for module
aliases, and name the replacement. Removal is a 2.0 decision, not a scheduled
1.x change. The warning says "will be removed no earlier than ksef2 2.0.0";
this is a minimum version, not a promise to remove the API in 2.0.

## Deprecated APIs

These APIs still work throughout 1.x. Each one emits a `DeprecationWarning`
once per call, is marked with PEP 702 `@deprecated` so type checkers and IDEs
flag call sites, and may be removed no earlier than ksef2 2.0.0. Python hides `DeprecationWarning`
outside `__main__` and test runners, so run your tests with
`python -W error::DeprecationWarning` to find them.

| Deprecated | Use instead | Removed in |
| --- | --- | --- |
| `Client.authenticated(tokens)` and `AsyncClient.authenticated(tokens)` | `client.authentication.resume(AuthenticationResumeState.from_tokens(tokens))` | 2.0.0 or later |
| `get_state()` on online and batch session clients | `resume_state()` | 2.0.0 or later |
| `BatchSessionClient.access_token` | `AuthenticatedClient.access_token` of the parent client | 2.0.0 or later |
| `dump_state()` on session resume state | `to_dict()` | 2.0.0 or later |
| `model_dump_sensitive()` on session resume state | `to_dict()` | 2.0.0 or later |
| `model_dump_sensitive_json()` on session resume state | `to_json()` | 2.0.0 or later |
| `from_state()` on session resume state | `from_dict()` | 2.0.0 or later |
| `BaseSessionState`, `OnlineSessionState`, `BatchSessionState` | `BaseSessionResumeState`, `OnlineSessionResumeState`, `BatchSessionResumeState` | 2.0.0 or later |
| `access_token=` argument of `from_encoded()` on session resume state (ignored) | Persist `AuthenticationResumeState` separately | 2.0.0 or later |
| `access_token` key in stored session resume state (ignored; old files still load) | Persist `AuthenticationResumeState` separately | 2.0.0 or later |
| `auth_timeout` key in a profile written by ksef2-cli 0.0.2 | `max_poll_attempts` (and optionally `poll_interval`) | 2.0.0 or later |
| `send_invoice_and_wait()` and `wait_for_invoice_ready()` on the online session | `send_invoice(...).wait()` | 2.0.0 or later |
| `get_invoice_upo_by_ksef_number()` and `get_invoice_upo_by_reference()` on the online session | `download_invoice_upo(ksef_number=...)` or `download_invoice_upo(reference_number=...)` | 2.0.0 or later |
| `BatchSessionClient.get_upo(upo_reference_number=...)` | `download_upo()` | 2.0.0 or later |
| `auth.batch.prepare_batch()` and `prepare_batch_from_paths()` | `auth.batch.prepare()` | 2.0.0 or later |
| `auth.batch.submit_batch()`, `submit_prepared_batch()` and `open_session()` | `auth.batch.submit()` or `auth.batch_session(...)` | 2.0.0 or later |
| `auth.batch.get_status()`, `list_invoices()`, `list_failed_invoices()`, `get_upo()` and `wait_for_completion()` (with `session=`) | The same operations on the session client, with `wait()` and `download_upo()` | 2.0.0 or later |
| `auth.open_batch_session(aes_key=..., iv=..., ...)` | `auth.raw` | 2.0.0 or later |
| `auth.resume_online_session(state)` and `auth.resume_batch_session(state)` | `auth.online_session(state=...)` and `auth.batch_session(state=...)` | 2.0.0 or later |
| `auth.invoices.query_metadata()`, `query_metadata_pages()`, `all_metadata()` and `wait_for_invoices()` | `auth.invoices.search(...)` with `.responses()`, `.first_response()`, `.pages()`, `.first_page()` and `.wait()` | 2.0.0 or later |
| `auth.invoices.download_invoice()` and `wait_for_invoice_download()` | `auth.invoices.download(...)` | 2.0.0 or later |
| `auth.invoices.schedule_export()`, `get_export_status()`, `wait_for_export_package()`, `fetch_package()`, `fetch_package_bytes()` and `export_and_download()` | `auth.invoices.export(...)`, then `ExportJob.wait()` | 2.0.0 or later |
| `auth.tokens.wait_for_activation(reference_number=...)` | `auth.tokens.generate(...).wait()` | 2.0.0 or later |
| `auth.tokens.status()` | `auth.tokens.get_status()` | 2.0.0 or later |
| `auth.tokens.list_all()` | `auth.tokens.list(...)` with `.pages()` and `.first_page()` | 2.0.0 or later |
| `auth.certificates.query()` and `all()` | `auth.certificates.list(...)` | 2.0.0 or later |
| `client.peppol.query()` and `all()` | `client.peppol.list(...)` | 2.0.0 or later |
| `auth.sessions.query()` and `all()` | `auth.sessions.list(...)` | 2.0.0 or later |
| `auth.sessions.close(reference_number=...)` | `auth.sessions.terminate(reference_number)` | 2.0.0 or later |
| `auth.invoice_sessions.query()` and `all()` | `auth.invoice_sessions.list(session_type, ...)` | 2.0.0 or later |
| `auth.collective_identifiers.query()` and `query_all()` | `auth.collective_identifiers.list(filters)` | 2.0.0 or later |
| `auth.collective_identifiers.query_by_ksef_number()` and `query_all_by_ksef_number()` | `auth.collective_identifiers.list_for_invoice(ksef_number)` | 2.0.0 or later |
| `auth.collective_identifiers.list_all_invoices()` | `auth.collective_identifiers.list_invoices(numbers)` | 2.0.0 or later |
| `auth.permissions.query_persons()`, `query_entities()`, `query_authorizations()`, `query_eu_entities()`, `query_personal()`, `query_subunits()` and `query_subordinate_entities()` | `auth.permissions.list_persons(query)`, `list_entities(query)`, `list_authorizations(query)`, `list_eu_entities(query)`, `list_personal(query)`, `list_subunits(query)` and `list_subordinate_entities(query)` | 2.0.0 or later |
| `auth.permissions.get_entity_roles()` | `auth.permissions.list_entity_roles()` | 2.0.0 or later |
| `auth.permissions.revoke_common()` | `auth.permissions.revoke()` | 2.0.0 or later |
| `InvoicesClient` and `AsyncInvoicesClient` imported from `ksef2.clients` | `auth.invoices` (`InvoicesService`) | 2.0.0 or later |

`session.send_invoice()` keeps its name and accepts the XML positionally as
`bytes` or `str`. It now returns an `InvoiceSubmission` handle that exposes every
field of the old `SendInvoiceResponse`, so code that reads `.reference_number`
keeps working.

The same holds for the other operations KSeF finishes asynchronously:
`tokens.generate()` returns a `GeneratedToken` (read `.token` at once, `.wait()`
for activation), `permissions.grant_*()` and `revoke*()` return a
`PermissionOperation`, and `certificates.enroll()` returns a
`CertificateEnrollment`. Each exposes every field of the response it replaces,
and `get_operation_status()` and `get_enrollment_status()` stay as the data
getters.

`auth.collective_identifiers.list_invoices()` keeps its name but now returns a
`Pager` over the invoices instead of one page, so it is the one name in the table
above whose return type changes. Iterate it, or call `.first_page()` for the old
single request; `list_all_invoices()` still returns pages.

`auth.tokens.list_page()` stays supported and is no longer described as
deprecated: it is the single request that takes KSeF's own continuation token,
and resumable paging does not replace it. Every `Pager`, including the one from
`auth.invoices.search(...)`, answers `.page(cursor)` with a `Page` holding
`items` and the `next_cursor` you store to continue that collection later.

`InvoiceBuilder.dump_state()` and `from_state()` are a separate builder
draft API and are not deprecated.

## Reference

- [Client lifecycle](client-lifecycle.md): Review root clients, authenticated clients, and lifecycle ownership.
- [Low-level API](low-level/overview.md): Use schema-native endpoint wrappers through the supported raw surface.
- [Sync code generation](../contributing/sync-generation.md): Understand how sync clients are generated from async implementations.

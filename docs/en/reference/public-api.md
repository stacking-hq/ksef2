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
| `ksef2.models` | SDK request, response, filter, pagination, token, permission, session, and batch models. |
| `ksef2.fa3` | FA(3) invoice builder, draft snapshots, and public FA(3) domain models used by builder workflows. |
| `ksef2.xades` | Certificate loading, TEST certificate generation, local XAdES signing helpers, and `LocalSigner`. |
| `ksef2.testdata` | TEST-only helpers that generate valid NIP and PESEL numbers (`generate_nip`, `generate_pesel`). |
| `ksef2.profiles` | Local `ksef2-cli` compatible profile config helpers. |
| `ksef2.renderers` | Optional local XSLT/PDF invoice rendering helpers. |
| `ksef2.raw` | Low-level endpoint clients, schema-native `spec` and `supp` models, and low-level crypto helpers. |
| `ksef2.raw.mappers` | Public mappers for crossing between raw schema models and SDK models. |

Prefer the highest-level import that fits the workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoiceDraft, VatRate
from ksef2.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.renderers import InvoicePDFExporter, InvoiceXSLTRenderer
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem
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

Private modules can change or disappear in any release, including patch
releases, and are not part of the compatibility contract. The packages that
earlier pre-release versions exposed without an underscore (`core`, `domain`,
`infra`, `endpoints`, `services`, plus the client implementation modules,
`config` and `logging`) no longer exist under those names; importing them raises
`ImportError`. Import the same names from the public paths above instead, for
example models from `ksef2.models`, clients and workflow service types from
`ksef2.clients`, and configuration and exceptions from `ksef2`.

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

Treat anything produced by these methods as a credential: store it encrypted,
never log it, and never commit it.

## Compatibility rule

After 1.0, changes that remove or rename stable import paths require a major
version bump, with one exception: a deprecated API is removed in the 1.x release
that its deprecation names. Additive APIs can ship in minor releases. Patch
releases should preserve documented imports and behavior except for bug fixes.
Two cases are spelled out below: changes KSeF forces on the SDK, and
SDK-initiated deprecations.

### KSeF-driven changes

When KSeF removes or changes an endpoint in a way the SDK cannot absorb, the
resulting change may ship in a minor release. It is listed in the changelog
under a "KSeF API changes" heading so it is not mistaken for an SDK decision.
Breaking changes the SDK initiates itself still require a major version bump.

### Deprecation policy

Within 1.x, anything the SDK itself wants to retire is deprecated first, in a
minor release: it gets `@deprecated` (or a module-level warning for aliases), a
message of the form "`X` is deprecated and will be removed in ksef2 1.10.0; use
`Y` instead.", and a changelog entry. The message and the
[deprecated APIs](#deprecated-apis) table name the 1.x release that removes the
API, so you can plan the migration. Every deprecation listed today is removed in
**ksef2 1.10.0**; until then each one keeps its old behavior and return type. A
later deprecation names its own 1.x release, never a major version.

## Deprecated APIs

These APIs still work throughout 1.x. Each one emits a `DeprecationWarning`
once per call, is marked with PEP 702 `@deprecated` so type checkers and IDEs
flag call sites, and is removed in ksef2 1.10.0. Python hides `DeprecationWarning`
outside `__main__` and test runners, so run your tests with
`python -W error::DeprecationWarning` to find them.

| Deprecated | Use instead | Removed in |
| --- | --- | --- |
| `Client.authenticated(tokens)` and `AsyncClient.authenticated(tokens)` | `client.authentication.resume(AuthenticationResumeState.from_tokens(tokens))` | 1.10.0 |
| `get_state()` on online and batch session clients | `resume_state()` | 1.10.0 |
| `BatchSessionClient.access_token` | `AuthenticatedClient.access_token` of the parent client | 1.10.0 |
| `dump_state()` on session resume state | `to_dict()` | 1.10.0 |
| `model_dump_sensitive()` on session resume state | `to_dict()` | 1.10.0 |
| `model_dump_sensitive_json()` on session resume state | `to_json()` | 1.10.0 |
| `from_state()` on session resume state | `from_dict()` | 1.10.0 |
| `BaseSessionState`, `OnlineSessionState`, `BatchSessionState` | `BaseSessionResumeState`, `OnlineSessionResumeState`, `BatchSessionResumeState` | 1.10.0 |
| `access_token=` argument of `from_encoded()` on session resume state (ignored) | Persist `AuthenticationResumeState` separately | 1.10.0 |
| `access_token` key in stored session resume state (ignored; old files still load) | Persist `AuthenticationResumeState` separately | 1.10.0 |
| `auth_timeout` key in a profile written by ksef2-cli 0.0.2 | `max_poll_attempts` (and optionally `poll_interval`) | 1.10.0 |
| `send_invoice_and_wait()` and `wait_for_invoice_ready()` on the online session | `send_invoice(...).wait()` | 1.10.0 |
| `get_invoice_upo_by_ksef_number()` and `get_invoice_upo_by_reference()` on the online session | `download_invoice_upo(ksef_number=...)` or `download_invoice_upo(reference_number=...)` | 1.10.0 |
| `BatchSessionClient.get_upo(upo_reference_number=...)` | `download_upo()` | 1.10.0 |
| `auth.batch.prepare_batch()` and `prepare_batch_from_paths()` | `auth.batch.prepare()` | 1.10.0 |
| `auth.batch.submit_batch()`, `submit_prepared_batch()` and `open_session()` | `auth.batch.submit()` or `auth.batch_session(...)` | 1.10.0 |
| `auth.batch.get_status()`, `list_invoices()`, `list_failed_invoices()`, `get_upo()` and `wait_for_completion()` (with `session=`) | The same operations on the session client, with `wait()` and `download_upo()` | 1.10.0 |
| `auth.open_batch_session(aes_key=..., iv=..., ...)` | `auth.raw` | 1.10.0 |
| `auth.invoices.query_metadata()`, `query_metadata_pages()`, `all_metadata()` and `wait_for_invoices()` | `auth.invoices.search(...)` with `.pages()`, `.first_page()` and `.wait()` | 1.10.0 |
| `auth.invoices.download_invoice()` and `wait_for_invoice_download()` | `auth.invoices.download(...)` | 1.10.0 |
| `auth.invoices.schedule_export()`, `get_export_status()`, `wait_for_export_package()`, `fetch_package()`, `fetch_package_bytes()` and `export_and_download()` | `auth.invoices.export(...)`, then `ExportJob.wait()` | 1.10.0 |
| `auth.tokens.wait_for_activation(reference_number=...)` | `auth.tokens.generate(...).wait()` | 1.10.0 |
| `auth.tokens.status()` | `auth.tokens.get_status()` | 1.10.0 |
| `auth.tokens.list_page()` and `list_all()` | `auth.tokens.list(...)` with `.pages()` and `.first_page()` | 1.10.0 |
| `auth.certificates.query()` and `all()` | `auth.certificates.list(...)` | 1.10.0 |
| `client.peppol.query()` and `all()` | `client.peppol.list(...)` | 1.10.0 |
| `auth.sessions.query()` and `all()` | `auth.sessions.list(...)` | 1.10.0 |
| `auth.sessions.close(reference_number=...)` | `auth.sessions.terminate(reference_number)` | 1.10.0 |
| `auth.invoice_sessions.query()` and `all()` | `auth.invoice_sessions.list(session_type, ...)` | 1.10.0 |
| `auth.collective_identifiers.query()` and `query_all()` | `auth.collective_identifiers.list(filters)` | 1.10.0 |
| `auth.collective_identifiers.query_by_ksef_number()` and `query_all_by_ksef_number()` | `auth.collective_identifiers.list_for_invoice(ksef_number)` | 1.10.0 |
| `auth.collective_identifiers.list_all_invoices()` | `auth.collective_identifiers.list_invoices(numbers)` | 1.10.0 |
| `auth.permissions.query_persons()`, `query_entities()`, `query_authorizations()`, `query_eu_entities()`, `query_personal()`, `query_subunits()` and `query_subordinate_entities()` | `auth.permissions.list_persons(query)`, `list_entities(query)`, `list_authorizations(query)`, `list_eu_entities(query)`, `list_personal(query)`, `list_subunits(query)` and `list_subordinate_entities(query)` | 1.10.0 |
| `auth.permissions.get_entity_roles()` | `auth.permissions.list_entity_roles()` | 1.10.0 |
| `auth.permissions.revoke_common()` | `auth.permissions.revoke()` | 1.10.0 |
| `InvoicesClient` and `AsyncInvoicesClient` imported from `ksef2.clients` | `auth.invoices` (`InvoicesService`) | 1.10.0 |

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

`FA3InvoiceBuilder.dump_state()` and `from_state()` are a separate builder
draft API and are not deprecated.

## Reference

- [Client lifecycle](client-lifecycle.md): Review root clients, authenticated clients, and lifecycle ownership.
- [Low-level API](low-level/overview.md): Use schema-native endpoint wrappers through the supported raw surface.
- [Sync code generation](../contributing/sync-generation.md): Understand how sync clients are generated from async implementations.

## v1.0.0 (2026-10-03)

ksef2 1.0.0 is the first stable release. It targets KSeF OpenAPI 2.8.1 and starts
the 1.x compatibility contract. Since 0.22.2 there are two breaking changes
(internal modules moved to private `_`-prefixed paths, and collective-identifier
invoice queries); nothing else is removed. Read
[Breaking changes](#breaking-changes) and [Deprecated](#deprecated) before upgrading.

### Highlights

- The documented import paths (`ksef2`, `ksef2.clients`, `ksef2.models`,
  `ksef2.fa3`, `ksef2.xades`, `ksef2.profiles`, `ksef2.renderers`, `ksef2.raw`,
  `ksef2.raw.mappers`, and the new `ksef2.testdata`) are the compatibility
  contract for the whole 1.x line. The rule is simple: a module path with no
  underscore is public, and anything with an underscore is private and may change
  in any release. See the
  [public API contract](https://docs.stacking.me/sdk/reference/public-api/)
  and the [1.0.0 release notes](https://docs.stacking.me/sdk/reference/release-notes-1-0-0/).
- `model_dump()` and `model_dump_json()` redact secrets by default and are not a
  persistence format. Use `to_dict()` / `to_json()` / `from_dict()` on resume
  states and `to_sensitive_dict()` to persist.
- The invoice and admin workflows have their final 1.x shape: operations that
  start asynchronous KSeF work return a handle with `.wait()`, every collection
  returns one `Pager`, and access tokens refresh automatically (#162, #163, #165).
  See the [1.0.0 release notes](https://docs.stacking.me/sdk/reference/release-notes-1-0-0/)
  for a before/after.
- KSeF errors come from one pipeline with one message format, carry `ksef_code`,
  `trace_id` and `details`, and say what to do next in `hint` (#167).
- Deprecations are visible to type checkers and IDEs (PEP 702 `@deprecated`) and
  follow one stated policy: a deprecated API is removed in a named 1.x release.
  Everything deprecated today is removed in **1.10.0**.

### Breaking changes

- **Internal modules moved to private `_`-prefixed paths (#153).** A module path
  with no underscore is public; anything with an underscore is private. Internal
  modules moved to underscore-prefixed paths, with no compatibility aliases, and
  no runtime warning: importing an old path raises `ImportError`. Code that only
  uses the documented public paths is unaffected.

  | Old | New |
  | --- | --- |
  | `ksef2.core` | `ksef2._core` |
  | `ksef2.domain` | `ksef2._domain` |
  | `ksef2.infra` | `ksef2._infra` |
  | `ksef2.endpoints` | `ksef2._endpoints` |
  | `ksef2.services` | `ksef2._services` |
  | `ksef2.clients.<module>` (`base`, `auth`, `online`, `async_*`, ...) | `ksef2._clients.<module>` (`ksef2.clients` stays the public facade with the same `__all__`) |
  | `ksef2.config` | `ksef2._config` (names stay exported from `ksef2`) |
  | `ksef2.logging` | `ksef2._logging` (names stay exported from `ksef2`) |
  | `ksef2.raw.facade`, `ksef2.raw.async_facade` | `ksef2.raw._facade`, `ksef2.raw._async_facade` (names stay exported from `ksef2.raw`) |

  If you imported something from an old path, import it from the public module
  instead (see [Added](#added) for names newly exported from `ksef2.models`).

- **Collective-identifier invoice queries (#128).** KSeF API 2.8.1 replaced
  `GET /collective-identifiers/{collectiveIdentifierNumber}/invoices` with
  `POST /collective-identifiers/invoices`, which takes up to 10 identifiers in
  the body. The old call is removed, not deprecated. Migration is mechanical:

  ```python
  # before (0.22.x)
  page = auth.collective_identifiers.list_invoices(collective_identifier_number=cid)
  everything = auth.collective_identifiers.list_all_invoices(
      collective_identifier_number=cid
  )

  # after (1.0.0)
  for invoice in auth.collective_identifiers.list_invoices(
      collective_identifier_numbers=[cid]
  ):
      ...
  ```

  `list_invoices` now returns a `Pager` (iterate items, `.pages()`, `.first_page()`)
  and no longer takes `continuation_token`; `list_all_invoices` remains as a
  deprecated alias that still returns pages (#163). The high-level client
  validates 1 to 10 identifiers before sending. The raw
  endpoint takes a request body instead of a path parameter:

  ```python
  from ksef2.raw import spec

  # before (0.22.x)
  auth.raw.collective_identifiers.list_invoices(cid)

  # after (1.0.0)
  auth.raw.collective_identifiers.list_invoices(
      spec.CollectiveIdentifierInvoicesQueryRequest(collectiveIdentifierNumbers=[cid])
  )
  ```

### Deprecated

Every replaced name stays as a `@deprecated` alias that keeps its old behavior and
return type, warns once per call, and is removed in **ksef2 1.10.0**. That
includes the seven APIs deprecated in 0.19.0, whose removal moves from 2.0 to
1.10.0. See the
[deprecated APIs table](https://docs.stacking.me/sdk/reference/public-api/#deprecated-apis)
on the public API page for every alias and its replacement.

- The invoice, batch and export workflows (#162): `send_invoice_and_wait`,
  `wait_for_invoice_ready`, the `auth.batch.*` `prepare_batch` / `submit_batch` /
  `wait_for_completion` family, `query_metadata` / `all_metadata` /
  `wait_for_invoices`, `download_invoice`, `schedule_export` /
  `wait_for_export_package` / `fetch_package` and related names.
  `auth.resume_online_session()` and `auth.resume_batch_session()` give way to
  `online_session(state=...)` and `batch_session(state=...)`.
- The token, certificate, PEPPOL, session, collective-identifier and permission
  `query` / `all` / `list_page` / `query_*` methods give way to `list()` /
  `list_*()` (#163).
- `InvoicesClient` and `AsyncInvoicesClient` imported from `ksef2.clients`; use
  `auth.invoices` (#163).
- The 0.19.0 deprecations (`Client.authenticated()`, `get_state()`,
  `*SessionState` aliases, `dump_state()` / `model_dump_sensitive()` /
  `from_state()`, `BatchSessionClient.access_token`, `from_encoded(access_token=...)`,
  the stored `access_token` key) and the legacy `auth_timeout` profile key
  (#150, #162).

### Added

- Handles with `.wait()` for operations KSeF finishes asynchronously, each exposing
  the fields of the response it replaces: `InvoiceSubmission` from
  `session.send_invoice(xml)` (also `get_status()`, `download_upo()`), `ExportJob`,
  `GeneratedToken` from `tokens.generate()`, `PermissionOperation` from
  `permissions.grant_*()` / `revoke()`, `CertificateEnrollment` from
  `certificates.enroll()`, and the generic `OperationHandle` (#162, #163).
- `auth.invoices.search(filters)`, returning a `Pager`; `auth.invoices.download(ksef_number)`;
  and `auth.invoices.export(filters)`, whose `ExportJob.wait()` returns
  `ExportedInvoices` (`.invoices()`, `.metadata`, `.archive`, `.save()`) (#162).
- `auth.batch.prepare()` and `auth.batch.submit()`, which opens, uploads and closes
  the batch and returns the closed `BatchSessionClient` (#162).
- One `Pager` for every collection (tokens, certificates, PEPPOL, sessions,
  collective identifiers and all `permissions.list_*()`): iterate items, `.pages()`,
  `.first_page()` (#162, #163).
- Resume through the method that starts the work, with `state=` (the resume-state
  object or its JSON): `auth.online_session(state=...)`,
  `auth.batch_session(state=...)`, `auth.invoices.export(state=...)`. Exports are
  resumable through `ExportJob.resume_state()` and the new `ExportResumeState`, and
  `session.submission(reference_number)` returns the handle for an invoice sent
  earlier (#162).
- Automatic access-token refresh: shortly before expiry and once after a 401, shared
  by concurrent requests. Disable with `TransportConfig(auto_refresh_tokens=False)`
  (#165).
- New exceptions: `KSeFArgumentError`, `KSeFAuthenticationExpiredError`,
  `KSeFExportFailedError`, `KSeFOnlineSessionTimeoutError`,
  `KSeFPermissionOperationFailedError`, `KSeFPermissionOperationTimeoutError`,
  `KSeFCertificateEnrollmentFailedError` and
  `KSeFCertificateEnrollmentTimeoutError` (#162, #163, #165).
- `tokens.get_status()`, `sessions.terminate(reference_number)` and
  `permissions.revoke()` (#163).
- `KSeFApiError.ksef_code` (the raw KSeF code, also for codes the SDK does not
  list), `trace_id` and `details`; `KSeFException.hint`, which says what to do next;
  and `KSeFNotReadyError` for KSeF codes 21165 and 21178 (#167).
- `timeout` and `poll_interval` on `download_upo()` (#167).
- `Retry-After` is read in its HTTP-date form as well as in seconds, in errors and
  in the retry middleware (#167).
- `ksef2.testdata` with `generate_nip()` and `generate_pesel()` for TEST-environment
  data (#148).
- `CertUsageEnum` is exported from `ksef2.models` (#148).
- 21 new `ksef2.models` exports, so code that imported them from internal paths has
  a public home (#153): `ContextIdentifierTypeEnum`, `CertificateStatusEnum`,
  `CertificateTypeEnum`, `RevocationReasonEnum`,
  `validate_certificate_serial_number`, `AuthorizationPermissionTypeEnum`,
  `AuthorizationSubjectIdentifierTypeEnum`, `EntityPermissionTypeEnum`,
  `EuEntityAdminContextIdentifierTypeEnum`, `EuEntityPermissionTypeEnum`,
  `IndirectPermissionTypeEnum`, `IndirectTargetIdentifierTypeEnum`,
  `SubunitIdentifierTypeEnum`, `AuthContextIdentifierTypeEnum`,
  `IdentifierTypeEnum` (the TEST-data one: `nip`, `pesel`, `fingerprint`,
  `system`), `PermissionTypeEnum`, `SubjectTypeEnum`,
  `TokenAuthorIdentifierTypeEnum`, `TokenPermissionEnum`, `TokenStatusEnum` and
  `CurrencyCodes`.
- Python 3.14 support: tested in CI and smoke-tested on the built wheel on 3.12,
  3.13 and 3.14 (#146).
- PyPI project URLs and classifiers, including
  `Development Status :: 5 - Production/Stable` (#146).
- `ProfileConfig` accepts the flat `auth_timeout` key written by ksef2-cli 0.0.2,
  maps it to `max_poll_attempts` and warns, instead of silently using the 60-second
  default (#150).
- `typing-extensions` is now a direct dependency, for `@deprecated` (#150).

### Changed

- Deprecation policy: a deprecated API is removed in a stated 1.x release, not
  only in the next major. The seven APIs deprecated in 0.19.0 move from 2.0 to
  1.10.0 (#162).
- `session.send_invoice()` keeps its name but now returns an `InvoiceSubmission`
  handle (#162).
- Argument errors from `batch_session()`, `online_session()` and `export()` are
  now `KSeFArgumentError`, which subclasses `KSeFValidationError` (and
  `TypeError`), so existing handlers still catch them (#162).
- `PermissionOperation.wait()` raises `KSeFPermissionOperationFailedError` when
  KSeF rejects a grant, for example with status 440 on TEST (#163).

- API error messages have one format: `KSeF rejected <METHOD path> (HTTP ..., KSeF
  code ...): <description>`, followed by `Details`, `Trace ID` and `Hint` lines. The
  response body is no longer dumped into the message; it stays on `e.response`.
  Messages are for people: branch on the exception class or `ksef_code`, never on
  message text (#167).
- `download_upo()` on a submission, an online session or a batch session waits for
  processing first instead of failing too early (#167).
- `KSeFAuthError.exception_code` now reflects the KSeF code instead of always
  being `UNKNOWN_ERROR` (#167).

### KSeF API

- Targets KSeF OpenAPI 2.8.1; API coverage is 100% of the 83 endpoints in the spec.
- Policy: a breaking change forced by KSeF itself may ship in a minor release under
  a "KSeF API changes" heading. Breaking changes the SDK chooses to make need a
  new major version.

### Fixed

- Give each invoice in the batch examples its own FA(3) number (#135).
- Compare `(method, path)` pairs in the API coverage check and enforce the result,
  so a missing or SDK-only endpoint fails the check (#129).
- Remove the invalid `[project] pythonpath` setting from `pyproject.toml` (#146).

### Build and CI

- Run the invoice workflows against KSeF TEST instead of skipping them (#138), on
  every push to `main`, pull request and dispatch through a new `integration.yml`,
  and in the release path with a check that rejects workflows that never ran (#139).
- Releases no longer dispatch a docs deployment. The ksef2-docs site picks up the
  new release on its daily run or a manual run (#154).
- Smoke-test the built wheel on Python 3.12, 3.13 and 3.14 before publishing, and
  add 3.14 to the CI matrix (#146).
- `scripts/validate_examples.py` rejects examples and documentation code blocks that
  import from a module path with an underscore-prefixed component;
  `scripts/validate_docs_paths.py` and the OpenAPI-version check cover the docs
  pages (#148, #153, #136).
- A module visibility contract test asserts that the public modules import and
  that the old internal paths no longer exist (#153).
- A docstring test and ruff pydocstyle keep every public API documented (#159).
- `scripts/validate_docs_markdown.py` checks the docs Markdown (#158).
- Remove the in-repo CLI script and its integration test; the CLI lives in the
  separate `ksef2-cli` package (#137).

### Docs

- Rewrite the examples and documentation snippets to import from public paths only;
  the one example that needs internals moved to `scripts/advanced_examples/` (#148).
- Document the public API contract, the "Deprecated APIs" table, the secrets and
  serialization rules and the KSeF-driven change policy, in English and Polish
  (#148, #150).
- Correct the 1.0.0 release notes (OpenAPI 2.8.1, collective-identifier surface),
  drop the stale pre-1.0 migration page and add drift gates (#136).
- Document every public API with Google-style docstrings (1428 of 1428 public
  units and 957 of 957 model fields). The docstrings are now the source of the
  generated API reference (#159).
- The SDK docs are plain Markdown instead of MDX (#158).

### Release history note

Two earlier versions never reached PyPI. v0.21.0 was bumped but never tagged; its
changes (OpenAPI 2.8.1) shipped in v0.22.0. The v0.22.1 tag points at a commit whose
project version was still 0.22.0, so the publish run failed its version check; its
fix (#118) shipped in v0.22.2. PyPI goes 0.20.0, 0.22.0, 0.22.2, 1.0.0.

## v0.22.2 (2026-09-25)

## v0.22.1 (2026-09-25)

### Fix

- Preserve invoice rejection details and extensions in `KSeFInvoiceRejectedError` for sync and async clients (#118).

## v0.22.0 (2026-09-25)

### Changed

- Derive `ksef2.__version__` from installed package metadata (#120).

## v0.21.0 (2026-09-24)

### Feat

- update OpenAPI spec to KSeF API 2.8.1 and regenerate models (#113)
- update OpenAPI spec to KSeF API 2.8.0 and regenerate models

## v0.20.0 (2026-09-15)

### Fix

- **limits**: support OpenAPI 2.8 rate limit groups

## v0.19.0 (2026-09-05)

### Feat

- establish documented `ksef2`, `ksef2.clients`, `ksef2.models`, `ksef2.fa3`,
  `ksef2.raw`, `ksef2.xades`, and `ksef2.profiles` compatibility surfaces
- add complete sync and async high-level workflows for authentication, sessions,
  invoices, tokens, permissions, certificates, limits, PEPPOL, and TEST data
- target KSeF OpenAPI 2.7.1 and expose collective-identifier workflows through
  matching sync and async public clients
- add the public FA(3) invoice builder, versioned draft state, and XSD conformance
- return one-time generated tokens before explicit activation polling
- version authentication and session resume-state documents
- store new SDK and CLI profiles under `~/.config/ksef`, while continuing to
  read existing `~/.config/ksef2-cli` profiles as a fallback

### Fix

- prevent automatic retries from consuming one-shot authentication redemption
- isolate presigned storage transfers from KSeF authentication and error middleware
- preserve protected batch recovery state when uploads fail
- redact bearer tokens, encryption material, and signed URLs from default output
- normalize invoice filter datetimes and reject ambiguous or reversed ranges
- reject invalid FA(3) invoice numbers before XML serialization

### Build

- verify release tags against source and wheel metadata before PyPI upload
- run live integration tests against the exact tagged release commit
- gate local FA(3), generated-artifact, coverage, and deprecation contracts

### Docs

- publish the 1.0 public API contract, migration guide, and bilingual workflow
  documentation

## v0.18.0 (2026-06-21)

### Feat

- **profiles**: add public profile store API
- **auth**: authenticate from ksef2-cli compatible profiles

### Docs

- expand English and Polish SDK profile documentation

## v0.17.1 (2026-06-16)

### Docs

- document public SDK exception contracts and API docstrings

## v0.17.0 (2026-06-04)

### Feat

- **fa3**: support gross unit price lines

## v0.16.0 (2026-05-21)

### Feat

- **api**: support OpenAPI 2.6 compression options

### Fix

- tolerate unknown auth method codes
- make pdf rendering dependencies optional

## v0.15.0 (2026-05-15)

### Feat

- **invoices**: merge metadata pagination helpers
- **invoices**: add metadata pagination helpers

## v0.14.1 (2026-05-13)

### Fix

- **invoices**: wait for invoice download availability

## v0.14.0 (2026-05-09)

### Feat

- **models**: change base model extra from forbid to ignore with warning logging

### Fix

- resolve pyright errors in alias-aware _warn_extra_fields
- **models**: make _warn_extra_fields alias-aware to avoid false warnings

## v0.13.3 (2026-05-08)

### Feat

- **api**: add support for new certificate fields introduced in the 2.5.0 API version update

## v0.13.2 (2026-05-04)

### Fix

- eliminate all beartype warnings
- **fa3**: require country codes for emitted addresses
- **fa3**: allow omitting system info and third-party country code

## v0.13.1 (2026-04-23)

### Fix

- adapt certificate SDK to updated spec

## v0.13.0 (2026-04-20)

### Feat

- **async**: restore _async core support

### Fix

- **async-invoices**: sanitize export part filename before writing

### Refactor

- **async**: consolidate async client implementation
- **builders**: simplify builders __init__ with lazy import via __getattr__
- **mappers**: rewrite permissions query_entity mapper to use spec enum matching
- **mappers**: split encryption response mapper into dedicated functions
- **async**: share client internals

## v0.12.0 (2026-04-17)

### Feat

- handle ProblemDetails (application/problem+json) error responses

### Fix

- preserve ProblemDetails error semantics
- **type**: add type arguments for generic dict container
- correct AllowedIps list constraints from ge/le to max_length

## v0.11.2 (2026-04-09)

### Fix

- **fa3**: avoid beartype JsonDict forward refs

## v0.11.1 (2026-04-09)

### Feat

- **fa3**: annotate builder parameter metadata

## v0.11.0 (2026-04-08)

### Feat

- add public FA3 builder drafts
- rework FA3 builders and invoice mapping
- **new-fa3**: add builder and sample test
- **fa3**: finish correction and advance fields
- **fa3**: model invoice body contexts
- **fa3**: add correction party models
- **fa3**: add transaction conditions mapper
- **fa3**: add payment mappers and brochure tests
- **fa3**: add attachment spec mappers and tests
- refine attachment models and add validation logic
- introduce invoice footer models
- refine header model fields and docstring
- **fa3**: add invoice builder and fa3 body validation
- **fa3**: introduce invoice body model
- **examples**: add fa3 invoice export example
- **fa3**: add invoice models and mappers

### Fix

- clean up basedpyright typing
- stabilize FA3 mapper roundtrips
- restore fa3 builder entrypoint
- **fa3**: correct buyer identifier mapping

### Refactor

- **fa3**: align builder context names
- **fa3**: regenerate schema models as dataclasses

## v0.10.0 (2026-03-19)

### Feat

- **invoices**: add metadata-only exports and invoice schema filtering
- **sessions**: add FA_RR form schema support for session requests

## v0.9.2 (2026-03-14)

### Fix

- **auth**: add support for ksef certificate authentication

## v0.9.1 (2026-03-13)

### Fix

- **auth**: accept ec private keys in with_xades
- update OpenAPI spec refresh workflow

## v0.9.0 (2026-03-07)

### Feat

- **logging**: add package structlog helpers
- add batch upload workflow
- add client lifecycle and transport config
- expand client layer with dedicated modules for all API domains
- reorganize infra mappers into domain-specific modules
- refactor domain models, remove deprecated module
- refactor core infrastructure with middleware support
- refactored certifacets client, mappers and models layers
- refactor the endpoints layer along with comprehensive unit tests, 100% coverage
- move Peppol from services to clients, improve API, add method with internal pagination

### Fix

- **mappers**: handle unsupported authentication method codes
- **permissions**: add entity grants query endpoint
- **logging**: remove duplicate logger imports
- **examples**: remove invalid demo testdata grants
- **auth**: register auth response mapper

### Refactor

- **scripts**: remove obsolete api playground script
- **types**: tighten public literal type surface
- **sdk**: split session clients and refresh release docs
- **cleanup**: remove obsolete docs and legacy request mappers
- reorganize examples and harden xml and session handling
- **examples**: standardize example script execution and layout
- narrow public enum surface
- refresh generated spec and tooling
- consolidate services layer, add InvoicesService
- update scripts and examples for new API
- improve testdata service API and cleanup tracking
- restructure API facade and client layer

## v0.8.0 (2026-02-20)

### Feat

- add pyrightconfig.json file for basedpyright static analysis
- add CLI tool for downloading invoices and exporting to PDF
- add invoice PDF export with XSLT rendering support
- introduce new exception type for timeout errors
- add FA(3) models generated from schemat.xml document
- add invoice renderers for CSV and HTML output
- add FA3 domain models and invoice mappers
- add FA3 schema models and code generation

## v0.7.1 (2026-02-18)

### Feat

- add example for bulk purchase invoice download across multiple entities
- add certificate loading helpers and DEMO/PROD XAdES docs

### Fix

- resolve bugs discovered by e2e example tests
- limit export date range to 90 days (KSeF max 3 months per request)

## v0.7.0 (2026-02-17)

### BREAKING CHANGE

- Services now receive access_token in constructor
- PermissionsService, CertificateService, TokenService, LimitsService refactored
- Remove permissions from OnlineSessionClient (now on AuthenticatedClient)
- Consistent API pattern: client.auth.* for authenticated operations

### Feat

- add AuthenticatedClient with consolidated authenticated operations
- complete 100% API coverage with Peppol, batch sessions, and session UPO endpoints
- add certificates endpoints (7 endpoints)
- add list tokens endpoint (GET /tokens)

### Refactor

- services store access_token internally, remove per-method token params

## v0.6.3 (2026-02-17)

### Feat

- add testdata endpoints (block/unblock context, revoke attachments, production rate limits)

## v0.6.2 (2026-02-16)

## v0.6.1 (2026-02-16)

### Fix

- resolve type issues in permissions spec imports and bump version to 0.6.1

## v0.6.0 (2026-02-16)

### Feat

- add permissions endpoints, docs, and bump version to 0.6.0

## v0.5.0 (2026-02-16)

### Feat

- add invoice query, export, and download endpoints

## v0.4.0 (2026-02-16)

### Feat

- update example scripts and add session workflow
- add invoice status, UPO endpoints, and session query support
- add UPO_NOT_FOUND and NOT_PROCESSED_YET exception codes

### Fix

- replace session token header with bearer authentication
- prevent double base64 encoding of encrypted token in auth

## v0.1.2 (2026-02-15)

### Feat

- add OpenAPI version tracking and supplemental schemas
- add example scripts and utilities
- add exception codes and improve error handling

## v0.2.0 (2026-02-14)

### Fix

- correct API URL paths and token authentication

## v0.1.1 (2026-02-14)

### Fix

- **types**: resolve all 22 basedpyright errors
- **types**: use Middleware protocol instead of concrete KSeFProtocol

### Refactor

- **models**: remove unused deprecated model re-exports and clean up imports

## v0.1.0 (2026-02-14)

### Feat

- update services / add context managed cleanup for test data service
- update mappers
- inject middleware that maps error responses into SDK exceptions
- add endpoints registry and fix some typos in urls and used http methods
- calculate coverage info based on openapi.json spec and implemented endpoints
- add API coverage badge
- add remaining SDK modules, config, codecs, and lock file
- add auth service with token and XAdES authentication
- add XAdES authentication, token management, and testdata client
- implement KSeF SDK with auth, sessions, and invoice sending

### Fix

- **ci**: ignore non-zero exit from coverage script
- add build-system to pyproject.toml so package is installable
- **ci**: add missing Python install step in coverage workflow
- align unit tests with updated API schema and architecture
- register testdata endpoints and fix endpoint URL
- use hex color values for coverage badge compatibility
- use master branch in coverage badge URL
- update API coverage badge URL to match current repo
- add overloads to http post/request for correct return types

### Refactor

- simplify limits API with fetch-modify-post workflow
- replace url properties with class fields in all endpoints
- rename package
- move legacy clients, models, and mappers to _deprecated
- remove obsolete modules superseded by new architecture

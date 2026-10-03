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
  [public API contract](https://docs.stacking.me/ksef2/sdk/reference/public-api/)
  and the [1.0.0 release notes](https://docs.stacking.me/ksef2/sdk/reference/release-notes-1-0-0/).
- `model_dump()` and `model_dump_json()` redact secrets by default and are not a
  persistence format. Use `to_dict()` / `to_json()` / `from_dict()` on resume
  states and `to_sensitive_dict()` to persist.
- Deprecations are now visible to type checkers and IDEs (PEP 702 `@deprecated`),
  with one stated policy: deprecate in a minor release with `@deprecated` and a
  changelog entry, remove only in the next major.

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
  page = auth.collective_identifiers.list_invoices(collective_identifier_numbers=[cid])
  everything = auth.collective_identifiers.list_all_invoices(
      collective_identifier_numbers=[cid]
  )
  ```

  The high-level client validates 1 to 10 identifiers before sending. The raw
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

Deprecated APIs stay through 1.x and are removed in ksef2 2.0. Each warns once
per call and is flagged by type checkers (PEP 702).

| Deprecated | Use instead |
| --- | --- |
| `Client.authenticated(tokens)`, `AsyncClient.authenticated(tokens)` | `client.authentication.resume(AuthenticationResumeState.from_tokens(tokens))` |
| `get_state()` on online and batch session clients | `resume_state()` |
| `BatchSessionClient.access_token` | `AuthenticatedClient.access_token` of the parent client |
| `dump_state()`, `model_dump_sensitive()` on session resume state | `to_dict()` |
| `model_dump_sensitive_json()` | `to_json()` |
| `from_state()` | `from_dict()` |
| `BaseSessionState`, `OnlineSessionState`, `BatchSessionState` | `BaseSessionResumeState`, `OnlineSessionResumeState`, `BatchSessionResumeState` |
| `access_token=` argument of `from_encoded()` and the `access_token` key in stored resume state (ignored; old files still load) | Persist `AuthenticationResumeState` separately |
| `auth_timeout` in a profile written by ksef2-cli 0.0.2 (now mapped to `max_poll_attempts`) | `max_poll_attempts` and optionally `poll_interval` |

### Added

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
- Fail a release before upload when `DOCS_DISPATCH_TOKEN` is missing, and fail
  instead of silently skipping the docs dispatch (#146).
- Smoke-test the built wheel on Python 3.12, 3.13 and 3.14 before publishing, and
  add 3.14 to the CI matrix (#146).
- `scripts/validate_examples.py` rejects examples and documentation code blocks that
  import from a module path with an underscore-prefixed component;
  `scripts/validate_docs_paths.py` and the OpenAPI-version check cover the docs
  pages (#148, #153, #136).
- A module visibility contract test asserts that the public modules import and
  that the old internal paths no longer exist (#153).
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

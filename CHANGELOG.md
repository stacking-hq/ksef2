## v0.19.0 (2026-06-23)

### Feat

- expose the low-level `ksef2.raw` endpoint API and public raw mappers
- add the public `ksef2.xades` facade for certificate and XAdES helpers

### Docs

- sync README OpenAPI target version with KSeF API 2.6.1
- document the low-level API, public API contract, error handling, and sync code generation

### Refactor

- remove the FA(3) invoice builder and legacy generated sample-invoice helpers

### Build

- run `just release-check` in CI and the PyPI publish workflow

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

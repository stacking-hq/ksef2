---
title: Overview
description: Start here for the KSeF2 Python SDK documentation.
---

KSeF2 is a Python SDK for Poland's KSeF v2 API. It provides typed sync and
async clients for authentication, invoice sessions, metadata queries, exports,
permissions, KSeF tokens, certificates, PEPPOL, TEST data, and FA(3) invoice
building.

> **Unofficial SDK.** KSeF2 is a community-maintained Python SDK. It is not
> published, endorsed, or supported by Poland's Ministry of Finance. Use the
> official KSeF documentation as the authority for API behavior.

## Start here

- [Install the SDK](getting-started/installation.md)
- [Run the quickstart](getting-started/quickstart.md)
- [Choose an authentication flow](getting-started/authentication.md)

## Documentation map

The documentation is organized around four kinds of work:

- **Getting started**: install the package, choose an authentication flow, and
  complete a first TEST workflow.
- **How-to guides**: solve concrete tasks such as sending invoices, exporting
  metadata, managing tokens, using TEST helpers, or running the async client.
- **Concepts**: understand design decisions that affect usage, especially the
  async source of truth and generated sync tree.
- **Reference**: inspect the generated public API reference, including
  signatures, stable import paths, referenced models, public exception classes,
  FA(3), and XAdES helpers.

## Reference entry points

- [API reference](reference/api-signatures.md): generated source-derived cards
  grouped by the official KSeF API workflow structure where the SDK maps to it.
- [Sync code generation](contributing/sync-codegen.md): why sync APIs mirror the
  async source tree.

## Public API promise

The 1.0 documentation treats these import paths as public:

- `ksef2`
- `ksef2.domain.models`
- `ksef2.fa3`
- `ksef2.core.xades`
- stable exception classes exported from `ksef2`

Endpoint, mapper, and schema modules remain implementation details unless a
reference page says otherwise.

---
title: Overview
description: Start here for the ksef2 Python SDK documentation.
---

ksef2 is a Python SDK for Poland's KSeF v2 API. It gives you sync and async
clients, typed request models, invoice session helpers, and low-level endpoint
access.

> **Unofficial SDK.** ksef2 is a community-maintained Python SDK. It is not
> published, endorsed, or supported by Poland's Ministry of Finance. Use the
> official KSeF documentation as the authority for API behavior.

## Start

- [Run the quickstart](getting-started/quickstart.md)
- [Choose an authentication workflow](workflows/authentication.mdx)
- [Send, query, and download invoices](workflows/overview.mdx)

## Main pages

- [Workflow overview](workflows/overview.mdx): task-oriented paths for
  clients, authentication, invoices, status, tokens, permissions, certificates,
  limits, public lookup, TEST data, and XAdES.
- [Client setup](workflows/client-setup.mdx): choose sync or async, public root
  branches, and authenticated workflow branches.
- [Public API contract](guides/public-api.md): stable import paths and internal
  package boundaries for application code.
- [Error handling](guides/errors.md): catch SDK exceptions, inspect KSeF error
  payloads, and handle polling timeouts.
- [Sending invoices](workflows/sending-invoices.mdx): open online or batch
  sessions and submit XML to KSeF.
- [Admin workflows](workflows/tokens.mdx): start with tokens, then use
  permissions, certificates, and limits as needed.
- [Low-level API](raw/overview.md): use schema-native endpoint wrappers for
  custom signing, encryption custody, or exact KSeF payload debugging.

## Reference

Use the [API reference](reference/api-signatures.md) when you need signatures,
return types, model names, or the exact generated sync/async variants.

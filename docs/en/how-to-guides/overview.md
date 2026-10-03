---
title: How-to Guide Overview
description: Choose the right task guide for the public ksef2 SDK surface.
---

Use this section when you already know the SDK shape and want to complete a
specific KSeF task. The quickstart shows one end-to-end path; these how-to
guides separate the decisions you usually make in production code.

## Setup

- [Set up clients](client-setup.md): Choose sync or async, public root branches, and authenticated workflow branches.
- [Authenticate](authenticate.md): Choose TEST certificates, KSeF tokens, XAdES certificates, environment variables, or CLI-compatible profiles.
- [Use profiles](profiles.md): Share local ksef2-cli profile configuration with SDK authentication and ProfileStore.

## Invoice work

- [Build FA(3) invoices](build-fa3-invoices.md): Generate simple public invoice models and sendable FA(3) XML with the fluent builder.
- [Send invoices](send-invoices.md): Submit FA(3) XML through online sessions or batch sessions, then inspect processing results.
- [Check status and UPO](get-status-and-upo.md): Poll online or batch status, list session invoices, and retrieve UPO documents.
- [Query invoices](query-invoices.md): Build metadata filters, page through results, and poll until newly sent invoices are visible.
- [Download invoices](download-invoices.md): Download one processed invoice by KSeF number or schedule encrypted export packages.

## Administration

- [Manage tokens](manage-tokens.md): Generate, list, inspect, and revoke KSeF tokens for automation.
- [Manage permissions](configure-permissions.md): Grant, query, revoke, and monitor KSeF permissions.
- [Manage certificates](manage-certificates.md): Check limits, enroll certificates, retrieve issued material, and revoke certificates.
- [Manage limits](manage-limits.md): Read and override context, subject, and API rate limits.

## Utilities

- [Inspect encryption certificates](inspect-encryption-certificates.md): Inspect public KSeF certificates used by encrypted invoice and export workflows.
- [Query PEPPOL providers](query-peppol-providers.md): Query public PEPPOL provider data from the root client.
- [Use TEST data](use-test-data.md): Create sandbox subjects, permissions, attachment flags, and temporal cleanup fixtures.
- [Use XAdES helpers](use-xades-helpers.md): Load certificate material, generate TEST certificates, and sign XML.
- [Low-level API](../reference/low-level/overview.md): Drop to schema-native endpoint wrappers for custom signing, encryption custody, or payload debugging.

:::tip[Sync and async use the same workflow]
The async client exposes the same branches and method names. Use
`AsyncClient`, await network calls, and use `async with` for client and
session lifecycles.
:::

## Typical production order

1. Configure the environment and credentials.

   Use environment variables for secrets and local config for non-secret profile
   defaults.

2. Authenticate once for the target context.

   The authenticated client exposes `online_session`, `batch`, `invoices`,
   `tokens`, `permissions`, `certificates`, and other workflow branches.

3. Run the workflow branch that owns the task.

   Use public root branches for encryption certificates, PEPPOL lookup, and
   TEST data. Use authenticated branches for invoices, sessions, tokens,
   permissions, certificates, and limits.

4. Poll for KSeF processing or operation status.

   The high-level helpers include polling methods for invoice status, batch
   completion, permission operations, certificate enrollment, query visibility,
   and export package readiness.

5. Persist the business result.

   Store KSeF numbers, session references, operation references, export handles,
   downloaded XML, token references, certificate serial numbers, and UPO
   documents according to your application’s retention policy.

## Reference

- [Quickstart](../getting-started/quickstart.md): Run the first generate, send, confirm, and download workflow.
- [Operations](../reference/operations.md): Map common tasks to SDK branches, polling helpers, and retry boundaries.
- [Public API contract](../reference/public-api.md): Review stable imports and public modules exposed by the SDK.
- [Low-level API](../reference/low-level/overview.md): Use schema-native endpoint wrappers when a high-level workflow is not enough.

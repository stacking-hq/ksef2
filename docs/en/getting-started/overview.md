---
title: Overview
description: Start here for the ksef2 Python SDK documentation.
---

![ksef2](../assets/logo-dark.png)

**ksef2** is a fully typed Python SDK for Poland's KSeF v2 API.

> **Unofficial SDK.** ksef2 is a community-maintained Python SDK. It is not
> published, endorsed, or supported by Poland's Ministry of Finance. Use the
> official KSeF documentation as the authority for API behavior.

[Official KSeF API v2 documentation](https://api-test.ksef.mf.gov.pl/docs/v2/) — Use the Ministry of Finance documentation as the authority for API behavior.

This project aims to be a go-to solution for developers building custom integrations, automations and back-office tools around KSeF without hand-writing HTTP requests, polling loops, or encryption handling.

The main premise of the SDK is to provide a high-level pythonic interface that allows developers to focus on their business logic rather than the intricacies of the KSeF API.

While the SDK abstracts away many of the complexities of interacting with the KSeF API, we are aware that some developers may want to have more control over the requests and responses. Therefore, the SDK also provides low-level access to the API endpoints, allowing developers to customize their interactions with the API as needed.

## Next steps

- [Run the quickstart](../getting-started/quickstart.md): Get started with a working example of authentication, sending, querying, and downloading invoices.
- [Get familiar with the SDK](../concepts/overview.md): Learn about the SDK's authentication patterns, client lifecycle, and invoice handling.
- [Send, query, and download invoices](../how-to-guides/overview.md): Learn how to send invoices online or in batch, query invoices with filters and pagination, and download invoices directly or as export packages.
- [Low-level API](../reference/low-level/overview.md): Use schema-native endpoint wrappers when you need direct control.

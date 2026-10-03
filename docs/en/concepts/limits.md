---
title: Limits, Polling, and Retries
description: Understand KSeF context limits, subject limits, API rate limits, polling deadlines, and retry boundaries.
---

KSeF limits are part of integration design. They influence how many invoices you
put into a session, how often workers poll, when to choose exports instead of
direct downloads, and how aggressively a system should retry after throttling.

The SDK exposes limit reads and administrative overrides through
`auth.limits`, but most applications should treat limits as scheduling inputs,
not as values to change during ordinary business workflows.

## Limit families

| Limit family | SDK model | What it affects |
| --- | --- | --- |
| Context limits | `ContextLimits` | Online and batch session invoice counts and payload sizes. |
| Subject limits | `SubjectLimits` | Certificate enrollment and certificate issuance limits for the authenticated subject. |
| API rate limits | `ApiRateLimits` | Per-second, per-minute, and per-hour request volume for endpoint families. |

```python
context = auth.limits.get_context_limits()
print(context.online_session.max_invoices)
print(context.batch_session.max_invoice_size_mb)

rate = auth.limits.get_api_rate_limits()
print(rate.invoice_send.per_minute)
```

## How limits shape workflows

Use online sending for low-volume or immediate invoice submission. Use batch
sending when invoices can be prepared as a package. Use exports when you need a
larger retrieval set; repeated direct downloads and high-frequency incremental
queries are usually the wrong architecture for a production synchronizer.

For production applications, treat KSeF as a remote system of record that you
synchronize from at controlled intervals. Store metadata and downloaded invoice
content locally, then serve user-facing screens from your local store.

:::caution[Limits are integration inputs]
Batch sizes, export usage, polling cadence, and retry strategy should be
chosen from KSeF limits and your own operational requirements. Do not hide
limit overrides inside ordinary invoice processing code.
:::

## Polling deadlines

Many KSeF workflows are asynchronous. The SDK provides helpers such as
`.wait()` on invoice submissions, sessions, export jobs and `search()` results,
`download(..., timeout=...)`, and token activation polling.

Those helper timeouts are workflow wait limits. They are not the same as HTTP
socket timeouts. A polling timeout means the expected KSeF state was not reached
before the local deadline; it does not always mean the remote operation failed.

## Retry boundaries

The root client transport can retry transport failures and retryable KSeF
responses. That does not mean every operation is safe to repeat blindly.
Invoice submission, permission grants, certificate enrollment, token
generation, and session opening should be retried from your application boundary
with stored references and workflow-specific idempotency rules.

When KSeF throttles a request, respect the returned retry guidance and back off
the worker schedule. If a workflow already has a KSeF reference number, prefer
checking status or resuming from that reference over recreating the operation.

## Related pages

- [Manage limits](../how-to-guides/manage-limits.md): Read context, subject, and API rate limits through SDK code.
- [Operations](../reference/operations.md): Review timeout, retry, polling, and idempotency behavior.
- [Sending invoices](invoice-lifecycle.md): Choose online or batch sending based on workflow and volume.
- [Querying and exports](querying-and-exports.md): Use exports and incremental retrieval patterns with KSeF limits in mind.

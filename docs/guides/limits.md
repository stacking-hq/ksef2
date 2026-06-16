---
title: Limits and Restrictions
description: Read and manage KSeF API, context, and subject limits.
---

Manage API limits and restrictions for the KSeF system. All limits operations are accessed through the authenticated client via `auth.limits`.

## Querying Limits

### Context Limits

Get the effective limits for the current context (session type limits).

**SDK Endpoint:** `GET /limits/context`

```python
# After authenticating:
auth = client.authentication.with_xades(nip=NIP, cert=cert, private_key=private_key)

context_limits = auth.limits.get_context_limits()
print(f"Online max invoices: {context_limits.online_session.max_invoices}")
print(f"Online max invoice size (MB): {context_limits.online_session.max_invoice_size_mb}")
print(f"Online max with attachment (MB): {context_limits.online_session.max_invoice_with_attachment_size_mb}")
print(f"Batch max invoices: {context_limits.batch_session.max_invoices}")
print(f"Batch max invoice size (MB): {context_limits.batch_session.max_invoice_size_mb}")
```

### Subject Limits

Get the effective limits for the current subject (certificate/enrollment limits).

**SDK Endpoint:** `GET /limits/subject`

```python
subject_limits = auth.limits.get_subject_limits()
if subject_limits.certificate:
    print(f"Max certificates: {subject_limits.certificate.max_certificates}")
if subject_limits.enrollment:
    print(f"Max enrollments:  {subject_limits.enrollment.max_enrollments}")
```

### API Rate Limits

Get the current API rate limits.

**SDK Endpoint:** `GET /rate-limits`

```python
rate_limits = auth.limits.get_api_rate_limits()
print(f"Invoice send: {rate_limits.invoice_send.per_second}/request  {rate_limits.invoice_send.per_minute}/m  {rate_limits.invoice_send.per_hour}/h")
print(f"Online session: {rate_limits.online_session.per_second}/request  {rate_limits.online_session.per_minute}/m  {rate_limits.online_session.per_hour}/h")
print(f"Invoice download: {rate_limits.invoice_download.per_second}/request  {rate_limits.invoice_download.per_minute}/m  {rate_limits.invoice_download.per_hour}/h")
```

> Full example: [`scripts/examples/limits/limits_query.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/limits/limits_query.py)

## Test Environment Only

The following endpoints are only available on the TEST environment and allow modifying limits for testing purposes.

The recommended workflow is to **fetch** the current limits, **modify** the values you need, and **post** them back:

### Set Session Limits

**SDK Endpoint:** `POST /testdata/limits/context/session`

```python
# Fetch current limits
limits = auth.limits.get_context_limits()

# Modify what you need
limits.online_session.max_invoices = 5000
limits.batch_session.max_invoice_size_mb = 5

# Push back
auth.limits.set_session_limits(limits=limits)
```

### Reset Session Limits

**SDK Endpoint:** `DELETE /testdata/limits/context/session`

```python
auth.limits.reset_session_limits()
```

### Set Subject Limits

**SDK Endpoint:** `POST /testdata/limits/subject/certificate`

```python
# Fetch current limits
limits = auth.limits.get_subject_limits()

# Modify what you need
limits.certificate.max_certificates = 5

# Push back
auth.limits.set_subject_limits(limits=limits)
```

### Reset Subject Limits

**SDK Endpoint:** `DELETE /testdata/limits/subject/certificate`

```python
auth.limits.reset_subject_limits()
```

### Set API Rate Limits

**SDK Endpoint:** `POST /testdata/rate-limits`

```python
# Fetch current rate limits
limits = auth.limits.get_api_rate_limits()

# Modify what you need
limits.invoice_send.per_second = 100
limits.invoice_send.per_minute = 500
limits.online_session.per_hour = 1200

# Push back
auth.limits.set_api_rate_limits(limits=limits)
```

### Reset API Rate Limits

**SDK Endpoint:** `DELETE /testdata/rate-limits`

```python
auth.limits.reset_api_rate_limits()
```

### Set Production Rate Limits

Set API rate limits to production values. This is useful for testing with production-like constraints.

**SDK Endpoint:** `POST /testdata/rate-limits/production`

```python
# Set production rate limits
auth.limits.set_production_rate_limits()

# Later, reset back to test defaults
auth.limits.reset_api_rate_limits()
```

> Full example: [`scripts/examples/limits/limits_modify.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/limits/limits_modify.py)

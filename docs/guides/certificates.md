---
title: Certificates
description: Enroll, query, retrieve, and revoke KSeF certificates.
---

Certificate management is available through `auth.certificates`.

## Certificate Limits

```python
limits = auth.certificates.get_limits()
print(limits.can_request)
print(limits.enrollment_remaining, limits.enrollment_limit)
print(limits.certificate_remaining, limits.certificate_limit)
```

SDK endpoint: `GET /certificates/limits`

## Enrollment Data

```python
data = auth.certificates.get_enrollment_data()
print(data.common_name)
print(data.iso_country_code)
print(data.organization_identifier)
```

SDK endpoint: `GET /certificates/enrollments/data`

## Enroll a Certificate

```python
result = auth.certificates.enroll(
    certificate_name="SDK auth certificate",
    certificate_type="authentication",
    csr=base64_encoded_csr,
)

print(result.reference_number)
print(result.timestamp)
```

SDK endpoint: `POST /certificates/enrollments`

## Check Enrollment Status

```python
status = auth.certificates.get_enrollment_status(
    reference_number=result.reference_number,
)
print(status.status_code, status.status_description)
print(status.certificate_serial_number)
```

SDK endpoint: `GET /certificates/enrollments/{referenceNumber}`

## Query Certificates

```python
from ksef2.domain.models.pagination import OffsetPaginationParams

response = auth.certificates.query(certificate_type="authentication", status="active",
                                   params=OffsetPaginationParams(page_offset=0, page_size=20))

for cert in response.certificates:
    print(cert.serial_number, cert.name, cert.status)
```

SDK endpoint: `POST /certificates/query`

To iterate all matching certificates:

```python
for cert in auth.certificates.all(status="active"):
    print(cert.serial_number, cert.valid_to)
```

## Retrieve Certificates

```python
retrieved = auth.certificates.retrieve(
    certificate_serial_numbers=["0321C82DA41B4362"],
)
for cert in retrieved.certificates:
    print(cert.serial_number, cert.name, cert.certificate_type)
    print(cert.base64_encoded_certificate[:32])
```

SDK endpoint: `POST /certificates/retrieve`

## Revoke a Certificate

```python
auth.certificates.revoke(
    certificate_serial_number="0321C82DA41B4362",
    reason="key_compromise",
)
```

SDK endpoint: `POST /certificates/{certificateSerialNumber}/revoke`

## Common Values

Certificate types:
- `authentication`
- `offline`

Certificate statuses:
- `active`
- `blocked`
- `revoked`
- `expired`

Revocation reasons:
- `unspecified`
- `superseded`
- `key_compromise`

## Related

- [Authentication](authentication.md)

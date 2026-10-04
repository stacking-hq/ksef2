---
title: Manage Certificates
description: Check certificate limits, enroll certificates, query issued certificates, and revoke certificates.
---

Use `auth.certificates` for KSeF certificate enrollment, search, retrieval, and
revocation. The SDK sends CSR and lifecycle requests. Your certificate tooling
still owns private-key generation and private-key storage.

## Check limits and enrollment data

```python
limits = auth.certificates.get_limits()

# CertificateLimitsResponse
# {
#   "can_request": true,
#   "enrollment_limit": 10,
#   "enrollment_remaining": 9,
#   "certificate_limit": 10,
#   "certificate_remaining": 8
# }

subject = auth.certificates.get_enrollment_data()

# CertificateEnrollmentData
# {
#   "common_name": "Example subject",
#   "iso_country_code": "PL",
#   "organization_identifier": "VATPL-5261040828"
# }
```

Use the enrollment data when building the CSR in your certificate tooling.

## Enroll a certificate

Submit a CSR and persist the returned enrollment reference.

```python
csr = """-----BEGIN CERTIFICATE REQUEST-----
...
-----END CERTIFICATE REQUEST-----"""

enrollment = auth.certificates.enroll(
    certificate_name="billing-service",
    certificate_type="authentication",
    csr=csr,
)

# CertificateEnrollment: exposes every field of the enrollment response
# {
#   "reference_number": "20260625-CERT-...",
#   "timestamp": "2026-06-25T10:00:00Z"
# }
```

`enroll()` returns a `CertificateEnrollment` handle. Wait for KSeF to issue the
certificate:

```python
status = enrollment.wait(timeout=60.0, poll_interval=2.0)
```

`wait()` raises `KSeFCertificateEnrollmentFailedError` when KSeF rejects or
cancels the request and `KSeFCertificateEnrollmentTimeoutError` when it does not
finish in time. To check the status once without waiting, call
`enrollment.get_status()`, or
`auth.certificates.get_enrollment_status(reference_number=...)` when you only
stored the reference number:

```python
status = auth.certificates.get_enrollment_status(
    reference_number=enrollment.reference_number,
)

# CertificateEnrollmentStatusResponse
# {
#   "status_code": 200,
#   "status_description": "Completed",
#   "certificate_serial_number": "0123456789ABCDEF"
# }
```

:::caution[Keep private keys outside the SDK]
The SDK does not need the private key for certificate enrollment. Generate and
protect the private key in your certificate tooling, submit only the CSR to
KSeF, and store the issued certificate next to its matching key.
:::

## Query, retrieve, and revoke

### Query

```python
for certificate in auth.certificates.list(status="active"):
    print(certificate.serial_number, certificate.name, certificate.valid_to)
```

### Retrieve

```python
result = auth.certificates.retrieve(
    certificate_serial_numbers=["0123456789ABCDEF"],
)

for certificate in result.certificates:
    print(certificate.serial_number, certificate.certificate_type)
```

### Revoke

```python
auth.certificates.revoke(
    certificate_serial_number="0123456789ABCDEF",
    reason="key_compromise",
)
```

## Recommended flow

1. Check certificate and enrollment quotas.

2. Fetch enrollment subject data.

3. Generate a private key and CSR outside the SDK.

4. Submit enrollment and persist the reference number.

5. Wait for issuance, retrieve the certificate, and store it with the private key.

6. Revoke certificates that are no longer valid or whose private key may be
   compromised.

## Next workflows

- [Use XAdES helpers](use-xades-helpers.md): Load certificate material and authenticate with XAdES.
- [Certificates](../concepts/certificates.md): Understand certificate roles in authentication, signing, and enrollment.
- [Authenticate](authenticate.md): Use issued certificate material for SDK authentication.

---
title: Certyfikaty
description: Limity, rejestracja, pobieranie i unieważnianie certyfikatów.
---

Operacje certyfikatów są dostępne przez `auth.certificates`.

```python
limits = auth.certificates.get_limits()
print(limits)
```

## Rejestracja

```python
enrollment = auth.certificates.get_enrollment_data()
print(enrollment)
```

Po rejestracji możesz sprawdzić status i pobrać certyfikat:

```python
status = auth.certificates.get_enrollment_status(reference_number="ref")
cert = auth.certificates.retrieve(reference_number="ref")
```

## Listowanie

```python
for cert in auth.certificates.all(status="active"):
    print(cert.reference_number)
```

## Unieważnienie

```python
auth.certificates.revoke(reference_number="ref")
```

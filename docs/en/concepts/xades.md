---
title: XAdES
description: Understand the XML signature step used by certificate-based KSeF authentication.
---

XAdES is the XML signature format used when KSeF authentication is backed by a
certificate. In the SDK, XAdES belongs to authentication: it signs the
`AuthTokenRequest` built from a KSeF challenge and a login context.

It is not the invoice XML schema, not session encryption, and not the export
package format.

## What XAdES proves

During XAdES authentication, KSeF checks a signed XML document and the
certificate embedded in the signature. The login context is the NIP passed to
the SDK method. The authenticating subject is read from the signing certificate,
for example:

- a qualified personal certificate containing PESEL or NIP;
- a qualified organization seal containing NIP;
- a KSeF-issued authentication certificate;
- a certificate recognized by fingerprint permissions;
- TEST-only self-signed certificate material.

KSeF then checks whether that subject is allowed to operate in the requested
context.

## SDK layers

Most applications should use `with_xades()` or a profile that dispatches to it:

```python
auth = client.authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=private_key,
)
```

The helper handles the normal sequence:

1. Request an authentication challenge.
2. Build `AuthTokenRequest` XML for the context.
3. Sign the XML with XAdES.
4. Submit the signed XML to KSeF.
5. Poll the authentication operation.
6. Redeem access and refresh tokens.

Use `ksef2.xades` directly when you need to load certificate material yourself,
inspect signed XML, or test a low-level integration boundary.

:::tip[External signing boundary]
If another system signs XML and Python should only submit or redeem the
result, use the low-level authentication endpoints and then bind the redeemed
tokens with
`client.authentication.resume(AuthenticationResumeState.from_tokens(auth_tokens))`.
:::

## TEST certificates

The SDK can generate TEST-only self-signed certificate material with
`with_test_certificate()` or lower-level helpers in `ksef2.xades`. That is a
development shortcut for `Environment.TEST`; it is not valid for DEMO or
PRODUCTION.

## Related pages

- [Authentication methods](authentication-methods.md): See XAdES alongside token, TEST certificate, and profile authentication.
- [Use XAdES helpers](../how-to-guides/use-xades-helpers.md): Load certificate material and sign authentication XML in code.
- [Certificates](certificates.md): Understand certificate identity, enrollment, and issued certificate types.
- [Low-level authentication](../reference/low-level/authentication.md): Run manual authentication when signing is handled outside the high-level SDK helper.

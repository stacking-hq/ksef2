---
title: Low-level authentication
description: Run KSeF authentication steps manually and bind the result back to ksef2 clients.
---

Use low-level authentication when another system owns signing, token encryption,
or polling policy. The SDK still sends requests and parses responses, but your
code chooses each step.

## Token authentication

```python
from time import sleep

from ksef2 import Client, Environment
from ksef2.raw import encrypt_token, spec
from ksef2.raw.mappers import auth as auth_mapper

POLL_INTERVAL_SECONDS = 1.0
MAX_POLL_ATTEMPTS = 60

client = Client(Environment.TEST)

challenge = client.raw.auth.challenge()
cert = next(
    cert
    for cert in client.raw.encryption.fetch_public_certificates()
    if spec.PublicKeyCertificateUsage.KsefTokenEncryption in cert.usage
)

encrypted = encrypt_token(
    "your-ksef-token",
    str(challenge.timestampMs),
    cert.certificate,
)
request = spec.InitTokenAuthenticationRequest(
    challenge=challenge.challenge,
    contextIdentifier=spec.AuthenticationContextIdentifier(
        type=spec.AuthenticationContextIdentifierType.Nip,
        value="5261040828",
    ),
    encryptedToken=encrypted,
    publicKeyId=cert.publicKeyId,
)

init = client.raw.auth.token_auth(request)

for _ in range(MAX_POLL_ATTEMPTS):
    status = client.raw.auth.auth_status(
        bearer_token=init.authenticationToken.token,
        reference_number=init.referenceNumber,
    )

    if status.status.code == 200:
        break
    if status.status.code >= 400:
        raise RuntimeError(
            f"Authentication failed: {status.status.code} "
            f"{status.status.description}"
        )

    sleep(POLL_INTERVAL_SECONDS)
else:
    raise TimeoutError("Authentication did not finish")

raw_tokens = client.raw.auth.redeem_token(init.authenticationToken.token)
auth = client.authenticated(auth_mapper.from_spec(raw_tokens))
```

After `client.authenticated(...)`, you can use either workflow branches such as
`auth.invoices` or low-level branches such as `auth.raw.invoices`.

## XAdES with external signing

Use this shape when a signing gateway or HSM returns the signed XML.

```python
from ksef2.raw.mappers import auth as auth_mapper

challenge = client.raw.auth.challenge()
signed_xml = signing_gateway.sign_ksef_challenge(
    challenge=challenge.challenge,
    nip="5261040828",
)

init = client.raw.auth.xades_auth(signed_xml, verify_chain=True)
status = client.raw.auth.auth_status(
    bearer_token=init.authenticationToken.token,
    reference_number=init.referenceNumber,
)

if status.status.code == 200:
    raw_tokens = client.raw.auth.redeem_token(init.authenticationToken.token)
    auth = client.authenticated(auth_mapper.from_spec(raw_tokens))
```

## Async shape

Async clients expose the same low-level branches. Await network calls:

```python
challenge = await client.raw.auth.challenge()
init = await client.raw.auth.xades_auth(signed_xml)
raw_tokens = await client.raw.auth.redeem_token(init.authenticationToken.token)
auth = client.authenticated(auth_mapper.from_spec(raw_tokens))
```

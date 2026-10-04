---
title: Authentication methods
description: Understand KSeF token, XAdES, TEST certificate, and profile-based authentication in ksef2.
---

Authentication is the step that turns a root `Client` or `AsyncClient` into an
authenticated client for one KSeF context. The root client chooses the
environment and owns transport resources. The authentication method proves who
may operate in the selected context.

KSeF separates two ideas that are easy to merge mentally:

| Idea | Meaning in KSeF | SDK surface |
| --- | --- | --- |
| Login context | The taxpayer or entity on whose behalf operations will run. | `nip` plus `context_type`, for example `context_type="nip"`. |
| Authenticating subject | The token or certificate-backed identity proving the right to enter that context. | `ksef_token`, or `cert` plus `private_key`. |

After authentication succeeds, the SDK returns an `AuthenticatedClient`. That
client carries KSeF access and refresh tokens and exposes protected branches
such as sessions, invoices, tokens, permissions, certificates, limits, and
session history.

```text
Client(Environment.TEST)
  -> client.authentication
    -> with_token(), with_xades(), with_test_certificate(), or with_profile()
      -> AuthenticatedClient for one KSeF context
        -> online sessions, batch sessions, invoices
        -> tokens, permissions, certificates, limits
```

## KSeF methods and SDK helpers

At the KSeF API level, authentication has two main families:

| KSeF family | What is sent to KSeF | SDK helper |
| --- | --- | --- |
| XAdES authentication | A signed `AuthTokenRequest` XML document. | `with_xades()` |
| KSeF token authentication | A KSeF token encrypted with the current token-encryption certificate. | `with_token()` |

The SDK adds two convenience layers:

| SDK helper | What it adds |
| --- | --- |
| `with_test_certificate()` | Generates temporary TEST certificate material, then uses the XAdES flow. |
| `with_profile()` | Reads local `ksef2-cli` profile configuration and dispatches to token, TEST certificate, PEM XAdES, or PKCS#12 XAdES authentication. |

:::note[Profiles are not another KSeF credential]
A profile stores how to authenticate: environment, NIP, method, certificate
paths, polling settings, and secret environment-variable names. The actual
credential is still a KSeF token or certificate-backed XAdES signature.
:::

## Choose a method

| Method | Use it when | What the SDK does |
| --- | --- | --- |
| `with_test_certificate()` | You are developing against `Environment.TEST` and want the least setup. | Generates a TEST certificate from the NIP and authenticates through XAdES. |
| `with_token()` | Your application already has a KSeF token for the target context. | Loads the KSeF token-encryption certificate, encrypts the token with the challenge timestamp, submits token authentication, polls status, and redeems tokens. |
| `with_xades()` | Your application has certificate and private-key material available to Python. | Builds the KSeF challenge XML, signs it with XAdES, submits the signed XML, polls status, and redeems tokens. |
| `with_profile()` | You want SDK code and `ksef2-cli` to share named local authentication settings. | Resolves the selected profile and calls the matching SDK method. |

**See also:**

- [Configure authentication](../how-to-guides/authenticate.md): Use the selected method in runnable SDK code with environment variables and secret boundaries.
- [Use profiles](../how-to-guides/profiles.md): Share CLI-compatible local authentication settings between command-line and SDK workflows.

## XAdES subject and context

For XAdES authentication, the SDK builds and signs the XML request for the
context NIP you pass to `with_xades()`. KSeF reads the authenticating subject
from the signing certificate: for example a company seal certificate, a
personal certificate containing a NIP or PESEL, a KSeF authentication
certificate, or a certificate allowed by fingerprint permissions.

That means `nip` is the login context, not necessarily the identifier embedded
in the signing certificate. A person can authenticate into a company context if
KSeF sees the right active permissions for that person or certificate.

:::tip[Externally signed XML]
`with_xades()` is the high-level path when Python can load the certificate
and private key. If signing happens outside Python, use the low-level raw
authentication endpoints and bind the redeemed `AuthTokens` with
`client.authentication.resume(AuthenticationResumeState.from_tokens(auth_tokens))`.
:::

## Access tokens refresh themselves

KSeF access tokens are short-lived. The authenticated client therefore keeps
the refresh token next to the access token and renews the access token without
your code doing anything: shortly before `access_token_valid_until`, and once
after a `401` response, retrying the failed request a single time. Concurrent
requests share one refresh.

This also covers `client.authentication.resume(state)`: a state whose access
token has expired works as long as its refresh token is still valid.
`auth.resume_state()` and `auth.auth_tokens` return the current tokens, so save
the state again after long-running work.

When the refresh token is expired or rejected, the client raises
`KSeFAuthenticationExpiredError`, which subclasses `KSeFAuthError`. Authenticate
again to continue. To refresh tokens yourself, pass
`TransportConfig(auto_refresh_tokens=False)`. See the
[Operations reference](../reference/operations.md#access-token-refresh) for the
exact rules.

## Profiles are local authentication configuration

`with_profile()` is not a separate credential type. It is a configuration layer
over the same authentication methods:

| Profile auth type | Direct SDK method |
| --- | --- |
| `token` | `with_token()` |
| `test_certificate` | `with_test_certificate()` |
| `xades_pem` | `with_xades()` with PEM certificate and key files |
| `xades_p12` | `with_xades()` with a PKCS#12/PFX archive |

A profile stores non-secret settings such as environment, NIP, auth type,
certificate paths, polling settings, and the name of the environment variable
that contains a secret. It should not store token values, private-key
passwords, or PKCS#12 passwords.

Profile selection follows the same order in the SDK and CLI:

1. Explicit profile name passed to `with_profile("name")`.
2. `KSEF2_PROFILE`.
3. `active_profile` in the local profile config.

:::tip[Profiles work well with the CLI]
Create and select profiles with `ksef2-cli` when humans operate the same
context from the terminal. Use `ProfileStore` when a Python tool should
create or update the shared profile file itself.
:::

The root client environment must match the selected profile environment. A
`test` profile belongs with `Client(Environment.TEST)`, a `demo` profile with
`Client(Environment.DEMO)`, and a `production` profile with
`Client(Environment.PRODUCTION)`.

## Authentication lifecycle

1. The root client requests a challenge from the selected KSeF environment.

2. The chosen method proves identity for the requested context.

   Token authentication encrypts the KSeF token together with the challenge
   timestamp. XAdES authentication signs the challenge XML. TEST certificate
   authentication generates TEST certificate material first. Profile
   authentication resolves one of those paths from local configuration.

3. KSeF starts an asynchronous authentication operation.

   The SDK keeps the temporary operation token and reference number internally
   while it polls for completion.

4. The SDK redeems the completed operation into access and refresh tokens.

5. The returned `AuthenticatedClient` carries those tokens into protected SDK
   operations.

Async clients use the same method names on `AsyncClient`; call them with
`await`. The choice between token, TEST certificate, XAdES, and profile
authentication stays the same.

## What to protect

| Value | Why it matters |
| --- | --- |
| KSeF token | It can authenticate into its configured context until revoked or expired. |
| Private key and certificate password | They can prove the identity used by XAdES authentication. |
| Access token | It authorizes protected SDK calls while valid. |
| Refresh token | It can mint a new access token while valid. |
| Authentication resume state | It contains access and refresh tokens needed to rehydrate an authenticated client. |
| Serialized session state | It can contain session encryption material and batch upload URLs needed to resume a workflow. |

Keep secrets in environment variables, secret managers, or application-owned
secure storage. Keep profile files limited to non-secret defaults and the names
of environment variables that contain secrets.

## Authentication is not authorization

Authentication proves identity for a context. Permissions still determine which
operations that identity may perform. A credential can authenticate correctly
and still fail when sending invoices, querying metadata, managing tokens, or
granting permissions.

:::note[Debug the context and permissions together]
When a protected operation fails after authentication, check the selected
environment, context NIP, and active permission set. The credential type alone
does not decide authorization.
:::

## Related pages

- [Authenticate](../how-to-guides/authenticate.md): Configure environment variables, token auth, XAdES auth, TEST certificates, and profiles.
- [Use profiles](../how-to-guides/profiles.md): Share local ksef2-cli profile configuration with SDK authentication and ProfileStore.
- [Low-level authentication](../reference/low-level/authentication.md): Run the authentication operation manually when another system signs XML or owns token exchange.
- [CLI authentication](../../cli/guides/authentication.md): Use the same profile-backed authentication methods from ksef2-cli.
- [Tokens and permissions](permissions.md): Understand how authentication credentials and protected permissions fit together.
- [XAdES](xades.md): Understand certificate-backed XML signing during authentication.

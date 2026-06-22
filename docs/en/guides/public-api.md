---
title: Public API Contract
description: Stable import paths and internal boundaries for ksef2 1.0.
---

Use the documented import paths on this page when building application code.
They are the paths intended to remain stable through the 1.x line.

## Stable application imports

| Import path | Use it for |
| --- | --- |
| `ksef2` | Root clients, environment and transport config, `FormSchema`, `__version__`, and public exceptions. |
| `ksef2.clients` | Concrete sync and async client classes when you need them for type annotations. |
| `ksef2.domain.models` | SDK request, response, filter, pagination, token, permission, session, and batch models. |
| `ksef2.xades` | Certificate loading, TEST certificate generation, local XAdES signing helpers, and `LocalSigner`. |
| `ksef2.profiles` | Local `ksef2-cli` compatible profile config helpers. |
| `ksef2.raw` | Low-level endpoint clients, schema-native `spec` and `supp` models, and low-level crypto helpers. |
| `ksef2.raw.mappers` | Public mappers for crossing between raw schema models and SDK models. |
| `ksef2.services` | High-level service classes when you construct services manually instead of using client branches. |
| `ksef2.services.renderers` | Optional XSLT/PDF invoice rendering helpers. |

Prefer the highest-level import that fits the workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem
```

## Root package exports

The root `ksef2` package is the public facade for common application code:

- `Client`, `AsyncClient`;
- `Environment`, `TransportConfig`, `TimeoutConfig`, `RetryConfig`,
  `TlsConfig`, `ConnectionPoolConfig`;
- `FormSchema`;
- `ExceptionCode` and all public `KSeF*` exception classes;
- `__version__`.

Use root imports for these names instead of reaching into implementation
modules.

## Low-level API stability

`ksef2.raw` is public, but intentionally lower level. Its import path is stable;
its schema-native model shapes follow the checked KSeF OpenAPI version.

```python
from ksef2.raw import spec
from ksef2.raw.mappers import auth as auth_mapper
```

Do not import generated OpenAPI models from `ksef2.infra.schema.api`. Use
`ksef2.raw.spec` and `ksef2.raw.supp` so application code stays on the supported
surface.

## Internal paths

Avoid these paths in application code:

- `ksef2.infra.*`: generated schemas and mapper internals;
- `ksef2.endpoints.*`: endpoint transport implementation;
- `ksef2.core.*`: internal protocol, transport, middleware, and helper modules;
- `scripts/*`: repository tooling, not package API.

Some internal paths may still be importable for SDK implementation or tests, but
they are not the compatibility contract for application code.

## Compatibility rule

After 1.0, changes that remove or rename stable import paths require a major
version bump. Additive APIs can ship in minor releases. Patch releases should
preserve documented imports and behavior except for bug fixes.

## Reference

- [Client guide](client.md)
- [Low-level API](../raw/overview.md)
- [Sync code generation](../contributing/sync-generation.md)

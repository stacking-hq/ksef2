---
title: Sync Code Generation
description: Understand the generated sync tree and the async source of truth.
---

The async modules are the hand-written source of truth for mirrored SDK APIs.
Their sync twins are committed generated artifacts.

When changing a mirrored client, endpoint, middleware, protocol, or service:

1. Edit the `async_*` source.
2. Run `just gen-sync`.
3. Review the generated sync diff.
4. Run `just check-gen-sync` and the normal verification suite.

Do not edit files with the generated header directly. If generated sync code is
wrong, fix `scripts/gen_sync.py` or the async source, then regenerate.

## Commands

```bash
just gen-sync
just check-gen-sync
uv run python scripts/gen_sync.py --only src/ksef2/clients/async_invoices.py --diff
```

`check-gen-sync` fails when any generated sync file differs from a fresh
generation. The same guard also runs in `just release-check` and in
`tests/unit/test_generated_sync.py`, so stale generated files are caught by the
plain unit suite.

## Exclusions

Some files intentionally stay hand-written because their sync and async
lifecycles are not mechanical twins, including root clients, HTTP transports,
`__init__.py` files, and already-shared helper modules. The authoritative list
and justification for each exclusion lives in `scripts/gen_sync.py`.

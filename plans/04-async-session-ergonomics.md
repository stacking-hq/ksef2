# Plan 4 — Eliminate the `async with await` session pattern

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed), preparing for 1.0.0. The async
client currently forces this pattern, which appears in the README quickstart
and all async docs/examples:

```python
async with await auth.online_session(form_code=FormSchema.FA3) as session:
    ...
```

Cause: `AsyncAuthenticatedClient.online_session()`
(`src/ksef2/clients/async_authenticated.py`) is an `async def` that performs
the network call to open the session and returns an
`AsyncOnlineSessionClient` (`src/ksef2/clients/async_online.py`), which
implements `__aenter__`/`__aexit__` but whose `__aenter__` only validates
state. The same pattern exists for batch sessions
(`src/ksef2/clients/async_batch.py`, also used via
`services/async_batch.py`'s `open_session`) and the temporal testdata
context (`src/ksef2/clients/async_testdata.py`, `AsyncTemporalTestData`).

This must be fixed **before** 1.0.0 because it is a breaking change.

## Target design

Make session factories return an object that supports **both** usage styles
without double-await:

```python
# preferred
async with auth.online_session(form_code=FormSchema.FA3) as session:
    ...

# still works for non-context usage
session = await auth.online_session(form_code=FormSchema.FA3)
...
await session.close()
```

Implement a small generic awaitable-context wrapper (the pattern used by
aiohttp's `ClientSession.request`), e.g. in `clients/async_base.py` or a new
private module owned by this plan:

```python
class _AwaitableSession[T]:
    def __init__(self, coro: Coroutine[Any, Any, T]) -> None: ...
    def __await__(self) -> Generator[Any, None, T]: ...        # await factory()
    async def __aenter__(self) -> T: ...                        # opens, returns client
    async def __aexit__(self, *exc) -> None: ...                # closes client
```

`online_session`, `batch_session` (and the testdata temporal context if it has
the same shape) become regular `def` returning this wrapper around the
existing open coroutine. The wrapper's `__aexit__` must delegate to the
session client's existing `__aexit__` semantics (graceful close, logged
termination failures) — do not duplicate that logic.

Decide and keep consistent: `resume_online_session` / `resume_batch_session`
should get the same treatment if they are also `async def` factories.

## Tasks

1. Implement the wrapper and convert the async session/testdata factories.
2. Keep backward compatibility within this release: `await
   auth.online_session(...)` (the old style's inner await) must still return
   a working session client, so existing user code only has to drop the
   extra `await` inside `async with` — verify both styles in tests.
3. Update **all** occurrences of `async with await` in: `README.md` (async
   quickstart + Root Client section), `docs/guides/async-client.md`, any
   other `docs/` files, `scripts/examples/`, and `services/async_batch.py`
   internal usage.
4. Tests: add unit tests covering (a) `async with factory()` opens and closes
   the session, (b) `await factory()` returns an open client, (c) exceptions
   inside the block still close the session. Update existing async session
   tests for the new call shape.
5. Typecheck carefully — the wrapper must be precisely typed so
   `basedpyright` infers the session client type in both styles
   (no `Any` leaks).

## Constraints

- Owned files only: `src/ksef2/clients/async_authenticated.py`,
  `src/ksef2/clients/async_online.py`, `src/ksef2/clients/async_batch.py`,
  `src/ksef2/clients/async_testdata.py`, `src/ksef2/clients/async_base.py`
  (or one new private module under `clients/`),
  `src/ksef2/services/async_batch.py` (call sites only), `README.md` (async
  sections only), `docs/guides/async-client.md`, async examples under
  `scripts/examples/`, and tests. Do **not** touch the sync clients —
  `with auth.online_session(...)` already works and must stay identical.
- Never add `from __future__ import annotations` (project rule).
- No `@asynccontextmanager`-only solution — the return value must remain
  usable without a `with` block (resume/persist workflows depend on holding
  the session object).

## Acceptance criteria

- `rg "async with await" --type md --type py` returns zero hits outside
  CHANGELOG.
- Both usage styles work and are tested.
- Sync API untouched (`git diff --stat` shows no sync client changes).
- `just lint && just format-check && just typecheck && just test` pass
  (run `just sync` first).

## Commits

- `feat(async): sessions usable directly as async context managers`
- `docs: drop async-with-await pattern from quickstarts and guides`

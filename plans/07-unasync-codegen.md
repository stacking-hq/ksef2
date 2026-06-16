# Plan 7 — Async-first: generate the sync tree from the async sources

> **Blocked on plans 1, 2, 4, 5, 6 being merged.** Run the prerequisite gate
> (section 2) before doing anything else. If any check fails, STOP and report —
> do not improvise around a missing prerequisite.

## 1. Context and goal

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed, pydantic v2, httpx, basedpyright,
ruff). The SDK exposes mirrored sync and async APIs as **hand-written twin
modules**: `foo.py` (class `FooClient`) and `async_foo.py` (class
`AsyncFooClient`) across `clients/`, `endpoints/`, `core/middlewares/`, and
`services/`. This is ~3.5k LOC of near-mechanical duplication, and it has
already produced real drift (a security fix that landed async-only).

**Goal:** invert authorship. The `async_*` modules become the single
hand-written source of truth; the sync modules become **committed, generated
artifacts** produced by a deterministic codemod script. After this plan:

- Editing a generated sync file by hand is impossible to do silently (CI
  guard + file header).
- Adding a feature means writing it once, in the async module, and running
  `just gen-sync`.

This is the approach used by httpcore, urllib3 v2, and elasticsearch-py
("unasync"). Direction matters: **async → sync** (deleting `await` is
mechanical; inserting it is not). Never attempt the reverse.

Non-goals: no public API changes, no behavior changes, no test-tree
generation (tests stay hand-written; see section 9), no restructuring of
package layout. The existing module/file naming stays exactly as is —
`invoices.py` next to `async_invoices.py`.

## 2. Prerequisite gate (run first)

Run these checks from the repo root. ALL must pass:

```bash
# Plan 1 landed: shared sanitization helper exists
test -f src/ksef2/services/export_parts.py

# Plan 2 landed: sync endpoints/middleware use shared helpers
rg -q "endpoints.shared" src/ksef2/endpoints/base.py
rg -q "raise_for_ksef_status" src/ksef2/core/middlewares/exceptions.py
rg -q "RETRYABLE_POST_PATHS" src/ksef2/core/routes.py

# Plan 4 landed: no double-await session pattern remains
! rg -q "async with await" README.md docs/ src/ scripts/

# Plan 6 landed: parity gate exists and passes
test -f tests/unit/test_sync_async_parity.py
uv run pytest tests/unit/test_sync_async_parity.py -q
```

Also run the full baseline once and record it — it is your contract:

```bash
just sync && just lint && just format-check && just typecheck && just test
```

If a prerequisite is missing, stop and report which one. (Plans 3 and 5 touch
different files; they are not strict prerequisites, but if plan 5 landed, the
query-param TypedDicts now live under `domain/` — your generator must not
need to care either way.)

## 3. Inventory: what gets generated, what is excluded

### Generated (sync file produced from async source)

| Layer | Pairs (async source → generated sync) |
|---|---|
| `endpoints/` | `async_auth, async_certificates, async_encryption, async_invoices, async_limits, async_peppol, async_permissions, async_session, async_testdata, async_tokens, async_base` → their non-prefixed twins (11 files) |
| `core/middlewares/` | `async_auth, async_exceptions, async_lifecycle, async_retry, async_base` → twins (5 files) |
| `core/` | `async_protocols.py` → `protocols.py` |
| `clients/` | `async_auth, async_authenticated, async_batch, async_certificates, async_encryption, async_invoice_sessions, async_invoices, async_limits, async_online, async_peppol, async_permissions, async_session_management, async_testdata, async_tokens` → twins (14 files) |
| `services/` | `async_invoices, async_batch` → `invoices.py`, `batch.py` |

### Excluded (stays hand-written on both sides) — `EXCLUDED` list in the script

| File | Reason |
|---|---|
| `core/http.py` / `core/async_http.py` | Structurally divergent: async owns `_owns_client` + `aclose()`; sync client closing happens in `Client.close()`. Tiny files (~50 LOC each); not worth forcing. |
| `clients/base.py` / `clients/async_base.py` | Root client wiring differs (httpx client construction, plan 4's awaitable-session wrapper lives async-side only). |
| All `__init__.py` files | They import BOTH variants and define `__all__`; never generate. |
| `endpoints/shared.py`, `services/batch_preparation.py`, `services/export_parts.py`, `clients/_metadata_pagination.py`, `core/polling.py`, `core/response_errors.py` | Already shared single implementations — no twin. |
| `services/builders/`, `services/renderers/` | Sync-only, no twin. |

If during migration another pair turns out to be genuinely irreconcilable,
add it to `EXCLUDED` with a one-line justification comment and move on. Do
**not** contort the async source or hand-tune a generated file to force a
match.

## 4. The generator: `scripts/gen_sync.py`

### Technology

Use **libcst** (add with `uv add --group codegen libcst` — codegen group, NOT
runtime dependencies). libcst preserves comments/formatting and lets you
transform code constructs without touching string literals — a regex/`sed`
approach WILL corrupt docstrings and string contents; do not use one.

### Transformation rules (implement as libcst transformers, in this order)

**R1 — structural async removal**

| Async construct | Sync output |
|---|---|
| `async def f(...)` | `def f(...)` |
| `await <expr>` | `<expr>` |
| `async with <e> as x:` | `with <e> as x:` |
| `async for x in <e>:` | `for x in <e>:` |

**R2 — `asyncio.to_thread` unwrapping** (must run BEFORE generic `await`
removal): `await asyncio.to_thread(f, a, b, kw=v)` → `f(a, b, kw=v)`. The
first positional argument becomes the callee; it may be a dotted attribute,
e.g. `await asyncio.to_thread(target_path.mkdir, parents=True, exist_ok=True)`
→ `target_path.mkdir(parents=True, exist_ok=True)`. Current call sites to
verify against: `services/async_invoices.py` (4), `services/async_batch.py`
(2), `clients/async_auth.py` (2).

**R3 — sleep**: `asyncio.sleep` → `time.sleep` (as an expression reference
too, e.g. `_sleep_fn or asyncio.sleep` in `async_retry.py`).

**R4 — identifier map** (exact, whole-identifier matches only):

| Async | Sync |
|---|---|
| `AsyncIterator` / `AsyncIterable` / `AsyncGenerator` | `Iterator` / `Iterable` / `Generator` |
| `Awaitable[X]` annotation | `X` |
| `Coroutine[Any, Any, X]` annotation | `X` |
| `httpx.AsyncClient` | `httpx.Client` |
| `__aenter__` / `__aexit__` / `__anext__` / `__aiter__` | `__enter__` / `__exit__` / `__next__` / `__iter__` |
| `aclose` | `close` |
| `StopAsyncIteration` | `StopIteration` |
| `AsyncSleep` (type alias, if present) | `Sleep` |

**R5 — SDK class/name prefix strip**: any identifier matching `Async[A-Z]\w*`
that refers to a ksef2 symbol loses the `Async` prefix (`AsyncInvoicesClient`
→ `InvoicesClient`, `AsyncBaseMiddleware` → `BaseMiddleware`, ...). Apply to
definitions, references, and strings used in `repr`/error messages if any.

**R6 — import rewrites**:
- `from ksef2.<pkg>.async_<mod> import ...` → `from ksef2.<pkg>.<mod> import ...`
- `import asyncio` → `import time` if (and only if) the transformed module
  still references `time.sleep`; drop `import asyncio` entirely when no
  asyncio reference survives. Drop now-unused typing imports
  (`AsyncIterator`, `Awaitable`, ...) and add newly needed ones (`Iterator`).
  Easiest robust approach: after transformation, run `ruff check --fix
  --select F401,I` plus `ruff format` on the output and let it clean imports
  — but you must still ADD missing imports yourself (ruff won't invent
  them); track which mapped names you emitted and ensure their import lines
  exist.

**R7 — docstring pass** (docstrings only, simple string replaces):
Use phrase-specific replacements for known docstring wording, such as
`"Async high-level"`→`"High-level"`, `"Async client"`→`"Client"`,
`"Root async"`→`"Root"`, `"Raw async"`→`"Raw"`, `"async with"`→`"with"`,
`"await "`→`""`, `"AsyncClient"`→`"Client"`, and
`"async context manager"`→`"context manager"`. Keep this list short and
conservative; minor residual async phrasing in a docstring is acceptable,
broken docstrings are not.

**R8 — header**: prepend to every generated file:

```python
# Generated by scripts/gen_sync.py from <async source path>.
# DO NOT EDIT BY HAND — edit the async source and run `just gen-sync`.
```

### Script interface

```
uv run python scripts/gen_sync.py                 # regenerate all targets in place
uv run python scripts/gen_sync.py --check         # exit 1 if any generated file differs (no writes)
uv run python scripts/gen_sync.py --only clients/async_invoices.py --diff
                                                  # print unified diff vs existing file, no writes
```

The file-pair table and `EXCLUDED` list live at the top of the script as
plain data. Output must be deterministic (same input → byte-identical
output). After generation, run `ruff format` on outputs programmatically or
document that `just gen-sync` does it.

### Wiring

- `justfile`: add `gen-sync: uv run python scripts/gen_sync.py && uv run ruff format <generated files>` and `check-gen-sync: uv run python scripts/gen_sync.py --check`; add `just check-gen-sync` to the `release-check` recipe.
- Add `tests/unit/test_generated_sync.py` with a single test that imports the
  generator functions and asserts every generated file matches a fresh
  in-memory regeneration. This makes the guard run inside plain `just test`
  with zero CI configuration.

## 5. Phase 0 — canonicalize the async sources

Before generating anything, make the async modules worthy of being the source
of truth. For every pair in section 3:

1. **Docstrings**: the sync modules currently have the better docstrings
   (Google style, Args/Returns/Raises). Copy every docstring that exists
   sync-side but not async-side INTO the async module, adapting phrasing
   (`await`, `async with`). After this step the async file is a superset.
2. **Known micro-divergences** — resolve toward the async pattern unless
   noted:
   - `async_retry.py` has an injectable `_sleep_fn` test hook the sync twin
     lacks. Keep it in the async source; the generated sync gains the same
     hook (type alias `AsyncSleep` → `Sleep` per R4 — define both aliases in
     a shared or per-variant location so the mapping works). Update sync
     retry tests if they can now use the hook.
   - `services/async_invoices.py` uses an `async def _noop` where sync used
     `lambda: None`. The generated sync will contain a plain `def _noop` —
     fine; delete nothing manually.
3. **Behavioral diff audit per pair**: before trusting generation, read the
   current sync file side-by-side with what the generator produces (the
   `--diff` mode). Every hunk falls into exactly one class:
   - **(a) generator rule gap** → extend the rule table; regenerate.
   - **(b) async source is missing something the sync file has** (docstring,
     comment, a fix that landed sync-only) → port it to the async source;
     regenerate.
   - **(c) sync file has divergent behavior that is WRONG** (stale, buggy) →
     the generated version replaces it; note the behavior change in the
     commit message and make sure a test covers the corrected behavior.
   - **(d) legitimate irreconcilable divergence** → move the pair to
     `EXCLUDED`, justify, move on.

   Never resolve a hunk by editing the generated output.

## 6. Migration order (one commit per layer, diff-zero before replacing)

Work layer by layer; each layer must end with the full check suite green:

1. **`endpoints/`** — most mechanical after plan 2; proves the generator.
2. **`core/middlewares/` + `core/async_protocols.py`** — small, but
   `protocols.py` defines the `Middleware` protocol many files import;
   confirm the generated version is import-identical (same `__all__`, same
   class names).
3. **`clients/`** — largest layer. `async_online.py` / `async_batch.py`
   contain plan 4's session semantics; their generated sync output must
   reproduce the EXISTING sync context-manager behavior (`__enter__` opens
   nothing — it validates; `__exit__` closes gracefully). If plan 4 put the
   awaitable-wrapper into `clients/async_base.py` (excluded), the session
   modules themselves should transform cleanly; if the wrapper leaked into
   `async_online.py`/`async_batch.py`, the wrapper class itself needs an R-rule
   (`__await__` has no sync meaning — strip the method entirely via an
   explicit allowlisted deletion rule, documented in the script).
4. **`services/`** — `async_invoices.py`, `async_batch.py`; exercises R2
   heavily.

For each layer: Phase-0 the sources → iterate `--diff` to zero/accepted →
replace files via `just gen-sync` → run `just lint && just format-check &&
just typecheck && just test` → commit.

## 7. Hard rules (do not violate)

- **NEVER** hand-edit a file carrying the generated header. If a generated
  file is wrong, the async source or the generator is wrong — fix those.
- **NEVER** add `from __future__ import annotations` anywhere (project rule).
- **NEVER** use regex/sed over whole files for the transformation — libcst
  nodes only. String literals and docstrings must survive untouched except
  via R7.
- Public API must not change: same class names, same method names, same
  signatures, same `__all__` contents in every `__init__.py`. The plan-6
  parity test plus the full unit suite is the contract; if either fails, the
  generator is wrong.
- The package activates beartype on import (`ksef2/__init__.py`): generated
  annotations must stay precise — beartype will reject e.g. an
  `Iterator` annotation on a function still returning a generator coroutine.
  Importing the package after each layer (`uv run python -c "import ksef2"`)
  is a cheap smoke test.
- Keep decorators (`@final`, `@property`, `@singledispatch` registrations)
  exactly as in the async source.
- Generated files are committed. Do not gitignore them; do not move them.

## 8. Acceptance criteria

- All pairs from section 3 are generated; every generated file starts with
  the R8 header; `EXCLUDED` contains only the entries from section 3 plus
  any additions each carrying a written justification.
- `uv run python scripts/gen_sync.py --check` exits 0 on a clean tree, and
  exits 1 if you manually corrupt one generated file (verify once, revert).
- `tests/unit/test_generated_sync.py` passes and fails appropriately (same
  manual verification).
- `just lint && just format-check && just typecheck && just test` all pass;
  the plan-6 parity suite passes unchanged (or with `KNOWN_DIVERGENCES`
  entries REMOVED — generation should shrink that list, never grow it).
- `git diff --stat` against the merge base shows no changes to public
  `__init__.py` export lists, `pyproject.toml` runtime dependencies, or any
  `domain/`/`infra/` module.
- A short `docs/tooling/sync-codegen.md` (or a section in CONTRIBUTING if
  that exists) explains: async is hand-written, sync is generated, how to
  run `just gen-sync`, and what to do when `check-gen-sync` fails.

## 9. Explicitly out of scope (do not do these)

- Generating the test tree (`tests/unit/**` stays hand-written; a follow-up
  may unasync the tests later).
- Touching `core/http.py`/`async_http.py` or `clients/base.py`/`async_base.py`
  beyond Phase-0 docstring syncing.
- Renaming modules, classes, or restructuring packages.
- "Improving" code while porting — this plan changes authorship, not design.

## 10. Commits

- `chore(codegen): add libcst-based sync generator and CI guard`
- `docs: sync code generation workflow`
- one `refactor(<layer>): generate sync <layer> from async sources` per
  layer (endpoints, middlewares, clients, services), each containing the
  Phase-0 async-source edits for that layer plus the regenerated files.

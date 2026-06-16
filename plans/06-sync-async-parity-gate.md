# Plan 6 — CI gate enforcing sync/async API parity

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed), preparing for 1.0.0. The SDK
maintains hand-written mirrored sync/async trees (`Foo` in `foo.py`,
`AsyncFoo` in `async_foo.py`) across `clients/`, `endpoints/`, and
`services/`. There is no automation preventing the two surfaces from
drifting — an audit found drift had already shipped (a sanitization fix and
shared-helper refactors landed async-only). Method-name parity is currently
clean across all pairs, so a strict gate can be introduced without
grandfathering.

**Important**: this plan should be merged **after** the parallel workstreams
that intentionally change async signatures (notably the async session
context-manager refactor). Write the gate against whatever the code looks
like in your worktree, and make mismatch output actionable so rebasing onto
the other branches is easy.

## Tasks

Create `tests/unit/test_sync_async_parity.py` containing a programmatic
parity gate:

1. **Pair discovery.** Automatically discover pairs rather than hardcoding:
   for each module `m` in `ksef2.clients`, `ksef2.endpoints`,
   `ksef2.services` with a sibling `async_<m>`, match public classes by the
   `X` ↔ `AsyncX` naming convention. Assert that every sync class has an
   async twin and vice versa (explicit, documented skip list for legitimate
   singletons — e.g. shared helper modules like `endpoints/shared.py`,
   `services/batch_preparation.py`, `clients/_metadata_pagination.py`).

2. **Method-surface parity.** For each pair, compare the sets of public
   attributes (methods + properties, names not starting with `_`). Any
   one-sided method fails the test with a message naming the class, the
   method, and which side is missing it.

3. **Signature parity.** For each shared public method, compare
   `inspect.signature` parameter names, kinds, and defaults — ignoring
   return annotations and async-specific differences. Normalize before
   comparing:
   - `self` excluded;
   - annotation comparison by string with `Async` prefixes stripped and
     known sync/async type swaps mapped (e.g. `Iterator` ↔ `AsyncIterator`,
     `httpx.Client` ↔ `httpx.AsyncClient`, `Middleware` ↔ `AsyncMiddleware`);
   - allow an explicit, per-method exemption dict at the top of the file
     (`KNOWN_DIVERGENCES: dict[str, str]` mapping `"ClassName.method"` to a
     short justification) so intentional differences are visible and
     reviewed rather than silently tolerated. Seed it only with divergences
     you actually find and can justify from the code (document each).

4. **Docstring presence (soft parity).** If a sync method has a docstring and
   its async twin does not (or vice versa), report it. Decide based on the
   current count: if there are ≤ ~15 gaps, copy the missing docstrings to
   the bare twins (adjusting `await`/`async with` phrasing) and make the
   check strict; if there are many more, make this check a clearly-labeled
   skipped/xfail summary that prints the gaps, and note the count in the
   commit message.

5. Keep the whole gate fast (pure introspection, no network, no fixtures) so
   it runs in the normal `just test` invocation with zero configuration.

## Constraints

- New files only: `tests/unit/test_sync_async_parity.py` (single file
  preferred). The **only** allowed `src/` edits are docstring copies from
  task 4 — no signature or behavior changes. If the gate exposes a real
  signature mismatch, do not fix it here: add it to `KNOWN_DIVERGENCES`
  with a `TODO` justification and list it prominently in the commit message
  so it can be triaged.
- Never add `from __future__ import annotations` (project rule).
- Note: the package activates beartype on import (`ksef2/__init__.py`);
  introspect classes via their defining modules normally — `inspect`
  signatures survive beartype wrapping, but verify and use
  `inspect.unwrap` if needed.

## Acceptance criteria

- Deleting a random public method from one async client makes the gate fail
  with a message that names the exact class/method (verify manually once,
  then restore).
- Gate passes on the current tree, with every entry in `KNOWN_DIVERGENCES`
  justified.
- `just lint && just format-check && just typecheck && just test` pass
  (run `just sync` first).

## Commit

`test: enforce sync/async API parity across clients, endpoints, services`

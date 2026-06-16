# Plan 2 — Single error pipeline + finish endpoint shared-helper migration

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed, pydantic v2, httpx). The SDK maintains
hand-written mirrored sync/async trees. Two refactors were started for the
async side and never completed for sync, leaving duplicated logic that must be
fixed in two places whenever error mapping or response parsing changes:

1. **Exception middleware.** `src/ksef2/core/middlewares/async_exceptions.py`
   is ~40 LOC and delegates to the shared `raise_for_ksef_status()` in
   `src/ksef2/core/response_errors.py`. The sync
   `src/ksef2/core/middlewares/exceptions.py` is ~120 LOC and still embeds its
   own inline `_raise_for_status` / `_try_parse` / problem-details handling —
   a near-copy of what `response_errors.py` already centralizes.

2. **Endpoint base classes.** `src/ksef2/endpoints/async_base.py` imports
   `parse_response`, `parse_response_list`, `build_params`, and
   `DEFAULT_PARAMS_ADAPTER` from `src/ksef2/endpoints/shared.py`. The sync
   `src/ksef2/endpoints/base.py` still inlines its own `_parse`,
   `_parse_list`, and `build_params` (~60 LOC duplicate).

3. **Retry route allowlist.** `src/ksef2/core/middlewares/retry.py` and
   `async_retry.py` each define an identical `_RETRYABLE_POST_PATHS`
   frozenset (11 route paths). The canonical route constants live in
   `src/ksef2/core/routes.py`.

A parity test file `tests/unit/test_shared_refactor_helpers.py` already proves
sync and async `build_params` agree — use it as a reference for expectations.

## Tasks

1. Refactor sync `KSeFExceptionMiddleware`
   (`core/middlewares/exceptions.py`) to delegate to
   `raise_for_ksef_status()` from `core/response_errors.py`, mirroring the
   async middleware's structure. Delete the now-dead inline parsing helpers.
   Behavior (exception types, messages, status mapping, rate-limit handling)
   must remain identical — existing middleware tests are the contract; only
   update tests that assert on removed private helpers.

2. Migrate sync `BaseEndpoints` (`endpoints/base.py`) onto
   `endpoints/shared.py` exactly as `AsyncBaseEndpoints` does: same imports,
   same delegation, delete the inline `_parse` / `_parse_list` /
   `build_params`. Public method signatures of `BaseEndpoints` must not
   change (all `endpoints/*.py` modules subclass it).

3. Extract `_RETRYABLE_POST_PATHS` into a single definition — put it in
   `src/ksef2/core/routes.py` (e.g. `RETRYABLE_POST_PATHS`) and import it
   from both retry middlewares. Verify the two existing frozensets are
   identical before consolidating; if they differ, keep the union and note it
   in the commit message.

4. Tests: run the full unit suite; strengthen
   `tests/unit/test_shared_refactor_helpers.py` if a previously-spot-checked
   equivalence is now structural (e.g. the build_params parity test can
   become a simple identity assertion).

## Constraints

- Owned files only: `src/ksef2/endpoints/base.py`,
  `src/ksef2/endpoints/shared.py`, `src/ksef2/core/middlewares/exceptions.py`,
  `src/ksef2/core/middlewares/async_exceptions.py`,
  `src/ksef2/core/middlewares/retry.py`,
  `src/ksef2/core/middlewares/async_retry.py`, `src/ksef2/core/routes.py`,
  `src/ksef2/core/response_errors.py`, and tests. Do **not** touch
  `src/ksef2/core/exceptions.py` (exception class definitions — owned by a
  parallel workstream) or `pyproject.toml`.
- Never add `from __future__ import annotations` (project rule).
- This is a pure consolidation: zero public API changes, zero behavior
  changes. If you find a real behavioral difference between the sync and
  async error paths while merging them, preserve the **async** behavior
  (it is the newer, intended one) and document the difference in the commit
  message.

## Acceptance criteria

- `core/response_errors.py` is the only place that maps HTTP responses to
  KSeF exceptions; both middlewares are thin shells.
- `endpoints/shared.py` is the only implementation of response parsing and
  query-param building; both base classes delegate to it.
- One `RETRYABLE_POST_PATHS` definition.
- `just lint && just format-check && just typecheck && just test` pass
  (run `just sync` first).

## Commits

- `refactor(core): route sync exception middleware through response_errors`
- `refactor(endpoints): migrate sync BaseEndpoints onto shared helpers`
- `refactor(core): single source for retryable POST paths`

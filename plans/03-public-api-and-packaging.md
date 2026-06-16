# Plan 3 — Dependency hygiene, public exports, and honest timeout errors

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed, pydantic v2), preparing for a 1.0.0
release. Three independent packaging/public-surface problems were found in an
audit; this plan fixes all of them.

### A. Dead runtime dependencies

`pyproject.toml` `[project].dependencies` declares packages that are never
imported by `src/ksef2` (verified by grep):

- `requests` — never imported anywhere in the repo's runtime code (httpx is
  the HTTP stack). Remove entirely.
- `pytest-cov` — test tooling. Move to the `dev` dependency group.
- `polyfactory` — only used under `tests/`. Move to `dev`.
- `dotenv` — only `tests/integration/conftest.py` uses `from dotenv import
  load_dotenv`, which is actually served by the transitive `python-dotenv`.
  Remove `dotenv` from runtime deps and add `python-dotenv` to `dev`.

### B. Undocumented public error surface

`src/ksef2/__init__.py` exports only clients + transport config + `FormSchema`
(see its `__all__`). Users must import exceptions from
`ksef2.core.exceptions` — a path that appears in no `__all__` and no docs.
There is also no top-level `__version__` even though
`src/ksef2/__version__.py` exists (commitizen bumps it).

### C. Fake HTTP status codes on SDK-side timeouts

Polling timeouts that never touched HTTP are raised as API errors:

- `src/ksef2/clients/tokens.py` (~line 52): timeout factory raises
  `KSeFApiError(0, ExceptionCode.UNKNOWN_ERROR, ...)` — `status_code=0`
  breaks user code matching on status codes.
- `src/ksef2/clients/auth.py` (~line 219): timeout factory raises
  `KSeFAuthError(status_code=408, ...)` — pretends a 408 HTTP response
  occurred.

The exception module `src/ksef2/core/exceptions.py` already has precedents for
proper domain timeouts: `KSeFExportTimeoutError`,
`KSeFInvoiceProcessingTimeoutError`, etc.

## Tasks

1. **Dependencies**: apply the moves/removals above in `pyproject.toml`, run
   `uv lock` (commit `uv.lock`), and run the unit suite to prove nothing
   imported the removed packages.

2. **Exceptions for timeouts**: in `core/exceptions.py` add (following the
   style of the existing timeout exceptions, inheriting from `KSeFException`,
   carrying structured fields like attempts/elapsed):
   - `KSeFAuthPollingTimeoutError`
   - `KSeFTokenStatusTimeoutError` (name per existing conventions — inspect
     the module and match its naming/docstring style)

   Use them in the two timeout factories in `clients/auth.py` /
   `clients/tokens.py` and their async twins (`clients/async_auth.py`,
   `clients/async_tokens.py` — mirror exactly). Update affected tests.
   Note these were previously `KSeFApiError`/`KSeFAuthError` subclass
   instances — check whether any internal code catches them and adjust.

3. **Root exports**: extend `src/ksef2/__init__.py` `__all__` with the stable
   error surface and version:
   - `__version__` (re-export from `ksef2.__version__`)
   - `KSeFException`, `KSeFApiError`, `KSeFAuthError`,
     `KSeFValidationError`, `KSeFRateLimitError`, `ExceptionCode`, and the
     timeout exceptions (inspect `core/exceptions.py` and export the full
     coherent public set — skip clearly internal ones if any).
   Keep `ksef2.core.exceptions` importable (no moves, just re-exports).

4. **Error handling guide**: write `docs/guides/errors.md` documenting the
   exception hierarchy (small tree diagram), `ExceptionCode` semantics
   (including that unknown KSeF codes map to `UNKNOWN_ERROR`), the
   retry-on-`NOT_PROCESSED_YET` pattern already used internally in
   `services/invoices.py` (~line 90), rate-limit handling
   (`KSeFRateLimitError.retry_after`), and the new timeout exceptions.
   Match the tone/structure of existing files in `docs/guides/`. Add a short
   "Error handling" section to `README.md` linking to it.

## Constraints

- Owned files only: `pyproject.toml`, `uv.lock`, `src/ksef2/__init__.py`,
  `src/ksef2/core/exceptions.py`, `src/ksef2/clients/{auth,async_auth,tokens,async_tokens}.py`,
  `docs/guides/errors.md`, `README.md` (new section only), and tests.
  Do **not** touch `src/ksef2/core/middlewares/` or `src/ksef2/core/response_errors.py`
  (owned by a parallel workstream).
- Never add `from __future__ import annotations` (project rule).
- Mirror every sync client change into its async twin.
- Do not rename or remove any existing exception class — only add.

## Acceptance criteria

- `uv pip show requests` finds nothing after a fresh `uv sync` without dev
  groups; unit tests still pass.
- `python -c "import ksef2; print(ksef2.__version__); ksef2.KSeFApiError"`
  works.
- SDK-side polling timeouts no longer carry fabricated HTTP status codes.
- `docs/guides/errors.md` exists and README links to it.
- `just lint && just format-check && just typecheck && just test` pass
  (run `just sync` first).

## Commits

- `build: remove unused runtime dependencies`
- `feat(exceptions): dedicated polling timeout errors`
- `feat: export error surface and __version__ from package root`
- `docs: add error handling guide`

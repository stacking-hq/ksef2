# Plan 1 — Port export-part name sanitization to the sync client (security)

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed, pydantic v2). The SDK maintains
hand-written mirrored sync/async trees (`foo.py` / `async_foo.py`).

A security fix landed **only on the async side**. When downloading and
decrypting export packages, part file names come from the KSeF API response and
are used to build local file paths.

- **Async (correct)** — `src/ksef2/services/async_invoices.py`, in
  `fetch_package` (~lines 167–178): strips directory components
  (`Path(part.part_name.replace("\\", "/")).name`), uses
  `removesuffix(".aes")`, and raises `ValueError` for empty names, names
  starting with `.`, names containing NUL, or `.`/`..`.
- **Sync (vulnerable)** — `src/ksef2/services/invoices.py`, in
  `fetch_package` (~line 165): writes
  `target_path / part.part_name.replace(".aes", "")` directly. Two bugs:
  1. No path-traversal protection — a part name like
     `../../evil.zip.aes` escapes `target_directory` (zip-slip class).
  2. `str.replace(".aes", "")` removes **all** occurrences, mangling names
     like `report.aes.backup.zip.aes`, where async's `removesuffix` only
     strips the trailing extension.

Async-side tests exist in `tests/unit/services/test_async_invoices.py`
(`test_fetch_package_sanitizes_part_name...`,
`test_fetch_package_rejects_invalid_part_names`). The sync suite
`tests/unit/services/test_invoices.py` has no equivalents.

## Tasks

1. Extract the sanitization into a single shared, pure function so the logic
   can never drift again. Create `src/ksef2/services/export_parts.py` with
   something like:

   ```python
   def safe_part_filename(part_name: str) -> str:
       """Return a sanitized local filename for an export package part.

       Raises ValueError for path-traversal attempts and degenerate names.
       """
   ```

   Move the exact async validation rules into it (backslash normalization,
   `Path(...).name`, `removesuffix(".aes")`, rejection of empty/`.`/`..`/
   dot-prefixed/NUL-containing names). Keep the raised exception type and
   message format compatible with the existing async behavior.

2. Use it from **both** `services/invoices.py` and
   `services/async_invoices.py` `fetch_package` implementations, deleting the
   inline copies.

3. Tests:
   - Add unit tests for `safe_part_filename` itself (happy path, traversal
     with `/` and `\\`, double `.aes`, empty, `.`, `..`, dot-prefixed, NUL).
   - Mirror the existing async `fetch_package` sanitization tests into
     `tests/unit/services/test_invoices.py` for the sync client.
   - Keep the async tests passing unchanged (or update them minimally if they
     asserted on private internals you removed).

## Constraints

- Do not modify any files outside: `src/ksef2/services/invoices.py`,
  `src/ksef2/services/async_invoices.py`, `src/ksef2/services/export_parts.py`
  (new), `src/ksef2/services/__init__.py` (only if an export is needed),
  `tests/unit/services/`.
- Never add `from __future__ import annotations` (project rule).
- Mirror sync/async exactly — the point of this change is eliminating drift.
- No behavior changes beyond the sanitization (no new params, no renames).

## Acceptance criteria

- Sync `fetch_package` rejects/neutralizes hostile part names identically to
  async.
- A single shared implementation of the sanitization exists; neither service
  module contains an inline copy.
- New tests cover both clients; `just lint && just format-check &&
  just typecheck && just test` all pass (run `just sync` first).

## Commit

One commit: `fix(invoices): sanitize export part names in sync fetch_package`
(plus a `test:` commit if you prefer splitting).

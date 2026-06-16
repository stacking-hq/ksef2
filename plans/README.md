# Pre-1.0.0 hardening plans

Six independent workstreams derived from the 1.0.0 readiness review (June 2026).
Each plan is a self-contained brief for an agent running in its own worktree:
it carries all required context, exact file ownership, acceptance criteria, and
verification commands. Hand one plan file to one agent as its full prompt.

## Plans

| # | Plan | Theme | Size |
|---|------|-------|------|
| 1 | `01-sync-export-security-parity.md` | Port async export-part sanitization to sync (security) | S |
| 2 | `02-error-pipeline-and-endpoints-consolidation.md` | Finish half-migrated shared helpers; single error pipeline | M |
| 3 | `03-public-api-and-packaging.md` | Dependency cleanup, root exports, timeout exception fixes | M |
| 4 | `04-async-session-ergonomics.md` | Eliminate `async with await` session pattern | M |
| 5 | `05-layering-and-dead-code.md` | Fix layering inversions, remove dead code | M |
| 6 | `06-sync-async-parity-gate.md` | CI gate enforcing sync/async API parity | S |
| 7 | `07-unasync-codegen.md` | Async-first: generate the sync tree from async sources (**blocked on 1, 2, 4, 6**) | L |

## Merge order

Merge in numeric order. Rationale:

1. **Plan 1 first** — security fix, smallest diff, no dependencies.
2. **Plans 2, 3, 4, 5 in any order** — file ownership is disjoint by design
   (see matrix below). Numeric order is safest if you want zero rebase noise.
3. **Plan 6 last** — the parity gate asserts the post-refactor API surface;
   merging it earlier would pin signatures that plans 4 and 5 still change.
4. **Plan 7 strictly after all of the above** — it runs alone (not in
   parallel with anything), since it rewrites the entire sync tree. Its
   prerequisite gate (section 2 of the plan) verifies plans 1, 2, 4, and 6
   landed before any work starts.

## File-ownership matrix (conflict avoidance)

| Plan | Owns (may modify) |
|------|--------------------|
| 1 | `src/ksef2/services/invoices.py`, `src/ksef2/services/async_invoices.py`, `src/ksef2/services/export_parts.py` (new), `tests/unit/services/` |
| 2 | `src/ksef2/endpoints/base.py`, `src/ksef2/endpoints/shared.py`, `src/ksef2/core/middlewares/exceptions.py`, `src/ksef2/core/middlewares/async_exceptions.py`, `src/ksef2/core/middlewares/retry.py`, `src/ksef2/core/middlewares/async_retry.py`, `src/ksef2/core/routes.py`, `src/ksef2/core/response_errors.py`, related tests |
| 3 | `pyproject.toml`, `uv.lock`, `src/ksef2/__init__.py`, `src/ksef2/core/exceptions.py`, `src/ksef2/clients/auth.py`, `src/ksef2/clients/async_auth.py`, `src/ksef2/clients/tokens.py`, `src/ksef2/clients/async_tokens.py`, `docs/guides/errors.md` (new), related tests |
| 4 | `src/ksef2/clients/async_authenticated.py`, `src/ksef2/clients/async_online.py`, `src/ksef2/clients/async_batch.py`, `src/ksef2/clients/async_testdata.py`, `README.md` (async sections only), `docs/guides/async-client.md`, async examples in `scripts/examples/`, related tests |
| 5 | `src/ksef2/domain/models/pagination.py`, query-param TypedDict relocation (`src/ksef2/domain/types.py` or new module), `src/ksef2/endpoints/session.py` / `async_session.py` (TypedDict removal only), `src/ksef2/services/auth.py` (delete), `src/ksef2/core/invoices.py` (delete), related tests |
| 6 | `tests/unit/test_sync_async_parity.py` (new) only |

Overlap notes:
- Plans 2 and 5 both touch `endpoints/session.py`: plan 2 only changes base-class
  usage inside endpoint classes; plan 5 only moves TypedDict definitions. If both
  land, expect at most a trivial import-line rebase.
- Plan 3 touches exception **classes** (`core/exceptions.py`); plan 2 touches
  exception **middleware** (`core/middlewares/`). Disjoint files.

## Shared instructions baked into every plan

- Python 3.12+, `uv`-managed. Run `just sync` once after creating the worktree.
- Never add `from __future__ import annotations` (project rule, AGENTS.md).
- Every change to a sync module must be mirrored in its `async_*` twin and
  vice versa, including tests.
- Verify with: `just lint && just format-check && just typecheck && just test`.
- Conventional-commit messages (`fix:`, `refactor:`, `feat:`, `test:`).

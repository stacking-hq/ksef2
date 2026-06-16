# Plan 5 — Fix layering inversions and remove dead code

## Context

You are working on `ksef2`, a Python SDK for Poland's KSeF e-invoicing API
(`src/ksef2`, Python 3.12+, uv-managed, pydantic v2), preparing for 1.0.0.
The intended layering is:

```
domain  (pure models)  ←  core  ←  infra  ←  endpoints  ←  clients/services
```

An architecture audit found one dependency inversion plus several pieces of
dead/duplicated code that should not ship in 1.0.

### A. Inversion: `domain` imports from `endpoints`

`src/ksef2/domain/models/pagination.py` (~lines 21–24):

```python
from ksef2.endpoints.base import OffsetPaginationQueryParams
from ksef2.endpoints.invoices import InvoiceMetadataQueryParams
from ksef2.endpoints.session import ListSessionsQueryParams
from ksef2.endpoints.tokens import ListTokensQueryParams
```

Domain pagination models are typed against endpoint-layer TypedDicts. The
wire-shape TypedDicts should live in a layer both can import.

### B. Duplicated TypedDict

`ListSessionsQueryParams` is defined identically in both
`src/ksef2/endpoints/session.py` and `src/ksef2/endpoints/async_session.py`.

### C. Dead code

- `src/ksef2/services/auth.py` — contains only `AuthService = AuthClient`,
  imported nowhere.
- `src/ksef2/core/invoices.py` — a tiny `InvoiceTemplater` string-replace
  helper orphaned from the architecture. Verify it is unused (check
  `scripts/` and `tests/` too) before deleting; if something uses it, leave
  it and note that in the commit message instead.
- `SessionListParams` and `AuthSessionListParams` in
  `domain/models/pagination.py` — used only by test factories, not by any
  production client. Either delete them (and their factory usages) or wire
  them into the corresponding client methods; prefer deletion unless wiring
  is trivial and consistent with sibling clients.

## Tasks

1. Move the query-param TypedDicts that `domain/models/pagination.py` needs
   into the domain/core layer. Recommended target:
   `src/ksef2/domain/types.py` (it already holds shared domain-level types)
   or a new `src/ksef2/domain/query_params.py` if that file would get
   crowded. Then:
   - `endpoints/*.py` and `endpoints/async_*.py` import them from the new
     location (keep re-export aliases in the endpoint modules if many
     call sites/tests reference the old paths — check first; prefer updating
     imports over aliases since these are internal modules).
   - `domain/models/pagination.py` imports them from the new location.
   - Result: `rg "from ksef2.endpoints" src/ksef2/domain/` returns nothing.
2. While moving, deduplicate `ListSessionsQueryParams` so sync and async
   session endpoints import the single definition.
3. Delete the dead code listed in C (with the verification caveats noted).
4. Update tests/factories accordingly.

## Constraints

- Owned files: `src/ksef2/domain/models/pagination.py`,
  `src/ksef2/domain/types.py` (or one new domain module),
  TypedDict-definition blocks and imports inside `src/ksef2/endpoints/*.py`,
  `src/ksef2/services/auth.py` (delete), `src/ksef2/core/invoices.py`
  (delete), and tests.
- A parallel workstream owns the **base-class/parsing logic** in
  `endpoints/base.py` and `endpoints/shared.py` — in those two files you may
  only touch import lines for moved TypedDicts, nothing else.
- Never add `from __future__ import annotations` (project rule).
- Pure refactor: zero public API changes. `ksef2.domain.models` re-exports
  must keep working (check `domain/models/__init__.py`).
- Mirror any sync endpoint import change in its `async_*` twin.

## Acceptance criteria

- No module under `src/ksef2/domain/` imports from `ksef2.endpoints` or
  `ksef2.clients` (verify with `rg`).
- `ListSessionsQueryParams` has exactly one definition.
- `services/auth.py` gone; `core/invoices.py` gone or justified.
- `just lint && just format-check && just typecheck && just test` pass
  (run `just sync` first).

## Commits

- `refactor(domain): move query-param types out of endpoints layer`
- `refactor: remove dead AuthService alias and orphaned helpers`
